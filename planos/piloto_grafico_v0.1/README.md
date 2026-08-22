# Graphic presentation pilot v0.1

This folder contains presentation-only SVG prototypes. They are not current drawings,
do not supersede any versioned source, and have no design, procurement or construction
authority.

## GP01 — ground-floor readability

- Source: `../actual/DH-ARQ-PLN-001_CURRENT-GROUND-FLOOR.svg`
- Generator: `../../dreamhouse/svg/pilot_ground_floor.py`
- Output: `DH-ARQ-PLN-001-GP01_GROUND-FLOOR-READABILITY-PILOT.svg`
- Review: `../../docs/08_investigacion/svg_graphic_pilot_01_visual_review.md`

Regenerate from the repository root:

```bash
python3 -m dreamhouse.svg.pilot_ground_floor
```

The generator copies source-space geometry without coordinate changes. It may alter the
sheet canvas, presentation attributes and annotation placement only.

## GP02 — Side B elevation readability

- Source: `../actual/DH-ARQ-ELE-004_CURRENT-SIDE-B.svg`
- Generator: `../../dreamhouse/svg/pilot_side_b.py`
- Output: `DH-ARQ-ELE-004-GP02_SIDE-B-READABILITY-PILOT.svg`
- Manifest: `DH-ARQ-ELE-004-GP02.manifest.json`
- Review: `../../docs/08_investigacion/svg_graphic_pilot_02_visual_review.md`

Regenerate the pilot and its untracked visual-review build from the repository root:

```bash
python3 -m dreamhouse.svg.pilot_side_b
python3 -m dreamhouse.svg.audit \
  --before planos/actual/DH-ARQ-ELE-004_CURRENT-SIDE-B.svg \
  --after planos/piloto_grafico_v0.1/DH-ARQ-ELE-004-GP02_SIDE-B-READABILITY-PILOT.svg \
  --output-dir .build/svg-pilot/gp02 \
  --prefix gp02
```

GP02 copies the R10 façade, opening, level and dimension geometry without coordinate
changes. `GLZ-DINING-STUDY-B` remains outside the façade geometry and is shown only as a
`NOT ADOPTED` evidence item.

## GP03 — transverse roof-section readability

- Source: `../actual/DH-ARQ-SEC-002_CURRENT-TRANSVERSE.svg`
- Generator: `../../dreamhouse/svg/pilot_transverse_section.py`
- Output: `DH-ARQ-SEC-002-GP03_TRANSVERSE-SECTION-READABILITY-PILOT.svg`
- Manifest: `DH-ARQ-SEC-002-GP03.manifest.json`
- Review: `../../docs/08_investigacion/svg_graphic_pilot_03_visual_review.md`

Regenerate the pilot and its untracked visual-review build from the repository root:

```bash
python3 -m dreamhouse.svg.pilot_transverse_section
python3 -m dreamhouse.svg.audit \
  --before planos/actual/DH-ARQ-SEC-002_CURRENT-TRANSVERSE.svg \
  --after planos/piloto_grafico_v0.1/DH-ARQ-SEC-002-GP03_TRANSVERSE-SECTION-READABILITY-PILOT.svg \
  --output-dir .build/svg-pilot/gp03 \
  --prefix gp03
```

GP03 repairs the missing scalable viewport only in the pilot, copies the R06 technical
geometry without coordinate changes and keeps D-039 explicitly provisional.

## GP04 — P2 wall-family readability

- Source: `../actual/DH-ARQ-DET-003_CURRENT-P2-ACOUSTIC-PARTITION.svg`
- Generator: `../../dreamhouse/svg/pilot_p2_wall_family.py`
- Output: `DH-ARQ-DET-003-GP04_P2-WALL-FAMILY-READABILITY-PILOT.svg`
- Manifest: `DH-ARQ-DET-003-GP04.manifest.json`
- Review: `../../docs/08_investigacion/svg_graphic_pilot_04_visual_review.md`

Regenerate the pilot and its untracked visual-review build from the repository root:

```bash
python3 -m dreamhouse.svg.pilot_p2_wall_family
python3 -m dreamhouse.svg.audit \
  --before planos/actual/DH-ARQ-DET-003_CURRENT-P2-ACOUSTIC-PARTITION.svg \
  --after planos/piloto_grafico_v0.1/DH-ARQ-DET-003-GP04_P2-WALL-FAMILY-READABILITY-PILOT.svg \
  --output-dir .build/svg-pilot/gp04 \
  --prefix gp04
```

GP04 copies the R22 W01A/W01B controlled build-up geometry without coordinate changes,
retains every D-080 wall type and adds pattern-plus-text layer coding. It claims no
tested performance and books no saving.

## GP05 — integrated E1 structural evidence readability

- Source: `../actual/DH-EST-E1-001_CURRENT-SYNTHESIS.svg`
- Generator: `../../dreamhouse/svg/pilot_e1_synthesis.py`
- Output: `DH-EST-E1-001-GP05_STRUCTURAL-EVIDENCE-READABILITY-PILOT.svg`
- Manifest: `DH-EST-E1-001-GP05.manifest.json`
- Review: `../../docs/08_investigacion/svg_graphic_pilot_05_visual_review.md`

Regenerate the pilot and its untracked visual-review build from the repository root:

```bash
python3 -m dreamhouse.svg.pilot_e1_synthesis
python3 -m dreamhouse.svg.audit \
  --before planos/actual/DH-EST-E1-001_CURRENT-SYNTHESIS.svg \
  --after planos/piloto_grafico_v0.1/DH-EST-E1-001-GP05_STRUCTURAL-EVIDENCE-READABILITY-PILOT.svg \
  --output-dir .build/svg-pilot/gp05 \
  --prefix gp05
```

GP05 copies all six calculation-linked technical geometry groups, retains the nine-row
evidence matrix and keeps every system-design result blocked. It selects no structural
system, section, quantity, product or construction release.

## Shared static lint

Run the staged fail-closed profile across all five pilots:

```bash
python3 -m dreamhouse.svg.lint planos/piloto_grafico_v0.1 \
  --format markdown \
  --json-output .build/svg-lint/pilots.json \
  --markdown-output .build/svg-lint/pilots.md
```

The v0.2 gate fails on identity, accessibility, authority, unsafe content, semantic-layer,
model-reference, non-finite-number, presentation-palette, text-contrast and required-text
errors. It reports inherited colour/precision, scaled-lineweight and source-microtext debt
as warnings. See `../../docs/08_investigacion/svg_static_lint_v0.1.md` and
`../../docs/08_investigacion/svg_palette_contrast_lint_v0.2.md` for the implemented boundary
and remaining bounds/collision checks.
