# Connected Source Inventory

**Status:** audited baseline; coordination evidence only  
**Version:** 0.6<br>
**Date:** 2026-10-03<br>
**Source:** Read-only inspection of the PB b37 and P2 b28 loaders, their JSON inputs and
transitive loader lineage, current drawing catalog and adjacent issue manifests.  
**Authority:** This inventory records existing source ownership and known limits. It does
not adopt geometry, resolve a conflict, select an assembly, change cost or promote a
drawing.

**Implementation reference:** D-084, increments 01–02 and the 2026-10-03 continuation;
this inventory reconciles source ownership with the implemented resolver and preserves
the audited baseline. See the [workflow](connected_coordination_workflow.md) for execution
and the [current phase checkpoint](connected_project_coordination_next_step.md#current-migration-checkpoint--2026-10-03)
for software completion and remaining source-data/professional gates.

The final 2026-10-03 acceptance record covers 36 current SVGs, 20 source-backed native
sheets, 322 checked source anchors and 166 checked named dimensions. Two P2 schematic
layer-sum dimensions have separate source-context audits; seven tabular/screening sheets
are explicitly nonmetric. Exact identities and test results are retained in the
[final acceptance record](connected_coordination_migration_and_extension_guide.md#final-acceptance-record--2026-10-03).

## Current migration — 2026-10-03

The nine review views include SC-01's cross-level envelopes and known access-floor datum.
View definitions and saved issue references retain the original package identity; optional
presentation cuts do not change physical quantities. Purpose/milestone requirements and
review-evidence dependencies are separate generated reports. The closure record links
all nineteen subphases to their current artifacts and acceptance test modules.


The current view inventory (schema 3) audits explicit source bindings, numerical
measurements and declared painted dimension labels. Registered source-to-SVG transforms
bind native geometry and measurements on enrolled sheets. Other sheet annotations retain
explicit coverage limits. The main review links all inventoried occurrences; source editing
remains in JSON/Python. CF-014 is included in propagated open-conflict context.


The [migration and extension guide](connected_coordination_migration_and_extension_guide.md) supersedes the pilot migration statuses in the retained table below.
The resolver captures all 27 catalog identities and adjacent source-manifest hashes in
`drawing_catalog` and `drawing_source_evidence`. The connected drawing dispatcher uses
captured native PB/P2, roof and structure inputs; it does not reload a historical scenario
while rendering. It writes a separate review sheet per catalog identity alongside the
nine annotated review projections. `drawing_inventory.json` is the executable coverage
record, including limitations of inherited annotations and engineering hypotheses.
`capabilities.json` relates entities, permitted operations, rule coverage and occurrences.

Structural search spaces are now captured in `discipline_inputs.structure`; wall,
stair, phase, service and maintenance adapters use the same snapshot. Existing pinned
studies need a reviewed rebase because this expands the model fingerprint. Full rebuilds
remain deliberate; dependency ordering rejects missing consumers and cycles.

Historical source hashes, revisions and publication aliases below remain unchanged.
Review releases and their rollback pointer do not rewrite the adopted catalog.

## Scope and publication boundary

This inventory preserves the Phase 0 source baseline for the connected-coordination
implementation. The current published plans use `load_b37_model()` and `load_b28_model()`;
the existing shared-model loader still defaults to the distinct D059 integration scenario.
The current implementation produces nine new review views in an isolated review output
directory. Those views remain candidate evidence and are not added to the current drawing catalog. All 27
existing SVG/PNG aliases remain separately published until an explicit catalog promotion
is made under the current publication workflow.

The project frame uses metres: X runs from the front to the rear (0–36 m), Y from Side A
to Side B (0–18 m), and Z is vertical. [`stair_core.json`](../../dreamhouse/stair_core.json)
sets PB finished floor to Z=0, P2 finished floor to +3.80 m and the stair intermediate
landing to +1.90 m. Side A maps to Y=0 and Side B to Y=18; site orientation is unresolved,
so these side labels do not establish compass orientation. P2 geometry occupies X=21–36 m
and Y=0–18 m. Its current model inherits this coordinate convention through SC-01 rather
than declaring a top-level coordinate system of its own.

## Current and historical loaders

| Purpose | Loader | Effective source lineage | Boundary |
| --- | --- | --- | --- |
| Current PB issue | [`generate_pb_b37.py`](../../dreamhouse/generate_pb_b37.py), `load_b37_model()` | PB deltas b37 → b36 → b35 → b34 → b32 → b31 → b30 → b29 → b28 → b27 → b26 → b25 → b24 → [`pb_b05.json`](../../dreamhouse/pb_b05.json); b34 also loads SC-01. | Adds D083 workstation glazing and adapts five P2 bedroom windows for PB elevations. It also uses the P2 b28 loader and `rooflight_b12.json` to build the opening schedule. b33 is a separate published issue, not a b37 loader dependency. |
| Current P2 issue | [`generate_p2_b28.py`](../../dreamhouse/generate_p2_b28.py), `load_b28_model()` | P2 deltas b28 → b27 → b26 → b25 → b24 → b23 → b22 → b21 → b20 → b19 → b18 → b17 → b16 → [`p2_b15.json`](../../dreamhouse/p2_b15.json); b24 loads SC-01. | Replaces the five bedroom-window geometries from D083. P2 b25 owns the D080 wall schedule; b27 owns the D082 rescue-window change. |
| Older shared integration scenario | [`model/io.py`](../../dreamhouse/model/io.py), `load_project()`; [`project_v04.json`](../../dreamhouse/model/project_v04.json) | Default scenario `D059_P2_REFINED_ENVELOPE`: PB_B05, P2_B15, rooflight B12, structure-system/E1 screening and roof-space inputs. | Retain for its declared scenario and comparisons. It is not the current PB b37/P2 b28 source adapter and must not be silently relabelled as one. |

The PB b37 loader verifies its immediate PB base-delta hash and the D083 source hash. The
P2 b28 loader verifies its immediate base-delta hash but does not compare the D083 file to
the source hash declared in `p2_b28_delta.json`; its generated manifest records that
source hash. The nested delta loaders check their declared predecessor chain. The b37 and
b28 issue manifests record direct source references and the named generator, but do not
fingerprint every transitive Python dependency. The implemented resolver therefore
records a conservative input and code dependency set in `model.json` and verifies it
before exposing a package. An adjacent historical issue manifest is not treated as a
complete build fingerprint. This deliberately broad dependency set is not yet a minimal
graph for selective rebuilding of individual consumers.

The active drawing aliases are synchronized only from the explicit [`catalog.json`](../../planos/actual/catalog.json)
by [`sync_current_drawings.py`](../../.github/scripts/sync_current_drawings.py). Its
source-manifest and revision checks preserve the published source-to-alias relationship.
The inventory below reports the generator named by each source manifest; it does not
change that relationship.

## Source ownership and normalized geometry limits

### Openings and aliases

[`window_daylight_d083.json`](../../dreamhouse/window_daylight_d083.json) owns five P2
bedroom windows (`W-H1`, `W-H2`, `W-G`, `W-M-LAT-A`, `W-M-REAR`) and two PB workstation
openings (`GLZ-WS-A`, `GLZ-WS-B`). The P2 windows use `room_id`, `edge`, `from`, `to`,
`sill`, `height` and `modules`; the PB workstation records use `side`, `x0`, `x1`,
`sill`, `height`, `head` and `modules`. The same source records a 1.20 m module, P2 level
+3.80 m and the excluded `GLZ-DINING-STUDY-B` proposal.

PB b37 creates elevation aliases for the five P2 windows and stores their native IDs in
`p2_id`: `W-H1` ↔ `GLZ-H1`, `W-H2` ↔ `GLZ-H2`, `W-G` ↔ `GLZ-G`, `W-M-LAT-A` ↔
`GLZ-M-A`, and `W-M-REAR` ↔ `GLZ-M-R`. Each pair describes one opening and must not be
counted twice. The alias mapping is assembled in [`generate_pb_b37.py`](../../dreamhouse/generate_pb_b37.py).

The remaining PB vertical glazing records are `GLZ-CAR` and `GLZ-RC` in the inherited
`technical_glazing` array from `pb_b05.json`. Each is 7.20 × 2.90 m with a +0.90 m sill.
The PB and D083 sources map Side A/B to Y=0/18; their X spans are `x0..x1`. Rear glazing
uses X=36 and spans along Y. PB b37 replaces workstation glazing from D083 and constructs
the five bedroom aliases from P2 b28.

P2 has seven current window records: those five D083 bedroom windows, inherited `W-WELL`,
and `W-EGRESS-P2` from the D082 b27 delta. For P2, `south` is Y=0 and `north` is Y=18,
with spans along X; `east` is X=36, with spans along Y. P2 `sill` and `height` are local
to the +3.80 m floor. For example, `W-H1` spans X=21.8–25.4 on Y=0 and project elevations
+3.85 to +6.75 m. In the existing opening schedule, `head_m` is `sill + height` (the
floor-relative head), not the global project elevation. Preserve that distinction when
normalizing datums.

The existing [`opening_schedule.json`](../../planos/conceptual_v0.3_b37_pb/opening_schedule.json)
contains four PB vertical openings (two technical and two workstation), seven P2 windows,
and two rooflights. It keeps the dining study separate. Its measured opening areas are
21.96 m² for `GLZ-WS-A` and 5.40 m² for `GLZ-WS-B`; the two-workstation baseline is
27.36 m². These are nominal rectangular opening envelopes, not net glass, free ventilation
area or selected products.

### Doors and host references

P2 has 20 door/opening records with native `id`, `connects`, `kind`, `swing`, `wall`,
`width`, a fixed `x` or `y`, and `at`. For horizontal walls, the fixed coordinate is Y and
the opening spans X=`at..at+width`; for vertical walls, the fixed coordinate is X and the
opening spans Y=`at..at+width`. The validator checks the opening against the common
boundary of the two named spaces. A normalized host reference can point to that derived
shared boundary without asserting an assembly or performance rating. P2 door heights are
not present in these records.

PB has no single `doors[]` collection. Its front `front_openings[]` use `id`, `y0`,
`width` and `height`; the front plane is X=0 in the renderer. Rear `exterior_doors[]` use
`id`, `edge="rear"`, `y` and `width`; their plan plane is X=36 and the renderer treats
`y..y+width` as the span, while the rear elevation and enlarged detail start at `y - 0.50`.
The five internal core doors are embedded in `core[]` as
`door_y` and `door_width`, without a separate door ID or host-wall key. The renderer places
them at the Great Wall plane X=31.5. The source does not clearly state whether `door_y`
denotes a centre or an endpoint: the enlarged core detail subtracts a fixed 0.45 m, while
the plan symbol helper receives the unadjusted value. Keep this mapping unresolved until
that convention is reconciled under CF-013. Door heights are absent for the PB core and rear doors.

Geometric host references can be explicit where the source supports them: a PB opening can
reference its front/rear/façade plane; a P2 window can reference its declared exterior
edge; a P2 door can reference the computed shared space boundary; and a PB core opening can
reference X=31.5 as a renderer-derived location. These links do not establish the wall
assembly, window filling, structure, fire rating or envelope continuity.

### Spaces and walls

P2 has 21 axis-aligned `spaces[]` rectangles using `id`, `x`, `y`, `w` and `d`, plus
`kind`, `suite` and `phase` where applicable. The records have no individual Z field; the
P2 plan and shared levels supply the +3.80 m floor context. P2 `doors[].connects` refers to
these space IDs.

PB does not have a complete space registry. Its five `core[]` entries provide room IDs,
types and Y intervals (`y0`, `y1`) but no X coordinate; the renderer places the core in
X=31.5–36.0 m. Other program rectangles are distributed among records such as
`car_territory` and `social_layout.program_territories`; these do not form one exhaustive
room list.

P2 `wall_schedule` defines eight wall types and nominal thicknesses, but there is no
complete authored wall-instance list. The plan renderer derives internal wall lines from
shared space boundaries and assigns types by `kind` and `suite`. P2-W04R is an explicit
X=21 m line from Y=0 to 18 m with the family frontage Y=5.00–12.45 m open. P2-W05 declares
the south, north and east envelope edges at 230 mm nominal. P2-W06 is a scheduled type with
no current wall instance. Do not turn generated shared boundaries or type classifications
into authored assemblies. The P2-W05 `layer_sum_note` still describes approximately 297/300
mm even though D080 sets 230 mm and the listed layers total 229 mm; this stale note is not
an assembly authority.

PB geometry declares a 180 mm exterior-wall thickness, a Great Wall at X=31.5 m with
200 mm nominal thickness, and standard/stair partition values of 150/200 mm. These values
locate schematic coordination geometry; they do not supply a full set of PB wall instances
or approved assemblies.

### Columns and structural context

The four SC-01 stair-column reservations repeat across PB, P2 and
`stair_core.structure.column_reservations`: `GW-STAIR-S` (31.5, 7.4), `GW-STAIR-N`
(31.5, 11.0), `STAIR-REAR-S` (36.0, 7.4) and `STAIR-REAR-N` (36.0, 11.0). Their records
are plan points. `column_reservation_size=0.3` is a schematic plan reservation; no member
section or per-column Z interval is stored.

The separate E1 `vertical_continuity.candidate_columns` source contains eight XY
candidates, including four additional Great Wall positions. Its `trial_bay_height_m=7.5`
belongs to a generic lateral bay and is not a height assigned to each candidate. The E0
`structure_system.json` has six trial Great Wall Y positions. Structural calculation code
uses a 3.8 m test height for selected column weight/screening calculations; this is a
calculation input, not an authored column solid or a selected member length. Keep
point-only reservations distinct from any named analysis span. Current E0/E1 sheets remain
screening evidence, and CF-009/CF-010 structural interfaces are unresolved.

## Source-derived baseline figures

These are the existing loader/schedule values for comparison, not results of a new test
run or a change in authority:

| Family | Count | Source-derived quantity | Basis |
| --- | ---: | ---: | --- |
| PB vertical openings | 4 | 69.12 m² | Two technical + two workstation openings in PB b37. |
| P2 vertical openings | 7 | 54.72 m² | Five D083 bedroom + W-WELL + W-EGRESS-P2. |
| Total vertical glazing | 11 | 123.84 m² | Existing PB b37 schedule; PB aliases of five P2 windows are not added again. |
| Rooflights | 2 | 23.04 m² | `RL-CAR` and `RL-RC` from rooflight B12. |
| PB workstation glazing | 2 | 27.36 m² | 21.96 m² + 5.40 m², D083 source. |

The per-family subtotals reconcile to the existing combined 123.84 m² schedule figure.
The pilot retains per-entity values from its resolved snapshot. Do not treat this
inventory as a priced quantity or substitute it for that schedule.

## Retained catalog provenance and pilot disposition — 2026-10-02

The table enumerates the 27 records in [`planos/actual/catalog.json`](../../planos/actual/catalog.json).
“Current consumer” is the generator named in the source issue manifest. Pilot statuses
refer to the isolated window-coordination pilot; current SVG/PNG aliases remain in place.

| Catalog ID | Published source (revision) | Current consumer | Migration status |
| --- | --- | --- | --- |
| `architecture-ground-floor` | `planos/conceptual_v0.3_b37_pb/DH-ARQ-PLN-001-R15_PB-WINDOW-DAYLIGHT-DATUMS.svg` (b37) | `dreamhouse/generate_pb_b37.py` | Pilot baseline view; alias retained. |
| `architecture-upper-floor` | `planos/conceptual_v0.3_b28_p2/DH-ARQ-PLN-002-R25_P2-COORDINATED.svg` (b28) | `dreamhouse/generate_p2_b28.py` | Pilot baseline view; alias retained. |
| `architecture-roof-plan` | `planos/integracion_v0.4_i01/rooflights/DH-ARQ-PLN-CUB-001-R11_D054-HALF-CENTRES.svg` (I01) | `dreamhouse/generate_rooflight_b11.py` | Rooflight quantity context; separate alias retained. |
| `architecture-roof-daylight-section` | `planos/integracion_v0.4_i01/rooflights/DH-ARQ-SEC-CUB-003-R11_D054-DAYLIGHT.svg` (I01) | `dreamhouse/generate_rooflight_b11.py` | Rooflight quantity context; separate alias retained. |
| `architecture-roof-longitudinal-section` | `planos/conceptual_v0.3_b07_cubierta/DH-ARQ-SEC-001-R06_LONGITUDINAL-CUBIERTA.svg` (b07) | `dreamhouse/generate_roof_b07.py` | Outside pilot; current alias retained. |
| `architecture-roof-transverse-section` | `planos/conceptual_v0.3_b07_cubierta/DH-ARQ-SEC-002-R06_TRANSVERSAL-CUBIERTA.svg` (b07) | `dreamhouse/generate_roof_b07.py` | Outside pilot; current alias retained. |
| `architecture-front-elevation` | `planos/conceptual_v0.3_b07_cubierta/DH-ARQ-ELE-001-R06_FACHADA-FRONTAL-CUBIERTA.svg` (b07) | `dreamhouse/generate_roof_b07.py` | New candidate front projection; published alias retained. |
| `architecture-rear-elevation` | `planos/conceptual_v0.3_b37_pb/DH-ARQ-ELE-002-R07_REAR-WINDOW-DAYLIGHT.svg` (b37) | `dreamhouse/generate_pb_b37.py` | Pilot baseline view; alias retained. |
| `architecture-side-a-elevation` | `planos/conceptual_v0.3_b37_pb/DH-ARQ-ELE-003-R10_SIDE-A-WINDOW-DAYLIGHT.svg` (b37) | `dreamhouse/generate_pb_b37.py` | Pilot baseline view; alias retained. |
| `architecture-side-b-elevation` | `planos/conceptual_v0.3_b37_pb/DH-ARQ-ELE-004-R10_SIDE-B-WINDOW-DAYLIGHT.svg` (b37) | `dreamhouse/generate_pb_b37.py` | Pilot baseline view; alias retained. |
| `architecture-great-wall-elevation` | `planos/conceptual_v0.3_b05_pb/DH-ARQ-ELE-INT-001-R04_GRAN-MURO.svg` (b05) | `dreamhouse/generate_pb_b05.py` | Outside pilot; current alias retained. |
| `architecture-ground-floor-core` | `planos/conceptual_v0.3_b33_pb/DH-ARQ-DET-001-R05_PB-STAIR-CORE.svg` (b33) | `dreamhouse/generate_pb_b33.py` | Stair context only; current alias retained. |
| `architecture-pb-media-wall` | `planos/conceptual_v0.3_b27_pb/DH-ARQ-ELE-INT-002-R01_PB-100IN-SIDE-B-WALL.svg` (b27) | `dreamhouse/generate_pb_b27.py` | Outside pilot; current alias retained. |
| `architecture-pb-integrated-workstations` | `planos/conceptual_v0.3_b37_pb/DH-ARQ-DET-006-R03_PB-DESK-WINDOW-INTERFACE.svg` (b37) | `dreamhouse/generate_pb_b37.py` | Opening represented in candidate; full workstation/interface detail pending; alias retained. |
| `architecture-pb-technical-workbenches` | `planos/conceptual_v0.3_b36_pb/DH-ARQ-DET-007-R01_PB-TECHNICAL-WORKBENCH-SYSTEM.svg` (b36) | `dreamhouse/generate_pb_b36.py` | Outside pilot; current alias retained. |
| `architecture-p2-bedroom-windows` | `planos/conceptual_v0.3_b28_p2/DH-ARQ-DET-008-R00_P2-BEDROOM-WINDOW-FAMILY.svg` (b28) | `dreamhouse/generate_p2_b28.py` | Pilot baseline view; alias retained. |
| `architecture-window-schedule` | `planos/conceptual_v0.3_b37_pb/DH-ARQ-SCH-001-R00_D083-WINDOW-SCHEDULE.svg` (b37) | `dreamhouse/generate_pb_b37.py` | Pilot baseline schedule; alias retained. |
| `architecture-access-egress` | `planos/conceptual_v0.3_b27_p2/DH-ARQ-DIA-001-R24_P2-ACCESS-EGRESS.svg` (b27) | `dreamhouse/generate_p2_b27.py` | Egress context only; current alias retained. |
| `architecture-owner-priorities` | `planos/conceptual_v0.3_b27_p2/DH-ARQ-DET-002-R24_OWNER-PRIORITIES.svg` (b27) | `dreamhouse/generate_p2_b27.py` | Egress/interface context only; current alias retained. |
| `architecture-p2-acoustic-partition` | `planos/conceptual_v0.3_b25_p2/DH-ARQ-DET-003-R22_P2-ACOUSTIC-PARTITION.svg` (b25) | `dreamhouse/generate_p2_b25.py` | Wall-type context; detail not migrated; alias retained. |
| `architecture-p2-hall-edge` | `planos/conceptual_v0.3_b25_p2/DH-ARQ-DET-004-R22_P2-HALL-EDGE.svg` (b25) | `dreamhouse/generate_p2_b25.py` | Wall-type context; detail not migrated; alias retained. |
| `architecture-p2-exterior-wall` | `planos/conceptual_v0.3_b25_p2/DH-ARQ-DET-005-R22_P2-EXTERIOR-WALL.svg` (b25) | `dreamhouse/generate_p2_b25.py` | Wall-type context; detail not migrated; alias retained. |
| `structure-coordination-plan` | `planos/estructura/DH-EST-E0-002_ESTRUCTURA-INSPECCION.svg` (E0/E1) | `dreamhouse/generate_structure_plan.py` | Structural context only; separate alias retained. |
| `structure-lateral-a` | `planos/estructura/DH-EST-E0-003_ESTRUCTURA-LATERAL-A.svg` (E0/E1) | `dreamhouse/generate_structure_plan.py` | Structural context only; separate alias retained. |
| `structure-great-wall` | `planos/estructura/DH-EST-E0-004_PARED-HIBRIDA.svg` (E0/E1) | `dreamhouse/generate_structure_plan.py` | Structural context only; separate alias retained. |
| `structure-e1-synthesis` | `planos/estructura/DH-EST-E1-001_SINTESIS-ESTRUCTURAL.svg` (E0/E1) | `dreamhouse/generate_structure_plan.py` | Structural context only; separate alias retained. |
| `structure-vertical-continuity` | `planos/estructura/DH-EST-E1-002_CONTINUIDAD-VERTICAL-ESCALERA.svg` (E0/E1) | `dreamhouse/generate_structure_plan.py` | Column-context evidence; separate alias retained. |

The nine new review views are isolated candidate outputs, not catalog records.
Their generated identities, source references and findings must be traceable within the
review package. Adding or replacing any stable current alias remains a separate explicit
promotion step.

## Retained increment 02 implementation reconciliation — 2026-10-02

This subsection records the implementation at its 2026-10-02 checkpoint; it is superseded
for current view count and software status by [Current migration](#current-migration--2026-10-03)
and the [closure guide](connected_coordination_migration_and_extension_guide.md). The
[increment 02 record](connected_coordination_increment_02.md) documents that retained
software scope. Its eight-view package added `window-sections.svg`, a projected section of
GLZ-WS-A only; it did not add details for every opening or change the adopted opening
geometry. That package audited named anchors, dimensions and cross-view callouts. Optional
`--visuals` output supplies pinned-font PNG previews, a contact sheet and pixel comparisons
for review; those artifacts do not grant approval. Dependency metadata identifies affected
consumers, while package generation still performs a conservative full rebuild rather than
selectively rebuilding only those consumers.

Current discipline adapters consume the resolved P2 programme, captured equipment
catalogue/layout benchmark, PB workstation data and structural source candidates. The
current primary dressing area is 13.44 m² under the D-065 P2 rebalance record; the historic
15 m² closet check is superseded, inapplicable and remains OPEN, not a new FAIL or a new
minimum. Equipment placements remain an unadopted benchmark: the primary-bed host fit and
0.90 m clearance retain raw FAIL evidence, and the refrigerator depth mismatch remains raw OPEN;
all equipment findings remain OPEN pending current product/layout applicability. The
structural adapter compares four SC-01 plan reservations and six E0 source candidate lines
with current room/opening geometry. All ten findings remain OPEN and establish plan
relationships only. No vertical member extent, solid 3D clearance, capacity, current
structural result or installed mass is inferred. These software additions do not promote
the 27 current drawing identities or change the house design.

## Open conflicts and limits

Keep the following conflicts open in all pilot artifacts:

- **CF-009:** scheduled P2 wall/opening geometry is not reconciled with installed mass,
  facade panel deductions, wind actions, structural response or cost.
- **CF-010:** the open P2 family frontage, guard, slab edge, exposed truss and retained
  walls lack coordinated structural, movement, fire and acoustic design.
- **CF-011:** `EXT-ESC` is drawn at PB grade while the stair reaches the rear opening plane
  at the +1.90 m intermediate landing; it is not a resolved grade discharge.
- **CF-012:** the D082 foldout ladder is supplementary rescue equipment and is not credited
  as a required second means of egress.
- **CF-013:** PB core/rear door scalar anchors receive inconsistent endpoint offsets in
  archived plan/detail/elevation generators; the new registry keeps their spans unresolved.

The source-derived opening figures do not close safety, glazing, daylight, solar, privacy,
structural, wind, envelope, drainage or cost review. Preserve every unknown as unknown and
keep the source geometry at schematic authority. No files under `docs/BORN_Legacy/` were
used as writable inputs or changed for this inventory.
