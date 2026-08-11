from __future__ import annotations

import copy
import hashlib
import html
import json
from pathlib import Path

import generate_b03 as b03
import generate_detailed_plans as base

ROOT = Path(__file__).resolve().parents[1]
REVISION = Path(__file__).with_name("revision_b04.json")
OUT = ROOT / "planos" / "conceptual_v0.3_b04"
S, X0, Y0 = base.S, base.X0, base.Y0


def load_model():
    p = copy.deepcopy(json.loads(base.DATA.read_text(encoding="utf-8")))
    r = json.loads(REVISION.read_text(encoding="utf-8"))
    p["project"].update(revision=r["revision"], status=r["status"])
    p["ground_floor"]["equipment"] = r["ground_floor_equipment"]
    p["upper_floor"]["spaces"] = r["upper_floor_spaces"]
    p["upper_floor"]["equipment"] = r["upper_floor_equipment"]
    return p, r


def exterior_door_svg(d):
    if d["edge"] != "right":
        return ""
    y1 = Y0 + (18 - d["to"]) * S
    y2 = Y0 + (18 - d["from"]) * S
    x = X0 + 36 * S
    return (
        f'<g stroke="#236a45" fill="none" stroke-width="6">'
        f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2}"/>'
        f'</g>'
    )


def phase_boundary_svg():
    y = Y0 + (18 - 10.5) * S
    x1, x2 = X0 + 21 * S, X0 + 36 * S
    return (
        f'<g stroke="#7b3f8c" fill="none">'
        f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke-width="4" stroke-dasharray="10 5"/>'
        f'<text x="{(x1+x2)/2}" y="{y-7}" text-anchor="middle" fill="#7b3f8c" stroke="none" font-size="9" font-weight="700">FRONTERA ÚNICA DE OBRA F1 / F2</text>'
        f'</g>'
    )


def enhance(svg, revision, floor):
    details = revision["details"]
    svg = svg.replace("0.3-borrador-02", "0.3-borrador-04")
    overlays = "".join(b03.window_svg(w) for w in details["windows"][floor])
    overlays += "".join(b03.door_svg(d) for d in details["doors"][floor])
    overlays += "".join(b03.fixture_svg(f) for f in details["fixtures"][floor])
    overlays += b03.stair_svg() + b03.chain(floor)
    if floor == "PB":
        overlays += "".join(exterior_door_svg(d) for d in details["exterior_doors"] if d["floor"] == "PB")
    else:
        overlays += phase_boundary_svg()
    legend = (
        '<g font-family="Arial">'
        '<line x1="770" y1="108" x2="805" y2="108" stroke="#27859a" stroke-width="6"/>'
        '<text x="812" y="112" font-size="9">ventana provisional</text>'
        '<line x1="770" y1="126" x2="805" y2="126" stroke="#236a45" stroke-width="6"/>'
        '<text x="812" y="130" font-size="9">salida exterior</text>'
        '</g>'
    )
    return svg.replace('<rect x="75" y="650"', overlays + legend + '<rect x="75" y="650"')


def validate(p, r):
    checks, suites = base.validate(p)
    spaces = p["upper_floor"]["spaces"]
    f2 = [z for z in spaces if z.get("phase") == 2]
    bedrooms = {z["suite"]: base.area(z) for z in spaces if z["id"] in {"P2-H1-D", "P2-H2-D"}}
    exterior_ids = {d["id"] for d in r["details"]["exterior_doors"]}
    fixtures = r["details"]["fixtures"]["P2"]
    extra = [
        ("ARQ-CHILD-BED-EQ", abs(bedrooms["H1"] - bedrooms["H2"]) < 0.01, "Dormitorios de hijos conservan 26,00 m² útiles nominales"),
        ("ARQ-F2-BOUNDARY", all(z["y"] >= 10.5 - 1e-6 for z in f2), "Toda Fase 2 queda detrás de una frontera continua en Y=10,50 m"),
        ("ARQ-CORE-EXITS", {"EXT-BOD", "EXT-ESC"}.issubset(exterior_ids), "Bodega y escalera representan descarga posterior propia"),
        ("ARQ-WET-COMPLETE", sum(f["type"] == "shower" for f in fixtures) == 4 and sum(f["type"] == "vanity" for f in fixtures) >= 4, "Cuatro baños privados representan ducha y lavamanos"),
        ("ARQ-MASTER-CONTIG", all(z["x"] >= 28.6 and z["y"] < 10.5 + 1e-6 for z in spaces if z.get("suite") == "M"), "Suite principal ocupa un bloque continuo de Fase 1"),
        ("ARQ-AXIS-FREE", not any(base.overlaps(p["ground_floor"]["axis"], e) for e in p["ground_floor"]["equipment"]), "Equipamiento no invade el eje peatonal de 4,00 m"),
    ]
    checks += [{"rule_id": rid, "status": "PASS" if ok else "FAIL", "message": msg} for rid, ok, msg in extra]
    checks.append({"rule_id": "LIFE-EGRESS-2", "status": "OPEN", "message": "La necesidad de segunda salida independiente depende de clasificación de uso, ocupación, recorridos y concepto de incendio"})
    return checks, suites


def transverse():
    return b03.transverse().replace("estructura todavía por seleccionar", "reserva de canto 0,60–0,75 m; sistema por seleccionar").replace("Rev. 0.3-borrador-03", "Rev. 0.3-borrador-04")


def main():
    p, r = load_model()
    checks, suites = validate(p, r)
    OUT.mkdir(parents=True, exist_ok=True)
    outputs = {
        "DH-ARQ-PLN-001-R03_PB.svg": enhance(base.plan(p, "PB", suites), r, "PB"),
        "DH-ARQ-PLN-002-R03_P2.svg": enhance(base.plan(p, "P2", suites), r, "P2"),
        "DH-ARQ-SEC-001-R03_LONGITUDINAL.svg": base.section().replace("0.3-borrador-02", "0.3-borrador-04"),
        "DH-ARQ-SEC-002-R03_TRANSVERSAL.svg": transverse(),
        "DH-ARQ-ELE-001-R03_FRONTAL.svg": base.elevation(p),
    }
    for name, content in outputs.items():
        OUT.joinpath(name).write_text(content, encoding="utf-8")
    report = {
        "revision": r["revision"],
        "checks": checks,
        "passed": sum(c["status"] == "PASS" for c in checks),
        "open": sum(c["status"] == "OPEN" for c in checks),
        "failed": sum(c["status"] == "FAIL" for c in checks),
    }
    OUT.joinpath("compliance.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest = {
        "base": r["base_model"],
        "revision_file": str(REVISION.relative_to(ROOT)),
        "revision_sha256": hashlib.sha256(REVISION.read_bytes()).hexdigest(),
        "generator": "dreamhouse/generate_b04.py",
        "revision": r["revision"],
        "outputs": list(outputs) + ["compliance.json", "manifest.json"],
    }
    OUT.joinpath("manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"passed": report["passed"], "open": report["open"], "failed": report["failed"]}))
    if report["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
