from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(__file__).with_name("project_b02.json")
OUT = ROOT / "planos" / "conceptual_v0.3_b02"
S = 24.0
X0, Y0 = 75, 145
PW, PH = 36*S, 18*S

COLORS = {"technical":"#cedae0","buffer":"#f4f0e8","social":"#ddcbbb","work":"#c8d9d2",
"domestic":"#e0cbb2","service":"#c1cbc4","vertical":"#cbbdb0","bedroom":"#ded0c5",
"closet":"#c9b8a9","bath":"#b9d3d0","master":"#c5ab98","wellness":"#b8d4ce",
"shared":"#d8d1b8","circulation":"#f3e6b7"}

def area(o): return o["w"]*o["d"]
def xy(o): return X0+o["x"]*S, Y0+(18-o["y"]-o["d"])*S, o["w"]*S, o["d"]*S

def overlaps(a,b):
    return min(a["x"]+a["w"],b["x"]+b["w"])-max(a["x"],b["x"])>1e-6 and min(a["y"]+a["d"],b["y"]+b["d"])-max(a["y"],b["y"])>1e-6

def validate(p):
    p2=[z for z in p["upper_floor"]["spaces"] if area(z)>0]
    suite_areas={k:sum(area(z) for z in p2 if z.get("suite")==k) for k in ("H1","H2","G","M")}
    core=[z for z in p["ground_floor"]["spaces"] if z["id"] in {"PB-BOD","PB-BAN","PB-ESC","PB-HOM","PB-PAN"}]
    checks=[
      ("HR-P2-BOUND",all(z["x"]>=21 and z["y"]>=0 and z["x"]+z["w"]<=36 and z["y"]+z["d"]<=18 for z in p2),"Espacios P2 dentro de su envolvente"),
      ("HR-P2-TOPO",not any(overlaps(a,b) for i,a in enumerate(p2) for b in p2[i+1:]),"Espacios P2 sin solapes"),
      ("HR-4-SUITES",len([v for v in suite_areas.values() if v>0])==4,"Cuatro suites identificadas"),
      ("HR-CHILD-EQ",abs(suite_areas["H1"]-suite_areas["H2"])<1e-6,"Suites de hijos iguales"),
      ("HR-CHILD-AREA",abs(suite_areas["H1"]-38)<1e-6,"Cada suite de hijo reserva 38,00 m²"),
      ("DCV-GUEST",abs(suite_areas["G"]-33)<1e-6,"Suite huéspedes reserva 33,00 m²"),
      ("DCV-MASTER",72<=suite_areas["M"]<=80,f'Suite principal reserva {suite_areas["M"]:.2f} m²'),
      ("DCV-CORE",abs(sum(area(z) for z in core)-81)<1e-6,"Núcleo PB conserva 81,00 m²"),
      ("HR-DOORS",len(p["ground_floor"]["front_openings"])==3,"Tres accesos frontales")]
    return [{"rule_id":r,"status":"PASS" if ok else "FAIL","message":m} for r,ok,m in checks],suite_areas

def space_svg(z):
    x,y,w,h=xy(z); phase=z.get("phase"); dash=' stroke-dasharray="7 4"' if phase==2 else ''
    label=html.escape(z["name"]); meta=f'{area(z):.1f} m²'+(f' · F{phase}' if phase else '')
    if h<27 or w<55: label=html.escape(z["id"]); meta=""
    fs=12 if min(w,h)>65 else 9
    return f'<g><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{COLORS.get(z["kind"],"#ddd")}" stroke="#263238" stroke-width="1.3"{dash}/><text x="{x+w/2}" y="{y+h/2-3}" text-anchor="middle" font-size="{fs}" font-weight="600">{label}</text><text x="{x+w/2}" y="{y+h/2+12}" text-anchor="middle" font-size="8">{meta}</text></g>'

def equipment_svg(e):
    x,y,w,h=xy(e); label=html.escape(e["name"])
    extra=""
    if e["symbol"]=="car":
        extra=f'<ellipse cx="{x+w*.18}" cy="{y+h}" rx="10" ry="4"/><ellipse cx="{x+w*.82}" cy="{y+h}" rx="10" ry="4"/>'
    if e["symbol"]=="bed": extra=f'<rect x="{x+4}" y="{y+4}" width="{w-8}" height="{h*.25}" fill="#fff"/>'
    return f'<g fill="none" stroke="#59666c" stroke-width="1.2"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{5 if e["symbol"] in ("car","sofa") else 0}"/>{extra}<text x="{x+w/2}" y="{y+h/2+3}" text-anchor="middle" fill="#364247" stroke="none" font-size="8">{label}</text></g>'

def dims():
    return f'<g stroke="#566269" fill="none" stroke-width="1"><line x1="{X0}" y1="{Y0+PH+35}" x2="{X0+PW}" y2="{Y0+PH+35}"/><text x="{X0+PW/2}" y="{Y0+PH+29}" fill="#263238" stroke="none" text-anchor="middle" font-size="11">36,00 m</text><line x1="{X0-32}" y1="{Y0}" x2="{X0-32}" y2="{Y0+PH}"/><text x="{X0-43}" y="{Y0+PH/2}" fill="#263238" stroke="none" text-anchor="middle" font-size="11" transform="rotate(-90 {X0-43} {Y0+PH/2})">18,00 m</text></g>'

def plan(p,floor,suite_areas):
    ispb=floor=="PB"; spaces=p["ground_floor"]["spaces"] if ispb else p["upper_floor"]["spaces"]
    equipment=p["ground_floor"]["equipment"] if ispb else p["upper_floor"]["equipment"]
    title="PLANTA BAJA · ANTEPROYECTO" if ispb else "PLANTA SEGUNDO PISO · ANTEPROYECTO"
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="760" viewBox="0 0 1120 760"><rect width="1120" height="760" fill="#fbfaf7"/><g font-family="Arial" fill="#20292e"><text x="75" y="46" font-size="25" font-weight="700">{title}</text><text x="75" y="73" font-size="13" fill="#566269">Rev. 0.3-borrador-02 · hipótesis · 2026-08-11 · cotas en metros</text>']
    if not ispb:
      parts += [f'<rect x="{X0}" y="{Y0}" width="{21*S}" height="{PH}" fill="#eeebe4" stroke="#8b9294" stroke-dasharray="6 5"/><text x="{X0+10.5*S}" y="{Y0+PH/2}" text-anchor="middle" font-size="18" fill="#98938b">VACÍO DOBLE ALTURA · 378 m²</text>']
    parts += [space_svg(z) for z in spaces if area(z)>0]
    if ispb:
      a=p["ground_floor"]["axis"]; x,y,w,h=xy(a)
      parts += [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="#b8841e" stroke-width="2" stroke-dasharray="8 5"/><rect x="{X0+10.6*S}" y="{y+h/2-11}" width="190" height="19" fill="#fbfaf7"/><text x="{X0+10.6*S+7}" y="{y+h/2+3}" font-size="10" font-weight="700" fill="#8a6518">EJE PEATONAL LIBRE · 4,00 m</text>']
      for op in p["ground_floor"]["front_openings"]:
        yy=Y0+(18-op["y0"]-op["width"])*S
        parts += [f'<line x1="{X0}" y1="{yy}" x2="{X0}" y2="{yy+op["width"]*S}" stroke="#b95336" stroke-width="7"/>']
    parts += [equipment_svg(e) for e in equipment]
    parts += [f'<rect x="{X0}" y="{Y0}" width="{PW}" height="{PH}" fill="none" stroke="#172126" stroke-width="3"/>']
    for gx in (0,6,12,18,24,30,36):
      xx=X0+gx*S; parts += [f'<line x1="{xx}" y1="{Y0-15}" x2="{xx}" y2="{Y0+PH+15}" stroke="#9ba1a2" stroke-width=".6" stroke-dasharray="3 5"/><circle cx="{xx}" cy="{Y0-27}" r="10" fill="#fbfaf7" stroke="#566269"/><text x="{xx}" y="{Y0-23}" text-anchor="middle" font-size="9">{chr(65+gx//6)}</text>']
    parts += [dims()]
    if not ispb:
      parts += [f'<text x="75" y="620" font-size="11">Áreas de suite: hijos {suite_areas["H1"]:.1f} m² c/u · huéspedes {suite_areas["G"]:.1f} m² · principal {suite_areas["M"]:.1f} m².</text>']
    parts += ['<rect x="75" y="650" width="970" height="70" fill="#fff3dc" stroke="#b95336"/><text x="95" y="678" font-size="18" font-weight="700" fill="#8e3825">NO APTO PARA CONSTRUIR</text><text x="95" y="703" font-size="11" fill="#4d5559">Anteproyecto sujeto a predio, estructura, egreso/incendio, accesibilidad, espesores, MEP, equipos, iluminación y revisión profesional.</text></g></svg>']
    return "".join(parts)

def section():
    sx, sy, sc = 105, 570, 23
    roof = sy-7.5*sc; p2 = sy-3.8*sc
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="720" viewBox="0 0 1120 720">
<rect width="1120" height="720" fill="#fbfaf7"/><g font-family="Arial" fill="#20292e">
<text x="75" y="48" font-size="25" font-weight="700">CORTE LONGITUDINAL A–A · ANTEPROYECTO</text>
<text x="75" y="75" font-size="13" fill="#566269">Rev. 0.3-borrador-02 · alturas de estudio · sección por eje peatonal</text>
<line x1="{sx}" y1="{sy}" x2="{sx+36*sc}" y2="{sy}" stroke="#172126" stroke-width="4"/>
<polyline points="{sx},{roof+10} {sx+36*sc},{roof}" fill="none" stroke="#172126" stroke-width="5"/>
<line x1="{sx}" y1="{sy}" x2="{sx}" y2="{roof+10}" stroke="#172126" stroke-width="4"/>
<line x1="{sx+36*sc}" y1="{sy}" x2="{sx+36*sc}" y2="{roof}" stroke="#172126" stroke-width="4"/>
<rect x="{sx+21*sc}" y="{p2}" width="{15*sc}" height="8" fill="#8f6f5a"/>
<rect x="{sx+21*sc}" y="{p2+8}" width="{15*sc}" height="{sy-p2-8}" fill="#e0cbb2" opacity=".45"/>
<line x1="{sx+21*sc}" y1="{p2}" x2="{sx+21*sc}" y2="{roof+4}" stroke="#566269" stroke-width="2" stroke-dasharray="7 5"/>
<text x="{sx+10.5*sc}" y="{sy-3.7*sc}" text-anchor="middle" font-size="17">DOBLE ALTURA · 21,00 m</text>
<text x="{sx+28.5*sc}" y="{p2-16}" text-anchor="middle" font-size="14">P2 PRIVADO · 15,00 m</text>
<text x="{sx+28.5*sc}" y="{p2+55}" text-anchor="middle" font-size="13">COCINA / NÚCLEO BAJO P2</text>
<text x="{sx+5.25*sc}" y="{sy-22}" text-anchor="middle" font-size="11">TÉCNICA · 10,50 m</text>
<text x="{sx+15.75*sc}" y="{sy-22}" text-anchor="middle" font-size="11">MONUMENTAL · 10,50 m</text>
<text x="{sx+26.25*sc}" y="{sy-22}" text-anchor="middle" font-size="11">DOMÉSTICA · 10,50 m</text>
<text x="{sx+33.75*sc}" y="{sy-22}" text-anchor="middle" font-size="11">NÚCLEO · 4,50 m</text>
<g stroke="#6c777b" fill="none"><line x1="{sx-30}" y1="{sy}" x2="{sx-30}" y2="{roof+10}"/><line x1="{sx-35}" y1="{p2}" x2="{sx-25}" y2="{p2}"/><line x1="{sx-35}" y1="{roof+10}" x2="{sx-25}" y2="{roof+10}"/></g>
<text x="{sx-42}" y="{(sy+p2)/2}" text-anchor="middle" font-size="11" transform="rotate(-90 {sx-42} {(sy+p2)/2})">P2 ≈ +3,80 m</text>
<text x="{sx-62}" y="{(p2+roof)/2}" text-anchor="middle" font-size="11" transform="rotate(-90 {sx-62} {(p2+roof)/2})">altura interior ≈ 7,50 m</text>
<rect x="75" y="620" width="970" height="62" fill="#fff3dc" stroke="#b95336"/><text x="95" y="648" font-size="18" font-weight="700" fill="#8e3825">NO APTO PARA CONSTRUIR</text><text x="95" y="671" font-size="11">Cantos, pendiente, estructura, envolvente, drenaje, MEP y niveles dependen de ingeniería y predio.</text>
</g></svg>'''

def elevation(p):
    ex, base, sc = 170, 570, 42
    width=18*sc; top=base-7.5*sc
    openings=p["ground_floor"]["front_openings"]
    els=[]
    for op in openings:
        x=ex+op["y0"]*sc; w=op["width"]*sc; h=op["height"]*sc
        els.append(f'<rect x="{x}" y="{base-h}" width="{w}" height="{h}" fill="#38464c" stroke="#172126" stroke-width="2"/><text x="{x+w/2}" y="{base-h/2}" text-anchor="middle" fill="#f7f4ec" font-size="11">{html.escape(op["name"])}<tspan x="{x+w/2}" dy="15">{op["width"]:.2f} × {op["height"]:.2f} m</tspan></text>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="720" viewBox="0 0 1120 720"><rect width="1120" height="720" fill="#fbfaf7"/><g font-family="Arial" fill="#20292e">
<text x="75" y="48" font-size="25" font-weight="700">FACHADA FRONTAL · ANTEPROYECTO</text><text x="75" y="75" font-size="13" fill="#566269">Tres accesos exactos · composición nominal pendiente de estructura y sistema comercial</text>
<rect x="{ex}" y="{top}" width="{width}" height="{base-top}" fill="#a9afb0" stroke="#172126" stroke-width="4"/>
<line x1="{ex}" y1="{top+10}" x2="{ex+width}" y2="{top}" stroke="#e4e7e5" stroke-width="3"/>{''.join(els)}
<rect x="{ex-45}" y="{base}" width="{width+90}" height="35" fill="#d5d0c7"/><text x="{ex+width/2}" y="{base+23}" text-anchor="middle" font-size="11">PLATAFORMA DE CONCRETO · drenaje y niveles pendientes</text>
<line x1="{ex}" y1="{base+56}" x2="{ex+width}" y2="{base+56}" stroke="#566269"/><text x="{ex+width/2}" y="{base+50}" text-anchor="middle" font-size="12">18,00 m</text>
<rect x="75" y="650" width="970" height="48" fill="#fff3dc" stroke="#b95336"/><text x="95" y="680" font-size="17" font-weight="700" fill="#8e3825">NO APTO PARA CONSTRUIR · color, panel, estructura, remates y drenajes pendientes</text>
</g></svg>'''

def main():
    p=json.loads(DATA.read_text(encoding="utf-8")); checks,suites=validate(p); OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"DH-ARQ-PLN-001-R01_PB.svg").write_text(plan(p,"PB",suites),encoding="utf-8")
    (OUT/"DH-ARQ-PLN-002-R01_P2.svg").write_text(plan(p,"P2",suites),encoding="utf-8")
    (OUT/"DH-ARQ-SEC-001-R01_LONGITUDINAL.svg").write_text(section(),encoding="utf-8")
    (OUT/"DH-ARQ-ELE-001-R01_FRONTAL.svg").write_text(elevation(p),encoding="utf-8")
    report={"revision":p["project"]["revision"],"checks":checks,"suite_areas_m2":suites,"passed":sum(c["status"]=="PASS" for c in checks),"failed":sum(c["status"]=="FAIL" for c in checks)}
    (OUT/"compliance.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    manifest={"input":str(DATA.relative_to(ROOT)),"sha256":hashlib.sha256(DATA.read_bytes()).hexdigest(),"generator":"dreamhouse/generate_detailed_plans.py","outputs":["DH-ARQ-PLN-001-R01_PB.svg","DH-ARQ-PLN-002-R01_P2.svg","DH-ARQ-SEC-001-R01_LONGITUDINAL.svg","DH-ARQ-ELE-001-R01_FRONTAL.svg","compliance.json"]}
    (OUT/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print(json.dumps({"passed":report["passed"],"failed":report["failed"],"suite_areas":suites}))
    if report["failed"]: raise SystemExit(1)

if __name__=="__main__": main()
