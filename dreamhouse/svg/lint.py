"""Fail-closed static checks for Dream House SVG publication candidates.

The first lint profile covers the shared pilot contract: document identity, accessibility,
metadata and authority, unsafe content, semantic layers, stable model references, numeric
safety and required-text preview size.  Precision normalization, palette/contrast, measured
bounds and collision checks remain explicit follow-on gates.
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


def lint_file(
    path: Path,
    *,
    preview_width: int = 1400,
    min_required_text_px: float = 8.0,
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
    _check_numbers(
        root,
        findings,
        max_precision=max_precision,
        strict_precision=strict_precision,
    )
    metrics = _check_text(
        root,
        findings,
        viewbox_width=viewbox_width,
        preview_width=preview_width,
        min_required_text_px=min_required_text_px,
    )
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
    max_precision: int = 6,
    strict_precision: bool = False,
) -> dict[str, Any]:
    files = [
        lint_file(
            path,
            preview_width=preview_width,
            min_required_text_px=min_required_text_px,
            max_precision=max_precision,
            strict_precision=strict_precision,
        )
        for path in paths
    ]
    errors = sum(file["errors"] for file in files)
    warnings = sum(file["warnings"] for file in files)
    return {
        "schema_version": 1,
        "profile": {
            "max_precision": max_precision,
            "min_required_text_px": min_required_text_px,
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
        "| File | Status | Errors | Warnings | Minimum effective text |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for file in report["files"]:
        minimum = file["metrics"].get("minimum_effective_text_px")
        minimum_label = "—" if minimum is None else f"{minimum:.2f} px"
        path = str(file["path"]).replace("|", "\\|")
        lines.append(
            f"| `{path}` | {file['status']} | {file['errors']} | {file['warnings']} | "
            f"{minimum_label} |"
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
