"""Orquestador del modelo E0: matriz sistemas x modulaciones y salidas."""

from __future__ import annotations

import csv
import hashlib
import html
import json
import sys
from pathlib import Path

import numpy as np

from .checks import build_model_audit
from .materials import materials_from_json
from .portal import build_frame_model
from .quantities import compute_quantities
from .profiles import profile

ROOT = Path(__file__).resolve().parents[2]
DATA = Path(__file__).with_name("structure_system.json")
OUT = ROOT / "planos" / "estructura_e0"
DOC_OUT = ROOT / "docs" / "03_ingenierias" / "modelo_estructural_e0.md"

META = {
    "generator": "dreamhouse/structure/e0.py",
    "model": "E0 — esquema estructural (no diseño profesional)",
    "label": "NO APTO PARA SELECCIONAR / PRESUPUESTAR / CONSTRUIR",
    "date": "2026-08-12",
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
        "model_audit": build_model_audit(cfg),
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
    report_md = markdown_report(cfg, rows, summary)
    (OUT / "DH-EST-E0-001_resumen.md").write_text(report_md, encoding="utf-8")
    DOC_OUT.write_text(report_md, encoding="utf-8")
    write_csv(rows)
    for system in cfg["systems"]:
        write_svg(system["id"])

    for m in cfg["geometry"]["modulations"]:
        write_svg_section(f"{m['id']}_SECCION")

    try:
        from dreamhouse.generate_structure_plan import main as _regenerate_structural_sheets
        _regenerate_structural_sheets()
    except Exception as exc:  # pragma: no cover
        print(f"aviso: no se regeneraron las láminas estructurales ({exc})", file=sys.stderr)

    digest = hashlib.sha256(DATA.read_bytes()).hexdigest()
    manifest = {
        "input": str(DATA.relative_to(ROOT)),
        "input_sha256": digest,
        "generator": META["generator"],
        "revision": cfg["project"]["revision"],
        "canonical_report": str(DOC_OUT.relative_to(ROOT)),
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
                "p2_greatwall_t": round(q["p2_floor_greatwall_kg"] / 1000.0, 1),
                "total_greatwall_t": q["total_greatwall_t"],
                "kg_m2_greatwall": q["kg_m2_greatwall"],
                "p2_interior_columns": q["staggered"]["interior_columns"],
                "wall_axial_kn_m": q["great_wall"]["wall_axial_kn_m"],
                "wall_beam": q["great_wall"]["beam_profile"],
                "secondary_t": round(q["secondary_kg"] / 1000.0, 1),
                "column": q["frames"].get("column", "-"),
                "rafter": q["frames"].get("rafter", q["frames"].get("truss_chord", "-")),
                "tie_area_cm2": q["frames"].get("tie_area_cm2", 0.0),
                "tie_force_kn": q["frames"].get("tie_force_kn", 0.0),
                "drift_m": q["frames"].get("drift_m", None),
                "analysis_status": q["frames"].get("analysis_status"),
                "screening_passed": q["frames"].get("screening_passed", False),
                "ranking_eligible": q["ranking_eligible"],
            }
    return out


def _markdown_report_v01(cfg: dict, rows: list[dict], summary: dict) -> str:
    """Generador histórico de la revisión 0.1; se conserva solo para trazabilidad."""
    lines = [
        "# Modelo E0 — comparación estructural (D-019)",
        "",
        "**Estatus:** hipótesis de esquema · **NO APTO PARA CONSTRUIR**",
        f'**Fecha:** {META["date"]} · **Revisión:** {cfg["project"]["revision"]}',
        "",
        "> " + cfg["loads"]["note_no_snow"],
        "",
        "| Sistema × Modulación | Columnas | Viga/cercha | Pórticos | Acero total (metaldeck) | Total (gran muro) | kg/m² |",
        "|---|---|---|---|---:|---:|---:|",
    ]
    for row in rows:
        mod = row["modulation"]
        for sid, q in row["quantities"]["systems"].items():
            f = q["frames"]
            col = f.get("column", "-")
            roof = f.get("rafter", f.get("truss_chord", "-"))
            lines.append(f"| {mod} · {sid} | {col} | {roof} | {row['quantities']['modulation']['n_portal_lines']} | **{q['total_t']} t** | {q['total_greatwall_t']} t | {q['kg_m2_greatwall']} |")
    lines += [
        "",
        "## Desglose por componente (t)",
        "",
        "| Sistema × Modulación | Marcos principales | Entrepiso P2 (metaldeck) | Entrepiso P2 (staggered) | Entrepiso P2 (gran muro) | Secundaria | Total metaldeck | Total gran muro |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        mod = row["modulation"]
        for sid, q in row["quantities"]["systems"].items():
            lines.append(
                f"| {mod} · {sid} | {q['main_frames_kg']/1000:.1f} | {q['p2_floor_metaldeck_kg']/1000:.1f} | {q['p2_floor_staggered_kg']/1000:.1f} | {q['p2_floor_greatwall_kg']/1000:.1f} | {q['secondary_kg']/1000:.1f} | {q['total_t']} | {q['total_greatwall_t']} |"
            )
    lines += [
        "",
        "## Entrepiso P2 — opciones comparadas",
        "",
        "Tres esquemas sin columnas interiores en la zona doméstica (el metaldeck con apoyos "
        "intermedios NO es viable sin columnas en cocina/núcleo):",
    ]
    great_first = list(rows[0]["quantities"]["systems"].values())[0]["great_wall"]
    lines.append(
        f"- **GRAN-MURO (preferido):** el gran muro de X=31,5 (núcleo) es portante y recibe el P2; "
        f"{great_first['n_beams']} vigas longitudinales {great_first['beam_profile']} de {great_first['beam_span_m']} m "
        f"en el plenum (Y≈3/9/15) apoyan en la cercha de borde X=21 (luz 18 m, cordón {great_first['edge_chord']}) y en el muro; "
        f"franja del núcleo con losa sobre el muro (luz {great_first['nucleus_span_m']} m). Acero ≈ "
        f"{great_first['total_kg']/1000:.1f} t, axial del muro ≈ {great_first['wall_axial_kn_m']} kN/m, "
        f"fn del panel ≈ {great_first['panel_frequency_hz']} Hz. El muro aporta núcleo de corte longitudinal."
    )
    lines += [
        "- **STAGGERED:** cerchas de canto completo de 18 m ocultas en particiones; requiere re-articular "
        "las particiones del P2 (hoy no existe línea continua de 18 m).",
        "- **METALDECK:** línea base; introduce columnas en cocina/núcleo.",
    ]
    staggered_first = list(rows[0]["quantities"]["systems"].values())[0]["staggered"]
    lines.append(f"- Staggered truss: {staggered_first['n_trusses']} cerchas de 18 m de canto completo "
                 f"(≈ {staggered_first['truss_depth_m']} m, d/L ≈ {staggered_first['truss_d_over_l']}), "
                 f"paneles de losa de {staggered_first['panel_span_m']} m entre cerchas, cordones "
                 f"{staggered_first['chord']}, flecha de cercha ≈ {staggered_first['truss_deflection_m']} m, "
                 f"frecuencia del panel ≈ {staggered_first['panel_frequency_hz']} Hz (criterio DG11 ≥ 5 Hz).")
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
        "columnas HEA500 en las tres modulaciones (marcos ≈ 25–41 t). El control de la "
        "auditoría (HEA300) no cumple la deriva de servicio con el viento de hipótesis "
        "E0; es una decisión del ingeniero en E1 si relaja el límite o introduce arriostramiento/rigidización.",
        "2. **El sistema de cerchas con columnas articuladas y arriostramiento pesa ≈ 37–41 t** "
        "(ahorro ≈ 25–40 % sobre pórticos) y resuelve la deriva con columnas HEA200; el costo extra "
        "de fabricación de la cercha debe cotizarse antes de decidir (E1, puerta PE-1).",
        "3. **Pórtico atado (PORTICO-T):** el tirante entre los apoyos de la cercha queda casi "
        "inactivo (≈ 1,4 kN) porque el faldón 1:30 es casi plano y la deriva de viento es un sway "
        "en la misma dirección de ambos muros; el tirante solo resistiría la apertura de aleros por "
        "empuje gravitatorio, que aquí no gobierna. Añade peso (≈ 1–2 t/pórtico) sin beneficio de "
        "deriva: **no es competitivo en este caso de carga.**",
        "4. **Pórtico con bases fijas (PORTICO-F):** es el control efectivo de deriva para el "
        "sistema de pórticos. Permite columna HEA300 con deriva ≈ 0,016–0,021 m (vs. HEA500 "
        "articulado) y un marco ≈ 25–35 % más liviano; el costo pasa a la cimentación (momento en la base).",
        "5. **Entrepiso P2:** tres esquemas sin columnas interiores — METALDECK (12,4–17,1 t según "
        "modulación, con columnas en cocina/núcleo y vigas de 6 m entre apoyos), STAGGERED (≈ 3,8 t, "
        "exige re-articular particiones) y **GRAN-MURO (≈ 5,9 t, preferido): el gran muro de X=31,5 "
        "trabaja como apoyo del P2**, con 3 vigas longitudinales en el plenum + cercha de borde X=21; "
        "sin re-articular particiones y con el muro actuando como núcleo de corte longitudinal. El peso "
        "de la losa de deck profundo se verifica en E1.",
        "6. **Cubierta de un solo faldón ≈ 1:30:** verificada por el modelo: la viga de cubierta del "
        "pórtico queda gobernada por flecha y resistencia con IPE450/500/550 según modulación "
        "(M45/M60/M90); la cercha IPE220 con flecha despreciable (d/L = 1/16).",
        "7. **Auditoría de física del modelo (11-08-2026):** corregidos signos de gravedad en cargas "
        "puntuales y uniformes (antes el pórtico 'flotaba' bajo carga muerta), proyección trigonométrica "
        "de cargas sobre miembros inclinados (la carga equivalente ahora es exactamente vertical) y "
        "límites de flecha L/180–L/240 comparados en metros (antes se comparaban con un límite 1000× "
        "más permisivo, dejando la flecha sin efecto).",
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


def markdown_report(cfg: dict, rows: list[dict], summary: dict) -> str:
    """Reporte auditado que falla cerrado frente a los límites del E0."""

    audit = build_model_audit(cfg)
    lines = [
        "# Modelo E0 — cribado estructural auditado (D-019)",
        "",
        "**Estatus:** hipótesis de esquema · **NO APTO PARA SELECCIONAR SISTEMA, "
        "PRESUPUESTAR PE-1, DIMENSIONAR PERFILES NI CONSTRUIR**",
        f'**Fecha:** {META["date"]} · **Revisión:** {cfg["project"]["revision"]}',
        "",
        "> " + cfg["loads"]["note_no_snow"],
        "",
        "> **Dictamen:** ninguna fila es elegible para cerrar D-019 o fijar tonelaje. "
        "Son subtotales inferiores que omiten estados límite y componentes críticos.",
        "",
        "| Sistema × modulación | Columnas* | Cubierta* | Líneas | Subtotal metaldeck* | Subtotal gran muro* | Estado |",
        "|---|---|---|---:|---:|---:|---|",
    ]
    for row in rows:
        mod = row["modulation"]
        for sid, q in row["quantities"]["systems"].items():
            frame = q["frames"]
            roof = frame.get("rafter", frame.get("truss_chord", "-"))
            if sid == "CERCHA":
                status = "INCOMPLETO: sin análisis lateral/estabilidad"
            elif frame.get("screening_passed"):
                status = "pasa cribado 2D limitado; no demuestra diseño"
            else:
                status = "FALLA cribado o agota catálogo E0"
            lines.append(
                f"| {mod} · {sid} | {frame.get('column', '-')} | {roof} | "
                f"{row['quantities']['modulation']['n_portal_lines']} | {q['total_t']} t | "
                f"{q['total_greatwall_t']} t | {status} |"
            )

    lines += [
        "",
        "\* Perfil y masa de cribado; no son selección ni cantidad de diseño. D-043 "
        "adopta el camino gravitacional GRAN-MURO, no los perfiles ni el tonelaje del E0.",
        "",
        "## Desglose de subtotales inferiores (t)",
        "",
        "| Sistema × modulación | Marcos | P2 metaldeck | P2 staggered* | P2 gran muro* | Secundaria/reserva* | Total metaldeck | Total gran muro* |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        mod = row["modulation"]
        for sid, q in row["quantities"]["systems"].items():
            lines.append(
                f"| {mod} · {sid} | {q['main_frames_kg']/1000:.1f} | "
                f"{q['p2_floor_metaldeck_kg']/1000:.1f} | "
                f"{q['p2_floor_staggered_kg']/1000:.1f} | "
                f"{q['p2_floor_greatwall_kg']/1000:.1f} | "
                f"{q['secondary_kg']/1000:.1f} | {q['total_t']} | "
                f"{q['total_greatwall_t']} |"
            )

    first = list(rows[0]["quantities"]["systems"].values())[0]
    staggered = first["staggered"]
    great_wall = first["great_wall"]
    lines += [
        "",
        "## Entrepiso P2 — estado de alternativas",
        "",
        "- **METALDECK con apoyos:** subtotal gravitacional; introduce apoyos en la banda "
        "doméstica y no incluye diseño compuesto, conectores, vibración ni fuego.",
        f"- **STAGGERED — NO ADOPTADO:** {staggered['n_trusses']} cerchas de 18 m, "
        f"canto {staggered['truss_depth_m']} m. La frecuencia del panel queda sin calcular "
        "hasta definir deck y sección compuesta.",
        f"- **GRAN-MURO — CONCEPTO GRAVITACIONAL ACTIVO D-043:** superficie de "
        f"madera/absorción delante de bastidor oculto {great_wall['hidden_column_trial_profile']} "
        f"+ viga de transferencia {great_wall['transfer_girder_trial_profile']}; "
        f"{great_wall['n_beams']} vigas {great_wall['beam_profile']} a "
        f"{18.0/great_wall['n_beams']:.1f} m en el tramo de 10,5 m y "
        f"{great_wall['rear_beam_profile']} en el tramo posterior de 4,5 m dejan un canto conceptual de "
        f"{great_wall['trial_floor_zone_m']:.2f} m. El subtotal "
        f"({great_wall['total_kg']/1000:.1f} t) es una prueba de cabida y no verifica pandeo, "
        f"uniones, fuego, diafragma, cimentación ni acción lateral.",
        "",
        "## Defectos corregidos en revisión 0.2",
        "",
        "1. Se calcula el momento interior para carga uniforme de ambos signos; la revisión "
        "0.1 devolvía cero en una viga simple bajo succión.",
        "2. La succión `WU` se separa de `WX+`/`WX-`; el sismo conceptual usa `EX+`/`EX-`.",
        "3. Los miembros de piso usan demanda factorizada para resistencia y servicio sin "
        "factor para flecha; se eliminó la reducción `/1,5` no sustentada.",
        "4. El catálogo ya no acepta silenciosamente su perfil mayor y el pórtico no ignora "
        "deriva/interacción al llegar a HEA500/HEB400.",
        "5. El rafter incorpora interacción axial-flexión en el cribado de fluencia bruta.",
        "6. Se retiró la frecuencia ficticia del deck modelado como losa maciza de 220 mm. "
        "D-043 adopta el camino gravitacional del gran muro, pero no valida perfiles ni cantidades.",
        "",
        "## Bloqueadores",
        "",
    ]
    for blocker in audit["blockers"]:
        lines.append(
            f"- **{blocker['id']} · {blocker['severity'].upper()}:** "
            f"{blocker['description']}"
        )
    lines += [
        "",
        "## Uso permitido",
        "",
        "El E0 sirve para coordinación geométrica, detección de conflictos y definición del "
        "alcance del E1. Los objetivos históricos de 30–45 t y 31–48 kg/m² no validan un "
        "resultado por coincidencia. D-019 y PE-1 siguen abiertos hasta contar con modelo "
        "normativo, camino lateral completo, entrepiso de fabricante, geotecnia y cantidades "
        "revisadas por ingeniero competente.",
    ]
    return "\n".join(lines) + "\n"


def write_csv(rows: list[dict]) -> None:
    path = OUT / "DH-EST-E0-001_resumen.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["modulacion", "sistema", "columnas_cribado", "viga_cercha_cribado", "tirante_cm2", "marcos_t_subtotal", "entrepiso_p2_metaldeck_t_subtotal", "entrepiso_p2_staggered_t_subtotal_no_adoptado", "entrepiso_p2_granmuro_t_subtotal_concepto_D043", "secundaria_t_reserva", "total_metaldeck_t_subtotal", "total_granmuro_t_subtotal_concepto_D043", "kg_m2_granmuro_concepto_D043", "drift_m_cribado", "estado_analisis", "elegible_ranking"])
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
                    round(q["p2_floor_greatwall_kg"] / 1000.0, 2),
                    round(q["secondary_kg"] / 1000.0, 2), q["total_t"], q["total_greatwall_t"],
                    q["kg_m2_greatwall"], f.get("drift_m", ""),
                    f.get("analysis_status", "incomplete"), q["ranking_eligible"],
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

    is_truss = not system_id.startswith("PORTICO")
    if not is_truss:
        cfg_sys = next(s for s in cfg["systems"] if s["id"] == system_id)
        col = profile("HEA300")
        rafter = profile("IPE500")
        nodes = _frame_node_coords(eave_low, eave_high, has_p2, p2_level)
        label = "PÓRTICO TRANSVERSAL"
        sub = "Cribado E0 · columna HEA + viga IPE uniforme (cartela NO modelada) · bases articuladas"
        if cfg_sys.get("tie"):
            sub = "Cribado E0 · pórtico atado con tirante entre cabezas de columna · bases articuladas"
        if cfg_sys.get("fixed_base"):
            sub = "Cribado E0 · viga IPE uniforme (cartela NO modelada) · base fija ideal sin cimentación"
        parts = _svg_header(f"{label} — {system_id}", sub)
    else:
        col = profile("HEA200")
        rafter = profile("IPE220")
        nodes = _frame_node_coords(eave_low, eave_high, has_p2, p2_level)
        truss_depth = 18.0 / 16.0
        nodes.update({
            "bottom_low": (nodes["top_low"][0], nodes["top_low"][1] + truss_depth * 30.0),
            "bottom_mid": (nodes["roof_mid"][0], nodes["roof_mid"][1] + truss_depth * 30.0),
            "bottom_high": (nodes["top_high"][0], nodes["top_high"][1] + truss_depth * 30.0),
        })
        parts = _svg_header(f"CERCHA TRANSVERSAL — {system_id}", "Alternativa E0 monopendiente incompleta · sin análisis lateral, estabilidad de barras ni conexiones")
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

    left_column_top = "bottom_low" if is_truss else "top_low"
    right_column_top = "bottom_high" if is_truss else "top_high"
    line("base_low", left_column_top)
    line("base_high", right_column_top)
    if has_p2:
        line("base_low", "p2_low")
        line("p2_low", left_column_top)
        line("base_high", "p2_high")
        line("p2_high", right_column_top)
    if system_id.endswith("-T"):
        line("top_low", "top_high", color="#27859a", width=3.0)
    line("top_low", "roof_mid")
    line("roof_mid", "top_high")
    if is_truss:
        line("bottom_low", "bottom_mid", width=5.0)
        line("bottom_mid", "bottom_high", width=5.0)
        line("bottom_low", "top_low", width=3.0)
        line("bottom_high", "top_high", width=3.0)
        # Warren conceptual, siguiendo el faldón único. Las barras son solo
        # representación geométrica; el E0 no analiza fuerzas de la cercha.
        top_left_x, top_left_y = nodes["top_low"]
        bot_left_x, bot_left_y = nodes["bottom_low"]
        for i in range(8):
            x1 = top_left_x + i * 540.0 / 8.0
            x2 = top_left_x + (i + 1) * 540.0 / 8.0
            top_y1 = top_left_y + i * (nodes["top_high"][1] - top_left_y) / 8.0
            top_y2 = top_left_y + (i + 1) * (nodes["top_high"][1] - top_left_y) / 8.0
            bot_y1 = bot_left_y + i * (nodes["bottom_high"][1] - bot_left_y) / 8.0
            bot_y2 = bot_left_y + (i + 1) * (nodes["bottom_high"][1] - bot_left_y) / 8.0
            if i % 2 == 0:
                parts.append(f'<line x1="{x1}" y1="{bot_y1}" x2="{x2}" y2="{top_y2}" stroke="#566269" stroke-width="2"/>')
            else:
                parts.append(f'<line x1="{x1}" y1="{top_y1}" x2="{x2}" y2="{bot_y2}" stroke="#566269" stroke-width="2"/>')

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
