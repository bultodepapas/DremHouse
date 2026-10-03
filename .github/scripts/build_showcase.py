#!/usr/bin/env python3
"""Build the Dream House README gallery and its static GitHub Pages showcase.

The standalone gallery uses the Python standard library. Connected-review export also
loads the local coordination verifier and its declared project dependencies.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
REPO_URL = "https://github.com/bultodepapas/DremHouse"
BEGIN = "<!-- showcase:begin -->"
END = "<!-- showcase:end -->"
CURRENT_MANIFEST = ROOT / "planos" / "actual" / "manifest.json"
BUILD_ROOT = ROOT / ".build"
COORDINATION_ROOT = BUILD_ROOT / "coordination"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def discover_outputs() -> list[dict]:
    """Return versioned SVG issues, excluding the stable current aliases."""

    outputs: list[dict] = []
    for manifest in sorted((ROOT / "planos").rglob("manifest.json")):
        if (ROOT / "planos" / "actual") in manifest.parents:
            continue
        data = load_json(manifest)
        revision = str(data.get("revision", "no revision"))
        for output in data.get("outputs", []):
            value = output.get("path") if isinstance(output, dict) else output
            if not isinstance(value, str):
                continue
            candidate = manifest.parent / value
            if candidate.suffix.lower() != ".svg" or not candidate.is_file():
                continue
            relative = candidate.relative_to(ROOT).as_posix()
            outputs.append(
                {
                    "path": candidate,
                    "relative": relative,
                    "filename": candidate.name,
                    "revision": revision,
                }
            )
    return outputs


def select_gallery() -> list[dict]:
    """Load the explicitly promoted gallery; never infer authority from revision numbers."""

    data = load_json(CURRENT_MANIFEST)
    gallery: list[dict] = []
    for item in data.get("drawings", []):
        if not item.get("featured"):
            continue
        svg_path = ROOT / item["canonical_svg"]
        source_path = ROOT / item["source"]
        for path in (svg_path, source_path):
            if not path.is_file():
                raise RuntimeError(f"Current drawing asset is missing: {path.relative_to(ROOT)}")
        gallery.append(
            {
                **item,
                "slug": item["id"],
                "path": svg_path,
                "image_path": svg_path,
                "source_path": source_path,
                "relative": item["canonical_svg"],
                "image_relative": item["canonical_svg"],
                "source_relative": item["source"],
                "revision": item["source_revision"],
            }
        )
    if not gallery:
        raise RuntimeError("The current-drawing manifest has no featured drawings")
    return gallery


def extract_meta(markdown: str, label: str, default: str) -> str:
    match = re.search(rf"^\*\*{re.escape(label)}:\*\*\s*(.+?)\s*$", markdown, re.MULTILINE)
    return match.group(1).strip() if match else default


def extract_list_value(markdown: str, label: str, default: str) -> str:
    match = re.search(rf"^- \*\*{re.escape(label)}:\*\*\s*(.+?)\s*$", markdown, re.MULTILINE)
    return match.group(1).strip() if match else default


def project_data(gallery: list[dict]) -> dict:
    model = load_json(ROOT / "dreamhouse" / "project.json")
    docs_index = (ROOT / "docs" / "README.md").read_text(encoding="utf-8")
    readme = README.read_text(encoding="utf-8")
    decisions_text = (ROOT / "docs" / "00_gobernanza" / "registro_decisiones.md").read_text(encoding="utf-8")
    conflicts_text = (ROOT / "docs" / "00_gobernanza" / "fuentes_precedencia_y_conflictos.md").read_text(encoding="utf-8")

    envelope = model["envelope"]
    width = float(envelope["width_y_m"])
    depth = float(envelope["depth_x_m"])
    p2_depth = depth - float(envelope["p2_start_x_m"])
    pb_area = width * depth
    p2_area = width * p2_depth
    total_area = pb_area + p2_area

    documents = len(list((ROOT / "docs").rglob("*.md")))
    decisions = len(re.findall(r"^\| D-\d+ \|", decisions_text, re.MULTILINE))
    open_conflicts = len(re.findall(r"\*\*Status:\*\*[^\n]*open", conflicts_text, re.IGNORECASE))
    sheets = len({item["relative"] for item in discover_outputs()})
    current_sheets = len(load_json(CURRENT_MANIFEST).get("drawings", []))

    phase = extract_list_value(readme, "Phase", "dimensional schematic design")
    blocker = extract_list_value(readme, "Primary blocker", "site selection and investigations")

    return {
        "project": "Dream House",
        "version": extract_meta(docs_index, "Version", "0.3"),
        "date": extract_meta(docs_index, "Date", "2026-08-12"),
        "status": extract_meta(docs_index, "Status", "active"),
        "phase": phase.rstrip("."),
        "blocker": blocker.rstrip("."),
        "dimensions": {
            "width": width,
            "depth": depth,
            "pb_area": pb_area,
            "p2_area": p2_area,
            "total_area": total_area,
        },
        "counts": {
            "documents": documents,
            "decisions": decisions,
            "open_conflicts": open_conflicts,
            "sheets": sheets,
            "current_sheets": current_sheets,
        },
        "gallery": gallery,
    }


def _is_coordination_package(path: Path) -> bool:
    if (path / "latest.json").is_file() and (path / "issues").is_dir():
        return True
    if (path / "current.json").is_file() and (path / "releases").is_dir():
        return True
    if (path / "release.json").is_file() and (path / "source_candidate_manifest.json").is_file():
        return True
    manifest_path = path / "manifest.json"
    if manifest_path.is_file():
        if all((path / name).is_file() for name in ("model.json", "changes.json", "index.html")):
            return True
        try:
            manifest = load_json(manifest_path)
        except (OSError, json.JSONDecodeError):
            return False
        if not isinstance(manifest, dict):
            return False
        return (
            manifest.get("purpose") == "coordination review"
            and manifest.get("build_status") == "complete"
        )
    return False


def _contains_coordination_package(path: Path) -> bool:
    """Find coordination package roots without following symlink directories."""
    for directory, subdirectories, _filenames in os.walk(path, followlinks=False):
        current = Path(directory)
        subdirectories[:] = [name for name in subdirectories if not (current / name).is_symlink()]
        if _is_coordination_package(current):
            return True
    return False


def render_readme_block(data: dict) -> str:
    counts = data["counts"]
    rows: list[str] = []
    gallery = data["gallery"]
    for index in range(0, len(gallery), 2):
        pair = gallery[index : index + 2]
        cells = []
        for item in pair:
            path = html.escape(item["relative"], quote=True)
            image_path = html.escape(item["image_relative"], quote=True)
            source_path = html.escape(item["source_relative"], quote=True)
            alt = html.escape(item["alt"], quote=True)
            title = html.escape(item["title"])
            eyebrow = html.escape(item["eyebrow"])
            revision = html.escape(item["revision"])
            cells.append(
                "\n".join(
                    [
                        '<td width="50%" valign="top">',
                        f'  <a href="{path}"><img src="{image_path}" alt="{alt}" width="100%"></a>',
                        f"  <br><sub><strong>{eyebrow}</strong> · {revision}</sub>",
                        f"  <br><strong>{title}</strong>",
                        f'  <br><sub><a href="{source_path}">Versioned source</a> · scalable current SVG above · PNG fallback in <code>planos/actual/</code></sub>',
                        "</td>",
                    ]
                )
            )
        rows.append("<tr>\n" + "\n".join(cells) + "\n</tr>")

    return "\n".join(
        [
            BEGIN,
            '<p align="center">',
            f'  <sub><strong>{counts["current_sheets"]}</strong> current SVG/PNG pairs · <strong>{counts["sheets"]}</strong> preserved versioned sheets · <strong>{counts["documents"]}</strong> documents · <strong>{counts["decisions"]}</strong> decisions · <strong>{counts["open_conflicts"]}</strong> open conflicts</sub>',
            "</p>",
            "",
            "<table>",
            *rows,
            "</table>",
            "",
            '<p align="center"><sub>Every thumbnail is the stable, scalable SVG in <code>planos/actual/</code>; open it to zoom without losing quality or follow its versioned source for history.</sub></p>',
            END,
        ]
    )


def updated_readme(data: dict) -> str:
    current = README.read_text(encoding="utf-8")
    if BEGIN not in current or END not in current:
        raise RuntimeError("README.md does not contain the automatic gallery markers")
    before, remainder = current.split(BEGIN, 1)
    _, after = remainder.split(END, 1)
    return before + render_readme_block(data) + after


def write_or_check_readme(data: dict, write: bool, check: bool) -> None:
    generated = updated_readme(data)
    current = README.read_text(encoding="utf-8")
    if write:
        README.write_text(generated, encoding="utf-8", newline="\n")
        print("README.md updated from the manifests.")
    if check and generated != current:
        print(
            "README.md does not match the manifests. Run: "
            "python .github/scripts/build_showcase.py --write-readme",
            file=sys.stderr,
        )
        raise SystemExit(1)


def build_site(data: dict, destination: Path, *, coordination_out: Path | None = None) -> None:
    destination = Path(destination)
    if destination.is_symlink():
        raise RuntimeError("Site destination cannot be a symlink")
    destination = destination.resolve()
    if destination == ROOT or ROOT not in destination.parents:
        raise RuntimeError("The site destination must be a directory inside the repository")
    if (
        destination == BUILD_ROOT
        or destination == COORDINATION_ROOT
        or destination.is_relative_to(COORDINATION_ROOT)
        or COORDINATION_ROOT.is_relative_to(destination)
    ):
        raise RuntimeError("Site output must not contain or replace .build/coordination")
    if any(
        destination == ROOT / name or destination.is_relative_to(ROOT / name)
        for name in (".git", ".github", "docs", "dreamhouse", "planos", "showcase")
    ):
        raise RuntimeError("Site output must not overwrite repository source directories")

    # A previously generated static site contains a copied review package under
    # coordination/. It is safe to replace that export after the new site is verified;
    # standalone candidate/release roots anywhere else must remain untouched.
    if destination.exists() and _is_coordination_package(destination):
        raise RuntimeError("Site output cannot replace a coordination package root")
    generated_site = (destination / ".nojekyll").is_file() and (
        destination / "index.html"
    ).is_file()
    if destination.exists() and not generated_site and _contains_coordination_package(destination):
        raise RuntimeError("Site output contains a coordination package and cannot be replaced")
    for parent in destination.parents:
        if parent == BUILD_ROOT.parent:
            break
        if _is_coordination_package(parent):
            raise RuntimeError("Site output cannot be inside a coordination package root")

    release = None
    if coordination_out is not None:
        # Direct script execution exposes .github/scripts, not the repository root.
        # Resolve the checked-out verifier even without an editable package install.
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        from dreamhouse.coordination.publication import read_current_release

        coordination_out = coordination_out.resolve()
        if (coordination_out == destination or coordination_out.is_relative_to(destination)
                or destination.is_relative_to(coordination_out)):
            raise RuntimeError("Site output must not contain the coordination source package")
        release = read_current_release(coordination_out / "published", require_fresh=True)

    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    (destination / "assets").mkdir()
    (destination / "media").mkdir()

    source = ROOT / "showcase"
    html_source = (source / "index.html").read_text(encoding="utf-8")
    public_data = {
        **{key: value for key, value in data.items() if key != "gallery"},
        "gallery": [],
    }

    for item in data["gallery"]:
        media_name = f'{item["slug"]}{item["image_path"].suffix.lower()}'
        shutil.copy2(item["image_path"], destination / "media" / media_name)
        public_data["gallery"].append(
            {
                "slug": item["slug"],
                "eyebrow": item["eyebrow"],
                "title": item["title"],
                "summary": item["summary"],
                "alt": item["alt"],
                "revision": item["revision"],
                "src": f"media/{media_name}",
                "href": f"media/{media_name}",
                "source_href": f'{REPO_URL}/blob/main/{item["source_relative"]}',
            }
        )

    payload = json.dumps(public_data, ensure_ascii=False).replace("</", "<\\/")
    marker = "<!-- showcase:data -->"
    if marker not in html_source:
        raise RuntimeError("The data marker is missing from showcase/index.html")
    built_html = html_source.replace(
        marker,
        f'<script id="showcase-data" type="application/json">{payload}</script>',
    )
    connected_link = ""
    if release is not None:
        release_id = release["release_id"]
        public_root = destination / "coordination"
        public_release = public_root / "releases" / release_id
        shutil.copytree(release["path"], public_release)
        for name, expected in release["release"]["artifacts"].items():
            if hashlib.sha256((public_release / name).read_bytes()).hexdigest() != expected:
                raise RuntimeError(f"Connected review changed during site export: {name}")
        shutil.copy2(release["bootstrap_path"], public_root / "index.html")
        (public_root / "current.json").write_text(
            json.dumps(release["pointer"], sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
        # A source edit during the export must fail the whole site build.
        latest = read_current_release(coordination_out / "published", require_fresh=True)
        if latest["release_id"] != release_id:
            raise RuntimeError("Selected review changed during site export")
        connected_link = (
            '<p class="gallery__intro"><a class="button button--line" '
            'href="coordination/index.html">Open the connected coordination review</a>'
            '<br><small>Generated plans, calculations and unresolved interfaces from one '
            'source revision. Schematic review; not for construction.</small></p>'
        )
    built_html = built_html.replace("<!-- showcase:coordination -->", connected_link)
    (destination / "index.html").write_text(built_html, encoding="utf-8", newline="\n")
    shutil.copy2(source / "styles.css", destination / "styles.css")
    shutil.copy2(source / "app.js", destination / "app.js")
    for asset_name in ("dream-house-cover.svg", "dream-house-cover-mobile.svg", "favicon.svg"):
        shutil.copy2(ROOT / ".github" / "assets" / asset_name, destination / "assets" / asset_name)
    (destination / ".nojekyll").write_text("", encoding="utf-8")
    print(f"Site built at {destination.relative_to(ROOT)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-readme", action="store_true", help="update the automatic README block")
    parser.add_argument("--check-readme", action="store_true", help="fail if the automatic README block is outdated")
    parser.add_argument("--site-dir", type=Path, help="build the static site in this directory")
    parser.add_argument("--coordination-out", type=Path, help="include the verified current review release from this coordination output root")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.coordination_out and not args.site_dir:
        raise SystemExit("--coordination-out requires --site-dir")
    if not (args.write_readme or args.check_readme or args.site_dir):
        raise SystemExit("Specify --write-readme, --check-readme, or --site-dir")
    gallery = select_gallery()
    data = project_data(gallery)
    write_or_check_readme(data, args.write_readme, args.check_readme)
    if args.site_dir:
        destination = args.site_dir if args.site_dir.is_absolute() else ROOT / args.site_dir
        build_site(data, destination, coordination_out=args.coordination_out)


if __name__ == "__main__":
    main()
