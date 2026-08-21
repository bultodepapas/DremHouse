# Restored ground-floor domestic layout — PB b34

**Status:** active schematic coordination basis; not for construction  
**Version:** 0.3-b34-PB / PLN-001-R12  
**Date:** 2026-08-21  
**Decision:** D-077  
**Sources:** PB b32 domestic/vehicle study; D-071; D-073; D-074/SC-01; owner visual
review dated 2026-08-21

## Outcome

PB b34 corrects the visual and spatial regression introduced when PB b33 was generated
from PB b29 instead of the later b32 study. It combines the preferred b32 domestic and
Project Car arrangement with the complete b33 stair-core coordination. No independent
redrawing of the stair or its structure occurs.

The active schematic relationship is:

- Side A, X=21.15–31.20 m: one 10.05 × 0.75 m full-span kitchen wall.
- Side A, X=22.40–29.60 m: one dry 7.20 × 1.25 m island with eight test seats, a
  1.35 m working aisle and at least 1.50 m on its social side.
- Side B: one centred 3.20 × 1.10 m table for 12 people, arranged 5+5+2, within a
  symmetric 5.40 × 3.30 m envelope that gives 1.10 m around the table.
- The dining centre is (26.25, 14.41); it sits opposite the kitchen across the clear
  4.00 m perceptual axis rather than being compressed beside a short island.
- The complete Project Car/lift test group is centred at (5.34, 3.965), with equal
  1.96 m longitudinal residuals inside the usable technical bay.

The D-071 living group and Side B perimeter-wall television, both D-073 9.00 m
corner-start workbenches, the mirrored workstations and all front-door controls remain
unchanged.

## Stair and four-column relationship

PB b34 imports SC-01 directly from `dreamhouse/stair_core.json`. The enclosure remains
X=31.50–36.00 m / Y=7.40–11.00 m and uses the same four foundation-to-roof reservations
as P2:

| Reservation | X (m) | Y (m) |
| --- | ---: | ---: |
| GW-STAIR-S | 31.50 | 7.40 |
| GW-STAIR-N | 31.50 | 11.00 |
| STAIR-REAR-S | 36.00 | 7.40 |
| STAIR-REAR-N | 36.00 | 11.00 |

The kitchen wall stops 0.30 m before the Great Wall/core plane. Dining and island also
stop on the hall side of X=31.50 m. The 22-riser, 20-going dogleg, lower-flight PB access,
four-column IDs and coordinates therefore remain concordant with P2 b24/R21.

## Mathematical and code controls

The generated compliance report has 73 passing checks, 11 explicitly open checks and no
failures. It verifies the exact domestic geometry, separation from SC-01, the shared stair
footprint, lower-flight access, all four columns, centred vehicle/lift group, clear axis,
room arithmetic and inherited hard rules.

Passing a check is not construction approval. Headroom, fire/smoke enclosure, guards,
handrails, stringers, landing beams, drift-compatible connections, bases, foundations and
the CF-011 rear-discharge level conflict remain professional design gates.

## Cost and product hold points

D-077 resolves the schematic spatial choice but does not close D-024. The 7.20 m island
is 50% longer than the 4.80 m allowance in cost item `20.02`; the combined 17.25 m wall
and island length is 23.2% above the 14.00 ml countertop allowance in `20.03`. Chapter 20
must be remeasured and quoted before design freeze. The island remains dry to limit MEP,
maintenance and cost unless a later recorded decision changes that strategy.

Real appliances, joinery modules, daylight, end routes, lift, vehicle, doors, arms, tool
carts and maintenance clearances remain open. No price or target change is recognized.

## Generated evidence

- Plan: `planos/conceptual_v0.3_b34_pb/DH-ARQ-PLN-001-R12_PB-INTEGRATED-RESTORATION.svg`
- Compliance: `planos/conceptual_v0.3_b34_pb/compliance.json`
- Provenance: `planos/conceptual_v0.3_b34_pb/manifest.json`
- Model delta: `dreamhouse/pb_b34_delta.json`
- Generator: `dreamhouse/generate_pb_b34.py`

The plan is the active schematic coordination visualization; it is not dimensional,
procurement, fabrication or construction authority.
