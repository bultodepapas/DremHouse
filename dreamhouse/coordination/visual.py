"""Deterministic, read-only PNG exports for coordination SVGs.

The renderer accepts SVG text and explicit local font files. It does not open SVG paths,
resolve external resources, or modify the SVG input. These PNGs are visual review evidence;
they do not add dimensional or construction authority.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import io
import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import unquote
from xml.etree import ElementTree as ET

from dreamhouse.svg.style import has_svg_css_variables

XML_NS = "http://www.w3.org/XML/1998/namespace"

CONTACT_SHEET_NAME = "contact_sheet.png"
CONTACT_COLUMNS = 2
CONTACT_GUTTER = 24
CONTACT_HEADER_HEIGHT = 76
CONTACT_LABEL_HEIGHT = 62
CONTACT_BACKGROUND = "#F4F1E9"
CONTACT_PANEL = "#FFFFFF"
CONTACT_RULE = "#CBD4D2"
CONTACT_INK = "#172A32"
CONTACT_MUTED = "#52636A"
CONTACT_TITLE = "D-084 coordination visual review"
URL_RE = re.compile(r"url\(\s*(['\"]?)(.*?)\1\s*\)", re.IGNORECASE)
CSS_IMPORT_RE = re.compile(r"@import\b", re.IGNORECASE)
CSS_FONT_FACE_RE = re.compile(r"@font-face\b", re.IGNORECASE)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_json(data: Mapping[str, Any]) -> bytes:
    return json.dumps(
        data,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


def _presentation_versions() -> dict[str, str]:
    try:
        import resvg_py  # noqa: F401
        from PIL import Image, features  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(
            "Visual PNG export requires the presentation dependencies. "
            "Install with: pip install -e '.[presentation]'"
        ) from exc

    versions: dict[str, str] = {}
    for package in ("resvg-py", "Pillow"):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError as exc:
            raise RuntimeError(
                f"Visual PNG export requires installed package metadata for {package}. "
                "Install with: pip install -e '.[presentation]'"
            ) from exc
    from PIL import features

    versions["FreeType"] = features.version_module("freetype2") or "unavailable"
    return versions


def _font_records(font_paths: Sequence[str | Path]) -> tuple[list[Path], list[dict[str, Any]]]:
    if isinstance(font_paths, (str, bytes)) or not font_paths:
        raise ValueError("At least one explicit font file is required for visual export")

    resolved: list[Path] = []
    records: list[dict[str, Any]] = []
    for index, value in enumerate(font_paths):
        path = Path(value).expanduser()
        if not path.is_file():
            raise FileNotFoundError(f"Declared visual font does not exist: {path}")
        absolute = path.resolve()
        contents = absolute.read_bytes()
        if not contents:
            raise ValueError(f"Declared visual font is empty: {path}")
        resolved.append(absolute)
        records.append(
            {
                "index": index,
                "file_name": absolute.name,
                "sha256": _sha256(contents),
                "size_bytes": len(contents),
            }
        )
    return resolved, records


def _validate_fonts(font_paths: Sequence[Path]) -> None:
    from PIL import ImageFont

    for path in font_paths:
        try:
            ImageFont.truetype(str(path), size=12)
        except OSError as exc:
            raise ValueError(
                f"Declared visual font is not a supported font file: {path.name}"
            ) from exc


def visual_configuration(
    font_paths: Sequence[str | Path],
    width_px: int = 1400,
) -> dict[str, Any]:
    """Return the stable renderer/font configuration used as a build dependency.

    Paths are validated and hashed, but absolute filesystem locations are omitted so an
    identical checked-in font set has the same fingerprint in different workspaces.
    """

    if isinstance(width_px, bool) or not isinstance(width_px, int) or width_px <= 0:
        raise ValueError("Visual render width must be a positive integer")
    resolved_fonts, fonts = _font_records(font_paths)
    versions = _presentation_versions()
    _validate_fonts(resolved_fonts)
    configuration: dict[str, Any] = {
        "schema_version": 1,
        "renderer": "resvg-py",
        "renderer_version": versions["resvg-py"],
        "rasterizer": "Pillow",
        "rasterizer_version": versions["Pillow"],
        "freetype_version": versions["FreeType"],
        "width_px": width_px,
        "font_files": fonts,
        "font_policy": "explicit font files only; system fonts disabled",
        "skip_system_fonts": True,
        "default_font_family": "IBM Plex Sans",
        "text_rendering": "optimize_legibility",
        "image_rendering": "optimize_quality",
        "contact_sheet": {
            "title": CONTACT_TITLE,
            "columns": CONTACT_COLUMNS,
            "gutter_px": CONTACT_GUTTER,
            "label_height_px": CONTACT_LABEL_HEIGHT,
            "label_font_file_index": 0,
        },
    }
    configuration["fingerprint"] = _sha256(_canonical_json(configuration))
    return configuration


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _is_data_image(reference: str) -> bool:
    lowered = reference.lower()
    return lowered.startswith("data:image/")


def _validate_reference(reference: str, *, context: str) -> None:
    value = reference.strip()
    if value.startswith("#") or _is_data_image(value):
        return
    raise ValueError(f"External SVG resource references are not allowed ({context}: {value!r})")


def _validate_css(value: str, *, context: str) -> None:
    if CSS_IMPORT_RE.search(value):
        raise ValueError(f"CSS imports are not allowed in visual SVGs ({context})")
    if CSS_FONT_FACE_RE.search(value):
        raise ValueError(
            "Embedded or linked font declarations are not allowed; "
            f"use declared font files ({context})"
        )
    for match in URL_RE.finditer(value):
        _validate_reference(match.group(2), context=context)


def _parse_svg(svg_text: str, *, name: str) -> ET.Element:
    if re.search(r"<!DOCTYPE\b|<!ENTITY\b", svg_text, re.IGNORECASE):
        raise ValueError(f"SVG document types and entities are not allowed: {name}")
    try:
        root = ET.fromstring(svg_text)
    except ET.ParseError as exc:
        raise ValueError(f"Invalid SVG text for {name}: {exc}") from exc
    if _local_name(root.tag) != "svg":
        raise ValueError(f"Visual input {name} must have an <svg> root element")

    if has_svg_css_variables(root):
        raise ValueError(f"Compile SVG CSS variables before raster export ({name})")

    for element in root.iter():
        local = _local_name(element.tag)
        if local in {"script", "foreignObject"}:
            raise ValueError(f"Active or foreign content is not allowed in visual SVGs: {name}")
        for attribute, value in element.attrib.items():
            attr_local = _local_name(attribute)
            if attribute == f"{{{XML_NS}}}base":
                raise ValueError(f"xml:base is not allowed in visual SVGs: {name}")
            if attr_local == "href":
                # A relative SVG navigation link is not a fetched image/font resource.
                # The connected view contract validates its semantic/DOM destination.
                target_path, separator, fragment = value.partition("#")
                if unquote(target_path) != target_path:
                    raise ValueError(f"Encoded SVG navigation paths are not allowed: {name}")
                if local == "a" and target_path and separator and fragment:
                    if target_path != "index.html" or not re.fullmatch(
                        r"(?:project-finding-register|html-finding-[0-9]+)", fragment
                    ):
                        _input_name(target_path)
                else:
                    _validate_reference(value, context=f"{name} @{attr_local}")
            if attr_local == "style":
                _validate_css(value, context=f"{name} @{attr_local}")
            else:
                for match in URL_RE.finditer(value):
                    _validate_reference(match.group(2), context=f"{name} @{attr_local}")
        if local == "style" and element.text:
            _validate_css(element.text, context=f"{name} <style>")
    return root


def _input_name(value: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("SVG input names must be non-empty relative paths")
    if "\\" in value:
        raise ValueError(f"SVG input paths must use forward slashes: {value!r}")
    if unquote(value) != value:
        raise ValueError(f"Encoded SVG artifact paths are not allowed: {value!r}")
    if ":" in value:
        raise ValueError(f"SVG input paths cannot contain a URI scheme: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or path == PurePosixPath("."):
        raise ValueError(f"SVG input paths must stay within the artifact root: {value!r}")
    if path.suffix.lower() != ".svg":
        raise ValueError(f"Visual input must be an SVG file: {value!r}")
    return path.as_posix()


def _element_title(root: ET.Element, fallback: str) -> str:
    title = next((node for node in root.iter() if _local_name(node.tag) == "title"), None)
    if title is None or not title.itertext():
        return fallback
    return " ".join("".join(title.itertext()).split()) or fallback


def _fit_label(value: str, *, width: int, font: Any) -> str:
    measure = font.getlength
    if measure(value) <= width:
        return value
    suffix = "…"
    shortened = value
    while shortened and measure(shortened + suffix) > width:
        shortened = shortened[:-1]
    return shortened.rstrip() + suffix


def _render_png(
    svg_text: str,
    *,
    width_px: int,
    font_paths: Sequence[Path],
    configuration: Mapping[str, Any],
) -> tuple[bytes, tuple[int, int]]:
    import resvg_py
    from PIL import Image, PngImagePlugin

    raw_png = resvg_py.svg_to_bytes(
        svg_string=svg_text,
        width=width_px,
        skip_system_fonts=True,
        font_files=[str(path) for path in font_paths],
        font_family="IBM Plex Sans",
        text_rendering="optimize_legibility",
        image_rendering="optimize_quality",
    )
    try:
        with Image.open(io.BytesIO(raw_png)) as opened:
            opened.load()
            size = opened.size
            if size[0] != width_px:
                raise ValueError(f"Renderer returned width {size[0]} px; expected {width_px} px")
            pixels = opened.convert("RGBA")
    except Exception as exc:
        if isinstance(exc, ValueError):
            raise
        raise ValueError(f"resvg-py returned an invalid PNG: {exc}") from exc

    metadata = PngImagePlugin.PngInfo()
    metadata.add_text("Source-SHA256", _sha256(svg_text.encode("utf-8")))
    metadata.add_text("Configuration-Fingerprint", str(configuration["fingerprint"]))
    metadata.add_text("Review-Purpose", "coordination review; no construction authority")
    output = io.BytesIO()
    pixels.save(output, format="PNG", optimize=False, compress_level=9, pnginfo=metadata)
    return output.getvalue(), size


def _contact_sheet(
    entries: Sequence[tuple[str, str, bytes]],
    *,
    width_px: int,
    font_path: Path,
) -> tuple[bytes, tuple[int, int]]:
    from PIL import Image, ImageDraw, ImageFont, PngImagePlugin

    if not entries:
        raise ValueError("A contact sheet requires at least one rendered SVG")
    font_title = ImageFont.truetype(str(font_path), size=22)
    font_subtitle = ImageFont.truetype(str(font_path), size=15)
    font_label = ImageFont.truetype(str(font_path), size=18)
    font_meta = ImageFont.truetype(str(font_path), size=14)

    decoded: list[tuple[str, str, Image.Image]] = []
    for name, title, content in entries:
        with Image.open(io.BytesIO(content)) as opened:
            opened.load()
            decoded.append((name, title, opened.convert("RGB")))

    rows = (len(decoded) + CONTACT_COLUMNS - 1) // CONTACT_COLUMNS
    row_heights = [
        max(
            image.height
            for _, _, image in decoded[row * CONTACT_COLUMNS : (row + 1) * CONTACT_COLUMNS]
        )
        for row in range(rows)
    ]
    row_origins = []
    next_row_y = CONTACT_HEADER_HEIGHT
    for preview_height in row_heights:
        row_origins.append(next_row_y)
        next_row_y += CONTACT_LABEL_HEIGHT + preview_height + CONTACT_GUTTER
    sheet_width = CONTACT_GUTTER + CONTACT_COLUMNS * (width_px + CONTACT_GUTTER)
    sheet_height = next_row_y
    sheet = Image.new("RGB", (sheet_width, sheet_height), CONTACT_BACKGROUND)
    draw = ImageDraw.Draw(sheet)
    draw.text((CONTACT_GUTTER, 10), CONTACT_TITLE, fill=CONTACT_INK, font=font_title)
    draw.text(
        (CONTACT_GUTTER, 43),
        f"{len(decoded)} SVGs · {width_px} px previews · REVIEW EVIDENCE ONLY",
        fill=CONTACT_MUTED,
        font=font_subtitle,
    )

    for index, (name, title, image) in enumerate(decoded):
        column = index % CONTACT_COLUMNS
        row = index // CONTACT_COLUMNS
        x = CONTACT_GUTTER + column * (width_px + CONTACT_GUTTER)
        y = row_origins[row]
        cell_height = CONTACT_LABEL_HEIGHT + row_heights[row]
        draw.rounded_rectangle(
            (x, y, x + width_px - 1, y + cell_height - 1),
            radius=5,
            fill=CONTACT_PANEL,
            outline=CONTACT_RULE,
        )
        title_line = _fit_label(title, width=width_px - 32, font=font_label)
        file_line = _fit_label(name, width=width_px - 32, font=font_meta)
        draw.text((x + 16, y + 4), title_line, fill=CONTACT_INK, font=font_label)
        draw.text((x + 16, y + 31), file_line, fill=CONTACT_MUTED, font=font_meta)
        sheet.paste(image, (x, y + CONTACT_LABEL_HEIGHT))

    metadata = PngImagePlugin.PngInfo()
    metadata.add_text("Included-SVG-Count", str(len(decoded)))
    metadata.add_text("Contact-Sheet-Title", CONTACT_TITLE)
    output = io.BytesIO()
    sheet.save(output, format="PNG", optimize=False, compress_level=9, pnginfo=metadata)
    return output.getvalue(), (sheet_width, sheet_height)


def _verified_configuration_fingerprint(configuration: Mapping[str, Any], *, label: str) -> str:
    if not isinstance(configuration, Mapping):
        raise TypeError(f"{label} visual configuration must be a mapping")
    fingerprint = configuration.get("fingerprint")
    payload = {key: value for key, value in configuration.items() if key != "fingerprint"}
    expected = _sha256(_canonical_json(payload))
    if not isinstance(fingerprint, str) or fingerprint != expected:
        raise ValueError(f"{label} visual configuration fingerprint is missing or invalid")
    return fingerprint


def _png_inputs(files: Mapping[str, bytes], *, label: str) -> tuple[dict[str, bytes], list[str]]:
    if not isinstance(files, Mapping):
        raise TypeError(f"{label} visual PNG inputs must be a mapping")
    normalized: dict[str, bytes] = {}
    contact_sheets: list[str] = []
    for raw_name, contents in files.items():
        if not isinstance(raw_name, str) or not raw_name:
            raise ValueError(f"{label} PNG names must be non-empty relative paths")
        if "\\" in raw_name:
            raise ValueError(f"{label} PNG paths must use forward slashes: {raw_name!r}")
        path = PurePosixPath(raw_name)
        if path.is_absolute() or ".." in path.parts or path == PurePosixPath("."):
            raise ValueError(f"{label} PNG paths must stay within the artifact root: {raw_name!r}")
        if path.suffix.lower() != ".png":
            raise ValueError(f"{label} visual input must be a PNG file: {raw_name!r}")
        name = path.as_posix()
        if not isinstance(contents, bytes):
            raise TypeError(f"{label} PNG input {name} must be bytes")
        if path.name == CONTACT_SHEET_NAME:
            contact_sheets.append(name)
            continue
        if name in normalized:
            raise ValueError(f"Duplicate normalized {label} PNG path: {name}")
        normalized[name] = contents
    return normalized, sorted(contact_sheets)


def _open_png(contents: bytes, *, name: str, label: str) -> tuple[Any, tuple[int, int]]:
    from PIL import Image

    try:
        with Image.open(io.BytesIO(contents)) as opened:
            if opened.format != "PNG":
                raise ValueError(f"{label} visual input is not a PNG file: {name}")
            opened.load()
            image = opened.convert("RGBA")
            return image, image.size
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"Unable to read {label} PNG {name}: {exc}") from exc


def _changed_pixels(current: Any, baseline: Any) -> tuple[int, list[int] | None, Any]:
    from PIL import ImageChops

    channel_delta = ImageChops.difference(current, baseline)
    red, green, blue, alpha = channel_delta.split()
    delta = ImageChops.lighter(ImageChops.lighter(red, green), ImageChops.lighter(blue, alpha))
    changed = delta.point(lambda value: 255 if value else 0)
    histogram = changed.histogram()
    changed_count = sum(histogram[1:])
    bounds = changed.getbbox()
    return changed_count, list(bounds) if bounds else None, changed


def _difference_png(
    changed: Any,
    *,
    baseline_sha256: str,
    current_sha256: str,
) -> bytes:
    from PIL import Image, PngImagePlugin

    difference = Image.new("RGB", changed.size, "white")
    red = Image.new("RGB", changed.size, "#D84032")
    difference.paste(red, mask=changed)
    metadata = PngImagePlugin.PngInfo()
    metadata.add_text("Comparison-Method", "exact pixel difference; changed pixels red")
    metadata.add_text("Baseline-PNG-SHA256", baseline_sha256)
    metadata.add_text("Current-PNG-SHA256", current_sha256)
    output = io.BytesIO()
    difference.save(output, format="PNG", optimize=False, compress_level=9, pnginfo=metadata)
    return output.getvalue()


def compare_visuals(
    current_pngs: Mapping[str, bytes],
    baseline_pngs: Mapping[str, bytes],
    *,
    current_configuration: Mapping[str, Any],
    baseline_configuration: Mapping[str, Any],
) -> tuple[dict[str, bytes], dict[str, Any]]:
    """Compare exact pixels under a verified matching renderer/font configuration.

    Contact sheets are omitted because they are summaries of the per-view images. Images
    are never resized or thresholded. The report describes visual evidence and does not
    decide whether a geometric or engineering change is acceptable.
    """

    current_fingerprint = _verified_configuration_fingerprint(
        current_configuration, label="Current"
    )
    baseline_fingerprint = _verified_configuration_fingerprint(
        baseline_configuration, label="Baseline"
    )
    current, current_sheets = _png_inputs(current_pngs, label="Current")
    baseline, baseline_sheets = _png_inputs(baseline_pngs, label="Baseline")
    current_images = {
        name: _open_png(contents, name=name, label="Current") for name, contents in current.items()
    }
    baseline_images = {
        name: _open_png(contents, name=name, label="Baseline")
        for name, contents in baseline.items()
    }

    same_configuration = current_fingerprint == baseline_fingerprint
    artifacts: dict[str, bytes] = {}
    source_report: dict[str, dict[str, Any]] = {}
    counts = {
        "pixel_identical": 0,
        "pixel_changed": 0,
        "added": 0,
        "removed": 0,
        "dimension_mismatch": 0,
        "configuration_mismatch": 0,
    }

    for name in sorted(set(current) | set(baseline)):
        current_content = current.get(name)
        baseline_content = baseline.get(name)
        if baseline_content is None:
            _current_image, current_size = current_images[name]
            source_report[name] = {
                "status": "added",
                "current_png_sha256": _sha256(current_content or b""),
                "current_dimensions_px": list(current_size),
            }
            counts["added"] += 1
            continue
        if current_content is None:
            _baseline_image, baseline_size = baseline_images[name]
            source_report[name] = {
                "status": "removed",
                "baseline_png_sha256": _sha256(baseline_content),
                "baseline_dimensions_px": list(baseline_size),
            }
            counts["removed"] += 1
            continue

        current_image, current_size = current_images[name]
        baseline_image, baseline_size = baseline_images[name]
        record: dict[str, Any] = {
            "current_png_sha256": _sha256(current_content),
            "baseline_png_sha256": _sha256(baseline_content),
            "current_dimensions_px": list(current_size),
            "baseline_dimensions_px": list(baseline_size),
        }
        if not same_configuration:
            record["status"] = "configuration_mismatch"
            counts["configuration_mismatch"] += 1
        elif current_size != baseline_size:
            record["status"] = "dimension_mismatch"
            counts["dimension_mismatch"] += 1
        else:
            changed_count, bounds, changed_mask = _changed_pixels(current_image, baseline_image)
            record["total_pixels"] = current_size[0] * current_size[1]
            record["changed_pixels"] = changed_count
            record["changed_pixel_bounds_xyxy"] = bounds
            if changed_count:
                record["status"] = "pixel_changed"
                difference_name = (
                    PurePosixPath("visual-diff") / PurePosixPath(name).with_suffix(".diff.png")
                ).as_posix()
                artifacts[difference_name] = _difference_png(
                    changed_mask,
                    baseline_sha256=record["baseline_png_sha256"],
                    current_sha256=record["current_png_sha256"],
                )
                record["difference_image"] = difference_name
                counts["pixel_changed"] += 1
            else:
                record["status"] = "pixel_identical"
                record["difference_image"] = None
                counts["pixel_identical"] += 1
        source_report[name] = record

    if not same_configuration:
        comparison_status = "incompatible_configuration"
    elif counts["dimension_mismatch"]:
        comparison_status = "partially_compared_dimension_mismatch"
    else:
        comparison_status = "compared"
    report = {
        "schema_version": 1,
        "status": comparison_status,
        "comparison_method": "exact RGBA pixel comparison; no threshold; no image resizing",
        "automatic_acceptance": False,
        "construction_authority": False,
        "configuration": {
            "matches": same_configuration,
            "current_fingerprint": current_fingerprint,
            "baseline_fingerprint": baseline_fingerprint,
        },
        "counts": counts,
        "sources": source_report,
        "skipped_contact_sheets": {
            "current": current_sheets,
            "baseline": baseline_sheets,
        },
    }
    return artifacts, report


def render_visuals(
    files: Mapping[str, str],
    *,
    font_paths: Sequence[str | Path],
    width_px: int = 1400,
) -> tuple[dict[str, bytes], dict[str, Any]]:
    """Render SVG text inputs to PNG artifacts and return their machine-readable provenance.

    The output mapping contains one PNG beside each SVG path and a `contact_sheet.png`.
    No path is written. Every source SVG is validated in memory and passed unchanged to
    resvg; referenced local files, fonts discovered from the host, and network resources
    are not loaded.
    """

    if not isinstance(files, Mapping) or not files:
        raise ValueError("Visual export requires at least one SVG text input")
    if isinstance(width_px, bool) or not isinstance(width_px, int) or width_px <= 0:
        raise ValueError("Visual render width must be a positive integer")

    configuration = visual_configuration(font_paths, width_px)
    resolved_fonts, _font_data = _font_records(font_paths)
    normalized: dict[str, tuple[str, ET.Element]] = {}
    output_names: set[str] = set()
    for raw_name, svg_text in files.items():
        name = _input_name(raw_name)
        if name in normalized:
            raise ValueError(f"Duplicate normalized SVG input path: {name}")
        if not isinstance(svg_text, str):
            raise TypeError(f"SVG input {name} must be text")
        if not svg_text.strip():
            raise ValueError(f"SVG input {name} is empty")
        root = _parse_svg(svg_text, name=name)
        png_name = PurePosixPath(name).with_suffix(".png").as_posix()
        if png_name in output_names:
            raise ValueError(f"Duplicate visual output path: {png_name}")
        normalized[name] = (svg_text, root)
        output_names.add(png_name)
    if CONTACT_SHEET_NAME in output_names:
        raise ValueError(f"Reserved visual output path: {CONTACT_SHEET_NAME}")

    artifacts: dict[str, bytes] = {}
    entries: list[tuple[str, str, bytes]] = []
    output_records: dict[str, dict[str, Any]] = {}
    for name in sorted(normalized):
        svg_text, root = normalized[name]
        png, size = _render_png(
            svg_text,
            width_px=width_px,
            font_paths=resolved_fonts,
            configuration=configuration,
        )
        png_name = PurePosixPath(name).with_suffix(".png").as_posix()
        artifacts[png_name] = png
        svg_bytes = svg_text.encode("utf-8")
        output_records[name] = {
            "source_sha256": _sha256(svg_bytes),
            "output": png_name,
            "output_sha256": _sha256(png),
            "width_px": size[0],
            "height_px": size[1],
        }
        entries.append((name, _element_title(root, PurePosixPath(name).stem), png))

    contact_png, contact_size = _contact_sheet(
        entries,
        width_px=width_px,
        font_path=resolved_fonts[0],
    )
    artifacts[CONTACT_SHEET_NAME] = contact_png
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "status": "visual review evidence",
        "construction_authority": False,
        "geometry_mutated": False,
        "configuration": configuration,
        "sources": output_records,
        "contact_sheet": {
            "output": CONTACT_SHEET_NAME,
            "output_sha256": _sha256(contact_png),
            "width_px": contact_size[0],
            "height_px": contact_size[1],
            "included_sources": sorted(normalized),
        },
    }
    return artifacts, manifest
