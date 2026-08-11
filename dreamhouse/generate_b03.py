from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path

import generate_detailed_plans as base

ROOT=Path(__file__).resolve().parents[1]
DETAILS=Path(__file__).with_name("details_b03.json")
OUT=ROOT/"planos"/"conceptual_v0.3_b03"
S,X0,Y0=base.S,base.X0,base.Y0

def screen(x,y): return X0+x*S,Y0+(18-y)*S

def door_svg(d):
    x,y=screen(d["x"],d["y"]); w=d["width"]*S
    if d["orientation"]=="vertical":
        return f'<g stroke="#9b4e32" fill="none" stroke-width="1.7"><line x1="{x}" y1="{y}" x2="{x+w}" y2="{y}"/><path d="M {x} {y} A {w} {w} 0 0 1 {x} {y-w}" stroke-dasharray="3 2"/></g>'
    return f'<g stroke="#9b4e32" fill="none" stroke-width="1.7"><line x1="{x}" y1="{y}" x2="{x}" y2="{y-w}"/><path d="M {x} {y} A {w} {w} 0 0 0 {x+w} {y}" stroke-dasharray="3 2"/></g>'

def window_svg(w):
    edge=w["edge"]; a,b=w["from"]*S,w["to"]*S
    if edge=="bottom": return f'<line x1="{X0+a}" y1="{Y0+18*S}" x2="{X0+b}" y2="{Y0+18*S}" stroke="#27859a" stroke-width="7"/>'
    if edge=="top": return f'<line x1="{X0+a}" y1="{Y0}" x2="{X0+b}" y2="{Y0}" stroke="#27859a" stroke-width="7"/>'
    if edge=="right":
        y1=Y0+(18-w["to"])*S; y2=Y0+(18-w["from"])*S
        return f'<line x1="{X0+36*S}" y1="{y1}" x2="{X0+36*S}" y2="{y2}" stroke="#27859a" stroke-width="7"/>'
    return ""

def fixture_svg(f):
    x=X0+f["x"]*S; y=Y0+(18-f["y"]-f["d"])*S; w=f["w"]*S; h=f["d"]*S; typ=f["type"]
    if typ=="wc": return f'<g stroke="#52636a" fill="#f8faf9"><ellipse cx="{x+w/2}" cy="{y+h*.6}" rx="{w*.42}" ry="{h*.36}"/><rect x="{x+w*.15}" y="{y}" width="{w*.7}" height="{h*.28}"/></g>'
    if typ=="shower": return f'<g stroke="#27859a" fill="none"><rect x="{x}" y="{y}" width="{w}" height="{h}"/><line x1="{x}" y1="{y}" x2="{x+w}" y2="{y+h}"/><line x1="{x+w}" y1="{y}" x2="{x}" y2="{y+h}"/></g>'
    if typ=="vanity": return f'<g stroke="#52636a" fill="#f8faf9"><rect x="{x}" y="{y}" width="{w}" height="{h}"/><ellipse cx="{x+w/2}" cy="{y+h/2}" rx="{w*.18}" ry="{h*.3}"/></g>'
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="#52636a" stroke-width="1.5"/>'

def stair_svg():
    x=X0+31.72*S; y=Y0+(18-10.78)*S; w=4.06*S; h=3.16*S
    parts=[f'<g stroke="#4e5b60" fill="none" stroke-width="1"><rect x="{x}" y="{y}" width="{w}" height="{h}"/>']
    for i in range(1,11):
        yy=y+i*h/11
        parts.append(f'<line x1="{x}" y1="{yy}" x2="{x+w*.38}" y2="{yy}"/><line x1="{x+w*.62}" y1="{yy}" x2="{x+w}" y2="{yy}"/>')
    parts.append(f'<line x1="{x+w*.5}" y1="{y+h*.78}" x2="{x+w*.5}" y2="{y+h*.22}"/><polyline points="{x+w*.44},{y+h*.3} {x+w*.5},{y+h*.22} {x+w*.56},{y+h*.3}"/><text x="{x+w/2}" y="{y+h*.92}" text-anchor="middle" fill="#4e5b60" stroke="none" font-size="8">U · 21 contrahuellas aprox.</text></g>')
    return ''.join(parts)

def chain(floor):
    if floor=="PB":
        vals=[(0,10.5,"10,50"),(10.5,21,"10,50"),(21,31.5,"10,50"),(31.5,36,"4,50")]
    else: vals=[(0,21,"21,00 vacío"),(21,36,"15,00 P2")]
    y=Y0-48; chunks=[]
    for a,b,t in vals:
        x1,x2=X0+a*S,X0+b*S
        chunks.append(f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}"/><line x1="{x1}" y1="{y-5}" x2="{x1}" y2="{y+5}"/><line x1="{x2}" y1="{y-5}" x2="{x2}" y2="{y+5}"/><text x="{(x1+x2)/2}" y="{y-7}" text-anchor="middle" fill="#445158" stroke="none" font-size="10">{t} m</text>')
    return '<g stroke="#687479" fill="none" stroke-width=".8">'+''.join(chunks)+'</g>'

def enhance(svg,details,floor):
    svg=svg.replace("0.3-borrador-02","0.3-borrador-03")
    overlays=''.join(window_svg(w) for w in details["windows"][floor])
    overlays+=''.join(door_svg(d) for d in details["doors"][floor])
    overlays+=''.join(fixture_svg(f) for f in details["fixtures"][floor])
    overlays+=stair_svg()
    overlays+=chain(floor)
    legend='<g font-family="Arial"><line x1="790" y1="112" x2="825" y2="112" stroke="#27859a" stroke-width="6"/><text x="832" y="116" font-size="9">ventana / vidrio provisional</text><path d="M 790 130 A 22 22 0 0 1 812 108" fill="none" stroke="#9b4e32"/><text x="832" y="133" font-size="9">puerta y giro preliminar</text></g>'
    return svg.replace('<rect x="75" y="650"',overlays+legend+'<rect x="75" y="650"')

def transverse():
    x0,base,sc=170,575,42; w=18*sc; low=base-7.2*sc; high=base-7.8*sc; slab=base-3.8*sc
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="720"><rect width="1120" height="720" fill="#fbfaf7"/><g font-family="Arial" fill="#20292e"><text x="75" y="48" font-size="25" font-weight="700">CORTE TRANSVERSAL B–B · BAJO P2</text><text x="75" y="75" font-size="13" fill="#566269">Cubierta mono-pendiente transversal · subida 0,60 m / 18,00 m ≈ 3,33 %</text><line x1="{x0}" y1="{base}" x2="{x0+w}" y2="{base}" stroke="#172126" stroke-width="4"/><polyline points="{x0},{low} {x0+w},{high}" fill="none" stroke="#172126" stroke-width="5"/><line x1="{x0}" y1="{base}" x2="{x0}" y2="{low}" stroke="#172126" stroke-width="4"/><line x1="{x0+w}" y1="{base}" x2="{x0+w}" y2="{high}" stroke="#172126" stroke-width="4"/><rect x="{x0}" y="{slab}" width="{w}" height="8" fill="#8f6f5a"/><text x="{x0+w/2}" y="{slab-16}" text-anchor="middle" font-size="14">P2 PRIVADO · cielo horizontal 3,00–3,10 m + plenum variable</text><text x="{x0+w/2}" y="{slab+58}" text-anchor="middle" font-size="14">PB BAJO P2 · altura libre objetivo 3,05–3,20 m</text><text x="{x0+8}" y="{low-12}" font-size="12">LADO BAJO ≈ 7,20 m</text><text x="{x0+w-8}" y="{high-12}" text-anchor="end" font-size="12">LADO ALTO ≈ 7,80 m</text><line x1="{x0}" y1="{base+45}" x2="{x0+w}" y2="{base+45}" stroke="#566269"/><text x="{x0+w/2}" y="{base+39}" text-anchor="middle" font-size="12">18,00 m · sentido bajo/alto reversible según predio y drenaje</text><rect x="75" y="650" width="970" height="48" fill="#fff3dc" stroke="#b95336"/><text x="95" y="680" font-size="17" font-weight="700" fill="#8e3825">NO APTO PARA CONSTRUIR · pendiente y sistema sujetos a estructura, fabricante y lluvias</text></g></svg>'''

def main():
    p=json.loads(base.DATA.read_text(encoding="utf-8")); d=json.loads(DETAILS.read_text(encoding="utf-8")); checks,suites=base.validate(p); OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"DH-ARQ-PLN-001-R02_PB.svg").write_text(enhance(base.plan(p,"PB",suites),d,"PB"),encoding="utf-8")
    (OUT/"DH-ARQ-PLN-002-R02_P2.svg").write_text(enhance(base.plan(p,"P2",suites),d,"P2"),encoding="utf-8")
    (OUT/"DH-ARQ-SEC-001-R02_LONGITUDINAL.svg").write_text(base.section().replace("0.3-borrador-02","0.3-borrador-03"),encoding="utf-8")
    (OUT/"DH-ARQ-SEC-002-R02_TRANSVERSAL.svg").write_text(transverse(),encoding="utf-8")
    (OUT/"DH-ARQ-ELE-001-R02_FRONTAL.svg").write_text(base.elevation(p),encoding="utf-8")
    extra=[("ARQ-OPENINGS",len(d["doors"]["P2"])>=10,"P2 representa accesos principales"),("ARQ-DAYLIGHT",len(d["windows"]["P2"])>=4,"Cuatro suites con ventana exterior provisional"),("ARQ-WET",sum(f["type"]=="shower" for f in d["fixtures"]["P2"])==4,"Cuatro duchas privadas representadas")]
    checks += [{"rule_id":r,"status":"PASS" if ok else "FAIL","message":m} for r,ok,m in extra]
    report={"revision":d["revision"],"checks":checks,"passed":sum(c["status"]=="PASS" for c in checks),"failed":sum(c["status"]=="FAIL" for c in checks)}
    (OUT/"compliance.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    (OUT/"manifest.json").write_text(json.dumps({"base":d["base_model"],"detail_sha256":hashlib.sha256(DETAILS.read_bytes()).hexdigest(),"generator":"dreamhouse/generate_b03.py","revision":d["revision"]},indent=2),encoding="utf-8")
    print(json.dumps({"passed":report["passed"],"failed":report["failed"]}))
    if report["failed"]: raise SystemExit(1)

if __name__=="__main__": main()
