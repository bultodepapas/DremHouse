from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = Path(__file__).with_name("project.json")
OUT = ROOT / "planos" / "conceptual_v0.3"
SCALE = 24.0
MARGIN = 75
PLAN_W = 36 * SCALE
PLAN_H = 18 * SCALE

COLORS = {
    "technical": "#ccd8de", "circulation": "#f4e8bb", "buffer": "#f5f1e8",
    "social": "#dcc9b7", "work": "#c7d9d1", "domestic": "#dfcab3",
    "service": "#bfc9c2", "vertical": "#c9bcae", "suite": "#d8c9bd",
    "master": "#c3aa98", "wellness": "#b9d2cd", "shared": "#d5d0b8"
}


def area(z):
    return round(z["w"] * z["d"], 6)


def validate(p):
    checks = []
    W, D, p2x = p["envelope"]["depth_x_m"], p["envelope"]["width_y_m"], p["envelope"]["p2_start_x_m"]
    pb = p["ground_floor"]["zones"] + p["ground_floor"]["core"]
    p2 = p["upper_floor"]["zones"]
    def inside(z, xmin=0):
        return z["x"] >= xmin and z["y"] >= 0 and z["x"] + z["w"] <= W and z["y"] + z["d"] <= D
    checks.append(("HR-ENV", all(inside(z) for z in pb), "Todas las zonas PB dentro de 18 × 36 m"))
    checks.append(("HR-P2", all(inside(z, p2x) for z in p2), "Todas las zonas P2 dentro de 18 × 15 m"))
    def overlap(a, b):
        return min(a["x"] + a["w"], b["x"] + b["w"]) - max(a["x"], b["x"]) > 1e-7 and min(a["y"] + a["d"], b["y"] + b["d"]) - max(a["y"], b["y"]) > 1e-7
    checks.append(("HR-P2-TOPO", not any(overlap(a, b) for i, a in enumerate(p2) for b in p2[i+1:]), "Zonificación P2 sin solapes"))
    checks.append(("HR-DOORS", len(p["ground_floor"]["front_openings"]) == 3, "Exactamente tres accesos frontales"))
    suites = [z for z in p2 if z["kind"] in ("suite", "master") and not z["id"].endswith("-B")]
    checks.append(("HR-SUITES", len(suites) == 4, "Exactamente cuatro suites"))
    vals = {z["id"]: z.get("target_area", area(z)) for z in p2}
    checks.append(("HR-CHILD-EQ", abs(vals["P2-H1"] - vals["P2-H2"]) <= .001, "Suites de hijos con igual área objetivo"))
    checks.append(("DCV-CORE", abs(sum(area(z) for z in p["ground_floor"]["core"]) - 81) <= .001, "Núcleo PB = 81,00 m²"))
    checks.append(("DCV-P2-AREA", abs(sum(area(z) for z in p2) - 270) <= .001, "Zonificación P2 suma 270,00 m²"))
    return [{"rule_id": rid, "status": "PASS" if ok else "FAIL", "message": msg} for rid, ok, msg in checks]


def rect(zone, x0, y0):
    x = x0 + zone["x"] * SCALE
    y = y0 + (18 - zone["y"] - zone["d"]) * SCALE
    w, h = zone["w"] * SCALE, zone["d"] * SCALE
    axis = zone["id"] == "PB-EJE"
    fill = "none" if axis else COLORS.get(zone["kind"], "#ddd")
    phase = zone.get("phase")
    dash = ' stroke-dasharray="8 5"' if phase == 2 or axis else ""
    label = html.escape(zone["name"])
    meta = f'{zone["id"]} · {area(zone):.1f} m²' + (f" · F{phase}" if phase else "")
    fs = 14 if min(w, h) > 90 else 11
    if axis:
        lx = x0 + 10.6 * SCALE
        ly = y + h / 2
        return (f'<g><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="#b8841e" '
                f'stroke-width="2.2" stroke-dasharray="8 5"/><rect x="{lx}" y="{ly-12}" width="190" height="20" fill="#fbfaf7"/>'
                f'<text x="{lx+8}" y="{ly+3}" font-size="11" font-weight="700" fill="#8a6518">EJE PEATONAL LIBRE · 4,00 m</text></g>')
    stroke = "#b8841e" if axis else "#29343a"
    return (f'<g><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{2.2 if axis else 1.4}"{dash}/><text x="{x+w/2}" y="{y+h/2-4}" '
            f'text-anchor="middle" font-size="{fs}" font-weight="600">{label}</text>'
            f'<text x="{x+w/2}" y="{y+h/2+14}" text-anchor="middle" font-size="10">{meta}</text></g>')


def dimension(x1, y1, x2, y2, label):
    return (f'<g stroke="#566269" fill="none" stroke-width="1"><line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"/>'
            f'<line x1="{x1-5}" y1="{y1-5}" x2="{x1+5}" y2="{y1+5}"/><line x1="{x2-5}" y1="{y2-5}" x2="{x2+5}" y2="{y2+5}"/>'
            f'<text x="{(x1+x2)/2}" y="{(y1+y2)/2-7}" fill="#29343a" stroke="none" text-anchor="middle" font-size="12">{label}</text></g>')


def svg_plan(p, floor):
    x0, y0 = MARGIN, 145
    zones = (p["ground_floor"]["zones"] + p["ground_floor"]["core"]) if floor == "PB" else p["upper_floor"]["zones"]
    title = "PLANTA BAJA · BORRADOR DE ZONIFICACIÓN" if floor == "PB" else "PLANTA SEGUNDO PISO · BORRADOR DE ZONIFICACIÓN"
    subtitle = "18,00 × 36,00 m · área nominal 648 m²" if floor == "PB" else "P2 posterior 18,00 × 15,00 m · área nominal 270 m²"
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="720" viewBox="0 0 1120 720">',
             '<rect width="1120" height="720" fill="#fbfaf7"/>',
             f'<text x="75" y="48" font-family="Arial" font-size="25" font-weight="700" fill="#20292e">{title}</text>',
             f'<text x="75" y="76" font-family="Arial" font-size="14" fill="#566269">{subtitle} · Rev. 0.3-borrador-01 · 2026-08-11</text>',
             '<g font-family="Arial" fill="#20292e">']
    if floor == "P2":
        parts.append(f'<rect x="{x0}" y="{y0}" width="{21*SCALE}" height="{PLAN_H}" fill="#eeeae2" stroke="#888" stroke-dasharray="5 5"/>')
        parts.append(f'<text x="{x0+10.5*SCALE}" y="{y0+PLAN_H/2}" text-anchor="middle" font-size="18" fill="#9a958d">VACÍO DOBLE ALTURA · 378 m²</text>')
    zones = [z for z in zones if z["id"] != "PB-EJE"] + [z for z in zones if z["id"] == "PB-EJE"]
    for z in zones:
        parts.append(rect(z, x0, y0))
    parts.append(f'<rect x="{x0}" y="{y0}" width="{PLAN_W}" height="{PLAN_H}" fill="none" stroke="#172126" stroke-width="3"/>')
    for gx in (0, 6, 12, 18, 24, 30, 36):
        xx = x0 + gx*SCALE
        parts.append(f'<line x1="{xx}" y1="{y0-18}" x2="{xx}" y2="{y0+PLAN_H+18}" stroke="#8d9699" stroke-width=".7" stroke-dasharray="3 5"/>')
        parts.append(f'<circle cx="{xx}" cy="{y0-27}" r="11" fill="#fbfaf7" stroke="#566269"/><text x="{xx}" y="{y0-23}" text-anchor="middle" font-size="10">{chr(65+gx//6)}</text>')
    if floor == "PB":
        for op in p["ground_floor"]["front_openings"]:
            yy1 = y0 + (18-op["y0"]-op["width"])*SCALE
            parts.append(f'<line x1="{x0}" y1="{yy1}" x2="{x0}" y2="{yy1+op["width"]*SCALE}" stroke="#bc5c3c" stroke-width="7"/>')
            parts.append(f'<text x="{x0+7}" y="{yy1+op["width"]*SCALE/2}" font-size="9" fill="#8e3825" transform="rotate(-90 {x0+7} {yy1+op["width"]*SCALE/2})">{html.escape(op["name"])} {op["width"]:.2f} m</text>')
        parts.append(f'<text x="{x0-40}" y="{y0+PLAN_H/2}" transform="rotate(-90 {x0-40} {y0+PLAN_H/2})" text-anchor="middle" font-size="12" font-weight="700">FACHADA / PLATAFORMA</text>')
    parts.append(dimension(x0, y0+PLAN_H+38, x0+PLAN_W, y0+PLAN_H+38, "36,00 m"))
    parts.append(dimension(x0-35, y0+PLAN_H, x0-35, y0, "18,00 m"))
    parts += ['</g>',
              '<rect x="75" y="625" width="970" height="62" fill="#fff3dc" stroke="#bc5c3c" stroke-width="1.5"/>',
              '<text x="95" y="650" font-family="Arial" font-size="18" font-weight="700" fill="#8e3825">NO APTO PARA CONSTRUIR</text>',
              '<text x="95" y="674" font-family="Arial" font-size="12" fill="#4d5559">Hipótesis conceptual para validar programa, estructura, egreso, espesores, equipos, MEP, predio y normativa. Las cotas contractuales están pendientes.</text>',
              '<text x="1000" y="650" font-family="Arial" font-size="11" text-anchor="end">Escala gráfica aprox. 1:42 en lienzo</text>',
              '</svg>']
    return "".join(parts)


def main():
    p = json.loads(DATA.read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    checks = validate(p)
    (OUT / "DH-ARQ-PLN-001-R00_PB.svg").write_text(svg_plan(p, "PB"), encoding="utf-8")
    (OUT / "DH-ARQ-PLN-002-R00_P2.svg").write_text(svg_plan(p, "P2"), encoding="utf-8")
    report = {"project_revision": p["project"]["revision"], "status": p["project"]["status"], "checks": checks,
              "summary": {"passed": sum(c["status"] == "PASS" for c in checks), "failed": sum(c["status"] == "FAIL" for c in checks)}}
    (OUT / "compliance.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = ["# Reporte de cumplimiento", "", f'**Revisión:** {p["project"]["revision"]}  ', "**Estatus:** hipótesis / no apto para construir", "", "| Regla | Resultado | Comprobación |", "|---|---|---|"]
    lines += [f'| {c["rule_id"]} | {c["status"]} | {c["message"]} |' for c in checks]
    (OUT / "reporte_cumplimiento.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    digest = hashlib.sha256(DATA.read_bytes()).hexdigest()
    manifest = {"input": str(DATA.relative_to(ROOT)), "input_sha256": digest, "generator": "dreamhouse/generate_plans.py", "revision": p["project"]["revision"], "outputs": ["DH-ARQ-PLN-001-R00_PB.svg", "DH-ARQ-PLN-002-R00_P2.svg", "compliance.json", "reporte_cumplimiento.md"]}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    if report["summary"]["failed"]:
        raise SystemExit(json.dumps(report, ensure_ascii=False))
    print(json.dumps(report["summary"]))


if __name__ == "__main__":
    main()
