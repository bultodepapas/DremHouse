"""Generador de láminas ESTRUCTURALES conectadas a los cálculos E0.

Las láminas se dibujan **calculando en vivo** desde `structure_system.json` a
través del modelo (`compute_quantities`, `size_staggered_floor`): perfiles,
canto, tonelajes, paneles, frecuencia y posiciones de cerchas salen del estado
actual de los cálculos. Si los cálculos cambian, basta re-ejecutar
`python -m dreamhouse.structure.e0` (que regenera todo) o
`python dreamhouse/generate_structure_plan.py`.

Láminas:
- DH-EST-E0-002_ESTRUCTURA-INSPECCION.svg : planta estructural + corte B-B.
- DH-EST-E0-003_ESTRUCTURA-LATERAL-A.svg  : vista lateral A (elevación estructural).

NO APTO PARA CONSTRUIR. Solo inspección visual de coordinación.
"""

from __future__ import annotations

import hashlib
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dreamhouse.structure.materials import materials_from_json
from dreamhouse.structure.quantities import compute_quantities
from dreamhouse.structure.staggered import size_staggered_floor

SYSTEM = Path(__file__).with_name("structure") / "structure_system.json"
PB = Path(__file__).with_name("pb_b05.json")
OUT = ROOT / "planos" / "estructura"

SHEET2 = "EST-002-R00"
SHEET3 = "EST-003-R00"


def esc(value: str) -> str:
    return html.escape(value)


def rect(x, y, w, h, **attrs):
    a = " ".join(f'{k.replace("_", "-")}="{v}"' for k, v in attrs.items())
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" {a}/>'


def text(x, y, value, size=10, anchor="middle", weight=400, fill="#243238", rotate=None):
    transform = f' transform="rotate({rotate} {x} {y})"' if rotate is not None else ""
    return (f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" '
            f'font-weight="{weight}" fill="{fill}"{transform}>{esc(value)}</text>')


def line(x1, y1, x2, y2, color="#172126", width=1.0, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"{d}/>'


def poly(points, color="#172126", width=1.0, dash=None, fill="none"):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    pts = " ".join(f"{px},{py}" for px, py in points)
    return f'<polyline points="{pts}" fill="{fill}" stroke="{color}" stroke-width="{width}"{d}/>'


def title_block(title_value, subtitle, sheet):
    return (
        '<rect width="1400" height="900" fill="#fbfaf7"/>'
        '<g font-family="Arial">'
        + text(70, 45, title_value, 26, "start", 700)
        + text(70, 72, subtitle, 12, "start", 400, "#59676c")
        + text(1325, 105, sheet, 16, "end", 700, "#7e3f2c")
        + '</g>'
    )


def frame_positions(cfg) -> list[float]:
    """Posiciones de los pórticos de la modulación M60 (X=0..36 cada 6 m)."""
    m60 = next(m for m in cfg["geometry"]["modulations"] if m["bay_m"] == 6.0)
    return [i * m60["bay_m"] for i in range(m60["n_bays"] + 1)]


def staggered_positions(cfg, st) -> list[float]:
    """Posiciones X de las cerchas staggered derivadas del cálculo (paneles)."""
    geom = cfg["geometry"]
    panel = geom["p2_length_m"] / st["n_trusses"]
    return [geom["p2_start_x_m"] + k * panel for k in range(1, st["n_trusses"] + 1)]


def beam_y_positions(gw) -> list[float]:
    """Posiciones Y de las vigas longitudinales del esquema GRAN-MURO."""
    spacing = 18.0 / gw["n_beams"]
    return [(k + 0.5) * spacing for k in range(gw["n_beams"])]


def live_results(cfg):
    """Cálculo en vivo: misma vía que e0.py, sin depender de resultados exportados."""
    steel = materials_from_json(cfg)["S355"]
    phi_b = cfg["criteria"]["phi_bending"]
    phi_c = cfg["criteria"]["phi_axial"]
    q = compute_quantities(cfg, steel, 6.0, 6, phi_b, phi_c)["systems"]["CERCHA"]
    st = size_staggered_floor(cfg, steel, 6.0, phi_b, phi_c)
    return q, st


# ---------------------------------------------------------------- PLANTA + CORTE

def draw_plan(parts, cfg, pb, gw):
    S = 22.0
    X0, Y0 = 150.0, 170.0
    L, W = 36.0, 18.0
    def sx(x): return X0 + x * S
    def sy(y): return Y0 + (W - y) * S
    def pr(x, y, w, d, **attrs):
        return rect(sx(x), sy(y + d), w * S, d * S, **attrs)

    frames = frame_positions(cfg)
    beam_ys = beam_y_positions(gw)

    parts.append(pr(0, 0, L, W, fill="none", stroke="#172126", stroke_width=3))
    parts.append(pr(21, 0, 15, 18, fill="none", stroke="#7a8689", stroke_width=1, stroke_dasharray="8 5"))
    parts.append(text(sx(28.5), sy(0.6), "P2 · 18 × 15 m · nivel +3,80", 9, weight=700, fill="#5c676b"))

    for y in (3, 6, 9, 12, 15):
        parts.append(line(sx(0), sy(y), sx(36), sy(y), color="#c3c8cb", width=0.6, dash="2 4"))
    parts.append(text(sx(2), sy(17.6), "correas c/1,5 m (secundaria)", 6, fill="#9aa3a6", anchor="start"))

    for zone in ((0, 12), (24, 36)):
        xa, xb = zone
        parts.append(line(sx(xa), sy(0), sx(xb), sy(18), color="#7a8689", width=1.0, dash="7 4"))
        parts.append(line(sx(xa), sy(18), sx(xb), sy(0), color="#7a8689", width=1.0, dash="7 4"))
    parts.append(text(sx(6), sy(9), "ARRIOSTRAMIENTO LONGITUDINAL · WIND GIRDER", 7, weight=700, fill="#667377", rotate=-56))
    parts.append(text(sx(30), sy(9), "ARRIOSTRAMIENTO LONGITUDINAL · WIND GIRDER", 7, weight=700, fill="#667377", rotate=56))

    for op in pb["front_openings"]:
        parts.append(line(sx(0), sy(op["y0"]), sx(0), sy(op["y0"] + op["width"]), color="#c9a38f", width=5))
    parts.append(pr(1.6, 0.45, 6.4, 5.9, fill="none", stroke="#c9a38f", stroke_width=1.2, stroke_dasharray="6 4"))

    # RETÍCULA: cerchas de cubierta en cada línea de pórtico (M60).
    for x in frames:
        parts.append(line(sx(x), sy(0), sx(x), sy(18), color="#1f2d33", width=5))
    parts.append(text(sx(18), sy(0.6), f"CERCHA DE CUBIERTA 18 m · L/16 · {len(frames)} LÍNEAS (M60)", 9, weight=700, fill="#1f2d33"))

    for x in frames:
        for y in (0, 18):
            parts.append(f'<circle cx="{sx(x)}" cy="{sy(y)}" r="5" fill="#172126"/>')
    parts.append(text(sx(36) + 34, sy(18), "COLUMNA HEA200 EN MUROS", 7, weight=700, fill="#172126", anchor="start"))

    # GRAN MURO estructural (apoyo del P2 + núcleo de corte longitudinal).
    parts.append(line(sx(31.5), sy(0), sx(31.5), sy(18), color="#6b4a2e", width=8))
    parts.append(text(sx(31.5), sy(17.6), f"GRAN MURO ESTRUCTURAL X=31,5 · t≈{gw['wall_t_m']} m · portante + núcleo de corte", 7, weight=700, fill="#6b4a2e"))

    # Esquema GRAN-MURO del entrepiso P2: cercha de borde X=21 + vigas longitudinales.
    parts.append(line(sx(21), sy(0), sx(21), sy(18), color="#3f7d8a", width=3, dash="9 5"))
    parts.append(text(sx(21), sy(0.6), "CERCHA DE BORDE X=21 (luz 18 m)", 7, weight=700, fill="#3f7d8a", rotate=-90))
    for y in beam_ys:
        parts.append(line(sx(21), sy(y), sx(36), sy(y), color="#3f7d8a", width=3, dash="4 4"))
    parts.append(text(sx(21.2), sy(beam_ys[0] + 0.6), f"VIGAS LONG. {gw['beam_profile']} ×{gw['n_beams']} EN PLENUM · luz {gw['beam_span_m']} m", 7, weight=700, fill="#3f7d8a", anchor="start"))
    parts.append(text(sx(28.5), sy(0.6), f"P2: franja núcleo sobre el muro (luz {gw['nucleus_span_m']} m) · paneles deck profundo · fn≈{gw['panel_frequency_hz']} Hz", 7, weight=700, fill="#3f7d8a"))

    for i, x in enumerate(frames):
        px = sx(x)
        parts.append(line(px, Y0 - 18, px, Y0 + 18 * S + 18, color="#9ea5a5", width=0.6, dash="4 5"))
        parts.append(f'<circle cx="{px}" cy="{Y0 - 31}" r="10" fill="#fbfaf7" stroke="#5a666a"/>')
        parts.append(text(px, Y0 - 27, chr(65 + i), 8))
    dimx = Y0 + 18 * S + 42
    parts.append(line(sx(0), dimx, sx(36), dimx, color="#536166"))
    for x in (0, 10.5, 21, 31.5, 36):
        parts.append(line(sx(x), dimx - 6, sx(x), dimx + 6, color="#536166"))
    for a, b, label in ((0, 10.5, "10,50"), (10.5, 21, "10,50"), (21, 31.5, "10,50"), (31.5, 36, "4,50")):
        parts.append(text((sx(a) + sx(b)) / 2, dimx - 7, label, 8))
    parts.append(text((sx(0) + sx(36)) / 2, dimx + 25, "36,00 m", 10, weight=700))
    dimy = X0 - 40
    parts.append(line(dimy, sy(0), dimy, sy(18), color="#536166"))
    parts.append(line(dimy - 6, sy(0), dimy + 6, sy(0), color="#536166"))
    parts.append(line(dimy - 6, sy(18), dimy + 6, sy(18), color="#536166"))
    parts.append(text(dimy - 12, (sy(0) + sy(18)) / 2, "18,00 m", 8, rotate=-90))


def draw_section(parts, cfg, gw):
    left, base, sc = 1010.0, 470.0, 20.0
    w = 18.0 * sc
    low, high = cfg["geometry"]["eave_low_m"], cfg["geometry"]["eave_high_m"]
    def yy(h): return base - h * sc

    parts.append(text(left + w / 2, 185, "CORTE TRANSVERSAL ESTRUCTURAL B-B", 15, weight=700))
    parts.append(text(left + w / 2, 203, f"Mono-pitch {low}→{high} · cercha de cubierta L/16 + P2 sobre muro", 9, fill="#59676c"))

    parts.append(line(left, base, left + w, base, color="#172126", width=3))
    parts.append(line(left, yy(3.8), left + w, yy(3.8), color="#3f7d8a", width=2, dash="9 5"))
    parts.append(text(left + w + 6, yy(3.8), "+3,80", 9, weight=700, fill="#3f7d8a", anchor="start"))

    # Losa del P2 y vigas longitudinales (de canto, en sección) dentro del plenum 3,20→3,80.
    panel = 18.0 / gw["n_beams"]
    for k in range(gw["n_beams"]):
        px = left + w * (k + 0.5) / gw["n_beams"]
        parts.append(rect(px - 4, yy(3.2), 8, 0.6 * sc, fill="#3f7d8a", stroke="#274a53", stroke_width=1))
    parts.append(text(left + w / 2, yy(3.4) - 8, f"{gw['n_beams']} VIGAS LONG. {gw['beam_profile']} EN PLENUM (3,20→3,80) · paneles de losa {panel:.0f} m entre vigas", 8, weight=700, fill="#3f7d8a"))
    parts.append(text(left + w / 2, yy(3.8) - 24, "El GRAN MURO X=31,5 (perpendicular a este corte) recibe el P2 y aporta núcleo de corte longitudinal", 7, fill="#6b4a2e"))

    # Cercha de cubierta (L/16 ≈ 1,13 m) bajo el faldón.
    top_c = yy(low)
    truss_h = 1.125 * sc
    parts.append(line(left, top_c, left + w, yy(high), color="#172126", width=4))
    parts.append(line(left, top_c + truss_h, left + w, yy(high) + truss_h, color="#172126", width=2))
    steps = 6
    for i in range(steps):
        xa = left + w * i / steps
        xb = left + w * (i + 1) / steps
        parts.append(line(xa, top_c + truss_h, xb, top_c, color="#5d6b70", width=1.0))
        parts.append(line(xa, top_c, xb, top_c + truss_h, color="#5d6b70", width=1.0))
    parts.append(text(left + 4, top_c - 12, f"LADO BAJO ≈ {low} m", 9, "start", 700))
    parts.append(text(left + w - 4, yy(high) - 12, f"LADO ALTO ≈ {high} m", 9, "end", 700))

    for px in (left, left + w):
        parts.append(line(px, base, px, top_c + truss_h, color="#172126", width=7))
        parts.append(poly([(px - 10, base), (px + 10, base), (px, base + 12), (px - 10, base)], color="#536166", width=1.5))
    parts.append(text(left + w / 2, base + 24, "COLUMNA HEA200 · base articulada · solo en muros largos", 8, weight=700))
    parts.append(text(left + w / 2, base + 46, "18,00 m", 10, weight=700))


# ---------------------------------------------------------------- VISTA LATERAL A

def draw_lateral(parts, cfg, pb, q, gw):
    left, base, sc = 140.0, 640.0, 16.0
    L = cfg["geometry"]["nave_length_m"]
    frames = frame_positions(cfg)
    eave = cfg["geometry"]["eave_low_m"]  # lateral A = lado bajo
    eave_high = cfg["geometry"]["eave_high_m"]
    width = L * sc
    def xx(x): return left + x * sc
    def yy(h): return base - h * sc
    col = q["frames"]["column"]
    chord = q["frames"]["truss_chord"]

    parts.append(text(left + width / 2, 120, "VISTA LATERAL A · ELEVACIÓN ESTRUCTURAL (muro Y=0)", 18, weight=700))
    parts.append(text(left + width / 2, 140, f"Largo 36,00 m · alero bajo ≈ {eave} m (toda el agua descarga aquí · D-039) · solo estructura", 10, fill="#59676c"))

    # Envolvente / plano del muro.
    parts.append(line(left, base, left + width, base, color="#172126", width=3))
    top = yy(eave)
    parts.append(line(left, top, left + width, top, color="#172126", width=3))
    # Eave alta (B) en línea discontinua para leer el monopitch.
    parts.append(line(left, yy(eave_high), left + width, yy(eave_high), color="#8a9396", width=1.5, dash="10 5"))

    # Columnas HEA200 del sistema CERCHA en los pórticos M60.
    for x in frames:
        px = xx(x)
        parts.append(line(px, base, px, top, color="#172126", width=6))
        parts.append(poly([(px - 8, base), (px + 8, base), (px, base + 10), (px - 8, base)], color="#536166", width=1.2))
    parts.append(text(left + width + 8, top, f"{len(frames)} COLUMNAS {col} EN M60", 8, weight=700, fill="#172126", anchor="start"))

    # Arriostramiento vertical en los paños de borde (estabilidad longitudinal).
    for zone in ((0, 12), (24, 36)):
        xa, xb = zone
        parts.append(line(xx(xa), base, xx(xb), top, color="#7a8689", width=1.2, dash="7 4"))
        parts.append(line(xx(xa), top, xx(xb), base, color="#7a8689", width=1.2, dash="7 4"))
    parts.append(text(xx(6), yy(3.0), "X-BRACING VERTICAL", 7, weight=700, fill="#667377"))
    parts.append(text(xx(30), yy(3.0), "X-BRACING VERTICAL", 7, weight=700, fill="#667377"))

    # P2 y esquema GRAN-MURO (visto en el muro A): borde X=21, vigas longitudinales y muro X=31,5.
    p2x = xx(cfg["geometry"]["p2_start_x_m"])
    p2y = yy(3.8)
    parts.append(line(p2x, top, p2x, base, color="#687579", width=1.2, dash="7 5"))
    parts.append(line(p2x, p2y, xx(36), p2y, color="#3f7d8a", width=2.5, dash="9 5"))
    parts.append(text(xx(28.5), p2y - 8, f"P2 POSTERIOR · 15,00 m · +3,80 · vigas longitudinales {gw['beam_profile']} + losa (paneles {18.0/gw['n_beams']:.0f} m)", 8, weight=700, fill="#3f7d8a"))
    # Borde X=21 (cercha de borde de 18 m, de canto) y muro estructural X=31,5 (núcleo de corte).
    parts.append(rect(xx(21) - 3, p2y - gw['edge_truss_depth_m'] * sc, 6, gw['edge_truss_depth_m'] * sc, fill="#3f7d8a", stroke="#274a53", stroke_width=1))
    parts.append(text(xx(21), p2y - gw['edge_truss_depth_m'] * sc - 6, "BORDE X=21", 6, weight=700, fill="#3f7d8a"))
    parts.append(rect(xx(31.5) - 4, top, 8, base - top, fill="#d9c9a0", stroke="#6b4a2e", stroke_width=1.2))
    parts.append(text(xx(31.5), (base + top) / 2, "MURO ESTRUCTURAL X=31,5 · portante + caja de escalera + núcleo de corte", 6.5, weight=700, fill="#6b4a2e", rotate=-90))

    # Aberturas de contexto (tenues) para orientar.
    for g in pb["technical_glazing"]:
        if g["side"] != "A":
            continue
        x1 = xx(g["x0"]); x2 = xx(g["x1"])
        y1 = yy(g["sill"] + g["height"]); y2 = yy(g["sill"])
        parts.append(rect(x1, y1, x2 - x1, y2 - y1, fill="#cfe0e3", stroke="#8aa4a9", stroke_width=0.8, opacity="0.55"))
        parts.append(text((x1 + x2) / 2, (y1 + y2) / 2, "VENTANAL TÉCNICO 7,20 m", 6, fill="#46707a"))
    for g in pb["bedroom_glazing"]:
        if g["facade"] != "A":
            continue
        x1 = xx(g["from"]); x2 = xx(g["to"])
        y1 = yy(3.8 + g["sill"] + g["height"]); y2 = yy(3.8 + g["sill"])
        parts.append(rect(x1, y1, x2 - x1, y2 - y1, fill="#cfe0e3", stroke="#8aa4a9", stroke_width=0.8, opacity="0.45"))
    # Claraboya del taller (solo afecta correas).
    parts.append(rect(xx(2.4), yy(eave), xx(4.8) - xx(2.4), 10, fill="#d9c9a0", stroke="#8a7a4f", stroke_width=0.8, opacity="0.7"))
    parts.append(text(xx(3.6), yy(eave) - 6, "CLARABOYA 2,40 m (b08)", 6, fill="#8a7a4f"))

    # Cotas.
    dimy = base + 46
    parts.append(line(left, dimy, left + width, dimy, color="#536166"))
    for x in frames:
        parts.append(line(xx(x), dimy - 6, xx(x), dimy + 6, color="#536166"))
    for a, b, label in ((0, 6, "6,00"), (6, 12, "6,00"), (12, 18, "6,00"), (18, 24, "6,00"), (24, 30, "6,00"), (30, 36, "6,00")):
        parts.append(text((xx(a) + xx(b)) / 2, dimy - 9, label, 7))
    parts.append(text(left + width / 2, dimy + 24, "36,00 m · vanos M60", 10, weight=700))
    hdim = left - 30
    parts.append(line(hdim, base, hdim, top, color="#536166"))
    parts.append(line(hdim - 6, base, hdim + 6, base, color="#536166"))
    parts.append(line(hdim - 6, top, hdim + 6, top, color="#536166"))
    parts.append(line(hdim - 6, p2y, hdim + 6, p2y, color="#536166"))
    parts.append(text(hdim - 14, (base + top) / 2, f"{eave} m", 8, rotate=-90))
    parts.append(text(hdim - 14, (base + p2y) / 2, "3,80 m", 7, rotate=-90))

    parts.append(text(left + width / 2, 170, f"CUBIERTA: CERCHA {chord} (L/16) EN {len(frames)} LÍNEAS · P2: {gw['n_beams']} VIGAS {gw['beam_profile']} + BORDE {gw['edge_chord']} SOBRE GRAN MURO", 9, weight=700, fill="#243238"))


# ---------------------------------------------------------------- NOTAS

def note_box(parts, q, st, gw):
    lines = [
        "Cálculo EN VIVO: esta lámina se dibuja desde structure_system.json vía el modelo (no usa salidas exportadas).",
    ]
    if q and gw:
        total_gw = q["total_greatwall_kg"]
        lines.append(
            f"Modelo E0 · M60 · CERCHA: marcos {q['main_frames_kg']/1000:.1f} t · columnas {q['frames']['column']} · "
            f"cuerda {q['frames']['truss_chord']}. Entrepiso P2: metaldeck {q['p2_floor_metaldeck_kg']/1000:.1f} t "
            f"(con columnas) · staggered {q['p2_floor_staggered_kg']/1000:.1f} t · GRAN-MURO {q['p2_floor_greatwall_kg']/1000:.1f} t."
        )
        lines.append(
            f"GRAN-MURO (preferido): {gw['n_beams']} vigas longitudinales {gw['beam_profile']} de {gw['beam_span_m']} m en el plenum "
            f"(Y≈3/9/15) + cercha de borde X=21 (luz 18 m, cordón {gw['edge_chord']}) + gran muro portante (axial ≈ "
            f"{gw['wall_axial_kn_m']} kN/m, núcleo de corte) + franja núcleo sobre el muro (luz {gw['nucleus_span_m']} m). "
            f"fn del panel ≈ {gw['panel_frequency_hz']} Hz. Total estimado con GRAN-MURO ≈ {total_gw/1000:.1f} t "
            f"(≈ {q['kg_m2_greatwall']} kg/m²)."
        )
        if st:
            lines.append(
                f"Staggered (alternativa): {st['n_trusses']} cerchas de 18 m, canto {st['truss_depth_m']} m (d/L {st['truss_d_over_l']}), "
                f"paneles {st['panel_span_m']} m sin viguetas, fn ≈ {st['panel_frequency_hz']} Hz — exige re-articular particiones."
            )
    lines += [
        "Cero columnas interiores en los tres esquemas; el gran muro además aporta rigidez lateral longitudinal (wind girder simplificado).",
        "NO APTO PARA CONSTRUIR · hipótesis de esquema para inspección visual, no diseño profesional.",
    ]
    parts.append(rect(70, 780, 1260, 92, fill="#fff4df", stroke="#bd5c3c", stroke_width=1))
    parts.append(text(90, 803, "RESUMEN DE CÁLCULO (modelo E0 · en vivo)", 12, "start", 700, "#8e3825"))
    for i, n in enumerate(lines):
        parts.append(text(90, 826 + i * 14, "• " + n, 8.5, "start", 700 if i == len(lines) - 1 else 400, "#8e3825" if i == len(lines) - 1 else "#3f4c51"))


# ---------------------------------------------------------------- MAIN

def build_sheets():
    cfg = json.loads(SYSTEM.read_text(encoding="utf-8"))
    pb = json.loads(PB.read_text(encoding="utf-8"))
    q, st = live_results(cfg)
    gw = q["great_wall"]

    # Lámina 1: planta + corte B-B.
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="900" viewBox="0 0 1400 900">']
    parts.append(title_block("PLANTA DE ESTRUCTURA + CORTE B-B · SOLO ESTRUCTURA (E0)",
                             "Inspección visual de coordinación · retícula M60 · perfiles y tonelajes calculados en vivo", SHEET2))
    parts.append('<g font-family="Arial" fill="#20292e">')
    draw_plan(parts, cfg, pb, gw)
    draw_section(parts, cfg, gw)
    parts.append('</g>')
    note_box(parts, q, st, gw)
    parts.append('</svg>')

    # Lámina 2: vista lateral A.
    parts2 = ['<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="900" viewBox="0 0 1400 900">']
    parts2.append(title_block("VISTA LATERAL A · ESTRUCTURA (E0)",
                              "Elevación estructural del muro Y=0 · perfiles y cotas calculados en vivo", SHEET3))
    parts2.append('<g font-family="Arial" fill="#20292e">')
    draw_lateral(parts2, cfg, pb, q, gw)
    parts2.append('</g>')
    note_box(parts2, q, st, gw)
    parts2.append('</svg>')

    return {"DH-EST-E0-002_ESTRUCTURA-INSPECCION.svg": "".join(parts),
            "DH-EST-E0-003_ESTRUCTURA-LATERAL-A.svg": "".join(parts2)}


def main():
    cfg = json.loads(SYSTEM.read_text(encoding="utf-8"))
    outputs = build_sheets()
    OUT.mkdir(parents=True, exist_ok=True)
    for name, content in outputs.items():
        OUT.joinpath(name).write_text(content, encoding="utf-8")
    manifest = {
        "input": [str(SYSTEM.relative_to(ROOT)), str(PB.relative_to(ROOT))],
        "generator": "dreamhouse/generate_structure_plan.py",
        "revision": cfg["project"]["revision"],
        "mode": "cálculo en vivo (compute_quantities + size_staggered_floor) — sin salidas exportadas",
        "outputs": list(outputs),
        "status": "hipótesis de esquema; NO APTO PARA CONSTRUIR",
    }
    OUT.joinpath("manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"outputs": list(outputs), "live": True}))


if __name__ == "__main__":
    main()
