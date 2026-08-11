from __future__ import annotations
import hashlib, html, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=Path(__file__).with_name("p2_b06.json")
OUT=ROOT/"planos"/"conceptual_v0.3_b06_p2"
S=27; X0=205; Y0=155

def sx(x): return X0+(x-21)*S
def sy(y): return Y0+(18-y)*S
def esc(s): return html.escape(str(s))

def net_dims(z,env):
    """Dimensiones netas de un recinto, descontando espesores reales.

    El modelo teselaba la envolvente completa (18 × 15 = 270,00 m² exactos), es decir
    declaraba áreas "brutas" que no dejaban sitio para un solo muro (hallazgo H-04).
    Aquí cada recinto pierde el espesor de envolvente donde toca el perímetro y medio
    tabique donde linda con otro recinto.
    """
    ext=env["exterior_wall"]
    t=env["wet_wall"] if z["kind"] in ("bath","vertical","wellness") else env["partition"]
    h=t/2
    eq=lambda a,b: abs(a-b)<1e-9
    dx0=ext if eq(z["x"],21.0) else h
    dx1=ext if eq(z["x"]+z["w"],36.0) else h
    dy0=ext if eq(z["y"],0.0) else h
    dy1=ext if eq(z["y"]+z["d"],18.0) else h
    return max(0.0,z["w"]-dx0-dx1),max(0.0,z["d"]-dy0-dy1)

def net_area(z,env):
    w,d=net_dims(z,env); return w*d
def rect(x,y,w,d,fill="#fff",stroke="#45545a",sw=1.2,rx=0):
    return f'<rect x="{sx(x)}" y="{sy(y+d)}" width="{w*S}" height="{d*S}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" rx="{rx}"/>'
def txt(x,y,s,size=9,weight=400,anchor="middle",fill="#233238"):
    return f'<text x="{x}" y="{y}" font-family="Arial" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" fill="{fill}">{esc(s)}</text>'
def label(z,env):
    cx=sx(z["x"]+z["w"]/2); cy=sy(z["y"]+z["d"]/2)
    nw,nd=net_dims(z,env)
    fs=max(5.2,min(8.0,z["w"]*S/max(1,len(z["name"])*.62)))
    return (txt(cx,cy-7,z["name"],fs,700)
            +txt(cx,cy+5,f'{nw:.2f} × {nd:.2f} = {nw*nd:.1f} m² netos',max(5.0,fs-.7))
            +txt(cx,cy+15,f'bruto {z["w"]:.2f} × {z["d"]:.2f}',max(4.6,fs-1.5),400,fill="#7d8a8e"))
def bed(x,y,w=2.1,d=2.0):
    return rect(x,y,w,d,"#f3eee6","#627176",1.1,6)+rect(x+.1,y+d-.45,w-.2,.35,"#fff","#9ca5a6",.8,4)
def fixture(kind,x,y,w,d):
    color={"shower":"#d7edf0","wc":"#f7f5ef","vanity":"#e8ddca","sauna":"#d9b890"}[kind]
    return rect(x,y,w,d,color,"#58676c",1,3)+txt(sx(x+w/2),sy(y+d/2)+3,kind.upper(),6,700)
def window(w):
    if w["edge"] in ("south","north"):
        yy=sy(0 if w["edge"]=="south" else 18)
        return f'<line x1="{sx(w["from"])}" y1="{yy}" x2="{sx(w["to"])}" y2="{yy}" stroke="#168aa3" stroke-width="7"/>'
    xx=sx(36); return f'<line x1="{xx}" y1="{sy(w["to"])}" x2="{xx}" y2="{sy(w["from"])}" stroke="#168aa3" stroke-width="7"/>'
def base(title,sheet,subtitle):
    return ['<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="900" viewBox="0 0 1400 900">','<rect width="1400" height="900" fill="#fbfaf7"/>',txt(70,45,title,25,700,"start"),txt(70,70,subtitle,11,400,"start","#59676c"),txt(1325,95,sheet,15,700,"end","#7e3f2c")]
def plan(p):
    q=base("SEGUNDO PISO DETALLADO · ANTEPROYECTO","PLN-002-R05","Rev. 0.3-borrador-06-P2 · cotas en metros · no apto para construir")
    q += [rect(21,0,15,18,"#f8f7f2","#172126",6)]
    colors={"bedroom":"#dbe7eb","master":"#eadaca","bath":"#d8e8e5","closet":"#e8e0d4","circulation":"#f2eee5","service":"#e3e7df","deck":"#e7d6ba","vertical":"#ddd6cf","wellness":"#dec7aa"}
    for z in p["spaces"]: q += [rect(z["x"],z["y"],z["w"],z["d"],colors[z["kind"]],"#4c5b60",1.4),label(z,p["envelope"])]
    q += [bed(21.8,.9),bed(30.7,1.0),bed(21.8,13.2),bed(28.2,13.2)]
    for f in [("shower",26.35,3.7,1.15,1.05),("wc",27.55,2.3,.65,.8),("vanity",26.35,2.25,.9,.45),("shower",29.0,5.5,1.7,1.45),("wc",31.8,4.65,.65,.8),("vanity",29.0,4.45,2.4,.45),("shower",23.55,16.65,1.2,1.1),("wc",26.5,16.65,.65,.8),("vanity",25.0,17.35,1.1,.4),("shower",29.65,16.65,1.1,1.1),("wc",31.8,16.65,.65,.8),("vanity",30.85,17.35,.8,.4),("sauna",33.25,15.1,2.5,2.5),("shower",33.3,13.0,1.15,1.15)]: q.append(fixture(*f))
    q += [window(w) for w in p["windows"]]
    y=sy(p["phase_boundary_y"]); q += [f'<line x1="{sx(21)}" y1="{y}" x2="{sx(36)}" y2="{y}" stroke="#7b3f8c" stroke-width="4" stroke-dasharray="12 6"/>',txt((sx(21)+sx(36))/2,y-8,"FRONTERA ÚNICA F1 / F2 · CIERRE TEMPORAL ESTANCO",9,700,fill="#7b3f8c")]
    # dimensions and legend
    q += [f'<line x1="{sx(21)}" y1="{sy(0)+35}" x2="{sx(36)}" y2="{sy(0)+35}" stroke="#344247"/><line x1="{sx(21)}" y1="{sy(0)+29}" x2="{sx(21)}" y2="{sy(0)+41}" stroke="#344247"/><line x1="{sx(36)}" y1="{sy(0)+29}" x2="{sx(36)}" y2="{sy(0)+41}" stroke="#344247"/>',txt((sx(21)+sx(36))/2,sy(0)+31,"15,00 m",9,700)]
    q += [txt(730,160,"CRITERIOS DE COORDINACIÓN",13,700,"start")]
    for i,n in enumerate(p["design_notes"]): q.append(txt(730,185+i*24,"• "+n,9,400,"start"))
    # Las áreas del rótulo se calculan, nunca se escriben a mano (hallazgo H-04).
    env=p["envelope"]; by={z["id"]:z for z in p["spaces"]}
    na=lambda i:net_area(by[i],env)
    d1,d2=net_dims(by["H1-D"],env),net_dims(by["H2-D"],env)
    dif=abs(na("H1-D")-na("H2-D")); okeq=dif<=.05
    q += [txt(730,360,"ESPESORES DE ESTUDIO",12,700,"start"),txt(730,384,"Exterior 0,18 m · húmedos/escalera 0,20 m · divisiones 0,15 m",9,400,"start"),
          txt(730,425,"ÁREAS NETAS (espesores descontados)",12,700,"start"),
          txt(730,449,f'Hijo 1: {na("H1-D"):.2f} m² · {d1[0]:.2f} × {d1[1]:.2f}',9,700,"start"),
          txt(730,469,f'Hijo 2: {na("H2-D"):.2f} m² · {d2[0]:.2f} × {d2[1]:.2f}',9,700,"start"),
          txt(730,489,f'Diferencia {dif:.2f} m² · hard rule 9 exige igualdad exacta',9,700,"start","#2f6146" if okeq else "#8e3328"),
          txt(730,511,f'Principal {na("M-D"):.1f} m² · vestidor {na("M-C"):.1f} m² · baño {na("M-B"):.1f} m²',9,400,"start"),
          txt(730,531,f'Wellness {na("WELL"):.1f} m² · vestíbulo F2 {min(net_dims(by["F2-HALL"],env)):.2f} m libres',9,400,"start"),
          txt(730,568,"LEYENDA",12,700,"start"),txt(730,592,"Azul grueso: vidrio casi piso a techo / vano alto",9,400,"start"),txt(730,614,"Morado punteado: frontera de obra F1/F2",9,400,"start"),'</svg>']
    return ''.join(q)
def diagram(p):
    q=base("LÓGICA, PRIVACIDAD Y EVACUACIÓN P2","DIA-001-R05","Diagrama de coordinación · recorridos indicativos, no cálculo normativo")
    q += [rect(21,0,15,18,"#f7f6f1","#172126",5)]
    for z in p["spaces"]:
        col="#d9e5df" if z["phase"]==1 else "#eadfed"
        q += [rect(z["x"],z["y"],z["w"],z["d"],col,"#657276",1),txt(sx(z["x"]+z["w"]/2),sy(z["y"]+z["d"]/2)+3,z["id"],7,700)]
    pts=[(23.6,2.5),(26.9,9.5),(29.0,11.5),(32.8,9.2),(34.0,9.2)]
    q.append('<polyline points="'+' '.join(f'{sx(x)},{sy(y)}' for x,y in pts)+'" fill="none" stroke="#b54332" stroke-width="4" marker-end="url(#a)"/>')
    q.insert(5,'<defs><marker id="a" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="#b54332"/></marker></defs>')
    q += [txt(730,175,"LECTURA ARQUITECTÓNICA",13,700,"start"),txt(730,205,"1. Llegada protegida y distribución sin balcón abierto.",10,400,"start"),txt(730,232,"2. Suites con filtros; camas fuera de la visual directa del hall.",10,400,"start"),txt(730,259,"3. F2 se aísla mediante una sola puerta y cierre continuo.",10,400,"start"),txt(730,286,"4. Zona húmeda compacta; bajantes por coordinar con núcleo PB.",10,400,"start"),txt(730,325,"ALERTA DE VIDA Y SEGURIDAD",13,700,"start","#8e3328"),txt(730,353,"La flecha roja ilustra la única salida hoy representada.",10,700,"start"),txt(730,378,"La segunda salida, distancias y resistencia al fuego siguen ABIERTAS.",10,400,"start"),'</svg>']
    return ''.join(q)
def validate(p):
    """FAIL = defecto del modelo o hard rule incumplida. OPEN = decisión pendiente del propietario."""
    sp=p["spaces"]; env=p["envelope"]; by={z["id"]:z for z in sp}
    net=lambda z:net_area(z,env)
    ratio=lambda z:(lambda w,d:max(w,d)/max(1e-9,min(w,d)))(*net_dims(z,env))
    pairs=[]
    for i,a in enumerate(sp):
        for b in sp[i+1:]:
            if min(a["x"]+a["w"],b["x"]+b["w"])-max(a["x"],b["x"])>1e-6 and min(a["y"]+a["d"],b["y"]+b["d"])-max(a["y"],b["y"])>1e-6: pairs.append((a["id"],b["id"]))
    ext=env["exterior_wall"]
    interior=(18-2*ext)*(15-2*ext)
    sum_net=sum(net(z) for z in sp); sum_gross=sum(z["w"]*z["d"] for z in sp)
    n1,n2=net(by["H1-D"]),net(by["H2-D"]); r1,r2=ratio(by["H1-D"]),ratio(by["H2-D"])
    circ=[z for z in sp if z["kind"]=="circulation"]
    narrow=min(circ,key=lambda z:min(net_dims(z,env)))
    nmin=min(net_dims(narrow,env))
    mc,mb=net(by["M-C"]),net(by["M-B"])
    tests=[
      ("P2-ENV",all(z["x"]>=21 and z["x"]+z["w"]<=36 and z["y"]>=0 and z["y"]+z["d"]<=18 for z in sp),"Espacios dentro de 18 × 15 m"),
      ("P2-NO-OVERLAP",not pairs,"Sin solapes de recintos"),
      ("P2-AREA-CLOSURE",sum_net<=interior+1e-6,f"Σ neta {sum_net:.1f} m² ≤ interior útil {interior:.1f} m² (bruto teselado {sum_gross:.1f})"),
      ("P2-4-SUITES",{z.get("suite") for z in sp if z.get("suite")}=={"H1","H2","G","M"},"Cuatro suites exactas"),
      ("P2-CHILD-EQUAL",abs(n1-n2)<=.05,f"Hard rule 9 · dormitorios hijos NETOS: H1 {n1:.2f} m² vs H2 {n2:.2f} m² (Δ {abs(n1-n2):.2f} m²)"),
      ("P2-CIRC-MIN",nmin>=1.20-1e-6,f"Circulación mínima declarada 1,20 m · más estrecha: {narrow['id']} = {nmin:.2f} m netos"),
      ("P2-F2",all(z["y"]>=11 for z in sp if z["phase"]==2),"F2 tras frontera única"),
      ("P2-BED-WINDOWS",all(any(w["id"]=="W-"+i for w in p["windows"]) for i in ("H1","H2","G")),"Dormitorios secundarios con vidrio alto"),
      ("P2-MASTER-WIDTH",by["M-D"]["w"]>=7.0,"Dormitorio principal ancho y jerárquico"),
      ("P2-WELLNESS",net(by["WELL"])>=16,f"Wellness {net(by['WELL']):.1f} m² netos ≥ 16 m²"),
    ]
    out=[{"rule_id":i,"status":"PASS" if ok else "FAIL","message":m} for i,ok,m in tests]
    out += [
      # La hard rule 9 exige igualdad de área ("tendrán") pero sólo aspira a la equivalencia
      # cualitativa ("se buscará"): la proporción se reporta, no bloquea.
      {"rule_id":"P2-CHILD-PROPORTION","status":"OPEN" if abs(r1-r2)>.15 else "PASS","message":f"Equivalencia cualitativa (hard rule 9, 2.ª cláusula): H1 {r1:.2f}:1 vs H2 {r2:.2f}:1 — igualar área no iguala la habitación"},
      {"rule_id":"P2-MASTER-PROGRAM","status":"OPEN","message":f"Programa vs. dibujo (decisión del propietario): vestidor {mc:.1f} m² netos frente a 15–16 · baño principal {mb:.1f} m² frente a 17–18"},
      {"rule_id":"LIFE-EGRESS-2","status":"OPEN","message":"Segunda salida independiente sujeta a concepto profesional de incendio"},
    ]
    return out
def main():
    p=json.loads(DATA.read_text(encoding="utf-8")); OUT.mkdir(parents=True,exist_ok=True)
    outputs={"DH-ARQ-PLN-002-R05_P2-DETALLADA.svg":plan(p),"DH-ARQ-DIA-001-R05_LOGICA-EGRESO-P2.svg":diagram(p)}
    for n,v in outputs.items(): (OUT/n).write_text(v,encoding="utf-8")
    checks=validate(p); report={"revision":p["revision"],"passed":sum(x["status"]=="PASS" for x in checks),"open":sum(x["status"]=="OPEN" for x in checks),"failed":sum(x["status"]=="FAIL" for x in checks),"checks":checks}; (OUT/"compliance.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    manifest={"revision":p["revision"],"source":"dreamhouse/p2_b06.json","source_sha256":hashlib.sha256(DATA.read_bytes()).hexdigest(),"generator":"dreamhouse/generate_p2_b06.py","outputs":list(outputs)+["compliance.json","manifest.json"]}; (OUT/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({k:report[k] for k in ("passed","open","failed")})); raise SystemExit(1 if report["failed"] else 0)
if __name__=="__main__": main()
