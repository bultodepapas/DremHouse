# Contributing to Dream House

**Status:** active contributor guide<br>
**Version:** 0.6<br>
**Date:** 2026-10-03<br>
**Source:** repository instructions, D-044, D-056 and D-084 connected coordination migration.

This repository is a living technical project record, not a collection of
unconnected ideas. Every contribution must preserve traceability across source,
decision, assumption, drawing, and cost.

## Before making a change

1. Read the [project-record index](docs/README.md), the
   [Project Constitution](docs/00_gobernanza/constitucion_del_proyecto.md), and the
   [document precedence](docs/00_gobernanza/fuentes_precedencia_y_conflictos.md).
2. Determine whether the information is a hard rule, a control value, an
   assumption, or an open matter.
3. Never resolve a contradiction silently: record the conflict or open a
   decision.
4. If the change affects scope or cost, update the
   [Cost Baseline and Control](docs/04_costos/base_y_control_de_costos.md).
5. Follow the
   [Language and Translation Policy](docs/00_gobernanza/language_and_translation_policy.md).
   Do not translate or edit files under `docs/BORN_Legacy/`.

## Recommended workflow

- Open a **decision** issue for a change in criteria, or an **RFI** for a
  technical query.
- Work in the existing checkout; **do not create branches**, as required by
  [`AGENTS.md`](AGENTS.md). Keep each contribution focused and reviewable.
- State the source, date, version, status, assumptions, and affected documents.
- When issuing a drawing, retain its `manifest.json` and limitation-of-use note.
- When that issue becomes current, update its entry in
  [`planos/actual/catalog.json`](planos/actual/catalog.json). Promotion is explicit: never
  infer authority from the highest revision number.
- A connected coordination review release is a separate immutable evidence package. It
  does not promote an adopted drawing, change stable aliases, or close an engineering gate.
  See the [migration and extension guide](docs/06_gestion_y_obra/connected_coordination_migration_and_extension_guide.md).
- Keep the versioned issue in place. The stable SVG/PNG aliases are additional
  publication copies, not replacements for history.
- Validate existing publication before submitting changes:

```bash
python3 .github/scripts/sync_current_drawings.py --check
python3 .github/scripts/build_showcase.py --check-readme
```

### Source-driven coordination changes

Follow the [coordination workflow](docs/06_gestion_y_obra/connected_coordination_workflow.md)
and [increment 02 record](docs/06_gestion_y_obra/connected_coordination_increment_02.md).
Create a pinned JSON study, change supported fields by canonical entity ID, then build
and inspect the complete candidate. It produces nine review SVGs, including the schematic
GLZ-WS-A interface and SC-01 stair-envelope sections. Named anchors, dimensions, declared
labels and saved finding viewpoints retain explicit source and package identity.
Preserve historical hash-locked inputs; do not edit SVGs, generated snapshots or current
aliases to author geometry. Record the resulting design decision separately before
adopting any study into the published source basis.

```bash
python3 -m pip install -e '.[optimization,dev,presentation]'
python3 -m unittest discover -s dreamhouse -p 'test_*.py'
python3 -m ruff check dreamhouse/coordination dreamhouse/quantities
python3 -m dreamhouse.coordination --require-no-fail
python3 -m dreamhouse.coordination --check --require-no-fail
python3 -m dreamhouse.coordination --visuals --require-no-fail --release
python3 -m dreamhouse.coordination --check-release
```

For optional visual review, use the pinned-font renderer with system font discovery
disabled:

```bash
python3 -m pip install -e '.[presentation]'
python3 -m dreamhouse.coordination --visuals
python3 -m dreamhouse.coordination --check --visuals
```

This adds PNG previews, contact sheets and pixel-difference evidence; it does not approve
a drawing. Consumer-impact metadata identifies affected outputs, but builds still rebuild
the complete candidate. Programme and workstation checks use current resolved data;
equipment geometry remains an unadopted benchmark with OPEN applicability, and ten
structural line comparisons establish plan relationships only. Unsupported geometry,
capacity and professional engineering remain OPEN.

The `drawing_inventory.json` file is a connected-consumer migration ledger; its registered
coverage and limitations are separate from adopted issues in `planos/actual/catalog.json`.
Do not infer complete equivalence across all 27 published sheets from a connected release.
The full regression suite uses the existing optimization dependencies; the coordination
builder itself does not require them. OPEN findings remain unresolved even if the command
exits successfully. `--release` selects only a complete no-change current-baseline review;
`--check-release` compares the selected package with current inputs. `--rollback <id>`
selects a verified retained package and marks freshness as not revalidated. Neither action
promotes the current drawing catalog.

For iterative studies, `--watch` debounces source edits and rebuilds candidates while
preserving the last complete package after an invalid or failed build. It never selects a
release. The [migration and extension guide](docs/06_gestion_y_obra/connected_coordination_migration_and_extension_guide.md)
records the review commands and extension requirements.
When changing source ownership, rules, outputs or supported authoring operations, update
the increment record, workflow, source inventory, phase checkpoint and affected discipline
documents.

### Synchronize an explicitly promoted issue

Use these write commands after a publication decision and catalog update, or to regenerate
documentation from its maintained template. Review the diff; synchronization itself is
not design adoption. For documentation-only work, SVG/PNG source bytes and catalog entries
must remain unchanged.

```powershell
python -m pip install -e ".[presentation]"
python .github/scripts/sync_current_drawings.py --write
python .github/scripts/build_showcase.py --write-readme --site-dir .build/showcase
python .github/scripts/sync_current_drawings.py --check
python .github/scripts/build_showcase.py --check-readme
```

The drawing indexes in `planos/README.md`, `planos/actual/README.md` and
`docs/02_arquitectura/planos_actuales.md` are generated by
`.github/scripts/sync_current_drawings.py`. Update their Markdown templates before
regenerating them. The root README's `showcase:begin`/`showcase:end` block is generated
by `build_showcase.py`; maintain its surrounding prose directly.

## Acceptance criteria

A contribution is ready when it is traceable, does not violate hard rules,
states its uncertainties, updates every affected document, and clearly
distinguishes concept work, coordination information, and construction-ready
documentation.

Pinned coordination studies can be migrated with `--project OLD.json --migrate-study
NEW.json`. Retain the generated report and reevaluate the new candidate; a changed
expected value is a conflict, not permission to replace its precondition. When adding
annotations, test source coordinates, numerical spans and declared visible text
independently. Register a source-to-SVG transform before claiming native projection
coverage; keep unsupported sheets explicit in the inventory.

The candidate's `phase_gates.md` links all nineteen software subphases to artifacts and
acceptance test modules. Keep view settings independent of physical geometry. Saved issue
links must use stable finding/entity/view identities and the original package fingerprints;
never infer identity from display order. Retained professional evidence must be invalidated
when its declared source/dependencies change; freshness does not grant professional approval.
