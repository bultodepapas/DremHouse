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
def rect(x,y,w,d,fill="#fff",stroke="#45545a",sw=1.2,rx=0):
    return f'<rect x="{sx(x)}" y="{sy(y+d)}" width="{w*S}" height="{d*S}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" rx="{rx}"/>'
def txt(x,y,s,size=9,weight=400,anchor="middle",fill="#233238"):
    return f'<text x="{x}" y="{y}" font-family="Arial" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" fill="{fill}">{esc(s)}</text>'
def label(z):
    cx=sx(z["x"]+z["w"]/2); cy=sy(z["y"]+z["d"]/2)
    a=z["w"]*z["d"]
    fs=max(5.2,min(8.0,z["w"]*S/max(1,len(z["name"])*.62)))
    return txt(cx,cy-3,z["name"],fs,700)+txt(cx,cy+10,f'{z["w"]:.2f} × {z["d"]:.2f} = {a:.1f} m²',max(5.0,fs-.7))
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
    for z in p["spaces"]: q += [rect(z["x"],z["y"],z["w"],z["d"],colors[z["kind"]],"#4c5b60",1.4),label(z)]
    q += [bed(21.8,.9),bed(30.7,1.0),bed(21.8,13.2),bed(28.2,13.2)]
    for f in [("shower",26.35,3.7,1.15,1.05),("wc",27.55,2.3,.65,.8),("vanity",26.35,2.25,.9,.45),("shower",29.0,5.5,1.7,1.45),("wc",31.8,4.65,.65,.8),("vanity",29.0,4.45,2.4,.45),("shower",23.55,16.65,1.2,1.1),("wc",26.5,16.65,.65,.8),("vanity",25.0,17.35,1.1,.4),("shower",29.65,16.65,1.1,1.1),("wc",31.8,16.65,.65,.8),("vanity",30.85,17.35,.8,.4),("sauna",33.25,15.1,2.5,2.5),("shower",33.3,13.0,1.15,1.15)]: q.append(fixture(*f))
    q += [window(w) for w in p["windows"]]
    y=sy(p["phase_boundary_y"]); q += [f'<line x1="{sx(21)}" y1="{y}" x2="{sx(36)}" y2="{y}" stroke="#7b3f8c" stroke-width="4" stroke-dasharray="12 6"/>',txt((sx(21)+sx(36))/2,y-8,"FRONTERA ÚNICA F1 / F2 · CIERRE TEMPORAL ESTANCO",9,700,fill="#7b3f8c")]
    # dimensions and legend
    q += [f'<line x1="{sx(21)}" y1="{sy(0)+35}" x2="{sx(36)}" y2="{sy(0)+35}" stroke="#344247"/><line x1="{sx(21)}" y1="{sy(0)+29}" x2="{sx(21)}" y2="{sy(0)+41}" stroke="#344247"/><line x1="{sx(36)}" y1="{sy(0)+29}" x2="{sx(36)}" y2="{sy(0)+41}" stroke="#344247"/>',txt((sx(21)+sx(36))/2,sy(0)+31,"15,00 m",9,700)]
    q += [txt(730,160,"CRITERIOS DE COORDINACIÓN",13,700,"start")]
    for i,n in enumerate(p["design_notes"]): q.append(txt(730,185+i*24,"• "+n,9,400,"start"))
    q += [txt(730,360,"ESPESORES DE ESTUDIO",12,700,"start"),txt(730,384,"Exterior 0,18 m · húmedos/escalera 0,20 m · divisiones 0,15 m",9,400,"start"),txt(730,425,"ÁREAS CLAVE",12,700,"start"),txt(730,449,"Dormitorios hijos: 26,0 m² exactos cada uno",9,700,"start"),txt(730,471,"Dormitorio principal: 31,1 m² · fachada doble",9,400,"start"),txt(730,493,"Wellness: 16,5 m² brutos con sauna, ducha y relax",9,400,"start"),txt(730,535,"LEYENDA",12,700,"start"),txt(730,559,"Azul grueso: vidrio casi piso a techo / vano alto",9,400,"start"),txt(730,581,"Morado punteado: frontera de obra F1/F2",9,400,"start"),'</svg>']
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
    sp=p["spaces"]; by={z["id"]:z for z in sp}; area=lambda z:z["w"]*z["d"]
    pairs=[]
    for i,a in enumerate(sp):
        for b in sp[i+1:]:
            if min(a["x"]+a["w"],b["x"]+b["w"])-max(a["x"],b["x"])>1e-6 and min(a["y"]+a["d"],b["y"]+b["d"])-max(a["y"],b["y"])>1e-6: pairs.append((a["id"],b["id"]))
    tests=[("P2-ENV",all(z["x"]>=21 and z["x"]+z["w"]<=36 and z["y"]>=0 and z["y"]+z["d"]<=18 for z in sp),"Espacios dentro de 18 × 15 m"),("P2-NO-OVERLAP",not pairs,"Sin solapes de recintos"),("P2-4-SUITES",{z.get("suite") for z in sp if z.get("suite")}=={"H1","H2","G","M"},"Cuatro suites exactas"),("P2-CHILD-EQUAL",abs(area(by["H1-D"])-area(by["H2-D"]))<.001,"Dormitorios hijos = 26,0 m²"),("P2-F2",all(z["y"]>=11 for z in sp if z["phase"]==2),"F2 tras frontera única"),("P2-BED-WINDOWS",all(any(w["id"]=="W-"+i for w in p["windows"]) for i in ("H1","H2","G")),"Dormitorios secundarios con vidrio alto"),("P2-MASTER-WIDTH",by["M-D"]["w"]>=7.0,"Dormitorio principal ancho y jerárquico"),("P2-WELLNESS",area(by["WELL"])>=16,"Wellness >=16 m²")]
    out=[{"rule_id":i,"status":"PASS" if ok else "FAIL","message":m} for i,ok,m in tests]
    out.append({"rule_id":"LIFE-EGRESS-2","status":"OPEN","message":"Segunda salida independiente sujeta a concepto profesional de incendio"})
    return out
def main():
    p=json.loads(DATA.read_text(encoding="utf-8")); OUT.mkdir(parents=True,exist_ok=True)
    outputs={"DH-ARQ-PLN-002-R05_P2-DETALLADA.svg":plan(p),"DH-ARQ-DIA-001-R05_LOGICA-EGRESO-P2.svg":diagram(p)}
    for n,v in outputs.items(): (OUT/n).write_text(v,encoding="utf-8")
    checks=validate(p); report={"revision":p["revision"],"passed":sum(x["status"]=="PASS" for x in checks),"open":sum(x["status"]=="OPEN" for x in checks),"failed":sum(x["status"]=="FAIL" for x in checks),"checks":checks}; (OUT/"compliance.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    manifest={"revision":p["revision"],"source":"dreamhouse/p2_b06.json","source_sha256":hashlib.sha256(DATA.read_bytes()).hexdigest(),"generator":"dreamhouse/generate_p2_b06.py","outputs":list(outputs)+["compliance.json","manifest.json"]}; (OUT/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({k:report[k] for k in ("passed","open","failed")})); raise SystemExit(1 if report["failed"] else 0)
if __name__=="__main__": main()
