# PB corner-start technical workbenches — draft 29

**Status:** active schematic coordination hypothesis under D-073; not for construction
**Version:** 0.3-draft-29-PB
**Date:** 2026-08-20
**Scope:** longitudinal start of the Project Car and RC/electronics wall benches
**Source:** explicit owner correction after visual review of PB b28 and D-073.

## Correction

Both 9.00 m technical benches now begin at X=0.18 m, the interior face of the front wall.
The Project Car bench follows Side A and the RC/electronics bench follows Side B. Their
predecessor X=0.55 m positions left 0.37 m unusable end gaps that contradicted the intended
permanent, building-integrated character.

| Bench | Wall | Start | End | Depth |
| --- | --- | ---: | ---: | ---: |
| Project Car | Side A | X=0.18 m | X=9.18 m | 0.75 m |
| RC/electronics | Side B | X=0.18 m | X=9.18 m | 0.75 m |

Both benches remain below their technical windows and retain the D-068 secondary-steel
rail/replaceable-worktop family. D-072's lift test position remains unchanged.

## Front-corner coordination

The 0.75 m bench depths leave nominal 0.27 m plan gaps to the adjacent 4.80 m front-door
openings. These gaps prove that the rectangles do not overlap; they do not select a door
frame, track, guard or safe hand/maintenance clearance. The developed detail must:

- resolve the bench end, front-wall return, door jamb, track and seals together;
- avoid an inaccessible dirt trap at either corner;
- keep bench services removable and isolated;
- preserve facade drainage, air/water control and corrosion/fire protection; and
- transfer bench and cabinet loads to verified independent backing, not door/window frames.

## Parametric evidence

PB b29 checks exact X=0.18 m corner starts, retained 9.00 m lengths, common X=9.18 m ends
and at least 0.25 m nominal plan separation from both adjacent front-door openings. Door,
bench and equipment interfaces remain professional coordination gates.

The issue is in `planos/conceptual_v0.3_b29_pb/`; its source is
`dreamhouse/pb_b29_delta.json` and it is generated deterministically with
`python -m dreamhouse.generate_pb_b29`.
