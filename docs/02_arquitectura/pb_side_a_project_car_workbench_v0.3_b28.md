# PB Side A project-car workbench — draft 28

**Status:** retained D-072 wall/lift basis; bench start coordinates superseded by D-073/PB b29; historical coordination evidence; not for construction
**Version:** 0.3-draft-28-PB
**Date:** 2026-08-20
**Scope:** project-car workbench, Side A wall/window relationship and lift test envelope
**Source:** explicit owner correction after visual review of PB b27 and D-072.

## Correction

PB b28 fixes the nominal 9.00 m project-car workbench directly against the Side A
perimeter wall. The predecessor showed it as a floating bar across the car bay even though
the D-068 family intended permanent wall-integrated technical furniture. The corrected
bench occupies X=0.55–9.55 m and Y=0.18–0.93 m, below the X=1.50–8.70 m project-car
technical window. The RC/electronics bench remains against Side B.

## Active test geometry

| Item | Test geometry | Coordination status |
| --- | ---: | --- |
| Project-car bench | 9.00 × 0.75 m; worktop +0.90 m | fixed against Side A |
| Technical window | X=1.50–8.70 m; sill +0.90 m | retained predecessor opening |
| Lift/vehicle envelope | X=1.60–8.00 m; Y=1.05–6.95 m | shifted 0.60 m inward |
| Graphic bench/lift gap | 0.12 m | non-overlap test only |
| Central pedestrian axis | begins at Y=7.00 m | lift test envelope ends at Y=6.95 m |

The shift allows the plan to communicate the requested wall relationship without drawing
the lift through the bench. It does not prove operation: 0.12 m is deliberately recorded
as a graphic separation, not a person, door, tool-cart or maintenance clearance.

## Construction and service logic

Use the D-068 economical family: replaceable worktop on a dedicated bolted secondary-steel
service rail with accessible power, task lighting, source extraction and compressed-air
coordination. Bench loads may not be assigned to the window frame, cladding or unverified
facade girts. Coordinate local backing, corrosion/fire protection, drainage and air/water
seals at the Side A wall/window interface.

## Mandatory next verification

- Overlay the selected lift's posts, arms, locks, controls and manufacturer working zones.
- Test the real project car with doors open, hood/trunk access and wheel/arm positions.
- Add loaded cabinets, mobile tool carts and a safe escape/maintenance route.
- Confirm window sill, operable modules, bench splash/impact protection and cleaning.
- Coordinate extraction, power, compressed air, data and task lighting with accessible
  isolation and no concealed interference with facade drainage.

## Parametric evidence

PB b28 checks Side A wall contact, full technical-window coverage, the pair of opposing
wall-side technical benches, at least 0.10 m graphic bench/lift separation and termination
of the lift envelope before the central axis. The real equipment interface remains an
explicit `OPEN` gate.

The issue is in `planos/conceptual_v0.3_b28_pb/`; its source is
`dreamhouse/pb_b28_delta.json` and it is generated deterministically with
`python -m dreamhouse.generate_pb_b28`.
