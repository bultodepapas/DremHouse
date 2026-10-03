# Connected coordination — increment 02

**Version:** 0.1<br>
**Date:** 2026-10-02<br>
**Status:** implemented coordination review extension; professional gates remain open<br>
**Source:** continued owner authorization under D-084; documentation baseline `e58aba5`;
current PB b37/P2 b28, D-083, SC-01, equipment benchmarks and declared structural hypotheses.<br>
**Authority:** software and information workflow only; no architectural change, construction
scope/cost change, selected product, professional approval or current-drawing promotion.

## Result and execution

The same resolved scenario now supplies opening checks, bounded programme/equipment
adapters, support-line plan comparisons, eight SVG review views, quantities, dependency
evidence and annotated before/after review. SVG remains generated output. Source changes
are authored in the repository's pinned JSON studies.

```bash
python3 -m pip install -e '.[presentation]'
python3 -m dreamhouse.coordination --visuals --require-no-fail
python3 -m dreamhouse.coordination --check --visuals --require-no-fail
```

The first command prints the candidate `index.html` path. `--visuals` adds PNG previews,
the current and archived-baseline contact sheets, and pixel-difference evidence. Without
that option, the Python build remains a text/SVG workflow with no raster dependency.
An OPEN package still requires coordination; `--require-no-fail` distinguishes supported
FAIL findings from successful artifact generation, and does not turn OPEN into approval.

## One source boundary, explicit discipline inputs

`resolve_project()` captures the current PB/P2 loader outputs, equipment catalog/layout,
SC-01, rooflights and structural-system context once. `discipline_inputs` is captured
context, not an additional editable master. Normalized entity geometry takes precedence
inside the adapters; evaluations and renderers perform no hidden source reloads.
The context participates in the model fingerprint and is preserved separately in the
archived baseline.

| Connected consumer | Executed scope | Limit retained |
| --- | --- | --- |
| Programme | Current tagged primary-suite component areas and recorded study comparisons | No certification of net usable area or complete room-performance compliance |
| Equipment | Existing body/operating-envelope validator applied to current host geometry and explicit benchmark catalog/layout | Products and placements remain unadopted; raw geometric outcomes remain visible inside OPEN applicability findings |
| Workstation/window | Opening span and sill compared with the current workstation zone and worktop datum | No assumed glazing support, drainage performance or installation tolerance |
| Support-line plan audit | Four SC-01 plan reservations and six source-referenced E0 positions compared with current spaces/openings | No selected column, verified vertical extent, solid collision, capacity or structural design result |
| Opening quantities/cost | Existing same-snapshot nominal areas, rooflight curbs and cost mappings | No whole-house takeoff, selected rates or approved total |

Two distinctions matter when reading the newly connected evidence:

- D-065's current compact dressing is 13.44 m² gross. The older 15 m² comparison is
  preserved as an inapplicable historical criterion; it is not a new design failure or
  a replacement minimum. The primary-suite gross/net and owner-target question remains open.
- The historical equipment layout does not fit the current primary-bedroom geometry in
  its bed host/clearance checks; the refrigerator depth also remains OPEN. These are
  explicitly labelled benchmark results requiring layout/product review, not evidence
  that those placements were adopted into the current design.

Missing geometry is unsupported; unevaluated engineering remains `not_run`. All finding
groups enter the same coverage and lifecycle reports. Losing an adapter input cannot
resolve an earlier finding. Historical E0/E1 assertions and published evidence are preserved.

## Connected drawings and measurable annotations

The original two plans, four elevations and opening-detail plate are joined by
`window-sections.svg`. This eighth SVG links `GLZ-WS-A` opening levels to its source
worktop datum and shows head, sill and jamb interface questions. Water-management,
air-control and thermal paths are deliberately interrupted where assembly information
is missing. The drawing states that horizontal spacing is schematic; it does not invent
wall thicknesses, fixings, profiles, materials or proven control-layer continuity.

Named anchors retain model coordinates independently of displayed rounding. Dimensions
refer to those anchors; callouts refer to stable view identities and DOM targets. The
builder validates identities, references and supported two-anchor linear measurements.
A missing/misdirected target, incorrect clickable destination or contradictory dimension
prevents publication. Callout identities survive a sheet rename; the generated navigation
must resolve to the renamed file and the same declared anchor.

`view_inventory.json` reports occurrences and annotation coverage separately.
`anchor_lifecycle.json` records added, changed, removed and unchanged anchors against the
archived current baseline. Unlocated PB doors remain in the registry and findings under
CF-013; the new section does not supply their missing coordinates.

## Dependencies, visual evidence and complete packages

`dependencies.json` exposes source/element relationships, registered consumers, changed
entity/context inputs and review obligations. It is a conservative explanation of a full
rebuild, not an incremental cache or proof of a minimal dependency graph. Professional
evidence remains outstanding; a changed scenario gets a different evidence fingerprint,
without manufacturing an approval record or closing a conflict.

Visual export uses checked-in, unmodified IBM Plex Sans regular/bold fonts and disables
system font discovery. The manifest records font hashes, resvg, Pillow and FreeType
versions. CI pins resvg-py 0.4.0 and Pillow 11.3.0; output equivalence across untested
platforms is not asserted. PNGs are previews, not dimensional authority.

The source `input_hash` and rendered-package `issue_id` are distinct. A different export
mode/configuration produces another complete package for the same source snapshot.
`--check` automatically reads the package mode and verifies the current environment;
`--check --visuals` additionally requires the visual package. Missing fonts/dependencies,
changed inputs, broken annotations and rendering failure preserve the previous pointer.

The visual package retains baseline SVG/PNG previews and its own visual manifest under
`baseline/`. Pixel comparison reports exact changed-pixel counts/bounds, added/removed
views and incompatible sizes/configurations without resizing or an approval threshold.
Differences include scenario labels and findings; use `changes.json` and anchor changes
to distinguish model changes from sheet metadata. The comparison baseline is the archived
current PB b37/P2 b28 state, not the last generated candidate.

## Compatibility and remaining gates

The package manifest is now schema version 2. Capturing discipline context changes the
semantic baseline fingerprint: older nonempty studies pinned to the previous fingerprint
must be reviewed and rebased from a fresh template. Preserve their intended deltas and
inspect expected values; never replace a hash blindly to bypass the stale-input check.

The [phase checkpoint](connected_project_coordination_next_step.md#implementation-checkpoint--2026-10-02)
separates delivered software evidence from remaining work. The current 27-sheet catalog
has not been migrated or promoted. Full discipline calculations, wall/product masses,
MEP routes, section/assembly engineering, actual equipment selection, broader entity
authoring and construction/maintenance records still require their documented inputs
and acceptance work. No phase is considered complete merely because a partial adapter
or readable drawing exists.

## Verification — 2026-10-02

| Check | Observed result |
| --- | --- |
| Full repository unittest discovery | **403 tests passed**, including historical engineering regressions, source propagation, missing-data lifecycle, annotation corruption, rendering failure and artifact tampering |
| Ruff | Coordination, quantities and the changed structural adapter passed; publication-template script passed with its pre-existing EXE001 excluded |
| Visual build, identical-input repeat and freshness check | Passed; repeated package identity and artifact hashes agree; 60 artifacts plus the manifest |
| Baseline registry | 105 entities; 98 represented in SVGs; seven unresolved PB doors remain explicit under CF-013 |
| Annotation audit | Eight views, 154 named anchors, 82 dimensions, three cross-view callouts; all views have named dimensions; zero unresolved declared anchors |
| Baseline findings | 56 PASS, 171 OPEN, zero FAIL; OPEN includes benchmark applicability, missing geometry and professional gates |
| Current publication | All 27 SVG/PNG pairs and their provenance validated; no catalog or drawing-asset changes |
| Documentation | Generated README/guides and local Markdown paths/anchors checked; phase checkpoint, workflow, source inventory, discipline notes and research application status reconciled |
| Visual inspection | Section/worktop datums, interface unknowns, callout badges and Side A warning priority inspected; contact-sheet row heights adjusted to the actual preview heights |

```bash
python3 -m unittest discover -s dreamhouse -p 'test_*.py' -q
python3 -m ruff check dreamhouse/coordination dreamhouse/quantities dreamhouse/structure/vertical_continuity.py
python3 .github/scripts/sync_current_drawings.py --check
python3 .github/scripts/build_showcase.py --check-readme
python3 -m dreamhouse.coordination --visuals --require-no-fail
python3 -m dreamhouse.coordination --check --visuals --require-no-fail
```

These are local checks; remote CI execution is not claimed. Zero unresolved declared
anchors does not mean every entity or interface has sufficient geometry. The seven PB
doors are deliberately unrepresented, and unselected assemblies remain unknown. Review
the coverage denominator and discipline evidence alongside the counts.
