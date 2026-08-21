"""Render repeatable colour, grayscale and before/after SVG pilot review files."""

from __future__ import annotations

import argparse
import io
import json
import re
from pathlib import Path
from xml.etree import ElementTree as ET

import resvg_py
from PIL import Image, ImageDraw


SVG_NS = "http://www.w3.org/2000/svg"
SCALE_RE = re.compile(r"scale\(\s*([0-9.+-]+)(?:[ ,]+([0-9.+-]+))?\s*\)")
HEX_RE = re.compile(r"#[0-9A-Fa-f]{6}")


def q(tag: str) -> str:
    return f"{{{SVG_NS}}}{tag}"


def render(svg_path: Path, width: int) -> Image.Image:
    raw = resvg_py.svg_to_bytes(
        svg_path=str(svg_path),
        width=width,
        resources_dir=str(svg_path.parent),
        text_rendering="optimize_legibility",
        image_rendering="optimize_quality",
    )
    with Image.open(io.BytesIO(raw)) as opened:
        opened.load()
        return opened.convert("RGB")


def _viewbox_width(root: ET.Element) -> float:
    values = root.get("viewBox", "").replace(",", " ").split()
    if len(values) != 4:
        return float(root.get("width", "0"))
    return float(values[2])


def _walk_text(
    element: ET.Element,
    *,
    inherited_scale: float = 1.0,
    inherited_hidden: bool = False,
):
    scale = inherited_scale
    match = SCALE_RE.search(element.get("transform", ""))
    if match:
        scale *= float(match.group(1))
    hidden = inherited_hidden or element.get("display") == "none"
    if element.tag == q("text") and not hidden:
        yield element, scale
    for child in element:
        yield from _walk_text(child, inherited_scale=scale, inherited_hidden=hidden)


def metrics(svg_path: Path, preview_width: int = 1400) -> dict[str, object]:
    root = ET.parse(svg_path).getroot()
    viewbox_width = _viewbox_width(root)
    effective_sizes: list[float] = []
    for text, transform_scale in _walk_text(root):
        raw_size = text.get("font-size")
        if raw_size:
            effective_sizes.append(
                float(raw_size) * transform_scale * preview_width / viewbox_width
            )
    literals = set(HEX_RE.findall(svg_path.read_text(encoding="utf-8")))
    return {
        "canvas": {
            "height": root.get("height"),
            "viewBox": root.get("viewBox"),
            "width": root.get("width"),
        },
        "colour_literals": len(literals),
        "effective_text_below_7_px": sum(size < 7 for size in effective_sizes),
        "effective_text_below_8_px": sum(size < 8 for size in effective_sizes),
        "effective_text_below_9_px": sum(size < 9 for size in effective_sizes),
        "minimum_effective_text_px": min(effective_sizes, default=None),
        "preview_width_px": preview_width,
        "visible_text_elements": len(effective_sizes),
    }


def _labelled(image: Image.Image, label: str) -> Image.Image:
    band = 34
    output = Image.new("RGB", (image.width, image.height + band), "white")
    output.paste(image, (0, band))
    ImageDraw.Draw(output).text((18, 10), label, fill="#172A32")
    return output


def build_review(
    before: Path,
    after: Path,
    output_dir: Path,
    *,
    prefix: str,
    widths: tuple[int, ...] = (480, 800, 1400, 1684),
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    rendered: dict[int, Image.Image] = {}
    for width in widths:
        image = render(after, width)
        rendered[width] = image
        image.save(output_dir / f"{prefix}-{width}.png", optimize=True)
        image.convert("L").save(output_dir / f"{prefix}-{width}-grayscale.png", optimize=True)

    review_width = 1400
    before_image = _labelled(render(before, review_width), "CURRENT SOURCE / BASELINE")
    after_image = _labelled(rendered[review_width], "PRESENTATION PILOT / NOT CURRENT")
    comparison = Image.new(
        "RGB",
        (review_width, before_image.height + after_image.height),
        "white",
    )
    comparison.paste(before_image, (0, 0))
    comparison.paste(after_image, (0, before_image.height))
    comparison.save(output_dir / f"{prefix}-before-after-1400.png", optimize=True)

    report = {
        "after": {"path": after.as_posix(), **metrics(after)},
        "before": {"path": before.as_posix(), **metrics(before)},
    }
    (output_dir / f"{prefix}-metrics.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--prefix", required=True)
    args = parser.parse_args()
    build_review(args.before, args.after, args.output_dir, prefix=args.prefix)


if __name__ == "__main__":
    main()
