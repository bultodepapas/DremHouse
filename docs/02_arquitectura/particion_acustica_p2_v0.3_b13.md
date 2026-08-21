# P2 Acoustic Partition Coordination — b13/R10

**Status:** historical D-057 assembly; thickness superseded by D-080/P2 b25; not for
construction
**Version:** 0.3-draft-13-P2 / R10  
**Date:** 2026-08-13  
**Sources:** D-034, D-042, D-050, D-057; p2 b10/R09 predecessor  
**Supersedes:** the 150 mm study thickness for ordinary dry interior P2 partitions only  
**Superseded by:** D-080/P2 b25 for current dry-wall classification, thickness and
build-up; privacy and reuse intent retained in P2-W01B
**Approval pending:** architect of record, structural engineer, fire/life-safety
professional, selected-system manufacturer, and full-height mock-up review

## Architectural decision

P2-W01 is the frozen Design Control Value for ordinary dry interior upper-floor
partitions. It is coordinated at **250 mm nominal overall thickness**. The assembly uses
mass, absorption, airtightness, and structural decoupling without relying on expensive
specialty products.

From Room A to Room B:

1. 12.7 mm nominal new gypsum board as the visible finish;
2. 12.7 mm nominal reclaimed gypsum board as a concealed mass layer;
3. approximately 60 mm independent light-gauge metal frame with 50 mm nominal glass-wool
   infill;
4. approximately 80 mm clear central air cavity;
5. approximately 60 mm second independent frame with 50 mm nominal glass-wool infill;
6. 12.7 mm nominal reclaimed concealed board; and
7. 12.7 mm nominal new visible finish board.

The illustrative layer sum is 250.8 mm and is drawn/dimensioned as **250 mm nominal**.
Final locally available stud and board dimensions may adjust the clear central gap, but
must retain the nominal total, two physically independent frames, insulation in both
frames, and no gypsum board in the centre cavity.

## Scope boundary

P2-W01 applies to ordinary dry partitions between bedrooms, closets, shared dry rooms,
filters, and circulation. The following remain separate wall types and are not silently
converted to P2-W01:

- exterior and façade walls;
- sauna hot-side and other wet-area build-ups;
- protected-stair and fire-rated enclosures;
- shafts and equipment enclosures; and
- structural, transfer, and bracing walls.

The plan uses a separate dashed graphic for these unresolved wet/hot or protected wall
interfaces. Their 200 mm predecessor thickness remains a provisional study value, not an
approved construction build-up.

## Why the reused board is inside the finished faces

Reclaimed board is useful here as low-cost concealed mass. It is not placed as a third
leaf in the middle of the wall: the central cavity remains clear so that the two frames
stay decoupled. Reclaimed sheets must be dry, clean, sound, free of mould and
delamination, capable of holding the required fasteners, staggered from the visible-board
joints, and sealed continuously at the perimeter. New board remains the exposed finish on
both room faces.

## Plan effect and verified adjustment

Applying the thicker partition to b10/R09 initially reduced the guest-suite filter to
1.10 m clear and therefore failed the project's 1.20 m circulation control. Revision
b13/R10 rebalances the Phase 2 band without enlarging P2:

- the Phase 2 lobby becomes 1.45 m gross and **1.20 m clear**;
- the guest filter becomes 1.45 m gross and **1.20 m clear**;
- the child-bedroom net areas remain 22.98 m² and 22.53 m², a 0.45 m² difference within
  D-042;
- the guest bedroom, bathroom, and wardrobe remain inside their coordinated programme
  bands;
- the wellness/sauna reserve remains 16.1 m² gross and still fits the 2.40 m sauna; and
- the gross P2 envelope remains exactly 270.000 m².

The model closes at **21 PASS · 0 FAIL · 3 OPEN**. The three open items remain the
professional second-exit review, X=21 edge-truss design, and site/orientation-dependent
glazing design.

## Mandatory coordination before construction

- Select locally available studs and boards while retaining the declared assembly
  principles and nominal overall thickness.
- Detail head-of-wall movement, seismic restraint, floor-edge support, junctions, and
  deflection compatibility.
- Coordinate acoustic doors, drop seals, perimeter seals, back-to-back outlets, ducts,
  pipes, cable trays, and fire stopping.
- Confirm any required fire rating using a tested assembly accepted by the responsible
  professionals; reclaimed board cannot be assumed to preserve a listed rating.
- Recheck the structural partition dead-load allowance using actual products and measured
  wall lengths.
- Build one full-height mock-up and inspect the reused board, wool fit, airtightness, and
  absence of rigid bridges before repeating the wall.

No STC, Rw, field DnT,w, or fire rating is claimed by this schematic decision. The target
is robust low-cost isolation; performance must be verified after product selection and,
where warranted, by field testing.

## Controlled files

- `dreamhouse/p2_b13.json`
- `dreamhouse/generate_p2_b13.py`
- `planos/conceptual_v0.3_b13_p2/DH-ARQ-PLN-002-R10_P2-COORDINATED.svg`
- `planos/conceptual_v0.3_b13_p2/DH-ARQ-DIA-001-R10_P2-ACCESS-EGRESS.svg`
- `planos/conceptual_v0.3_b13_p2/DH-ARQ-DET-002-R10_OWNER-PRIORITIES.svg`
- `planos/conceptual_v0.3_b13_p2/DH-ARQ-DET-003-R10_P2-ACOUSTIC-PARTITION.svg`
- `planos/conceptual_v0.3_b13_p2/compliance.json`
- `planos/conceptual_v0.3_b13_p2/manifest.json`

Reproduce the issue with:

```bash
python dreamhouse/generate_p2_b13.py
```
