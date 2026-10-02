# Connected editing and validation research — October 2026

**Status:** research and proposed plan improvements; not adopted for implementation<br>
**Version:** 0.1<br>
**Date:** 2026-10-02<br>
**Source:** owner's request for precise delivery phases for a living model, connected
drawings/calculations and edits originating in graphical views; the
[coordination plan](../06_gestion_y_obra/connected_project_coordination_next_step.md)
and repository evidence described below.<br>
**Access date:** all linked external sources were opened and checked on 2026-10-02.<br>
**Authority:** research only. No geometry, implementation dependency, construction scope,
cost, drawing promotion or professional approval is adopted here.

## Method and contribution

Three focused investigations, **R23–R25**, examine six primary technical sources: W3C,
MDN, IfcOpenShell and IETF documentation. They extend
[R01–R12](connected_coordination_research_2026_10.md) and
[R13–R22](connected_coordination_delivery_research_2026_10.md). Findings attributed to
external sources are separated from inspected repository evidence and proposed
application. Local observations describe the inspected implementation, not a completed
editor. Proposed door, window and column cases are **synthetic acceptance fixtures**,
not diagnosed conflicts in the actual project.

The [Project Constitution](../00_gobernanza/constitucion_del_proyecto.md) and
[source precedence/conflict register](../00_gobernanza/fuentes_precedencia_y_conflictos.md)
remain authoritative. Technical feasibility does not promote a study into an adopted
design. The recommended progression is a resolved model snapshot, tested commands,
validated local persistence, then graphical controls using those same commands.

| Investigation | Distinct question | Proposed delivery consequence |
| --- | --- | --- |
| [R23](#r23) | How can a drawing originate a meaningful model edit? | Explicit coordinate mapping and semantic commands shared by drag and form controls |
| [R24](#r24) | What can a geometric conflict check actually establish? | Classified rules, supported geometry and visible coverage rather than unexplained pass/fail |
| [R25](#r25) | How can an edit avoid overwriting newer work or saving half a change? | Revision preconditions and one serialized, complete candidate write |

<a id="r23"></a>

## R23 — Edit model meaning through the graphical view

**Question.** How can selecting and dragging an SVG object change a model property
reliably under pan, zoom and different drawing projections?

**Source-backed finding.** SVG `getScreenCTM()` maps an element's coordinates to the
document viewport, including ancestor, viewBox and layout transforms.
[W3C SVG 2 interfaces](https://www.w3.org/TR/SVG2/types.html#__svg__SVGGraphicsElement__getScreenCTM).
`matrixTransform()` transforms a point without changing its input; `inverse()` returns
the inverse matrix, with non-finite components when inversion fails.
[MDN point transformation](https://developer.mozilla.org/en-US/docs/Web/API/DOMPointReadOnly/matrixTransform),
[MDN matrix inversion](https://developer.mozilla.org/en-US/docs/Web/API/DOMMatrixReadOnly/inverse).
These are coordinate operations; building-element semantics require an application model.

**Repository connection.** The current
[showcase builder](../../.github/scripts/build_showcase.py) publishes static output.
The plan already proposes stable entity references and controlled study edits; these need
an explicit bridge from graphical interaction to a model command and repository writer.

**Dream House inference / proposed improvement.** Resolve selection through
`data-entity-id`, distinct from the DOM ID. Convert pointer client coordinates through the
editing layer's inverse screen matrix, then through its declared view-to-model mapping.
Constrain movement to a known host plane or axis: a plan projection cannot recover an
unknown height. Translate the gesture into an allowed command, such as changing a
host-relative opening position; numeric controls produce the same command. Arbitrary
path manipulation cannot infer that command safely. Label placement remains an annotation
operation. Both routes preview an isolated resolved snapshot and invalidate dependent
outputs. An explicit local writer validates and persists commands; the static showcase
can export a proposal for that writer. Browser state is not repository persistence.

**Acceptance evidence.** Equivalent gestures under pan, zoom, CSS scaling and mirrored
views produce the same model change. Unknown depth is never guessed; missing or singular
transforms disable the operation. Drag and numeric entry yield equivalent commands;
export/import preserves identity, base revision and values.

**Applicability / limits.** Start with a small editable property set. This does not require
a full CAD editor, network service or credentials in the published page.

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

## R25 — Save a complete candidate against its expected revision

**Question.** How can competing edits preserve changes, warnings and adopted inputs?

**Source-backed finding.** HTTP `If-Match` uses strong entity-tag comparison to prevent
lost updates; a false precondition prevents the requested change from being performed.
[RFC 9110, section 13.1.1](https://www.rfc-editor.org/rfc/rfc9110.html#name-if-match).
HTTP PATCH requires the complete patch to be applied atomically, with no partial modified
representation exposed when application fails.
[RFC 5789, section 2](https://www.rfc-editor.org/rfc/rfc5789.html#section-2).
These specify HTTP behaviour; they do not supply a local filesystem transaction.

**Repository connection.** The [model loader](../../dreamhouse/model/io.py) already
provides source hashes, an input hash and validation results. These identify expected
input but do not constitute an editing transaction. The plan's
study-edit proposal already calls for base fingerprints and expected prior values.

**Dream House inference / proposed improvement.** Carry a base snapshot revision,
element ID, expected values, operation and schema version in each command. Apply it
to an isolated snapshot, validate structure and semantics, then
evaluate coordination rules. A serialized local writer rechecks the base and persists
the complete candidate within the same protected operation; an earlier check alone
leaves a race. Use staged immutable snapshots and a controlled current-state pointer,
or another documented complete-write mechanism. Replacing individual files independently
does not make a multi-file change atomic. Historical hash-locked inputs remain intact.

Invalid input, missing identities and broken required relationships block candidate
acceptance. Coordination warnings and unresolved professional questions can remain
attached to a saved, unadopted study; promotion applies its own evidence requirements.
Regression guards for historical scenarios need separate applicability from reusable
candidate checks.

**Acceptance evidence.** Two commands share a revision: saving A makes B stale,
and B changes nothing. A failure midway through a compound edit leaves prior state
complete. Refreshing the base requires renewed comparison. Warnings survive saving,
reloading and regeneration, without silently becoming approvals.

**Applicability / limits.** Local optimistic concurrency needs no HTTP backend. Revision
matching does not replace authorization, validation or design adoption.
