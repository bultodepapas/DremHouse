# Connected model propagation and validation research — October 2026

**Status:** research basis; bounded applications and consumer migration under D-084; remaining recommendations open<br>
**Version:** 0.4<br>
**Date:** 2026-10-03<br>
**Source:** owner's request for a living repository model with connected calculations,
SVG outputs and warnings; explicit clarification that changes occur in repository sources
and that there is no graphical editing.<br>
**Access date:** linked external sources were opened and checked on 2026-10-02.<br>
**Authority:** planning evidence only; no geometry, scope, cost or publication change.

## Migration application — 2026-10-03

The [migration and extension guide](../06_gestion_y_obra/connected_coordination_migration_and_extension_guide.md)
records the later implementation of native drawing consumers, complete review releases,
recovery and source-connected extension records. The tables below retain the incremental
research-to-code audit; their earlier migration gaps must be read with that current guide.
Source watching still performs a full rebuild. Named review annotations and inherited
catalog annotations have separate coverage; neither visual equivalence nor engineering
approval is inferred. This update records local implementation evidence only; original
external access dates and research conclusions are unchanged.

## Implementation reconciliation — D-084

The first implementation commit `0e69ddf` and D-084 increment 02 deliver bounded
applications of these investigations. This update changes documentation status, not the
external-source findings or access record. SVG remains generated output; all source edits
occur in repository JSON/Python.

| Research | Implemented application | Remaining acceptance scope |
| --- | --- | --- |
| R23 | One snapshot supplies eight SVGs, quantities, dimensions and findings; HTML selection is read-only; optional pinned-font PNG/contact-sheet pixel comparison | Remaining published views, broader section/interface details, approved visual baselines and further calculation consumers |
| R24 | Synthetic overlap/contact/height fixtures, room/host/rooflight and bounded discipline checks; ten structural source lines are compared with current plan geometry and remain OPEN | Solid geometry from responsible sources, equipment selection and engineering checks |
| R25 | Study preconditions, before/after input hashes, complete artifact verification, serialized output writers and atomic candidate pointer | Current-catalog publication transaction and broader release consumers |

The observed reservation/opening plan relationships are not confirmed solid collisions.
The ten-line structural comparison is also plan-only; it does not establish a member,
vertical clearance or capacity. Current programme checks use the P2 rebalance basis, so
the historic 15 m² closet target is superseded by D-065 and is an inapplicable OPEN
comparison against the current 13.44 m² dressing record. Equipment results preserve raw benchmark geometry but remain
OPEN because placements are not adopted as current selections. CF-013 separately records
audited PB door-anchor inconsistencies. Neither result was assumed from the owner's
illustrative examples. See the [source inventory](../06_gestion_y_obra/connected_source_inventory.md),
[workflow](../06_gestion_y_obra/connected_coordination_workflow.md), and
[increment 02 record](../06_gestion_y_obra/connected_coordination_increment_02.md) for limits.

## Method and contribution

Three focused investigations, **R23–R25**, use five primary sources from W3C,
IfcOpenShell and IETF. They extend [R01–R12](connected_coordination_research_2026_10.md)
and [R13–R22](connected_coordination_delivery_research_2026_10.md). Findings from sources,
inspected repository behaviour and proposed applications remain separate.

This revision corrects R23 and its application: SVGs are generated representations for
reading geometry and findings. Source changes happen in repository JSON, scenario inputs
and Python. The file path is retained for existing links; its subject is source-driven
propagation, not a graphical editor. Illustrative door/window/column cases are synthetic
acceptance examples, not diagnosed project conflicts.

The [Project Constitution](../00_gobernanza/constitucion_del_proyecto.md) and
[source precedence/conflict register](../00_gobernanza/fuentes_precedencia_y_conflictos.md)
remain authoritative. The [plan](../06_gestion_y_obra/connected_project_coordination_next_step.md)
now organizes delivery around sources, model resolution, evaluation, generated outputs,
automation and wider project coverage.

| Investigation | Question | Contribution |
| --- | --- | --- |
| [R23](#r23) | How do SVGs represent the same evaluated model coherently? | Shared element references, declared projection transforms and read-only evidence links |
| [R24](#r24) | What can a geometric conflict check establish? | Classified rules, supported geometry and visible coverage |
| [R25](#r25) | How do builds retain consistent inputs and complete outputs? | Source-revision checks, isolated candidate packages and controlled publication |

<a id="r23"></a>

## R23 — Generate traceable SVG representations from model data

**Question.** How can every relevant drawing show the same source change and the warnings
produced by Python, without turning the SVG into an editing surface?

**Source-backed finding.** SVG supports grouped graphics, document IDs and custom `data-*`
attributes. Its coordinate model defines viewports, user coordinate systems and transforms.
These mechanisms support identified representations and explicit drawing transforms;
the application supplies the relationship to a building model.
[W3C SVG document structure](https://www.w3.org/TR/SVG2/struct.html),
[W3C SVG coordinate systems](https://www.w3.org/TR/SVG2/coords.html).

**Repository connection.** The current [showcase](../../showcase/app.js) displays generated
images and provides zoom/pan. The [SVG modules](../../dreamhouse/svg/) supply drawing and
QA tools. Current generators need common model identities and injected scenario inputs
so their views do not diverge after changes to repository data.

**Dream House inference / proposed improvement.** Python resolves the sources once and
passes that snapshot to each view generator. Use a unique occurrence ID plus a shared
`data-entity-id`; declare each view's projection, datums, scale and representation role.
Generate geometry and dimensions from model values, and warning overlays from the same
rule results. The manifest binds drawings, quantities and findings to one source/build
fingerprint. Optional selection links occurrences and evidence for inspection only.
The browser does not change source parameters or write to the repository.

**Acceptance evidence.** Change a supported source parameter and run Python. Relevant
plans, elevations, sections, dimensions and reports all reflect the resulting snapshot.
A warning identifies the affected entities in available views. Zoom, selection and
navigation preserve model data. A skipped output is marked stale; manual changes to a
generated SVG are detected as divergent rather than treated as authoritative inputs.

**Applicability / limits.** Begin with the existing generators and static site. Semantic
SVG metadata does not itself provide model synchronization; the shared Python pipeline
and dependency declarations implement that behaviour. No graphical editor is proposed.

<a id="r24"></a>

## R24 — Classify geometric conflicts and disclose check coverage

**Question.** What distinguishes possible overlap, confirmed conflict and unevaluated pairs?

**Source-backed finding.** IfcOpenShell distinguishes intersection, surface collision and
clearance checks. Surface collision can miss full containment; intersection handling
depends on manifold geometry. Bounding-box selection is faster but less precise than
geometry selection. Some clash routines may stop at the first detected result rather
than the worst case; tolerances and touching rules are explicit parameters.
[IfcOpenShell geometry tree](https://docs.ifcopenshell.org/ifcopenshell-python/geometry_tree.html).
One overlap predicate cannot answer every coordination question.

**Repository connection.** The existing
[rectangle geometry](../../dreamhouse/geometry/rectangles.py) models axis-aligned XY
rectangles and tests interior overlap, excluding touching within its tolerance. It has
no height interval. It supports plan-space rules but cannot establish volumetric clashes
or vertical clearance.

**Dream House inference / proposed improvement.** Use conservative bounds to find
candidate pairs, then apply the narrower test supported by each representation. Simple
rectangular solids may need only XY geometry plus height intervals; more complex shapes
need a declared supported method. Classify penetration, contact, required clearance,
door-swing space and maintenance reservations separately. Record rule source, units,
threshold, geometry support and intentional relationship exclusions. A broad overlap
becomes a confirmed issue only when the relevant predicate supports that conclusion.
Report evaluated, excluded and unsupported pairs; missing height or unsupported geometry
must remain visible, not become PASS. Preserve illustrative door/window/column examples
as synthetic fixtures until actual model evidence identifies a project issue.

**Acceptance evidence.** Fixtures distinguish equal XY footprints at separate heights,
touching versus penetration, containment, overlapping bounds without intersecting shapes,
and clearance around a threshold. Unsupported cases remain listed. Each
issue resolves to entities, tested geometry and rule version; summaries
state whether reported distance is exhaustive or merely the first detection.

**Applicability / limits.** Borrow the distinctions without requiring IfcOpenShell.
Geometric checks do not certify structural capacity, fire compliance, constructability
or professional approval; each requires its own evidence and review scope.

<a id="r25"></a>

## R25 — Build against a consistent input revision

**Question.** How can a run avoid combining different input revisions or replacing a
complete package with an incomplete one?

**Source-backed finding.** HTTP `If-Match` uses strong entity-tag comparison to avoid lost
updates; a failed precondition prevents the requested change. HTTP PATCH requires a
complete atomic application rather than a partly modified representation. These are HTTP
contracts, not implementations of local filesystem transactions.
[RFC 9110, section 13.1.1](https://www.rfc-editor.org/rfc/rfc9110.html#name-if-match),
[RFC 5789, section 2](https://www.rfc-editor.org/rfc/rfc5789.html#section-2).

**Repository connection.** [Model I/O](../../dreamhouse/model/io.py) records source/input
hashes and validates historical source locks. The [pipeline](../../dreamhouse/pipeline.py)
writes a package and manifest, but source loading, result generation and publication need
an explicit complete-build contract for the new current-state workflow.

**Dream House inference / proposed improvement.** Borrow the expected-revision principle
for repository processing. Resolve a consistent source snapshot, record all consumed
hashes and evaluate/render only from that snapshot. If inputs change during the run,
mark its output outdated or reject/restart it. Before advancing a latest-complete pointer,
recheck source identity and serialize the update. Independent concurrent builds use
separate candidate directories. Historical locked sources remain preserved; a study delta
names its expected base instead of silently targeting a different revision.

Stage the required model, drawings, findings and quantities together and verify inventory
and output hashes. A failed build retains the previous complete package. Coordination
warnings remain visible in a complete study package; publication and engineering adoption
retain their separate gates.

**Acceptance evidence.** Modify a fixture input during generation: no mixed-revision
package is labelled current. A render failure leaves the previous complete package intact.
A late obsolete run cannot replace a newer complete run. Warnings survive reloading and
regeneration, without becoming approvals.

**Applicability / limits.** This is an inference for local Python execution, not a
requirement for HTTP endpoints, a browser writer or a multiuser editor. Atomic file
replacement alone does not make a multi-file publication atomic.
