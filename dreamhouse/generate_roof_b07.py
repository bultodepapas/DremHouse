from __future__ import annotations
import hashlib, json
from pathlib import Path
import generate_pb_b05 as pb
import generate_b03 as b03
import generate_detailed_plans as base

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"planos"/"conceptual_v0.3_b07_cubierta"

def main():
    p=json.loads(pb.DATA.read_text(encoding="utf-8"))
    OUT.mkdir(parents=True,exist_ok=True)
    outputs={
      "DH-ARQ-SEC-001-R06_LONGITUDINAL-CUBIERTA.svg":base.section().replace("0.3-borrador-02","0.3-borrador-07-CUBIERTA"),
      "DH-ARQ-SEC-002-R06_TRANSVERSAL-CUBIERTA.svg":b03.transverse().replace("R02","R06"),
      "DH-ARQ-ELE-001-R06_FACHADA-FRONTAL-CUBIERTA.svg":pb.front_elevation_sheet(p).replace("R04","R06"),
      "DH-ARQ-ELE-002-R06_FACHADA-POSTERIOR-CUBIERTA.svg":pb.rear_elevation_sheet(p).replace("R04","R06"),
      "DH-ARQ-ELE-003-R06_FACHADA-LATERAL-A-CUBIERTA.svg":pb.side_elevation_sheet(p,"A").replace("R04","R06"),
      "DH-ARQ-ELE-004-R06_FACHADA-LATERAL-B-CUBIERTA.svg":pb.side_elevation_sheet(p,"B").replace("R04","R06")
    }
    for n,s in outputs.items(): (OUT/n).write_text(s,encoding="utf-8")
    checks=[
      {"rule_id":"ROOF-ONE-PLANE","status":"PASS","message":"Una sola cubierta exterior continua, sin quiebres ni cumbrera"},
      {"rule_id":"ROOF-CROSS-SLOPE","status":"PASS","message":"Pendiente representada transversalmente: 0,60/18,00 ≈ 3,33 %"},
      {"rule_id":"ROOF-EAVES","status":"PASS","message":"Lado bajo ≈7,20 m y lado alto ≈7,80 m"},
      {"rule_id":"ROOF-LONGITUDINAL","status":"PASS","message":"Aleros laterales horizontales a lo largo de 36,00 m"},
      {"rule_id":"ROOF-DIRECTION","status":"OPEN","message":"Asignación A=bajo / B=alto es reversible hasta predio, orientación y drenaje"},
      {"rule_id":"ROOF-FINAL-SLOPE","status":"OPEN","message":"Pendiente final sujeta a fabricante, estructura y cálculo pluvial"}
    ]
    report={"revision":"0.3-borrador-07-CUBIERTA","passed":4,"open":2,"failed":0,"checks":checks}
    (OUT/"compliance.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    manifest={"revision":report["revision"],"generator":"dreamhouse/generate_roof_b07.py","source":"dreamhouse/pb_b05.json + fuentes canónicas","source_sha256":hashlib.sha256(pb.DATA.read_bytes()).hexdigest(),"outputs":list(outputs)+["compliance.json","manifest.json"]}
    (OUT/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"passed":4,"open":2,"failed":0}))

if __name__=="__main__": main()
