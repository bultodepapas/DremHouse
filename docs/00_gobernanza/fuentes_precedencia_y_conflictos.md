# Sources, precedence, and conflicts

**Status:** active  
**Version:** 0.4  
**Date:** 2026-08-12  
**Language note:** controlled English translation under D-044; no technical change.

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

| Source | Role | Status |
|---|---|---|
| `casa_bodega_boyaca_conclusiones_anteproyecto.md` | Intent, hard rules, and synthesis | Active conceptual source |
| `Dream_House_Plano_Conceptual_v0.2.md` | Geometry and nominal areas | Active for dimensional control |
| `Dream House — Presupuesto Técnico y Control de Costos v0.2.docx` | Target and construction divisions | Active; low-to-medium confidence |
| `Dream_House_Presupuesto_Preliminar_v0.1.md` | Earlier feasibility estimate | Historical / superseded |

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

- **Interim rule:** 4.80 × 1.40 m is the test envelope. Adopt it only if ergonomics,
  services, daily use, and cost justify its size.
- **Status:** open until the v0.3 kitchen layout is completed.

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

## Resolution rule

Every conflict must be closed with evidence, a responsible party, a date, and a decision.
“Use the most convenient figure” is not a valid method.
