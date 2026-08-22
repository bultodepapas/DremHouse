"""Fail-closed static checks for Dream House SVG publication candidates.

The staged lint profile covers the shared pilot contract: identity, accessibility,
authority, unsafe content, layers, model references, numeric safety, controlled
presentation colours, typed text contrast, required-text preview size, declared safe
bounds and conservative text collisions. Precision normalization and measured geometry
bounds remain explicit follow-on gates.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from dreamhouse.svg.layout import Bounds, estimate_text_bounds
from dreamhouse.svg.theme import APPROVED_PRESENTATION_COLOURS


SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
SVG_TAG = f"{{{SVG_NS}}}svg"
REQUIRED_LAYER_IDS = (
    "layer-background",
    "layer-model",
    "layer-annotations",
    "layer-sheet",
)
REQUIRED_METADATA = (
    "construction_authority",
    "revision",
    "sheet",
    "source",
    "status",
)
REQUIRED_TEXT_ROLES = {
    "dimension",
    "key",
    "level",
    "opening",
    "primary",
    "secondary",
}
NUMERIC_ATTRIBUTES = {
    "cx",
    "cy",
    "font-size",
    "height",
    "opacity",
    "r",
    "rx",
    "ry",
    "stroke-width",
    "width",
    "x",
    "x1",
    "x2",
    "y",
    "y1",
    "y2",
}
NUMBER_PATTERN = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
NUMBER_RE = re.compile(NUMBER_PATTERN)
PLAIN_NUMBER_RE = re.compile(rf"^{NUMBER_PATTERN}(?:px)?$")
SCIENCE_RE = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)[eE][-+]?\d+")
NONFINITE_RE = re.compile(r"(?i)(?:^|[^A-Za-z])(?:nan|[-+]?inf(?:inity)?)(?:$|[^A-Za-z])")
SCALE_RE = re.compile(
    rf"scale\(\s*({NUMBER_PATTERN})(?:[ ,]+({NUMBER_PATTERN}))?\s*\)"
)
URL_RE = re.compile(r"url\(\s*(['\"]?)(.*?)\1\s*\)", re.IGNORECASE)
HEX_COLOUR_RE = re.compile(r"#[0-9A-Fa-f]{6}\b")
CSS_RULE_RE = re.compile(r"([^{}]+)\{([^{}]*)\}", re.DOTALL)
CSS_VAR_RE = re.compile(r"var\(\s*(--[A-Za-z0-9_-]+)\s*\)")


def q(tag: str) -> str:
    return f"{{{SVG_NS}}}{tag}"


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    message: str
    element: str | None = None


def _element_ref(element: ET.Element) -> str:
    tag = element.tag.rsplit("}", 1)[-1] if isinstance(element.tag, str) else "unknown"
    element_id = element.get("id")
    return f"{tag}#{element_id}" if element_id else tag


def _finding(
    findings: list[Finding],
    code: str,
    severity: str,
    message: str,
    element: ET.Element | None = None,
) -> None:
    findings.append(
        Finding(
            code=code,
            severity=severity,
            message=message,
            element=_element_ref(element) if element is not None else None,
        )
    )


def _parse_positive_dimension(value: str | None) -> float | None:
    if value is None:
        return None
    normalized = value.strip()
    if not PLAIN_NUMBER_RE.fullmatch(normalized):
        return None
    number = float(normalized.removesuffix("px"))
    return number if math.isfinite(number) and number > 0 else None


def _parse_viewbox(value: str | None) -> tuple[float, float, float, float] | None:
    if value is None:
        return None
    parts = value.replace(",", " ").split()
    if len(parts) != 4 or not all(NUMBER_RE.fullmatch(part) for part in parts):
        return None
    parsed = tuple(float(part) for part in parts)
    if not all(math.isfinite(number) for number in parsed) or parsed[2] <= 0 or parsed[3] <= 0:
        return None
    return parsed  # type: ignore[return-value]


def _check_root(
    root: ET.Element,
    findings: list[Finding],
) -> tuple[float | None, dict[str, list[ET.Element]]]:
    if root.tag != SVG_TAG:
        _finding(findings, "SVG-R001", "error", "Root element must use the SVG namespace", root)

    width = _parse_positive_dimension(root.get("width"))
    height = _parse_positive_dimension(root.get("height"))
    viewbox = _parse_viewbox(root.get("viewBox"))
    if width is None:
        _finding(findings, "SVG-R002", "error", "Root width must be explicit and positive", root)
    if height is None:
        _finding(findings, "SVG-R003", "error", "Root height must be explicit and positive", root)
    if viewbox is None:
        _finding(
            findings,
            "SVG-R004",
            "error",
            "Root viewBox must contain four finite values",
            root,
        )
    if root.get("role") != "img":
        _finding(findings, "SVG-A001", "error", 'Root role must be "img"', root)

    ids: dict[str, list[ET.Element]] = {}
    for element in root.iter():
        element_id = element.get("id")
        if element_id:
            ids.setdefault(element_id, []).append(element)
    duplicates = sorted(element_id for element_id, elements in ids.items() if len(elements) > 1)
    if duplicates:
        _finding(
            findings,
            "SVG-I001",
            "error",
            f"Duplicate IDs: {', '.join(duplicates[:8])}",
            root,
        )

    labelled_by = root.get("aria-labelledby", "").split()
    if len(labelled_by) != 2:
        _finding(
            findings,
            "SVG-A002",
            "error",
            "aria-labelledby must reference one title and one description",
            root,
        )
    else:
        expected_tags = (q("title"), q("desc"))
        for referenced_id, expected_tag in zip(labelled_by, expected_tags, strict=True):
            referenced = ids.get(referenced_id, [])
            if len(referenced) != 1 or referenced[0].tag != expected_tag:
                _finding(
                    findings,
                    "SVG-A003",
                    "error",
                    f"aria-labelledby reference {referenced_id!r} has the wrong type or count",
                    root,
                )
                continue
            if not " ".join(referenced[0].itertext()).strip():
                _finding(
                    findings,
                    "SVG-A004",
                    "error",
                    f"Referenced {referenced_id!r} must contain accessible text",
                    referenced[0],
                )

    return viewbox[2] if viewbox else width, ids


def _check_metadata(root: ET.Element, findings: list[Finding]) -> dict[str, Any] | None:
    metadata_elements = list(root.findall(q("metadata")))
    if len(metadata_elements) != 1:
        _finding(
            findings,
            "SVG-M001",
            "error",
            "Exactly one direct metadata element is required",
            root,
        )
        return None
    metadata_element = metadata_elements[0]
    try:
        metadata = json.loads(metadata_element.text or "")
    except (json.JSONDecodeError, TypeError) as error:
        _finding(
            findings,
            "SVG-M002",
            "error",
            f"Metadata must be a JSON object: {error}",
            metadata_element,
        )
        return None
    if not isinstance(metadata, dict):
        _finding(findings, "SVG-M003", "error", "Metadata JSON must be an object", metadata_element)
        return None

    missing = [key for key in REQUIRED_METADATA if key not in metadata]
    if missing:
        _finding(
            findings,
            "SVG-M004",
            "error",
            f"Metadata is missing required keys: {', '.join(missing)}",
            metadata_element,
        )
    if metadata.get("construction_authority") is not False:
        _finding(
            findings,
            "SVG-M005",
            "error",
            "construction_authority must be the boolean false",
            metadata_element,
        )
    if root.get("data-construction-authority") != "false":
        _finding(
            findings,
            "SVG-M006",
            "error",
            'Root data-construction-authority must be "false"',
            root,
        )

    for key in ("revision", "sheet", "source", "status"):
        value = metadata.get(key)
        if not isinstance(value, str) or not value.strip():
            _finding(
                findings,
                "SVG-M007",
                "error",
                f"Metadata {key!r} must be a non-empty string",
                metadata_element,
            )

    root_sheet = root.get("data-sheet-id")
    if root_sheet and metadata.get("sheet") != root_sheet:
        _finding(
            findings,
            "SVG-M008",
            "error",
            "Metadata sheet does not match root data-sheet-id",
            metadata_element,
        )
    root_revision = root.get("data-revision")
    if root_revision and metadata.get("revision") != root_revision:
        _finding(
            findings,
            "SVG-M009",
            "error",
            "Metadata revision does not match root data-revision",
            metadata_element,
        )
    if not root.get("data-status"):
        _finding(findings, "SVG-M010", "error", "Root data-status is required", root)
    return metadata


def _check_security(root: ET.Element, findings: list[Finding]) -> None:
    external_references: list[str] = []
    event_attributes: list[str] = []
    unsafe_elements: list[str] = []

    for element in root.iter():
        local_tag = element.tag.rsplit("}", 1)[-1] if isinstance(element.tag, str) else ""
        if local_tag in {"script", "foreignObject"}:
            unsafe_elements.append(_element_ref(element))
        for attribute, value in element.attrib.items():
            local_attribute = attribute.rsplit("}", 1)[-1]
            if local_attribute.lower().startswith("on"):
                event_attributes.append(f"{_element_ref(element)}:{local_attribute}")
            if local_attribute == "href" or attribute == f"{{{XLINK_NS}}}href":
                if value and not value.startswith("#"):
                    external_references.append(value)
            for match in URL_RE.finditer(value):
                target = match.group(2).strip()
                if target and not target.startswith("#"):
                    external_references.append(target)

    for style in root.iter(q("style")):
        css = style.text or ""
        if "@import" in css.lower():
            external_references.append("CSS @import")
        for match in URL_RE.finditer(css):
            target = match.group(2).strip()
            if target and not target.startswith("#"):
                external_references.append(target)

    if unsafe_elements:
        _finding(
            findings,
            "SVG-S001",
            "error",
            f"Unsafe executable/foreign elements: {', '.join(unsafe_elements[:6])}",
            root,
        )
    if event_attributes:
        _finding(
            findings,
            "SVG-S002",
            "error",
            f"Event-handler attributes are forbidden: {', '.join(event_attributes[:6])}",
            root,
        )
    if external_references:
        _finding(
            findings,
            "SVG-S003",
            "error",
            f"External or unsafe references are forbidden: {', '.join(external_references[:6])}",
            root,
        )


def _check_style(root: ET.Element, findings: list[Finding]) -> None:
    styles = [style.text or "" for style in root.iter(q("style"))]
    if not styles or not any("font-family" in css for css in styles):
        _finding(
            findings,
            "SVG-P001",
            "error",
            "An embedded font-family style declaration is required",
            root,
        )
    has_lineweight = any(
        "stroke-width" in element.attrib
        for element in root.iter()
    ) or any("stroke-width" in css for css in styles)
    if not has_lineweight:
        _finding(
            findings,
            "SVG-P002",
            "error",
            "At least one explicit lineweight/profile rule is required",
            root,
        )

    model = root.find(f"{q('g')}[@id='layer-model']")
    has_scaled_model = model is not None and "scale(" in model.get("transform", "")
    has_model_non_scaling = model is not None and any(
        element.get("vector-effect") == "non-scaling-stroke" for element in model.iter()
    )
    has_non_scaling = has_model_non_scaling or any(
        "vector-effect" in css and "non-scaling-stroke" in css for css in styles
    )
    if has_scaled_model and not has_non_scaling:
        _finding(
            findings,
            "SVG-P003",
            "warning",
            "Scaled model has no explicit non-scaling-stroke policy; verify lineweight intent",
            model,
        )


def _check_layers(root: ET.Element, findings: list[Finding]) -> None:
    direct_groups = [element for element in root if element.tag == q("g")]
    by_id: dict[str, list[ET.Element]] = {}
    for group in direct_groups:
        if group.get("id"):
            by_id.setdefault(group.get("id", ""), []).append(group)
    for layer_id in REQUIRED_LAYER_IDS:
        groups = by_id.get(layer_id, [])
        if len(groups) != 1:
            _finding(
                findings,
                "SVG-L001",
                "error",
                f"Required direct semantic layer {layer_id!r} must occur exactly once",
                root,
            )
        elif not groups[0].get("data-layer"):
            _finding(
                findings,
                "SVG-L002",
                "error",
                f"Semantic layer {layer_id!r} requires a data-layer value",
                groups[0],
            )

    model_groups = by_id.get("layer-model", [])
    if len(model_groups) == 1:
        children = list(model_groups[0])
        if not children:
            _finding(findings, "SVG-L003", "error", "Model layer cannot be empty", model_groups[0])
        missing_references = [child for child in children if not child.get("data-model-id")]
        if missing_references:
            _finding(
                findings,
                "SVG-L004",
                "error",
                f"{len(missing_references)} direct model nodes lack stable data-model-id values",
                model_groups[0],
            )


def _check_numbers(
    root: ET.Element,
    findings: list[Finding],
    *,
    max_precision: int,
    strict_precision: bool,
) -> None:
    nonfinite: list[str] = []
    scientific: list[str] = []
    overprecise: list[str] = []
    for element in root.iter():
        for attribute, value in element.attrib.items():
            local_attribute = attribute.rsplit("}", 1)[-1]
            if local_attribute not in NUMERIC_ATTRIBUTES and local_attribute not in {
                "d",
                "points",
                "transform",
                "viewBox",
            }:
                continue
            if NONFINITE_RE.search(value):
                nonfinite.append(f"{_element_ref(element)}:{local_attribute}={value}")
            if SCIENCE_RE.search(value):
                scientific.append(f"{_element_ref(element)}:{local_attribute}={value}")
            for number in NUMBER_RE.findall(value):
                mantissa = number.lower().split("e", 1)[0]
                decimals = mantissa.partition(".")[2]
                if len(decimals.rstrip("0")) > max_precision:
                    overprecise.append(f"{_element_ref(element)}:{local_attribute}={number}")

    if nonfinite:
        _finding(
            findings,
            "SVG-N001",
            "error",
            f"Non-finite numeric values: {', '.join(nonfinite[:6])}",
            root,
        )
    precision_severity = "error" if strict_precision else "warning"
    if scientific:
        _finding(
            findings,
            "SVG-N002",
            precision_severity,
            f"Scientific notation requires canonical serialization: {', '.join(scientific[:6])}",
            root,
        )
    if overprecise:
        _finding(
            findings,
            "SVG-N003",
            precision_severity,
            f"{len(overprecise)} numeric values exceed {max_precision} decimal places; "
            f"examples: {', '.join(overprecise[:4])}",
            root,
        )


def _css_declarations(body: str) -> dict[str, str]:
    declarations: dict[str, str] = {}
    for declaration in body.split(";"):
        name, separator, value = declaration.partition(":")
        if separator and name.strip() and value.strip():
            declarations[name.strip()] = value.strip()
    return declarations


def _parse_stylesheets(
    root: ET.Element,
) -> tuple[dict[str, str], list[tuple[str, dict[str, str]]]]:
    variables: dict[str, str] = {}
    rules: list[tuple[str, dict[str, str]]] = []
    for style in root.iter(q("style")):
        css = style.text or ""
        for selectors, body in CSS_RULE_RE.findall(css):
            declarations = _css_declarations(body)
            for selector in selectors.split(","):
                normalized = selector.strip()
                if normalized == ":root":
                    variables.update(
                        (name, value)
                        for name, value in declarations.items()
                        if name.startswith("--")
                    )
                elif normalized:
                    rules.append((normalized, declarations))
    return variables, rules


def _inline_declarations(element: ET.Element) -> dict[str, str]:
    return _css_declarations(element.get("style", ""))


def _selector_matches(element: ET.Element, selector: str) -> bool:
    local_tag = element.tag.rsplit("}", 1)[-1] if isinstance(element.tag, str) else ""
    if selector == local_tag:
        return True
    if selector.startswith(".") and re.fullmatch(r"\.[A-Za-z0-9_-]+", selector):
        return selector[1:] in element.get("class", "").split()
    return False


def _selector_specificity(selector: str) -> int:
    return 10 if selector.startswith(".") else 1


def _resolve_css_value(value: str | None, variables: dict[str, str]) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    match = CSS_VAR_RE.fullmatch(normalized)
    if match:
        return variables.get(match.group(1))
    return normalized


def _computed_property(
    element: ET.Element,
    property_name: str,
    *,
    parent_map: dict[ET.Element, ET.Element],
    variables: dict[str, str],
    rules: list[tuple[str, dict[str, str]]],
) -> str | None:
    chain = [element]
    while chain[-1] in parent_map:
        chain.append(parent_map[chain[-1]])

    value: str | None = None
    for current in reversed(chain):
        local_value: str | None = None
        if property_name in current.attrib:
            local_value = current.get(property_name)
        matching_rules = [
            (_selector_specificity(selector), index, declarations[property_name])
            for index, (selector, declarations) in enumerate(rules)
            if property_name in declarations and _selector_matches(current, selector)
        ]
        if matching_rules:
            local_value = max(matching_rules)[2]
        inline = _inline_declarations(current)
        if property_name in inline:
            local_value = inline[property_name]
        if local_value is not None:
            value = local_value
    return _resolve_css_value(value, variables)


def _normalise_colour(value: str | None, variables: dict[str, str]) -> str | None:
    resolved = _resolve_css_value(value, variables)
    if resolved is None or not HEX_COLOUR_RE.fullmatch(resolved):
        return None
    return resolved.upper()


def _has_ancestor(
    element: ET.Element,
    *,
    parent_map: dict[ET.Element, ET.Element],
    tag: str | None = None,
    element_id: str | None = None,
) -> bool:
    current: ET.Element | None = element
    while current is not None:
        if tag is not None and current.tag == q(tag):
            return True
        if element_id is not None and current.get("id") == element_id:
            return True
        current = parent_map.get(current)
    return False


def _check_palette(root: ET.Element, findings: list[Finding]) -> dict[str, Any]:
    parent_map = {child: parent for parent in root.iter() for child in parent}
    presentation_literals: list[str] = []
    presentation_unapproved: list[str] = []
    inherited_unapproved: list[str] = []
    colour_attributes = {
        "color",
        "data-contrast-bg",
        "fill",
        "flood-color",
        "stop-color",
        "stroke",
    }

    for element in root.iter():
        inherited_scope = _has_ancestor(
            element,
            parent_map=parent_map,
            element_id="layer-model",
        ) or _has_ancestor(element, parent_map=parent_map, tag="defs")
        if element.tag == q("style"):
            values = HEX_COLOUR_RE.findall(element.text or "")
        else:
            values = []
            for attribute, value in element.attrib.items():
                local_attribute = attribute.rsplit("}", 1)[-1]
                if local_attribute in colour_attributes or local_attribute == "style":
                    values.extend(HEX_COLOUR_RE.findall(value))
        for raw_value in values:
            value = raw_value.upper()
            if inherited_scope:
                if value not in APPROVED_PRESENTATION_COLOURS:
                    inherited_unapproved.append(value)
                continue
            presentation_literals.append(value)
            if value not in APPROVED_PRESENTATION_COLOURS:
                presentation_unapproved.append(value)

    if presentation_unapproved:
        distinct = sorted(set(presentation_unapproved))
        _finding(
            findings,
            "SVG-C001",
            "error",
            f"{len(presentation_unapproved)} presentation colour literals are outside the "
            f"approved palette: {', '.join(distinct[:10])}",
            root,
        )
    if inherited_unapproved:
        distinct = sorted(set(inherited_unapproved))
        _finding(
            findings,
            "SVG-C002",
            "warning",
            f"{len(inherited_unapproved)} inherited model/defs colour literals remain outside "
            f"the presentation palette ({len(distinct)} distinct); examples: "
            f"{', '.join(distinct[:8])}",
            root,
        )

    return {
        "presentation_colour_literals": len(presentation_literals),
        "presentation_colours_declared": len(set(presentation_literals)),
        "presentation_palette_failures": len(presentation_unapproved),
        "inherited_off_palette_literals": len(inherited_unapproved),
        "inherited_off_palette_colours": len(set(inherited_unapproved)),
    }


def _relative_luminance(colour: str) -> float:
    channels = [int(colour[index : index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [
        channel / 12.92
        if channel <= 0.04045
        else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast_ratio(foreground: str, background: str) -> float:
    lighter, darker = sorted(
        (_relative_luminance(foreground), _relative_luminance(background)),
        reverse=True,
    )
    return (lighter + 0.05) / (darker + 0.05)


def _nearest_contrast_background(
    text: ET.Element,
    *,
    parent_map: dict[ET.Element, ET.Element],
    variables: dict[str, str],
) -> str | None:
    current: ET.Element | None = text
    while current is not None:
        if "data-contrast-bg" in current.attrib:
            return _normalise_colour(current.get("data-contrast-bg"), variables)
        current = parent_map.get(current)
    return None


def _font_weight(value: str | None) -> int:
    if value is None or value == "normal":
        return 400
    if value == "bold":
        return 700
    try:
        return int(float(value))
    except ValueError:
        return 400


def _text_example(text: ET.Element) -> str:
    return " ".join(" ".join(piece.split()) for piece in text.itertext())[:60]


def _check_contrast(
    root: ET.Element,
    findings: list[Finding],
    *,
    viewbox_width: float | None,
    preview_width: int,
    normal_contrast: float,
    large_contrast: float,
    large_text_px: float,
    large_bold_text_px: float,
) -> dict[str, Any]:
    parent_map = {child: parent for parent in root.iter() for child in parent}
    variables, rules = _parse_stylesheets(root)
    missing_background: list[str] = []
    invalid_colours: list[str] = []
    failures: list[str] = []
    ratios: list[float] = []
    checked = 0
    model_skipped = 0

    for text, transform_scale, inside_model in _walk_text(root):
        if inside_model or _has_ancestor(text, parent_map=parent_map, tag="defs"):
            model_skipped += 1
            continue
        background = _nearest_contrast_background(
            text,
            parent_map=parent_map,
            variables=variables,
        )
        example = _text_example(text) or _element_ref(text)
        if background is None:
            missing_background.append(example)
            continue
        foreground = _normalise_colour(
            _computed_property(
                text,
                "fill",
                parent_map=parent_map,
                variables=variables,
                rules=rules,
            ),
            variables,
        )
        if foreground is None:
            invalid_colours.append(example)
            continue

        raw_size = text.get("font-size")
        if (
            viewbox_width is None
            or viewbox_width <= 0
            or raw_size is None
            or not PLAIN_NUMBER_RE.fullmatch(raw_size)
        ):
            continue
        effective_size = (
            float(raw_size.removesuffix("px"))
            * transform_scale
            * preview_width
            / viewbox_width
        )
        weight = _font_weight(
            _computed_property(
                text,
                "font-weight",
                parent_map=parent_map,
                variables=variables,
                rules=rules,
            )
        )
        is_large = effective_size >= large_text_px or (
            effective_size >= large_bold_text_px and weight >= 700
        )
        minimum = large_contrast if is_large else normal_contrast
        ratio = _contrast_ratio(foreground, background)
        ratios.append(ratio)
        checked += 1
        if ratio + 1e-9 < minimum:
            failures.append(
                f"{example!r} {ratio:.2f}:1 < {minimum:g}:1 "
                f"({foreground} on {background})"
            )

    if missing_background:
        _finding(
            findings,
            "SVG-C003",
            "error",
            f"{len(missing_background)} presentation texts lack a typed data-contrast-bg; "
            f"examples: {', '.join(missing_background[:5])}",
            root,
        )
    if invalid_colours:
        _finding(
            findings,
            "SVG-C004",
            "error",
            f"{len(invalid_colours)} presentation text colours cannot be resolved to #RRGGBB; "
            f"examples: {', '.join(invalid_colours[:5])}",
            root,
        )
    if failures:
        _finding(
            findings,
            "SVG-C005",
            "error",
            f"{len(failures)} presentation texts fail computed contrast; examples: "
            f"{', '.join(failures[:4])}",
            root,
        )

    return {
        "contrast_text_elements": checked,
        "minimum_contrast_ratio": min(ratios, default=None),
        "contrast_failures": len(failures),
        "untyped_contrast_backgrounds": len(missing_background),
        "unresolved_text_colours": len(invalid_colours),
        "model_text_contrast_skipped": model_skipped,
    }


def _walk_text(
    element: ET.Element,
    *,
    inherited_scale: float = 1.0,
    inherited_hidden: bool = False,
    inside_model: bool = False,
):
    scale = inherited_scale
    for match in SCALE_RE.finditer(element.get("transform", "")):
        scale_x = abs(float(match.group(1)))
        scale_y = abs(float(match.group(2))) if match.group(2) is not None else scale_x
        scale *= min(scale_x, scale_y)
    hidden = (
        inherited_hidden
        or element.get("display") == "none"
        or element.get("visibility") == "hidden"
    )
    in_model = inside_model or element.get("id") == "layer-model"
    if element.tag == q("text") and not hidden:
        yield element, scale, in_model
    for child in element:
        yield from _walk_text(
            child,
            inherited_scale=scale,
            inherited_hidden=hidden,
            inside_model=in_model,
        )


def _check_text(
    root: ET.Element,
    findings: list[Finding],
    *,
    viewbox_width: float | None,
    preview_width: int,
    min_required_text_px: float,
) -> dict[str, Any]:
    missing_size: list[str] = []
    required_small: list[str] = []
    annotation_small: list[str] = []
    model_small: list[str] = []
    micro_small: list[str] = []
    effective_sizes: list[float] = []
    required_count = 0
    if viewbox_width is None or viewbox_width <= 0:
        return {
            "preview_width_px": preview_width,
            "visible_text_elements": 0,
            "minimum_effective_text_px": None,
            "required_text_below_minimum": 0,
            "model_microtext_below_minimum": 0,
        }

    for text, transform_scale, inside_model in _walk_text(root):
        raw_size = text.get("font-size")
        if raw_size is None or not PLAIN_NUMBER_RE.fullmatch(raw_size):
            missing_size.append(_element_ref(text))
            continue
        size = float(raw_size.removesuffix("px")) * transform_scale * preview_width / viewbox_width
        effective_sizes.append(size)
        role = text.get("data-text-role")
        if role in REQUIRED_TEXT_ROLES:
            required_count += 1
        if size >= min_required_text_px:
            continue
        value = " ".join(" ".join(piece.split()) for piece in text.itertext())
        example = value[:60] or _element_ref(text)
        if role in REQUIRED_TEXT_ROLES:
            required_small.append(example)
        elif role == "micro":
            micro_small.append(example)
        elif inside_model:
            model_small.append(example)
        else:
            annotation_small.append(example)

    if missing_size:
        _finding(
            findings,
            "SVG-T001",
            "error",
            f"Visible text requires explicit font-size: {', '.join(missing_size[:6])}",
            root,
        )
    if required_small:
        _finding(
            findings,
            "SVG-T002",
            "error",
            f"{len(required_small)} required-role texts fall below {min_required_text_px:g} px; "
            f"examples: {', '.join(required_small[:5])}",
            root,
        )
    if annotation_small:
        _finding(
            findings,
            "SVG-T003",
            "error",
            f"{len(annotation_small)} sheet/evidence texts fall below {min_required_text_px:g} px; "
            f"examples: {', '.join(annotation_small[:5])}",
            root,
        )
    if model_small or micro_small:
        examples = (model_small + micro_small)[:5]
        _finding(
            findings,
            "SVG-T004",
            "warning",
            f"{len(model_small) + len(micro_small)} inherited model microtexts fall below "
            f"{min_required_text_px:g} px; examples: {', '.join(examples)}",
            root,
        )

    return {
        "preview_width_px": preview_width,
        "visible_text_elements": len(effective_sizes),
        "required_text_elements": required_count,
        "minimum_effective_text_px": min(effective_sizes, default=None),
        "required_text_below_minimum": len(required_small) + len(annotation_small),
        "model_microtext_below_minimum": len(model_small) + len(micro_small),
    }


def _parse_css_number(value: str | None, *, default: float = 0.0) -> float:
    if value is None:
        return default
    normalized = value.strip()
    if not PLAIN_NUMBER_RE.fullmatch(normalized):
        raise ValueError(f"Expected a plain numeric CSS value, received {value!r}")
    number = float(normalized.removesuffix("px"))
    if not math.isfinite(number):
        raise ValueError(f"Expected a finite CSS value, received {value!r}")
    return number


def _minimum_inset(panel: Bounds, safe: Bounds) -> float:
    return min(
        safe.x - panel.x,
        safe.y - panel.y,
        panel.right - safe.right,
        panel.bottom - safe.bottom,
    )


def _check_layout(
    root: ET.Element,
    findings: list[Finding],
    *,
    min_panel_inset: float,
    min_text_gap: float,
    bounds_tolerance: float,
) -> dict[str, Any]:
    """Check typed presentation-text regions with deterministic conservative boxes."""

    parent_map = {child: parent for parent in root.iter() for child in parent}
    variables, rules = _parse_stylesheets(root)
    missing: list[str] = []
    malformed: list[str] = []
    invalid_regions: list[str] = []
    region_conflicts: list[str] = []
    outside: list[str] = []
    unsupported_transforms: list[str] = []
    boxes_by_region: dict[str, list[tuple[ET.Element, Bounds]]] = {}
    region_contracts: dict[str, tuple[str, Bounds, Bounds]] = {}
    panel_insets: list[float] = []
    checked = 0
    rotated_skipped = 0
    presentation_count = 0

    required_attributes = (
        "data-layout-region",
        "data-layout-kind",
        "data-panel-bounds",
        "data-safe-bounds",
    )
    for text, _transform_scale, inside_model in _walk_text(root):
        if inside_model or _has_ancestor(text, parent_map=parent_map, tag="defs"):
            continue
        presentation_count += 1
        example = _text_example(text) or _element_ref(text)
        absent = [name for name in required_attributes if not text.get(name, "").strip()]
        if absent:
            missing.append(f"{example!r} ({', '.join(absent)})")
            continue
        region_id = text.get("data-layout-region", "")
        kind = text.get("data-layout-kind", "")
        try:
            panel = Bounds.parse(text.get("data-panel-bounds", ""))
            safe = Bounds.parse(text.get("data-safe-bounds", ""))
        except ValueError as error:
            malformed.append(f"{example!r} ({error})")
            continue
        if not panel.contains(safe, tolerance=bounds_tolerance):
            invalid_regions.append(f"{example!r} (safe bounds leave panel {region_id!r})")
            continue

        contract = (kind, panel, safe)
        prior_contract = region_contracts.setdefault(region_id, contract)
        if prior_contract != contract:
            region_conflicts.append(f"{region_id!r} at {example!r}")
            continue
        if kind == "panel":
            inset = _minimum_inset(panel, safe)
            panel_insets.append(inset)
            if inset + bounds_tolerance < min_panel_inset:
                invalid_regions.append(
                    f"{example!r} (panel {region_id!r} inset {inset:g} < "
                    f"{min_panel_inset:g})"
                )
                continue

        transform = text.get("transform", "").strip()
        if transform:
            if "rotate(" in transform and text.get("data-layout-policy") == "rotated-skip":
                rotated_skipped += 1
                continue
            unsupported_transforms.append(f"{example!r} ({transform})")
            continue

        try:
            letter_spacing = _parse_css_number(
                _computed_property(
                    text,
                    "letter-spacing",
                    parent_map=parent_map,
                    variables=variables,
                    rules=rules,
                )
            )
            stroke_width = _parse_css_number(
                _computed_property(
                    text,
                    "stroke-width",
                    parent_map=parent_map,
                    variables=variables,
                    rules=rules,
                )
            )
            weight = _font_weight(
                _computed_property(
                    text,
                    "font-weight",
                    parent_map=parent_map,
                    variables=variables,
                    rules=rules,
                )
            )
            box = estimate_text_bounds(
                text,
                letter_spacing=letter_spacing,
                stroke_width=stroke_width,
                bold=weight >= 700,
            )
        except ValueError as error:
            malformed.append(f"{example!r} ({error})")
            continue
        checked += 1
        if not safe.contains(box, tolerance=bounds_tolerance):
            outside.append(
                f"{example!r} in {region_id!r}: box {box.serialize()} outside "
                f"{safe.serialize()}"
            )
        boxes_by_region.setdefault(region_id, []).append((text, box))

    if missing or malformed or unsupported_transforms:
        examples = (missing + malformed + unsupported_transforms)[:5]
        _finding(
            findings,
            "SVG-B001",
            "error",
            f"{len(missing) + len(malformed) + len(unsupported_transforms)} presentation "
            f"texts have missing, malformed or unsupported layout contracts; examples: "
            f"{', '.join(examples)}",
            root,
        )
    if invalid_regions or region_conflicts:
        examples = (invalid_regions + region_conflicts)[:5]
        _finding(
            findings,
            "SVG-B002",
            "error",
            f"{len(invalid_regions) + len(region_conflicts)} layout region declarations are "
            f"inconsistent or breach the panel inset; examples: {', '.join(examples)}",
            root,
        )
    if outside:
        _finding(
            findings,
            "SVG-B003",
            "error",
            f"{len(outside)} axis-aligned presentation text boxes leave their safe bounds; "
            f"examples: {', '.join(outside[:4])}",
            root,
        )

    untyped_collisions: list[str] = []
    typed_collisions = 0
    for region_id, entries in boxes_by_region.items():
        for index, (left_text, left_box) in enumerate(entries):
            for right_text, right_box in entries[index + 1 :]:
                if not left_box.expanded(min_text_gap / 2).intersects(
                    right_box.expanded(min_text_gap / 2)
                ):
                    continue
                left_relation = left_text.get("data-layout-relation", "").strip()
                right_relation = right_text.get("data-layout-relation", "").strip()
                if left_relation and left_relation == right_relation:
                    typed_collisions += 1
                    continue
                untyped_collisions.append(
                    f"{_text_example(left_text)!r} ↔ {_text_example(right_text)!r} "
                    f"in {region_id!r}"
                )
    if untyped_collisions:
        _finding(
            findings,
            "SVG-B004",
            "error",
            f"{len(untyped_collisions)} presentation text pairs breach the "
            f"{min_text_gap:g}-unit gap without a shared typed relation; examples: "
            f"{', '.join(untyped_collisions[:5])}",
            root,
        )

    return {
        "layout_text_elements": presentation_count,
        "layout_axis_aligned_checked": checked,
        "layout_rotated_skipped": rotated_skipped,
        "layout_contract_failures": (
            len(missing)
            + len(malformed)
            + len(invalid_regions)
            + len(region_conflicts)
            + len(unsupported_transforms)
        ),
        "safe_bound_failures": len(outside),
        "untyped_text_collisions": len(untyped_collisions),
        "typed_text_collisions": typed_collisions,
        "minimum_declared_panel_inset": min(panel_insets, default=None),
    }


def lint_file(
    path: Path,
    *,
    preview_width: int = 1400,
    min_required_text_px: float = 8.0,
    normal_contrast: float = 4.5,
    large_contrast: float = 3.0,
    large_text_px: float = 24.0,
    large_bold_text_px: float = 18.66,
    min_panel_inset: float = 8.0,
    min_text_gap: float = 6.0,
    bounds_tolerance: float = 0.5,
    max_precision: int = 6,
    strict_precision: bool = False,
) -> dict[str, Any]:
    findings: list[Finding] = []
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as error:
        _finding(findings, "SVG-X001", "error", f"SVG cannot be parsed: {error}")
        return _file_report(path, findings, metrics={})

    viewbox_width, _ids = _check_root(root, findings)
    _check_metadata(root, findings)
    _check_security(root, findings)
    _check_style(root, findings)
    _check_layers(root, findings)
    palette_metrics = _check_palette(root, findings)
    _check_numbers(
        root,
        findings,
        max_precision=max_precision,
        strict_precision=strict_precision,
    )
    text_metrics = _check_text(
        root,
        findings,
        viewbox_width=viewbox_width,
        preview_width=preview_width,
        min_required_text_px=min_required_text_px,
    )
    contrast_metrics = _check_contrast(
        root,
        findings,
        viewbox_width=viewbox_width,
        preview_width=preview_width,
        normal_contrast=normal_contrast,
        large_contrast=large_contrast,
        large_text_px=large_text_px,
        large_bold_text_px=large_bold_text_px,
    )
    layout_metrics = _check_layout(
        root,
        findings,
        min_panel_inset=min_panel_inset,
        min_text_gap=min_text_gap,
        bounds_tolerance=bounds_tolerance,
    )
    metrics = {**text_metrics, **palette_metrics, **contrast_metrics, **layout_metrics}
    return _file_report(path, findings, metrics=metrics)


def _file_report(
    path: Path,
    findings: list[Finding],
    *,
    metrics: dict[str, Any],
) -> dict[str, Any]:
    errors = sum(finding.severity == "error" for finding in findings)
    warnings = sum(finding.severity == "warning" for finding in findings)
    status = "FAIL" if errors else ("WARN" if warnings else "PASS")
    return {
        "path": path.as_posix(),
        "status": status,
        "errors": errors,
        "warnings": warnings,
        "metrics": metrics,
        "findings": [asdict(finding) for finding in findings],
    }


def lint_paths(
    paths: list[Path],
    *,
    preview_width: int = 1400,
    min_required_text_px: float = 8.0,
    normal_contrast: float = 4.5,
    large_contrast: float = 3.0,
    large_text_px: float = 24.0,
    large_bold_text_px: float = 18.66,
    min_panel_inset: float = 8.0,
    min_text_gap: float = 6.0,
    bounds_tolerance: float = 0.5,
    max_precision: int = 6,
    strict_precision: bool = False,
) -> dict[str, Any]:
    files = [
        lint_file(
            path,
            preview_width=preview_width,
            min_required_text_px=min_required_text_px,
            normal_contrast=normal_contrast,
            large_contrast=large_contrast,
            large_text_px=large_text_px,
            large_bold_text_px=large_bold_text_px,
            min_panel_inset=min_panel_inset,
            min_text_gap=min_text_gap,
            bounds_tolerance=bounds_tolerance,
            max_precision=max_precision,
            strict_precision=strict_precision,
        )
        for path in paths
    ]
    errors = sum(file["errors"] for file in files)
    warnings = sum(file["warnings"] for file in files)
    return {
        "schema_version": 3,
        "profile": {
            "bounds_tolerance": bounds_tolerance,
            "large_bold_text_px": large_bold_text_px,
            "large_contrast": large_contrast,
            "large_text_px": large_text_px,
            "max_precision": max_precision,
            "min_panel_inset": min_panel_inset,
            "min_required_text_px": min_required_text_px,
            "min_text_gap": min_text_gap,
            "normal_contrast": normal_contrast,
            "preview_width_px": preview_width,
            "strict_precision": strict_precision,
        },
        "summary": {
            "files": len(files),
            "passed": sum(file["status"] == "PASS" for file in files),
            "warned": sum(file["status"] == "WARN" for file in files),
            "failed": sum(file["status"] == "FAIL" for file in files),
            "errors": errors,
            "warnings": warnings,
        },
        "files": files,
    }


def markdown_report(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# SVG static lint report",
        "",
        (
            f"**Files:** {summary['files']} · **Passed:** {summary['passed']} · "
            f"**Warnings:** {summary['warned']} · **Failed:** {summary['failed']} · "
            f"**Errors:** {summary['errors']} · **Warning findings:** {summary['warnings']}"
        ),
        "",
        "| File | Status | Errors | Warnings | Minimum text | Minimum contrast | "
        "Bounds / collisions |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for file in report["files"]:
        minimum = file["metrics"].get("minimum_effective_text_px")
        minimum_label = "—" if minimum is None else f"{minimum:.2f} px"
        contrast = file["metrics"].get("minimum_contrast_ratio")
        contrast_label = "—" if contrast is None else f"{contrast:.2f}:1"
        path = str(file["path"]).replace("|", "\\|")
        bounds_label = (
            f"{file['metrics'].get('safe_bound_failures', 0)} / "
            f"{file['metrics'].get('untyped_text_collisions', 0)}"
        )
        lines.append(
            f"| `{path}` | {file['status']} | {file['errors']} | {file['warnings']} | "
            f"{minimum_label} | {contrast_label} | {bounds_label} |"
        )

    for file in report["files"]:
        if not file["findings"]:
            continue
        lines.extend(["", f"## {file['path']}", ""])
        for finding in file["findings"]:
            location = f" · `{finding['element']}`" if finding.get("element") else ""
            lines.append(
                f"- **{finding['severity'].upper()} {finding['code']}**{location}: "
                f"{finding['message']}"
            )
    return "\n".join(lines) + "\n"


def exit_code(report: dict[str, Any], *, warnings_as_errors: bool = False) -> int:
    summary = report["summary"]
    return int(bool(summary["errors"] or (warnings_as_errors and summary["warnings"])))


def _expand_paths(arguments: list[Path]) -> list[Path]:
    expanded: list[Path] = []
    for path in arguments:
        if path.is_dir():
            expanded.extend(sorted(path.glob("*.svg")))
        else:
            expanded.append(path)
    unique: list[Path] = []
    seen: set[Path] = set()
    for path in expanded:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(path)
    return unique


def _write_optional(path: Path | None, value: str) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path, help="SVG files or flat SVG directories")
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--preview-width", type=int, default=1400)
    parser.add_argument("--min-required-text-px", type=float, default=8.0)
    parser.add_argument("--normal-contrast", type=float, default=4.5)
    parser.add_argument("--large-contrast", type=float, default=3.0)
    parser.add_argument("--large-text-px", type=float, default=24.0)
    parser.add_argument("--large-bold-text-px", type=float, default=18.66)
    parser.add_argument("--min-panel-inset", type=float, default=8.0)
    parser.add_argument("--min-text-gap", type=float, default=6.0)
    parser.add_argument("--bounds-tolerance", type=float, default=0.5)
    parser.add_argument("--max-precision", type=int, default=6)
    parser.add_argument("--strict-precision", action="store_true")
    parser.add_argument("--warnings-as-errors", action="store_true")
    arguments = parser.parse_args(argv)

    paths = _expand_paths(arguments.paths)
    if not paths:
        parser.error("No SVG files found")
    report = lint_paths(
        paths,
        preview_width=arguments.preview_width,
        min_required_text_px=arguments.min_required_text_px,
        normal_contrast=arguments.normal_contrast,
        large_contrast=arguments.large_contrast,
        large_text_px=arguments.large_text_px,
        large_bold_text_px=arguments.large_bold_text_px,
        min_panel_inset=arguments.min_panel_inset,
        min_text_gap=arguments.min_text_gap,
        bounds_tolerance=arguments.bounds_tolerance,
        max_precision=arguments.max_precision,
        strict_precision=arguments.strict_precision,
    )
    json_text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    markdown_text = markdown_report(report)
    _write_optional(arguments.json_output, json_text)
    _write_optional(arguments.markdown_output, markdown_text)
    sys.stdout.write(json_text if arguments.format == "json" else markdown_text)
    return exit_code(report, warnings_as_errors=arguments.warnings_as_errors)


if __name__ == "__main__":
    raise SystemExit(main())
