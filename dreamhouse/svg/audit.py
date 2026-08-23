"""Render repeatable SVG review images, metrics and labelled contact sheets."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
from pathlib import Path
from xml.etree import ElementTree as ET

import resvg_py
from PIL import Image, ImageDraw, ImageFont


SVG_NS = "http://www.w3.org/2000/svg"
SCALE_RE = re.compile(r"scale\(\s*([0-9.+-]+)(?:[ ,]+([0-9.+-]+))?\s*\)")
HEX_RE = re.compile(r"#[0-9A-Fa-f]{6}")
DEFAULT_COLLECTION_WIDTHS = (480, 800, 1400)
DEFAULT_REVIEW_WIDTHS = (480, 800, 1400, 1684)
CONTACT_COLUMNS = 2
CONTACT_GUTTER = 16
CONTACT_HEADER_HEIGHT = 70
CONTACT_LABEL_HEIGHT = 52
CONTACT_BACKGROUND = "#F4F1E9"
CONTACT_PANEL = "#FFFFFF"
CONTACT_RULE = "#CBD4D2"
CONTACT_INK = "#172A32"
CONTACT_MUTED = "#52636A"


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


def _identity(svg_path: Path) -> dict[str, str]:
    root = ET.parse(svg_path).getroot()
    title = root.find(q("title"))
    normalized_title = (
        " ".join((title.text or "Untitled SVG").split())
        if title is not None
        else "Untitled SVG"
    )
    return {
        "revision": root.get("data-revision", "UNVERSIONED"),
        "status": root.get("data-status", "status-not-declared"),
        "title": normalized_title,
    }


def _font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    family = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    try:
        return ImageFont.truetype(family, size=size)
    except OSError:
        return ImageFont.load_default(size=size)


def _fit_label(value: str, *, width: int, font: ImageFont.ImageFont) -> str:
    if font.getlength(value) <= width:
        return value
    suffix = "..."
    available = width - font.getlength(suffix)
    shortened = value
    while shortened and font.getlength(shortened) > available:
        shortened = shortened[:-1]
    return shortened.rstrip() + suffix


def _contact_sheet(
    entries: list[tuple[Path, Image.Image]],
    *,
    title: str,
    thumbnail_width: int,
    columns: int,
) -> Image.Image:
    if not entries:
        raise ValueError("A contact sheet requires at least one SVG image")
    if thumbnail_width <= 0 or columns <= 0:
        raise ValueError("Contact-sheet width and columns must be positive")
    if any(image.width != thumbnail_width for _, image in entries):
        raise ValueError("Every contact-sheet image must use the declared thumbnail width")

    rows = (len(entries) + columns - 1) // columns
    image_height = max(image.height for _, image in entries)
    cell_height = CONTACT_LABEL_HEIGHT + image_height
    sheet_width = CONTACT_GUTTER + columns * (thumbnail_width + CONTACT_GUTTER)
    sheet_height = CONTACT_HEADER_HEIGHT + rows * (cell_height + CONTACT_GUTTER)
    sheet = Image.new("RGB", (sheet_width, sheet_height), CONTACT_BACKGROUND)
    draw = ImageDraw.Draw(sheet)
    title_font = _font(17, bold=True)
    body_font = _font(12)
    label_font = _font(12, bold=True)
    meta_font = _font(10)
    draw.text((CONTACT_GUTTER, 14), title, fill=CONTACT_INK, font=title_font)
    draw.text(
        (CONTACT_GUTTER, 40),
        f"{len(entries)} sheets · {thumbnail_width} px thumbnails · REVIEW EVIDENCE ONLY",
        fill=CONTACT_MUTED,
        font=body_font,
    )

    for index, (path, image) in enumerate(entries):
        column = index % columns
        row = index // columns
        x = CONTACT_GUTTER + column * (thumbnail_width + CONTACT_GUTTER)
        y = CONTACT_HEADER_HEIGHT + row * (cell_height + CONTACT_GUTTER)
        draw.rounded_rectangle(
            (x, y, x + thumbnail_width - 1, y + cell_height - 1),
            radius=5,
            fill=CONTACT_PANEL,
            outline=CONTACT_RULE,
        )
        identity = _identity(path)
        label_width = thumbnail_width - 24
        draw.text(
            (x + 12, y + 8),
            _fit_label(identity["title"], width=label_width, font=label_font),
            fill=CONTACT_INK,
            font=label_font,
        )
        meta = f"{identity['revision']} · {identity['status']}"
        draw.text(
            (x + 12, y + 29),
            _fit_label(meta, width=label_width, font=meta_font),
            fill=CONTACT_MUTED,
            font=meta_font,
        )
        sheet.paste(image, (x, y + CONTACT_LABEL_HEIGHT))
    return sheet


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
    widths: tuple[int, ...] = DEFAULT_REVIEW_WIDTHS,
) -> None:
    if not widths or any(width <= 0 for width in widths) or len(set(widths)) != len(widths):
        raise ValueError("Review render widths must be positive and unique")
    output_dir.mkdir(parents=True, exist_ok=True)
    rendered: dict[int, Image.Image] = {}
    for width in widths:
        image = render(after, width)
        rendered[width] = image
        image.save(output_dir / f"{prefix}-{width}.png", optimize=True)
        image.convert("L").save(output_dir / f"{prefix}-{width}-grayscale.png", optimize=True)

    review_width = 1400
    before_image = _labelled(render(before, review_width), "CURRENT SOURCE / BASELINE")
    after_review = rendered.get(review_width) or render(after, review_width)
    after_image = _labelled(after_review, "PRESENTATION PILOT / NOT CURRENT")
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


def build_collection(
    paths: list[Path],
    output_dir: Path,
    *,
    prefix: str,
    widths: tuple[int, ...] = DEFAULT_COLLECTION_WIDTHS,
    contact_width: int = 480,
    columns: int = CONTACT_COLUMNS,
) -> dict[str, object]:
    """Build deterministic multi-scale renders, contact sheets and one metrics report."""

    if not paths:
        raise ValueError("The SVG audit collection requires at least one input path")
    if len(set(paths)) != len(paths):
        raise ValueError("The SVG audit collection cannot contain duplicate paths")
    if not widths or any(width <= 0 for width in widths):
        raise ValueError("Audit render widths must be positive")
    if len(set(widths)) != len(widths):
        raise ValueError("Audit render widths must be unique")
    if contact_width <= 0 or columns <= 0:
        raise ValueError("Contact-sheet width and columns must be positive")
    for path in paths:
        if path.suffix.lower() != ".svg" or not path.is_file():
            raise ValueError(f"Audit input is not an existing SVG file: {path}")
    ordered = sorted(
        paths,
        key=lambda path: (_identity(path)["revision"], path.as_posix()),
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    render_dir = output_dir / "renders"
    render_dir.mkdir(parents=True, exist_ok=True)
    contact_entries: list[tuple[Path, Image.Image]] = []
    file_records: list[dict[str, object]] = []
    for path in ordered:
        rendered: dict[int, Image.Image] = {}
        for width in widths:
            image = render(path, width)
            rendered[width] = image
            image.save(render_dir / f"{path.stem}-{width}.png", optimize=True)
            image.convert("L").save(
                render_dir / f"{path.stem}-{width}-grayscale.png",
                optimize=True,
            )
        contact_image = rendered.get(contact_width) or render(path, contact_width)
        contact_entries.append((path, contact_image))
        file_records.append(
            {
                "identity": _identity(path),
                "path": path.as_posix(),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                **metrics(path),
            }
        )

    contact = _contact_sheet(
        contact_entries,
        title="DREAM HOUSE · SVG DRAWING AUDIT",
        thumbnail_width=contact_width,
        columns=columns,
    )
    contact_path = output_dir / f"{prefix}-contact-{contact_width}.png"
    grayscale_path = output_dir / f"{prefix}-contact-{contact_width}-grayscale.png"
    contact.save(contact_path, optimize=True)
    contact.convert("L").save(grayscale_path, optimize=True)

    minimum_sizes = [
        float(record["minimum_effective_text_px"])
        for record in file_records
        if record["minimum_effective_text_px"] is not None
    ]
    report: dict[str, object] = {
        "schema_version": 1,
        "profile": {
            "columns": columns,
            "contact_width_px": contact_width,
            "preview_width_px": 1400,
            "render_widths_px": list(widths),
        },
        "summary": {
            "effective_text_below_7_px": sum(
                int(record["effective_text_below_7_px"]) for record in file_records
            ),
            "effective_text_below_8_px": sum(
                int(record["effective_text_below_8_px"]) for record in file_records
            ),
            "effective_text_below_9_px": sum(
                int(record["effective_text_below_9_px"]) for record in file_records
            ),
            "files": len(file_records),
            "minimum_effective_text_px": min(minimum_sizes, default=None),
            "visible_text_elements": sum(
                int(record["visible_text_elements"]) for record in file_records
            ),
        },
        "files": file_records,
    }
    (output_dir / f"{prefix}-metrics.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", type=Path)
    parser.add_argument("--after", type=Path)
    parser.add_argument("--paths", type=Path, nargs="+")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--prefix", required=True)
    parser.add_argument("--widths", type=int, nargs="+")
    parser.add_argument("--contact-width", type=int, default=480)
    parser.add_argument("--columns", type=int, default=CONTACT_COLUMNS)
    args = parser.parse_args()
    if args.paths:
        if args.before or args.after:
            parser.error("--paths cannot be combined with --before or --after")
        build_collection(
            args.paths,
            args.output_dir,
            prefix=args.prefix,
            widths=tuple(args.widths or DEFAULT_COLLECTION_WIDTHS),
            contact_width=args.contact_width,
            columns=args.columns,
        )
        return
    if args.before is None or args.after is None:
        parser.error("either --paths or both --before and --after are required")
    build_review(
        args.before,
        args.after,
        args.output_dir,
        prefix=args.prefix,
        widths=tuple(args.widths or DEFAULT_REVIEW_WIDTHS),
    )


if __name__ == "__main__":
    main()
