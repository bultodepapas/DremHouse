#!/usr/bin/env python3
"""Synchronise stable current-drawing aliases from explicitly promoted sources.

The source files remain immutable historical issues. This script copies each promoted
SVG byte-for-byte, creates a PNG preview, and writes a hash-bearing publication manifest.
It never infers authority from a filename or revision number.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import io
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CURRENT_DIR = ROOT / "planos" / "actual"
CATALOG = CURRENT_DIR / "catalog.json"
MANIFEST = CURRENT_DIR / "manifest.json"
CURRENT_README = CURRENT_DIR / "README.md"
DRAWINGS_README = ROOT / "planos" / "README.md"
DOCS_CURRENT = ROOT / "docs" / "02_arquitectura" / "planos_actuales.md"
CANONICAL_NAME = re.compile(r"^[A-Z0-9][A-Z0-9._-]*$")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def repository_path(value: str) -> Path:
    path = (ROOT / value).resolve()
    if path == ROOT or ROOT not in path.parents:
        raise ValueError(f"Path escapes the repository: {value}")
    return path


def manifest_output_names(data: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    for output in data.get("outputs", []):
        value = output.get("path") if isinstance(output, dict) else output
        if isinstance(value, str):
            names.add(Path(value).as_posix())
            names.add(Path(value).name)
    return names


def source_record(entry: dict[str, Any]) -> dict[str, Any]:
    source = repository_path(entry["source"])
    if source.suffix.lower() != ".svg" or not source.is_file():
        raise ValueError(f"Canonical source is not an SVG file: {entry['source']}")
    if CURRENT_DIR.resolve() in source.parents:
        raise ValueError(f"A canonical alias cannot be its own source: {entry['source']}")

    source_manifest = source.parent / "manifest.json"
    if not source_manifest.is_file():
        raise ValueError(f"Source has no adjacent manifest: {entry['source']}")
    source_data = load_json(source_manifest)
    if source.name not in manifest_output_names(source_data):
        raise ValueError(f"Source is not declared by {source_manifest.relative_to(ROOT)}")

    revision = str(source_data.get("revision", "no revision declared"))
    if revision != entry["source_revision"]:
        raise ValueError(
            f"Revision mismatch for {entry['id']}: catalog={entry['source_revision']!r}, "
            f"manifest={revision!r}"
        )

    canonical = entry["canonical"]
    if not CANONICAL_NAME.fullmatch(canonical):
        raise ValueError(f"Invalid stable canonical name: {canonical!r}")

    return {
        **entry,
        "source_path": source,
        "source_manifest_path": source_manifest,
        "source_sha256": sha256(source),
        "canonical_svg_path": CURRENT_DIR / f"{canonical}.svg",
        "canonical_png_path": CURRENT_DIR / f"{canonical}.png",
    }


def load_records() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    catalog = load_json(CATALOG)
    if catalog.get("schema_version") != 1:
        raise ValueError("Unsupported current-drawing catalog schema")
    records = [source_record(entry) for entry in catalog.get("drawings", [])]
    if not records:
        raise ValueError("The current-drawing catalog is empty")
    ids = [item["id"] for item in records]
    names = [item["canonical"] for item in records]
    if len(ids) != len(set(ids)) or len(names) != len(set(names)):
        raise ValueError("Drawing IDs and canonical names must be unique")
    return catalog, records


def render_png(record: dict[str, Any], width_px: int) -> tuple[int, int]:
    try:
        import resvg_py
        from PIL import Image, PngImagePlugin
    except ImportError as exc:
        raise RuntimeError(
            "PNG generation requires the presentation dependencies. "
            "Install with: pip install -e '.[presentation]'"
        ) from exc

    raw_png = resvg_py.svg_to_bytes(
        svg_path=str(record["source_path"]),
        width=width_px,
        resources_dir=str(record["source_path"].parent),
        text_rendering="optimize_legibility",
        image_rendering="optimize_quality",
    )
    metadata = PngImagePlugin.PngInfo()
    metadata.add_text("Canonical-ID", record["id"])
    metadata.add_text("Source-SHA256", record["source_sha256"])
    metadata.add_text("Source-Revision", record["source_revision"])
    with Image.open(io.BytesIO(raw_png)) as image:
        image.load()
        size = image.size
        image.save(
            record["canonical_png_path"],
            format="PNG",
            optimize=True,
            pnginfo=metadata,
        )
    return size


def public_record(record: dict[str, Any], image_size: tuple[int, int]) -> dict[str, Any]:
    return {
        key: record[key]
        for key in (
            "id",
            "group",
            "eyebrow",
            "title",
            "summary",
            "alt",
            "source_revision",
            "status",
            "featured",
        )
    } | {
        "source": record["source_path"].relative_to(ROOT).as_posix(),
        "source_manifest": record["source_manifest_path"].relative_to(ROOT).as_posix(),
        "source_sha256": record["source_sha256"],
        "canonical_svg": record["canonical_svg_path"].relative_to(ROOT).as_posix(),
        "canonical_svg_sha256": sha256(record["canonical_svg_path"]),
        "canonical_png": record["canonical_png_path"].relative_to(ROOT).as_posix(),
        "canonical_png_sha256": sha256(record["canonical_png_path"]),
        "png_size_px": {"width": image_size[0], "height": image_size[1]},
    }


def featured_gallery(drawings: list[dict[str, Any]], *, from_docs: bool) -> str:
    featured = [item for item in drawings if item["featured"]]
    rows: list[str] = []
    prefix = "../../" if from_docs else ""
    if not from_docs:
        def local(path: str) -> str:
            return Path(path).relative_to("planos").as_posix()
    else:
        def local(path: str) -> str:
            return prefix + path

    for index in range(0, len(featured), 2):
        cells: list[str] = []
        for item in featured[index : index + 2]:
            svg = html.escape(local(item["canonical_svg"]), quote=True)
            png = html.escape(local(item["canonical_png"]), quote=True)
            source = html.escape(local(item["source"]), quote=True)
            title = html.escape(item["title"])
            alt = html.escape(item["alt"], quote=True)
            revision = html.escape(item["source_revision"])
            cells.append(
                "\n".join(
                    [
                        '<td width="50%" valign="top">',
                        f'  <a href="{svg}"><img src="{png}" alt="{alt}" width="100%"></a>',
                        f"  <br><strong>{title}</strong>",
                        f'  <br><sub>{revision} · <a href="{source}">versioned source</a></sub>',
                        "</td>",
                    ]
                )
            )
        rows.append("<tr>\n" + "\n".join(cells) + "\n</tr>")
    return "<table>\n" + "\n".join(rows) + "\n</table>"


def render_drawings_readme(manifest: dict[str, Any]) -> str:
    drawings = manifest["drawings"]
    table_rows: list[str] = []
    for item in drawings:
        svg = Path(item["canonical_svg"]).relative_to("planos").as_posix()
        png = Path(item["canonical_png"]).relative_to("planos").as_posix()
        source = Path(item["source"]).relative_to("planos").as_posix()
        table_rows.append(
            f'| `{item["id"]}` | {item["title"]} | [SVG]({svg}) · [PNG]({png}) | '
            f'[{item["source_revision"]}]({source}) | {item["status"]} |'
        )
    return f"""# Dream House drawings

**Status:** {manifest["status"]}<br>
**Version:** {manifest["version"]}<br>
**Date:** {manifest["date"]}<br>
**Source:** [`actual/catalog.json`](actual/catalog.json)

> [!IMPORTANT]
> `actual/` is the stable publication layer for the current project state. Its SVG files
> are byte-for-byte copies of explicitly promoted versioned issues; its PNG files are
> previews. Neither format creates dimensional or construction authority.

## Start here

{featured_gallery(drawings, from_docs=False)}

The current state is a **coordinated set**, not a claim that one sheet contains every
active decision. In particular, read the ground-floor plan with the owner-priorities
detail for D-050's laundry reserve, the rear elevation with D-051's stair reserve, and
all architectural sheets with the structural studies and their open gates.

## Complete current set

| Stable ID | Drawing | Current aliases | Preserved issue | Status / limitation |
| --- | --- | --- | --- | --- |
{chr(10).join(table_rows)}

Full provenance and SHA-256 hashes are recorded in
[`actual/manifest.json`](actual/manifest.json). The human-controlled promotion list is
[`actual/catalog.json`](actual/catalog.json).

## History and update rule

Versioned folders and issued files—including `conceptual_v0.3_b10_p2/`, `estructura/`,
and `integracion_v0.4_i01/`—remain preserved. They are not renamed or overwritten.

When a new drawing becomes the active issue for one of the stable IDs:

1. issue it under its versioned filename and retain its adjacent `manifest.json`;
2. update that ID's `source`, `source_revision`, status, and catalog date;
3. run `python .github/scripts/sync_current_drawings.py --write`;
4. review the SVG and PNG, then run the command again with `--check`; and
5. record any design, scope, or cost decision in the governing project documents.

The presentation workflow performs the same validation in CI. A higher revision number
alone never promotes a hypothesis to the current set.
"""


def render_current_readme(manifest: dict[str, Any]) -> str:
    return f"""# Current drawing aliases

**Status:** {manifest["status"]}<br>
**Version:** {manifest["version"]}<br>
**Date:** {manifest["date"]}<br>
**Construction authority:** none

This generated directory contains **{len(manifest["drawings"])} stable SVG/PNG pairs**
representing the issues currently used for project coordination.

- [Open the visual drawing index](../README.md)
- [Inspect source-to-alias provenance and hashes](manifest.json)
- [Inspect the explicit promotion catalog](catalog.json)

Do not edit aliases directly. Issue and preserve the versioned drawing first, update its
catalog entry, and run `python .github/scripts/sync_current_drawings.py --write`.

“Current” does not mean frozen, approved, or suitable for construction. Every alias
inherits the status and limitations of its versioned source.
"""


def render_docs_current(manifest: dict[str, Any]) -> str:
    drawings = manifest["drawings"]
    architecture = sum(item["group"] == "Architecture" for item in drawings)
    structure = sum(item["group"] == "Structure" for item in drawings)
    return f"""# Current drawings and visual index

**Status:** active publication guide; source-sheet limitations remain in force<br>
**Version:** {manifest["version"]}<br>
**Date:** {manifest["date"]}<br>
**Source:** [current-drawing catalog](../../planos/actual/catalog.json) and D-056

This page is the visual entry point to the current coordinated state of Dream House. It
uses stable files under [`planos/actual/`](../../planos/actual/) so links in the project
record, repository README, and presentation do not change when a new issue is promoted.

> [!WARNING]
> These are schematic coordination drawings, not construction documents. A current alias
> means “the issue presently used for coordination”; it does not freeze a hypothesis or
> override the [source precedence](../00_gobernanza/fuentes_precedencia_y_conflictos.md).

## Current visual set

{featured_gallery(drawings, from_docs=True)}

[Open the complete drawing index →](../../planos/README.md)

## What the set contains

The publication layer currently contains **{len(drawings)} SVG/PNG pairs**:
**{architecture} architectural views** and **{structure} structural coordination
views**. It covers both floor plans, roof and rooflights, longitudinal and transverse
sections, all four exterior elevations, the Great Wall and service core, access/egress,
owner-priority interfaces, structural plans/elevations, the hybrid-wall study, E1
screening, and stair-frame vertical continuity.

The set must be read together:

- the ground-floor base sheet predates D-050's laundry relocation, which is explicitly
  shown in the current owner-priorities detail;
- the rear façade remains supplemented by D-051's retractable-stair reserve;
- roof form is represented by the b07 sections and façades, while the current rooflight
  position is represented by the 0.4-I01/D-054 roof plan and daylight section; and
- structural sheets are screening and coordination evidence only; they do not select a
  frame, member, joint, foundation, fire system, or construction method.

## Traceability

Every current SVG is identical to its preserved versioned source. Every PNG carries the
source revision and SHA-256 hash as embedded metadata. The generated
[publication manifest](../../planos/actual/manifest.json) records both aliases, their
hashes, their versioned source, status, and adjacent issue manifest.

Promotion is explicit. The workflow never decides that a drawing is current merely
because its filename contains a larger revision number. See the
[drawing-directory guide](../../planos/README.md) for the update procedure.
"""


def png_metadata(path: Path) -> tuple[dict[str, str], tuple[int, int]]:
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError(
            "PNG validation requires Pillow. Install with: pip install -e '.[presentation]'"
        ) from exc
    with Image.open(path) as image:
        image.verify()
    with Image.open(path) as image:
        return dict(image.text), image.size


def expected_manifest(
    catalog: dict[str, Any], records: list[dict[str, Any]], *, validate: bool
) -> dict[str, Any]:
    drawings: list[dict[str, Any]] = []
    width_px = int(catalog["raster_width_px"])
    for record in records:
        svg = record["canonical_svg_path"]
        png = record["canonical_png_path"]
        if not svg.is_file() or not png.is_file():
            raise FileNotFoundError(f"Missing current assets for {record['id']}")
        if svg.read_bytes() != record["source_path"].read_bytes():
            raise ValueError(f"Current SVG is stale: {svg.relative_to(ROOT)}")
        metadata, image_size = png_metadata(png)
        if validate:
            expected_metadata = {
                "Canonical-ID": record["id"],
                "Source-SHA256": record["source_sha256"],
                "Source-Revision": record["source_revision"],
            }
            for key, value in expected_metadata.items():
                if metadata.get(key) != value:
                    raise ValueError(f"Current PNG metadata is stale: {png.relative_to(ROOT)}")
            if image_size[0] != width_px:
                raise ValueError(f"Current PNG has the wrong width: {png.relative_to(ROOT)}")
        drawings.append(public_record(record, image_size))

    return {
        "schema_version": catalog["schema_version"],
        "version": catalog["version"],
        "date": catalog["date"],
        "status": catalog["status"],
        "construction_authority": False,
        "catalog": CATALOG.relative_to(ROOT).as_posix(),
        "raster_width_px": width_px,
        "drawings": drawings,
    }


def write_current(catalog: dict[str, Any], records: list[dict[str, Any]]) -> None:
    CURRENT_DIR.mkdir(parents=True, exist_ok=True)
    width_px = int(catalog["raster_width_px"])
    expected_assets = {
        *(record["canonical_svg_path"].name for record in records),
        *(record["canonical_png_path"].name for record in records),
    }
    for path in CURRENT_DIR.iterdir():
        if (
            path.is_file()
            and path.suffix.lower() in {".svg", ".png"}
            and path.name not in expected_assets
        ):
            path.unlink()
    for record in records:
        svg_is_current = (
            record["canonical_svg_path"].is_file()
            and record["canonical_svg_path"].read_bytes() == record["source_path"].read_bytes()
        )
        if not svg_is_current:
            shutil.copyfile(record["source_path"], record["canonical_svg_path"])

        png_is_current = False
        if record["canonical_png_path"].is_file():
            metadata, image_size = png_metadata(record["canonical_png_path"])
            png_is_current = image_size[0] == width_px and metadata == {
                "Canonical-ID": record["id"],
                "Source-SHA256": record["source_sha256"],
                "Source-Revision": record["source_revision"],
            }
        if not png_is_current:
            render_png(record, width_px)
    manifest = expected_manifest(catalog, records, validate=True)
    MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    DRAWINGS_README.write_text(
        render_drawings_readme(manifest), encoding="utf-8", newline="\n"
    )
    DOCS_CURRENT.write_text(render_docs_current(manifest), encoding="utf-8", newline="\n")
    CURRENT_README.write_text(
        render_current_readme(manifest), encoding="utf-8", newline="\n"
    )
    print(f"Synchronised {len(records)} current drawings in {CURRENT_DIR.relative_to(ROOT)}.")


def check_current(catalog: dict[str, Any], records: list[dict[str, Any]]) -> None:
    expected = expected_manifest(catalog, records, validate=True)
    if not MANIFEST.is_file() or load_json(MANIFEST) != expected:
        raise ValueError(
            "The current-drawing manifest is stale. Run: "
            "python .github/scripts/sync_current_drawings.py --write"
        )
    expected_assets = {
        *(record["canonical_svg_path"].name for record in records),
        *(record["canonical_png_path"].name for record in records),
    }
    actual_assets = {
        path.name
        for path in CURRENT_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in {".svg", ".png"}
    }
    if actual_assets != expected_assets:
        extra = sorted(actual_assets - expected_assets)
        missing = sorted(expected_assets - actual_assets)
        raise ValueError(f"Current asset set differs from the catalog; extra={extra}, missing={missing}")
    expected_docs = {
        CURRENT_README: render_current_readme(expected),
        DRAWINGS_README: render_drawings_readme(expected),
        DOCS_CURRENT: render_docs_current(expected),
    }
    for path, content in expected_docs.items():
        if not path.is_file() or path.read_text(encoding="utf-8") != content:
            raise ValueError(f"Generated drawing index is stale: {path.relative_to(ROOT)}")
    print(f"Validated {len(records)} current SVG/PNG pairs and their provenance.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="write SVG/PNG aliases and manifest")
    mode.add_argument("--check", action="store_true", help="validate aliases and provenance")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        catalog, records = load_records()
        if args.write:
            write_current(catalog, records)
        else:
            check_current(catalog, records)
    except (FileNotFoundError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"current drawings: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
