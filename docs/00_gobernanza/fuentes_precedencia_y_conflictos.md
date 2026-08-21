# Sources, precedence, and conflicts

**Status:** active  
**Version:** 1.1
**Date:** 2026-08-21
**Language note:** controlled English translation under D-044; D-063 incorporated into
CF-009/CF-010 and D-074/CF-011 added without closing the fire/egress gate; D-077 updates
CF-006 without freezing products, MEP, joinery, or cost; D-078 changes Side A workstation
and glazing geometry without selecting structure, facade products or cost.

## Precedence

When sources conflict, the following order governs:

1. A later explicit owner decision, recorded and dated.
2. The active Project Constitution.
3. The most recent active document for the relevant discipline.
4. Conceptual plan v0.2 for dimensional control.
5. The consolidated concept document for intent and hard rules.
6. Technical budget v0.2 for the working cost target.
7. Historical documents.
8. Renders, evocative sketches, and AI-generated imagery.

Regulations, safety requirements, and designs signed by competent professionals take
precedence over any incompatible preference.

## Classification of original sources

The original files remain unchanged and in Spanish under `docs/BORN_Legacy/`.

| Source                                                            | Role                              | Status                           |
| ----------------------------------------------------------------- | --------------------------------- | -------------------------------- |
| `casa_bodega_boyaca_conclusiones_anteproyecto.md`                 | Intent, hard rules, and synthesis | Active conceptual source         |
| `Dream_House_Plano_Conceptual_v0.2.md`                            | Geometry and nominal areas        | Active for dimensional control   |
| `Dream House — Presupuesto Técnico y Control de Costos v0.2.docx` | Target and construction divisions | Active; low-to-medium confidence |
| `Dream_House_Presupuesto_Preliminar_v0.1.md`                      | Earlier feasibility estimate      | Historical / superseded          |

## Identified conflicts

### CF-001 — Total budget

- v0.1: planning range of COP 4.3–4.8 billion; reserve of COP 5.0 billion.
- v0.2: COP 941 million construction + 5% = COP 988.05 million; control ceiling of
  COP 1.0 billion.
- **Interim rule:** v0.2 is the active target because it explicitly supersedes v0.1, but
  it is not a validated figure. Do not commit scope, contracts, or financing against it
  until the economic gate defined in the master plan has been passed.
- **Status:** critical, open.

### CF-002 — “No rigid budget” versus COP 1.0 billion ceiling

The concept calls for efficiency without a rigid constraint, while cost plan v0.2 sets a
ceiling. Treat COP 1.0 billion as a provisional design constraint, not as a guaranteed
price or permission to reduce performance.

- **Decision required:** confirm whether COP 1.0 billion is an aspiration, a physical
  construction ceiling, or the total investment ceiling.
- **Status:** open.

### CF-003 — Suite areas

The conceptual narrative initially identifies 28–32 m² for each child's suite and
23–26 m² for the guest suite. Plan v0.2 assigns approximately 38 m² to each child's suite
and approximately 32–33 m² to the guest suite.

- **Interim rule:** the gross areas in plan v0.2 govern. The equality requirement applies
  to the usable bedroom areas of the two children.
- **Status:** resolved by precedence; verify against the net v0.3 plan.

### CF-004 — Rear service-core areas

The early narrative proposes 16–20 m² for storage, 7–9 m² for the homelab, and 5–6 m² for
the PB bathroom. Plan v0.2 distributes the 81 m² as follows: 22.5 + 10.8 + 20.7 + 10.8 +
16.2 m².

- **Interim rule:** plan v0.2 governs as the nominal gross allowance. v0.3 must
  demonstrate that the homelab and bathroom are not oversized at the expense of the main
  hall.
- **Status:** provisionally resolved.

### CF-005 — Service-core arithmetic

One concept review states that a 5.0 m depth would produce approximately 70 m² and a
4.5 m depth approximately 63 m². Those figures correspond to a width of 14 m. At 18 m,
the correct areas are 90 m² and 81 m² respectively.

- **Rule:** the active nominal core is 18 × 4.5 = **81 m²**.
- **Status:** error identified; correct in the next consolidation of the source.

### CF-006 — Kitchen island

The narrative proposes 3.6–4.0 × 1.10–1.25 m; plan v0.2 proposes 4.80 × 1.40 m.

- **Schematic geometric resolution:** D-077/PB b34 adopts a dry 7.20 × 1.25 m island with
  eight test seats, opposite a centred 12-seat dining group, as the active spatial
  coordination envelope. This later owner decision supersedes both earlier island
  envelopes for the active PB plan.
- **Remaining gates:** D-024 still governs final product and equipment selection. Verify
  appliance modules, MEP, end routes, seating ergonomics, joinery fabrication, daylight,
  maintenance and Chapter 20 cost before freezing or procuring the kitchen.
- **Status:** schematic geometry resolved by D-077; developed selection and cost remain
  open under D-024.

### CF-007 — Actual scope of the COP 988.05 million total

Document v0.2 calls this figure the “total construction cost,” not the total project cost.
It does not demonstrate inclusion of professional fees, studies, permits, utility
connections, taxes, special logistics, insurance, independent supervision, escalation,
or site contingencies.

- **Rule:** always separate physical construction, soft costs, equipment, site/external
  works, and the owner's reserve.
- **Status:** critical, open.

### CF-008 — Architectural Great Wall versus P2 structural support

D-033 defined the Great Wall at X=31.50 m as a continuous timber/acoustic surface with
flush doors. The initial E0 model silently converted it into a load-bearing wall and a
“longitudinal shear core,” without defining a frame, transfers, connections, or
compatibility with the five openings shown in the interior elevation.

- **Gravity resolution:** D-043 adopts a hybrid wall. The architectural finish remains,
  while a concealed steel frame supports P2 through a top beam and columns located within
  wall piers coordinated with the doors. D-045 fixes, for E0 v0.3 only, the hypothesis of
  continuous beams with a rear overhang, avoiding reliance on an undefined support at X=36.
- **Geometric reservation:** the conceptual 0.20 m thickness may increase; it does not
  override requirements for connections, fire protection, tolerances, or acoustics.
- **Lateral-system reservation:** because the wall lies in the X=31.50 m plane and extends
  along Y, it does not automatically provide longitudinal X stability. Do not omit façade
  bracing, diaphragm action, or collectors until the E1 model is complete.
- **Status:** authority conflict resolved by D-043 for gravity support; detailed design
  and the lateral function remain open.

### CF-009 — D-057/D-059 P2 walls versus structural dead-load and wind allowances

D-057 fixes a 250 mm nominal P2 dry-partition assembly with two metal frames, four total
gypsum-board layers, and glass wool in both frames. D-058 originally applied that opaque
principle to the full 18.00 m X=21 hall edge as P2-W04; D-063 now removes it from
Y=5.00–12.45 and retains P2-W04R only at the two bedroom ends. D-059 adds the 300 mm nominal P2-W05
double-frame exterior envelope on the other three edges, including sheathing, rainscreen,
two insulated frames and interior boards. The structural screening model still
uses a global `partitions_p2_kpa` allowance rather than wall lengths and actual product
masses or wind reactions, and the issued E0/E1 structural sheets predate P2 b15/R12.

- **Architectural rule:** P2 b19/R16 governs current P2 wall geometry under D-057–D-063.
- **Structural hold point:** do not infer that the existing partition allowance covers
  P2-W01/P2-W04R/P2-W05 or the new guard/edge system. Measure wall lengths, openings and
  guard/edge loads; select local products;
  calculate installed mass including frames/boards/insulation/sheathing/rainscreen, and
  compare the result with the allowance and local concentrations. Design P2-W05 studs,
  sheathing, fasteners and attachments for wind before the next structural issue.
- **Publication rule:** the current structural sheets remain screening evidence and may
  not be presented as coordinated construction design for D-057–D-063.
- **Status:** open; responsible structural engineer and architect of record must close it
before developed-design freeze.

### CF-010 — D-052 exposed edge truss versus D-063 open family balcony

D-052 asks for one large exposed industrial truss at X=21. D-063 now opens the family
frontage from Y=5.00 to 12.45 and requires a continuous guard at the floor edge, while
P2-W04R remains at both bedroom ends. The truss, guard, slab edge and retained walls do
not yet have a coordinated structural, movement or fire-protection detail.

- **Interim architectural rule:** the 7.45 m family frontage remains visually open and
  continuously guarded. P2-W04R closes only the bedroom ends. GLZ-DECK is removed.
- **Engineering hold point:** coordinate truss depth, supports, connections, fire
  protection, roof movement, retained wall heads, edge beam, guard anchors and MEP before
  freezing either system. No guard or architectural edge may be assumed structural.
- **Status:** open; architect of record, structural engineer, acoustic consultant and
  fire/life-safety professional must close the interface before developed-design freeze.
  Hall-to-family acoustic isolation is intentionally relinquished by the owner; suite
  noise control and smoke movement are not resolved by that preference.

### CF-011 — Rear grade discharge versus the coordinated dogleg stair

D-028 requires the protected stair to discharge directly to the rear. The predecessor PB
graphics showed a rear opening at the same plan position as the stair but did not model
risers, landings or levels consistently. D-074/SC-01 now coordinates the unchanged
4.50 × 3.60 m enclosure as a conventional two-flight dogleg: 11 risers reach the rear
intermediate landing at **+1.90 m**, then 11 more risers reach P2 at **+3.80 m**. The
current rear-door plane therefore intersects the intermediate landing rather than a PB
grade landing.

- **Geometric rule:** PB and P2 must continue to show the same SC-01 flights, landing,
  doors and four column coordinates. The rear opening is shown as an unresolved level
  conflict, not as a functioning exit.
- **Prohibited inference:** do not call the current rear opening a direct grade discharge,
  count it as an approved exit, or design/fabricate the stair from the plan symbols.
- **Resolution alternatives to study:** revise the stair topology within or beyond the
  present enclosure; provide a separately protected grade-level exit passage with verified
  headroom; or revise the core geometry through an explicit owner decision. Each alternative
  must preserve the Great Wall, P2 access, four-column load path, fire/smoke enclosure,
  usable widths and cost control.
- **Required evidence:** coordinated plan and longitudinal section, occupancy and egress
  classification, door/landing/headroom checks, structural analysis, fire strategy, and
  measured cost comparison by the responsible professionals.
- **Status:** critical, open. D-074 resolves PB/P2 graphic and mathematical concordance;
  it deliberately does not resolve direct discharge.

## Resolution rule

Every conflict must be closed with evidence, a responsible party, a date, and a decision.
“Use the most convenient figure” is not a valid method.
