# PB living, dining and media wall — draft 26

**Status:** superseded by D-071/PB b27 for the TV wall and living arrangement; historical coordination evidence; not for construction
**Version:** 0.3-draft-26-PB
**Date:** 2026-08-20
**Scope:** ground-floor social hall, dining hinge, media wall and Side B hall-bay graphic
**Source:** owner visual review of PB b25, D-070, active programme and governing spatial sequence.

## Purpose

Replace the inherited abstract living-room symbol with a legible social composition. The
ground floor must show where people sit, what they face, how the 100-inch television meets
a real wall, how dining connects to the kitchen and how the 4.00 m central pedestrian
axis remains unobstructed.

PB b26 retains the D-069 workstations and cabinets unchanged. It supersedes PB b25 only
for the ground-floor social furniture and plan graphics, and Side B R08 only for the
unassigned dashed hall-bay alternative. Shell, core, kitchen equipment, workstations,
technical areas, roof and unaffected openings remain inherited controls.

## Corrected reading

The predecessor represented the living area as a 5.80 × 5.00 m rounded rectangle with
two parallel upholstered bars and a table labelled `CENTRE`. That assembly had no focal
wall or television and extended 1.70 m into the Y=7.00–11.00 m pedestrian axis. An empty
`LOUNGE / TRANSITION` territory and a dashed, unprogrammed Side B facade alternative made
the domestic sequence still less legible.

PB b26 removes those three graphics. The revised sequence is:

**technical atelier → breathing buffer → double-height living / TV lounge → media wall →
12-seat dining hinge → kitchen → Great Wall and service core.**

## Active test geometry

| Item | Test geometry | Coordination status |
| --- | ---: | --- |
| Media wall | X=20.75–21.00 m; Y=2.00–6.20 m; 4.20 × 3.80 m | partial wall aligned with P2 edge |
| TV envelope | 100 in, 16:9; 2.214 × 1.245 m | owner equipment, product pending |
| TV centre | +1.25 m above finished floor | ergonomic test value |
| Viewing distance | 3.90 m | seated-eye test distance |
| AV console | 3.40 × 0.45 × 0.45 m | accessible built-in test envelope |
| Main sofa | 3.50 m plus 2.45 m return | furniture test envelope |
| Dining table | 3.60 × 1.30 m; 12 seats | retained programme control |
| Dining sideboard | 3.80 × 0.40 m | reverse-face service element |

The rug, sofa, return, chairs, coffee table and media wall all terminate before Y=7.00 m.
The central route therefore remains a clear perceptual axis rather than a passage drawn
through furniture.

## Media-wall logic

The wall sits on the X=21.00 m transition between the double-height hall and the partial
upper floor. It gives the living room a focal plane without closing the central route. Its
living face uses a warm acoustic finish, matte screen background and accessible AV
console; its dining face provides a sideboard/service surface. One element therefore
clarifies living, dining and the section change without inventing another room.

Alignment with X=21.00 m does **not** make the wall part of the D-043 edge truss or any
primary load path. Treat its secondary frame, connections, deflection, fire strategy,
acoustic build-up and interfaces with the upper-floor edge as open structural design.

## AV, comfort and facade holds

- Confirm the selected television dimensions, mass, VESA/mount pattern, ventilation and
  replacement path; the 100-inch rectangle is an equipment envelope only.
- Provide accessible power, data, spare AV conduits, speaker routes and equipment cooling.
  Do not trap power supplies or connectors inside an inaccessible wall cavity.
- Coordinate screen luminance, reflections and daytime blackout with real site
  orientation. The main Side A glazing remains governed by open finding H-07.
- Retain the existing curtain-pocket concept as a coordination aid, not a selected blind
  or acoustic system.
- The Side B hall bay becomes solid in this issue; removing its dashed alternative does
  not freeze facade coating, insulation, structure or the final site response.

## Parametric controls and evidence

PB b26 adds fail-closed checks for pedestrian-axis clearance, separation from the Side A
workstation envelope, X=21.00 m wall alignment, the 100-inch 16:9 geometry, 3.90 m viewing
distance, dining clearances and removal of the Side B alternative opening. Structural,
AV/MEP and glare interfaces remain explicit `OPEN` gates.

The issued evidence is in `planos/conceptual_v0.3_b26_pb/`: the revised ground-floor plan,
the corrected Side B elevation, the interior media-wall coordination sheet,
`compliance.json` and `manifest.json`. The source delta is
`dreamhouse/pb_b26_delta.json`; generation is deterministic through
`python -m dreamhouse.generate_pb_b26`.
