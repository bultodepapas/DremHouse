"""Bounded SVG style compilation for portable, literal-colour export.

The current drawing theme uses CSS custom properties for maintainable source
styles. Some SVG rasterizers do not resolve those properties consistently, so
the export boundary compiles theme ``var(--token)`` references to literal CSS
values while retaining selectors, classes, IDs, metadata and geometry.

This is deliberately a small compiler rather than a general CSS evaluator: it
supports literal six-digit theme colours, rejects unresolved names and does not
evaluate selectors, inheritance, general cascade, functions or fallback
expressions. Only simple top-level ``:root`` literal colour declarations are
read so exported styles preserve their source theme values.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from xml.etree import ElementTree as ET

from dreamhouse.svg.theme import THEME_COLOURS

_HEX_COLOUR = re.compile(r"^#[0-9A-Fa-f]{6}$")
_VARIABLE_NAME = re.compile(r"^--([A-Za-z_][A-Za-z0-9_-]*)$")
_VARIABLE_CALL_START = re.compile(r"(?<![-_A-Za-z0-9])var\s*\(", re.IGNORECASE)
_CUSTOM_PROPERTY_ASSIGNMENT = re.compile(
    r"(?<![-_A-Za-z0-9])(--[A-Za-z_][A-Za-z0-9_-]*)\s*:\s*([^;{}]+)"
)
_PAINT_ATTRIBUTES = frozenset(
    {
        "color",
        "fill",
        "flood-color",
        "lighting-color",
        "solid-color",
        "stop-color",
        "stroke",
        "viewport-fill",
    }
)
_NON_CSS_METADATA_ATTRIBUTES = frozenset({"class", "href", "id", "role", "style", "title", "desc"})


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _validate_variables(variables: Mapping[str, str] | None) -> dict[str, str]:
    resolved = dict(THEME_COLOURS)
    if variables is None:
        return resolved

    for raw_name, value in variables.items():
        if not isinstance(raw_name, str):
            raise TypeError(f"SVG CSS variable names must be strings, received {raw_name!r}")
        name = raw_name if raw_name.startswith("--") else f"--{raw_name}"
        if not _VARIABLE_NAME.fullmatch(name):
            raise ValueError(f"Invalid SVG CSS variable name: {raw_name!r}")
        if not isinstance(value, str) or not _HEX_COLOUR.fullmatch(value):
            raise ValueError(f"SVG CSS variable {name} must map to a literal six-digit colour")
        resolved[name[2:]] = value.upper()
    return resolved


def _mask_comments_and_strings(css: str) -> str:
    """Mask comments and strings while preserving indexes for bounded parsing."""

    masked = list(css)
    cursor = 0
    while cursor < len(css):
        skipped = _skip_comment_or_string(css, cursor)
        if skipped is not None:
            for index in range(cursor, skipped):
                if css[index] not in "\r\n":
                    masked[index] = " "
            cursor = skipped
        else:
            cursor += 1
    return "".join(masked)


def _top_level_css_rules(css: str):
    """Yield simple top-level selector/body pairs without evaluating CSS."""

    masked = _mask_comments_and_strings(css)
    cursor = 0
    depth = 0
    selector_start = 0
    block_start = 0
    selector = ""
    while cursor < len(masked):
        char = masked[cursor]
        if char == "{":
            if depth == 0:
                selector = masked[selector_start:cursor].strip()
                block_start = cursor + 1
            depth += 1
        elif char == "}":
            if depth == 0:
                raise ValueError("Unmatched CSS closing brace while compiling SVG styles")
            depth -= 1
            if depth == 0:
                yield selector, css[block_start:cursor], masked[block_start:cursor]
                selector_start = cursor + 1
        cursor += 1
    if depth != 0:
        raise ValueError("Unterminated CSS rule while compiling SVG styles")


def _root_custom_properties(css: str, *, context: str) -> dict[str, str]:
    """Read literal custom properties from simple ``:root`` rules only."""

    masked = _mask_comments_and_strings(css)
    all_assignments = list(_CUSTOM_PROPERTY_ASSIGNMENT.finditer(masked))
    root_assignments: list[tuple[str, str]] = []
    for selector, body, masked_body in _top_level_css_rules(css):
        matches = list(_CUSTOM_PROPERTY_ASSIGNMENT.finditer(masked_body))
        if not matches:
            continue
        if selector != ":root":
            raise ValueError(
                f"Scoped SVG CSS custom properties are unsupported in {context}: "
                f"{selector or '<unnamed selector>'}"
            )
        for match in matches:
            # Use the same span against source text so whitespace/case is retained,
            # while comments and strings cannot masquerade as declarations.
            raw_value = body[match.start(2) : match.end(2)].strip()
            if not _HEX_COLOUR.fullmatch(raw_value):
                raise ValueError(
                    f"SVG root custom property {match.group(1)} in {context} must be a "
                    "literal six-digit colour"
                )
            root_assignments.append((match.group(1), raw_value.upper()))

    if len(root_assignments) != len(all_assignments):
        raise ValueError(
            f"Nested or unsupported SVG CSS custom-property declaration in {context}; "
            "only top-level :root colour declarations are supported"
        )
    return {name[2:]: value for name, value in root_assignments}


def _reject_inline_custom_properties(style: str, *, context: str) -> None:
    masked = _mask_comments_and_strings(style)
    if _CUSTOM_PROPERTY_ASSIGNMENT.search(masked):
        raise ValueError(
            f"Inline SVG custom properties are unsupported in {context}; declare literal "
            "theme colours in a top-level :root rule"
        )


def _skip_comment_or_string(value: str, index: int) -> int | None:
    if value.startswith("/*", index):
        end = value.find("*/", index + 2)
        if end < 0:
            raise ValueError("Unterminated CSS comment while compiling SVG styles")
        return end + 2
    if value[index] in ("'", '"'):
        quote = value[index]
        index += 1
        while index < len(value):
            if value[index] == "\\":
                index += 2
            elif value[index] == quote:
                return index + 1
            else:
                index += 1
        raise ValueError("Unterminated CSS string while compiling SVG styles")
    return None


def _variable_call_end(value: str, opening: int) -> int:
    """Return the index after a balanced CSS function call."""

    depth = 1
    index = opening + 1
    while index < len(value):
        skipped = _skip_comment_or_string(value, index)
        if skipped is not None:
            index = skipped
            continue
        char = value[index]
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return index + 1
        index += 1
    raise ValueError("Unterminated CSS var() expression while compiling SVG styles")


def _compile_css_value(
    value: str,
    variables: Mapping[str, str],
    *,
    context: str,
) -> str:
    output: list[str] = []
    cursor = 0
    while cursor < len(value):
        skipped = _skip_comment_or_string(value, cursor)
        if skipped is not None:
            output.append(value[cursor:skipped])
            cursor = skipped
            continue

        match = _VARIABLE_CALL_START.match(value, cursor)
        if match is None:
            output.append(value[cursor])
            cursor += 1
            continue

        if value[match.start() : match.end() - 1].lower() != "var":
            raise ValueError(
                f"Malformed CSS var() function spacing in {context}: "
                f"{value[match.start() : match.end()]!r}"
            )

        opening = match.end() - 1
        call_end = _variable_call_end(value, opening)
        argument = value[match.end() : call_end - 1].strip()
        name_match = _VARIABLE_NAME.fullmatch(argument)
        if name_match is None:
            if "," in argument:
                reason = "fallback values are outside the supported bounded style subset"
            else:
                reason = "expected a single custom-property name such as var(--ink)"
            raise ValueError(
                f"Unsupported CSS var() expression in {context}: {value[match.start() : call_end]!r}; "
                f"{reason}"
            )

        name = name_match.group(1)
        if name not in variables:
            raise ValueError(
                f"Unknown SVG CSS variable --{name} in {context}; add it to the explicit "
                "theme variable mapping"
            )
        replacement = variables[name]
        if not _HEX_COLOUR.fullmatch(replacement):
            raise ValueError(
                f"SVG CSS variable --{name} in {context} is not a literal six-digit colour"
            )
        output.append(replacement.upper())
        cursor = call_end
    return "".join(output)


def _contains_variable_call(value: str) -> bool:
    cursor = 0
    while cursor < len(value):
        skipped = _skip_comment_or_string(value, cursor)
        if skipped is not None:
            cursor = skipped
            continue
        if _VARIABLE_CALL_START.match(value, cursor):
            return True
        cursor += 1
    return False


def has_svg_css_variables(root: ET.Element) -> bool:
    """Return whether SVG style text or attributes contain a real ``var()`` call."""

    for element in root.iter():
        local = _local_name(element.tag) if isinstance(element.tag, str) else ""
        if local == "style" and element.text and _contains_variable_call(element.text):
            return True
        for attribute, value in element.attrib.items():
            attribute_name = _local_name(attribute)
            if attribute_name == "style":
                if _contains_variable_call(value):
                    return True
                continue
            if attribute_name in _NON_CSS_METADATA_ATTRIBUTES or attribute_name.startswith(
                ("data-", "aria-")
            ):
                continue
            if _contains_variable_call(value):
                return True
    return False


def compile_svg_styles(
    root: ET.Element,
    *,
    variables: Mapping[str, str] | None = None,
) -> ET.Element:
    """Compile supported CSS theme variables to literal colours in an SVG tree.

    The function mutates and returns ``root`` to make it convenient at a final
    SVG generation boundary. It only rewrites CSS stylesheet text, inline
    ``style`` attributes and SVG paint presentation attributes. It is safe to
    call more than once. Unknown variables and variable expressions outside the
    supported paint/style surface fail with a contextual ``ValueError``.

    ``variables`` extends the shared theme palette for references without a
    source ``:root`` declaration. Keys may be written with or without their
    CSS ``--`` prefix; values must be literal six-digit colours. Literal values
    declared in source top-level ``:root`` rules take precedence, matching SVG
    cascade intent. Scoped custom properties are rejected rather than flattened
    to a potentially different colour.
    """

    palette = _validate_variables(variables)
    for element in root.iter():
        local = _local_name(element.tag) if isinstance(element.tag, str) else ""
        if local == "style" and element.text:
            palette.update(
                _root_custom_properties(
                    element.text,
                    context=f"<style> under {element.get('id', '<unnamed>')}",
                )
            )
        inline_style = element.get("style")
        if inline_style:
            _reject_inline_custom_properties(
                inline_style,
                context=f"style attribute on {local or 'element'}",
            )

    for element in root.iter():
        local = _local_name(element.tag) if isinstance(element.tag, str) else ""
        if local == "style" and element.text:
            element.text = _compile_css_value(
                element.text,
                palette,
                context=f"<style> under {element.get('id', '<unnamed>')}",
            )

        for attribute, raw_value in tuple(element.attrib.items()):
            attribute_name = _local_name(attribute)
            context = f"attribute {attribute_name!r} on {local or 'element'}"
            if attribute_name == "style" or attribute_name in _PAINT_ATTRIBUTES:
                element.set(
                    attribute,
                    _compile_css_value(raw_value, palette, context=context),
                )
            elif (
                attribute_name not in _NON_CSS_METADATA_ATTRIBUTES
                and not attribute_name.startswith(("data-", "aria-"))
                and _contains_variable_call(raw_value)
            ):
                raise ValueError(
                    f"CSS variable in unsupported SVG attribute {attribute_name!r} "
                    f"on {local or 'element'}"
                )
    return root
