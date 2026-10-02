# Connected coordination research — October 2026

**Status:** research and proposed plan improvements; not adopted for implementation  
**Version:** 0.1  
**Date:** 2026-10-02  
**Source:** owner's request for at least ten internet investigations to strengthen the
[connected coordination plan](../06_gestion_y_obra/connected_project_coordination_next_step.md);
primary specifications and first-party technical documentation linked in each investigation.  
**Access date:** all external sources below were opened and checked on 2026-10-02.  
**Authority:** evidence for planning only. This document does not adopt a design, select
products, change scope or cost, promote drawings, or close professional gates.

## Method and interpretation

Each investigation separates a source-backed finding from its proposed application to
Dream House, and identifies evidence that could accept or reject that application.
Industry Foundation Classes (IFC), Information Delivery Specification (IDS), and BIM
Collaboration Format (BCF) provide useful concepts without requiring an immediate software
or file-format migration. IFC references below use the official 4.3.2.0 release, rather
than the parallel development documentation. Versioned releases and maintained documentation
are distinguished where relevant. Recommendations remain subordinate to the
[Project Constitution](../00_gobernanza/constitucion_del_proyecto.md) and
[source precedence and open conflicts](../00_gobernanza/fuentes_precedencia_y_conflictos.md).

The twelve investigations are distinct design questions. Each was researched online and
checked against the primary pages cited below. Standards explain information patterns;
the proposed repository implementation and acceptance fixtures are project inferences.

| Investigation | Contribution to the revised plan |
| --- | --- |
| [R01](#r01) | Persistent element identity and revision continuity |
| [R02](#r02) | Host, opening, filling and module relationships |
| [R03](#r03) | Units, placement, datums and consistent projections |
| [R04](#r04) | Applicable information requirements and explicit coverage |
| [R05](#r05) | Issues linked to preserved viewpoints and model revisions |
| [R06](#r06) | Measurement definitions before cost mapping |
| [R07](#r07) | Schema validation followed by semantic checks |
| [R08](#r08) | Complete build dependencies, reproducibility and CI coverage |
| [R09](#r09) | Provenance separate from adoption and approval |
| [R10](#r10) | Semantic SVG and a viable interaction mechanism |
| [R11](#r11) | Accessible selection, focus and status presentation |
| [R12](#r12) | Change-sequence tests and controlled visual comparisons |

<a id="r01"></a>

## R01 — Element identity that survives drawing and model revisions

**Question.** What identity can reliably connect an element across views, quantities,
issues, and successive project states?

**Source-backed finding.** IFC separates persistent object identity from names and
serialization identifiers. Its Software Identity concept requires IFC-GUID persistence
and explicitly says file-local instance numbers are not stable across exchanges.
`IfcRoot.GlobalId` supplies the unique identifier, while its optional `OwnerHistory`
records only the latest modification, not a complete revision history.
[IFC Software Identity](https://standards.buildingsmart.org/IFC/RELEASE/IFC4_3/HTML/concepts/Object_Attributes/Software_Identity/content.html),
[IfcRoot](https://standards.buildingsmart.org/IFC/RELEASE/IFC4_3/HTML/lexical/IfcRoot.htm).

**Dream House inference / proposed improvement.** Define an immutable project element ID
independent of the visible tag, list order, coordinates, or SVG primitive order. Preserve
existing tags such as `GLZ-WS-A` as recognizable references, with an explicit mapping if
they are later renamed or differentiated into opening and filling records. Store revision,
scenario, and source separately. Define continuity for edits and explicit lineage for
split, merge, retirement, and replacement; never silently reuse a retired identity.
Every SVG representation should point back to that identity while retaining its own
document-unique representation ID.

**Acceptance evidence.** Reordering source records, renaming a tag, and regenerating a
sheet preserve element links and issue references. A split records the predecessor and
new identities; duplicate identities and dangling references fail validation.

**Applicability / limits.** This can begin in JSON. An IFC-shaped GUID alone does not
establish correct identity continuity: the project needs lifecycle rules, migration maps,
and revision evidence. Introducing IFC export is a separate later task.

<a id="r02"></a>

## R02 — Separate the opening, its host, and the window that fills it

**Question.** Which relationships prevent a connected window family from conflating a
hole in the envelope with the assembly installed in it?

**Source-backed finding.** `IfcOpeningElement` represents a void and must relate to the
element it voids through `IfcRelVoidsElement`. A window, door, or other filling is a
separate element associated through `IfcRelFillsElement`; the filling may occupy only
part of the opening. An opening can have zero-to-many filling relationships. The schema
also distinguishes subtraction geometry from reference geometry that describes an
already-cut host, avoiding a second subtraction.
[IfcOpeningElement](https://standards.buildingsmart.org/IFC/RELEASE/IFC4_3/HTML/lexical/IfcOpeningElement.htm),
[IfcRelFillsElement](https://standards.buildingsmart.org/IFC/RELEASE/IFC4_3/HTML/lexical/IfcRelFillsElement.htm).

**Dream House inference / proposed improvement.** Model a small relationship graph:
`host assembly → opening → proposed filling → modules`, with separate geometry and
quantity meanings. Associate the workstation, jamb/header reservations, drainage detail,
and unresolved professional checks with the appropriate element or interface. A schematic
opening may exist before a filling product is selected. Treat its coordination envelope,
the frame envelope, glass dimensions, and clear operable passage as distinct values;
unknown product dimensions should remain unknown. Document what the existing `GLZ-*`
records actually represent before assigning new semantics to their IDs.

**Acceptance evidence.** Every active opening resolves its declared host. Removing a
filling leaves the opening and its wall deduction traceable. Changing module count does
not multiply the number of wall openings or deduct the same area twice. Unknown filling
and interface data remain visibly pending.

**Applicability / limits.** Reuse these distinctions without implementing the complete
IFC relationship schema. A host link proves a modeled relationship; it does not prove
structural capacity, waterproofing, installation tolerance, or constructibility.

<a id="r03"></a>

## R03 — Units, placement, and projections from one geometric definition

**Question.** How can plans, elevations, and sections remain numerically coherent when
their coordinate systems and display scales differ?

**Source-backed finding.** `IfcLocalPlacement` distinguishes relative placement from
absolute placement in the project representation context. A missing parent means world
placement, and prevention of cyclic placement chains is an application responsibility.
`IfcUnitAssignment` provides project unit defaults and permits explicitly defined local
units; duplicate definitions for the same unit type are disallowed.
[IfcLocalPlacement](https://standards.buildingsmart.org/IFC/RELEASE/IFC4_3/HTML/lexical/IfcLocalPlacement.htm),
[IfcUnitAssignment](https://standards.buildingsmart.org/IFC/RELEASE/IFC4_3/HTML/lexical/IfcUnitAssignment.htm).

**Dream House inference / proposed improvement.** Declare the repository's established
project axes, origin, vertical datum, and length units explicitly. Resolve elements to one
project coordinate system and give each view a documented projection, direction, clipping
rule, and drawing transform. Derive a window's sill and head from its placement and
height; keep SVG pixel coordinates and page layout downstream. Use explicit conversions
for imported millimetres or other units. Separate numerical comparison tolerance from
display rounding and from future construction tolerance.

**Acceptance evidence.** A known opening has the same width and elevation datums in plan,
elevation, schedule, and a supported section. Mirrored façade views preserve left/right
relationships correctly. A metre-to-millimetre input conversion preserves the physical
result. Placement cycles or ambiguous units stop the affected derivation. Moving a sheet
viewport changes no quantity.

**Applicability / limits.** A local project origin is enough for the first demonstration;
the exact site and survey remain pending. A shared transform does not automatically
produce correct cut geometry or hidden-line conventions. Unsupported section/detail
derivations must be identified explicitly.

<a id="r04"></a>

## R04 — Machine-readable information requirements with bounded claims

**Question.** How can the project state exactly what information each applicable element
must contain, without overstating what automated validation proves?

**Source-backed finding.** IDS 1.0 is a final buildingSMART standard. Its maintained
specification guide separates applicability, which selects elements, from requirements,
which constrain their information. It describes six facets: entity, attribute,
classification, property, material, and parts/relationships. The guide explicitly excludes
geometry checks and checks requiring calculated values or external data from this first
version's scope. Existing quantity properties can be constrained without verifying their
geometric derivation.
[IDS 1.0 release](https://github.com/buildingSMART/IDS/releases/tag/v1.0.0),
[IDS specification guide, maintained documentation](https://raw.githubusercontent.com/buildingSMART/IDS/development/Documentation/UserManual/specifications.md).

**Dream House inference / proposed improvement.** Adopt the applicability/requirements
pattern in a small repository-native check catalog before considering IDS export. Each
check should state its ID, scope, required inputs, source, responsible review role,
result, and evidence. Separate information completeness, geometric consistency, semantic
mapping, and professional assessment. Select all active windows first, then require the
necessary data; a filter that selects only already-complete records would conceal missing
information. Report the matched population so an empty result cannot look like complete
coverage.

**Acceptance evidence.** Deliberately remove a host reference or source reference from
one active opening and obtain an element-specific failure. An unsupported check reports
that status. An information-complete element can still display unresolved geometric or
professional gates. Optional studies remain identifiable outside the active check scope.

**Applicability / limits.** Native JSON checks are not IDS conformance. Actual IDS exchange
would require supported IFC data and validation against the intended IDS version. No
schema or information check establishes safe glazing, fire compliance, or structural adequacy.

<a id="r05"></a>

## R05 — Preserve issues and the exact views that explain them

**Question.** How should unresolved matters connect to selected elements and visual
evidence without losing the context in which they were raised?

**Source-backed finding.** BCF 3.0 distinguishes topics from viewpoints and snapshots.
Viewpoints describe cameras, selected/visible components, and optional visual markup;
new visualization requires a new viewpoint because viewpoints are immutable. The API
prefers an IFC GUID but permits an authoring-tool identifier when one is unavailable.
The XML documentation warns that matching relevant model files may need user assistance.
[BCF 3.0 XML technical documentation](https://raw.githubusercontent.com/buildingSMART/BCF-XML/release_3_0/Documentation/README.md),
[BCF 3.0 API specification](https://github.com/buildingSMART/BCF-API/blob/release_3_0/README.md).

**Dream House inference / proposed improvement.** Keep existing `CF-*` conflicts and
decision references as governing records. Add a derived coordination card with element
IDs, issue/scenario revision, affected view, selection, explanatory snapshot, pending
evidence, and reviewer role. Preserve the original evidence view when geometry advances;
offer a separate view of the current state and indicate what changed. For example, the
future CF-011 card should show its stair-landing and rear-opening relationship in the
relevant section without implying that the exit is approved.

**Acceptance evidence.** Opening a saved issue restores its recorded selection and
scenario, or reports the unavailable source. Regeneration preserves the prior snapshot
and creates new evidence. Retired or split elements resolve through the lineage from R01.
Closing an issue requires its governing evidence and decision, independently of graphic
highlighting.

**Applicability / limits.** Begin with local JSON/Markdown and static links. BCF export can
follow a demonstrated need. Custom IDs or a BCF-shaped record do not guarantee external
tool interoperability; mappings, coordinate conventions, schema validation, and a receiving
tool round trip would need testing.

<a id="r06"></a>

## R06 — Name what a quantity measures before connecting it to cost

**Question.** Which quantity distinctions prevent a correct area calculation from becoming
an incorrect glazing, envelope, or procurement total?

**Source-backed finding.** `Qto_WindowBaseQuantities.Area` describes the total area of the
window's outer lining; its width and height likewise describe outer lining dimensions for
rectangular windows. This is not a definition of net glass area. IFC wall base quantities
separate gross side area, which disregards modifications such as openings, from net side
area, which includes their effects.
[Qto_WindowBaseQuantities](https://standards.buildingsmart.org/IFC/RELEASE/IFC4_3/HTML/lexical/Qto_WindowBaseQuantities.htm),
[Qto_WallBaseQuantities](https://standards.buildingsmart.org/IFC/RELEASE/IFC4_3/HTML/lexical/Qto_WallBaseQuantities.htm).

**Dream House inference / proposed improvement.** Every quantity needs a named measurement
basis, element and scenario identity, unit, derivation, input revision, inclusion status,
and assembly mapping. Distinguish schematic opening area, frame-envelope area, net glass,
wall deduction, panel procurement, installed assembly count, and waste. Preserve historical
figures under their actual definitions; audit the current use of “vertical glazing” before
presenting it as a fabrication quantity. Product, cutting, overlap, accessory, installation,
and pricing assumptions require their own evidence. Do not infer installed cost by
multiplying an opening area by an unrelated unit rate.

**Acceptance evidence.** The two workstation openings map to their declared vertical
family, never a rooflight fallback. Enlarging an opening updates its measured area and
the supported host deduction exactly once. Frame and glass quantities remain pending
when dimensions are missing; procurement waste is explicit and separately evidenced.
An unknown rate remains unknown, and study-only openings remain excluded from active totals.

**Applicability / limits.** The IFC distinctions help define meaning; they do not select
the project's contractual measurement rules or suppliers. A computed geometric quantity
does not establish installed material quantities, product performance, or a validated cost.

<a id="r07"></a>

## R07 — Data contracts that reject ambiguity before drawing

**Question.** Which input checks can prevent malformed or misclassified information from
passing into every generated output?

**Source-backed finding.** JSON Schema's `properties` keyword does not itself require
properties or reject additional ones. `required` and explicit property restrictions
provide those controls; `unevaluatedProperties` accounts for composed schemas. A `null`
value differs from an absent property. The combination keyword `oneOf` accepts exactly
one matching alternative.
[JSON Schema object reference](https://json-schema.org/understanding-json-schema/reference/object),
[schema combination reference](https://json-schema.org/understanding-json-schema/reference/combining).

**Dream House inference / proposed improvement.** Define a versioned schema for the first
window registry with required identity, scenario, quantity kind, units and provenance.
Use explicit alternatives for supported element kinds and represent unknown values with
an agreed status instead of zero. Follow schema checking with separate Python checks for
duplicate IDs, dangling hosts, finite dimensions, placement consistency and valid
quantity-family mappings. Replace the ledger's catch-all rooflight classification with
an explicit mapping and an unsupported-family diagnostic.

**Acceptance evidence.** Fixtures independently reject a misspelled field, an unknown
kind, a duplicate identity, a dangling host and a vertical window assigned to a rooflight
assembly. The diagnostic names the element and the failed rule. Deliberately unknown
product information remains representable with its open status.

**Applicability / limits.** JSON Schema establishes data shape and declared constraints;
the additional domain checks establish the project's relationships. Neither layer proves
performance or professional approval. Pin the intended schema dialect when implementing.

<a id="r08"></a>

## R08 — Dependency completeness and repeatable review builds

**Question.** How can the project detect stale outputs when either inputs or generator
logic change, and ensure those changes are actually checked?

**Source-backed finding.** Bazel distinguishes actual from declared build dependencies;
correctness requires the declared graph to cover actual dependencies. Its hermetic-build
guidance treats tools and their versions as inputs and identifies host differences and
timestamps as sources of nondeterminism.
[Bazel dependencies](https://bazel.build/concepts/dependencies),
[Bazel hermeticity](https://bazel.build/basics/hermeticity).
GitHub Actions path filters determine whether changed paths trigger a workflow.
[GitHub workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax).

**Dream House inference / proposed improvement.** Keep a small Python build graph. Declare
source, generator, rule/schema, renderer and font dependencies for the outputs they
affect. Compare their fingerprints to each output's recorded build inputs; propagate
staleness through descendants. Keep the building relationship graph separate because
semantic relationships need not form an acyclic build graph. Generate review artifacts
outside preserved issues. Fix the relevant environment before claiming reproducibility.
Review CI triggers against the graph: the existing workflow path lists omit changes only
to `dreamhouse/window_daylight_d083.json`.

**Acceptance evidence.** A generator-only edit invalidates its outputs; a window-source
edit reaches coordination CI and marks dependent views/quantities stale. Equivalent clean
builds reproduce the declared outputs. A missing dependency or build cycle is diagnosed.

**Applicability / limits.** These are implementation principles, not a proposal to adopt
Bazel. Begin with correctness and a small full build; add selective caching only when
measurement justifies it. A matching hash does not establish engineering correctness.

<a id="r09"></a>

## R09 — Trace the production of evidence separately from its authority

**Question.** How should the project answer both “where did this result come from?” and
“what may it be used for?” without conflating the answers?

**Source-backed finding.** W3C PROV-O distinguishes entities, activities and agents, with
relations for used inputs, generated outputs, derivation and responsibility. It also
provides revision and invalidation relationships.
[W3C PROV-O](https://www.w3.org/TR/prov-o/).

**Dream House inference / proposed improvement.** Use a compact JSON provenance record
for each derived quantity, view and report: input references, scenario, source hashes,
producing calculation/version and output identity. Link adoption, professional review,
publication purpose and cost eligibility to their governing evidence separately. A
responsible review role may be known while its assigned person or signed evidence remains
pending. Store build-event timestamps separately when they would otherwise make
deterministic artifact content vary.

**Acceptance evidence.** From a selected quantity, the reviewer can reach its source
element, measured parameters and producing calculation. Regeneration preserves the
trace and cannot turn an open review into approval. Superseded evidence remains readable
with its source scenario and status.

**Applicability / limits.** This borrows provenance concepts; it does not require RDF,
an ontology server or PROV serialization. PROV does not define Dream House's approval
policy, and recording an author does not establish a signed professional acceptance.

<a id="r10"></a>

## R10 — Connected SVG needs semantic groups and document interaction

**Question.** What changes let a user select one building element across multiple SVG
views while retaining standalone drawings?

**Source-backed finding.** SVG supports grouped graphics, custom `data-*` attributes,
accessible names/descriptions and IDs that must be unique within a document tree.
[W3C SVG document structure](https://www.w3.org/TR/SVG2/struct.html).
SVG processing modes distinguish interactive documents from images: SVG referenced by
an HTML `img` does not expose internal interactive behaviour in its image mode; inline
SVG follows its host document's processing mode.
[W3C SVG conformance and processing modes](https://www.w3.org/TR/SVG2/conform.html).

**Dream House inference / proposed improvement.** The current image-based gallery needs
an additional document-based view for element interaction. Mount validated generated SVG
inline, and manage selection from the host page. Give each representation a view-prefixed
DOM ID and the same persistent `data-entity-id` across views. Keep names and descriptions
at meaningful element groups, rather than attaching controls to every drawing primitive.
Retain standalone SVG and PNG outputs. Preserve the existing restrictions on unsafe SVG
content when introducing this more capable embedding mode.

**Acceptance evidence.** Two mounted views have no duplicate DOM IDs. Selecting a window
highlights its matching representation and evidence card without changing coordinates.
Printed/exported drawings remain intelligible independently of the viewer.

**Applicability / limits.** Data attributes provide references, not automatic linkage:
the model registry and host-page behaviour must implement it. Browser support and the
existing `resvg` export path still require verification.

<a id="r11"></a>

## R11 — Accessible selection without distorting architectural geometry

**Question.** How can detailed drawings remain usable with keyboard, small displays or
limited colour perception?

**Source-backed finding.** WCAG 2.2 includes keyboard operation, visible focus and the
requirement that colour not be the sole means of conveying information.
[WCAG 2.2](https://www.w3.org/TR/WCAG22/).
Its target-size criterion uses 24 × 24 CSS pixels with defined exceptions, including an
equivalent control on the same page; this concerns interaction targets.
[W3C explanation of target size](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html).

**Dream House inference / proposed improvement.** Provide an HTML element list with
search, keyboard selection and visible focus alongside the SVG. Let the list and drawing
share one selected element. Use labels, symbols or patterns with status colours. Where
small drawing features are difficult to select, provide suitable interaction overlays or
equivalent list controls without enlarging the physical model. Keep detailed prose in
the evidence panel and preserve the existing graphic hierarchy on the sheet.

**Acceptance evidence.** A keyboard-only reviewer can locate `GLZ-WS-A`, open its evidence
and change views. Focus remains visible; open issues can be distinguished in grayscale.
Pointer and keyboard selection return the same element identity.

**Applicability / limits.** These are targeted design and test requirements, not a claim
that the viewer meets every WCAG criterion. CSS target dimensions are not drawing units,
and target-size exceptions must be evaluated in the actual interface.

<a id="r12"></a>

## R12 — Test meaningful changes and control visual baselines

**Question.** How can verification expose broken cross-view dependencies that unchanged
reference fixtures and successful rendering would miss?

**Source-backed finding.** Hypothesis supports generated action sequences and invariants
checked after steps, while advising that simpler tests may suffice.
[Hypothesis stateful testing](https://hypothesis.readthedocs.io/en/latest/stateful.html).
Playwright supports screenshot comparison but warns that browser, operating system,
fonts and environment affect rendering; baselines need a consistent environment.
[Playwright visual comparisons](https://playwright.dev/docs/test-snapshots).

**Dream House inference / proposed improvement.** Start with small independent fixtures:
resize an opening, move it without resizing, exclude a study, revise its source and
regenerate. Check stable identity, arithmetic deltas, affected outputs and retained open
gates. For a rectangular opening at fixed height, independently expect
`area_delta = height * width_delta`. A move-only case should preserve area while changing
placement-related results. Add property/stateful testing only when the action space makes
it useful. Keep geometric/semantic checks separate from visual comparisons and manual
review of the existing colour/grayscale contact sheets.

**Acceptance evidence.** A deliberately disconnected elevation fails the change test even
if its screenshot is attractive. A classification regression fails without needing a
visual difference. Visual baselines record browser/renderer, fonts and viewport, and
baseline changes receive review instead of automatic acceptance.

**Applicability / limits.** The current `unittest` suite can host the first fixtures;
researching Hypothesis or Playwright does not add dependencies. No test suite substitutes
for architectural judgement or responsible-professional design.

## Synthesis and changes carried into the plan

The research reinforces the window-family demonstration while making its contracts and
acceptance evidence more precise. The updated
[plan v0.2](../06_gestion_y_obra/connected_project_coordination_next_step.md) now includes:

- a minimum element/relationship/measurement contract;
- separate adoption, freshness, automated-check, professional-evidence, cost and
  publication dimensions;
- explicit geometry projections and a feasible interactive SVG route;
- preserved issue context and traceable derived evidence;
- dependency-aware regeneration and CI coverage; and
- twelve corresponding acceptance fixtures.

Full IFC/IDS/BCF exchange remains deferred until a receiving workflow requires it.
Standards-informed internal records do not establish interoperability or certification.
The research changes the proposed implementation plan, not the house geometry, budget,
current drawings or existing professional gates.
