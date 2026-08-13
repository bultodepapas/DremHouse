#!/usr/bin/env python3
"""Build the Dream House README gallery and its static GitHub Pages showcase.

The script intentionally uses only the Python standard library so the repository can
regenerate its presentation in GitHub Actions without installing dependencies.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
REPO_URL = "https://github.com/bultodepapas/DremHouse"
BEGIN = "<!-- showcase:begin -->"
END = "<!-- showcase:end -->"


@dataclass(frozen=True)
class GalleryRule:
    slug: str
    eyebrow: str
    title: str
    summary: str
    alt: str
    matches: Callable[[str], bool]


RULES = (
    GalleryRule(
        "planta-baja",
        "Arquitectura · PB",
        "La nave como un solo recinto",
        "Talleres, vacío monumental, vida doméstica y núcleo posterior coordinados en una planta continua.",
        "Lámina técnica de la planta baja detallada de Dream House",
        lambda name: "PLN-001" in name and "PB" in name and "DETALLADA" in name,
    ),
    GalleryRule(
        "segundo-piso",
        "Arquitectura · P2",
        "Privacidad anclada al fondo",
        "Cuatro suites, wellness y servicios preservan la doble altura delantera y la frontera de fases.",
        "Lámina técnica del segundo piso detallado de Dream House",
        lambda name: "PLN-002" in name and "P2" in name and "DETALLADA" in name,
    ),
    GalleryRule(
        "cubierta",
        "Arquitectura · cubierta",
        "Un solo gesto transversal",
        "La cubierta mono-pendiente mantiene la lectura de una nave única y concentra el drenaje en un alero.",
        "Corte transversal de la cubierta mono-pendiente de Dream House",
        lambda name: "SEC-002" in name and "TRANSVERSAL-CUBIERTA" in name,
    ),
    GalleryRule(
        "estructura",
        "Ingeniería · E0",
        "La estructura queda a la vista",
        "Retícula, cerchas, arriostramientos y entrepiso se comparan como hipótesis antes del cálculo profesional.",
        "Lámina de inspección del esquema estructural E0 de Dream House",
        lambda name: "ESTRUCTURA-INSPECCION" in name,
    ),
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def score_revision(revision: str, filename: str, manifest: Path) -> tuple[int, ...]:
    text = f"{revision} {filename} {manifest.parent.name}"
    numbers = tuple(int(value) for value in re.findall(r"\d+", text))
    return numbers or (0,)


def discover_outputs() -> list[dict]:
    outputs: list[dict] = []
    for manifest in sorted((ROOT / "planos").rglob("manifest.json")):
        data = load_json(manifest)
        revision = str(data.get("revision", "sin revisión"))
        for output in data.get("outputs", []):
            candidate = manifest.parent / output
            if candidate.suffix.lower() != ".svg" or not candidate.is_file():
                continue
            relative = candidate.relative_to(ROOT).as_posix()
            outputs.append(
                {
                    "path": candidate,
                    "relative": relative,
                    "filename": candidate.name,
                    "revision": revision,
                    "score": score_revision(revision, candidate.name, manifest),
                }
            )
    return outputs


def select_gallery() -> list[dict]:
    outputs = discover_outputs()
    gallery: list[dict] = []
    for rule in RULES:
        candidates = [item for item in outputs if rule.matches(item["filename"])]
        if not candidates:
            raise RuntimeError(f"No se encontró una lámina para la categoría {rule.slug!r}")
        selected = max(candidates, key=lambda item: item["score"])
        gallery.append(
            {
                **selected,
                "slug": rule.slug,
                "eyebrow": rule.eyebrow,
                "title": rule.title,
                "summary": rule.summary,
                "alt": rule.alt,
            }
        )
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
    open_conflicts = len(re.findall(r"\*\*Estado:\*\*[^\n]*abierto", conflicts_text, re.IGNORECASE))
    sheets = len({item["relative"] for item in discover_outputs()})

    phase = extract_list_value(readme, "Fase", "anteproyecto dimensional")
    blocker = extract_list_value(readme, "Bloqueador principal", "selección y estudios del predio")

    return {
        "project": "Dream House",
        "version": extract_meta(docs_index, "Versión", "0.2"),
        "date": extract_meta(docs_index, "Fecha", "2026-08-11"),
        "status": extract_meta(docs_index, "Estatus", "activo"),
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
        },
        "gallery": gallery,
    }


def render_readme_block(data: dict) -> str:
    counts = data["counts"]
    rows: list[str] = []
    gallery = data["gallery"]
    for index in range(0, len(gallery), 2):
        pair = gallery[index : index + 2]
        cells = []
        for item in pair:
            path = html.escape(item["relative"], quote=True)
            alt = html.escape(item["alt"], quote=True)
            title = html.escape(item["title"])
            eyebrow = html.escape(item["eyebrow"])
            revision = html.escape(item["revision"])
            cells.append(
                "\n".join(
                    [
                        '<td width="50%" valign="top">',
                        f'  <a href="{path}"><img src="{path}" alt="{alt}" width="100%"></a>',
                        f"  <br><sub><strong>{eyebrow}</strong> · {revision}</sub>",
                        f"  <br><strong>{title}</strong>",
                        "</td>",
                    ]
                )
            )
        rows.append("<tr>\n" + "\n".join(cells) + "\n</tr>")

    return "\n".join(
        [
            BEGIN,
            '<p align="center">',
            f'  <sub><strong>{counts["sheets"]}</strong> láminas vectoriales · <strong>{counts["documents"]}</strong> documentos · <strong>{counts["decisions"]}</strong> decisiones registradas · <strong>{counts["open_conflicts"]}</strong> conflictos abiertos</sub>',
            "</p>",
            "",
            "<table>",
            *rows,
            "</table>",
            "",
            '<p align="center"><sub>Selección regenerada desde los <code>manifest.json</code>; haz clic en una lámina para verla a resolución completa.</sub></p>',
            END,
        ]
    )


def updated_readme(data: dict) -> str:
    current = README.read_text(encoding="utf-8")
    if BEGIN not in current or END not in current:
        raise RuntimeError("El README no contiene los marcadores de la galería automática")
    before, remainder = current.split(BEGIN, 1)
    _, after = remainder.split(END, 1)
    return before + render_readme_block(data) + after


def write_or_check_readme(data: dict, write: bool, check: bool) -> None:
    generated = updated_readme(data)
    current = README.read_text(encoding="utf-8")
    if write:
        README.write_text(generated, encoding="utf-8", newline="\n")
        print("README.md actualizado desde los manifiestos.")
    if check and generated != current:
        print(
            "README.md no coincide con los manifiestos. Ejecuta: "
            "python .github/scripts/build_showcase.py --write-readme",
            file=sys.stderr,
        )
        raise SystemExit(1)


def build_site(data: dict, destination: Path) -> None:
    destination = destination.resolve()
    if destination == ROOT or ROOT not in destination.parents:
        raise RuntimeError("El destino del sitio debe ser una carpeta dentro del repositorio")

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
        media_name = f'{item["slug"]}{item["path"].suffix.lower()}'
        shutil.copy2(item["path"], destination / "media" / media_name)
        public_data["gallery"].append(
            {
                "slug": item["slug"],
                "eyebrow": item["eyebrow"],
                "title": item["title"],
                "summary": item["summary"],
                "alt": item["alt"],
                "revision": item["revision"],
                "src": f"media/{media_name}",
                "href": f'{REPO_URL}/blob/main/{item["relative"]}',
            }
        )

    payload = json.dumps(public_data, ensure_ascii=False).replace("</", "<\\/")
    marker = "<!-- showcase:data -->"
    if marker not in html_source:
        raise RuntimeError("Falta el marcador de datos en showcase/index.html")
    built_html = html_source.replace(
        marker,
        f'<script id="showcase-data" type="application/json">{payload}</script>',
    )
    (destination / "index.html").write_text(built_html, encoding="utf-8", newline="\n")
    shutil.copy2(source / "styles.css", destination / "styles.css")
    shutil.copy2(source / "app.js", destination / "app.js")
    for asset_name in ("dream-house-cover.svg", "dream-house-cover-mobile.svg", "favicon.svg"):
        shutil.copy2(ROOT / ".github" / "assets" / asset_name, destination / "assets" / asset_name)
    (destination / ".nojekyll").write_text("", encoding="utf-8")
    print(f"Sitio construido en {destination.relative_to(ROOT)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-readme", action="store_true", help="actualiza el bloque automático del README")
    parser.add_argument("--check-readme", action="store_true", help="falla si el bloque automático está desactualizado")
    parser.add_argument("--site-dir", type=Path, help="construye el sitio estático en esta carpeta")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not (args.write_readme or args.check_readme or args.site_dir):
        raise SystemExit("Indica --write-readme, --check-readme o --site-dir")
    gallery = select_gallery()
    data = project_data(gallery)
    write_or_check_readme(data, args.write_readme, args.check_readme)
    if args.site_dir:
        destination = args.site_dir if args.site_dir.is_absolute() else ROOT / args.site_dir
        build_site(data, destination)


if __name__ == "__main__":
    main()
