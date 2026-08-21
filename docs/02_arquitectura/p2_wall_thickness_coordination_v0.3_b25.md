# P2 Wall-Thickness Coordination Audit

**Status:** issued for D-080 schematic architectural coordination; not for construction  
**Version:** 0.3-b25 / R22  
**Date:** 2026-08-21  
**Decision:** D-080  
**Source model:** `dreamhouse/p2_b25_delta.json`  
**Supersedes:** b24/R21 for P2 wall classification, nominal thickness and schematic
wall details only

## Outcome

The predecessor P2 wall strategy was physically possible but economically
undifferentiated. It assigned a 250 mm twin-frame acoustic wall to ordinary dry
partitions and combined a separate 300 mm double-frame facade concept with a project
budget that already carried insulated metal facade panels. D-080 retains enhanced
separation where privacy justifies it and removes duplicated construction elsewhere.

The active coordination values are realistic nominal zones, not tender dimensions:

| Type | Nominal | Duty | Schematic basis and control |
| --- | ---: | --- | --- |
| P2-W01A | 90 mm | Dry boundary within one suite | 12.5 + 64 + 12.5 = 89 mm illustrative sum; 50 mm wool in the frame |
| P2-W01B | 200 mm | Suite-to-suite or suite-to-common | 12.5 + 12.5 + 64 + 20 clear + 64 + 12.5 + 12.5 = 198 mm; two independent insulated frames |
| P2-W02 | 150 mm | Wet/service wall | Coordination reserve; increase locally only where selected soil/waste stacks, valves or support frames require it |
| P2-W02S | 200 mm | Sauna/hot-side wall | Coordination reserve; separate thermal, moisture, ventilation and fire detail required |
| P2-W03 | 200 mm | Stair/protected core | Space reserve only; final thickness follows a tested fire/smoke assembly and SC-01 interfaces |
| P2-W04R | 200 mm | Retained bedroom ends at X=21 | Uses P2-W01B intent; guard/truss/fire interfaces remain separate |
| P2-W05 | 230 mm | Exterior P2 envelope | 100 mm insulated corrugated panel test value + 40 mm clear zone + 64 mm independent lining + 12.5 + 12.5 mm boards = 229 mm |
| P2-W06 | 90 mm | Reversible F1/F2 closure | Upgrade if the final fire/smoke or security strategy makes it more than a temporary dry divider |

## Architectural verification

### Fitness for the selected second floor

- P2 is residential/private above a large technical hall. Privacy therefore belongs at
  suite and hall interfaces, not at every closet or same-suite boundary.
- P2-W01A is deliberately excluded from suite-to-suite and suite-to-common boundaries.
  P2-W01B preserves twin-frame decoupling and four outer board layers at those boundaries
  while reducing the former 80 mm central void to a practical 20 mm clear separation.
- Wet rooms receive a wider service zone than ordinary dry walls. Sauna/hot-side walls
  remain a separate type because heat, vapour, membranes, timber support, ventilation
  and fire cannot be resolved by ordinary bathroom drywall.
- The protected stair is not specified by thickness alone. P2-W03 holds 200 mm until
  occupancy classification and the fire/smoke strategy select a tested assembly.
- P2-W05 retains the desired rugged corrugated exterior and smooth private interior. It
  uses the insulated metal panel as the weather shell and one independent inner lining,
  avoiding a redundant second exterior frame. Primary-column boxes may thicken locally.

### Market and technical reality check

- A current official USG Latin America reference system uses a 63.5 mm stud and one
  12.7 mm board per face, with insulation, as a normal light partition. Its published
  test data are useful evidence that the 90 mm P2-W01A geometry is ordinary rather than
  exotic. The project does **not** adopt its stated rating or span without matching the
  exact local tested system.
- Official Kingspan Colombia data list insulated wall panels in 40, 50, 60, 80, 100 and
  150 mm thicknesses. A 100 mm panel is therefore a credible coordination test value,
  but the manufacturer requires project engineering and provides load/span tables by
  product. D-080 keeps the final 80–120 mm selection open.
- Camacol Valle's official dry-construction manual identifies 12.7 mm gypsum board as a
  standard board dimension and routes acoustic and fire evidence through ASTM E90/E413
  and NTC 1480/ASTM E119 testing. D-080 therefore makes no rating claim from layer count
  or thickness alone.
- Current Colombian governance requires the architectural design to define nonstructural
  element types and performance and requires qualified professional seismic design of
  those elements. The wall schedule is an architectural coordination input, not that
  signed engineering design.

## Quantity and economy screening

The b25 centreline model measures the following shared-boundary runs. Door/opening widths
are deducted only when a modeled opening connects the same two spaces; the result is a
screening quantity, not a bill of quantities.

| Type | Gross shared boundary | Modeled openings | Screening opaque run |
| --- | ---: | ---: | ---: |
| P2-W01A | 31.94 m | 22.80 m | 9.14 m |
| P2-W01B | 15.89 m | 3.70 m | 12.19 m |
| P2-W02 | 49.52 m | 5.70 m | 43.82 m |
| P2-W02S | 8.45 m | 2.90 m | 5.55 m |
| P2-W03 | 12.60 m | 1.00 m | 11.60 m |
| **Total** | **118.40 m** | **36.10 m** | **82.30 m** |

Using those opaque runs, predecessor thicknesses and the unchanged centreline geometry,
the differentiated internal walls reduce the schematic wall footprint by approximately
**4.26 m²**. Reducing the 48.00 m exterior perimeter from 300 to 230 mm screens another
**3.36 m²**, and reducing the 10.55 m retained hall edge from 250 to 200 mm screens
approximately **0.53 m²**. The combined order-of-magnitude recovery is therefore about
**8.15 m² of plan footprint** before intersections, column boxes, finishes and field
tolerances.

This is not a booked monetary saving. P2-W05 may need a thicker or higher-cost core;
P2-W02 may widen at stacks; P2-W03 may change with fire design; and acoustic doors,
head tracks, seals, perimeter fire stopping and mock-ups can outweigh raw material
reductions. Chapters 09, 10, 14 and 23 must be remeasured against one coordinated scope
to avoid double counting facade and lining work.

## Mandatory gates before developed-design freeze

1. Confirm site/municipality, altitude, orientation and indoor design humidity; apply the
   current Colombian sustainable-construction climate method and complete a transient or
   otherwise professionally accepted condensation/drying analysis for P2-W05.
2. Resolve D-021 occupancy, fire and hazard separation; select tested P2-W02S, P2-W03,
   P2-W05 and any upgraded P2-W06 assemblies and compatible doors/penetrations.
3. Set acoustic criteria by adjacency; select a locally available tested P2-W01B system,
   doors and seals, then verify the complete installed junction with a full-height mock-up.
4. Confirm sanitary stack diameters, slopes, cleanouts, supports and valves before fixing
   local P2-W02 depth.
5. Measure selected-product mass and wall height; reconcile distributed and line loads
   with `partitions_p2_kpa`, slab, beams, edge members and diaphragm design under CF-009.
6. Engineer facade panel spans, girts, fasteners, wind reactions, corners, base, eaves,
   window perimeters, drainage, air sealing and primary-steel interfaces.
7. Obtain like-for-like local quotations for wall areas, openings, linings, seals,
   access, waste, mock-ups and phase remobilization before recognizing any saving.

## Sources

### Project sources

- Project Constitution v1.4.
- D-057, D-059, D-063, D-074 and D-080 in the active Decision Register.
- P2 b24/R21 predecessor model and P2 b25/R22 controlled delta.
- Cost-control chapters 09, 10, 14 and 23; CF-009 structural coordination conflict.

### External primary technical references

- [Ministerio de Vivienda — NSR technical amendment, nonstructural elements and professional responsibilities](https://www.minvivienda.gov.co/sites/default/files/consultasp/Anexo%20t%C3%A9cnico_4.pdf)
- [Ministerio de Vivienda — Resolución 0194 de 2025](https://minvivienda.gov.co/normativa/resolucion-0194-2025)
- [Camacol Valle — Manual de Construcción Liviana en Seco, Chapter 3](https://camacolvalle.org.co/wp-content/uploads/2022/07/Capitulo-3.pdf)
- [Camacol Valle — Manual de Construcción Liviana en Seco, Chapter 11](https://camacolvalle.org.co/wp-content/uploads/2022/07/Capitulo-11.pdf)
- [USG Latin America — Sistema Normal reference assembly](https://assemblies-tools.usg.com/content/usgcom/spanish/products/systems/sistema-normal.html)
- [Kingspan Colombia — KingWall technical data sheet](https://www.kingspan.com/content/dam/kingspan/kip-latam/colombia/sistema-de-paneles-para-fachada/kingwall/kingspan-kingwall-ft-v2-es-co.pdf)

External references establish plausibility and required verification routes only. They do
not select a manufacturer, warrant local availability or transfer published performance
to a different assembly.
