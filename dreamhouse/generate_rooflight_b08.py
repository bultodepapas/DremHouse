from __future__ import annotations
import hashlib, html, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; DATA=Path(__file__).with_name("rooflight_b08.json"); OUT=ROOT/"planos"/"conceptual_v0.3_b08_claraboyas"
def t(x,y,s,size=10,w=400,a="middle",fill="#233238",rot=None):
    tr=f' transform="rotate({rot} {x} {y})"' if rot else ""
    return f'<text x="{x}" y="{y}" font-family="Arial" font-size="{size}" font-weight="{w}" text-anchor="{a}" fill="{fill}"{tr}>{html.escape(str(s))}</text>'
def head(title,code,sub): return ['<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="900" viewBox="0 0 1400 900">','<rect width="1400" height="900" fill="#fbfaf7"/>',t(70,45,title,25,700,"start"),t(70,70,sub,11,400,"start","#59676c"),t(1325,95,code,15,700,"end","#7e3f2c")]
def roof_plan(p):
    q=head("PLANTA DE CUBIERTA · CLARABOYAS SOBRE TALLERES","PLN-CUB-001-R07","Faldón único 3,33 % · dos eventos de luz modulares · dimensiones en metros")
    x0,y0,s=150,150,27
    q += [f'<rect x="{x0}" y="{y0}" width="{36*s}" height="{18*s}" fill="#c9ced0" stroke="#172126" stroke-width="5"/>']
    for x in range(0,37,6): q.append(f'<line x1="{x0+x*s}" y1="{y0}" x2="{x0+x*s}" y2="{y0+18*s}" stroke="#727f83" stroke-dasharray="8 5"/>')
    for y in range(0,19,3): q.append(f'<line x1="{x0}" y1="{y0+y*s}" x2="{x0+36*s}" y2="{y0+y*s}" stroke="#a0a9ab" stroke-width=".8"/>')
    for r in p["rooflights"]:
        x=x0+r["x"]*s; y=y0+r["y"]*s; w=r["length"]*s; h=r["width"]*s
        q += [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="#6ea3b0" stroke="#173c46" stroke-width="3"/>',f'<path d="M{x+5} {y+h-8} L{x+w-5} {y+8}" stroke="#cde6eb" stroke-width="3"/>',t(x+w/2,y+h/2-5,r["name"].upper(),8,700),t(x+w/2,y+h/2+12,"2,40 × 4,80 m · 11,52 m²",7,700)]
    q += [t(x0+5.25*s,y0+9*s,"BANDA TÉCNICA / DOBLE ALTURA",13,700,rot=-90),t(x0+18*s,y0+18*s+35,"36,00 m",11,700),t(x0-30,y0+9*s,"18,00 m",11,700,rot=-90)]
    q += [f'<line x1="{x0+9*s}" y1="{y0+16*s}" x2="{x0+9*s}" y2="{y0+2*s}" stroke="#276e7d" stroke-width="4"/><polygon points="{x0+9*s-7},{y0+2*s+14} {x0+9*s},{y0+2*s} {x0+9*s+7},{y0+2*s+14}" fill="#276e7d"/>',t(x0+9*s+15,y0+9*s,"SUBIDA HACIA LADO ALTO",9,700,"start","#276e7d",-90)]
    q += [t(1160,170,"CRITERIO",13,700,"start"),t(1160,198,"Dos paños iguales; no una franja continua.",9,400,"start"),t(1160,222,"Separados del eje peatonal y sobre cada taller.",9,400,"start"),t(1160,246,"Dentro del primer módulo estructural de 6 m.",9,400,"start"),t(1160,270,"Posición final depende de pórticos y correas.",9,400,"start"),t(1160,315,"ÁREA TOTAL DE VIDRIO: 23,04 m²",11,700,"start","#1f6978"),t(1160,355,"No se altera el P2 ni la cubierta única.",9,700,"start"),'</svg>']
    return ''.join(q)
def section(p):
    q=head("CORTE TRANSVERSAL · LUZ CENITAL EN DOBLE ALTURA","SEC-CUB-003-R07","Corte por ambas claraboyas · geometría conceptual, no detalle constructivo")
    x0,base,s=180,650,48; low=base-7.2*s; high=base-7.8*s; width=18*s
    q += [f'<line x1="{x0}" y1="{base}" x2="{x0+width}" y2="{base}" stroke="#172126" stroke-width="4"/><line x1="{x0}" y1="{base}" x2="{x0}" y2="{low}" stroke="#172126" stroke-width="4"/><line x1="{x0+width}" y1="{base}" x2="{x0+width}" y2="{high}" stroke="#172126" stroke-width="4"/>']
    def ry(y): return low-(high-low)*y/18
    segments=[(0,1.2),(6.0,12.0),(16.8,18)]
    for a,b in segments: q.append(f'<line x1="{x0+a*s}" y1="{ry(a)}" x2="{x0+b*s}" y2="{ry(b)}" stroke="#172126" stroke-width="6"/>')
    for a,b,label in [(1.2,6.0,"CAR PROJECT"),(12.0,16.8,"RC / DIY")]:
        q += [f'<line x1="{x0+a*s}" y1="{ry(a)}" x2="{x0+b*s}" y2="{ry(b)}" stroke="#5c9dac" stroke-width="11"/>',f'<polygon points="{x0+(a+.3)*s},{ry(a)+12} {x0+(b-.3)*s},{ry(b)+12} {x0+(b-1)*s},{base-40} {x0+(a+1)*s},{base-40}" fill="#cce8ee" opacity=".34"/>',t(x0+(a+b)/2*s,base-20,label,10,700)]
    q += [t(x0,low-18,"≈7,20 m",10,700,"start"),t(x0+width,high-18,"≈7,80 m",10,700,"end"),t(1160,235,"VIDRIO AISLANTE LAMINADO",12,700,"start"),t(1160,263,"Curb elevado ≥0,20 m",9,400,"start"),t(1160,287,"Frita/control solar por orientación",9,400,"start"),t(1160,311,"Canal perimetral y rebose",9,400,"start"),t(1160,335,"Acceso seguro para limpieza",9,400,"start"),t(1160,375,"NO ABRIR CORREAS SIN CÁLCULO",10,700,"start","#9a3828"),'</svg>']
    return ''.join(q)
def detail(p):
    q=head("DETALLE CONCEPTUAL · BORDE DE CLARABOYA","DET-CUB-001-R07","Principio higrotérmico y de estanqueidad · requiere sistema certificado")
    q += [f'<polygon points="170,500 920,475 920,530 170,555" fill="#b9bec0" stroke="#172126" stroke-width="3"/>',t(500,590,"PANEL SÁNDWICH CONTINUO HACIA ALERO BAJO",11,700)]
    q += ['<rect x="420" y="400" width="300" height="45" fill="#71a5b1" stroke="#173c46" stroke-width="3"/>','<path d="M435 430 L700 408" stroke="#d9eef2" stroke-width="4"/>','<path d="M405 500 L405 430 L420 430 M735 482 L735 430 L720 430" fill="none" stroke="#7f553c" stroke-width="10"/>']
    q += [t(570,385,"UNIDAD DE VIDRIO AISLANTE + INTERIOR LAMINADO",11,700),t(380,418,"CURB ≥0,20 m",9,700,"end"),t(770,450,"REMATE / BABETA",9,700,"start"),t(770,477,"CANAL DE DRENAJE",9,700,"start"),t(170,680,"Principio: continuidad de aire/vapor/aislamiento; doble barrera de agua; vidrio retenido mecánicamente; reemplazo desde cubierta.",10,400,"start"),t(170,710,"No aceptar domo acrílico simple ni marco sin rotura térmica para clima frío de Boyacá.",10,700,"start","#963827"),'</svg>']
    return ''.join(q)
def validate(p):
    rs=p["rooflights"]; overlap=lambda a,b:min(a["x"]+a["length"],b["x"]+b["length"])-max(a["x"],b["x"])>0 and min(a["y"]+a["width"],b["y"]+b["width"])-max(a["y"],b["y"])>0
    tests=[("RL-TWO",len(rs)==2,"Dos claraboyas, una por taller"),("RL-IN-TECH",all(r["x"]+r["length"]<=10.5 for r in rs),"Dentro de banda técnica/doble altura"),("RL-NO-OVERLAP",not overlap(rs[0],rs[1]),"Paños separados"),("RL-AREA",abs(sum(r["area"] for r in rs)-23.04)<.01,"Área total 23,04 m²"),("RL-EDGE",all(r["y"]>=1 and r["y"]+r["width"]<=17 for r in rs),"Retiro preliminar de bordes")]
    out=[{"rule_id":i,"status":"PASS" if ok else "FAIL","message":m} for i,ok,m in tests]
    out += [{"rule_id":"RL-STRUCTURE","status":"OPEN","message":"Coordinación exacta con pórticos/correas pendiente"},{"rule_id":"RL-HYGRO","status":"OPEN","message":"Vidrio, control solar y condensación pendientes de cálculo"}]; return out
def main():
    p=json.loads(DATA.read_text(encoding="utf-8")); OUT.mkdir(parents=True,exist_ok=True); outputs={"DH-ARQ-PLN-CUB-001-R07_CLARABOYAS.svg":roof_plan(p),"DH-ARQ-SEC-CUB-003-R07_LUZ-CENITAL.svg":section(p),"DH-ARQ-DET-CUB-001-R07_BORDE-CLARABOYA.svg":detail(p)}
    for n,s in outputs.items():(OUT/n).write_text(s,encoding="utf-8")
    c=validate(p); rep={"revision":p["revision"],"passed":sum(x["status"]=="PASS" for x in c),"open":sum(x["status"]=="OPEN" for x in c),"failed":sum(x["status"]=="FAIL" for x in c),"checks":c}; (OUT/"compliance.json").write_text(json.dumps(rep,ensure_ascii=False,indent=2),encoding="utf-8"); m={"revision":p["revision"],"source":"dreamhouse/rooflight_b08.json","source_sha256":hashlib.sha256(DATA.read_bytes()).hexdigest(),"generator":"dreamhouse/generate_rooflight_b08.py","outputs":list(outputs)+["compliance.json","manifest.json"]}; (OUT/"manifest.json").write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding="utf-8"); print(json.dumps({k:rep[k] for k in ("passed","open","failed")}))
if __name__=="__main__":main()
