# Connected coordination — consumer migration and extension guide

**Version:** 0.3<br>
**Date:** 2026-10-03<br>
**Status:** software consumer migration verified within declared coverage; schematic review authority only<br>
**Source:** owner's instruction to complete software migrations; D-084; implementation
baselines `f0448ef` and `d7c3e65`; the [phased plan](connected_project_coordination_next_step.md).<br>
**Scope:** connected source consumers, review publication, recovery and maintenance of
the software. No changed house design, adopted equipment, engineering approval or cost
target is established.

## Routine operation

```bash
python3 -m pip install -e '.[presentation]' resvg-py==0.4.0 Pillow==11.3.0
python3 -m dreamhouse.coordination --visuals --require-no-fail --release
python3 -m dreamhouse.coordination --check --visuals --require-no-fail
python3 -m dreamhouse.coordination --check-release
python3 .github/scripts/build_showcase.py --site-dir .build/showcase --coordination-out .build/coordination
```

The build resolves inputs once and passes that snapshot to the checks, measurements,
review projections and catalog consumers. A complete candidate is available under
`.build/coordination/issues/<issue_id>/`. The source SVGs and published historical aliases
retain their original authority and provenance. Their migrated consumers produce new
review artifacts, with coverage and limitations recorded in `drawing_inventory.json`.

`--release` selects a complete, verified current-baseline review package. It rejects FAIL
packages and studies with requested model changes. An OPEN release is still schematic
evidence. This prevents an arbitrary study from becoming an adopted design through an
automated publishing command.

The showcase export includes the selected immutable release and its reader. CI builds
this connected review when package sources change, alongside the adopted drawing gallery.
The `drawing_inventory.json` report is a separate migration ledger for registered drawing
consumers: it exposes generated projections and per-item limitations, and does not establish
full equivalence for every one of the 27 adopted sheets. Neither a GitHub Actions success
nor a visual comparison supplies professional approval.

## Source edits, studies and automatic rebuilds

Continue to author geometry in repository JSON/Python. SVGs and generated snapshots
remain outputs. Create a study with `--study-template`, retain its baseline fingerprint,
and supply expected values for the exact parameters being changed. The
[workflow](connected_coordination_workflow.md) documents that input format.

```bash
python3 -m dreamhouse.coordination --project .build/studies/example.json --out .build/example --visuals
python3 -m dreamhouse.coordination --project .build/studies/example.json --out .build/example --watch
```

Watching is optional and creates candidates only. It debounces source saves, waits
through incomplete JSON and preserves the previous complete package after a failed
build. Every watched build runs in a fresh Python interpreter, so loader and rule edits
are reloaded as well. Stop it with Ctrl-C. Files generated under `.build/` do not trigger rebuild loops.

`structural_screening.json` retains the numerical E0/E1 screening inputs and raw results
used by the structural sheets. Those source hypotheses are not an adopted structural
design; read their OPEN/FAIL evidence with CF-009 and the declared engineering gaps.

`capabilities.json` lists every normalized entity's supported study fields, source,
represented occurrences and evaluated/unsupported rules. Source-context records such as
wall types, maintenance requirements and service reservations remain distinct from
editable geometry. A field absent from the capability report is not silently supported.

### Migrate a pinned study without discarding its preconditions

```bash
python3 -m dreamhouse.coordination --project .build/studies/old.json --migrate-study .build/studies/rebased.json
python3 -m dreamhouse.coordination --project .build/studies/rebased.json --out .build/rebased --visuals --require-no-fail
```

The first command compares every original `expected` value with the current baseline.
It preserves requested changes and expected values and updates only the baseline hash.
It creates a new study and an adjacent migration report; `--migration-report PATH`
selects a separate report destination. Existing destinations are never overwritten.
A conflicting precondition produces a report only and exit status 2. Malformed or
unsupported operations are rejected. The original study remains unchanged.

A ready report is not evidence that unchanged context is equivalent: the complete
candidate must run again against the current sources. The report records original
study, semantic baseline and current input fingerprints. This supports migration from
older studies without silently accepting a changed surrounding design. Watching uses
candidate rebuilds; `--watch --require-no-fail` is rejected because a persistent watcher
cannot provide a one-shot finding exit status.

### Source-bound dimensions and cross-sheet navigation

The root review index includes all enrolled entities, links to actual inventoried SVG
occurrences, and per-sheet annotation coverage. Unrepresented entities and unresolved
references remain visible. SVGs are generated output; these controls navigate and
highlight the review, not edit geometry.

`view_inventory.json` schema 3 records source checks separately from numerical
measurement and visible-label checks. Known opening-feature anchors in the eight
review projections bind to explicit model paths (or declared coordinate midpoints).
Linear dimensions and four-anchor rectangular areas are evaluated numerically;
labels declaring the fixed-format contract are checked against their painted text.
Unbound context anchors and unsupported annotations are reported without approval.

Five native catalog views now carry source-bound opening dimensions: front and side
A/B elevations, roof plan, and the measured A/B technical-bench elevations. Registered
transforms independently compare actual SVG rectangles with source coordinates.
Missing occurrences, changed rectangles, broken source bindings, corrupted declared
labels and inconsistent dimensions block the candidate before pointer selection.
Other sheets retain explicit unsupported/not-applicable annotation coverage; their
native detail graphics are not silently certified by these five projection contracts.

## Complete packages and recovery

The candidate manifest is schema version 3. Its identity includes source dependencies,
package schema and the selected rendering configuration. `drawing_catalog` and
`drawing_source_evidence` are captured publication provenance; they never override
normalized geometry or become additional editable masters.

Review releases live in `.build/coordination/published/releases/<release_id>/`.
`current.json` is the single mutable selection pointer. The stable HTTP reader resolves
that pointer to an immutable index; the CLI also prints a direct local file path.
Publication verifies all artifacts before and after copying, rechecks source freshness,
and changes the pointer only after the release is complete.

```bash
python3 -m dreamhouse.coordination --rollback <retained-release-id>
```

Rollback validates the retained package and selects it without regenerating it. Its
selection records that source freshness was not revalidated. An explicit
`--check-release` compares it with current inputs and the rendering environment; an older
release can remain intact and inspectable while correctly failing that freshness check.
`--watch` only rebuilds isolated candidates after source changes; it does not publish or
roll back a release. Do not edit a release manifest to relabel it as current.

The tracked `planos/actual/catalog.json` and historical stable aliases are the adopted
issue record. Review-release selection does not rewrite that record or close its known
conflicts. This distinction is preserved in the connected drawing index and showcase.

## Extending the system

| Change | Implementation location | Required evidence |
| --- | --- | --- |
| Add a source or entity family | `coordination/model.py` | Source owner and precedence; stable IDs; units/datums; explicit unknowns; semantic and dependency hashes; independent archived baseline |
| Add a study operation | `editable_fields()` and input validation | Expected-value preconditions, geometry update, reference validation, before/after findings and every affected view/quantity; reject unsupported cases |
| Add a calculation or engineering adapter | `coordination/rules.py`, `disciplines.py` or `extensions.py` | Pure snapshot input; required data; evaluated/unsupported coverage; stable finding identity; missing-input lifecycle; no inherited engineering approval |
| Add or migrate a catalog drawing | `coordination/drawings.py` | Explicit catalog identity and injected inputs; source-change propagation through geometry and text; no hidden loaders; declared partial or unsupported scope |
| Add a projection or annotation | `coordination/render.py`, `drawing_annotations.py` and `view_contract.py` | Stable view/occurrence IDs, known anchors, numerical dimension checks and working callout destinations; corruption and rename fixtures |
| Add a consumer | `coordination/dependencies.py` and `pipeline.py` | Dependency graph entry, complete artifact inventory, freshness and rollback behaviour; same-snapshot output |
| Change raster output | `coordination/visual.py` and declared fonts | Recorded renderer/font configuration, deterministic repeated export, contact-sheet inspection and exact pixel comparison with no automatic design-approval threshold |

Keep old scenario loaders and regression assertions reproducible. A new source revision
must describe its precedence; it must not silently reinterpret the old D059 scenario,
E0/E1 hypotheses, or an unresolved PB door anchor. Generated artifacts belong in the
same package inventory; never append an independently built drawing after publication.

## External information and design gates

The software can expose missing inputs and invalidate affected evidence; it cannot
invent a site survey, selected product, structural member, service route or commissioning
record. CF-009–CF-014 retain their source-specific closure requirements. The connected
extension records distinguish wall-line quantities from surface area/mass, stair
arithmetic from egress approval, reserved service envelopes from routes, and specified
assets from installed/tested/commissioned equipment.

The migration identified CF-014: an inherited P2-W05 note says 297/300 mm while the
current structured layers total 229 mm and D-080 schedules 230 mm nominal. The extension
evidence exposes the discrepancy without selecting a new build-up or mass.

Completion of a software migration means its declared inputs reach its consumers and
its unsupported claims are visible. It does not mean that all disciplines or the house's
design are complete. The phase checkpoint and verification record must state those
separate outcomes explicitly.

## Current completion record — continuation from d7c3e65

This continuation implements study migration and a stricter annotation contract under
D-084. It retains the earlier full drawing-consumer migration and adds these boundaries:

| Capability | Current evidence | Explicit limit |
| --- | --- | --- |
| Source propagation | 35 SVGs, 105 entities, 98 represented, 36 parameter-editable entities | Seven PB doors still lack source placement; no general add/delete/rehost authoring |
| Source-bound annotations | 204 of 214 anchors linked to model paths; all 112 declared measurements evaluated; 95 declared numeric labels checked | Ten context anchors and 17 labels lack source/text contracts; coverage is not inferred |
| Native geometric projections | Five catalog sheets, 15 actual rectangles and 30 named dimensions | 15 geometric sheets remain unsupported for this stricter annotation contract; seven nonmetric sheets are not applicable |
| Study migration | Existing W-H1 study migrated to a separate candidate and fully reevaluated; original preserved | Its intentionally incompatible module width remains FAIL after migration; migration is not acceptance |
| Review navigation | All 35 sheets and actual entity occurrence destinations exposed through the main index | Missing occurrences remain visible; no SVG write-back |
| Source conflicts | CF-014 now propagates in model conflict context | The inherited wall-build-up discrepancy remains unresolved |

Five rendered native sheets were inspected at 1400 px: front and both side elevations,
roof plan and technical-workbench elevations. Checks cover source projection, anchors,
measurements and declared labels; they do not constitute a general text collision engine.
Navigation is checked through real inventories and HTML contract tests; no browser-driven
interaction test is claimed in this environment.

### Integrated acceptance for this continuation

- **493 repository tests passed** with `python3 -m unittest discover -s dreamhouse -p 'test_*.py'`.
- Ruff passed for coordination and quantities; `git diff --check` passed. All 260 local
  links in changed Markdown resolved; generated README and all 27 historical alias pairs
  passed their checks. No tracked design JSON/SVG/PNG or legacy source was changed.
- Baseline findings remain **57 PASS / 186 OPEN / 0 FAIL**. The visual package contains
  **199 hashed artifacts** and regenerated all 35 current and archived-baseline SVGs.
- Repeated complete visual generation produced the same manifest and image hashes.
  Candidate/release freshness, failed-study publication refusal, rollback, rejection of
  stale history, restoration and same-release showcase export all passed.
- The existing study was migrated through the CLI to
  `.build/studies/completion-migrated.json`; its W-H1 module inconsistency remained FAIL
  after a complete build (exit 2), as required. Original-precondition conflict, refusal
  to overwrite files, and interrupted-write recovery are covered by migration tests.
- Corrupted native geometry blocks the pipeline while preserving the prior complete
  candidate pointer. Annotation tests also reject transformed geometry, stale source
  coordinates, invalid rectangular-area spans and corrupted declared label text.

```text
Candidate: 6808fe0b2ea3268b5605ae34c029846409c1b006ae139d86eea38647678bf131
Release:   0f048a03556d25cf48d8176589b38acdc03a7eeb912f03e2271d12e530e65320
Study:     b9963cf41f05091235ff7da3b486562469c0b5f59da0dbd497e4d67ccdb8b1ce
```

The main review is `.build/coordination/issues/6808fe0b2ea3268b5605ae34c029846409c1b006ae139d86eea38647678bf131/index.html`.
Logs and the machine-readable acceptance record are
`.build/connected-completion-tests.log`, `.build/connected-completion-build.log`,
`.build/connected-completion-verification.log` and `.build/connected-completion-verification.json`.
The showcase was regenerated locally; no remote deployment or remote CI run is claimed.

## Previous verification record — migration from f0448ef

Local integrated acceptance completed on **2026-10-03** against the working tree based
on `f0448ef`. These retained results superseded the earlier increments' software-delivery counts;
they do not supersede the design decisions or unresolved professional gates.

| Check | Result and scope |
| --- | --- |
| Complete repository suite | **468 tests passed** with `python3 -m unittest discover -s dreamhouse -p 'test_*.py'` |
| Static checks | Ruff passed for coordination, quantities, changed drawing/structural modules and publication scripts; the scripts retain their existing non-executable-file convention (`EXE001` excluded). `git diff --check` passed |
| Complete visual package | **35 current SVGs**: eight review projections and 27 catalog consumers; 35 independently rendered archived-baseline SVGs; current/baseline PNGs, difference images, contact sheets and reports; **199 hashed artifacts** |
| Actual entity coverage | **105 entities**, **98 represented**, **36 with supported study parameter changes**. The seven unlocated PB doors remain explicitly unresolved under CF-013 |
| Baseline evaluation | **57 PASS / 186 OPEN / 0 FAIL**; OPEN includes missing inputs and unsupported professional conclusions, not passed engineering checks |
| Repeat generation | Rebuilding the complete 1400 px visual package produced the same issue identity and complete artifact manifest, including PNG hashes |
| Freshness | Candidate and selected immutable release passed the CLI source/artifact checks after the final code changes |
| Propagation study | An isolated W-H1 width change from 3.60 to 3.00 m updated plans, elevation, detail, schedule and quantities; P2 window area became **52.98 m²**, exterior wall-line remainder **26.80 m**, and `OPENING-MODULE-CONSISTENCY` became FAIL. Publishing that study was refused |
| Native geometry regression | Separate H2/G dimensions, workstation position/sill, technical-window position/size/modules, front-door dimensions and rooflight geometry/screening are tested through their actual consumers; snapshot rendering performs no hidden file reads and does not mutate inputs |
| Source watch | Debounce, incomplete JSON, failure recovery and fresh-interpreter builds are tested; the propagation acceptance study also ran through the fresh-process builder |
| Recovery | Selected and verified an older complete release, confirmed its stale dependencies were rejected by a freshness check, then restored and reselected the current verified release |
| Connected showcase | Direct script invocation exported the same selected immutable review to `.build/showcase/`; verification runs before and after copying |
| Historical compatibility | The 27 adopted SVG/PNG pairs retain valid provenance. Five structural sheets and the P2 bedroom/workstation details reproduce byte-for-byte; regression tests also preserve original roof, front/side and technical-bench output |
| Documentation | Generated README/catalog checks and changed-document local links passed; no tracked design JSON, SVG, PNG or `BORN_Legacy` evidence was changed |

Visual inspection covered the front elevation, bedroom-window detail, workstation
interface, technical benches and structural continuity sheet. It exposed and corrected
missing native text under pinned-font rasterization, overlapping workstation annotation,
and unknown PB-door locations previously styled like confirmed conflicts. Raster tests
check visible banner contrast at thumbnail scale. This is targeted visual acceptance;
it is not an assertion that every annotation in all 35 views has been independently
audited or that schematic interfaces are construction details.

The final local artifacts are identified by:

```text
Candidate: e535311fff7e3a75df4773525d7b9e2686a5f4eac08aae203c99aa683d04105d
Release:   0e37c1be09065e1406322d6a73f8b9327ef0d65a59baeea22dd258c8f7551300
Study:     651cced8a6e0b9b56906576c37d5e4bbf372f116bd443e99d52f1426c0cd1032
```

Open the release's `drawings/index.html` for catalog thumbnails, or its root `index.html`
for the connected review and evidence. Local execution logs and the acceptance summary
are in `.build/migration-tests.log`, `.build/migration-verification.log` and
`.build/migration-verification.json`; generated `.build/` artifacts are not tracked.
Future source/code edits deliberately produce a different input fingerprint and require
a fresh build. GitHub Actions configuration was updated, but no remote CI run or external
deployment is claimed by this local record.

The remaining work is explicit: reconcile CF-013/CF-014, supply the outstanding
engineering/product/site inputs, broaden named annotation coverage per sheet, and enroll
new authoring operations or entity families through the extension contract above. The
software migration does not close those separate design and coverage gates.
