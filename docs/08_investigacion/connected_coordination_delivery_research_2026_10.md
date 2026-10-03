# Connected coordination delivery research — October 2026

**Status:** research basis; two bounded applications implemented under D-084; remaining recommendations open<br>
**Version:** 0.3<br>
**Date:** 2026-10-02<br>
**Source:** owner's request for a further ten internet investigations to strengthen the
[connected coordination plan](../06_gestion_y_obra/connected_project_coordination_next_step.md),
following [investigations R01–R12](connected_coordination_research_2026_10.md).<br>
**Access date:** all linked external sources were opened and checked on 2026-10-02.<br>
**Authority:** research only. Recommendations do not adopt geometry, assemblies, products,
construction scope, costs, drawing promotion, or professional approvals.

## Implementation reconciliation — D-084

This revision links the retained research to implementation commit `0e69ddf`; external
findings and their original access date are unchanged. Use the [workflow](../06_gestion_y_obra/connected_coordination_workflow.md)
for actual commands/artifacts and the [phase checkpoint](../06_gestion_y_obra/connected_project_coordination_next_step.md#implementation-checkpoint--2026-10-02)
for outstanding delivery gates. Researching a technique does not mean it is fully implemented.

| Research | Implemented application | Remaining acceptance scope |
| --- | --- | --- |
| R13 | Current PB b37/P2 b28 resolver, source/consumer inventory, historical regression retention and bounded programme/equipment/workstation/structure adapters | Wider discipline coverage, product adoption and published-view migration |
| R14, R15 | Repository study JSON with base/expected-value checks; separate source/model hashes; duplicate/non-finite rejection | Broader authoring operations; neither JSON Patch nor JCS conformance is claimed |
| R16 | Explicit numerical tolerance and tests for contact, overlap, height separation and missing data | Family-specific engineering clearances and tolerance budgets |
| R17 | Verified staged candidate packages, serialized writers, atomic candidate pointer and late-failure recovery | Atomic promotion of all current aliases and compatible readers |
| R18, R19 | Shared plan/elevation/detail projections, one GLZ-WS-A section, parameter-derived dimensions, named anchors and validated cross-view callouts | Broader section/cut coverage and migration of the published drawing set |
| R20 | Coverage and OPEN findings remain separate from build completion and construction authority | Procurement/construction information contracts and professional evidence records |
| R21 | Open envelope/interface gates remain visible | Sectioned sill/head/jamb control-layer continuity and assembly-specific evidence |
| R22 | Existing reservations keep their stated context and unknowns | Installed/commissioned assets, service histories and phased handover integration |

The current package remains an isolated coordination review. The existing 27 published
aliases retain their source revisions; completing the candidate is not current-set
promotion. Optional `--visuals` output uses explicitly pinned font files for PNG previews,
a contact sheet and pixel comparisons. Consumer-impact metadata is recorded, but builds
still rebuild the complete package. See the [increment 02 implementation record](../06_gestion_y_obra/connected_coordination_increment_02.md)
for the adapter and coverage limits; no equipment selection, structural result or approval
is implied.

## Method and contribution

This second round investigates **ten additional questions, R13–R22**, using 19 primary
source pages/documents. It complements the twelve foundation investigations and supplies
the delivery contracts added to plan v0.3. Source-backed findings are separated from
project inferences, local evidence and proposed acceptance fixtures. References to gaps
in the plan describe v0.2 at reviewed commit `d5ea6ca`, before this update.

Public specifications, first-party technical documentation, original engineering-pattern
writing and publicly accessible construction guidance were opened online. Python 3.11
documentation matches the repository's minimum supported version. IFC references use the
official release documentation. Archived FreeCAD pages and dated guidance are identified
as such; they support specific information patterns, not product-selection claims.

The [Project Constitution](../00_gobernanza/constitucion_del_proyecto.md) and
[source precedence/conflict register](../00_gobernanza/fuentes_precedencia_y_conflictos.md)
remain authoritative. External examples do not decide the actual wall assembly, local
compliance, construction tolerances or project approvals.

| Investigation | Distinct question | Resulting addition to the plan |
| --- | --- | --- |
| [R13](#r13) | How should existing loaders migrate? | Narrow adapters and same-scenario comparison before changing consumers |
| [R14](#r14) | How should an unadopted edit be applied? | Named base, expected prior values and all-or-nothing candidate creation |
| [R15](#r15) | What does a model fingerprint mean? | Separate source bytes, normalized content and build dependencies |
| [R16](#r16) | What counts as geometric agreement? | Explicit numerical policies separate from clearances and construction tolerances |
| [R17](#r17) | How should a complete issue be delivered? | Isolated candidate build, inventory verification and failure-preserving publication |
| [R18](#r18) | What does each drawing view represent? | View purpose, cut/projection rules and resolvable callouts |
| [R19](#r19) | How do dimensions remain connected? | Named anchors, generated measurements and unresolved-reference detection |
| [R20](#r20) | What evidence is sufficient now? | Information bundles by element, use and milestone |
| [R21](#r21) | What connects the window details? | Head/sill/jamb interface records and continuity evidence |
| [R22](#r22) | How does the record support later maintenance? | Progressive asset and service-reservation information |

The main delivery consequence is deliberately small: **reconcile the current window
state first**. The plan's C01–C06 sequence turns these findings into review outputs and
exit evidence. No implementation dependency is installed by this research.

<a id="r13"></a>

## R13 — Migrate through a narrow interface with comparison evidence

**Question.** How can current sources enter the integration pipeline without rewriting
the history or forcing all generators to change at once?

**Source-backed finding.** Martin Fowler describes incremental replacement through an
abstraction that allows old and new implementations to coexist, with clients moved
gradually and behaviour compared during the transition. The approach's name refers to
separating implementations; it does not require a version-control branch.
[Branch by Abstraction](https://martinfowler.com/bliki/BranchByAbstraction.html).

**Repository connection.** The [integration loader](../../dreamhouse/model/io.py) defaults
to `D059_P2_REFINED_ENVELOPE`, while current geometry is produced through
[PB b37](../../dreamhouse/generate_pb_b37.py) and [P2 b28](../../dreamhouse/generate_p2_b28.py).
The existing plan identifies the resulting lag and the workstation-to-rooflight quantity
mapping error. Different historical and current scenarios should not be forced to agree.

**Dream House inference / proposed improvement.** Introduce one adapter boundary that
assembles the current loaders into a normalized read model. Compare it with those same
loaders before redirecting a schedule or view. Preserve historic scenario access and
source files. Report expected semantic corrections separately from unexplained geometry
differences. Use this boundary only where it reduces duplicated knowledge; do not wrap
every helper or create a second independent source of truth.

**Acceptance evidence.** Produce a per-opening comparison for PB b37/P2 b28 with identical
geometry, source references and nominal opening measurements. The intended workstation
classification correction is explicit. An unexpected difference blocks the migration of
that consumer; historical reproductions remain available.

**Applicability / limits.** This is a software migration pattern, not a BIM standard or a
requirement to build a service platform. Repository instructions prohibit new branches;
the proposed migration happens incrementally in the existing workspace.

<a id="r14"></a>

## R14 — Apply study changes against an explicit expected base

**Question.** How can a dimensional experiment be replayed without silently modifying a
different element or a newer adopted baseline?

**Source-backed finding.** JSON Patch defines ordered operations over a target document.
Its `test` operation checks an expected value, and failed operations prevent the patch
from being considered successful. Array additions/removals shift later indices.
[RFC 6902, §§3–5](https://www.rfc-editor.org/rfc/rfc6902.html).

**Repository connection.** [PB b37's delta](../../dreamhouse/pb_b37_delta.json) already
locks a base delta and the D-083 source by hash. The connected plan proposes trial width
and position changes but needs a clear boundary between a test scenario and adopted data.

**Dream House inference / proposed improvement.** Give each new trial a base scenario,
fingerprint policy/value, reason and explicit element changes. Validate expected prior
values, apply to a copy, then validate the complete result. If JSON Patch is selected,
address stable entity-map keys rather than ordinal list positions, keep the trial metadata
outside the operation list, and implement candidate persistence transactionally. A narrow
typed edit record can provide the same project controls without adopting JSON Patch.
Retain existing historical delta formats and loaders.

**Acceptance evidence.** A study created for an old base is rejected after the base changes;
a failing second operation persists none of the first operation's effects. Reordering
source elements cannot redirect a window edit. The generated report shows exact before/
after values and affected outputs, while adopted inputs remain unchanged.

**Applicability / limits.** Patch syntax does not validate geometric plausibility or
authorize adoption. The RFC's HTTP context must not be confused with a local library
automatically providing transactional file persistence; that guarantee is project work.

<a id="r15"></a>

## R15 — Specify fingerprints before relying on them

**Question.** When do two differently serialized files represent the same model, and
when must an output be invalidated?

**Source-backed finding.** RFC 8785 defines a specific canonical JSON representation,
including primitive serialization and property ordering; it is an informational RFC.
Python's JSON module independently offers sorted keys and allows non-finite values and
duplicate object names by default. The RFC's verified errata also address negative zero.
[RFC 8785](https://www.rfc-editor.org/rfc/rfc8785.html),
[Python JSON](https://docs.python.org/3.11/library/json.html),
[RFC 8785 errata](https://www.rfc-editor.org/errata/rfc8785).

**Repository connection.** [Model I/O](../../dreamhouse/model/io.py) has both
`sha256_path()` and `canonical_json_hash()`. The latter serializes with sorted Python
keys; its name does not establish RFC 8785 interoperability. `_read_json()` also uses
the default parser. This observation identifies a contract gap, not evidence of corrupt
current data.

**Dream House inference / proposed improvement.** Preserve raw byte hashes for exact
source provenance. Define a separate versioned normalized-model fingerprint, specifying
units, included fields, numeric types, ordering and handling of negative zero. Reject
duplicate keys and non-finite values at input boundaries. Keep dependency/build fingerprints
separate so a changed generator invalidates output even when geometry is unchanged.
Retain historical verification under the original policy instead of replacing old hashes.

**Acceptance evidence.** Whitespace/key-order changes alter source bytes but preserve the
normalized fingerprint; changed geometry alters it. Tests cover `1`/`1.0` and `-0.0`
according to the chosen policy. Duplicate keys, NaN and infinity produce diagnostics.

**Applicability / limits.** A documented Python-only policy is sufficient initially.
Do not claim JCS compliance without its full rules, errata and interoperability fixtures;
hash equality proves neither engineering correctness nor approval.

<a id="r16"></a>

## R16 — Separate numerical precision from physical acceptance

**Question.** How can automatic geometry checks avoid treating rounding or numerical
noise as a construction clearance or a real collision?

**Source-backed finding.** Python's PEP 485 distinguishes relative and absolute comparison
tolerances, especially near zero. Shapely documents that precision-grid rounding can
remove vertices or collapse narrow geometry entirely; reducing precision changes geometry.
[PEP 485](https://peps.python.org/pep-0485/),
[Shapely 2.1.2 set_precision](https://shapely.readthedocs.io/en/2.1.2/reference/shapely.set_precision.html).

**Repository connection.** [Rectangle checks](../../dreamhouse/geometry/rectangles.py)
use a numerical tolerance of `1e-9` and treat touching boundaries differently from
overlapping interiors. [Model I/O's `_close()`](../../dreamhouse/model/io.py) supplies an
absolute tolerance to `math.isclose()` while retaining its default relative tolerance.
These behaviours should become explicit when reused across a larger coordination model.

**Dream House inference / proposed improvement.** Document a policy per rule: coordinate
units, comparison type, numerical tolerance and boundary semantics. Record physical
clearance requirements and their source independently. Format dimensions after computing
geometry and quantities. A label that prints the same rounded number cannot establish
equivalence of two different clearances. Keep the existing rectangle kernel for the
initial axis-aligned family; introduce more general geometry only for a demonstrated need.

**Acceptance evidence.** Exercise touching, a small positive gap and an overlap on both
sides of the declared numerical boundary. Repeat near zero and at building-scale
coordinates. Changing printed decimal places leaves calculations unchanged. If grid
snapping is later introduced, detect collapsed features rather than silently dropping them.

**Applicability / limits.** Neither source defines permissible installation tolerances or
safety clearances for this house. Those are separate professional inputs; this research
adopts no physical threshold or new geometry dependency.

<a id="r17"></a>

## R17 — Validate the complete candidate before exposing it as a release

**Question.** How can automatic generation avoid publishing a mixture of old and new
drawings if one late output fails?

**Source-backed finding.** Python documents `os.replace()` as an atomic rename when
successful, with filesystem and destination limitations. Temporary-directory APIs provide
isolated working directories and cleanup. Neither feature is a transaction over a whole
set of drawings, images and indexes.
[Python os.replace](https://docs.python.org/3.11/library/os.html#os.replace),
[Python TemporaryDirectory](https://docs.python.org/3.11/library/tempfile.html#tempfile.TemporaryDirectory).

**Repository connection.** In [the drawing synchronizer](../../.github/scripts/sync_current_drawings.py),
`write_current()` removes obsolete aliases, copies SVGs, renders PNGs and then writes the
manifest/indexes sequentially. Source and provenance checks already exist. The remaining
delivery concern is the intermediate state if a later step fails; this review found no
evidence that such a failure has occurred.

**Dream House inference / proposed improvement.** Build the new coordination package in
an isolated directory, verify the expected file inventory, dependencies and hashes, then
retain the complete candidate under a unique version. Promotion remains a separate
governed action. Before changing current publication, design how readers resolve one
complete release, including existing stable aliases. A single release pointer can support
that design only if consumers actually follow it. Per-file replacement alone is insufficient.

**Acceptance evidence.** Inject a render failure after other candidate outputs succeed.
All existing current-publication bytes remain unchanged, and the incomplete candidate
cannot pass release validation. A completed package can be reopened from its retained
manifest without selecting files from another revision.

**Applicability / limits.** Start with candidate isolation and verification. Cross-platform
publication, concurrent writers and crash durability need explicit design if introduced;
this source does not justify claiming those guarantees for the current synchronizer.

<a id="r18"></a>

## R18 — Views need a purpose and a cut/projection contract

**Question.** What makes an automatically generated section meaningfully different from
an elevation or a schematic assembly detail?

**Source-backed finding.** IFC representation subcontexts distinguish information content
by target view and scale while sharing the parent coordinate system. Its projection
enumeration distinguishes plan, reflected plan, elevation, section, and sketch views;
the section example explicitly concerns elements cut by a section line.
[IfcGeometricRepresentationSubContext](https://standards.buildingsmart.org/IFC/RELEASE/IFC4_3/HTML/lexical/IfcGeometricRepresentationSubContext.htm),
[IfcGeometricProjectionEnum](https://standards.buildingsmart.org/IFC/RELEASE/IFC4_3/HTML/lexical/IfcGeometricProjectionEnum.htm).

**Repository connection.** The [plan's element contract](../06_gestion_y_obra/connected_project_coordination_next_step.md#41-minimum-element-and-relationship-contract)
already separates projected geometry from schematic details, but does not yet define a
view record that can express cut position, depth, or supported representation rules.

**Dream House inference / proposed improvement.** Add a small view registry containing
view ID, purpose, referenced scenario, projection direction, cut plane where applicable,
visible depth/extent, target scale, and supported element kinds. Classify generated
geometry as cut, projected, hidden, or schematic. A detail should state which dimensions
derive from the model and which assembly relationships remain conceptual. Link section
markers and detail callouts to these records and generate their sheet references.

**Acceptance evidence.** Move a test cut plane across an opening and show the expected
change in cut versus projected geometry. A marker opens the matching view and scenario.
Unsupported intersections are reported. A renamed or moved sheet preserves the view link.

**Applicability / limits.** Implement only the planes and element families needed for the
first demonstration. IFC view labels describe intent; they do not perform intersections,
hidden-line removal, or construction-detail design. This proposal adds no CAD dependency.

<a id="r19"></a>

## R19 — Dimensions and callouts must retain their references

**Question.** How can a drawing dimension remain trustworthy when the geometry or sheet
layout changes?

**Source-backed finding.** FreeCAD's official TechDraw documentation distinguishes a
projected measurement from a true 3D measurement and permits arbitrary text to replace
the displayed dimension. Its repair documentation identifies broken geometry references
after topology or hidden-line changes. These archived first-party pages demonstrate both
associative dimensioning and its limitations; they are not a current software evaluation.
[TechDraw LengthDimension](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/TechDraw_LengthDimension.md),
[TechDraw DimensionRepair](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/TechDraw_DimensionRepair.md).

**Repository connection.** The [connected-view increment](../06_gestion_y_obra/connected_project_coordination_next_step.md#52-connect-one-element-family-to-multiple-views)
proposes optional dimensions and evidence links without an explicit dimension-reference
contract.

**Dream House inference / proposed improvement.** Represent each measured dimension using
element ID, named geometric anchors, measurement kind, units, source revision, and display
format. Bind opening width to named jamb anchors rather than a drawing primitive index;
derive its label from the measurement. Store annotation position separately. Distinguish
calculated dimensions, reference notes, and explicit text overrides. Resolve callouts
through view/detail IDs and the publication manifest rather than hard-coded sheet text.

**Acceptance evidence.** Resizing a test opening updates geometry and the dimension value;
moving the label changes neither. Deleting an anchor produces an unresolved dimension,
never a retained plausible number. A rotated view distinguishes projected from true
length. A detail revision updates its callout or marks it stale.

**Applicability / limits.** The FreeCAD documentation repository was archived in April
2026. Reuse the information pattern in the existing generator; do not infer that a tool
upgrade solves identity, topology, or annotation correctness.

<a id="r20"></a>

## R20 — Define sufficient information for each decision milestone

**Question.** How can the project mature without accumulating premature detail or claiming
that every discipline has reached the same readiness?

**Source-backed finding.** UK BIM Framework guidance defines information need by purpose,
including applicable geometry, alphanumeric information, and documentation. BIMForum's
2024 specification explains that model elements can mature at different rates; its LOD
language does not prescribe one level for an entire model or a universal design stage.
[UK BIM Framework Part D, §§2.2–2.6](https://ukbimframework.org/wp-content/uploads/2021/02/Guidance-Part-D_Developing-information-requirements_Edition-2.pdf),
[BIMForum LOD Specification 2024, pp. 192–196](https://bimforum.org/wp-content/uploads/2024/11/LOD-Spec-2024-Part-I-official-English.pdf).

**Repository connection.** [Review by stage](../06_gestion_y_obra/roles_entregables_y_calidad.md#review-by-stage)
defines broad deliverables. The connected plan separates statuses, but needs a matrix
explaining sufficient evidence for each use of the window family.

**Dream House inference / proposed improvement.** Define purpose-specific evidence bundles:
schematic coordination, professional interface review, comparable quotation, installation
release, and handover. For each bundle identify affected elements, required geometry/data/
documents, producer, reviewer, milestone, and acceptance evidence. A schematic opening
may support spatial comparison while its manufacturer data remains deliberately pending.
Show missing evidence against the selected purpose instead of assigning one overall
percentage of project completion.

**Acceptance evidence.** The same window passes its schematic information bundle while
remaining incomplete for installation release. Missing quotation exclusions prevent a
quotation comparison from being represented as complete. Adding irrelevant metadata does
not improve readiness for either purpose.

**Applicability / limits.** These are publicly available guidance documents, not evidence
that paid standards were fully reviewed or that foreign contractual conventions govern
Boyacá. Project professionals must define the actual gates; higher graphic detail alone
does not satisfy them.

<a id="r21"></a>

## R21 — Connect envelope details through continuous performance layers

**Question.** What evidence should link sill, head, jamb, wall, and workstation details
before a window interface can be judged coordinated?

**Source-backed finding.** DOE's Building America Solution Center explains window-to-wall
coordination through continuity of water, air, vapour, and thermal control, adapted to the
wall assembly and product. Its flashing guide addresses continuity across sill, side, and
head interfaces and integration with the drainage plane.
[Window installation concepts](https://basc.pnnl.gov/resource-guides/window-performance-grades-and-installation-details-multifamily-buildings),
[Windows and doors are fully flashed](https://basc.pnnl.gov/resource-guides/windows-and-doors-are-fully-flashed).

**Repository connection.** [D-083 coordination](../02_arquitectura/window_daylight_coordination_v0.3_b37_b28.md#open-professional-gates)
already requires drainage, thermal-bridge, condensation, support, and mock-up evidence.
The viewer should make those relationships inspectable across the detail family.

**Dream House inference / proposed improvement.** Give each window family
linked sill/head/jamb views sharing the host, opening, and filling references. Add optional
control-layer overlays and explicit transition endpoints, drainage destinations, movement/
support interfaces, and maintenance access. Record unresolved layer continuity as an
interface issue with required evidence and reviewer. Link the desk service gap and
independent support to that same interface record so furniture and wiring changes trigger
review of affected seals and drainage.

**Acceptance evidence.** A reviewer can trace each relevant layer through the three
details or identify a named unresolved transition. Changing the host build-up invalidates
affected interface evidence. A mock-up/test record identifies the exact assembly revision;
it does not silently validate later variants.

**Applicability / limits.** The sources discuss US assemblies and programmes. Extract
coordination principles only: no material, slope, sealant, vapour-layer placement, or test
threshold is adopted here. Site climate, selected products, Colombian requirements, and
responsible-professional design remain necessary.

<a id="r22"></a>

## R22 — Grow an asset record through phased construction and handover

**Question.** How can today's element records later support maintenance and phased
completion without pretending that unselected equipment is already installed?

**Source-backed finding.** NIBS COBie distinguishes product types from individual
components, locates components in spaces, and relates operational jobs and supporting
resources. Its phase guidance anticipates progressively available information: serial
numbers, installation dates, and precise locations arise during implementation, while
handover adds maintenance knowledge and verified records.
[COBie data tables](https://nibs.org/nbims/v3/cobie/4-2/),
[COBie phase considerations](https://nibs.org/nbims/v3/cobie/3-5/).

**Repository connection.** The [MEP basis](../03_ingenierias/bases_mep_confort_y_automatizacion.md#preparación-de-zonas-diferidas)
already requires labeled and protected reservations, recorded tests before closure, and
retesting for Phase 2. [Handover requirements](../06_gestion_y_obra/roles_entregables_y_calidad.md#handover)
call for manuals, warranties, inventory, and maintenance evidence.

**Dream House inference / proposed improvement.** Reserve stable links from maintainable
elements to space/system, delivery phase, access/removal envelope, responsible role, and
future document/test records. Distinguish planned, reserved, installed, tested, and
commissioned states. Add manufacturer, model, serial number, warranty, and service interval
only when supported by selection or installation evidence. For deferred services, record
the reservation's location, protection/isolation, last test, and reactivation obligations
independently of the future equipment.

**Acceptance evidence.** A Phase 1 reservation can appear in the plan and handover package
without creating a fictitious installed asset. Phase 2 activation requires its applicable
inspection/testing evidence. Replacing a maintainable component retains the location and
service-history links while recording the new asset identity.

**Applicability / limits.** Start with the few assets and reservations the owner must
actually maintain. These fields are an internal proposal, not COBie compliance; no
facilities-management platform or complete COBie export is needed for this increment.
