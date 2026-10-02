# Connected project coordination — recommended next step

**Status:** repository assessment and proposed next increment; not adopted for implementation  
**Version:** 0.2  
**Date:** 2026-10-02  
**Source:** owner's request to understand the repository and recommend meaningful progress
toward clearer, connected, automatically generated project information; repository review,
code inspection, numerical probes and validation performed in the same conversation;
subsequent owner-requested internet research against primary sources, recorded in
[twelve research investigations](../08_investigacion/connected_coordination_research_2026_10.md).  
**Reviewed baseline:** Git commit `24479a9`, with a clean working tree before this document.  
**Authority:** recommendation only. Recording this assessment does not adopt a design,
change scope or cost, promote a drawing, or close a professional design gate.

**Revision note:** v0.2 strengthens the proposed data contracts, graphical interaction,
dependency tracking, quantity semantics and acceptance evidence. The baseline findings
and 306-test result below belong to the original assessment; this documentation revision
does not claim to have implemented or tested the proposed system.

## 1. Recommendation and project intent

The next significant step is to make one part of the house traceable, with a persistent
identity, from its definition through drawings, quantities, conflicts and pending
decisions. Start with one element family and complete that entire connection.

Dream House's purpose is a simple industrial hall that accommodates a rich domestic and
technical life: family, making, work and landscape together. Precision should concentrate
on the relationships that make this possible: how daylight enters, how people sleep while
the ground floor is active, how an installation can be maintained, and how the house can
be completed in phases. The repository should make those relationships visible and
testable.

This interpretation follows the [Project Constitution](../00_gobernanza/constitucion_del_proyecto.md),
[master brief](../01_brief/brief_maestro.md) and
[spatial relationships](../01_brief/relaciones_y_experiencia.md). The active
[source precedence and conflict register](../00_gobernanza/fuentes_precedencia_y_conflictos.md)
continues to govern every value and unresolved interface.

Progress can therefore mean reducing uncertainty, exposing a dependency or making a
proposal easier to evaluate before any new architectural decision is made.

## 2. Review scope and verified starting point

The review covered governance, programme, architecture, the integration pipeline,
quantities, cost reconciliation, drawing generators, publication and graphic pilots.
Rendered ground-floor and pilot-contact images were also inspected.

The existing foundation is substantial:

- deterministic Python generators and machine-readable JSON inputs;
- versioned drawings and explicit promotion to stable current SVG/PNG aliases;
- input and output provenance checks;
- shared coordination inputs for the stair and recent window family;
- an architecture–structure–quantity–cost pipeline;
- five graphic pilots with readability and rendering controls.

Validation during the assessment produced:

| Check | Observed result |
| --- | --- |
| Repository test discovery | 306 tests passed |
| Current-drawing synchronization check | 27 SVG/PNG pairs and their provenance validated |
| Generated README check | Passed |
| Static lint of GP01–GP05 | 0 errors, 11 warning findings |

These results describe the reviewed baseline. They do not demonstrate complete
coordination across the latest discipline models. The commands used were:

```bash
python3 -m unittest discover -s dreamhouse -p 'test_*.py'
python3 .github/scripts/sync_current_drawings.py --check
python3 .github/scripts/build_showcase.py --check-readme
python3 -m dreamhouse.svg.lint planos/piloto_grafico_v0.1 --format markdown
```

## 3. Verified gaps and their consequences

| Finding | Evidence | Consequence |
| --- | --- | --- |
| Current drawings use PB b37 and P2 b28, while the default integration scenario still loads PB b05 and P2 b15. | [Current catalog](../../planos/actual/catalog.json), [scenario manifest](../../dreamhouse/model/project_v04.json), [model loader](../../dreamhouse/model/io.py). | A reproducible integrated calculation can still represent an earlier house state. |
| The earlier integrated opening schedule gives 96.78 m² of vertical glazing; the current inputs give 123.84 m². | Read-only calls to [the opening schedule builder](../../dreamhouse/envelope/openings.py), using the default scenario and then the PB b37/P2 b28 loaders with the same rooflight input. | File provenance alone does not establish that disciplines consume the same state. These are different scenario totals, not an approved scope or cost delta. |
| Supplying current inputs to the quantity ledger classifies the two workstation windows as rooflight glazing. | [Quantity ledger](../../dreamhouse/quantities/ledger.py): the fallback assembly assignment includes `PB.workstation_glazing`. The probe assigned 21.96 m² for `GLZ-WS-A` and 5.40 m² for `GLZ-WS-B` to `ROOFLIGHT-GLAZING`. | Updating sources also requires checking semantic mappings; a correct area can enter the wrong assembly. |
| Graphic QA is advanced in five pilots but has not become acceptance coverage for the current drawing set. | [Pilot contact audit v0.7](../08_investigacion/svg_pilot_contact_audit_v0.7.md). | Existing work can support a controlled rollout to current drawings. |
| GP01 assigns model-reference identifiers from positions in the copied source SVG. | [Ground-floor pilot generator](../../dreamhouse/svg/pilot_ground_floor.py), including `PB-SOURCE-{source_index:03d}`. | These identify copied drawing nodes, rather than a persistent building element shared by plan, elevation and quantities. |

The integration lag is partly acknowledged in the existing
[integration plan](parametric_architecture_structure_cost_integration_plan.md), including
its D-080 current-model gap. This assessment extends that observation to the current
PB/P2 window state and its quantity mapping. It does not invalidate historical evidence
for the scenario that evidence actually describes.

The next improvement should make the connections between disciplines verifiable.

## 4. First complete demonstration: windows and their interfaces

Build a first connected coordination viewer around windows and their interfaces. This
is a manageable family with an existing
[shared D-083 source](../../dreamhouse/window_daylight_d083.json). It connects daylight,
plans, elevations, details, secondary structure, envelope performance and quantities.

```mermaid
flowchart TD
    A[Explicit current-state manifest] --> B[Elements, relationships, units and provenance]
    B --> P[Shared geometry and view projections]
    P --> C[SVG plans, elevations and details]
    B --> D[Named measurements and cost mappings]
    B --> E[Checks, coverage and issue records]
    C --> F[Connected coordination viewer]
    D --> F
    E --> F
    B --> G[Dependency and freshness checks]
    G --> F
```

For example, selecting `GLZ-WS-A`, the Side A workstation window, should:

1. Highlight the same opening in the ground-floor plan, elevation and interface detail.
2. Show its current schematic definition: **7.20 × 3.05 m**, sill **+0.75 m**, nominal
   rectangular opening area **21.96 m²**, source **D-083**. This measured envelope does
   not establish net glass, ventilation free area or a manufacturer's window size.
3. Show its relationships to the workstation, host wall and unresolved interfaces.
4. Distinguish verified geometry from pending header, glazing, drainage, condensation
   and quotation work.
5. Make the differences from the preceding issue available for inspection.

The drawing becomes an entry point to the element's evidence. The viewer exposes the
model's authority and limitations; it does not create dimensional authority of its own.

### 4.1 Minimum element and relationship contract

The following is a proposed internal contract, informed by investigations
[R01–R03](../08_investigacion/connected_coordination_research_2026_10.md#r01) and
[R06–R07](../08_investigacion/connected_coordination_research_2026_10.md#r06). It does not
require IFC export to start.

| Record | Proposed content | Purpose |
| --- | --- | --- |
| Element identity | Persistent `entity_id`, existing human-readable tag and explicit legacy aliases | Preserve links when labels, file order or geometry change; record replacements separately. |
| Scenario occurrence | Scenario ID, element revision and adopted/study status | Compare alternatives without giving a study current authority. |
| Geometry | Declared length units, project axes, placement, host plane, width/height and elevation datum | Derive view geometry and distinguish local sill levels from project elevations. |
| Relationships | Host wall, void/opening, proposed filling/window assembly and relevant space references | Keep opening, frame and glass semantics distinct; leave unidentified assemblies explicitly unresolved. |
| Measurement | Source entity, named quantity kind, unit, formula/version, deductions and inclusion status | Prevent gross opening area being silently treated as net glass or as a priced assembly. |
| Evidence | Source reference/hash, decision/conflict references and applicable rule IDs | Explain both the value and its unresolved obligations. |

Keep existing project tags unchanged and map known aliases explicitly. A content hash
identifies a version of information; it should not replace the persistent identity of
the element. An unresolved host or filling must be reported rather than invented to make
the record appear complete.

Use a small shared geometric representation sufficient for this family: opening extents,
local placement, project levels and declared plan/elevation projection transforms. This
can be implemented without a complete solid-model kernel. Distinguish projected views
from schematic assembly details: a conceptual detail may share element references and
parameters while still having unsupported construction geometry.

### 4.2 Separate status dimensions

The proposed viewer should show these dimensions independently, following
[R04](../08_investigacion/connected_coordination_research_2026_10.md#r04) and
[R09](../08_investigacion/connected_coordination_research_2026_10.md#r09):

| Dimension | Question answered |
| --- | --- |
| Adoption | Is this an active schematic assumption, an unadopted study or historical evidence? |
| Freshness | Was this result generated from the declared current inputs and generator? |
| Automated checks | Which applicable information and geometry rules passed, failed or remain unevaluated? |
| Professional evidence | Which structural, envelope, safety and other reviews remain open? |
| Cost disposition | Is the quantity mapped, is a comparable rate available, and is its use authorized? |
| Publication authority | For which named purpose was this issue promoted? |

Retain existing `PASS`, `OPEN` and `FAIL` outcomes where applicable; add explicit coverage
and freshness information alongside them. An unsupported check must not disappear from
the coverage report. A current, geometrically consistent window can still have open
structural and cost gates. These are proposed project distinctions, not a claim of
standards certification.

## 5. Three implementation increments

### 5.1 Establish an unambiguous current state

Provide one entry point that assembles currently adopted models and their dependencies.
Initially, it can reuse existing loaders and generators while preserving all historical
issues.

Declare which portions of earlier studies still apply and which require review. Different
revision numbers across disciplines are acceptable when their compatibility and limits
are explicit.

The proposed output is a reviewable current-state manifest identifying the consumed
sources, their statuses, dependencies and applicable checks. Historical comparison
scenarios remain available with their actual scope clearly stated.

Before connecting the viewer, reproduce the existing PB b37/P2 b28 geometry through the
new entry point, with a comparison report. Correct the workstation-window classification
through an explicit typed mapping; an unknown source family must produce a diagnostic
instead of falling through to rooflights. Preserve current scenario totals as regression
evidence while introducing precise measurement names; do not silently relabel nominal
opening area as measured glass.

Use schema validation for required fields, supported kinds and units, followed by
separate checks for reference integrity, finite numbers, geometric relationships and
quantity mappings. A schema-valid document is only the first validation layer.

### 5.2 Connect one element family to multiple views

Give each opening a persistent identity with references to its location, source,
decision, quantities and checks. Preserve that identity in every generated SVG view.

Reuse the existing graphic library and pilot work. Provide a clear primary drawing with
optional dimensions, identifiers and conflict overlays, plus a side panel for detailed
evidence. This supports both an overall reading of the house and closer technical review.

The first connected family should cover the relevant plans, elevations, window/interface
detail and opening schedule. Its common identity must come from the model, independently
of where a primitive happens to appear inside an SVG file.

The current gallery embeds drawings as images. For element selection, the proposed
viewer should mount validated generated SVG as inline document content, with interaction
managed by the host page. Preserve standalone SVG/PNG outputs for publication. Give each
view occurrence a unique DOM `id`, and use a shared `data-entity-id` to connect occurrences
of the same element; do not duplicate DOM IDs when several views share a page. This
implementation recommendation follows [R10](../08_investigacion/connected_coordination_research_2026_10.md#r10).

Provide a searchable HTML element list as an equivalent selection route, keyboard
operation, visible focus and textual status labels. Selection targets may use separate
interaction overlays or list controls without changing architectural geometry. Review
these behaviours under [R11](../08_investigacion/connected_coordination_research_2026_10.md#r11).

Link each unresolved matter to affected elements, a saved view, a responsible role,
required evidence and its decision gate. Generate issue summaries from those records,
with explicit links to the authoritative Markdown conflict register. A saved view should
retain its scenario/source references so it can be reopened faithfully. These internal
records borrow useful BCF concepts from
[R05](../08_investigacion/connected_coordination_research_2026_10.md#r05); BCF exchange
remains a later compatibility task.

### 5.3 Automate verification of the complete package

One command should produce a proposed issue containing drawings, quantities, differences
and pending matters. When an input changes, dependent outputs should regenerate or be
explicitly marked as outdated.

Keep the existing explicit promotion mechanism for current publication. Generating an
experimental scenario or passing automated checks does not adopt that scenario.

The package should be usable through the existing static site and reviewable before
promotion, with source and output provenance retained.

Declare a build dependency graph separately from the semantic relationships between
building elements. Each output should identify the sources and generator dependencies
it actually consumes. Include code, schema/rule versions, renderer and font inputs where
they affect an output. Propagate stale status through dependent outputs. Build into a
separate review directory, and verify repeatability in the declared environment before
considering selective caching. These are lightweight Python implementation proposals
informed by [R08](../08_investigacion/connected_coordination_research_2026_10.md#r08), not
a recommendation to install Bazel.

Continuous-integration coverage must follow those dependencies. The reviewed workflows
use selective path filters that do not cover every active model/generator input; a change
only to `dreamhouse/window_daylight_d083.json`, for example, is outside both current
workflow path lists. Include a fast coordination job for relevant inputs and publish its
report, visual comparisons and contact sheets as review artifacts. Keep current-drawing
promotion explicit and independent of a passing review build.

Use the existing renderer comparisons as a starting point. Fix the browser, renderer,
fonts and viewport for a given visual baseline, and keep model checks independent of
pixel comparison. Test meaningful change sequences as well as unchanged reference
models, as proposed in [R12](../08_investigacion/connected_coordination_research_2026_10.md#r12).

## 6. Acceptance evidence

The main acceptance demonstration is a deliberate dimensional change in an unadopted
study scenario. The plan, elevation, relevant detail and quantity schedule must respond
coherently. Any affected view that cannot yet respond must be identified as outdated or
unsupported. The scenario remains a proposal until adoption under project governance.

Additional cross-layer checks should demonstrate that:

- every represented opening corresponds to a known model element;
- dimensions agree between its views;
- every quantity maps to the correct element family;
- unadopted studies are excluded from active totals;
- an unknown price remains pending rather than becoming zero or an invented allowance;
- a successful geometric check preserves applicable professional gates;
- changing a dependency cannot silently leave an apparently current downstream output.

These checks should complement the existing regression and graphic checks. The purpose
is to test the connections that were missing from the reviewed baseline.

### 6.1 Research-to-acceptance matrix

Each row below is a proposed acceptance fixture, not a statement that the fixture already
exists. The linked research records provide primary sources, findings and limits.

| Research | Concrete acceptance evidence |
| --- | --- |
| [R01 — Identity](../08_investigacion/connected_coordination_research_2026_10.md#r01) | Reordering source records or changing a display label preserves selection, issue links and quantity identity. |
| [R02 — Host/opening/filling](../08_investigacion/connected_coordination_research_2026_10.md#r02) | One void linked to a window assembly is measured once; a missing host or invalid relationship is reported. |
| [R03 — Coordinates and units](../08_investigacion/connected_coordination_research_2026_10.md#r03) | A P2 sill of +0.05 m relative to the +3.80 m floor maps to project elevation +3.85 m in the elevation view; a unit mismatch is rejected. |
| [R04 — Information requirements](../08_investigacion/connected_coordination_research_2026_10.md#r04) | Required window fields are checked for every applicable element; unsupported performance checks remain visible. |
| [R05 — Issues and viewpoints](../08_investigacion/connected_coordination_research_2026_10.md#r05) | Reopening a saved issue selects its original elements and view against the identified scenario, or reports an unavailable reference. |
| [R06 — Quantity meaning](../08_investigacion/connected_coordination_research_2026_10.md#r06) | The 21.96 m² workstation opening retains its nominal-envelope meaning; unknown net glass area remains unknown. |
| [R07 — Schema and semantics](../08_investigacion/connected_coordination_research_2026_10.md#r07) | Unknown kinds, duplicate identities, dangling references and workstation-to-rooflight mappings fail the appropriate validation layer. |
| [R08 — Dependencies](../08_investigacion/connected_coordination_research_2026_10.md#r08) | A relevant data or generator-only edit invalidates affected outputs; equivalent clean builds reproduce results; the edit triggers coordination CI. |
| [R09 — Provenance](../08_investigacion/connected_coordination_research_2026_10.md#r09) | A quantity can be traced to inputs and the producing calculation; successful regeneration never creates professional approval. |
| [R10 — SVG interaction](../08_investigacion/connected_coordination_research_2026_10.md#r10) | Selecting one occurrence highlights the corresponding element in other views without duplicate DOM IDs or coordinate changes. |
| [R11 — Accessibility](../08_investigacion/connected_coordination_research_2026_10.md#r11) | Keyboard and list selection reach the same element; focus and open issues remain understandable without colour. |
| [R12 — Change and visual tests](../08_investigacion/connected_coordination_research_2026_10.md#r12) | A width change updates the expected area; a move preserves area; excluding a study removes it from active totals; reviewed renders remain legible. |

For a rectangular opening with fixed height, the proposed width-change fixture has an
independent arithmetic expectation: `area_delta = height * width_delta`. Add a move-only
case because it changes location and affected interfaces while preserving area. These
fixtures test different dependencies and should not be replaced by screenshot equality.

## 7. Subsequent applications with practical decision value

### 7.1 Shared stair core and section relationships

The next application should connect the ground floor (PB), upper floor (P2), longitudinal
section, doors, landings and four columns through the same
[SC-01 geometry](../../dreamhouse/stair_core.json).

The existing conflict register documents that **CF-011** places the rear opening at the
**+1.90 m intermediate landing**, rather than at ground-floor grade. A connected section
and plan comparison would make that relationship explicit and help evaluate alternatives.
This is a recommendation for better evidence; it does not resolve discharge, headroom,
fire protection or structural design.

### 7.2 P2 wall assemblies, loads and quantities

Extend the mechanism to the current P2 wall family, measured wall/opening quantities and
their structural-load and cost dispositions. Retain **CF-009** and **CF-010** until the
required professional evidence resolves them. Installed masses, product performance and
costs remain unknown where supporting inputs are absent.

### 7.3 Services, maintenance and phased completion

Then connect service routes, access for maintenance and the provisions needed between
construction Phases 1 and 2. This would make future equipment replacement, reserved
capacity and completion work easier to understand before those details are frozen.

## 8. Delivery approach and authority

Use the existing Python, JSON, SVG and static-site foundation. Prioritize one complete,
verifiable element family and expand only after that connection works. This keeps the
software effort proportionate to the project's needs and reuses the drawing, validation
and publication work already completed.

The [research dossier](../08_investigacion/connected_coordination_research_2026_10.md)
supports adopting useful information patterns before taking on additional platforms.
Full IFC/IDS/BCF exchange, an RDF database, a general solid-model engine and a new build
framework remain deferred until a real exchange or engineering task requires them. The
immediate proposed deliverables are the current-state manifest, a validated window
registry, connected SVG views, named quantity records, linked issue evidence and a
repeatable review package.

Measure progress by how easily the project team can determine:

- what is known and what remains uncertain;
- which source governs a value;
- which elements and outputs depend on it;
- what a proposed change would affect;
- what evidence is still needed for a decision.

Saving this recommendation is documentation work only. It does not adopt its proposed
implementation, change the construction scope or cost baseline, or promote a drawing.
Consequently, it creates no new entry in the decision register or cost-control record.
Any later adopted change remains subject to the existing governance and recording rules.
