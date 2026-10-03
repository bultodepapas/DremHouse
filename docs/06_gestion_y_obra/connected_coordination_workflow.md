# Connected coordination workflow

**Version:** 0.3<br>
**Date:** 2026-10-02  
**Status:** two implemented source-to-review increments; schematic coordination only<br>
**Source:** owner authorization to implement the [phased plan](connected_project_coordination_next_step.md),
the [current-source audit](connected_source_inventory.md), PB b37/P2 b28/D-083, SC-01 and rooflight b12.  
**Decision:** D-084. Software workflow authority does not adopt a changed house design.

**Implementation reference:** first increment `0e69ddf`, documentation baseline `e58aba5`,
and [increment 02](connected_coordination_increment_02.md). This revision documents
bounded discipline adapters, annotated views and optional visual evidence under the same
software authority. Software phases 0–5 in the connected plan are distinct
from the project stage gates and the two construction phases in the
[master plan](plan_maestro.md).

## What now works

One Python command resolves the current architectural sources into a shared model,
evaluates supported rules, measures openings, reconciles the available cost mappings and
generates eight connected review SVGs plus a read-only HTML index. Changes originate in a
JSON study in the repository. Generated SVGs are outputs; no graphical editor or SVG
write-back exists.

The first registry contains 105 entities: 14 openings including the excluded dining
study, 30 doors including seven with unresolved placement, 26 space rectangles, 28 host
reference lines, four stair-column plan reservations and three stair envelopes. This is
an explicitly bounded coordination registry, not a complete building information model.
The host lines do not select wall assemblies; the reservations do not select columns.

The five `GLZ-*` bedroom elevation references are aliases of the corresponding `W-*`
entities. Their dimensions are calculated once. The new views and opening measurements
use those same objects, avoiding duplicate window quantities.

```mermaid
flowchart LR
    A[Preserved current source chain] --> R[Resolve one snapshot]
    B[Repository JSON study] --> R
    R --> E[Rules, discipline adapters, quantities and coverage]
    R --> V[Plans, elevations, opening details and section]
    E --> V
    E --> C[Cost reconciliation with unknowns]
    V --> A[Anchor and annotation audit]
    A --> P[Complete candidate package]
    C --> P
    P --> F[Input and output freshness check]
```

## Run the current-source review

From the repository root, with Python 3.11 or later and the project dependencies installed:

```bash
python3 -m dreamhouse.coordination
python3 -m dreamhouse.coordination --check
```

For PNG previews, contact sheets and archived-baseline pixel comparisons:

```bash
python3 -m pip install -e '.[presentation]'
python3 -m dreamhouse.coordination --visuals --require-no-fail
python3 -m dreamhouse.coordination --check --visuals --require-no-fail
```

`--check` alone detects the existing package's mode. The explicit `--visuals` check also
requires visual output. A nonvisual build needs no raster dependencies. The visual mode
uses the checked-in IBM Plex Sans files; CI pins resvg-py 0.4.0 and Pillow 11.3.0.

The installed entry point is `dreamhouse-coordinate`. Run it from an editable repository
checkout: this workflow deliberately depends on governance and published-source files
outside the Python package. A standalone wheel is not a complete project archive.

The command prints the generated `index.html` path. Open that file locally. The index
embeds the SVGs, supports read-only entity selection and exposes their findings. It does
not require a web server. `.build/coordination/latest.json` identifies the most recent
complete review; its `issue_id` selects `.build/coordination/issues/<issue_id>/`.

All candidate artifacts are in `.build/`, which is ignored by Git. Version the authored
study JSON in an appropriate repository folder when retaining a real study. CI retains
its generated review package as a downloadable artifact. Existing current aliases and
historical issue folders are not promoted by this command.

The package includes:

| Artifact | Purpose |
| --- | --- |
| `model.json` | Resolved identities, geometry, aliases, sources, relations, requested changes and conservative dependency hashes |
| `openings.json`, `quantities.json` | Active nominal opening measurements, excluded studies and explicit quantity-family mapping |
| `findings.json`, `coverage.json` | Rule findings, required inputs, numerical tolerance and evaluated/unsupported/inapplicable coverage |
| `changes.json`, `finding_lifecycle.json` | Comparison with the preserved current baseline, including prior finding evidence |
| `disciplines.json` | Bounded programme/equipment/workstation checks and source-referenced support-line plan comparisons |
| `dependencies.json` | Full-rebuild consumer relationships, entity/context change impact and outstanding professional evidence |
| `cost.json` | Existing cost-code reconciliation; unmapped or ineligible costs stay unknown; no approved total |
| `drawing_inventory.json` | All 27 published aliases, source hashes and pending migration status |
| `view_inventory.json`, `anchor_lifecycle.json` | Occurrence/annotation coverage, anchor coordinates, dimension/callout checks and before/after anchor changes |
| Eight SVGs and `index.html` | PB/P2 plans, four elevations, opening details and the GLZ-WS-A section/interface review |
| Optional PNGs, `contact_sheet.png`, `visual_manifest.json`, `visual_comparison.json`, `visual-diff/` | Pinned-font previews and exact pixel-change evidence; no automatic visual-approval threshold |
| Optional `baseline/` | Archived-baseline SVG/PNG previews, contact sheet and its rendering manifest |
| `review.md`, `manifest.json` | Readable review and complete output inventory with SHA-256 hashes and explicit authority |

Output paths inside the repository must be under `.build/`; external temporary/review
directories are also supported. Source/document/historical drawing folders are rejected
before either the build or freshness checker creates a lock or output file.

The nominal vertical opening total is **123.84 m²** and the rooflight total **23.04 m²**.
Workstation glazing is **27.36 m²**, in its own `PB-WORKSTATION-GLAZING` assembly. Nominal
opening area is not net glass area. The new ledger deliberately covers openings and
rooflight curbs; it is not the old integration pipeline's floor/programme ledger or a
whole-house takeoff. The older D059 scenario remains reproducible through its original
loader and command.

## Author and inspect a change

Create a study pinned to the current baseline:

```bash
python3 -m dreamhouse.coordination --study-template .build/studies/example.json --scenario-id EXAMPLE_ONLY
```

Edit the resulting JSON's `changes` object. This example changes a parameter in an
unadopted test scenario; it is not a proposed house change or a diagnosed current conflict:

```json
{
  "W-H1": {
    "expected": {"start_m": 21.8},
    "set": {"start_m": 22.0}
  }
}
```

Keep the generated `base_model_hash` and other top-level fields. Then run:

```bash
python3 -m dreamhouse.coordination --project .build/studies/example.json --out .build/study-review
python3 -m dreamhouse.coordination --project .build/studies/example.json --out .build/study-review --check
```

Use canonical entity IDs, not aliases or list positions. `expected` must contain exactly
the fields in `set`. The base fingerprint rejects a study based on changed source
semantics. Expected numeric values use a 1e-9 absolute comparison tolerance so ordinary
decimal authoring does not require binary-float display artifacts. Rule geometry uses
its separately declared numerical tolerance; neither tolerance specifies a construction
allowance.

Every study is applied to the archived PB b37/P2 b28 baseline. The build's lifecycle
comparison also uses that baseline, not the previous candidate selected by `latest.json`.
Keep the full intended study delta in its JSON file; a new empty template does not
inherit previous study changes. Review stale expected values against their actual source
before rebasing a study. The API can evaluate an explicitly supplied alternate baseline,
but the CLI does not currently offer that selection.

Supported changes are `start_m`, `width_m`, `height_m`, `sill_m` and `modules` for located
active windows/doors; rooflights support `x_m`, `y_m`, `length_m` and `width_m`. These
fields resolve through the existing host and level. Host reassignment, element addition,
deletion, room restructuring, product adoption and unresolved PB door placement are not
implemented authoring operations. An unsupported operation fails with a diagnostic.
Supplying a missing door height in a study creates an explicit assumption for that study;
it does not resolve the source design or approve the product.

Increment 02 adds captured `discipline_inputs` to the semantic fingerprint. A study
pinned before this schema extension may require a fresh template and a reviewed rebase.
Preserve its intended deltas and compare expected values; do not blindly replace the hash.
The captured context is generated evidence, not a second editable source.

An invalid input structure prevents generation. A structurally valid study with a
geometric FAIL remains available for inspection, with a FAIL manifest. Add
`--require-no-fail` when a caller needs exit code 2 for such findings. Exit code 0 from
the normal build means that the candidate was built, not that its design passed. `OPEN`
continues to mean unresolved even when no FAIL exists.

## Checks and limits

The evaluator checks nominal dimensions/family mappings, host extents, overlap of
openings sharing a host and opening/column interference when a supported column solid
and vertical extents are actually available. Source-declared module widths, window
placement on the boundary of its referenced space and rooflight plan containment also
have explicit checks. It enumerates candidate pairs afresh on
every run. Tests use clearly synthetic column boxes to verify interference, touching,
height separation, containment and missing-data behaviour. They do not assert that a
column clash exists in this house.

Actual SC-01 columns remain plan reservations with unknown heights. They produce
coverage gaps; a plan intersection with a located opening is reported as an OPEN pair
for review, not a confirmed solid collision or a claim of structural clearance. Definite plan overrun can fail a
host check while unknown host height still prevents a full containment pass. P2 door
heights, ambiguous PB door anchors and unsupported solids remain explicit. A disappeared
finding does not automatically become resolved; resolution requires a supported,
evaluated passing result. Removed or no-longer-applicable pairs retain their prior evidence.

The same evaluator now includes programme, workstation and equipment adapters. Current
normalized geometry overlays captured source context without reloading a hidden baseline.
D-065's 13.44 m² compact dressing supersedes the old 15 m² comparison, which remains
visible as inapplicable. Equipment geometry is a historical benchmark, so raw host or
clearance failures require product/layout review and remain OPEN applicability findings.
Four SC-01 reservations and six historical E0 positions receive plan comparisons against
current spaces/openings; all ten remain OPEN, without selected solids or verified heights.

Every generated view declares stable identities and named anchors. The builder checks
anchor references, supported linear measurements, callout destinations and per-view
coverage before publication. `window-sections.svg` compares GLZ-WS-A opening/worktop
levels and exposes unresolved control-layer interfaces; it supplies no invented assembly.

CF-009, CF-010, CF-011 and CF-012 remain open. The command does not calculate a new
structural design, fire approval, daylight simulation, MEP route, wall mass, thermal
performance or installed budget. Those consumers must be adapted and supplied with
their actual required data before their results can become part of the connected issue.

The source audit also records **CF-013**: PB core/rear door anchors differ between
archived plan, detail and elevation renderers. Their scalar source values remain in the
snapshot, but this increment deliberately leaves their endpoints unresolved pending
architectural reconciliation.

## Freshness, recovery and reproducibility

The build fingerprint conservatively covers package Python/JSON files, the study,
relevant governance, the current catalog and its source SVG/manifests, packaging and
available repository font files. This is deliberately a full-rebuild dependency set,
not a claim of minimal impact analysis. Model meaning has a separate fingerprint from
source paths and file bytes. The sorted Python JSON hash policy is explicitly not JCS.

`dependencies.json` records registered consumers and conservative affected-consumer
closure, including geometry and discipline-context changes. All consumers are rebuilt;
this is not a selective cache. Professional evidence remains outstanding and tied to the
model fingerprint, without manufacturing an approval.

Schema-2 packages distinguish `input_hash` from `issue_id`. The latter includes rendering
configuration and package schema, so visual and nonvisual exports can coexist for the
same source model. Font bytes and resvg/Pillow/FreeType versions participate in visual
identity; `--check` verifies them against the current environment.

The builder serializes concurrent writers to one output root using a local file lock,
writes to a staging directory, verifies the complete artifact inventory and rechecks
the inputs before exposing the issue through an atomic `latest.json` replacement. It
preserves prior complete packages. A renderer failure or changed input during the build
does not replace the previous pointer. `--check` detects edited SVGs, missing/extra
artifacts, changed manifests and stale source/code dependencies. It never imports a
manual SVG change back into the model.

A source edit after publication can make any previously built package stale; rerun
`--check` or rebuild before relying on it. Candidate locking uses `fcntl` and currently
targets Linux/macOS repository workflows. This is candidate publication only; atomic
promotion of all current catalog aliases is a separate rollout task. For recovery,
open the desired retained issue's `index.html` and manifest; do not relabel it fresh
without comparing it to its original inputs.

Governance files are among the declared dependencies, so a documentation-only change to
those files can legitimately make an existing candidate stale. Rebuild it through the
same command if a fresh local review is needed; do not alter its stored manifest. The
model fingerprint can remain identical while the input fingerprint changes.

SVG/HTML/JSON/Markdown remain the default artifacts. Optional PNG export disables
system-font discovery and uses the declared font files. Exact pixel comparison retains
changed-pixel counts/bounds and flags size/configuration incompatibility without resizing
or imposing a pass threshold. Scenario labels and findings can also cause pixel changes;
interpret them with entity/anchor changes. Its baseline is the archived current source
state, not the last candidate. Cross-platform equivalence is not certified.
Full engineered construction details and migration of the existing publication set remain
acceptance work.

## Extension points and next acceptance gates

- `dreamhouse/coordination/model.py`: source ownership, normalization, identities,
  strict study validation and freshness inputs. Add a family here only with a source
  and an explicit geometry capability.
- `dreamhouse/coordination/rules.py`: pure evaluation and rule metadata. New rules need
  supported-input criteria, failure/unknown fixtures and explicit engineering limits.
- `dreamhouse/coordination/disciplines.py`: pure bounded adapters for existing domain
  checks; preserve current design precedence and raw benchmark evidence.
- `dreamhouse/coordination/dependencies.py`: consumer relationships and changed-evidence
  obligations; extend it whenever a consumer is enrolled.
- `dreamhouse/coordination/render.py`: pure snapshot-to-SVG/HTML projections. New
  occurrences need stable entity/view IDs, anchored measurements and propagation tests.
- `dreamhouse/coordination/pipeline.py`: complete-package assembly. Register each new
  artifact in the same manifest; do not add independent source reloads inside consumers.
- `dreamhouse/coordination/view_contract.py`: semantic view/anchor/dimension/callout
  audits and anchor lifecycle; validate new annotation types explicitly.
- `dreamhouse/coordination/visual.py`: declared-font rendering, contact sheets and exact
  pixel evidence; rendering failure must preserve the previous complete package.

Before extending authoring beyond openings, finish the phase gates recorded in the
plan: qualify existing publication consumers against the shared snapshot and their
annotation/occurrence contract; resolve missing source data before extending discipline
claims. The bounded adapters, GLZ-WS-A plate and optional visual evidence do not complete
the broader engineering or publication migration. The 27-row audit makes that remaining
work explicit. No missing engineering geometry is filled in merely to advance a phase.

## Retained increment 01 evidence — 2026-10-02

| Check | Result |
| --- | --- |
| Full repository unittest discovery | 353 tests passed; historical regressions retained |
| Final renderer regression check | 10 tests passed, including floor datums and visible failure priority |
| Ruff on coordination and quantities | Passed |
| Current drawing provenance | All 27 SVG/PNG pairs passed; no source promotion |
| Generated README consistency | Passed |
| Candidate build, repeat build and freshness verification | Passed; full artifact inventories agree for matching inputs |
| Resolved baseline | 105 entities; 98 have SVG occurrences; seven unresolved PB doors remain in the registry/findings |
| Baseline findings | 53 PASS, 138 OPEN, zero FAIL; these counts include coverage and standing professional gates |
| Visual review | P2 footprint, opening detail plate, Side A and rear projections rendered locally; finding text wrapping and absolute PB/P2 datums checked |

```bash
python3 -m unittest discover -s dreamhouse -p 'test_*.py'
python3 -m ruff check dreamhouse/coordination dreamhouse/quantities
python3 .github/scripts/sync_current_drawings.py --check
python3 .github/scripts/build_showcase.py --check-readme
python3 -m dreamhouse.coordination --require-no-fail
python3 -m dreamhouse.coordination --check --require-no-fail
```

The GitHub workflow is configured in `.github/workflows/coordination.yml`; remote CI
execution is not claimed by this local verification record. These checks establish
the implemented candidate workflow, not completion of the remaining plan phases.

The test counts above are the retained implementation verification record, not a claim
that each subsequent documentation edit reruns every engineering calculation. For a
documentation reconciliation, validate local paths, generated indexes, current-publication
provenance and any affected build fingerprints. Keep the dated software test evidence
and the documentation checks distinguishable.

### Documentation reconciliation verification — 2026-10-02

The v0.2 documentation update was checked against implementation commit `0e69ddf`:

| Check | Result for this documentation revision |
| --- | --- |
| Local Markdown references in 22 updated documents | 437 paths/anchors checked; no missing targets or anchors |
| Generated publication guides and current provenance | All three guides match their maintained templates; 27 SVG/PNG pairs validated |
| Generated root README block | Consistent with the catalog and project registers |
| Existing candidate freshness | Verified with `--check --require-no-fail`; status remains OPEN, engineering/construction authority false |
| Change scope | Markdown and Markdown template text only; no model, calculation, catalog or drawing-source change |
| Whitespace and template lint | `git diff --check` passed; Ruff passed with pre-existing EXE001 excluded for the Python-invoked, non-executable publication script |

The full software suite was not rerun for these editorial changes. Its implementation
results remain the dated record above. No additional phase gate is marked complete by
this reconciliation.

### Increment 02 verification — 2026-10-02

The [increment 02 record](connected_coordination_increment_02.md) contains current test,
artifact, annotation and visual-review evidence. The tables above preserve the earlier
software and documentation checkpoints; their counts do not describe the extended package.
