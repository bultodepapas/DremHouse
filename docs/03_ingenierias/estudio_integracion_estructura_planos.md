# Structural-to-Drawing Integration Study — E1 Screening

**Status:** active coordination audit; research evidence, not a calculation memorandum or
professional design
**Version:** 0.5
**Date:** 2026-08-13
**Sources:** D-039, D-043, D-045, D-046, D-047, D-048, D-050, D-051, D-052,
D-053; architectural drafts b05–b11; `pb_b05.json`; `p2_b10.json`;
`rooflight_b11.json`; `structure_system.json`;
`roof_truss_space.json`; `e1_screening_space.json`; generated E0 and E1 structural
evidence
**Approval pending:** responsible structural engineer, architect of record, fire and
life-safety professional, geotechnical engineer, fabricator/erector, and owner

> **Authority boundary.** The integrated drawing is a visual index of active geometry,
> adopted schematic intent, calculated screening results, and unresolved gates. It does
> not select D-019, establish PE-1 quantities, or authorize procurement, fabrication,
> erection, foundations, or construction.

## 1. Purpose

This study reconciles the architectural drafts, the adopted P2 gravity intent, the
neutral roof-truss test specimen, and the E1 multi-phenomenon screens in one controlled
view. It answers three questions:

1. Which geometry and load paths are actually supported by current sources?
2. Which numerical checks have been executed, and what did they prove narrowly?
3. Which missing inputs still prevent a structural system from being selected or issued?

D-048 records the owner's new vertical-continuity and stair-frame study direction. It
does not select the complete structural system or convert the geometry screen into
professional design.

D-050 changes the active P2 room and door organization but deliberately preserves the
D-048 stair footprint and four corner coordinates. D-051 adds a rear retractable-stair
reserve, D-052 defines the desired architectural expression of the X=21 edge truss, and
D-053 relocates the rooflight pair to the centre of the double-height hall. The structural
generators now read `p2_b10.json` and `rooflight_b11.json`; their deterministic re-run
retains the same four compatible stair-frame lines and previously declared conflicts.

## 2. New integrated evidence sheet

The current visual synthesis is
[DH-EST-E1-001 — Integrated Structural E1 Screening](../../planos/estructura/DH-EST-E1-001_SINTESIS-ESTRUCTURAL.svg).
It is generated from the active JSON sources and the same `run_screening()` calculation
used by the E1 report. Its four principal readings are:

- **Plan:** M60 test grid, D-053 rooflights, D-043/D-045 P2 gravity path, diaphragm
  demand, and four explicitly uncoordinated trial lateral bays.
- **Reference truss:** exact six-panel modified-Warren grammar—25 members and 14 nodes—
  with physical top- and bottom-chord restraint assumptions drawn separately.
- **Evidence gate:** every narrow calculation result is paired with a separate design
  status; every system-level status remains `BLOCKED`.
- **Details:** generic connection components, trial base/footing sensitivity, erection
  envelope, and elevated-temperature sensitivity.

The earlier E0 sheets remain valid as historical coordination evidence. The E1 sheet
does not overwrite them or imply that their trial sections have become selected.

The focused companion sheet is
[DH-EST-E1-002 — Vertical Continuity and Stair-Enclosure Frame](../../planos/estructura/DH-EST-E1-002_CONTINUIDAD-VERTICAL-ESCALERA.svg).
It audits every current Great Wall candidate against P2 rooms and glazing, identifies the
four compatible stair-corner lines, separates enclosure-frame resistance from stair
flights, and shows why the protected portal and rear discharge control the transverse
lateral-system topology.

## 3. Reconciled geometry and status

| Item            |                                                            Current value shown | Authority/status                                               |
| --------------- | -----------------------------------------------------------------------------: | -------------------------------------------------------------- |
| Hall            |                                                                36.00 × 18.00 m | D-003 DCV; not a frozen construction dimension                 |
| P2              |                                                       X=21.00→36.00 m; +3.80 m | D-004 / active coordination DCV                                |
| Mono-pitch roof |                                                      7.20→7.80 m across Y=0→18 | D-039 provisional DCV                                          |
| Roof test lines |                                                           X=0/6/12/18/24/30/36 | neutral M60 specimen under D-047; not D-019 selection          |
| Rooflights      | two 4.80 × 2.40 m openings at X=8.10→12.90 m; combined centre X=10.50/Y=9.00 m | D-053 active geometric hypothesis                              |
| P2 edge         |                                             full-depth truss line at X=21.00 m | D-043 schematic gravity intent; design pending                 |
| Hybrid wall     |                                             concealed steel frame at X=31.50 m | D-043 gravity intent; no longitudinal lateral role assigned    |
| P2 beams        |                                    six lines at Y=1.5/4.5/7.5/10.5/13.5/16.5 m | D-045 E0 hypothesis only                                       |
| Rear overhang   |                                                       X=31.50→36.00 m = 4.50 m | D-045 E0 hypothesis; must be compared with a real rear support |
| Stair enclosure |                                                X=31.50→36.00 m; Y=7.40→11.00 m | D-048 four-column geometry study; system design blocked        |

## 4. Integrated load paths

### 4.1 Roof gravity and uplift specimen

The sheet draws the neutral M60, six-panel, variable-depth modified-Warren truss used by
the E1 screening. The top chord follows the canonical roof line; depth varies from about
0.99 m at the supports to 1.80 m at midspan. Trial sections are HSS120×120×6 chords and
HSS100×100×6 webs. The calculated specimen mass is about 1,241 kg per truss.

These sections are **not selected**. The model assumes top-chord out-of-plane restraint
at 1.50 m and bottom-chord restraint at 6.00 m. The drawing marks both restraint systems
because a numerical unbraced length is not a physical load path: qualified purlin
connections, roof-plane bracing, bottom-chord braces, collectors, and erection sequence
must make those assumptions real.

The maximum screened member force is 209.8 kN, maximum support downward reaction is
79.7 kN, maximum combined interaction is 0.653, and the member B1 sensitivity is 1.255.
Those values support a reproducible specimen screen only.

### 4.2 P2 gravity intent through the Great Wall

D-043 establishes the gravity concept and D-045 establishes the current E0 analytical
hypothesis:

1. Six longitudinal trial beams run continuously from X=21.00 to X=36.00 m.
2. They are supported by the full-depth edge truss at X=21.00 m and the concealed hybrid
   wall frame at X=31.50 m.
3. They continue 4.50 m beyond the wall as a free rear overhang because no support at
   X=36.00 m is currently defined.
4. The transfer over the Great Wall must develop negative moment; it is not a simple
   bearing detail.
5. Trial hidden-column locations are Y=0/2.4/7.4/11.0/13.4/18.0 m so the stair portal and
   doors remain available for architectural coordination.

The Great Wall is **not assigned longitudinal X-direction resistance**. Its possible
transverse contribution, eccentricity, torsion, collectors, joints, fire protection,
and foundations remain professional-design tasks.

### 4.3 D-048 vertical continuity and stair-enclosure frame

The PB and P2 stair geometry aligns exactly at X=31.50→36.00 m and Y=7.40→11.00 m.
The deterministic audit reaches the following narrow result:

- **retain for full-height study:** GW-STAIR-S (31.50, 7.40), GW-STAIR-N (31.50,
  11.00), STAIR-REAR-S (36.00, 7.40), and STAIR-REAR-N (36.00, 11.00);
- **reject at current coordinates:** GW-SOUTH because of W-M-LAT-A glazing, GW-Y2.4
  because it crosses M-D, GW-Y13.4 because it crosses G-C, and GW-NORTH because of W-G
  glazing.

The preferred study is therefore a four-column **stair-enclosure frame**, reusing two
Great Wall columns and adding two rear columns. The two side planes at Y=7.40 and 11.00
can study diagonal bracing for X-direction resistance. Full diagonals cannot simply be
placed in the front X=31.50 or rear X=36.00 planes because they contain the protected
stair portal and direct-discharge door; those planes require a coordinated moment or
segmented-frame study.

The stair flights and stringers receive no primary lateral-system credit. They must use
drift-compatible connections unless their stiffness and resulting actions are explicitly
included in the global model. This follows the conceptual separation in the official
[2020 NEHRP Recommended Provisions](https://www.fema.gov/sites/default/files/2020-10/fema_2020-nehrp-provisions_part-1-and-part-2.pdf)
and the fixed-versus-slotted stair damage classifications in
[FEMA P-58-2](https://www.fema.gov/sites/default/files/documents/fema_p-58-2-se_volume2_implementation.pdf).
These are technical cross-checks only; the applicable Colombian NSR-10 requirements and
the responsible engineer govern the project.

Continuing columns to roof level also does **not** make them automatic gravity props for
the current roof specimen. The roof trusses remain on fixed X lines and X=31.50 is not an
M60 line. P2/roof collectors may be studied, but roof gravity support, landing restraints,
torsional response, member and joint design, bases, foundations, fire protection,
clearances, and erection remain unresolved. The official
[AISC lateral-systems guidance](https://www.aisc.org/architecture-center/resources/engineering-basics/lateral-systems/)
is used only to reinforce the early coordination principle that doors and windows govern
whether diagonal or rigid-frame solutions are feasible.

### 4.4 Lateral path and diaphragm

The E1 force-distribution hypothesis gives a preliminary governing lateral force of
157.8 kN. Dividing it among two wall lines and two active bays per line gives a trial
L50×5 tension-brace demand of 63.2 kN and a gross-yield ratio of 0.622. This does not
validate any location, reversal behavior, brace connection, or collector.

The corresponding roof-diaphragm demand is 8.77 kN/m with a 39.5 kN chord force. The
manufacturer system, strength, assembled stiffness, fastener pattern, sidelaps,
rooflight framing, collectors, and connections are absent. The sheet therefore draws
the demand arrows but leaves diaphragm design blocked.

## 5. E1 evidence gate

| Phenomenon                        |                                           Executed screen | What remains unresolved                                                      |
| --------------------------------- | --------------------------------------------------------: | ---------------------------------------------------------------------------- |
| HSS local/biaxial stability       |            local ratio 0.696; axial 0.325; combined 0.653 | complete member/code design and global model                                 |
| Chord local bending               |                                   12.51 kN·m; ratio 0.369 | real load introduction and joint geometry                                    |
| Member second order               |                       reduced-Euler ratio 0.203; B1 1.255 | 3D direct analysis, imperfections, notional loads                            |
| Generic gusset parts              |                    demand 209.8 kN; component ratio 0.387 | HSS wall limit states, eccentricity, access, seismic hierarchy               |
| Trial lateral bays                |                         brace demand 63.2 kN; ratio 0.622 | locations, reversal/buckling, joints, collectors, openings                   |
| Vertical continuity / stair frame |             four compatible corners; two reused + two new | orthogonal system, torsion, drift joints, collectors, bases, fire and egress |
| Roof diaphragm                    |                                  8.77 kN/m; chord 39.5 kN | manufacturer-tested assembly and opening framing                             |
| Fire sensitivity                  |               0.65 at 400°C; 1.05 at 550°C; 2.84 at 700°C | D-021 rating, scenario, section factor, tested protection                    |
| Erection                          | hook 15.8 kN; sling 9.1 kN; at least two transport pieces | crane chart/radius, lift lugs, splices, wind limit, temporary bracing        |
| Trial footing                     |        2.0×2.0×0.5 m; qmax 37.3 kPa under assumed 150 kPa | geotechnics, lateral/moment allocation, RC punching/flexure/shear            |
| Trial base plate                  |           300×300×20 mm; centered compression ratio 0.057 | anchors, shear, moment, grout, pedestal, concrete limit states               |

A `PASS*` label in the drawing means only that the listed narrow calculation passes its
declared hypothesis. It is deliberately paired with `DESIGN BLOCKED`.

## 6. Coordination conflicts still visible

1. **Trial lateral bays versus openings.** The four force-distribution bays are shown at
   the ends only to expose the hypothesis. They conflict with technical glazing,
   upper-floor glazing, front openings, P2 use, and possibly rooflight collectors.
2. **Rooflights versus secondary steel.** D-053 moves the pair across the X=6 and X=12 m
   grid lines around the exact centre of the double-height hall. The architectural centre
   is now controlled, but framing becomes more demanding: purlin trimmers, diaphragm
   shear transfer, local wind zones, drainage crickets, and secondary overflows require a
   new coordinated detail.
3. **P2 edge truss versus architecture.** D-052 accepts one large exposed X=21 truss and
   rejects small decorative trusses, while keeping the mini-deck view primary. Depth,
   panel points, bedroom/door interfaces, ceiling, fire separation, and MEP remain open.
4. **Great Wall joints versus finish.** A continuous timber/acoustic reading does not
   remove the need for transfer-beam depth, stiffeners, erection access, tolerances, fire
   protection, and replaceable joints behind the finish.
5. **Rear overhang versus real support.** D-045 requires comparison of the continuous
   overhang with a defined rear support before profiles or connections can be frozen.
6. **Foundation sensitivity versus site reality.** The drawn pad and plate are dimension
   studies only; site, groundwater, settlement, seismic/wind base actions, uplift, and the
   complete reinforced-concrete/anchor design are unknown.
7. **Stair core versus protected egress.** D-048 improves the possible continuous load
   path, but braces, column encasement, landing joints, deflected shapes, bases, and
   collectors must preserve stair width, headroom, fire rating, and direct discharge.
8. **Retractable stair versus life safety and rear structure.** D-051 reserves a second
   route from the common Phase 2 lobby and clears the D-048 corner coordinate. Its landing,
   deployment loads, façade support, corrosion, guards, fail-safe operation, and emergency
   acceptance remain unproved; the reserve receives no exit credit at E1.

## 7. Explicit corrections to the previous integration study

This revision corrects superseded derived statements under the project precedence rules:

- The prior text said that no structural layer existed in the drawings. Dedicated E0
  structural sheets and the two E1 sheets now exist; architectural b05–b11
  remain separate drafts and are not silently converted into structural issue drawings.
- The prior text described **three** P2 beams, a wall continuing as a shear core, and a
  strip foundation. Those statements were not supported by the active model or later
  decisions. D-043/D-045 and `structure_system.json` v0.3 govern: **six** beam lines, no
  assigned longitudinal lateral role, and no adopted foundation type.
- Historic descriptions of `GRAN-MURO` as “preferred” are not a D-019 system selection.
  Only the P2 gravity intent is active; trial sections, weights, lateral behavior, and
  foundations remain open.

The corrections remain precedence work. The owner's vertical-continuity direction is
recorded as D-048, the active architectural reorganization as D-050/D-051, the edge-truss
brief as D-052, and the centred rooflight geometry as D-053, rather than being hidden in
the drawings.

## 8. Required progression to design

Before an E2 structural issue, the responsible team must provide at least:

- site and municipality, normative wind/seismic actions, topography, and exposure;
- geotechnical investigation and foundation criteria;
- coordinated 3D geometry with all openings, support conditions, deck assemblies, and
  load-bearing nonstructural interfaces;
- complete second-order lateral analysis, diaphragm/collector design, and torsion;
- coordinated stair-enclosure frame analysis, landing drift interfaces, egress clearances,
  and fire-protection details;
- member, connection, HSS wall, base plate, anchor, and reinforced-concrete design;
- D-021 fire criteria and tested protection system;
- fabrication, transport, lifting, temporary stability, and erection engineering; and
- signed calculations and drawings by the responsible Colombian professionals.

## 9. Anti-false-precision rule

Every dimension and result on the E1 sheets retains the authority of its source. Decimal
precision does not convert a hypothesis into a construction value. The SVG is a
calculation-linked research drawing and must remain visibly marked **NOT FOR
CONSTRUCTION** until the unresolved gates are closed and a professional issue replaces
it.
