# Shared PB/P2 stair-core coordination — PB b33 / P2 b24

**Status:** D-074 stair geometry remains active; P2 b24 publication superseded by
D-080/P2 b25 for walls only; not for construction
**Version:** 0.3-b33-PB / 0.3-b24-P2  
**Date:** 2026-08-21  
**Decision:** D-074  
**Primary model:** [`dreamhouse/stair_core.json`](../../dreamhouse/stair_core.json)  
**Sources:** D-028, D-048, D-061, D-074, active PB/P2 geometry, and NSR-10 Title K
as modified by Decree 340 of 2012

## Controlled outcome

PB and P2 now use one coordinate system, one stair enclosure, one dogleg arrangement and
one set of four structural reservations. The plans no longer contain independently drawn
stair symbols. PB reads the lower flight **up to P2**; P2 reads the upper flight **down to
PB**. Both drawings are generated from SC-01 and carry its revision as SVG metadata.

This outcome coordinates schematic geometry only. It does not approve an exit, fire
enclosure, steel member, joint, base, foundation, guard, handrail, finish, erection method
or construction detail.

## Shared coordinate control

| Element | X range / coordinate | Y range / coordinate | Z / role |
| --- | ---: | ---: | --- |
| Stair enclosure | 31.50–36.00 m | 7.40–11.00 m | PB to roof coordination zone |
| Schematic clear rectangle | 31.70–35.80 m | 7.60–10.80 m | 4.10 × 3.20 m |
| Lower flight ST-F1 | 31.70–34.40 m | 7.70–9.10 m | +0.00 to +1.90 m; up toward +X |
| Upper flight ST-F2 | 31.70–34.40 m | 9.30–10.70 m | +1.90 to +3.80 m; up toward −X |
| Intermediate landing ST-L1 | 34.40–35.80 m | 7.70–10.70 m | +1.90 m |
| PB Great Wall portal | X=31.50 m | lower-flight access zone | platform outside enclosure |
| P2 family-distributor door | X=31.50 m | 9.50–10.50 m | upper-flight top platform |

The transverse clear-width closure is exact:

`0.10 side clearance + 1.40 flight + 0.20 gap + 1.40 flight + 0.10 side clearance = 3.20 m`.

The longitudinal clear-depth closure is also exact:

`2.70 flight run + 1.40 intermediate landing = 4.10 m`.

## Stair arithmetic

The +3.80 m schematic floor-to-floor height is divided into 22 equal risers:

- riser: `3.80 / 22 = 0.172727 m = 172.7 mm`;
- two flights: `11 + 11 risers`;
- goings: `10 per flight × 270 mm = 2.70 m run`;
- comfort/code screen: `2R + G = 2(172.7) + 270 = 615.5 mm`;
- intermediate landing: `+1.90 m`;
- schematic pitch: `atan(172.7 / 270) = 32.61°`;
- clear flight width and intermediate-landing depth: `1.40 m` each.

The official 2012 Title K amendment requires fixed permanent evacuation stairs, gives
minimum-width rules by occupancy, requires `600 mm ≤ 2R+G ≤ 640 mm`, requires landing
depth at least equal to stair width, limits rise between landings to 3.60 m, and requires
2.05 m minimum headroom. SC-01 passes only the plan/arithmetic portions that can be tested
without a section. Occupancy classification and professional application remain open.
See the official [Decree 340 of 2012](https://minvivienda.gov.co/sites/default/files/normativa/0340%20-%202012.pdf).
The Ministry states that NSR-10 is still the Colombian framework while an update is being
developed; the adopted regulation and later amendments must be checked again at licensing.
See [Ministry construction-resistance information](https://www.minvivienda.gov.co/viceministerio-de-vivienda/espacio-urbano-y-territorial).

## Four-column steel-frame logic

| ID | X (m) | Y (m) | Coordination role |
| --- | ---: | ---: | --- |
| GW-STAIR-S | 31.50 | 7.40 | reuse Great Wall south jamb line |
| GW-STAIR-N | 31.50 | 11.00 | reuse Great Wall north jamb line |
| STAIR-REAR-S | 36.00 | 7.40 | new rear south line |
| STAIR-REAR-N | 36.00 | 11.00 | new rear north line |

The four reservations form an independent enclosure-frame study from foundations to roof.
The stair flights and stringers do not brace the building. Their connections must
accommodate calculated inter-storey drift unless the stair stiffness and force transfer
are deliberately included in the global structural model. Landing beams may restrain
columns only after their stiffness, joints and force path are analysed. No member size is
selected; the 0.30 m plan markers are coordination zones, not adopted steel sections.

The side planes at Y=7.40 and Y=11.00 can continue to study bracing. The Great Wall and
rear planes contain doors, so they require opening-aware moment or segmented-frame studies.
Fire protection, diaphragm collectors, torsion, bases, anchors, foundations, tolerances,
erection and temporary stability remain blocked.

## CF-011 — rear discharge is not resolved

A conventional two-flight dogleg places the rear intermediate landing at +1.90 m. The
predecessor rear opening was drawn at PB grade in the same plane without a stair section.
Those conditions cannot both be true. The new PB drawings therefore mark the opening as a
level conflict and do not call it a functioning direct discharge.

The next comparison must test at least:

1. a revised stair topology that preserves usable width and both PB/P2 access platforms;
2. a separately protected grade-level exit passage with verified 2.05 m headroom; and
3. a controlled enlargement or redistribution of the core if the first two are not viable.

Each alternative must include a coordinated longitudinal section, fire/egress review,
four-column structural analysis, usable-area effect, steel quantity, enclosure quantity,
foundation effect and cost comparison. D-028 remains active; D-074 does not silently
waive it.

## Issued evidence

- PB plan: `planos/conceptual_v0.3_b33_pb/DH-ARQ-PLN-001-R11_PB-STAIR-CORE.svg`
- PB rear-core detail: `planos/conceptual_v0.3_b33_pb/DH-ARQ-DET-001-R05_PB-STAIR-CORE.svg`
- P2 plan: `planos/conceptual_v0.3_b24_p2/DH-ARQ-PLN-002-R21_P2-COORDINATED.svg`
- P2 access diagram: `planos/conceptual_v0.3_b24_p2/DH-ARQ-DIA-001-R21_P2-ACCESS-EGRESS.svg`
- Machine checks: adjacent `compliance.json` and `manifest.json` files

The current structural continuity sheet remains valid only for the unchanged four column
coordinates and its published limitations. It does not close SC-01 headroom, landing,
member, connection, fire or discharge gates.
