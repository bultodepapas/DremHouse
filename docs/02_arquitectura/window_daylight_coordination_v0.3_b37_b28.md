# Window and daylight coordination — PB b37 / P2 b28

**Status:** adopted schematic architectural coordination under D-083; not for procurement
or construction  
**Version:** 0.3-b37-PB / 0.3-b28-P2  
**Date:** 2026-08-21  
**Document revision:** 0.4 — migration note updated on 2026-10-03; original design issue retained<br>
**Decision:** D-083  
**Canonical geometry source:** `dreamhouse/window_daylight_d083.json`  
**Drawing sources:** `planos/conceptual_v0.3_b37_pb/` and
`planos/conceptual_v0.3_b28_p2/`

## Connected consumer migration — 2026-10-03

The [migration and extension guide](../06_gestion_y_obra/connected_coordination_migration_and_extension_guide.md)
connects native plans, elevations, workstation/bedroom details and the schedule to one
resolved source snapshot. Review drawing identities remain distinct from this adopted
D-083 issue. The generated inventory declares annotation coverage and unresolved interfaces;
CF-013 doors cannot acquire a measured placement from the earlier sketches.

## Connected review and source ownership

D-084 now resolves this adopted opening geometry through the PB b37 and P2 b28 loaders
into one candidate review. The [connected workflow](../06_gestion_y_obra/connected_coordination_workflow.md)
explains how validated repository JSON changes regenerate the applicable plans,
elevations, window details, quantities and findings. SVG is generated evidence; it is
not an editing interface. A candidate does not overwrite this adopted source issue or
promote a new drawing to `planos/actual/`.

The five P2 bedroom `W-*` identities and their PB-elevation `GLZ-*` aliases describe the
same five openings. The connected quantity ledger counts each once and reproduces
the 123.84 m² vertical-glazing and 23.04 m² rooflight baseline below. The dining study
remains excluded from adopted totals; it may appear with a distinct study status in the
read-only candidate review. Review quantities are measured schematic geometry, without
approved prices, procurement quantities or glass/frame specifications.

### Increment 02 implementation note — 2026-10-02

The [D-084 increment 02 record](../06_gestion_y_obra/connected_coordination_increment_02.md)
adds eight isolated review SVGs. `window-sections.svg` is a schematic section projection
of GLZ-WS-A only; it does not detail all openings or revise the D-083 geometry, the
worktop/window design intent or the source authority stated below. The connected check
compares current PB workstation spans and sills with the captured workstation data. It
does not verify frame design, load transfer, drainage, flashing or envelope performance.
The review remains outside the published drawing catalog and is not an approval or
construction issue.

All sill/head values in the tables below are relative to the corresponding finished
floor. PB uses project Z=0 and P2 uses Z=+3.80 m: the bedroom-window sill/head therefore
resolve to project Z=+3.85/+6.75 m. The source inventory documents this conversion.
The current connected rules do not calculate daylight, glare, thermal performance or
engineered window interfaces; the professional gates below remain open.

## Adopted schematic outcome

D-083 concentrates glass where it materially improves bedrooms and permanent desk use.
It does not turn the hall into a transparent box and does not lower the technical-workbench
windows. All adopted openings use simple repeated modules and remain subject to site,
professional design and quotations.

### P2 bedroom-window family

| Opening | Room / edge | Width | Height | Sill | Head | 1.20 m modules |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| W-H1 | Child 1 / south | 3.60 m | 2.90 m | +0.05 m | +2.95 m | 3 |
| W-H2 | Child 2 / north | 3.60 m | 2.90 m | +0.05 m | +2.95 m | 3 |
| W-G | Guest / north | 3.60 m | 2.90 m | +0.05 m | +2.95 m | 3 |
| W-M-LAT-A | Primary / south | 3.60 m | 2.90 m | +0.05 m | +2.95 m | 3 |
| W-M-REAR | Primary / rear | 2.40 m | 2.90 m | +0.05 m | +2.95 m | 2 |

The five openings total **48.72 m²** of schematic bedroom glazing. The 50 mm sill is a
visual near-floor-to-ceiling datum, not a declaration that unprotected full-height glass
is safe. Laminated safety glass, fall protection, restrictors, operable panels, insect
screens, cleaning access and any rescue function require professional design. One product
need not use one glass sheet: economical replaceable panelization is the governing intent.

The wellness opening and the D-082 operable rescue window remain unchanged. The primary
suite uses a three-module side opening plus a two-module rear opening, subject to privacy,
solar and curtain coordination after site selection.

### PB desk-window datum

| Opening | Width | Sill | Retained head | Height | Modules |
| --- | ---: | ---: | ---: | ---: | ---: |
| GLZ-WS-A | 7.20 m | +0.75 m | +3.80 m | 3.05 m | 6 |
| GLZ-WS-B | 3.00 m | +0.75 m | +2.55 m | 1.80 m | 3 |

Both workstation-window sills now share the **+0.75 m** worktop datum. The worktop does
not bear on the window: retain a removable **30–50 mm** shadow/service gap, independent
secondary steel, independent flashings and drainage, and no furniture load into the frame
or facade girts. Coordinate final mullions with monitor sightlines and operable panels.

The Project Car and RC/electronics technical-window sills remain at **+0.90 m**. Their
workbench duties, variable module heights and service requirements are not ordinary desk
conditions and were deliberately excluded from the lowering.

## Quantities and unadopted study

The coordinated active schedule measures:

- 41.76 m² PB technical glazing;
- 27.36 m² PB workstation glazing;
- 54.72 m² P2 vertical windows, including retained wellness and rescue openings;
- **123.84 m² active vertical glazing total**; and
- 23.04 m² retained rooflights, scheduled separately.

Relative to the immediately preceding active geometry, D-083 adds **4.035 m²** to the five
bedroom openings and **1.530 m²** to the two desk openings: **5.565 m²** net additional
vertical glazing before frame deductions. These measurements are cost alerts, not an
approved budget increase.

`GLZ-DINING-STUDY-B` is a separate 4.80 × 1.80 m / 8.64 m² study only. It is excluded from
active drawings and totals until the real site establishes whether view, solar exposure,
privacy, structure and cost justify it.

## Open professional gates

Before developed-design freeze:

1. select the site and establish cardinal orientation, views, privacy and obstructions;
2. calculate daylight, glare, overheating and natural ventilation room by room;
3. design safe glass, fall protection, restrictors and operable areas;
4. design headers, jambs, girts, anchors, drift interfaces and wind resistance;
5. resolve U-value, thermal bridges, condensation, acoustic performance, seals, drainage
   and flashings;
6. coordinate curtains, blackout, insect screens, furniture, monitors and cleaning; and
7. build one representative sill/desk/facade mock-up and obtain comparable local quotes.

The generated window schedule and details are dimensional coordination evidence only.
They do not select profiles, glass make-up, hardware, coatings or installation methods.
