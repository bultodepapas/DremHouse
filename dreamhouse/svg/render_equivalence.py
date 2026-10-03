"""Compare SVG text-line and editorial-geometry rendering in resvg and Chromium."""

from __future__ import annotations

import argparse
import copy
import json
import re
import shutil
import subprocess
from collections import Counter
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from dreamhouse.svg.style import compile_svg_styles, has_svg_css_variables

SVG_NS = "http://www.w3.org/2000/svg"
DRAWABLE_TAGS = frozenset(
    {"circle", "ellipse", "image", "line", "path", "polygon", "polyline", "rect", "use"}
)
NUMBER_RE = re.compile(r"^[0-9]+(?:\.[0-9]+)?(?:px)?$")
MAX_PROBE_ITEMS = 511
DEFAULT_SCALE = 2
DEFAULT_TEXT_EDGE_TOLERANCE_PX = 5
DEFAULT_GEOMETRY_EDGE_TOLERANCE_PX = 2
PROBE_NOISE_GAP_PX = 32
TEXT_CLEARANCE_USER_UNITS = 6.0
GEOMETRY_CLEARANCE_USER_UNITS = 3.0


def q(tag: str) -> str:
    return f"{{{SVG_NS}}}{tag}"


def _local_name(element: ET.Element) -> str:
    if not isinstance(element.tag, str):
        return ""
    return element.tag.rsplit("}", 1)[-1]


def _normalized_text(element: ET.Element) -> str:
    return " ".join("".join(element.itertext()).split())


def _hidden(element: ET.Element, inherited: bool) -> bool:
    return inherited or element.get("display") == "none" or element.get("visibility") == "hidden"


def _walk(
    element: ET.Element,
    *,
    inside_defs: bool = False,
    inside_model: bool = False,
    inherited_hidden: bool = False,
):
    local = _local_name(element)
    in_defs = inside_defs or local == "defs"
    in_model = inside_model or element.get("id") == "layer-model"
    hidden = _hidden(element, inherited_hidden)
    yield element, in_defs, in_model, hidden
    for child in element:
        yield from _walk(
            child,
            inside_defs=in_defs,
            inside_model=in_model,
            inherited_hidden=hidden,
        )


def _probe_colour(index: int) -> tuple[int, int, int]:
    """Return one of 511 exact, well-separated colours that survives alpha rendering."""

    if not 1 <= index <= MAX_PROBE_ITEMS:
        raise ValueError(f"Probe index must be between 1 and {MAX_PROBE_ITEMS}")
    value = index
    channels: list[int] = []
    for _ in range(3):
        channels.append(24 + 28 * (value % 8))
        value //= 8
    return tuple(channels)  # type: ignore[return-value]


def _hex_colour(index: int) -> str:
    return "#{:02X}{:02X}{:02X}".format(*_probe_colour(index))


def _append_style(element: ET.Element, declarations: str) -> None:
    existing = element.get("style", "").strip().rstrip(";")
    element.set("style", f"{existing};{declarations}" if existing else declarations)


def _prune_probe(
    parent: ET.Element,
    *,
    keep_drawables: set[int],
    keep_texts: set[int],
    inside_defs: bool = False,
) -> None:
    for child in list(parent):
        local = _local_name(child)
        child_in_defs = inside_defs or local == "defs"
        if not child_in_defs:
            if local in DRAWABLE_TAGS and id(child) not in keep_drawables:
                parent.remove(child)
                continue
            if local == "text" and id(child) not in keep_texts:
                parent.remove(child)
                continue
        _prune_probe(
            child,
            keep_drawables=keep_drawables,
            keep_texts=keep_texts,
            inside_defs=child_in_defs,
        )


def build_text_line_probe(root: ET.Element) -> tuple[ET.Element, list[dict[str, Any]]]:
    """Build a text-only SVG where every explicit visual line has a unique colour."""

    probe = copy.deepcopy(root)
    visible_texts = [
        element
        for element, inside_defs, _inside_model, hidden in _walk(probe)
        if _local_name(element) == "text" and not inside_defs and not hidden
    ]
    keep_texts = {id(element) for element in visible_texts}
    _prune_probe(probe, keep_drawables=set(), keep_texts=keep_texts)

    items: list[dict[str, Any]] = []
    for parent_index, text in enumerate(visible_texts, start=1):
        tspans = list(text.findall(q("tspan")))
        direct_content = [text.text or "", *(span.tail or "" for span in tspans)]
        if tspans and any(value.strip() for value in direct_content):
            raise ValueError(
                "Text probes require multiline content to live entirely in direct tspans"
            )
        targets = tspans or [text]
        if tspans:
            _append_style(
                text,
                "fill:none!important;stroke:none!important;visibility:visible!important",
            )
        for line_index, target in enumerate(targets, start=1):
            index = len(items) + 1
            colour = _hex_colour(index)
            _append_style(
                target,
                f"fill:{colour}!important;stroke:none!important;opacity:1!important;"
                "fill-opacity:1!important;visibility:visible!important",
            )
            items.append(
                {
                    "index": index,
                    "parent_index": parent_index,
                    "line_index": line_index,
                    "source_id": text.get("id") or f"text-{parent_index:03d}",
                    "text": _normalized_text(target),
                    "layout_region": text.get("data-layout-region"),
                    "layout_relation": text.get("data-layout-relation"),
                    "layout_policy": text.get("data-layout-policy"),
                    "colour": colour,
                }
            )
    return probe, items


def build_geometry_probe(root: ET.Element) -> tuple[ET.Element, list[dict[str, Any]]]:
    """Build an SVG containing only explicitly registered editorial geometry."""

    probe = copy.deepcopy(root)
    geometries = [
        element
        for element, inside_defs, inside_model, hidden in _walk(probe)
        if element.get("data-layout-geometry")
        and not inside_defs
        and not inside_model
        and not hidden
    ]
    keep_drawables = {id(element) for element in geometries}
    _prune_probe(probe, keep_drawables=keep_drawables, keep_texts=set())

    items: list[dict[str, Any]] = []
    for index, element in enumerate(geometries, start=1):
        colour = _hex_colour(index)
        _append_style(
            element,
            f"display:inline!important;visibility:visible!important;fill:{colour}!important;"
            f"stroke:{colour}!important;opacity:1!important;fill-opacity:1!important;"
            "stroke-opacity:1!important",
        )
        items.append(
            {
                "index": index,
                "source_id": element.get("id") or f"geometry-{index:03d}",
                "tag": _local_name(element),
                "role": element.get("data-layout-geometry"),
                "layout_region": element.get("data-layout-region"),
                "layout_relation": element.get("data-layout-relation"),
                "colour": colour,
            }
        )
    return probe, items


def _numeric_dimension(root: ET.Element, attribute: str) -> int:
    raw = root.get(attribute, "").strip()
    if not NUMBER_RE.fullmatch(raw):
        raise ValueError(
            f"SVG {attribute} must be an explicit positive pixel number, received {raw!r}"
        )
    value = float(raw.removesuffix("px"))
    if value <= 0 or not value.is_integer():
        raise ValueError(f"SVG {attribute} must be a positive integer for browser parity")
    return int(value)


def discover_browser(explicit: Path | None = None) -> Path:
    """Find a local Chrome/Chromium executable without installing a browser."""

    if explicit is not None:
        candidate = explicit.expanduser().resolve()
        if not candidate.is_file():
            raise FileNotFoundError(f"Browser executable does not exist: {candidate}")
        return candidate

    names = ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable")
    for name in names:
        resolved = shutil.which(name)
        if resolved:
            return Path(resolved).resolve()

    cache = Path.home() / ".cache"
    patterns = (
        "puppeteer/chrome/*/chrome-linux64/chrome",
        "ms-playwright/chromium-*/chrome-linux64/chrome",
    )
    cached = sorted(
        (candidate for pattern in patterns for candidate in cache.glob(pattern)),
        key=lambda candidate: candidate.stat().st_mtime,
        reverse=True,
    )
    if cached:
        return cached[0].resolve()
    raise FileNotFoundError(
        "No Chrome/Chromium executable found; pass --browser with an existing executable"
    )


def browser_version(browser: Path) -> str:
    completed = subprocess.run(
        [str(browser), "--version"],
        check=True,
        capture_output=True,
        text=True,
        timeout=15,
    )
    return completed.stdout.strip() or completed.stderr.strip()


def _render_resvg(svg_path: Path, output: Path, *, width: int, height: int) -> None:
    import resvg_py

    raw = resvg_py.svg_to_bytes(
        svg_path=str(svg_path),
        width=width,
        height=height,
        resources_dir=str(svg_path.parent),
        text_rendering="optimize_legibility",
        image_rendering="optimize_quality",
    )
    output.write_bytes(raw)


def _render_browser(
    svg_path: Path,
    output: Path,
    *,
    browser: Path,
    width: int,
    height: int,
    scale: int,
) -> None:
    command = [
        str(browser),
        "--headless=new",
        "--no-sandbox",
        "--disable-gpu",
        "--hide-scrollbars",
        f"--force-device-scale-factor={scale}",
        f"--window-size={width},{height}",
        "--default-background-color=00000000",
        f"--screenshot={output.resolve()}",
        svg_path.resolve().as_uri(),
    ]
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if completed.returncode != 0 or not output.is_file():
        detail = (completed.stderr or completed.stdout).strip()[-1000:]
        raise RuntimeError(f"Browser render failed for {svg_path}: {detail}")


def _image_size(path: Path) -> tuple[int, int]:
    from PIL import Image

    with Image.open(path) as image:
        return image.size


def decode_probe_boxes(path: Path, item_count: int) -> dict[int, tuple[int, int, int, int]]:
    """Recover exact item paint boxes from a unique-colour transparent probe."""

    import numpy as np
    from PIL import Image

    if not 0 <= item_count <= MAX_PROBE_ITEMS:
        raise ValueError(f"Probe item count exceeds {MAX_PROBE_ITEMS}: {item_count}")
    with Image.open(path) as image:
        rgba = np.asarray(image.convert("RGBA"))
    rgb = rgba[:, :, :3].astype(np.int16)
    palette_pixel = np.all((rgb - 24) % 28 == 0, axis=2) & np.all(
        (rgb >= 24) & (rgb <= 220), axis=2
    )
    digits = (rgb - 24) // 28
    labels = digits[:, :, 0] + 8 * digits[:, :, 1] + 64 * digits[:, :, 2]
    valid = palette_pixel & (rgba[:, :, 3] > 0) & (labels >= 1) & (labels <= item_count)
    y_values, x_values = np.nonzero(valid)
    item_values = labels[valid]
    order = np.argsort(item_values, kind="stable")
    item_values = item_values[order]
    x_values = x_values[order]
    y_values = y_values[order]
    unique_items, starts, counts = np.unique(
        item_values, return_index=True, return_counts=True
    )
    boxes: dict[int, tuple[int, int, int, int]] = {}
    for item, start, count in zip(unique_items, starts, counts):
        item_x = x_values[start : start + count]
        item_y = y_values[start : start + count]
        unique_x, x_counts = np.unique(item_x, return_counts=True)
        split_at = np.where(np.diff(unique_x) > PROBE_NOISE_GAP_PX)[0] + 1
        x_groups = np.split(unique_x, split_at)
        count_groups = np.split(x_counts, split_at)
        group_sizes = [int(group.sum()) for group in count_groups]
        largest_group = max(group_sizes)
        minimum_group = min(largest_group, max(4, (largest_group + 49) // 50))
        keep = np.zeros(item_x.shape, dtype=bool)
        for group, group_size in zip(x_groups, group_sizes):
            if group_size >= minimum_group:
                keep |= (item_x >= group[0]) & (item_x <= group[-1])
        kept_x = item_x[keep]
        kept_y = item_y[keep]
        boxes[int(item)] = (
            int(kept_x.min()),
            int(kept_y.min()),
            int(kept_x.max()),
            int(kept_y.max()),
        )
    return boxes


def compare_probe_boxes(
    items: list[dict[str, Any]],
    browser_boxes: dict[int, tuple[int, int, int, int]],
    resvg_boxes: dict[int, tuple[int, int, int, int]],
    *,
    tolerance_px: int,
) -> dict[str, Any]:
    comparisons: list[dict[str, Any]] = []
    missing_browser: list[int] = []
    missing_resvg: list[int] = []
    mismatch_count = 0
    maximum_delta = 0
    for item in items:
        index = item["index"]
        browser_box = browser_boxes.get(index)
        resvg_box = resvg_boxes.get(index)
        if browser_box is None:
            missing_browser.append(index)
        if resvg_box is None:
            missing_resvg.append(index)
        delta = None
        if browser_box is not None and resvg_box is not None:
            edges = [abs(left - right) for left, right in zip(browser_box, resvg_box)]
            delta = max(edges)
            maximum_delta = max(maximum_delta, delta)
        if browser_box is None or resvg_box is None or delta is None or delta > tolerance_px:
            mismatch_count += 1
        comparisons.append(
            {
                "index": index,
                "label": item.get("text") or item.get("source_id"),
                "source_id": item.get("source_id"),
                "parent_index": item.get("parent_index"),
                "line_index": item.get("line_index"),
                "role": item.get("role"),
                "browser_box_px": browser_box,
                "resvg_box_px": resvg_box,
                "maximum_edge_delta_px": delta,
            }
        )
    ranked = sorted(
        comparisons,
        key=lambda entry: entry["maximum_edge_delta_px"]
        if entry["maximum_edge_delta_px"] is not None
        else tolerance_px + 1,
        reverse=True,
    )
    return {
        "items": len(items),
        "matched_items": len(items) - len(set(missing_browser + missing_resvg)),
        "missing_in_browser": missing_browser,
        "missing_in_resvg": missing_resvg,
        "maximum_edge_delta_px": maximum_delta,
        "mismatches": mismatch_count,
        "tolerance_px": tolerance_px,
        "largest_deltas": ranked[:8],
        "passed": mismatch_count == 0,
    }


def _union_boxes(
    items: list[dict[str, Any]],
    boxes: dict[int, tuple[int, int, int, int]],
) -> dict[int, dict[str, Any]]:
    parents: dict[int, dict[str, Any]] = {}
    for item in items:
        box = boxes.get(item["index"])
        parent_index = item.get("parent_index")
        if (
            box is None
            or parent_index is None
            or item.get("layout_region") is None
        ):
            continue
        entry = parents.setdefault(
            parent_index,
            {
                "box": box,
                "label": item.get("text") or item.get("source_id"),
                "region": item.get("layout_region"),
                "relation": item.get("layout_relation"),
            },
        )
        prior = entry["box"]
        entry["box"] = (
            min(prior[0], box[0]),
            min(prior[1], box[1]),
            max(prior[2], box[2]),
            max(prior[3], box[3]),
        )
    return parents


def _breaches_gap(
    left: tuple[int, int, int, int],
    right: tuple[int, int, int, int],
    gap_px: float,
) -> bool:
    left_right = left[2] + 1
    left_bottom = left[3] + 1
    right_right = right[2] + 1
    right_bottom = right[3] + 1
    return (
        left[0] < right_right + gap_px
        and left_right + gap_px > right[0]
        and left[1] < right_bottom + gap_px
        and left_bottom + gap_px > right[1]
    )


def check_layout_clearance(
    text_items: list[dict[str, Any]],
    text_boxes: dict[int, tuple[int, int, int, int]],
    geometry_items: list[dict[str, Any]],
    geometry_boxes: dict[int, tuple[int, int, int, int]],
    *,
    scale: int,
) -> dict[str, Any]:
    """Recheck typed layout clearances with renderer-measured paint boxes."""

    parents = _union_boxes(text_items, text_boxes)
    text_untyped: list[str] = []
    text_typed = 0
    parent_entries = list(parents.values())
    for index, left in enumerate(parent_entries):
        for right in parent_entries[index + 1 :]:
            if left["region"] != right["region"] or not _breaches_gap(
                left["box"], right["box"], TEXT_CLEARANCE_USER_UNITS * scale
            ):
                continue
            if left["relation"] and left["relation"] == right["relation"]:
                text_typed += 1
                continue
            text_untyped.append(f"{left['label']!r} ↔ {right['label']!r}")

    geometry_untyped: list[str] = []
    geometry_typed = 0
    for text in parent_entries:
        for geometry in geometry_items:
            box = geometry_boxes.get(geometry["index"])
            if (
                box is None
                or text["region"] != geometry["layout_region"]
                or not _breaches_gap(
                    text["box"], box, GEOMETRY_CLEARANCE_USER_UNITS * scale
                )
            ):
                continue
            if (
                geometry["role"] != "keepout"
                and text["relation"]
                and text["relation"] == geometry["layout_relation"]
            ):
                geometry_typed += 1
                continue
            geometry_untyped.append(
                f"{text['label']!r} ↔ {geometry['role']}:{geometry['source_id']}"
            )

    return {
        "registered_text_elements": len(parents),
        "rotated_text_elements_skipped": len(
            {
                item["parent_index"]
                for item in text_items
                if item.get("layout_policy") == "rotated-skip"
            }
        ),
        "rotated_text_elements_measured": len(
            {
                item["parent_index"]
                for item in text_items
                if item.get("layout_policy") == "rotated-measured"
            }
        ),
        "typed_text_pairs": text_typed,
        "untyped_text_pairs": len(text_untyped),
        "typed_text_geometry_pairs": geometry_typed,
        "untyped_text_geometry_pairs": len(geometry_untyped),
        "examples": (text_untyped + geometry_untyped)[:8],
        "text_gap_user_units": TEXT_CLEARANCE_USER_UNITS,
        "geometry_gap_user_units": GEOMETRY_CLEARANCE_USER_UNITS,
        "passed": not text_untyped and not geometry_untyped,
    }


def _full_render_metrics(browser_path: Path, resvg_path: Path) -> dict[str, Any]:
    import numpy as np
    from PIL import Image, ImageChops, ImageEnhance, ImageOps

    with Image.open(browser_path) as opened:
        browser = opened.convert("RGB")
    with Image.open(resvg_path) as opened:
        resvg = opened.convert("RGB")
    if browser.size != resvg.size:
        raise ValueError(f"Full-render sizes differ: browser {browser.size}, resvg {resvg.size}")
    difference = ImageChops.difference(browser, resvg)
    amplified = ImageEnhance.Brightness(difference).enhance(4.0)
    visual_difference = ImageOps.invert(amplified)
    array = np.asarray(difference, dtype=np.uint8)
    return {
        "browser": browser,
        "resvg": resvg,
        "difference": visual_difference,
        "mean_absolute_channel_delta": round(float(array.mean()), 4),
        "pixels_above_16_percent": round(
            float(np.any(array > 16, axis=2).mean() * 100), 4
        ),
        "maximum_channel_delta": int(array.max()),
    }


def _save_comparison(metrics: dict[str, Any], output: Path) -> None:
    from PIL import Image, ImageDraw

    browser = metrics["browser"]
    resvg = metrics["resvg"]
    difference = metrics["difference"]
    band = 34
    comparison = Image.new("RGB", (browser.width * 3, browser.height + band), "white")
    comparison.paste(browser, (0, band))
    comparison.paste(resvg, (browser.width, band))
    comparison.paste(difference, (browser.width * 2, band))
    draw = ImageDraw.Draw(comparison)
    draw.text((18, 10), "CHROMIUM", fill="#172A32")
    draw.text((browser.width + 18, 10), "RESVG", fill="#172A32")
    draw.text((browser.width * 2 + 18, 10), "AMPLIFIED DIFFERENCE · WHITE = SAME", fill="#172A32")
    comparison.save(output, optimize=True)


def _package_version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def _font_resolution() -> dict[str, str] | None:
    executable = shutil.which("fc-match")
    if not executable:
        return None
    completed = subprocess.run(
        [executable, "Inter", "--format=%{family}|%{file}"],
        check=False,
        capture_output=True,
        text=True,
        timeout=15,
    )
    if completed.returncode != 0 or "|" not in completed.stdout:
        return None
    family, path = completed.stdout.split("|", 1)
    return {"requested": "Inter", "resolved_family": family, "resolved_path": path}


def _font_requirement_passes(resolution: dict[str, str] | None) -> bool:
    if resolution is None:
        return False
    families = {family.strip() for family in resolution["resolved_family"].split(",")}
    return "Inter" in families


def audit_file(
    svg_path: Path,
    output_dir: Path,
    *,
    browser: Path,
    scale: int = DEFAULT_SCALE,
    text_tolerance_px: int = DEFAULT_TEXT_EDGE_TOLERANCE_PX,
    geometry_tolerance_px: int = DEFAULT_GEOMETRY_EDGE_TOLERANCE_PX,
) -> dict[str, Any]:
    root = ET.parse(svg_path).getroot()
    source_had_css_variables = has_svg_css_variables(root)
    portable_root = copy.deepcopy(root)
    compile_svg_styles(portable_root)
    width = _numeric_dimension(root, "width")
    height = _numeric_dimension(root, "height")
    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = svg_path.stem

    text_probe, text_items = build_text_line_probe(root)
    geometry_probe, geometry_items = build_geometry_probe(root)
    text_probe_path = output_dir / f"{prefix}-text-lines.svg"
    geometry_probe_path = output_dir / f"{prefix}-geometry.svg"
    ET.ElementTree(text_probe).write(text_probe_path, encoding="utf-8", xml_declaration=True)
    ET.ElementTree(geometry_probe).write(
        geometry_probe_path, encoding="utf-8", xml_declaration=True
    )

    probe_width = width * scale
    probe_height = height * scale
    text_browser = output_dir / f"{prefix}-text-lines-browser.png"
    text_resvg = output_dir / f"{prefix}-text-lines-resvg.png"
    geometry_browser = output_dir / f"{prefix}-geometry-browser.png"
    geometry_resvg = output_dir / f"{prefix}-geometry-resvg.png"
    _render_browser(
        text_probe_path,
        text_browser,
        browser=browser,
        width=width,
        height=height,
        scale=scale,
    )
    _render_resvg(text_probe_path, text_resvg, width=probe_width, height=probe_height)
    _render_browser(
        geometry_probe_path,
        geometry_browser,
        browser=browser,
        width=width,
        height=height,
        scale=scale,
    )
    _render_resvg(
        geometry_probe_path,
        geometry_resvg,
        width=probe_width,
        height=probe_height,
    )
    expected_probe_size = (probe_width, probe_height)
    probe_sizes = {
        "text_browser": _image_size(text_browser),
        "text_resvg": _image_size(text_resvg),
        "geometry_browser": _image_size(geometry_browser),
        "geometry_resvg": _image_size(geometry_resvg),
    }
    if any(size != expected_probe_size for size in probe_sizes.values()):
        raise ValueError(
            f"Probe render size mismatch for {svg_path.name}: {probe_sizes}, "
            f"expected {expected_probe_size}"
        )

    text_browser_boxes = decode_probe_boxes(text_browser, len(text_items))
    text_resvg_boxes = decode_probe_boxes(text_resvg, len(text_items))
    geometry_browser_boxes = decode_probe_boxes(geometry_browser, len(geometry_items))
    geometry_resvg_boxes = decode_probe_boxes(geometry_resvg, len(geometry_items))
    text_comparison = compare_probe_boxes(
        text_items,
        text_browser_boxes,
        text_resvg_boxes,
        tolerance_px=text_tolerance_px,
    )
    geometry_comparison = compare_probe_boxes(
        geometry_items,
        geometry_browser_boxes,
        geometry_resvg_boxes,
        tolerance_px=geometry_tolerance_px,
    )
    browser_clearance = check_layout_clearance(
        text_items,
        text_browser_boxes,
        geometry_items,
        geometry_browser_boxes,
        scale=scale,
    )
    resvg_clearance = check_layout_clearance(
        text_items,
        text_resvg_boxes,
        geometry_items,
        geometry_resvg_boxes,
        scale=scale,
    )

    full_browser = output_dir / f"{prefix}-browser.png"
    full_resvg = output_dir / f"{prefix}-resvg.png"
    portable_svg = output_dir / f"{prefix}-portable.svg"
    ET.ElementTree(portable_root).write(
        portable_svg,
        encoding="utf-8",
        xml_declaration=True,
    )
    _render_browser(
        portable_svg,
        full_browser,
        browser=browser,
        width=width,
        height=height,
        scale=1,
    )
    _render_resvg(portable_svg, full_resvg, width=width, height=height)
    full_metrics = _full_render_metrics(full_browser, full_resvg)
    _save_comparison(full_metrics, output_dir / f"{prefix}-comparison.png")

    parent_line_counts = Counter(item["parent_index"] for item in text_items)
    geometry_roles = Counter(item["role"] for item in geometry_items)
    registered_parents = {
        item["parent_index"] for item in text_items if item["layout_region"] is not None
    }
    rotated_skip_lines = sum(
        item["layout_policy"] == "rotated-skip" for item in text_items
    )
    result = {
        "path": svg_path.as_posix(),
        "canvas_px": {"width": width, "height": height},
        "text": {
            **text_comparison,
            "visible_text_elements": len(parent_line_counts),
            "registered_layout_text_elements": len(registered_parents),
            "multiline_text_elements": sum(count > 1 for count in parent_line_counts.values()),
            "rotated_measured_lines": sum(
                item["layout_policy"] == "rotated-measured" for item in text_items
            ),
            "rotated_skip_lines": rotated_skip_lines,
        },
        "geometry": {**geometry_comparison, "roles": dict(sorted(geometry_roles.items()))},
        "layout_clearance": {
            "browser": browser_clearance,
            "resvg": resvg_clearance,
        },
        "full_render": {
            "style_compilation": "theme variables compiled to literal paint values",
            "portable_copy_rendered_for_parity": True,
            "source_had_css_variable_references": source_had_css_variables,
            "original_source_style_portable": not source_had_css_variables,
            "original_source_artifact_parity_certified": not source_had_css_variables,
            "parity_subject": portable_svg.name,
            "parity_limit": (
                "A source containing CSS variable references is compared only after bounded "
                "literal compilation; this result does not certify direct rendering of the "
                "uncompiled source artifact."
                if source_had_css_variables
                else "The source has no CSS variable references; the literal style tree is "
                "rendered in both engines."
            ),
            "mean_absolute_channel_delta": full_metrics["mean_absolute_channel_delta"],
            "pixels_above_16_percent": full_metrics["pixels_above_16_percent"],
            "maximum_channel_delta": full_metrics["maximum_channel_delta"],
        },
    }
    result["passed"] = (
        text_comparison["passed"]
        and geometry_comparison["passed"]
        and browser_clearance["passed"]
        and resvg_clearance["passed"]
        and rotated_skip_lines == 0
    )
    return result


def audit_paths(
    paths: list[Path],
    output_dir: Path,
    *,
    browser: Path | None = None,
    scale: int = DEFAULT_SCALE,
    text_tolerance_px: int = DEFAULT_TEXT_EDGE_TOLERANCE_PX,
    geometry_tolerance_px: int = DEFAULT_GEOMETRY_EDGE_TOLERANCE_PX,
) -> dict[str, Any]:
    resolved_browser = discover_browser(browser)
    font_resolution = _font_resolution()
    font_requirement_passed = _font_requirement_passes(font_resolution)
    files = [
        audit_file(
            path,
            output_dir,
            browser=resolved_browser,
            scale=scale,
            text_tolerance_px=text_tolerance_px,
            geometry_tolerance_px=geometry_tolerance_px,
        )
        for path in sorted(paths)
    ]
    summary = {
        "files": len(files),
        "passed": sum(file["passed"] for file in files),
        "failed": sum(not file["passed"] for file in files),
        "text_lines": sum(file["text"]["items"] for file in files),
        "text_line_mismatches": sum(file["text"]["mismatches"] for file in files),
        "rotated_text_lines_measured": sum(
            file["text"]["rotated_measured_lines"] for file in files
        ),
        "rotated_text_lines_skipped": sum(
            file["text"]["rotated_skip_lines"] for file in files
        ),
        "registered_geometry": sum(file["geometry"]["items"] for file in files),
        "geometry_mismatches": sum(file["geometry"]["mismatches"] for file in files),
        "browser_untyped_layout_collisions": sum(
            file["layout_clearance"]["browser"]["untyped_text_pairs"]
            + file["layout_clearance"]["browser"]["untyped_text_geometry_pairs"]
            for file in files
        ),
        "resvg_untyped_layout_collisions": sum(
            file["layout_clearance"]["resvg"]["untyped_text_pairs"]
            + file["layout_clearance"]["resvg"]["untyped_text_geometry_pairs"]
            for file in files
        ),
        "maximum_text_edge_delta_px": max(
            (file["text"]["maximum_edge_delta_px"] for file in files), default=0
        ),
        "maximum_geometry_edge_delta_px": max(
            (file["geometry"]["maximum_edge_delta_px"] for file in files), default=0
        ),
        "font_requirement_failures": 0 if font_requirement_passed else 1,
    }
    report = {
        "schema_version": 2,
        "profile": {
            "browser": resolved_browser.as_posix(),
            "browser_version": browser_version(resolved_browser),
            "resvg_py_version": _package_version("resvg-py"),
            "pillow_version": _package_version("pillow"),
            "probe_scale": scale,
            "text_edge_tolerance_px": text_tolerance_px,
            "geometry_edge_tolerance_px": geometry_tolerance_px,
            "required_font_family": "Inter",
            "font_resolution": font_resolution,
            "font_requirement_passed": font_requirement_passed,
        },
        "summary": summary,
        "files": files,
    }
    report["passed"] = summary["failed"] == 0 and font_requirement_passed
    return report


def _expanded_paths(inputs: list[Path]) -> list[Path]:
    paths: list[Path] = []
    for value in inputs:
        if value.is_dir():
            pilots = sorted(value.glob("*PILOT.svg"))
            paths.extend(pilots or sorted(value.glob("*.svg")))
        elif value.suffix.lower() == ".svg":
            paths.append(value)
        else:
            raise ValueError(f"Expected an SVG file or directory, received {value}")
    unique = sorted(dict.fromkeys(path.resolve() for path in paths))
    if not unique:
        raise ValueError("No SVG files found")
    return unique


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--browser", type=Path)
    parser.add_argument("--scale", type=int, default=DEFAULT_SCALE)
    parser.add_argument(
        "--text-edge-tolerance-px", type=int, default=DEFAULT_TEXT_EDGE_TOLERANCE_PX
    )
    parser.add_argument(
        "--geometry-edge-tolerance-px",
        type=int,
        default=DEFAULT_GEOMETRY_EDGE_TOLERANCE_PX,
    )
    args = parser.parse_args()
    if args.scale < 1 or args.text_edge_tolerance_px < 0 or args.geometry_edge_tolerance_px < 0:
        parser.error("Scale must be positive and tolerances must be non-negative")
    report = audit_paths(
        _expanded_paths(args.paths),
        args.output_dir,
        browser=args.browser,
        scale=args.scale,
        text_tolerance_px=args.text_edge_tolerance_px,
        geometry_tolerance_px=args.geometry_edge_tolerance_px,
    )
    report_path = args.output_dir / "report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
