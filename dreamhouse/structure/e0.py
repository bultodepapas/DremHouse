"""Orquestador del modelo E0: matriz sistemas x modulaciones y salidas."""

from __future__ import annotations

import csv
import hashlib
import html
import json
import sys
from pathlib import Path

import numpy as np

from .materials import materials_from_json
from .portal import build_frame_model
from .quantities import compute_quantities
from .profiles import profile

ROOT = Path(__file__).resolve().parents[2]
DATA = Path(__file__).with_name("structure_system.json")
OUT = ROOT / "planos" / "estructura_e0"

META = {
    "generator": "dreamhouse/structure/e0.py",
    "model": "E0 — esquema estructural (no diseño profesional)",
    "label": "NO APTO PARA CONSTRUIR",
    "date": "2026-08-11",
}


def main() -> None:
    cfg = json.loads(DATA.read_text(encoding="utf-8"))
    materials = materials_from_json(cfg)
    steel = materials["S355"]
    phi_b = cfg["criteria"]["phi_bending"]
    phi_c = cfg["criteria"]["phi_axial"]

    rows = []
    for modulation in cfg["geometry"]["modulations"]:
        bay = modulation["bay_m"]
        n_bays = modulation["n_bays"]
        q = compute_quantities(cfg, steel, bay, n_bays, phi_b, phi_c)
        rows.append({"modulation": modulation["id"], "quantities": q})

    report = {
        "project": cfg["project"],
        "meta": META,
        "materials": {"principales": "S355/A572-50", "secundarios": "S235/A36", "E_mpa": 200000},
        "no_snow": cfg["loads"]["note_no_snow"],
        "matrix": rows,
        "targets": {
            "total_steel_t_range": cfg["criteria"]["target_total_steel_t"],
            "kg_m2_reference": cfg["criteria"]["target_kg_m2_reference"],
        },
    }
    OUT.mkdir(parents=True, exist_ok=True)

    summary = summarize(rows)
    report["summary"] = summary

    (OUT / "DH-EST-E0-001_resultados.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "DH-EST-E0-001_resumen.md").write_text(markdown_report(cfg, rows, summary), encoding="utf-8")
    write_csv(rows)
    for system in cfg["systems"]:
        write_svg(system["id"])

    for m in cfg["geometry"]["modulations"]:
        write_svg_section(f"{m['id']}_SECCION")

    digest = hashlib.sha256(DATA.read_bytes()).hexdigest()
    manifest = {
        "input": str(DATA.relative_to(ROOT)),
        "input_sha256": digest,
        "generator": META["generator"],
        "revision": cfg["project"]["revision"],
        "outputs": [
            "DH-EST-E0-001_resultados.json",
            "DH-EST-E0-001_resumen.md",
            "DH-EST-E0-001_resumen.csv",
            *[f"DH-EST-E0-001_{s['id']}.svg" for s in cfg["systems"]],
            *[f"DH-EST-E0-001_SECCION-{m['id']}.svg" for m in cfg["geometry"]["modulations"]],
            "manifest.json",
        ],
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))


def summarize(rows: list[dict]) -> dict:
    out = {}
    for row in rows:
        mod = row["modulation"]
        for sid, q in row["quantities"]["systems"].items():
            out[f"{mod}-{sid}"] = {
                "total_t": q["total_t"],
                "kg_m2": q["kg_m2"],
                "main_t": round(q["main_frames_kg"] / 1000.0, 1),
                "p2_metaldeck_t": round(q["p2_floor_metaldeck_kg"] / 1000.0, 1),
                "p2_staggered_t": round(q["p2_floor_staggered_kg"] / 1000.0, 1),
                "p2_interior_columns": q["staggered"]["interior_columns"],
                "secondary_t": round(q["secondary_kg"] / 1000.0, 1),
                "column": q["frames"].get("column", "-"),
                "rafter": q["frames"].get("rafter", q["frames"].get("truss_chord", "-")),
                "tie_area_cm2": q["frames"].get("tie_area_cm2", 0.0),
                "tie_force_kn": q["frames"].get("tie_force_kn", 0.0),
                "drift_m": q["frames"].get("drift_m", None),
            }
    return out


def markdown_report(cfg: dict, rows: list[dict], summary: dict) -> str:
    lines = [
        "# Modelo E0 — comparación estructural (D-019)",
        "",
        "**Estatus:** hipótesis de esquema · **NO APTO PARA CONSTRUIR**",
        f'**Fecha:** {META["date"]} · **Revisión:** {cfg["project"]["revision"]}',
        "",
        "> " + cfg["loads"]["note_no_snow"],
        "",
        "| Sistema × Modulación | Columnas | Viga/cercha | Pórticos | Acero total | kg/m² |",
        "|---|---|---|---|---:|---:|",
    ]
    for row in rows:
        mod = row["modulation"]
        for sid, q in row["quantities"]["systems"].items():
            f = q["frames"]
            col = f.get("column", "-")
            roof = f.get("rafter", f.get("truss_chord", "-"))
            lines.append(f"| {mod} · {sid} | {col} | {roof} | {row['quantities']['modulation']['n_portal_lines']} | **{q['total_t']} t** | {q['kg_m2']} |")
    lines += [
        "",
        "## Desglose por componente (t)",
        "",
        "| Sistema × Modulación | Marcos principales | Entrepiso P2 (metaldeck) | Entrepiso P2 (staggered) | Secundaria | Total |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        mod = row["modulation"]
        for sid, q in row["quantities"]["systems"].items():
            lines.append(
                f"| {mod} · {sid} | {q['main_frames_kg']/1000:.1f} | {q['p2_floor_metaldeck_kg']/1000:.1f} | {q['p2_floor_staggered_kg']/1000:.1f} | {q['secondary_kg']/1000:.1f} | {q['total_t']} |"
            )
    lines += [
        "",
        "## Entrepiso P2 — opciones comparadas",
        "",
        "La opción **STAGGERED** (cerchas escalonadas de 18 m entre los muros largos, "
        "ocultas en las particiones de las suites) elimina por completo las columnas "
        "interiores de la zona doméstica de PB (cocina/comedor). La opción METALDECK "
        "de la línea base requiere dos apoyos intermedios por pórtico en cocina/núcleo.",
    ]
    staggered_first = list(rows[0]["quantities"]["systems"].values())[0]["staggered"]
    lines.append(f"- Cercha staggered ({rows[0]['modulation']}): {staggered_first['n_trusses']} cerchas de 18 m, canto ≈ {staggered_first['truss_depth_m']} m, cordones {staggered_first['chord']}, flecha ≈ {staggered_first['truss_deflection_m']} m.")
    lines += [
        "",
        "## Objetivos de control (auditoría)",
        "",
        f"- Acero total realista: **{cfg['criteria']['target_total_steel_t'][0]}–{cfg['criteria']['target_total_steel_t'][1]} t** "
        f"(desglose v0.2: 28,35 t, subestimado).",
        f"- Equivalente: **{cfg['criteria']['target_kg_m2_reference'][0]}–{cfg['criteria']['target_kg_m2_reference'][1]} kg/m²** sobre 918 m².",
        "",
        "## Hallazgos del modelo E0 (11-08-2026)",
        "",
        "1. **Los pórticos con bases articuladas quedan gobernados por la deriva de viento (H/200):** "
        "columnas HEA500 en las tres modulaciones (peso principal ≈ 30–40 t). El control de la "
        "auditoría (HEA300, 23–24 t) no cumple la deriva de servicio con el viento de hipótesis "
        "E0; es una decisión del ingeniero en E1 si relaja el límite o introduce arriostramiento/rigidización.",
        "2. **El sistema de cerchas con columnas articuladas y arriostramiento pesa ≈ 36–40 t** "
        "(ahorro ≈ 30 % sobre pórticos) y resuelve la deriva con columnas HEA200; el costo extra "
        "de fabricación de la cercha debe cotizarse antes de decidir (E1, puerta PE-1).",
        "3. **Pórtico atado (PORTICO-T):** el tirante entre los apoyos de la cercha queda casi "
        "inactivo (≈ 2 kN) porque la deriva de viento es un sway en la misma dirección de ambos "
        "muros; el tirante solo resiste la apertura de aleros por empuje gravitatorio, que aquí "
        "no gobierna. Añade peso (≈ 1,4 t/pórtico) sin beneficio de deriva: **no es competitivo "
        "en este caso de carga.** Su papel clásico (empuje de cubierta en edificios con grúa) no aplica.",
        "4. **Pórtico con bases fijas (PORTICO-F):** es el control efectivo de deriva para el "
        "sistema de pórticos. Permite columna HEA300 con deriva ≈ 0,016–0,021 m (vs. HEA500 "
        "articulado) y un marco ≈ 27 % más liviano; el costo pasa a la cimentación (momento en la base).",
        "5. **Entrepiso P2:** la línea base METALDECK con dos apoyos intermedios por pórtico pesa "
        "≈ 12,0 t (M60) pero introduce columnas en cocina/núcleo. La opción **STAGGERED** elimina "
        "esas columnas (cero apoyos interiores) con tonelaje comparable (≈ 10,7–15,8 t según "
        "modulación); la planta v0.4 y el modelo E1 deben verificar peso, canto y vibración.",
        "6. **Cubierta de un solo faldón ≈ 1:30:** la flecha de la viga de cubierta queda "
        "controlada por resistencia (viento/succión), no por flecha, con IPE450–IPE550 según modulación.",
        "",
        "## Supuestos críticos de este modelo",
        "",
        "- Cargas y combinaciones son **hipótesis de ingeniero**, versionadas en `structure_system.json`; no es biblioteca NSR-10.",
        "- Sin carga de nieve (Boyacá). Viento y sismo como hipótesis E0 hasta definir municipio.",
        "- Pórticos con bases articuladas por defecto; PORTICO-T añade tirante de alero; PORTICO-F empotra las bases.",
        "- Entrepiso P2: METALDECK (viguetas + vigas de 18 m + apoyos intermedios) vs. STAGGERED (cerchas escalonadas sin columnas interiores).",
        "- Factor de detalle 15 % y desperdicio 5 %; perfiles de stock IPE/HEA/HSS.",
        "- Cada resultado debe ser revisado por el ingeniero estructural antes de cruzar PE-1.",
    ]
    return "\n".join(lines) + "\n"


def write_csv(rows: list[dict]) -> None:
    path = OUT / "DH-EST-E0-001_resumen.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["modulacion", "sistema", "columnas", "viga_cercha", "tirante_cm2", "marcos_t", "entrepiso_p2_metaldeck_t", "entrepiso_p2_staggered_t", "secundaria_t", "total_t", "kg_m2", "drift_m"])
        for row in rows:
            mod = row["modulation"]
            for sid, q in row["quantities"]["systems"].items():
                f = q["frames"]
                writer.writerow([
                    mod, sid, f.get("column", "-"), f.get("rafter", f.get("truss_chord", "-")),
                    f.get("tie_area_cm2", 0.0),
                    round(q["main_frames_kg"] / 1000.0, 2),
                    round(q["p2_floor_metaldeck_kg"] / 1000.0, 2),
                    round(q["p2_floor_staggered_kg"] / 1000.0, 2),
                    round(q["secondary_kg"] / 1000.0, 2), q["total_t"], q["kg_m2"],
                    f.get("drift_m", ""),
                ])


def _svg_header(title: str, subtitle: str) -> list[str]:
    return [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="720" viewBox="0 0 1120 720">',
        '<rect width="1120" height="720" fill="#fbfaf7"/>',
        f'<text x="75" y="48" font-family="Arial" font-size="22" font-weight="700" fill="#20292e">{html.escape(title)}</text>',
        f'<text x="75" y="76" font-family="Arial" font-size="13" fill="#566269">{html.escape(subtitle)}</text>',
        f'<text x="1045" y="76" text-anchor="end" font-size="13" font-weight="700" fill="#8e3825">{META["label"]}</text>',
    ]


def _frame_node_coords(eave_low: float, eave_high: float, has_p2: bool, p2_level: float) -> dict:
    scale = 30.0
    x0, y0 = 260.0, 470.0
    z = lambda h: y0 - h * scale
    nodes = {
        "base_low": (x0, y0),
        "top_low": (x0, z(eave_low)),
        "base_high": (x0 + 18 * scale, y0),
        "top_high": (x0 + 18 * scale, z(eave_high)),
        "roof_mid": (x0 + 9 * scale, z((eave_low + eave_high) / 2)),
    }
    if has_p2:
        nodes["p2_low"] = (x0, z(p2_level))
        nodes["p2_high"] = (x0 + 18 * scale, z(p2_level))
    return nodes


def write_svg(system_id: str) -> None:
    cfg = json.loads(DATA.read_text(encoding="utf-8"))
    materials = materials_from_json(cfg)
    steel = materials["S355"]
    eave_low = cfg["geometry"]["eave_low_m"]
    eave_high = cfg["geometry"]["eave_high_m"]
    p2_level = cfg["geometry"]["p2_floor_level_m"]
    has_p2 = True

    if system_id.startswith("PORTICO"):
        cfg_sys = next(s for s in cfg["systems"] if s["id"] == system_id)
        col = profile("HEA300")
        rafter = profile("IPE500")
        nodes = _frame_node_coords(eave_low, eave_high, has_p2, p2_level)
        label = "PÓRTICO TRANSVERSAL"
        sub = "Esquema E0 · columna HEA + viga IPE con cartela de alero · bases articuladas"
        if cfg_sys.get("tie"):
            sub = "Esquema E0 · pórtico atado con tirante entre los apoyos de la cercha (triángulo rígido) · bases articuladas"
        if cfg_sys.get("fixed_base"):
            sub = "Esquema E0 · columna HEA + viga IPE con cartela · bases empotradas"
        parts = _svg_header(f"{label} — {system_id}", sub)
    else:
        col = profile("HEA200")
        rafter = profile("IPE220")
        nodes = _frame_node_coords(eave_low, eave_high, has_p2, p2_level)
        nodes["roof_mid"] = (nodes["top_low"][0] + 9 * 30.0, nodes["top_low"][1] - 30.0 * 1.125)
        parts = _svg_header(f"CERCHA TRANSVERSAL — {system_id}", "Esquema E0 · cuerdas tubulares HSS + diagonalizado · profundidad L/16 ≈ 1,13 m")
    _ = (col, rafter)

    parts.append('<g font-family="Arial" fill="#20292e">')
    for name, (px, py) in nodes.items():
        parts.append(f'<circle cx="{px}" cy="{py}" r="4.5" fill="#b8841e"/>')
        if name in ("base_low", "base_high"):
            parts.append(f'<path d="M {px-14} {py} L {px+14} {py} L {px-8} {py+9} L {px+8} {py+9}" fill="none" stroke="#566269" stroke-width="1.5"/>')

    def line(a: str, b: str, color: str = "#172126", width: float = 7.0):
        x1, y1 = nodes[a]
        x2, y2 = nodes[b]
        parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"/>')

    line("base_low", "top_low")
    line("base_high", "top_high")
    if has_p2:
        line("base_low", "p2_low")
        line("p2_low", "top_low")
        line("base_high", "p2_high")
        line("p2_high", "top_high")
    if system_id.endswith("-T"):
        line("top_low", "top_high", color="#27859a", width=3.0)
    line("top_low", "roof_mid")
    line("roof_mid", "top_high")

    x0, y0 = nodes["base_low"]
    parts.append(f'<line x1="{x0}" y1="{y0+20}" x2="{x0+540}" y2="{y0+20}" stroke="#566269" stroke-width="1"/>')
    parts.append(f'<text x="{x0+270}" y="{y0+42}" text-anchor="middle" font-size="13" font-weight="700">18,00 m</text>')
    parts.append(f'<line x1="{x0-55}" y1="{y0}" x2="{x0-55}" y2="{y0-7.2*30}" stroke="#566269" stroke-width="1"/>')
    parts.append(f'<text x="{x0-65}" y="{y0-3.6*30}" text-anchor="middle" font-size="12" font-weight="700" transform="rotate(-90 {x0-65} {y0-3.6*30})">H ≈ 7,20 m</text>')
    parts.append(f'<line x1="{x0+540+55}" y1="{y0}" x2="{x0+540+55}" y2="{y0-7.8*30}" stroke="#566269" stroke-width="1"/>')
    parts.append(f'<text x="{x0+540+65}" y="{y0-3.9*30}" text-anchor="middle" font-size="12" font-weight="700" transform="rotate(90 {x0+540+65} {y0-3.9*30})">H ≈ 7,80 m</text>')
    if has_p2:
        px, py = nodes["p2_low"]
        parts.append(f'<line x1="{px}" y1="{py}" x2="{px+540}" y2="{py}" stroke="#27859a" stroke-width="2" stroke-dasharray="9 5"/>')
        parts.append(f'<text x="{px+270}" y="{py-10}" text-anchor="middle" font-size="12" font-weight="700" fill="#246b7a">NIVEL P2 ≈ +3,80 · ENTREPISO METALDECK</text>')

    parts.append("</g>")
    parts.append(
        '<rect x="75" y="625" width="970" height="62" fill="#fff3dc" stroke="#bc5c3c" stroke-width="1.5"/>'
        '<text x="95" y="650" font-family="Arial" font-size="17" font-weight="700" fill="#8e3825">HIPÓTESIS DE ESQUEMA E0 — NO APTO PARA CONSTRUIR</text>'
        '<text x="95" y="674" font-family="Arial" font-size="11" fill="#4d5559">Cargas, combinaciones y perfiles son hipótesis de ingeniero (structure_system.json). Sin nieve (Boyacá). Requiere revisión del ingeniero estructural antes de PE-1.</text>'
        "</svg>"
    )
    (OUT / f"DH-EST-E0-001_{system_id}.svg").write_text("".join(parts), encoding="utf-8")


def write_svg_section(name: str) -> None:
    cfg = json.loads(DATA.read_text(encoding="utf-8"))
    eave_low = cfg["geometry"]["eave_low_m"]
    eave_high = cfg["geometry"]["eave_high_m"]
    scale = 14.0
    x0, y0 = 150.0, 430.0
    parts = _svg_header(f"SECCIÓN LONGITUDINAL ESQUEMÁTICA — {name}", "Doble altura delantera ≈ 21 m + P2 posterior ≈ 15 m · cubierta de un solo faldón")
    parts.append('<g font-family="Arial" fill="#20292e">')
    z = lambda h: y0 - h * scale
    parts.append(f'<rect x="{x0}" y="{z(eave_low)}" width="{21*scale}" height="{(eave_low)*scale}" fill="#eee9df" stroke="#172126" stroke-width="3"/>')
    parts.append(f'<rect x="{x0+21*scale}" y="{z(eave_high)}" width="{15*scale}" height="{(eave_high)*scale}" fill="#e3d6c4" stroke="#172126" stroke-width="3"/>')
    parts.append(f'<line x1="{x0}" y1="{z(3.8)}" x2="{x0+36*scale}" y2="{z(3.8)}" stroke="#27859a" stroke-width="2.5"/>')
    parts.append(f'<text x="{x0+21*scale}" y="{z(3.8)-10}" text-anchor="middle" font-size="12" font-weight="700" fill="#246b7a">P2 ≈ +3,80</text>')
    parts.append(f'<text x="{x0+10*scale}" y="{z(eave_low)-14}" text-anchor="middle" font-size="13" font-weight="700">DOBLE ALTURA ≈ 21 m · 378 m²</text>')
    parts.append(f'<text x="{x0+28*scale}" y="{z(eave_high)-14}" text-anchor="middle" font-size="13" font-weight="700">P2 ≈ 15 m · 270 m²</text>')
    parts.append(f'<text x="{x0+3*scale}" y="{z(2.2)}" text-anchor="middle" font-size="11" fill="#5c666b">TÉCNICA + MONUMENTAL (car, RC, sala)</text>')
    parts.append(f'<text x="{x0+26*scale}" y="{z(2.2)}" text-anchor="middle" font-size="11" fill="#5c666b">DOMÉSTICA + NÚCLEO (cocina bajo P2)</text>')
    parts.append(f'<line x1="{x0}" y1="{y0+30}" x2="{x0+36*scale}" y2="{y0+30}" stroke="#566269" stroke-width="1"/>')
    parts.append(f'<text x="{x0+18*scale}" y="{y0+52}" text-anchor="middle" font-size="13" font-weight="700">36,00 m</text>')
    parts.append("</g>")
    parts.append(
        '<rect x="75" y="625" width="970" height="62" fill="#fff3dc" stroke="#bc5c3c" stroke-width="1.5"/>'
        '<text x="95" y="650" font-family="Arial" font-size="17" font-weight="700" fill="#8e3825">HIPÓTESIS DE ESQUEMA E0 — NO APTO PARA CONSTRUIR</text>'
        '<text x="95" y="674" font-family="Arial" font-size="11" fill="#4d5559">Las cotas de altura y pendiente de cubierta se ajustan con la estructura y el drenaje finales.</text>'
        "</svg>"
    )
    (OUT / f"DH-EST-E0-001_SECCION-{name}.svg").write_text("".join(parts), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
