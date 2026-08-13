# E1 Multi-Phenomenon Structural Screening

**Status:** research screening complete; design remains blocked
**Version:** 0.2
**Date:** 2026-08-12
**Input SHA-256:** `47c32728c61adedfea223d7bfca6aa8aeb0a8d453f9e9fbd13fb2b0bd80a8c2e`
**Authority:** not for system selection, pricing, fabrication, or construction

## Reference test specimen

The neutral specimen is M60 WARREN_MODIFIED with 6 panels, 1.80 m centre depth, and HSS120x120x6 / HSS100x100x6 chord/web trial sections. It is a reproducible test case, not a selected structural system.

## Screening matrix

| Phenomenon                            | Calculated result                                                               | Current status                                                                                                                 |
| ------------------------------------- | ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| HSS local and biaxial buckling        | local slenderness 0.696; axial 0.325                                            | trial screen passes; design unresolved                                                                                         |
| Chord local bending                   | M=12.51 kN·m; local bending ratio=0.369; combined ratio=0.653                   | included; joint/load-introduction detail unresolved                                                                            |
| Member second order                   | reduced-Euler ratio 0.203; B1 screen=1.255                                      | member screen included; global direct analysis unresolved                                                                      |
| Trial gusset components               | demand 209.8 kN; capacity 542.9 kN; ratio 0.387                                 | generic components pass; HSS wall limit states unresolved                                                                      |
| Trial longitudinal braced bays        | diagonal demand 63.2 kN; L50×5 gross-yield ratio 0.622                          | trial bar strength passes; locations, buckling in reversal, connections, collectors, and openings unresolved                   |
| Vertical continuity / stair enclosure | 4 compatible corner lines; 2 existing Great Wall + 2 new rear columns           | geometry screen passes; complete orthogonal system, collectors, bases, drift joints, fire, and egress unresolved               |
| Roof diaphragm                        | required unit shear 8.77 kN/m; chord force 39.5 kN                              | blocked by manufacturer system, openings, fasteners, collectors, and stiffness                                                 |
| Erection                              | hook load 15.8 kN; sling tension 9.1 kN; minimum transport pieces 2             | crane chart, lift lugs, weather limit, splices, and temporary bracing unresolved                                               |
| Trial foundation sensitivity          | gravity qmax 37.3 kPa; gravity bearing ratio 0.249; uplift net vertical 69.6 kN | no foundation adopted; geotechnical and RC/anchor design unresolved                                                            |
| Trial base plate                      | concrete-bearing ratio 0.057; required/provided plate thickness 4.1/20.0 mm     | centred compression components pass; anchor group, shear, moment, grout, pedestal, and concrete anchor limit states unresolved |

## Lateral-stability assumptions

The member screen assumes top-chord lateral restraint every 1.50 m and bottom-chord restraint every 6.00 m. The first requires qualified purlin-to-chord restraint and a complete roof-plane load path; the second is a new physical bracing requirement under uplift and is not present merely because it appears in the model.

The four trial longitudinal braced bays are only a force-distribution hypothesis. Their locations have not been reconciled with the technical windows, upper-floor glazing, doors, or rooflights, and compression under load reversal has not been assigned to a tension-only L-angle.

## Vertical continuity and stair-enclosure frame

The PB and P2 stair enclosure is geometrically aligned from X=31.50 to 36.00 m and Y=7.40 to 11.00 m. The screen retains four foundation-to-roof corner lines: GW-STAIR-S and GW-STAIR-N reuse two current Great Wall columns, while STAIR-REAR-S and STAIR-REAR-N are new rear lines. The other four Great Wall candidates are rejected by P2 rooms, full-height glazing, or failure to coincide with an enclosure corner.

The preferred study concept is an independent four-column stair-enclosure frame. Its two side planes can study diagonal bracing for longitudinal action; the front stair portal and rear discharge door block full-bay diagonals, so transverse resistance needs a coordinated moment or segmented frame. The stair flights and stringers are not assigned as primary lateral members: they require drift-compatible connections unless their stiffness and actions are included explicitly in the global model.

Column continuity to roof level does not automatically create a roof gravity support. The current roof specimen runs on fixed X lines and has no selected frame at X=31.50 m. A diaphragm collector connection may be studied, but roof gravity support, torsional response, landing restraints, connections, fire protection, foundations, and construction sequence all remain unresolved.

## Fire sensitivity—not a fire rating

The ambient governing ratio is conservatively divided by the Appendix 4 material-retention factors. This does not model a time–temperature curve, section factor, thermal gradients, restraint, load redistribution, or protection thickness.

| Trial steel temperature | Fy retention | E retention | Conservative strength ratio | Trial result            |
| ----------------------: | -----------: | ----------: | --------------------------: | ----------------------- |
|                  400 °C |        1.000 |       0.700 |                       0.653 | passes sensitivity only |
|                  550 °C |        0.625 |       0.455 |                       1.046 | fails sensitivity       |
|                  700 °C |        0.230 |       0.130 |                       2.841 | fails sensitivity       |

D-021 must establish occupancy, required fire-resistance period, fire scenarios, compartmentation, and a tested protection system before fire design can close.

## What remains genuinely blocked

- D-017 site, municipality, topography, normative wind and seismic actions
- geotechnical investigation and groundwater/settlement parameters
- complete three-dimensional lateral model and direct second-order analysis
- coordinated four-column stair-enclosure frame, orthogonal lateral planes, drift-compatible stair joints, diaphragm collectors, column bases, fire-rated enclosure, and egress clearances
- roof and floor deck manufacturer strength, stiffness, fasteners, sidelaps, and openings
- connection geometry including HSS local limit states and seismic demand hierarchy
- D-021 occupancy, fire-resistance target, fire scenario, and tested protection system
- fabricator splice strategy, crane chart/radius, temporary bracing, lift lugs, and weather limits
- reinforced-concrete footing, anchors, base plates, punching, shear, flexure, and development design

## Interpretation

The new calculations remove the former one-axis Euler and node-only load simplifications from the roof-truss shortlist. They do not resolve the complete building. Member checks can pass while diaphragm, HSS joints, global stability, erection, fire, and foundations remain open; those open gates prevent D-019, PE-1 quantities, procurement, and construction use.
