# PB living / TV on the Side B perimeter wall — draft 27

**Status:** active schematic coordination hypothesis under D-071; not for construction  
**Version:** 0.3-draft-27-PB  
**Date:** 2026-08-20  
**Scope:** ground-floor living group, 100-inch TV wall, viewing geometry and dining relationship  
**Source:** explicit owner correction after visual review of PB b26 and D-071.

## Correction

PB b27 retains the useful parts of D-070—the removal of the legacy abstract furniture,
the explicit living/dining programme, the clear pedestrian axis and the solid Side B hall
bay—but rejects the freestanding X=21 media partition. The television belongs directly
to a perimeter wall of the industrial hall.

The selected wall is Side B at Y=17.82 m, between the workstation-2 bay and the X=21.00 m
upper-floor edge. This position uses an already solid hall-wall field, avoids the main
Side A glazing and keeps the 4.00 m central route unobstructed. It does not add a room or
divide living from dining.

## Active test geometry

| Item | Test geometry | Coordination status |
| --- | ---: | --- |
| TV mounting field | Side B; X=16.40–20.80 m; 4.40 × 3.80 m | existing perimeter wall, local backing pending |
| TV envelope | 100 in, 16:9; 2.214 × 1.245 m | owner equipment, product pending |
| TV centre | X=18.60 m; +1.25 m above finished floor | ergonomic test value |
| Viewing distance | 4.10 m | seated-eye test distance |
| AV console | 3.40 × 0.45 × 0.45 m | accessible built-in test envelope |
| Main sofa | 4.00 × 1.05 m | faces Side B |
| Chaise | 1.10 × 2.70 m | living-group return |
| Living rug | 4.60 × 6.00 m | begins at Y=11.35 m |
| Dining table | 3.60 × 1.30 m; 12 seats | independent group beside kitchen |

All living furniture remains beyond Y=11.00 m and east of the workstation-2 envelope
ending at X=16.00 m. The dining table remains in the domestic band beside the kitchen; it
no longer depends on a reverse-face sideboard or any interior wall.

## Wall, structure and enclosure logic

The 4.40 m field is an interior finish and mounting zone on the existing Side B exterior
wall, not a second wall. Provide locally designed backing that transfers the real TV and
mount loads to verified members without loading window frames or assuming that facade
girts are adequate. Keep insulation, vapour control, air/water seals, fire performance,
acoustic isolation and corrosion protection continuous around every service penetration.

## AV and comfort holds

- Confirm actual TV dimensions, mass, VESA pattern, bracket eccentricity, ventilation and
  replacement path before fabrication.
- Keep power, data, spare conduits, speakers and active equipment accessible without
  dismantling the exterior-wall build-up.
- Coordinate Side B daylight, reflections and blackout after site selection. The solid
  TV field may not silently become another window.
- Retain workstation-2 glazing at X=13.00–16.00 m and its facade/drainage separation from
  the TV field.

## Parametric evidence

PB b27 checks the Side B perimeter-wall coincidence, absence of an internal media
partition, 100-inch 16:9 geometry, 4.10 m viewing distance, pedestrian-axis clearance,
workstation-2 clearance, independent 12-seat dining group and solid Side B hall bay.
Facade backing, AV/MEP and glare remain explicit `OPEN` gates.

The issue is in `planos/conceptual_v0.3_b27_pb/`; its source is
`dreamhouse/pb_b27_delta.json` and it is generated deterministically with
`python -m dreamhouse.generate_pb_b27`.
