# Connected project coordination — recommended next step

**Status:** repository assessment and proposed next increment; not adopted for implementation<br>
**Version:** 0.4<br>
**Date:** 2026-10-02<br>
**Source:** owner's request to understand the repository and recommend meaningful progress
toward clearer, connected, automatically generated project information; repository review,
code inspection, numerical probes and validation performed in the same conversation;
subsequent owner-requested internet research against primary sources, recorded in
[twelve foundation investigations](../08_investigacion/connected_coordination_research_2026_10.md)
and [ten additional delivery investigations](../08_investigacion/connected_coordination_delivery_research_2026_10.md);
the owner's subsequent request for a living system with coherent graphical edits,
propagation and warnings, supported by [three focused investigations](../08_investigacion/connected_editing_and_validation_research_2026_10.md).<br>
**Reviewed baseline:** Git commit `24479a9`, with a clean working tree before this document.<br>
**Delivery review baseline:** Git commit `d5ea6ca`, containing v0.2 and the first research round.<br>
**Authority:** recommendation only. Recording this assessment does not adopt a design,
change scope or cost, promote a drawing, or close a professional design gate.

**Revision note:** v0.4 turns the preceding contracts into seven phases and 22 subphases,
with entry dependencies, scope, outputs and completion criteria. It defines how graphical
edits become model changes, how rules and calculations respond, and how partial coverage
is exposed. It draws on 25 investigations. The owner's window/door/column examples explain
desired behaviour; they are not findings of actual clashes or instructions to implement
those examples literally. All proposed capabilities remain unimplemented by this update.

## 1. Recommendation and project intent

The target is a living project system: one resolved model per scenario supplies the
drawings, calculations, quantities and coordination findings. A supported edit made from
a drawing changes that model through an explicit command; Python evaluates the resulting
state and regenerates its dependent representations. Start with one element family and
complete that connection, then extend the same mechanism to the rest of the house.

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

Start with **Phase 0: establish the current baseline and its edit ownership**. The first
useful output is a comparison report for current sources and window measurements. The
core change/evaluation mechanism precedes graphical editing. [Section 5](#5-phases-and-subphases)
is the implementation sequence; section 8.1 maps the earlier C01–C06 packages into it.

"Automatic" initially means that one Python command evaluates a complete candidate and
updates all supported dependent outputs. Later phases add automatic refresh after an
editor action or source-file change. No supported output may silently retain the old
state; an unsupported affected output must explicitly become stale or unevaluated.

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

For v0.4, code inspection additionally covered current loader/generator call chains,
`vertical_continuity.py`, equipment checks, check aggregation, the static viewer and both
CI workflows. The following existing targeted suite was rerun: **18 tests passed**.
It verifies the existing implementation, not the proposed editing system:

```bash
python3 -m unittest dreamhouse.structure.tests.test_integrated_pipeline dreamhouse.structure.tests.test_pb_b37 dreamhouse.structure.tests.test_p2_b28 dreamhouse.structure.tests.test_stair_core_coordination
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

### 3.1 Implementation seams verified for the living-system plan

| Existing behaviour and evidence | Consequence for implementation |
| --- | --- |
| [PB b37](../../dreamhouse/generate_pb_b37.py) already maps P2 `W-*` tags to façade `GLZ-*` tags through `p2_id`; both current loaders consume D-083. | Preserve these explicit aliases and shared inputs; introduce persistent identity across existing representations. |
| `generate_pb_b37.generate(model)` reloads P2/rooflights from disk; `workstation_detail()` changes literal strings in an older detail. | A modified in-memory scenario would not automatically reach every output. New render paths need the same injected snapshot and generated dimensional labels. |
| [P2 b28 validation](../../dreamhouse/generate_p2_b28.py) checks exact D-083 values; [vertical continuity](../../dreamhouse/structure/vertical_continuity.py) raises if the expected compatible-column list changes. | Keep historical fidelity checks intact; extract reusable scenario checks that return findings for changed geometry instead of treating every intentional study as a broken historic revision. |
| The continuity audit checks candidate column lines against façade/window and door intervals; [equipment checks](../../dreamhouse/equipment/validators.py) use bodies and operating rectangles. | Useful rule implementations exist, but they do not form a complete collision model for all elements and elevations. Register their applicability, geometry assumptions and coverage. |
| [CheckResult](../../dreamhouse/model/schema.py) already carries rule IDs, outcomes and entity IDs. [Pipeline aggregation](../../dreamhouse/pipeline.py) counts selected groups; support/structural results are separate, and some evidence prose contains fixed scenario facts. | Extend the existing result interface with coverage and purpose-specific blocking policy; generate narratives from evaluated facts and register every claimed check group. |
| [The current viewer](../../showcase/app.js) changes image sources and uses CSS transforms for zoom/pan. | Screen movement currently changes presentation only. A model editor needs semantic selection, inverse view transforms and a repository-connected Python command path. |
| [Current publication](../../.github/scripts/sync_current_drawings.py) copies explicitly catalogued issues; [showcase CI](../../.github/workflows/showcase.yml) regenerates aliases automatically on main. | Keep source promotion explicit while automating synchronization after promotion; candidate builds must remain separate from that path. |

These are implementation observations, not new architectural conflicts. No actual
door/window/column interference is asserted on the basis of the owner's examples.

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
| Edit ownership | Owning source/field, writable scenario layer, inherited versus derived fields and permitted commands | Ensure one edit updates a governed input rather than a copied view value. |
| Geometry capability | Supported representation, extents/elevation interval, approximation and missing data | Distinguish an evaluated physical relationship from a diagram or unsupported check. |

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

### 4.3 Views and dimensions must declare what they represent

Each proposed view record should carry a view ID, scenario, purpose, projection basis,
scale and crop, plus a cut plane and depth range where applicable. Drawing layers should
distinguish cut elements, projected elements and schematic annotations. A plan symbol
above the cut plane can remain useful if identified as such; it should not imply that
the plane cuts that window. Follow [R18](../08_investigacion/connected_coordination_delivery_research_2026_10.md#r18).

Dimensions should reference the element and named geometric anchors, such as opening
left/right limits or sill/head, with a declared measurement direction and datum. Generate
their numbers from those anchors, retaining unrounded values for calculation and applying
rounding only for display. Record label positions separately. A deleted or ambiguous
anchor should produce an unresolved dimension rather than preserve an apparently valid
old number. These are proposed association rules from
[R19](../08_investigacion/connected_coordination_delivery_research_2026_10.md#r19), not an
instruction to replace the SVG generators with a CAD application.

Information requirements should depend on **element + intended use + delivery milestone**.
A coordination view needs location, dimensions, source and open interfaces; a procurement
package additionally needs reviewed performance requirements and comparable product
evidence. Later installation and maintenance uses need different records. Show coverage
against the selected purpose, including what is unknown, without assigning one global
completion percentage to the house. [R20](../08_investigacion/connected_coordination_delivery_research_2026_10.md#r20)
provides the information-delivery basis; project milestones remain governed locally.

### 4.4 First connected detail plate

Use `GLZ-WS-A` to demonstrate one readable review plate. The following proposed views
share the same selected identity and link back to the same source and issue records:

| View or panel | Automatically derived content | Evidence that remains to be developed |
| --- | --- | --- |
| Location plan | Opening position, host reference and affected workstation | An unresolved host identity is visible until mapped. |
| Elevation | Opening width, sill, head and dimensional anchors | Frame subdivisions and net glass require supported assembly data. |
| Vertical interface section | Opening extents and references to head and sill | Header, support, drainage and thermal interfaces need professional detail development. |
| Head / sill / jamb schematics | Parameter links and callouts to the selected opening | Materials, layer thicknesses, fixings and tolerances remain unresolved where no source exists. |
| Quantity and change panel | Named opening measurement, formula and study delta | Glass area, rates and quotation comparability remain separately pending. |
| Interface evidence panel | Open items, responsible roles, source and required evidence | Approval is recorded through existing project governance. |

For each head, sill and jamb, trace the intended water-management, air-control and thermal
continuity across the window-to-wall interface. Use explicit unresolved segments where
the assembly has not been designed. A visually continuous line is evidence of a drawing
relationship only; it is not proof of watertightness, condensation resistance or structural
adequacy. Research [R21](../08_investigacion/connected_coordination_delivery_research_2026_10.md#r21)
supports these questions without selecting an assembly for Boyacá.

This plate should help the owner see which detail matters next: for example, the opening
size may be consistent while the path by which sill water reaches the exterior is still
undefined. That uncertainty is a useful project output in its own right.

### 4.5 One model, several editing and reading surfaces

The proposed flow is deliberately asymmetric: a drawing may initiate a model edit, while
its rendered geometry remains a projection of the resulting model. Plan, elevation and
section files do not update each other by copying SVG coordinates.

```mermaid
flowchart TD
    S[Versioned sources and explicit scenario] --> M[Resolved model snapshot]
    UI[Semantic SVG controls or property form] --> C[Typed change command]
    CLI[Repository JSON change or Python command] --> C
    M --> C
    C --> T[Check base revision and apply to a copy]
    T --> N[Candidate model snapshot]
    N --> V[Domain rules and coverage]
    N --> Q[Quantities and dependent calculations]
    N --> D[Plans, elevations, sections and details]
    V --> R[Complete review package with findings]
    Q --> R
    D --> R
    R --> UI
    R --> G[Explicit adoption and publication process]
```

Keep three concerns explicit:

| Concern | Proposed ownership and behaviour |
| --- | --- |
| Authoring information | Each parameter has one declared source/owner. Existing historical JSON/delta chains remain readable and hash-verifiable. New studies record edits against a named base; accepting a study creates a governed new baseline rather than modifying a released issue in place. |
| Resolved scenario | Load/normalize sources once into one snapshot with units, placements, identity, relationships and provenance. Calculations and renderers receive that snapshot. Persisted resolved snapshots are derived artifacts, not competing writable masters. |
| Presentation | View records, annotation positions, sheet layout and styling are stored separately from building geometry. Moving a label changes the sheet; moving an element changes its model parameters and all affected projections. |

During migration, record field ownership and switch each consuming family to the resolved
model as a unit. Compatibility adapters can supply old dictionary shapes, but may not
silently reread a different source or maintain their own authoritative copy. Preserve
historical generators as reproducible historical entry points.

Provide a small Python coordination interface, provisionally three operations:
`resolve_project(scenario)`, `evaluate_change(snapshot, command)` and
`build_review(snapshot, evaluation, output_dir)`. These are proposed interface names,
not existing commands. The result exposes input fingerprint, changes, findings, affected
outputs and coverage. Extend model loading and the pipeline at these seams; use a small
`dreamhouse/coordination/` module for change/evaluation orchestration only where it brings
shared behaviour together. Keep calculations testable without a browser or file writes.

### 4.6 What editing a connected SVG means

**Supported model editing:** select an element in an inline SVG and edit its properties
or use a constrained handle. Selection resolves `entity_id`, scenario and model revision.
The editor converts the gesture into a typed command specifying allowed parameters,
units, expected prior values and the base fingerprint. For example, a host-relative
position edit has a direction and datum; a resize declares the fixed anchor. This is a
generic mechanism, not a request to change any current opening.

Convert screen coordinates through the inverse SVG transform and the declared view-to-
model transform. Zoom, pan, mirrored views and sheet scaling must not alter the resulting
model edit. A 2D view does not determine hidden depth: use an explicit host plane and
permitted degrees of freedom, otherwise require a property entry or another view. Apply
existing modular/dimensional constraints as identified rules; preview violations without
silently snapping, changing related parameters or moving another element.
[R23](../08_investigacion/connected_editing_and_validation_research_2026_10.md#r23)
provides the transform and interaction basis.

**Presentation editing:** label movement, line styling and view placement update only
the applicable view/annotation record. Distinguish these controls visibly from geometry
controls and preserve such edits when regenerating the view.

**Externally edited SVG:** arbitrary paths, flattened groups or manually changed dimension
text do not provide a reliable inverse building model. Detect changed generated artifacts
through provenance checks and present them as divergent. A future import adapter may
accept a documented subset of semantic edits, with identity, base revision and transform
validation, but must reject ambiguous imports. Full arbitrary-SVG reconstruction is not
a prerequisite for the connected editor.

The current static presentation has no repository-writing path. Deliver the complete
automatic loop through a local Python process that serves the editor and accepts the
same validated commands used by the CLI. Keep it on the local interface, accept declared
command fields rather than arbitrary file paths, validate origin/request intent, and
serialize writes with base-revision rechecks. This is a local working tool; public Pages
remains a viewer and can export a proposal for CLI import. Export alone is a useful early
fallback but does not satisfy completion of the automatic graphical-editing phase.

After each completed edit, the Python response identifies the evaluated revision and its
output package. Refresh every dependent view from that revision. Distinguish transient
drag previews from Python-verified results, and discard responses for superseded requests.
No browser geometry preview may impersonate a completed coordination calculation.
Saved issue viewpoints retain their original snapshot and view definitions; reopening
one must not silently substitute the latest model. Undoing a saved edit creates a new
reversal command against the current revision, preserving intervening work and history.

### 4.7 Rules, findings and useful warnings

Reuse `CheckResult` and existing validators through a common rule contract. Each rule
declares its version, purpose, applicable element kinds/relationships, required fields,
geometry capability, numerical tolerance, consumed inputs and dependencies. A result
adds coverage, severity, affected identities, scenario/fingerprint, measured evidence,
explanation, relevant view references and its disposition for the selected issue purpose.
Preserve `PASS`/`OPEN`/`FAIL` as check outcomes; use a separate coverage field such as
`evaluated`, `not_run`, `unsupported` or `inapplicable`. An evaluation exception records
its error and leaves dependent work unevaluated. Severity and release blocking depend on
the declared rule and purpose, not merely on the colour of a viewer badge.

| Situation | Required response |
| --- | --- |
| Invalid command, stale base, duplicate identity, impossible units or broken mandatory references | Reject the mutation; return the diagnostic; retain the prior snapshot. |
| Supported rule establishes an interference or requirement violation | Retain an explicitly problematic study for inspection, report `FAIL` and its evidence, and apply the issue-purpose release gate. Never auto-resolve by moving another element. |
| Candidate overlap with approximate geometry, missing elevations, unsupported shape or unavailable analysis | Report `OPEN` with unevaluated/approximate coverage and the missing inputs; a potential conflict remains distinguishable from a confirmed modeled conflict. |
| Supported applicable rule passes | Report `PASS` together with its actual scope and evidence. This does not close a professional review. |
| Rule is inapplicable | Record the reason in coverage; exclude it from the applicable denominator instead of counting a pass. |

Keep numerical comparison tolerance, physical clearance and construction tolerance
separate under [R16](../08_investigacion/connected_coordination_delivery_research_2026_10.md#r16).
SVG label collision checking remains drawing QA; its sheet-space bounds are not building
collision geometry. For model coordination, distinguish body interference, required free
space, operational envelopes and visual obstruction. A column appearing behind a window
in an elevation is not enough to establish physical intersection or a defined view-quality
violation. Any such rule needs the relevant depth, height and purpose information.

Initially use conservative candidate-pair filtering and supported rectangular/prismatic
checks with explicit elevation intervals. A broad bounding-box overlap is a candidate,
not a final collision verdict. Rotated or complex geometry must either have an adequate
supported test or remain unevaluated. Unknown extents cannot silently eliminate an element
from the applicability list. Legitimate host/opening/filling relations also need explicit
handling so intended assembly relationships are not reported as generic collisions.
[R24](../08_investigacion/connected_editing_and_validation_research_2026_10.md#r24)
supports this separation without requiring IFC adoption or a general solid-model engine.

Findings should have stable keys based on rule and affected entities within a scenario,
so a rerun can identify new, persistent, resolved and no-longer-evaluated findings. An
automatic finding resolving after a study edit does not close a `CF-*` governance record.
Link it to the existing register and retain the evidence revision and responsible role.

### 4.8 Propagation is an explicit dependency contract

Maintain the semantic relationship graph separately from the acyclic calculation/build
graph. Reciprocal building relationships are normal; circular calculated dependencies
must be detected or handled by an explicitly defined solver, never by endless regeneration.
Start by rebuilding the complete pilot package on each accepted study edit. Add selective
recomputation only after it agrees with full rebuilds on the same scenario.

| Change class | Required propagation within declared coverage |
| --- | --- |
| Create, remove or retype an element | Recheck identities, incoming/outgoing references, rule applicability and expected view occurrences. Retire removed identities explicitly; never reuse them for a different physical element or silently discard dependent annotations/issues. |
| Position, size, level, host or orientation | Re-resolve relationships and nearby candidate pairs; update applicable plans/sections/elevations, dimensions, opening/host quantities, rules and interface evidence. Recompute neighbours from the new state, including previously unrelated elements. |
| Type, material or assembly property | Re-evaluate applicable details, mass/load inputs, quantities, rate mapping and performance evidence. Missing engineering/product data stays pending. |
| Rule, generator, transform, schema or font input | Invalidate the affected checks or outputs even when building geometry is unchanged. |
| Annotation or sheet layout only | Regenerate affected views/graphic QA; preserve physical geometry and calculated quantities. |
| Source changed outside the editor | Compare source hashes, re-resolve the declared scenario and invalidate dependent outputs; retained baseline guards may require a new version rather than an in-place rewrite. |

A move may leave area unchanged while altering interference and access checks. A material
edit may leave geometry unchanged while invalidating a mass calculation. Unknown dependency
scope requires conservative invalidation. Record why each output was recomputed, unchanged
or left unevaluated; never label a skipped structural calculation current by default.

Before accepting a mutation, recheck its expected base inside the serialized writer
operation. Applying edits to a copy and validating them is insufficient if another edit
can replace the base between checking and saving. Preserve the command and resulting
snapshot as study evidence, with no partial persistence on failure.
[R25](../08_investigacion/connected_editing_and_validation_research_2026_10.md#r25)
supports the concurrency principle; no hosted multiuser application is required.

Stage the snapshot and all outputs required at the current capability level before
advancing the working-scenario pointer. Recheck the base during that final serialized
operation. A failed render may retain a diagnostic candidate, but cannot replace the last
complete working package or the current publication. A valid package may contain modeled
coordination failures; completeness and design acceptability are different conditions.

## 5. Phases and subphases

The phases below replace the earlier C01–C06 delivery order. Every phase has an observable
exit gate; each subphase states its dependencies, scope and completion evidence. Phase
completion means that its software/data contract works for the stated scope, not that
the house is approved for construction. All phases are currently **planned**.

```mermaid
flowchart LR
    P0[0. Current baseline] --> P1[1. Connected model]
    P1 --> P2[2. Changes and rules]
    P2 --> P3[3. Derived views]
    P3 --> P4[4. Reliable automation]
    P4 --> P5[5. Graphical authoring]
    P5 --> P6[6. Whole-project rollout]
```

Start with windows, their host references, affected spaces and the available structural
context. This is the first complete path through the system, not a permanent window-only
architecture. All formulas, rules and edit permissions remain explicit about the model
families they support. Use the existing Python/JSON/SVG stack and a local editor with a static frontend;
introduce additional geometry or infrastructure only for a demonstrated capability gap.

<a id="phase-0"></a>

### Phase 0 — Establish the current baseline and ownership

**Objective and scope:** understand exactly which present sources, loaders, outputs and
checks describe the current house. Produce a trustworthy baseline for the pilot without
redesigning it. **Entry:** repository governance and current catalog reviewed.

| Subphase | Depends on | Scope and objective | Output and completion criterion |
| --- | --- | --- | --- |
| <a id="phase-0-1"></a>0.1 — Source and consumer inventory | Entry | Inventory current PB b37/P2 b28/D-083, stair, structure and rooflight sources; follow transitive loader/code dependencies. Classify all catalogued drawing outputs (27 at the reviewed baseline) by source scenario and generator. Identify direct inputs, derived fields, aliases and intended edit owner. | Source/consumer matrix with paths, revisions, statuses, source hashes and field ownership. Every pilot input and affected output has an owner or an explicit unresolved mapping; no silently selected conflicting source. |
| <a id="phase-0-2"></a>0.2 — Capture existing behaviour | 0.1 | Run relevant existing tests and generate comparison evidence only in a temporary/review directory. Record current quantities, view extents, datums, aliases and known limitations. | Repeatable baseline fixture/report; original files and current aliases unchanged. The reviewed historical scenario and current scenario are labelled separately. |
| <a id="phase-0-3"></a>0.3 — Reconcile current inputs and measurements | 0.1, 0.2 | Assemble current loaders through a narrow read adapter. Compare same-scenario geometry; explicitly map workstation glazing and other known quantity families. Identify structure/roof inputs that remain preliminary or incompatible. | Per-opening source/geometry/measurement comparison; active/study totals separated; workstation values do not enter rooflights. Unknown families produce a diagnostic. Every unexpected difference is explained before advance. |

**Repository work:** begin at [model I/O](../../dreamhouse/model/io.py),
[current PB loader](../../dreamhouse/generate_pb_b37.py),
[current P2 loader](../../dreamhouse/generate_p2_b28.py),
[opening schedule](../../dreamhouse/envelope/openings.py) and
[quantity ledger](../../dreamhouse/quantities/ledger.py). Retain `project_v04.json`'s
historical scenario definitions; add an explicitly identified current scenario rather
than silently reinterpreting `D059_P2_REFINED_ENVELOPE`.

**Exit gate:** a reviewer can trace each pilot measurement to its source and explain its
scenario. Open engineering gates are visible and do not prevent a labelled schematic
comparison. This is the first useful deliverable even before a graphical editor exists.

<a id="phase-1"></a>

### Phase 1 — Establish the connected model contract

**Objective and scope:** resolve one authoritative snapshot for the selected scenario,
with sufficient identity, relationships and geometry for pilot calculations and views.
**Entry:** Phase 0 parity and source mapping accepted for this implementation scope.

| Subphase | Depends on | Scope and objective | Output and completion criterion |
| --- | --- | --- | --- |
| <a id="phase-1-1"></a>1.1 — Identity and geometry | Phase 0 | Normalize pilot elements and their actual host/space/structural context; retain `W-*`/`GLZ-*` aliases. Define units, axes, datums, placement, geometry capability and immutable snapshot revision. | Versioned contract and normalized registry. IDs survive ordering/label changes; source-derived dimensions agree with the baseline; missing host/depth/height information is explicit, never invented. |
| <a id="phase-1-2"></a>1.2 — Relationships and dependency inventory | 1.1 | Describe host/opening/filling, located-in-space, type and view occurrences; separately declare data-to-rule/calculation/output dependencies. Identify inherited/derived fields and input edit ownership. | Reference validation and dependency report. No dangling mandatory relationships; calculation cycles are diagnosed; affected consumers are enumerable and geometry changes explicitly require a fresh neighbour search. |
| <a id="phase-1-3"></a>1.3 — Validation and adapter interface | 1.1, 1.2 | Put schema checks before domain checks. Expose one resolver that supplies the same snapshot to all consumers. Define byte/model/build fingerprints and numerical policies. | Reordered JSON formatting preserves the declared normalized meaning; duplicate keys/non-finite values fail; historical hashes still verify. Adapters reproduce baseline semantics without independent hidden file reads or writable copies. |

**Repository work:** extend [model types](../../dreamhouse/model/schema.py) and model I/O;
reuse [rectangle operations](../../dreamhouse/geometry/rectangles.py). Keep the new contract
small enough for current callers. A source content hash identifies a revision, not an
element. `canonical_json_hash()` currently uses Python sorted-key serialization; define
its policy explicitly and do not label it RFC 8785 compliant without full conformance.
Record numerical tolerance separately from physical requirements and display rounding.

**Exit gate:** a source-to-element-to-consumer path can be followed both ways for every
pilot element. Read-only historical adapters and new scenario authoring have unambiguous
ownership; all consumers can receive the same snapshot without reconstructing it.

<a id="phase-2"></a>

### Phase 2 — Evaluate changes and coordination findings in Python

**Objective and scope:** make changes and their consequences testable without a browser.
Support declared pilot parameters and rules; expose gaps in the remaining model.
**Entry:** Phase 1 contract passes its fixtures.

| Subphase | Depends on | Scope and objective | Output and completion criterion |
| --- | --- | --- | --- |
| <a id="phase-2-1"></a>2.1 — Typed change transaction | 1.3 | Define supported operations, parameter ownership, units, fixed anchors, base fingerprint and expected values. Apply changes to a copied snapshot and serialize candidate persistence. | Shared command interface for CLI and future editor. Stale-base, unsupported edits and invalid references leave the prior state unchanged; multi-operation failures never partly persist. An intentionally problematic but structurally valid study remains inspectable. |
| <a id="phase-2-2"></a>2.2 — Rule registry and geometric coverage | 1.3 | Adapt existing equipment, opening, continuity and programme checks; separate historical fixed-value assertions from generic rules. Register applicable pair types, bounds, height requirements, tolerances and purpose-specific severity. | Unified findings and coverage report. Positive, negative, boundary and missing-data fixtures behave correctly; a plan-only overlap cannot become an unsupported 3D claim. Domain findings remain available even when a legacy evaluator needs an adapter. |
| <a id="phase-2-3"></a>2.3 — Change impact and finding lifecycle | 2.1, 2.2 | Evaluate candidate relationships, measurements and affected calculations. Recompute possible neighbours from the new geometry. Compare findings with the base; link evidence and manual gates. | Before/after report with changed inputs, affected entities/outputs and new/persistent/resolved/unevaluated findings. Move-only cases preserve area while still reevaluating neighbours; changed data invalidates linked professional evidence without auto-closing a conflict. |

**Repository work:** reuse [CheckResult](../../dreamhouse/model/schema.py),
[equipment validators](../../dreamhouse/equipment/validators.py),
[vertical continuity](../../dreamhouse/structure/vertical_continuity.py),
[support comparison](../../dreamhouse/structure/coordination.py) and current quantity
functions behind the evaluation interface. Preserve historical regression tests. Move
scenario-specific expected totals/compatible-ID assertions into the appropriate baseline
checks, while retaining reusable geometry calculations for new trials. Missing essential
geometry must produce a finding/coverage gap before downstream calculation is attempted.

JSON Patch remains optional. If selected for command encoding, address stable entity-map
keys rather than array indices, keep scenario metadata outside the operation list, and
apply expected-value preconditions. Existing historical delta formats remain supported.

**Exit gate:** an unadopted synthetic change produces a deterministic model delta and
traceable findings. The owner's examples guide the general capability, not the choice of
real geometry to alter. No general solver, autonomous layout correction or construction
approval is part of this gate.

<a id="phase-3"></a>
<a id="52-connect-one-element-family-to-multiple-views"></a>

### Phase 3 — Derive connected drawings, dimensions and detail evidence

**Objective and scope:** make the pilot's every supported representation consume the
same evaluated snapshot. **Entry:** Phase 2 can evaluate changes and report consequences.

| Subphase | Depends on | Scope and objective | Output and completion criterion |
| --- | --- | --- | --- |
| <a id="phase-3-1"></a>3.1 — Inject the snapshot into outputs | Phase 2 | Adapt pilot renderers/schedules to accept model inputs explicitly; extract geometry/measurement logic from file loading and presentation. Replace copied numeric prose in the new path with evaluated values. | A candidate passed to the builder reaches all pilot consumers. No migrated output reloads adopted P2/rooflights behind the caller's back; unchanged baseline views remain equivalent within documented graphic changes. |
| <a id="phase-3-2"></a>3.2 — Semantic views and associated annotations | 3.1 | Add persistent view IDs, occurrence IDs and `data-entity-id`; define projection/cut intent and model-to-view transforms. Bind dimensions to named anchors; bind callouts to view/detail IDs. | Same element resolves across plan/elevation/section. Coordinate/datum fixtures agree; deleted anchors flag unresolved dimensions; renaming a sheet preserves callout targets; duplicated DOM IDs fail validation. |
| <a id="phase-3-3"></a>3.3 — Complete pilot review plate | 3.1, 3.2 | Build the section 4.4 plate plus schedule and findings. Separate projected geometry, assembly schematics, operational envelopes and graphical QA. Link head/sill/jamb evidence by scenario. | Every inventoried pilot occurrence is refreshed or explicitly unavailable; no stale drawing is presented as current. A dimensional change reaches all represented views and the named quantity; schematic layer continuity remains an open design matter where appropriate. |

**Repository work:** reuse [SVG sheet](../../dreamhouse/svg/sheet.py),
[SVG layout](../../dreamhouse/svg/layout.py), [theme](../../dreamhouse/svg/theme.py) and
existing pilot QA. Keep standalone SVG/PNG export. Replace the new detail path's dependence
on `workstation_detail()` string substitutions with parameter-driven annotations while
leaving historical outputs reproducible.

**Exit gate:** a full pilot rebuild responds coherently to a model edit, including its
dimensions and warnings. Report an occurrence-coverage denominator; a good-looking plan
alone cannot satisfy this phase if the elevation or detail still carries old values.

<a id="phase-4"></a>

### Phase 4 — Make the complete Python workflow reliable and repeatable

**Objective and scope:** one execution builds a coherent review package and prevents
mixed-revision publication. **Entry:** Phase 3's complete pilot path works.

| Subphase | Depends on | Scope and objective | Output and completion criterion |
| --- | --- | --- | --- |
| <a id="phase-4-1"></a>4.1 — One candidate-build command | Phase 3 | Extend the pipeline to resolve/evaluate/build from explicit inputs and a review output directory. Emit manifest, model snapshot, changes, findings/coverage, quantities and drawings together. | One documented Python command reproduces the package in a clean location. Matching inputs/code/environment produce matching deterministic artifacts; late failure cannot alter current aliases or released packages. |
| <a id="phase-4-2"></a>4.2 — Invalidation and CI | 4.1 | Cover transitive data, generator, rule/schema, renderer/font dependencies in CI. Run the fast geometry/contract path routinely; schedule required slower analysis and mark skipped results unevaluated. Begin with full pilot rebuilds. | Data-only and generator-only changes trigger relevant checks; a skipped analysis never reports freshness. Review artifacts include machine-readable findings, visual comparisons and a contact sheet. Selective caching is allowed only after equality with full builds is demonstrated. |
| <a id="phase-4-3"></a>4.3 — Purpose-specific release and recovery | 4.1, 4.2 | Separate candidate availability, coordination findings, issue-purpose eligibility, design adoption and publication. Verify inventory/hashes before explicit catalog promotion; retain previous releases and define stable-alias compatibility. | A warning-bearing study can be inspected without being declared approved. An injected incomplete build leaves current publication intact; readers cannot select a mixed release. Prior complete issues remain recoverable through their manifests. |

**Repository work:** extend [pipeline.py](../../dreamhouse/pipeline.py),
[current-drawing synchronization](../../.github/scripts/sync_current_drawings.py) and
[workflows](../../.github/workflows/). The existing CLI writes to a versioned integration
directory by default; candidate execution must use an explicit isolated destination.
Keep existing command compatibility and label any new CLI examples as proposed until
implemented. Do not conflate the current `issue_ready` aggregate with whole-project
approval; show the purpose, participating checks and coverage behind every new gate.

The showcase job may continue synchronizing already promoted catalog entries. Changing
the catalog's sources is the explicit publication action. If using a release pointer,
first make readers resolve through it and address the stable aliases; separate atomic
file replacements do not constitute a complete-publication transaction.

**Exit gate:** the repository already behaves as a connected system when Python runs,
without a graphical editor. Every pilot consumer belongs to the same build or visibly
reports its limitation; automated checks cannot silently promote a design.

<a id="phase-5"></a>

### Phase 5 — Edit model parameters from the graphical views

**Objective and scope:** provide the owner with a visual entry point to the tested Python
workflow. **Entry:** Phase 4 is reliable; rendering, units and command semantics already
work headlessly. Begin with the pilot's declared edit capabilities.

| Subphase | Depends on | Scope and objective | Output and completion criterion |
| --- | --- | --- | --- |
| <a id="phase-5-1"></a>5.1 — Connected selection and evidence | Phase 4 | Mount validated semantic SVG inline; link selected identities across views, searchable list, quantity panel and findings. Provide scenario/revision/freshness labels and keyboard access. | Pointer/list/keyboard selection resolves the same entity and evidence. Warnings focus all affected objects in available views; status remains understandable without colour. Public static viewing still works. |
| <a id="phase-5-2"></a>5.2 — Forms and constrained graphical commands | 5.1, 2.1, 3.2 | Implement property edits first, then handles that produce the same commands through screen/SVG/model transforms. Separate annotation controls, declare fixed anchors and show proposed changes before saving. | Equivalent form and drag edits generate equivalent model commands despite zoom/pan/mirroring. Missing projection depth or unsupported handles cannot invent coordinates. Undo of an unsaved edit restores its base; changing text alone cannot change a physical dimension. |
| <a id="phase-5-3"></a>5.3 — Local Python round trip and refresh | 5.2, 4.1 | Connect the local editor to the serialized Python writer/evaluator. Save explicit study edits, rebuild the candidate and refresh all dependent views/findings from the returned revision. Provide command export/import for the static site. | A supported graphical edit, Python evaluation and all affected view/calculation updates complete without manual SVG copying. Stale concurrent proposals are rejected; stale asynchronous responses are discarded; a failed command leaves the preceding candidate intact. |

**Repository work:** use the [existing showcase](../../showcase/) for presentation assets,
but keep editing logic in a small dedicated module/page rather than enlarging the current
gallery's zoom handler. The local Python adapter calls the same evaluation interface as
the CLI. Use validated repository-generated SVG, a fixed command schema, local binding,
request-origin checks and explicit permitted write locations. No repository credentials
belong in public JavaScript. A hosted multiuser editor is outside this first rollout.

**Exit gate:** one declared model edit from a supported SVG view propagates automatically
and shows new findings or explicit coverage gaps. Public static command export alone does
not meet this gate. Arbitrary external SVG import remains separately scoped; provenance
checks detect such edits instead of pretending they are synchronized model changes.

<a id="phase-6"></a>

### Phase 6 — Extend the mechanism across the house and keep it maintainable

**Objective and scope:** move from one working family to the current project's elements,
engineering interfaces and outputs without introducing new independent data masters.
**Entry:** Phase 5 demonstrates the complete edit/evaluate/render cycle.

| Subphase | Depends on | Scope and objective | Output and completion criterion |
| --- | --- | --- | --- |
| <a id="phase-6-1"></a>6.1 — All opening, wall and structural-context families | Phase 5 | Extend identity, source ownership, geometry capability and rule applicability to remaining windows, doors, hosts and available column/support context. Add capabilities according to actual source data, not the owner's illustrative clashes. | Family/operation/view/rule coverage matrix includes every inventoried element. Supported changes propagate across relevant views and schedules; unsupported engineering geometry remains explicitly unevaluated. Alias and deletion/reference tests apply to each enrolled family. |
| <a id="phase-6-2"></a>6.2 — Stair, wall/load and cost dependencies | 6.1 | Connect SC-01 across levels, landing/discharge views and support studies; connect wall/opening measurements to available mass/load and cost inputs. Preserve CF-009/010/011/012 and professional review roles. | Changes invalidate/recompute actual consumers, including relevant sections and calculation evidence. Missing product masses, rates or design rules remain unknown. A reviewer can trace a model parameter through a quantity/calculation to the affected decision gate. |
| <a id="phase-6-3"></a>6.3 — Services, interfaces and phased handover | 6.1 | Enrol supported service routes, operating/removal envelopes and Phase 1/2 reservations. Use purpose-specific required information and progressive maintenance records. | Plans, access checks and interface records share IDs; planned/reserved/installed/tested/commissioned states remain distinct. A changed reservation invalidates affected closure/testing evidence; no unselected product or unknown route becomes fabricated geometry. |
| <a id="phase-6-4"></a>6.4 — Current-set rollout and extension protocol | 6.2, 6.3 | Reconcile all catalogued current views and calculations with the capability matrix; finish affected renderer migrations. Document adding a family/rule/view/source and routine rebuild/recovery. Add optional debounced source watching using the same pipeline. | Every active output that consumes enrolled data regenerates coherently; stale or incompatible outputs block a complete current issue until resolved. All exclusions/unknowns are explicit. A fresh checkout reproduces the review package; adding a fixture family proves the extension path without a parallel source of truth. |

**Repository work:** expand existing discipline modules and register their inputs/results
with the shared model and evaluator. Keep family-specific engineering in those modules;
do not collect unrelated physics into one universal clash function. New rule thresholds
need a source and responsible role. Existing semantic relationships may support later
IFC/BCF/IDS exchange, but exchange tooling is not required for the internal rollout.

**Exit gate:** the current set has an auditable coverage matrix linking elements, edit
capabilities, views, calculations and evidence. Missing professional inputs remain visible;
there are no silent, obsolete copies for enrolled data. A future change follows the same
recorded command/dependency path rather than requiring manual edits across sheets.

### Sequencing and cost controls

Phases 0–4 deliver the core value through Python before investment in editing controls.
Phase 5 adds the graphical input surface; Phase 6 repeats the proven mechanism. View
design and read-only inventories for later families can be prepared earlier, but cannot
claim a completed phase before their dependencies pass. Within Phase 2, rule fixtures
and command parsing can proceed independently once Phase 1's contract is stable.

Use full pilot rebuilds, existing generators and small local JSON records first. Add
incremental caches, more general geometry, a database or an always-running watcher only
when measured work requires them. Preserve baseline regression tests while adding
behavioural tests for changes; avoid tests that merely reproduce implementation formulas.
No calendar commitment or software-cost allowance is established by this plan.


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

### 6.2 Additional delivery acceptance evidence

These ten further fixtures turn the second research round into observable behaviour.
They are proposed tests for implementation, not checks claimed to have passed today.

| Research | Concrete acceptance evidence |
| --- | --- |
| [R13 — Migration](../08_investigacion/connected_coordination_delivery_research_2026_10.md#r13) | Current loaders and adapter agree on geometry and source identity for PB b37/P2 b28; the report separately identifies the intended quantity-classification correction. |
| [R14 — Study edits](../08_investigacion/connected_coordination_delivery_research_2026_10.md#r14) | A patch prepared against an older base fails without changing inputs or current output; reordered records cannot redirect the edit to another opening. |
| [R15 — Fingerprints](../08_investigacion/connected_coordination_delivery_research_2026_10.md#r15) | Formatting-only JSON edits change the byte hash but preserve the normalized fingerprint under its declared policy; duplicate keys and non-finite numbers are rejected. |
| [R16 — Numerical boundaries](../08_investigacion/connected_coordination_delivery_research_2026_10.md#r16) | Tests distinguish touching, a small gap and actual overlap; changing printed decimal places changes no geometry or clearance verdict. |
| [R17 — Complete releases](../08_investigacion/connected_coordination_delivery_research_2026_10.md#r17) | An injected late render failure leaves all previously published files unchanged; the failed candidate is not a promotable issue. |
| [R18 — View intent](../08_investigacion/connected_coordination_delivery_research_2026_10.md#r18) | Moving a plan cut plane changes cut/projected membership where supported, while preserving element identity and model quantities. |
| [R19 — Dimensions](../08_investigacion/connected_coordination_delivery_research_2026_10.md#r19) | A width edit updates its associated dimension and area; deleting a referenced anchor creates an unresolved annotation rather than a stale value. |
| [R20 — Information need](../08_investigacion/connected_coordination_delivery_research_2026_10.md#r20) | The same window can satisfy coordination fields while remaining incomplete for procurement; missing product evidence remains visible. |
| [R21 — Envelope interfaces](../08_investigacion/connected_coordination_delivery_research_2026_10.md#r21) | Head, sill and jamb records link to the selected window and show unresolved continuity; dimensional consistency does not close the envelope review. |
| [R22 — Handover](../08_investigacion/connected_coordination_delivery_research_2026_10.md#r22) | A Phase 2 provision is distinguishable from installed equipment; maintenance links survive renaming, and absent manufacturer data stays unknown. |

Advance by demonstrated connections, not by the total number of rendered sheets. For the
pilot, report represented elements versus expected elements, resolved dimension anchors,
valid quantity mappings, current versus stale outputs, and evidence completeness for the
declared purpose. Keep these counts separate so an improved drawing count cannot conceal
missing checks or unresolved engineering.

### 6.3 Editing and validation acceptance evidence

| Research | Concrete acceptance evidence | Completion gate |
| --- | --- | --- |
| [R23 — Graphical edits](../08_investigacion/connected_editing_and_validation_research_2026_10.md#r23) | The same supported edit entered numerically or through a transformed view produces the same candidate geometry, quantities and findings; Python's returned revision appears in every affected view. | Phase 5 |
| [R24 — Meaning of a conflict](../08_investigacion/connected_editing_and_validation_research_2026_10.md#r24) | Synthetic fixtures distinguish true overlap, containment, contact, separate heights and unsupported shapes; expected results are independently specified. Missing geometry never counts as a successful check. | Phase 2, then each family in Phase 6 |
| [R25 — Concurrent edits](../08_investigacion/connected_editing_and_validation_research_2026_10.md#r25) | Two commands use the same base; after one completes, the other is rejected without partial persistence. A failed build retains the previous complete working package, and saved warnings survive reload. | Phases 2, 4 and 5 |

The integrated demonstration should cover both a parameter edit and an annotation-only
edit. For the former, inspect the model delta, dependent calculations, represented
occurrences, findings and output fingerprints. For the latter, confirm that physical
geometry, quantities and engineering results remain unchanged. Introduce a synthetic
candidate that gains a new neighbour after movement, so invalidation cannot pass merely
by rechecking the old neighbour list. Introduce a generator-only edit as a separate test.

Complete each phase with its recorded evidence, supported scope, unresolved limitations
and next dependencies. Maintain a coverage matrix whose rows identify family/operation/
view/rule combinations and whose columns distinguish implemented, evaluated, current and
professionally reviewed. Never combine those into a single completion percentage.

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

Begin with location, system, phase, access/removal envelope and evidence links for a few
maintainable components and service reservations. Distinguish planned, reserved, installed,
tested and commissioned states. Add manufacturer, serial number, warranty and maintenance
interval only when supported. A protected Phase 1 reservation should retain its location,
test and reactivation obligations without masquerading as installed Phase 2 equipment.
[R22](../08_investigacion/connected_coordination_delivery_research_2026_10.md#r22)
supports progressive handover information within the existing repository.

## 8. Delivery approach and authority

Use the existing Python, JSON, SVG and static-site foundation. Prioritize one complete,
verifiable element family and expand only after that connection works. This keeps the
software effort proportionate to the project's needs and reuses the drawing, validation
and publication work already completed.

The [foundation research](../08_investigacion/connected_coordination_research_2026_10.md),
[delivery research](../08_investigacion/connected_coordination_delivery_research_2026_10.md)
and [editing/validation research](../08_investigacion/connected_editing_and_validation_research_2026_10.md)
support adopting useful information patterns before taking on additional platforms.
Full IFC/IDS/BCF exchange, an RDF database, a general solid-model engine and a new build
framework remain deferred until a real exchange or engineering task requires them. The
immediate proposed deliverables are the current-state manifest, a validated window
registry, connected SVG views, named quantity records, linked issue evidence and a
repeatable review package. The phased target adds tested change commands, reusable
coordination rules and a local graphical authoring path using that same Python workflow.

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

### 8.1 Continuity with the preceding plan

The v0.3 work packages remain traceable below, but section 5 is now the delivery order.
Change evaluation and reliable builds move ahead of graphical authoring so the editor
uses an already tested model workflow.

| Earlier package | Current phase ownership |
| --- | --- |
| C01 — Current sources and measurements | Phase 0 establishes the baseline; Phase 1 supplies the lasting resolver. |
| C02 — Small element contract | Phase 1, including geometry capability, source ownership and dependencies. |
| C03 — Linked view geometry | Phase 3, after Phase 2 establishes change evaluation. |
| C04 — Evidence navigation | Phase 5.1; Phases 5.2–5.3 add actual graphical model editing. |
| C05 — Controlled change demonstration | Phase 2 implements the headless mechanism; Phases 3–5 demonstrate propagation. |
| C06 — Delivery reliability | Phase 4, before the automatic graphical editing loop. |

The first implementation should deliver Phase 0's source/consumer inventory, baseline
fixtures and current-window comparison. Its review questions are concrete: which source
owns each input, which current views and calculations consume it, which historical checks
must remain unchanged, and which outputs still require migration. Then advance through
the phase gates; an attractive viewer is not a substitute for resolving those questions.

### 8.2 Evidence retained at each phase gate

Store a concise gate record beside the implementation's review artifacts: phase/subphase
IDs, scenario and source/build fingerprints, supported operations and scope, checks run,
results, coverage gaps, open professional gates and links to generated outputs. The
implementation reviewer verifies software/data behaviour; responsible project disciplines
continue to review their engineering evidence under existing governance. These are distinct
responsibilities, not a new approval board.

For the first candidate, proposed artifact names are `model.json`, `changes.json`,
`findings.json`, `coverage.json`, `opening_schedule.json`, `quantity_ledger.json`,
`views/`, `review.md` and `manifest.json` in an isolated review directory. These names are
an implementation proposal, not files created by this planning update. Keep volatile run
logs separate from deterministic technical content. List each expected artifact and its
hash; a complete candidate contains every required result or an explicit unevaluated
result allowed for its stated review purpose.
