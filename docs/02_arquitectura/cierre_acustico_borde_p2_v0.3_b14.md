# P2 Hall-Edge Acoustic Enclosure — b14/R11

**Status:** D-058/P2-W04 continuity partially superseded by D-063 at Y=5.00–12.45;
P2-W04R thickness/build-up superseded by D-080 at both bedroom ends; historical and not
for construction<br>
**Version:** 0.3-draft-14-P2 / R11  
**Date:** 2026-08-13  
**Sources:** Constitution hard rule 11; D-052, D-057, D-058; p2 b13/R10 predecessor  
**Supersedes:** b13/R10 as the current P2 plan; retains its P2-W01 assembly basis  
**Superseded by:** b25/R22 for current P2 wall thickness; P2-W04R remains active only at
Y=0.00–5.00 and Y=12.45–18.00 and references 200 mm P2-W01B intent<br>
**Approval pending:** architect of record, structural engineer, acoustic consultant,
fire/life-safety professional, glazing/guarding designer, selected-system manufacturer,
and full-height mock-up review

## Correction adopted

The previous plan showed the X=21 edge and the mini-deck acoustic glazing, but it did not
draw a continuous wall between private P2 and the double-height hall/workshops. That
representation contradicted the requirement for a private, acoustically enclosed upper
floor and left a direct airborne-noise flank toward the bedrooms and family spaces.

D-058 corrects the omission with **P2-W04**, running the complete **18.00 m** from Y=0.00
to Y=18.00 at X=21.00. It is full height from the P2 floor to the coordinated roof soffit
or head. The mini-deck acoustic glazing **GLZ-DECK**, from Y=5.25 to Y=8.20 in plan, is
the only planned interruption. No open gallery or unscheduled doorway is permitted.

## Assembly and continuity

Opaque P2-W04 portions use the P2-W01 principle fixed by D-057:

- 250 mm nominal overall thickness;
- two independent insulated light-gauge frames;
- nominal 50 mm glass wool in each frame;
- one accepted reclaimed concealed gypsum-board layer and one new visible finish layer
  on each side; and
- a clear central cavity without a third leaf or rigid bridging.

The wall is only as effective as its weakest junction. Maintain continuous seals at the
floor track, lateral returns, roof/head, glazing perimeter, structural supports, outlets,
ducts, pipes, cable routes and fire stopping. Do not compress insulation, connect the two
frames with uncontrolled blocking, or use the truss as a shortcut across the cavity.

## Truss, glazing and edge interface

D-052 remains active: one large industrial truss may be exposed as a deliberate object
seen from the hall. D-058 changes how that object must be coordinated. The enclosure
governs acoustic continuity; the truss should remain hall-side or use specifically
designed isolated and sealed junctions. Its topology, support points, movement,
connections and fire protection remain open under CF-010.

GLZ-DECK must be developed as one coordinated acoustic-glazing and edge-protection
system. Glass build-up, frame, seals, height, guarding resistance, deflection and fire
requirements are not selected by this issue.

## Geometry effects

The gross 18 × 15 m P2 envelope and room tessellation do not move. The b14 model assigns
the correct 250 mm hall-edge thickness when calculating net dimensions of spaces that
touch X=21. All validation controls still pass, including child-bedroom equivalence and
the declared 1.20 m minimum clear circulation.

## Required gates before construction

- Coordinate the wall head with roof slope, movement and deflection.
- Resolve truss supports and connections without puncturing or rigidly bridging P2-W04.
- Establish required fire/smoke separation and tested systems.
- Detail GLZ-DECK frame, seals, guarding and edge support.
- Coordinate all MEP penetrations and fire/acoustic seals.
- Measure actual wall and glazing areas and check structural dead-load allowance.
- Build and inspect a full-height representative mock-up before repetition.

No STC, Rw, field DnT,w or fire rating is claimed. The issue freezes enclosure intent
and coordination geometry only; it does not authorize procurement or construction.

## Controlled files

- `dreamhouse/p2_b14.json`
- `dreamhouse/generate_p2_b14.py`
- `planos/conceptual_v0.3_b14_p2/DH-ARQ-PLN-002-R11_P2-COORDINATED.svg`
- `planos/conceptual_v0.3_b14_p2/DH-ARQ-DIA-001-R11_P2-ACCESS-EGRESS.svg`
- `planos/conceptual_v0.3_b14_p2/DH-ARQ-DET-002-R11_OWNER-PRIORITIES.svg`
- `planos/conceptual_v0.3_b14_p2/DH-ARQ-DET-003-R11_P2-ACOUSTIC-PARTITION.svg`
- `planos/conceptual_v0.3_b14_p2/DH-ARQ-DET-004-R11_P2-HALL-EDGE.svg`
- `planos/conceptual_v0.3_b14_p2/compliance.json`
- `planos/conceptual_v0.3_b14_p2/manifest.json`

Reproduce the issue with:

```bash
python -m dreamhouse.generate_p2_b14
```
