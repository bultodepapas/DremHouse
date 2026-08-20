from __future__ import annotations

import hashlib
import html
import json
from itertools import pairwise
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(__file__).with_name("pb_b05.json")
OUT = ROOT / "planos" / "conceptual_v0.3_b05_pb"

S = 27.0
X0, Y0 = 205.0, 155.0


def esc(value: str) -> str:
    return html.escape(value)


def rect(x, y, w, h, **attrs):
    a = " ".join(f'{k.replace("_", "-")}="{v}"' for k, v in attrs.items())
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" {a}/>'


def sx(x):
    return X0 + x * S


def sy(y):
    return Y0 + (18 - y) * S


def core_net_y(room, p):
    """Rango neto en Y de un recinto del núcleo, según el tipo de cada borde.

    Antes se descontaba el espesor de envolvente (0,18 m) a los dos lados de todos
    los recintos, con lo que los tabiques interiores se dibujaban a 0,36 m cuando
    D-034 los declara a 0,15 m (y 0,20 m contra la caja de escalera) — hallazgo H-13.
    """
    ext = p["envelope"]["exterior_wall"]
    dv = p["design_values"]
    def half(b):
        stair = abs(b-7.4) < 1e-9 or abs(b-11.0) < 1e-9
        return (dv["partition_stair"] if stair else dv["partition_standard"])/2
    y0, y1 = room["y0"], room["y1"]
    a = ext if abs(y0) < 1e-9 else half(y0)
    b = ext if abs(y1-18) < 1e-9 else half(y1)
    return y0+a, y1-b


def plan_rect(x, y, w, d, **attrs):
    return rect(sx(x), sy(y + d), w * S, d * S, **attrs)


def text(x, y, value, size=10, anchor="middle", weight=400, fill="#243238", rotate=None):
    transform = f' transform="rotate({rotate} {x} {y})"' if rotate is not None else ""
    return f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" font-weight="{weight}" fill="{fill}"{transform}>{esc(value)}</text>'


def door_on_wall(x, y, width, emphasized=False):
    px, py, r = sx(x), sy(y), width * S
    color = "#9d4a2f" if not emphasized else "#754522"
    sw = 1.6 if not emphasized else 3.0
    return (
        f'<g stroke="{color}" fill="none" stroke-width="{sw}">'
        f'<line x1="{px}" y1="{py}" x2="{px+r}" y2="{py}"/>'
        f'<path d="M {px} {py} A {r} {r} 0 0 1 {px} {py-r}" stroke-dasharray="4 3"/>'
        '</g>'
    )


def rear_door(y, width):
    x, y1, y2 = sx(36), sy(y + width), sy(y)
    return f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2}" stroke="#236a45" stroke-width="7"/>'


def car_symbol(x, y, w=4.8, d=2.0):
    px, py, pw, ph = sx(x), sy(y + d), w * S, d * S
    return (
        f'<g stroke="#4e5d63" fill="#edf0ef" stroke-width="1.2">'
        f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="18"/>'
        f'<rect x="{px+pw*.24}" y="{py+ph*.12}" width="{pw*.52}" height="{ph*.76}" rx="10" fill="#c9d6d8"/>'
        f'<circle cx="{px+pw*.18}" cy="{py}" r="5" fill="#30393d"/><circle cx="{px+pw*.82}" cy="{py}" r="5" fill="#30393d"/>'
        f'<circle cx="{px+pw*.18}" cy="{py+ph}" r="5" fill="#30393d"/><circle cx="{px+pw*.82}" cy="{py+ph}" r="5" fill="#30393d"/>'
        '</g>'
    )


def table_symbol(x, y, w, d, label):
    px, py, pw, ph = sx(x), sy(y + d), w * S, d * S
    return rect(px, py, pw, ph, fill="#eee6d7", stroke="#59676c", stroke_width="1.2", rx="3") + text(px + pw/2, py + ph/2 + 3, label, 8)


def chair(cx, cy, r=7):
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#f4f1ea" stroke="#667378"/>'


def stair_symbol():
    x, y, w, d = sx(31.72), sy(10.78), 4.06*S, 3.16*S
    pieces = [rect(x, y, w, d, fill="#f0ebe4", stroke="#45545a", stroke_width="1.2")]
    for i in range(1, 11):
        yy = y + i*d/11
        pieces.append(f'<line x1="{x}" y1="{yy}" x2="{x+w*.38}" y2="{yy}" stroke="#69777c"/><line x1="{x+w*.62}" y1="{yy}" x2="{x+w}" y2="{yy}" stroke="#69777c"/>')
    pieces.append(f'<line x1="{x+w*.5}" y1="{y+d*.78}" x2="{x+w*.5}" y2="{y+d*.22}" stroke="#45545a" stroke-width="1.4"/><polyline points="{x+w*.44},{y+d*.30} {x+w*.5},{y+d*.22} {x+w*.56},{y+d*.30}" fill="none" stroke="#45545a"/>')
    return ''.join(pieces)


def title_block(sheet, title_value, subtitle):
    return (
        '<rect width="1400" height="900" fill="#fbfaf7"/>'
        '<g font-family="Arial">'
        + text(70, 45, title_value, 26, "start", 700)
        + text(70, 72, subtitle, 12, "start", 400, "#59676c")
        + text(1325, 105, sheet, 16, "end", 700, "#7e3f2c")
        + '</g>'
    )


def plan_sheet(p):
    L, W = p["envelope"]["length"], p["envelope"]["width"]
    ext = p["envelope"]["exterior_wall"]
    wall = p["great_wall"]
    meta = p.get("drawing_meta", {})
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="900" viewBox="0 0 1400 900">',
        title_block(
            meta.get("plan_code", "PLN-001-R04"),
            meta.get("plan_title", "PLANTA BAJA DETALLADA · ANTEPROYECTO"),
            meta.get(
                "plan_subtitle",
                "Rev. 0.3-borrador-05-PB · espesores y equipamiento de estudio · cotas en metros",
            ),
        ),
    ]
    parts.append('<defs><pattern id="concrete" width="9" height="9" patternUnits="userSpaceOnUse"><path d="M0 9L9 0" stroke="#d9d7d1" stroke-width=".5"/></pattern><pattern id="wood" width="8" height="8" patternUnits="userSpaceOnUse"><line x1="2" y1="0" x2="2" y2="8" stroke="#9a704d" stroke-width="1"/></pattern><pattern id="service" width="7" height="7" patternUnits="userSpaceOnUse"><path d="M0 0L7 7M7 0L0 7" stroke="#c5ceca" stroke-width=".45"/></pattern></defs>')

    # Exterior platform and continuous industrial slab.
    parts.append(plan_rect(-3.0, 0, 3.0, 18, fill="#dedbd4", stroke="#8e9493", stroke_width="1"))
    parts.append(text(sx(-1.5), sy(9), "PLATAFORMA FRONTAL 3,00 m · pendiente 1,5–2% hacia drenaje", 8, rotate=-90))
    parts.append(plan_rect(0, 0, L, W, fill="url(#concrete)", stroke="#172126", stroke_width="6"))
    parts.append(plan_rect(ext, ext, L-2*ext, W-2*ext, fill="#fbfaf7", stroke="#7b878a", stroke_width="1.2"))

    # Program territories, without creating walls.
    zones = [
        (0.18,0.18,10.32,6.82,"CAR PROJECT · 70,4 m² netos aprox.","#d6e0e4"),
        (0.18,11.0,10.32,6.82,"RC / DIY · 70,4 m² netos aprox.","#d6e0e4"),
        (10.5,0.18,2.0,17.64,"FRANJA DE RESPIRACIÓN", "#f1eee7"),
        (12.5,3.2,8.5,11.6,"SALA MONUMENTAL", "#e6d7c7"),
        (21.0,0.18,5.5,7.82,"COMEDOR", "#e7d3b9"),
        (21.0,11.0,5.5,6.82,"ESTAR / TRANSICIÓN", "#e7d3b9"),
        (26.5,0.18,5.0,17.64,"COCINA + GALERÍA DOMÉSTICA", "#ead4b6")
    ]
    for x,y,w,d,label,color in zones:
        parts.append(plan_rect(x,y,w,d,fill=color,stroke="#9aa2a2",stroke_width=".7",stroke_dasharray="5 4",opacity=".72"))
        label_y = y+d/2
        if label.startswith("FRANJA"):
            label_y = 12.0
        elif label.startswith("SALA"):
            label_y = 12.6
        elif label.startswith("COCINA"):
            label_y = 14.0
        parts.append(text(sx(x+w/2),sy(label_y),label,9,weight=700,fill="#45545a"))

    # Clear central axis.
    axis0, axis1 = p["design_values"]["axis_y0"], p["design_values"]["axis_y1"]
    parts.append(plan_rect(0.18,axis0,L-0.36,axis1-axis0,fill="none",stroke="#b47d16",stroke_width="2",stroke_dasharray="10 5"))
    parts.append(text(sx(18),sy((axis0+axis1)/2)+4,"EJE PEATONAL PERCEPTUAL LIBRE · 4,00 m",10,weight=700,fill="#8a6518"))

    # Core and great wall.
    parts.append(plan_rect(31.5,0,wall["thickness"],18,fill="url(#wood)",stroke="#6e4b30",stroke_width="1.5"))
    core_colors = {"service":"#d9d2bd","storage":"#cad0c9","stair":"#d2c5b9","wet":"#bfd6d3","technical":"#c4d1cc"}
    partition = p["design_values"]["partition_standard"]
    for room in p["core"]:
        y0, y1 = room["y0"], room["y1"]
        ny0,ny1=core_net_y(room,p)
        parts.append(plan_rect(31.7,ny0,4.12,max(0.01,ny1-ny0),fill=core_colors[room["type"]],stroke="#536166",stroke_width="1"))
        parts.append(text(sx(33.76),sy((y0+y1)/2)-4,room["name"],9,weight=700))
        parts.append(text(sx(33.76),sy((y0+y1)/2)+10,f'{room["gross_area"]:.1f} m² brutos',7,fill="#526168"))
        parts.append(door_on_wall(31.5,room["door_y"],room["door_width"],room["id"]=="ESC"))
    for boundary in (2.4,7.4,11.0,13.4):
        thick = p["design_values"]["partition_stair"] if boundary in (7.4,11.0) else partition
        parts.append(plan_rect(31.7,boundary-thick/2,4.12,thick,fill="#526168",stroke="none"))
    for d in p["exterior_doors"]:
        parts.append(rear_door(d["y"],d["width"]))

    # Kitchen, pantry relationship and equipment.
    k = p["kitchen"]
    kr, ki = k["wall_run"], k["island"]
    parts.append(plan_rect(kr["x"],kr["y"],kr["length"],kr["depth"],fill="#b69066",stroke="#60492f",stroke_width="1.2"))
    modules = [(26.7,"FR"),(27.6,"H"),(28.5,"PL"),(29.4,"LV"),(30.3,"AL")]
    for mx,label in modules:
        parts.append(plan_rect(mx,.25,.85,.75,fill="none",stroke="#72583c",stroke_width=".7"))
        parts.append(text(sx(mx+.425),sy(.63)+3,label,6,weight=700))
    parts.append(plan_rect(ki["x"],ki["y"],ki["length"],ki["depth"],fill="#d1b187",stroke="#60492f",stroke_width="1.3",rx="3"))
    parts.append(text(sx(ki["x"]+ki["length"]/2),sy(ki["y"]+ki["depth"]/2)+3,"ISLA 3,60 × 1,20 · 4 puestos",8,weight=700))
    for i in range(4):
        parts.append(chair(sx(27.35+i*.85),sy(3.65)))
    parts.append(text(sx(29),sy(1.6),"1,20 m operativo",7,fill="#7b552b"))
    parts.append(text(sx(29),sy(4.15),"≥1,50 m social",7,fill="#7b552b"))

    # Dining and living furniture.
    parts.append(table_symbol(22.0,2.2,3.6,1.3,"MESA 12 P · 3,60 × 1,30"))
    for i in range(6):
        parts.append(chair(sx(22.3+i*.6),sy(2.0)))
        parts.append(chair(sx(22.3+i*.6),sy(3.7)))
    parts.append(plan_rect(14.0,3.7,5.8,5.0,fill="#d9c6b2",stroke="#8b7765",stroke_width="1",rx="18"))
    parts.append(plan_rect(14.4,4.1,4.8,1.05,fill="#bda893",stroke="#796756",stroke_width="1",rx="10"))
    parts.append(plan_rect(14.4,7.1,4.8,1.05,fill="#bda893",stroke="#796756",stroke_width="1",rx="10"))
    parts.append(table_symbol(16.0,5.45,1.6,1.2,"CENTRO"))

    # Workstations, glazing and acoustic curtain pockets. Later revisions can describe
    # the pair parametrically; b05 retains the original historical symbols.
    if p.get("workstations"):
        workstation_windows = {item["id"]: item for item in p["workstation_glazing"]}
        for ws in p["workstations"]:
            is_a = ws["side"] == "A"
            zone_y = ext if is_a else W - ext - ws["zone_depth"]
            work_y = ext if is_a else W - ext - ws["worktop_depth"]
            chair_y = work_y + ws["worktop_depth"] + 0.35 if is_a else work_y - 1.0
            zone_width = ws["zone_x1"] - ws["zone_x0"]
            parts.append(
                plan_rect(
                    ws["zone_x0"],
                    zone_y,
                    zone_width,
                    ws["zone_depth"],
                    fill="#e8f0ed",
                    stroke="#5d6d69",
                    stroke_width="1.2",
                    stroke_dasharray="7 4",
                    opacity=".62",
                )
            )
            parts.append(
                plan_rect(
                    ws["worktop_x0"],
                    work_y,
                    ws["worktop_length"],
                    ws["worktop_depth"],
                    fill="#d7c29b",
                    stroke="#3d4c51",
                    stroke_width="1.4",
                    rx="2",
                )
            )
            cabinet_width = ws.get("drawer_cabinet_width")
            cabinet_depth = ws.get("drawer_cabinet_depth")
            if cabinet_width and cabinet_depth:
                cabinet_y = (
                    ext if is_a else W - ext - cabinet_depth
                )
                for cabinet_x in (
                    ws["worktop_x0"],
                    ws["worktop_x0"] + ws["worktop_length"] - cabinet_width,
                ):
                    parts.append(
                        plan_rect(
                            cabinet_x,
                            cabinet_y,
                            cabinet_width,
                            cabinet_depth,
                            fill="#9e7650",
                            stroke="#3d4c51",
                            stroke_width="1.1",
                            rx="1",
                        )
                    )
                    parts.append(
                        text(
                            sx(cabinet_x + cabinet_width / 2),
                            sy(cabinet_y + cabinet_depth / 2) + 1.5,
                            f'{ws.get("drawer_levels", 3)}D',
                            4.8,
                            weight=700,
                            fill="#fff8ed",
                        )
                    )
            parts.append(
                text(
                    sx(ws["worktop_x0"] + ws["worktop_length"] / 2),
                    sy(work_y + ws["worktop_depth"] / 2) + 2,
                    "FIXED WORKTOP",
                    5.8,
                    weight=700,
                    fill="#4f3925",
                )
            )
            rail_y = sy(ext if is_a else W - ext)
            parts.append(
                f'<line x1="{sx(ws["worktop_x0"])}" y1="{rail_y}" '
                f'x2="{sx(ws["worktop_x0"] + ws["worktop_length"])}" y2="{rail_y}" '
                'stroke="#26363b" stroke-width="4"/>'
            )
            for bx in (0.2, 1.2, 2.2):
                px = sx(ws["worktop_x0"] + bx)
                inner_y = sy(ext + ws["worktop_depth"] if is_a else W - ext - ws["worktop_depth"])
                parts.append(
                    f'<line x1="{px}" y1="{rail_y}" x2="{px}" y2="{inner_y}" '
                    'stroke="#3d4c51" stroke-width="1.5"/>'
                )
            parts.append(
                plan_rect(
                    ws["worktop_x0"] + ws["worktop_length"] / 2 - 0.33,
                    chair_y,
                    0.66,
                    0.66,
                    fill="#f5f1e8",
                    stroke="#667378",
                    stroke_width="1",
                    rx="8",
                )
            )
            label_y = zone_y + ws["zone_depth"] - 0.32 if is_a else zone_y + 0.32
            window = workstation_windows[ws["window_id"]]
            parts.append(
                text(
                    sx((ws["zone_x0"] + ws["zone_x1"]) / 2),
                    sy(label_y),
                    f'{ws["name"].upper()} · 3 × 3 m CLEAR',
                    6.6,
                    weight=700,
                    fill="#294b52",
                )
            )
            facade_y = sy(0 if is_a else W)
            parts.append(
                f'<line x1="{sx(window["x0"])}" y1="{facade_y}" '
                f'x2="{sx(window["x1"])}" y2="{facade_y}" '
                'stroke="#27859a" stroke-width="8"/>'
            )
            parts.append(
                text(
                    sx((window["x0"] + window["x1"]) / 2),
                    # On Side A the neighbouring main-glazing label occupies the
                    # exterior strip; keep this label inside its own 3 m bay.
                    facade_y + (-32 if is_a else -10),
                    f'{window["name"].upper()} · {window["x1"] - window["x0"]:.2f} m',
                    6.5,
                    weight=700,
                    fill="#246b7a",
                )
            )
    else:
        for y,label in ((0.35,"TRABAJO 1 · 3×3"),(14.65,"TRABAJO 2 · 3×3")):
            parts.append(plan_rect(13.0,y,3.0,3.0,fill="#d3ded9",stroke="#5d6d69",stroke_width="1"))
            parts.append(table_symbol(13.35,y+.35,2.2,.75,"ESCRITORIO"))
            parts.append(text(sx(14.5),sy(y+2.55),label,7,weight=700))
    parts.append(f'<line x1="{sx(16.2)}" y1="{sy(0)}" x2="{sx(20.5)}" y2="{sy(0)}" stroke="#27859a" stroke-width="8"/>')
    parts.append(f'<line x1="{sx(16.2)}" y1="{sy(.28)}" x2="{sx(20.5)}" y2="{sy(.28)}" stroke="#846e93" stroke-width="2" stroke-dasharray="5 3"/>')
    main_glazing_label_y = sy(0) + 15 if p.get("workstations") else sy(.55)
    parts.append(text(sx(18.35),main_glazing_label_y,"VIDRIO PRINCIPAL PROVISIONAL · bolsillo de cortina acústica",7,fill="#246b7a"))

    # Car bay and lift safety envelope.
    parts.append(plan_rect(1.6,.45,6.4,5.9,fill="none",stroke="#b14e35",stroke_width="1.8",stroke_dasharray="9 5"))
    parts.append(text(sx(4.8),sy(6.15),"PRISMA DE EXCLUSIÓN LIFT / VEHÍCULO",7,weight=700,fill="#9a3d2a"))
    parts.append(car_symbol(2.25,1.55))
    for px in (2.0,6.85):
        parts.append(plan_rect(px,.65,.35,4.0,fill="#48555b",stroke="#263238",stroke_width="1"))
    if p.get("built_in_benches"):
        car_bench = next(item for item in p["built_in_benches"] if item["id"] == "PB-BENCH-CAR")
        parts.append(
            plan_rect(
                car_bench["x0"], car_bench["y0"], car_bench["length"], car_bench["depth"],
                fill="#aeb9bc", stroke="#314247", stroke_width="1.4",
            )
        )
        parts.append(
            text(
                sx(car_bench["x0"] + car_bench["length"] / 2),
                sy(car_bench["y0"] + car_bench["depth"] / 2) + 3,
                "PROJECT-CAR STEEL BENCH · LIFT HOLD",
                6.5,
                weight=700,
            )
        )
    else:
        parts.append(plan_rect(.55,5.85,9.0,.75,fill="#aeb9bc",stroke="#5d6a6e",stroke_width="1"))
        parts.append(text(sx(5.05),sy(6.225)+3,"BANCO AUTOMOTRIZ 9,00 m · extracción en fuente / potencia dedicada",7))

    # RC/DIY benches, printers, LiPo and local extraction.
    if p.get("built_in_benches"):
        rc_bench = next(item for item in p["built_in_benches"] if item["id"] == "PB-BENCH-RC")
        parts.append(
            plan_rect(
                rc_bench["x0"], rc_bench["y0"], rc_bench["length"], rc_bench["depth"],
                fill="#aeb9bc", stroke="#314247", stroke_width="1.4",
            )
        )
        parts.append(
            text(
                sx(rc_bench["x0"] + rc_bench["length"] / 2),
                sy(rc_bench["y0"]) + 10,
                "RC / ELECTRONICS INTEGRATED BENCH · 9.00 m",
                6.5,
                weight=700,
            )
        )
    else:
        parts.append(plan_rect(.55,16.65,9.0,.75,fill="#aeb9bc",stroke="#5d6a6e",stroke_width="1"))
        parts.append(text(sx(5.05),sy(17.03)+3,"BANCO RC / ELECTRÓNICA 9,00 m",7))
    parts.append(table_symbol(2.8,12.7,4.5,1.6,"BANCO CENTRAL RC · 4,50 × 1,60"))
    parts.append(plan_rect(.65,14.4,1.2,1.8,fill="#c8d2d4",stroke="#54636a",stroke_width="1"))
    parts.append(text(sx(1.25),sy(15.3)+3,"3D ×3",7,weight=700))
    parts.append(plan_rect(8.15,14.4,1.25,1.8,fill="#d9c3b5",stroke="#8f4e38",stroke_width="1.2"))
    parts.append(text(sx(8.775),sy(15.15),"LiPo",7,weight=700,fill="#8f3c28"))
    parts.append(text(sx(8.775),sy(15.55),"ventilado",6,fill="#8f3c28"))
    parts.append(f'<path d="M {sx(8.78)} {sy(16.2)} L {sx(8.78)} {sy(17.65)}" stroke="#27859a" stroke-width="2" stroke-dasharray="5 3"/>')

    # PB bathroom fixtures and technical rooms.
    parts.append(plan_rect(32.05,11.35,1.2,1.1,fill="none",stroke="#27859a",stroke_width="1.2"))
    parts.append(f'<ellipse cx="{sx(35.15)}" cy="{sy(11.75)}" rx="9" ry="13" fill="#f8faf9" stroke="#59686d"/>')
    parts.append(plan_rect(33.45,12.72,1.0,.45,fill="#f8faf9",stroke="#59686d",stroke_width="1"))
    parts.append(plan_rect(32.05,14.0,1.05,.8,fill="#434f54",stroke="#1f292d",stroke_width="1"))
    parts.append(text(sx(32.575),sy(14.4)+3,"RACK",6,fill="#f6f4ed",weight=700))
    parts.append(plan_rect(34.2,14.0,1.25,1.7,fill="url(#service)",stroke="#59686d",stroke_width="1"))
    parts.append(text(sx(34.825),sy(14.85)+3,"UPS / TAB",6,weight=700))
    parts.append(plan_rect(32.05,.45,1.0,1.4,fill="#d9d1bd",stroke="#6d6657",stroke_width="1"))
    parts.append(text(sx(32.55),sy(1.15)+3,"FRÍO",6,weight=700))
    parts.append(plan_rect(34.0,.45,1.45,1.4,fill="#d9d1bd",stroke="#6d6657",stroke_width="1"))
    parts.append(text(sx(34.725),sy(1.15)+3,"LIMPIEZA",6,weight=700))
    parts.append(stair_symbol())


    # Front openings.
    for op in p["front_openings"]:
        y1, y2 = sy(op["y0"]+op["width"]), sy(op["y0"])
        parts.append(f'<line x1="{sx(0)}" y1="{y1}" x2="{sx(0)}" y2="{y2}" stroke="#b95336" stroke-width="8"/>')
        parts.append(text(sx(-.25), (y1+y2)/2, op["name"], 6, rotate=-90, fill="#873923"))

    # Large technical glazing on both long façades.
    for g in p["technical_glazing"]:
        yy=sy(0) if g["side"]=="A" else sy(18)
        parts.append(f'<line x1="{sx(g["x0"])}" y1="{yy}" x2="{sx(g["x1"])}" y2="{yy}" stroke="#27859a" stroke-width="8"/>')
        if p.get("workstations"):
            offset = 15 if g["side"] == "A" else -10
        else:
            offset=-13 if g["side"]=="A" else 18
        parts.append(text((sx(g["x0"])+sx(g["x1"]))/2,yy+offset,g["name"].upper()+" · 7,20 m",7,weight=700,fill="#246b7a"))

    # Grid and dimensions.
    for i,x in enumerate((0,6,12,18,24,30,36)):
        px=sx(x)
        parts.append(f'<line x1="{px}" y1="{Y0-18}" x2="{px}" y2="{Y0+18*S+18}" stroke="#9ea5a5" stroke-width=".6" stroke-dasharray="4 5"/>')
        parts.append(f'<circle cx="{px}" cy="{Y0-31}" r="10" fill="#fbfaf7" stroke="#5a666a"/>')
        parts.append(text(px,Y0-27,chr(65+i),8))
    dimy=Y0+18*S+42
    parts.append(f'<line x1="{sx(0)}" y1="{dimy}" x2="{sx(36)}" y2="{dimy}" stroke="#536166"/>')
    for x in (0,10.5,21,31.5,36):
        parts.append(f'<line x1="{sx(x)}" y1="{dimy-6}" x2="{sx(x)}" y2="{dimy+6}" stroke="#536166"/>')
    for a,b,label in ((0,10.5,"10,50"),(10.5,21,"10,50"),(21,31.5,"10,50"),(31.5,36,"4,50")):
        parts.append(text((sx(a)+sx(b))/2,dimy-7,label,8))
    parts.append(text((sx(0)+sx(36))/2,dimy+25,"36,00 m nominales exteriores",10,weight=700))

    # Key notes and legend.
    parts.append(rect(70,735,1260,110,fill="#fff4df",stroke="#bd5c3c",stroke_width="1"))
    parts.append(text(90,760,"CRITERIOS DE ESTA REVISIÓN",13,"start",700,"#8e3825"))
    notes=[
        "Envolvente 0,18 m; gran muro 0,20 m; divisiones 0,15 m y escalera 0,20 m: valores de estudio, no especificación IFC.",
        "Gran muro continuo de madera/listón con respaldo absorbente: puertas de pantry, bodega, baño y homelab enrasadas; escalera deliberadamente legible.",
        "Losa industrial continua; juntas, pendientes, cargas del lift, drenajes, estructura, fuego, extracción y MEP siguen pendientes de ingeniería y predio.",
        "NO APTO PARA CONSTRUIR. El mobiliario y equipos son envolventes de prueba y deben sustituirse por fichas reales."
    ]
    for i,n in enumerate(notes):
        parts.append(text(90,782+i*18,"• "+n,9,"start",700 if i==3 else 400,"#8e3825" if i==3 else "#3f4c51"))
    parts.append('</svg>')
    return ''.join(parts)


def wall_elevation_sheet(p):
    parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="900" viewBox="0 0 1400 900">',title_block("ELE-INT-001-R04","ELEVACIÓN INTERIOR · GRAN MURO POSTERIOR","MURO INTERIOR AL FONDO DE LA NAVE — NO ES LA FACHADA FRONTAL · vista hacia pantry, bodega, escalera, baño y homelab")]
    left, base, scale = 120, 610, 63
    top=base-3.2*scale
    parts.append('<defs><pattern id="slats" width="10" height="10" patternUnits="userSpaceOnUse"><line x1="2" y1="0" x2="2" y2="10" stroke="#835e3e" stroke-width="1.2"/></pattern></defs>')
    parts.append(rect(left,top,18*scale,3.2*scale,fill="#c7a47e",stroke="#332a24",stroke_width="3"))
    parts.append(rect(left,top,18*scale,3.2*scale,fill="url(#slats)",stroke="none"))
    boundaries=[0,2.4,7.4,11,13.4,18]
    for b in boundaries:
        x=left+b*scale
        parts.append(f'<line x1="{x}" y1="{top}" x2="{x}" y2="{base}" stroke="#725238" stroke-width=".7" opacity=".45"/>')
    for room in p["core"]:
        center=(room["y0"]+room["y1"])/2
        dw=room["door_width"]*scale
        dx=left+(room["door_y"]-.1)*scale
        dh=(2.45 if room["id"]=="ESC" else 2.30)*scale
        if room["id"]=="ESC":
            parts.append(rect(dx,base-dh,dw,dh,fill="#806044",stroke="#30251e",stroke_width="3"))
            parts.append(rect(dx-9,base-dh-9,dw+18,dh+9,fill="none",stroke="#513929",stroke_width="2"))
            parts.append(text(dx+dw/2,base-dh-16,"PORTAL ESCALERA",9,weight=700,fill="#513929"))
        else:
            parts.append(rect(dx,base-dh,dw,dh,fill="none",stroke="#6f513a",stroke_width="1.1"))
            parts.append(f'<circle cx="{dx+dw-10}" cy="{base-dh*.48}" r="2.5" fill="#3b3028"/>')
        parts.append(text(left+center*scale,base+25,room["name"].upper(),8,weight=700))
    parts.append(rect(left,base+48,18*scale,14,fill="#bbb8b0",stroke="#6c7271",stroke_width="1"))
    parts.append(text(left+9*scale,base+74,"ZÓCALO TÉCNICO CONTINUO / RETORNO DE SOMBRA · registrable por módulos",9,weight=700))
    parts.append(text(left+9*scale,top-28,"LISTÓN DE MADERA SOBRE SUBESTRUCTURA + ABSORCIÓN NEGRA · patrón continuo a coordinar con puertas",11,weight=700,fill="#6b462c"))
    dimy=base+115
    parts.append(f'<line x1="{left}" y1="{dimy}" x2="{left+18*scale}" y2="{dimy}" stroke="#536166"/>')
    for b in boundaries:
        x=left+b*scale
        parts.append(f'<line x1="{x}" y1="{dimy-7}" x2="{x}" y2="{dimy+7}" stroke="#536166"/>')
    labels=["2,40","5,00","3,60","2,40","4,60"]
    for a,b,label in zip(boundaries[:-1],boundaries[1:],labels):
        parts.append(text(left+(a+b)/2*scale,dimy-9,label,9))
    parts.append(text(left+9*scale,dimy+26,"18,00 m",11,weight=700))
    parts.append(rect(120,780,1134,65,fill="#fff4df",stroke="#bd5c3c",stroke_width="1"))
    parts.append(text(140,805,"INTENCIÓN",11,"start",700,"#8e3825"))
    parts.append(text(140,827,"El muro debe leerse como un solo testero cálido y acústico. Las juntas de puertas continúan el ritmo; solo la escalera se anuncia mediante portal profundo y luz.",9,"start"))
    parts.append(text(140,844,"Acabado, reacción al fuego, absorción, acceso técnico, herrajes y estabilidad requieren muestra 1:1 y especificación profesional.",8,"start",700,"#8e3825"))
    parts.append('</svg>')
    return ''.join(parts)


def roof_profile(p, sc, base):
    """Perfil del faldón para las láminas que mapean Y=0 a la izquierda.

    Devuelve (a_top, b_top, etiqueta_A, etiqueta_B) en coordenadas de lámina.
    Toda lámina que dibuje el faldón debe pasar por aquí: es lo único que impide
    que frontal, posterior y laterales vuelvan a contradecirse (hallazgo H-01).
    Invertir el faldón es cambiar `roof.low_side` en pb_b05.json, nada más.
    """
    r = p["roof"]
    a_is_low = r["low_side"] == "A"
    low_top, high_top = base-r["low_eave"]*sc, base-r["high_eave"]*sc
    a_top, b_top = (low_top, high_top) if a_is_low else (high_top, low_top)
    com = lambda v: f"{v:.2f}".replace(".", ",")
    a_eave = r["low_eave"] if a_is_low else r["high_eave"]
    b_eave = r["high_eave"] if a_is_low else r["low_eave"]
    a_label = f'LADO {"BAJO" if a_is_low else "ALTO"} ≈ {com(a_eave)} m · LATERAL A'
    b_label = f'LADO {"ALTO" if a_is_low else "BAJO"} ≈ {com(b_eave)} m · LATERAL B'
    return a_top, b_top, a_label, b_label


def front_elevation_sheet(p):
    parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="900" viewBox="0 0 1400 900">',title_block("ELE-001-R04","FACHADA FRONTAL DETALLADA · TRES ACCESOS","Portón carro + acceso peatonal central + portón RC/aviones · composición nominal 18,00 m")]
    left, base, sc = 140, 645, 62
    width = 18*sc
    a_top, b_top, a_txt, b_txt = roof_profile(p, sc, base)
    top = min(a_top, b_top)
    parts.append('<defs><pattern id="metal" width="16" height="16" patternUnits="userSpaceOnUse"><line x1="3" y1="0" x2="3" y2="16" stroke="#8e9799" stroke-width=".8"/></pattern><pattern id="doorpanel" width="18" height="18" patternUnits="userSpaceOnUse"><line x1="0" y1="5" x2="18" y2="5" stroke="#65747a" stroke-width="1"/></pattern></defs>')
    parts.append(f'<polygon points="{left},{base} {left},{a_top} {left+width},{b_top} {left+width},{base}" fill="#aeb5b6" stroke="#172126" stroke-width="4"/>')
    parts.append(f'<line x1="{left}" y1="{a_top}" x2="{left+width}" y2="{b_top}" stroke="#e6e9e7" stroke-width="4"/>')
    parts.append(text(left+10,a_top-12,a_txt,9,"start",700))
    parts.append(text(left+width-10,b_top-12,b_txt,9,"end",700))
    labels={"CAR":"PORTÓN CAR PROJECT","PED":"PUERTA PRINCIPAL","RC":"PORTÓN TALLER RC / AVIONES"}
    for op in p["front_openings"]:
        x=left+op["y0"]*sc
        w=op["width"]*sc
        h=op["height"]*sc
        y=base-h
        if op["id"]=="PED":
            parts.append(rect(x,y,w,h,fill="#303c41",stroke="#182126",stroke_width="3"))
            parts.append(rect(x+12,y+18,w-24,h-36,fill="#4b5a60",stroke="#9fa9aa",stroke_width="1"))
            parts.append(f'<circle cx="{x+w-17}" cy="{y+h*.52}" r="4" fill="#d9b56e"/>')
            parts.append(f'<line x1="{x-10}" y1="{y-18}" x2="{x+w+10}" y2="{y-18}" stroke="#d5a65c" stroke-width="4"/>')
        else:
            parts.append(rect(x,y,w,h,fill="#39484e",stroke="#172126",stroke_width="3"))
            parts.append(rect(x+6,y+6,w-12,h-12,fill="url(#doorpanel)",stroke="#718086",stroke_width="1"))
            parts.append(f'<line x1="{x+w/2}" y1="{y+6}" x2="{x+w/2}" y2="{base-6}" stroke="#718086" stroke-width="1"/>')
        parts.append(text(x+w/2,y+h/2-4,labels[op["id"]],11,weight=700,fill="#f7f4ec"))
        parts.append(text(x+w/2,y+h/2+16,f'{op["width"]:.2f} × {op["height"]:.2f} m',9,fill="#f7f4ec"))
    # Exterior platform, slot drain and lighting.
    parts.append(rect(left-45,base,width+90,42,fill="#d6d2ca",stroke="#858b89",stroke_width="1"))
    parts.append(f'<line x1="{left-25}" y1="{base+9}" x2="{left+width+25}" y2="{base+9}" stroke="#4d5b60" stroke-width="4" stroke-dasharray="7 4"/>')
    parts.append(text(left+width/2,base+32,"PLATAFORMA CONTINUA DE CONCRETO · canal lineal / pendiente alejándose de portones",9,weight=700))
    for x in (left+1.0*sc,left+8.0*sc,left+10.0*sc,left+17.0*sc):
        parts.append(f'<circle cx="{x}" cy="{top+58}" r="7" fill="#e5bd73" stroke="#594a32"/><path d="M {x-18} {top+85} L {x} {top+64} L {x+18} {top+85}" fill="#e7c985" opacity=".18"/>')
    # Horizontal dimensions, preserving the exact canonical composition.
    segments=[(0,1.2,"1,20"),(1.2,6.0,"4,80"),(6.0,8.2,"2,20"),(8.2,9.8,"1,60"),(9.8,12.0,"2,20"),(12.0,16.8,"4,80"),(16.8,18.0,"1,20")]
    dimy=base+100
    parts.append(f'<line x1="{left}" y1="{dimy}" x2="{left+width}" y2="{dimy}" stroke="#536166"/>')
    for a,b,label in segments:
        x1,x2=left+a*sc,left+b*sc
        parts.append(f'<line x1="{x1}" y1="{dimy-7}" x2="{x1}" y2="{dimy+7}" stroke="#536166"/>')
        parts.append(text((x1+x2)/2,dimy-9,label,8))
    parts.append(f'<line x1="{left+width}" y1="{dimy-7}" x2="{left+width}" y2="{dimy+7}" stroke="#536166"/>')
    parts.append(text(left+width/2,dimy+27,"18,00 m",11,weight=700))
    parts.append(rect(140,790,1116,62,fill="#fff4df",stroke="#bd5c3c"))
    parts.append(text(160,814,"LECTURA OBLIGATORIA",11,"start",700,"#8e3825"))
    parts.append(text(160,835,"Dos portones industriales iguales flanquean la puerta principal central. Dinteles, estructura, drenaje, sellos, motorización y panelización siguen pendientes de fabricante e ingeniería.",8,"start"))
    parts.append('</svg>')
    return ''.join(parts)


def rear_elevation_sheet(p):
    parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="900" viewBox="0 0 1400 900">',title_block("ELE-002-R04","FACHADA POSTERIOR · SERVICIOS Y NIVEL PRIVADO","Dos salidas PB + ventanas controladas de P2 · posición final sujeta a fachada, estructura y predio")]
    left, base, sc = 140, 645, 62
    width = 18*sc
    # El eje horizontal de esta lámina mapea Y=0 → izquierda, igual que la fachada frontal:
    # ambas derivan el perfil de cubierta de la misma fuente para no poder contradecirse.
    a_top, b_top, a_txt, b_txt = roof_profile(p, sc, base)
    parts.append('<defs><pattern id="metalr" width="16" height="16" patternUnits="userSpaceOnUse"><line x1="3" y1="0" x2="3" y2="16" stroke="#8e9799" stroke-width=".8"/></pattern></defs>')
    parts.append(f'<polygon points="{left},{base} {left},{a_top} {left+width},{b_top} {left+width},{base}" fill="#aeb5b6" stroke="#172126" stroke-width="4"/>')
    parts.append(f'<line x1="{left}" y1="{a_top}" x2="{left+width}" y2="{b_top}" stroke="#e7e9e7" stroke-width="4"/>')
    parts.append(text(left+10,a_top-12,a_txt,9,"start",700))
    parts.append(text(left+width-10,b_top-12,b_txt,9,"end",700))
    # Doors correspond to bodega and protected stair discharge.
    for d in p["exterior_doors"]:
        x=left+(d["y"]-.5)*sc
        w=d["width"]*sc
        h=(2.40 if d["id"]=="EXT-ESC" else 2.30)*sc
        y=base-h
        fill="#37454a" if d["id"]=="EXT-ESC" else "#59666a"
        parts.append(rect(x,y,w,h,fill=fill,stroke="#172126",stroke_width="2.5"))
        label="DESCARGA ESCALERA" if d["id"]=="EXT-ESC" else "SALIDA BODEGA"
        parts.append(text(x+w/2,y+h/2,label,8,weight=700,fill="#f5f3ed"))
    # P2 principal glazing is nearly floor-to-ceiling; wellness remains more contained.
    master=next(g for g in p["bedroom_glazing"] if g["facade"]=="REAR")
    rear_openings=[(master["from"],master["to"],master["name"].upper(),master["sill"],master["height"],True),(13.0,17.0,"WELLNESS",1.05,1.65,False)]
    for a,b,label,sill,opening_h,is_bedroom in rear_openings:
        x=left+a*sc; w=(b-a)*sc; h=opening_h*sc
        floor_y=base-3.8*sc
        y=floor_y-(sill+opening_h)*sc
        parts.append(rect(x,y,w,h,fill="#426671",stroke="#172126",stroke_width="2.2"))
        for m in range(1,max(1,int((b-a)/1.25))):
            xx=x+w*m/max(1,int((b-a)/1.25))
            parts.append(f'<line x1="{xx}" y1="{y}" x2="{xx}" y2="{y+h}" stroke="#88a2a8"/>')
        if is_bedroom:
            guard_y=floor_y-(sill+1.0)*sc
            parts.append(f'<line x1="{x}" y1="{guard_y}" x2="{x+w}" y2="{guard_y}" stroke="#d2e0e2" stroke-width="1.5"/>')
        parts.append(text(x+w/2,y+h/2+3,label+(" · PISO A TECHO" if is_bedroom else " · PROVISIONAL"),8,weight=700,fill="#eff5f5"))
    parts.append(f'<line x1="{left}" y1="{base-3.8*sc}" x2="{left+width}" y2="{base-3.8*sc}" stroke="#6f7a7d" stroke-width="1" stroke-dasharray="7 5"/>')
    parts.append(text(left+width-8,base-3.8*sc-8,"NIVEL P2 ≈ +3,80",8,"end",700,"#5c676b"))
    parts.append(rect(left-45,base,width+90,42,fill="#d6d2ca",stroke="#858b89"))
    parts.append(text(left+width/2,base+27,"FRANJA POSTERIOR DE SERVICIO · drenaje, acceso y paisaje por definir",9,weight=700))
    elevation_dims(parts,left,base,width,sc,18,"18,00 m")
    parts.append(note_box("Fachada contenida: los servicios permanecen opacos y el vidrio se concentra en espacios privados. Las ventanas son reservas; orientación, antepechos, control solar y estructura no están congelados."))
    parts.append('</svg>')
    return ''.join(parts)


def side_elevation_sheet(p,side):
    is_a=side=="A"
    meta = p.get("drawing_meta", {})
    code = meta.get("side_a_code" if is_a else "side_b_code", "ELE-003-R04" if is_a else "ELE-004-R04")
    title_value = meta.get(
        "side_a_title" if is_a else "side_b_title",
        f"FACHADA LATERAL {side} · NAVE DE 36 m",
    )
    subtitle = meta.get(
        "side_subtitle",
        "Evento principal de vidrio en sala + ventanas privadas provisionales"
        if is_a
        else "Fachada de control: taller/vida doméstica + ventanas privadas provisionales",
    )
    parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="900" viewBox="0 0 1400 900">',title_block(code,title_value,subtitle+" · orientación cardinal pendiente de predio")]
    left,base,sc=105,645,32.5
    # El alero de cada lateral sale de la fuente única de cubierta, no de un literal.
    is_low = p["roof"]["low_side"] == side
    eave = p["roof"]["low_eave"] if is_low else p["roof"]["high_eave"]
    length,height=36*sc,eave*sc
    top=base-height
    parts.append('<defs><pattern id="metals" width="14" height="14" patternUnits="userSpaceOnUse"><line x1="3" y1="0" x2="3" y2="14" stroke="#90999b" stroke-width=".7"/></pattern></defs>')
    parts.append(rect(left,top,length,height,fill="#aeb5b6",stroke="#172126",stroke_width="4"))
    parts.append(rect(left,top,length,height,fill="url(#metals)",stroke="none",opacity=".65"))
    parts.append(f'<line x1="{left}" y1="{top}" x2="{left+length}" y2="{top}" stroke="#e6e9e7" stroke-width="4"/>')
    parts.append(text(left+length-10,top-12,f'ALERO {"BAJO" if is_low else "ALTO"} ≈ {eave:.2f} m'+(" · TODA EL AGUA DE CUBIERTA DESCARGA AQUÍ" if is_low else ""),9,"end",700))
    p2x=left+21*sc
    p2y=base-3.8*sc
    parts.append(f'<line x1="{p2x}" y1="{top}" x2="{p2x}" y2="{base}" stroke="#687579" stroke-width="1.2" stroke-dasharray="7 5"/>')
    parts.append(f'<line x1="{p2x}" y1="{p2y}" x2="{left+length}" y2="{p2y}" stroke="#687579" stroke-width="1.2" stroke-dasharray="7 5"/>')
    parts.append(text(p2x+7.5*sc,p2y-9,"P2 POSTERIOR · 15,00 m",9,weight=700,fill="#59666a"))
    tech=next(g for g in p["technical_glazing"] if g["side"]==side)
    tx=left+tech["x0"]*sc
    tw=(tech["x1"]-tech["x0"])*sc
    th=tech["height"]*sc
    ty=base-(tech["sill"]+tech["height"])*sc
    parts.append(rect(tx,ty,tw,th,fill="#345e69",stroke="#172126",stroke_width="2.8"))
    for i in range(1,tech["modules"]):
        xx=tx+tw*i/tech["modules"]
        parts.append(f'<line x1="{xx}" y1="{ty}" x2="{xx}" y2="{ty+th}" stroke="#8eabb1" stroke-width="1.2"/>')
    transom=ty+th*.72
    parts.append(f'<line x1="{tx}" y1="{transom}" x2="{tx+tw}" y2="{transom}" stroke="#8eabb1" stroke-width="1.2"/>')
    for i in (1,4):
        ax=tx+tw*(i+.15)/tech["modules"]
        aw=tw*.7/tech["modules"]
        ah=th*.20
        parts.append(f'<path d="M {ax} {transom+4} L {ax+aw/2} {transom+ah} L {ax+aw} {transom+4}" fill="none" stroke="#d4e1e3" stroke-width="1.4"/>')
    parts.append(text(tx+tw/2,ty+th/2-4,tech["name"].upper(),9,weight=700,fill="#eff5f5"))
    parts.append(text(tx+tw/2,ty+th/2+15,f'{tech["x1"]-tech["x0"]:.2f} × {tech["height"]:.2f} m · antepecho {tech["sill"]:.2f} m',7,fill="#eff5f5"))
    # PB glazing: A carries the primary event; B remains a reversible alternative.
    gx=left+16.2*sc; gw=4.3*sc; gy=base-3.15*sc; gh=3.15*sc
    if is_a:
        parts.append(rect(gx,gy,gw,gh,fill="#416771",stroke="#172126",stroke_width="2.5"))
        for i in range(1,4):
            xx=gx+gw*i/4
            parts.append(f'<line x1="{xx}" y1="{gy}" x2="{xx}" y2="{base}" stroke="#8aa4a9"/>')
        parts.append(text(gx+gw/2,gy+gh/2,"EVENTO PRINCIPAL SALA",9,weight=700,fill="#eff5f5"))
    else:
        parts.append(rect(gx,gy,gw,gh,fill="none",stroke="#27859a",stroke_width="2",stroke_dasharray="9 5"))
        parts.append(text(gx+gw/2,gy+gh/2,"ALTERNATIVA SEGÚN PREDIO",8,weight=700,fill="#246b7a"))
    # Workstation opening and fixed worktop. Later revisions derive both from the
    # parametric pair so plan and elevations cannot diverge.
    if p.get("workstation_glazing"):
        workstation_window = next(
            item for item in p["workstation_glazing"] if item["side"] == side
        )
        workstation = next(item for item in p["workstations"] if item["side"] == side)
        wx = left + workstation_window["x0"] * sc
        ww = (workstation_window["x1"] - workstation_window["x0"]) * sc
        wh = workstation_window["height"] * sc
        wy = base - (workstation_window["sill"] + workstation_window["height"]) * sc
        parts.append(rect(wx,wy,ww,wh,fill="#4f7078",stroke="#172126",stroke_width="2.4"))
        for i in range(1, workstation_window.get("modules", 1)):
            xx = wx + ww * i / workstation_window["modules"]
            parts.append(
                f'<line x1="{xx}" y1="{wy}" x2="{xx}" y2="{wy+wh}" '
                'stroke="#9bb3b8" stroke-width="1.1"/>'
            )
        worktop_x = left + workstation["worktop_x0"] * sc
        worktop_w = workstation["worktop_length"] * sc
        worktop_y = base - workstation["worktop_height"] * sc
        rail_y = base - 0.68 * sc
        parts.append(
            f'<line x1="{worktop_x}" y1="{worktop_y}" '
            f'x2="{worktop_x+worktop_w}" y2="{worktop_y}" '
            'stroke="#c49a62" stroke-width="8"/>'
        )
        parts.append(
            f'<line x1="{worktop_x}" y1="{rail_y}" '
            f'x2="{worktop_x+worktop_w}" y2="{rail_y}" '
            'stroke="#26363b" stroke-width="4"/>'
        )
        for fraction in (0.12, 0.5, 0.88):
            px = worktop_x + worktop_w * fraction
            parts.append(
                f'<polyline points="{px-7},{rail_y} {px},{rail_y+12} {px+7},{rail_y}" '
                'fill="none" stroke="#26363b" stroke-width="2"/>'
            )
        cabinet_width = workstation.get("drawer_cabinet_width")
        cabinet_height = workstation.get("drawer_cabinet_height")
        if cabinet_width and cabinet_height:
            cabinet_top = worktop_y + 4
            cabinet_h = cabinet_height * sc
            cabinet_w = cabinet_width * sc
            for cabinet_x in (worktop_x, worktop_x + worktop_w - cabinet_w):
                parts.append(
                    rect(
                        cabinet_x,
                        cabinet_top,
                        cabinet_w,
                        cabinet_h,
                        fill="#8d6745",
                        stroke="#26363b",
                        stroke_width="1.2",
                    )
                )
                for drawer in range(1, workstation.get("drawer_levels", 3)):
                    drawer_y = cabinet_top + cabinet_h * drawer / workstation.get("drawer_levels", 3)
                    parts.append(
                        f'<line x1="{cabinet_x}" y1="{drawer_y}" '
                        f'x2="{cabinet_x+cabinet_w}" y2="{drawer_y}" '
                        'stroke="#d6c1a5" stroke-width=".8"/>'
                    )
        parts.append(
            text(
                wx + ww / 2,
                wy + wh / 2 - 2,
                workstation_window["name"].upper(),
                7.5,
                weight=700,
                fill="#eff5f5",
            )
        )
        parts.append(
            text(
                wx + ww / 2,
                wy + wh / 2 + 14,
                f'{workstation_window["x1"] - workstation_window["x0"]:.2f} × '
                f'{workstation_window["height"]:.2f} m · sill {workstation_window["sill"]:.2f} m',
                6.5,
                fill="#eff5f5",
            )
        )
        parts.append(
            text(
                worktop_x + worktop_w / 2,
                worktop_y - 9,
                "INTEGRATED STEEL / TIMBER WORKTOP",
                5.6,
                weight=700,
                fill="#5c4229",
            )
        )
        if is_a:
            junction_x = left + workstation_window["x1"] * sc
            junction_w = (16.2 - workstation_window["x1"]) * sc
            parts.append(
                rect(
                    junction_x,
                    base - 3.15 * sc,
                    junction_w,
                    3.15 * sc,
                    fill="#c69755",
                    stroke="#7d542b",
                    stroke_width="1",
                    opacity=".78",
                )
            )
            parts.append(
                text(
                    junction_x + junction_w / 2,
                    base - 3.15 * sc - 10,
                    "0.20 m MULLION / TRIMMER HOLD",
                    5.8,
                    weight=700,
                    fill="#8e3825",
                )
            )
    else:
        wx=left+13.0*sc; wy=base-2.35*sc; ww=3.0*sc; wh=1.65*sc
        parts.append(rect(wx,wy,ww,wh,fill="#4f7078",stroke="#172126",stroke_width="2"))
        parts.append(text(wx+ww/2,wy+wh/2+3,"TRABAJO "+("1" if is_a else "2"),7,weight=700,fill="#eff5f5"))
    # P2 bedroom windows differ by side but retain few, repeated openings.
    wins=[g for g in p["bedroom_glazing"] if g["facade"]==side]
    for g in wins:
        a,b,label=g["from"],g["to"],g["name"].upper()
        x=left+a*sc; w=(b-a)*sc; h=g["height"]*sc
        floor_y=base-3.8*sc
        y=floor_y-(g["sill"]+g["height"])*sc
        parts.append(rect(x,y,w,h,fill="#426671",stroke="#172126",stroke_width="2"))
        guard_y=floor_y-(g["sill"]+1.0)*sc
        parts.append(f'<line x1="{x}" y1="{guard_y}" x2="{x+w}" y2="{guard_y}" stroke="#d2e0e2" stroke-width="1.4"/>')
        parts.append(text(x+w/2,y+h/2+3,label+" · PISO A TECHO",7,weight=700,fill="#eff5f5"))
    # Downpipes as coordinated vertical elements, not final positions.
    for mx in (10.5,21.0,31.5):
        x=left+mx*sc
        parts.append(f'<line x1="{x}" y1="{top+15}" x2="{x}" y2="{base}" stroke="#536166" stroke-width="3"/>')
        parts.append(f'<rect x="{x-5}" y="{base-18}" width="10" height="18" fill="#536166"/>')
    parts.append(rect(left-25,base,length+50,38,fill="#d6d2ca",stroke="#858b89"))
    parts.append(text(left+length/2,base+25,"COTA EXTERIOR / DRENAJE PERIMETRAL PENDIENTE DE TOPOGRAFÍA",8,weight=700))
    # Band dimensions 10.5 + 10.5 + 10.5 + 4.5.
    dimy=base+90
    parts.append(f'<line x1="{left}" y1="{dimy}" x2="{left+length}" y2="{dimy}" stroke="#536166"/>')
    bounds=(0,10.5,21,31.5,36)
    labels=("10,50 técnica","10,50 monumental","10,50 doméstica","4,50 núcleo")
    for i,b in enumerate(bounds):
        x=left+b*sc
        parts.append(f'<line x1="{x}" y1="{dimy-7}" x2="{x}" y2="{dimy+7}" stroke="#536166"/>')
        if i<len(labels):
            parts.append(text(left+(b+bounds[i+1])/2*sc,dimy-9,labels[i],8))
    parts.append(text(left+length/2,dimy+27,"36,00 m",11,weight=700))
    parts.append(note_box("La posición de vidrio, ventanas, bajantes y panelización es una hipótesis coordinable. No adoptar orientación cardinal, protección solar ni huecos definitivos antes de seleccionar el predio."))
    parts.append('</svg>')
    return ''.join(parts)


def elevation_dims(parts,left,base,width,sc,total,label):
    dimy=base+100
    parts.append(f'<line x1="{left}" y1="{dimy}" x2="{left+width}" y2="{dimy}" stroke="#536166"/>')
    parts.append(f'<line x1="{left}" y1="{dimy-7}" x2="{left}" y2="{dimy+7}" stroke="#536166"/><line x1="{left+width}" y1="{dimy-7}" x2="{left+width}" y2="{dimy+7}" stroke="#536166"/>')
    parts.append(text(left+width/2,dimy-9,label,10,weight=700))


def note_box(message):
    return rect(140,790,1116,62,fill="#fff4df",stroke="#bd5c3c")+text(160,814,"NOTA DE COORDINACIÓN",11,"start",700,"#8e3825")+text(160,836,message,8,"start")


def core_sheet(p):
    parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="900" viewBox="0 0 1400 900">',title_block("DET-001-R04","DETALLE AMPLIADO · NÚCLEO POSTERIOR PB","Planta de coordinación 1:50 conceptual · áreas netas provisionales con cerramientos de estudio")]
    x0,y0,sc=300,115,36
    depth=4.5
    parts.append('<defs><pattern id="wood2" width="8" height="8" patternUnits="userSpaceOnUse"><line x1="2" y1="0" x2="2" y2="8" stroke="#8d6747"/></pattern></defs>')
    colors={"service":"#ded5ba","storage":"#ccd3cb","stair":"#d3c5b8","wet":"#bdd6d3","technical":"#c2d0cb"}
    clear_depth=p["design_values"]["core_depth_clear"]
    ext=p["envelope"]["exterior_wall"]
    for room in p["core"]:
        yy=y0+room["y0"]*sc
        hh=(room["y1"]-room["y0"])*sc
        parts.append(rect(x0,yy,depth*sc,hh,fill=colors[room["type"]],stroke="#435158",stroke_width="1.2"))
        ny0,ny1=core_net_y(room,p)
        net_width=max(0,ny1-ny0)
        net_area=clear_depth*net_width
        parts.append(text(x0+depth*sc/2,yy+hh/2-5,room["name"],10,weight=700))
        parts.append(text(x0+depth*sc/2,yy+hh/2+12,f"≈ {net_area:.1f} m² netos provisionales",8,fill="#4f5e63"))
    parts.append(rect(x0,y0,.20*sc,18*sc,fill="url(#wood2)",stroke="#6c4b32",stroke_width="1.4"))
    parts.append(rect(x0+(depth-ext)*sc,y0,ext*sc,18*sc,fill="#59666b",stroke="#263238",stroke_width="1"))
    for boundary in (2.4,7.4,11.0,13.4):
        th=.20 if boundary in (7.4,11.0) else .15
        parts.append(rect(x0+.2*sc,y0+(boundary-th/2)*sc,(depth-.2-ext)*sc,th*sc,fill="#58666b",stroke="none"))
    # Enlarged equipment callouts.
    parts.append(rect(x0+1.0*sc,y0+.35*sc,1.0*sc,1.45*sc,fill="#ece5d0",stroke="#5d645d"))
    parts.append(text(x0+1.5*sc,y0+1.1*sc,"frío",7,weight=700))
    parts.append(rect(x0+2.55*sc,y0+.35*sc,1.25*sc,1.45*sc,fill="#ece5d0",stroke="#5d645d"))
    parts.append(text(x0+3.175*sc,y0+1.1*sc,"limpieza",7,weight=700))
    parts.append(stair_detail(x0,y0,sc))
    parts.append(rect(x0+.55*sc,y0+11.30*sc,1.2*sc,1.1*sc,fill="none",stroke="#27859a",stroke_width="1.2"))
    parts.append(f'<ellipse cx="{x0+3.75*sc}" cy="{y0+12.05*sc}" rx="11" ry="15" fill="#fff" stroke="#59686d"/>')
    parts.append(rect(x0+2.15*sc,y0+12.55*sc,1.05*sc,.45*sc,fill="#fff",stroke="#59686d"))
    parts.append(rect(x0+.55*sc,y0+13.85*sc,1.05*sc,.8*sc,fill="#424f54",stroke="#263238"))
    parts.append(text(x0+1.075*sc,y0+14.3*sc,"rack",7,weight=700,fill="#fff"))
    parts.append(rect(x0+2.5*sc,y0+13.85*sc,1.25*sc,1.7*sc,fill="#e2e7e4",stroke="#59686d"))
    parts.append(text(x0+3.125*sc,y0+14.7*sc,"UPS / tableros",6,weight=700))
    # Doors and rear exits.
    for room in p["core"]:
        yy=y0+(room["door_y"]-.45)*sc
        parts.append(f'<line x1="{x0}" y1="{yy}" x2="{x0}" y2="{yy+room["door_width"]*sc}" stroke="#9d4a2f" stroke-width="5"/>')
    for d in p["exterior_doors"]:
        yy=y0+(d["y"]-.5)*sc
        parts.append(f'<line x1="{x0+depth*sc}" y1="{yy}" x2="{x0+depth*sc}" y2="{yy+d["width"]*sc}" stroke="#236a45" stroke-width="6"/>')
    # Notes panel.
    nx=570
    parts.append(text(nx,130,"CAPAS DE ESTUDIO",14,"start",700,"#6c452e"))
    notes=[
        "Gran muro: 0,20 m total conceptual; subestructura, absorbente y acabado listonado registrable.",
        "Particiones estándar: 0,15 m con desempeño acústico por definir.",
        "Escalera: cerramientos de 0,20 m y descarga posterior; resistencia al fuego pendiente.",
        "Envolvente posterior: 0,18 m conceptual de panel aislado; puentes térmicos y reacción al fuego pendientes.",
        "Profundidad libre resultante del núcleo: ≈4,12 m antes de trasdosados/equipos.",
        "No mezclar drenajes ni agua sobre rack/UPS; coordinar bandejas, detección, ventilación y acceso posterior.",
        "Bodega y homelab quedan separados por escalera y baño; pantry queda contiguo a cocina.",
        "Todas las áreas netas son aproximadas y se recalculan después de estructura y especificaciones."
    ]
    for i,n in enumerate(notes):
        parts.append(rect(nx,155+i*63,720,48,fill="#f5f2ea",stroke="#c7c3b9",stroke_width=".7"))
        parts.append(text(nx+15,176+i*63,f"{i+1:02d}",10,"start",700,"#9b4e32"))
        parts.append(text(nx+52,176+i*63,n,8,"start"))
    parts.append(rect(nx,690,720,125,fill="#fff4df",stroke="#bd5c3c"))
    parts.append(text(nx+18,718,"COORDINACIONES BLOQUEANTES",12,"start",700,"#8e3825"))
    blocks=["huella/contrahuella/gálibo y puertas de escalera", "extracción y aire de reposición del baño/homelab", "rutas hidráulicas y sanitarias hacia P2", "protección contra incendio y segunda salida", "equipos reales, registros y radios de mantenimiento"]
    for i,b in enumerate(blocks):
        parts.append(text(nx+22,742+i*15,"• "+b,8,"start",700 if i==3 else 400,"#8e3825" if i==3 else "#3f4c51"))
    parts.append('</svg>')
    return ''.join(parts)


def stair_detail(x0,y0,sc):
    x=x0+.35*sc; y=y0+7.62*sc; w=3.8*sc; h=3.0*sc
    pieces=[rect(x,y,w,h,fill="#efeae3",stroke="#46545a")]
    for i in range(1,11):
        yy=y+i*h/11
        pieces.append(f'<line x1="{x}" y1="{yy}" x2="{x+w*.38}" y2="{yy}" stroke="#657379"/><line x1="{x+w*.62}" y1="{yy}" x2="{x+w}" y2="{yy}" stroke="#657379"/>')
    pieces.append(text(x+w/2,y+h/2,"U · 21 contrahuellas aprox.",7,weight=700))
    return ''.join(pieces)


def validate(p):
    core=p["core"]
    checks=[]
    checks.append(("PB-ENV",p["envelope"]["length"]==36 and p["envelope"]["width"]==18,"Envolvente nominal 18 × 36 m"))
    checks.append(("PB-FRONT",len(p["front_openings"])==3,"Exactamente tres accesos frontales"))
    checks.append(("PB-CORE-SUM",abs(sum(r["gross_area"] for r in core)-81)<1e-6,"Núcleo conserva 81,00 m² brutos"))
    checks.append(("PB-CORE-COVER",abs(core[0]["y0"])<1e-6 and abs(core[-1]["y1"]-18)<1e-6 and all(abs(a["y1"]-b["y0"])<1e-6 for a,b in pairwise(core)),"Núcleo cubre los 18,00 m sin vacíos"))
    # Cierre de áreas del núcleo: lo dibujado debe sumar 18,00 m con los espesores declarados.
    ext=p["envelope"]["exterior_wall"]; dv=p["design_values"]
    nets=[core_net_y(r,p) for r in core]
    net_sum=sum(b-a for a,b in nets)
    gap_sum=sum(nets[i+1][0]-nets[i][1] for i in range(len(nets)-1))
    wrong=[]
    for i,(a,b) in enumerate(pairwise(core)):
        want=dv["partition_stair"] if abs(a["y1"]-7.4)<1e-9 or abs(a["y1"]-11.0)<1e-9 else dv["partition_standard"]
        got=nets[i+1][0]-nets[i][1]
        if abs(got-want)>1e-6: wrong.append(f'{a["id"]}|{b["id"]} {got:.3f} m ≠ {want:.2f} m declarados')
    checks.append(("PB-CORE-CLOSURE",abs(net_sum+gap_sum+2*ext-18.0)<1e-6 and not wrong,
        f"Núcleo: {net_sum:.2f} m netos + {gap_sum:.2f} m de tabiques + 2×{ext:.2f} m de envolvente = 18,00 m"+("" if not wrong else " · TABIQUES INCORRECTOS: "+" · ".join(wrong))))
    checks.append(("PB-GREAT-WALL",p["great_wall"]["x"]==31.5 and p["great_wall"]["thickness"]>=.20,"Gran muro continuo en X=31,50 m con espesor conceptual 0,20 m"))
    checks.append(("PB-CORE-DOORS",len(core)==5 and all(r["door_width"]>=.9 for r in core),"Cinco accesos del núcleo de mínimo 0,90 m"))
    ids={d["id"] for d in p["exterior_doors"]}
    checks.append(("PB-REAR-EXITS",{"EXT-BOD","EXT-ESC"}.issubset(ids),"Bodega y escalera conservan salidas posteriores"))
    k=p["kitchen"]
    clearance=k["island"]["y"]-(k["wall_run"]["y"]+k["wall_run"]["depth"])
    checks.append(("PB-KITCHEN-CLEAR",clearance>=k["operating_clearance"]-1e-6,f"Paso operativo cocina = {clearance:.2f} m"))
    checks.append(("PB-PANTRY-ADJ",core[0]["id"]=="PAN","Pantry se ubica junto al frente de cocina"))
    checks.append(("PB-STAIR-ALIGN",next(r for r in core if r["id"]=="ESC")["y0"]==7.4,"Escalera conserva alineación Y=7,40–11,00 m con P2"))
    glazing=p["technical_glazing"]
    checks.append(("PB-TECH-GLAZING",len(glazing)==2 and all(g["x1"]-g["x0"]>=6.0 and g["height"]>=2.5 for g in glazing),"Dos ventanales técnicos grandes, modulados y equivalentes"))
    bedrooms=p["bedroom_glazing"]
    required={"GLZ-H1","GLZ-H2","GLZ-G","GLZ-M-R"}
    checks.append(("P2-BEDROOM-GLAZING",required.issubset({g["id"] for g in bedrooms}) and all(g["height"]>=2.65 and g["sill"]<=.10 for g in bedrooms),"Cuatro dormitorios representan vidrio casi piso a techo"))
    # Los vanos de dormitorio se dibujan en dos emisiones distintas (elevaciones aquí,
    # planta P2 activa) y deben describir la misma ventana. Sin este cruce, b05 y P2
    # llegaron a poner el paño dominante en fachadas opuestas (hallazgo H-06).
    edge_of={"A":"south","B":"north","REAR":"east"}
    pair={"GLZ-H1":"W-H1","GLZ-H2":"W-H2","GLZ-G":"W-G","GLZ-M-A":"W-M-LAT-A","GLZ-M-R":"W-M-REAR"}
    room_of={"GLZ-H1":"H1-D","GLZ-H2":"H2-D","GLZ-G":"G-D","GLZ-M-A":"M-D","GLZ-M-R":"M-D"}
    try:
        p2=json.loads(DATA.with_name("p2_b10.json").read_text(encoding="utf-8"))
    except OSError:
        p2=None
    if p2 is None:
        checks.append(("PB-P2-WINDOW-SYNC",False,"No se pudo leer p2_b10.json para el chequeo cruzado"))
        checks.append(("PB-GLAZING-IN-ROOM",False,"No se pudo leer p2_b10.json para verificar contención"))
    else:
        w2={w["id"]:w for w in p2["windows"]}; sp2={z["id"]:z for z in p2["spaces"]}
        diffs=[]
        for g in bedrooms:
            o=w2.get(pair.get(g["id"],""))
            if o is None:
                diffs.append(f'{g["id"]} sin pareja en b10'); continue
            if o["edge"]!=edge_of[g["facade"]] or abs(o["from"]-g["from"])>1e-6 or abs(o["to"]-g["to"])>1e-6 or abs(o["height"]-g["height"])>1e-6:
                diffs.append(f'{g["id"]} ({g["facade"]} {g["from"]}–{g["to"]}) ≠ {o["id"]} ({o["edge"]} {o["from"]}–{o["to"]})')
        checks.append(("PB-P2-WINDOW-SYNC",not diffs,"Vanos de dormitorio idénticos en pb_b05.json y p2_b10.json" if not diffs else "DIVERGENCIA b05↔b10: "+" · ".join(diffs)))
        # Un vano no puede desbordar el muro del recinto que ilumina: el paño posterior
        # de 5,50 m metía 2,30 m de vidrio piso-techo dentro del vestidor principal.
        bad=[]
        for g in bedrooms:
            z=sp2.get(room_of.get(g["id"],""))
            if not z: continue
            lo,hi=(z["y"],z["y"]+z["d"]) if g["facade"]=="REAR" else (z["x"],z["x"]+z["w"])
            if g["from"]<lo-1e-6 or g["to"]>hi+1e-6:
                bad.append(f'{g["id"]} {g["from"]}–{g["to"]} desborda {z["id"]} {lo}–{hi}')
        checks.append(("PB-GLAZING-IN-ROOM",not bad,"Cada vano cae dentro del muro de su dormitorio" if not bad else "Vano fuera de recinto: "+" · ".join(bad)))
    return [{"rule_id":rid,"status":"PASS" if ok else "FAIL","message":msg} for rid,ok,msg in checks]


def main():
    p=json.loads(DATA.read_text(encoding="utf-8"))
    checks=validate(p)
    OUT.mkdir(parents=True,exist_ok=True)
    outputs={
        "DH-ARQ-PLN-001-R04_PB-DETALLADA.svg":plan_sheet(p),
        "DH-ARQ-ELE-001-R04_FACHADA-FRONTAL.svg":front_elevation_sheet(p),
        "DH-ARQ-ELE-002-R04_FACHADA-POSTERIOR.svg":rear_elevation_sheet(p),
        "DH-ARQ-ELE-003-R04_FACHADA-LATERAL-A.svg":side_elevation_sheet(p,"A"),
        "DH-ARQ-ELE-004-R04_FACHADA-LATERAL-B.svg":side_elevation_sheet(p,"B"),
        "DH-ARQ-ELE-INT-001-R04_GRAN-MURO.svg":wall_elevation_sheet(p),
        "DH-ARQ-DET-001-R04_NUCLEO-PB.svg":core_sheet(p)
    }
    for name,content in outputs.items():
        OUT.joinpath(name).write_text(content,encoding="utf-8")
    report={"revision":p["revision"],"checks":checks,"passed":sum(c["status"]=="PASS" for c in checks),"failed":sum(c["status"]=="FAIL" for c in checks)}
    OUT.joinpath("compliance.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    manifest={"input":"dreamhouse/pb_b05.json","input_sha256":hashlib.sha256(DATA.read_bytes()).hexdigest(),"generator":"dreamhouse/generate_pb_b05.py","revision":p["revision"],"outputs":list(outputs)+["compliance.json","manifest.json"]}
    OUT.joinpath("manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"passed":report["passed"],"failed":report["failed"]}))
    if report["failed"]:
        raise SystemExit(1)


if __name__=="__main__":
    main()
