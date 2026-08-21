# P2 Refined Exterior Envelope — b15/R12

**Status:** historical D-059 envelope concept; 300 mm double-frame build-up superseded by
D-080/P2 b25; not for construction
**Version:** 0.3-draft-15-P2 / R12  
**Date:** 2026-08-13  
**Sources:** Constitution hard rules 11, 19, 22 and 23; D-057–D-059; p2 b14/R11
predecessor  
**Supersedes:** b14/R11 as the current P2 plan and D-034's 180 mm study thickness on P2
exterior walls only  
**Superseded by:** D-080/P2 b25 for current P2-W05 thickness and integrated
insulated-panel-plus-lining build-up; refined private-interior intent retained
**Approval pending:** architect of record, envelope/building-physics professional,
structural engineer, fire/life-safety professional, window supplier, selected-system
manufacturers and representative mock-up review

## Architectural intent

Private P2 must feel quiet, finished and residential rather than like an occupied corner
of the warehouse. The hall and exterior can retain an honest industrial expression, but
P2 rooms and circulation must not expose corrugated sheet, cold-formed studs, primary
steel, bracing, membranes, ducts, pipes, power/data infrastructure or miscellaneous
services.

D-059 creates **P2-W05** on the three exterior P2 edges:

- south / Side A at Y=0;
- north / Side B at Y=18; and
- rear / east façade at X=36.

The X=21 edge remains P2-W04 under D-058 and is not part of P2-W05.

## Economical double-frame principle

P2-W05 is coordinated at **300 mm nominal overall thickness**. Its illustrative
outside-to-inside sequence is:

1. corrugated-metal rainscreen, visible outside only;
2. nominal 20 mm drained and ventilated cavity;
3. continuous weather-resistive air/water layer over nominal 11 mm exterior sheathing;
4. nominal 90 mm outer light-gauge frame with 90 mm glass wool;
5. nominal 50 mm clear decoupling and service cavity;
6. nominal 100 mm independent inner frame with 100 mm glass wool;
7. nominal 12.7 mm accepted reclaimed gypsum board as concealed interior mass; and
8. nominal 12.7 mm new gypsum board as the smooth visible finish.

The illustrative sum is approximately 297 mm and is drawn as 300 mm nominal. Final
locally available profiles and boards may adjust the clear cavity while retaining the
double-frame, drained-rainscreen and smooth-interior principles.

This arrangement concentrates spending on ordinary components that do more than one
job: the corrugated sheet is durable and economical outside; both wool-filled frames
improve thermal and acoustic separation; the clear cavity decouples the room lining and
holds services; recovered board adds concealed mass; and only the visible board must be
new and finish quality.

## Openings and continuity

Every scheduled P2 exterior window remains. Each opening must receive a coordinated
head, sill and reveal with positive drainage, flashing, continuous air/water seals,
thermal-break continuity, acoustic perimeter seals and structure capable of transferring
wind without distorting the window. The rear retractable-stair opening receives the same
envelope discipline but remains an unapproved egress reserve.

At corners, slab edge, primary steel, roof and eaves, continuity of drainage, air control,
insulation and interior finish must be drawn explicitly. Primary steel may sit within the
wall zone but cannot appear as an unfinished element inside P2.

## Moisture and fire caution

No generic polyethylene vapour barrier is adopted. Boyacá climate, selected site,
indoor humidity, sauna proximity, material permeability, thermal bridges and drying
direction must be assessed before locating any vapour-control layer. The final assembly
also requires wind design, fire and smoke criteria, cavity barriers, corrosion control,
insect closures and maintainable drainage.

No U-value, condensation clearance, STC, Rw, field DnT,w, fire rating or wind capacity is
claimed by this schematic decision.

## Geometry effects

The gross 18 × 15 m P2 envelope and room tessellation do not move. The b15 model deducts
300 mm at the exterior faces when calculating net dimensions. Child bedrooms remain
within D-042 at 22.07 m² and 21.65 m² net, a 0.42 m² difference; the narrowest declared
circulation remains 1.20 m clear. These are coordination outputs, not construction
dimensions.

## Required gates before construction

- Complete climate-specific hygrothermal and condensation analysis.
- Select local profiles, sheathing, membranes, insulation, boards and rainscreen fixings.
- Design wind resistance, stud spacing, fasteners, anchors and primary-steel interfaces.
- Detail windows, corners, roof/eaves, slab edge, flashings, drainage and air seals.
- Resolve fire, smoke, combustibility and cavity-barrier requirements.
- Calculate installed mass and compare it with structural allowances.
- Build and inspect a representative full-height wall/window mock-up.

## Controlled files

- `dreamhouse/p2_b15.json`
- `dreamhouse/generate_p2_b15.py`
- `planos/conceptual_v0.3_b15_p2/DH-ARQ-PLN-002-R12_P2-COORDINATED.svg`
- `planos/conceptual_v0.3_b15_p2/DH-ARQ-DIA-001-R12_P2-ACCESS-EGRESS.svg`
- `planos/conceptual_v0.3_b15_p2/DH-ARQ-DET-002-R12_OWNER-PRIORITIES.svg`
- `planos/conceptual_v0.3_b15_p2/DH-ARQ-DET-003-R12_P2-ACOUSTIC-PARTITION.svg`
- `planos/conceptual_v0.3_b15_p2/DH-ARQ-DET-004-R12_P2-HALL-EDGE.svg`
- `planos/conceptual_v0.3_b15_p2/DH-ARQ-DET-005-R12_P2-EXTERIOR-WALL.svg`
- `planos/conceptual_v0.3_b15_p2/compliance.json`
- `planos/conceptual_v0.3_b15_p2/manifest.json`

Reproduce the issue with:

```bash
python -m dreamhouse.generate_p2_b15
```
