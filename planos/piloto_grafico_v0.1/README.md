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
