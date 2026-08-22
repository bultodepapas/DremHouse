# SVG palette and contrast lint v0.2 — controlled presentation colour gate

**Status:** implemented for the five presentation pilots; not approved for current-drawing
rollout  
**Version:** 0.2  
**Date:** 2026-08-22  
**Source:** `architectural_drawing_conventions_research.md`,
`svg_drawing_system_improvement_plan.md`, `svg_static_lint_v0.1.md` and GP01–GP05  
**Implementation:** `dreamhouse/svg/theme.py`, `dreamhouse/svg/lint.py` and the five pilot
generators  
**Authority boundary:** presentation-quality control only. This batch changes no model
geometry, design value, evidence result, scope, cost, current alias or construction
authority.

## 1. Outcome

The static SVG gate now validates controlled presentation colours and computes text
contrast against an explicit semantic background. All five pilots pass with:

- zero presentation colours outside the approved palette;
- zero missing or unresolved presentation text/background relationships;
- zero computed contrast failures;
- zero model-space geometry differences; and
- a minimum computed presentation-text contrast of 4.67:1 across the pilot set.

The profile evaluates 373 editorial text elements. It deliberately excludes 119 inherited
model texts whose local backgrounds vary with source geometry; their colour and microtext
debt remains quantified separately. Passing this profile does not pass SVG-G0, SVG-G1 or
SVG-G2 and does not promote any pilot into `planos/actual/`.

## 2. Controlled palette

`dreamhouse/svg/theme.py` is now the single palette registry for pilot presentation. Its
30 unique semantic tokens cover:

- paper, panel, ink and muted editorial colours;
- information, open, conflict and hypothesis states;
- dark-footer foregrounds and rules;
- open, hypothesis and alternating table surfaces;
- GP01 programme-entry surfaces;
- GP04 material-pattern colours; and
- GP05 gravity, trial and composited rooflight cues.

The shared stylesheet serialises every token deterministically as a CSS custom property.
GP01 now consumes that common stylesheet instead of maintaining a near-duplicate copy.

`SVG-C001` fails on an unapproved literal in presentation layers or presentation CSS.
`SVG-C002` warns, without rewriting, when copied model/definition content retains colours
outside the presentation palette. This distinction prevents a graphic migration from
silently altering technical source geometry or material/program cues.

## 3. Computed contrast contract

Every presentation text inherits or directly declares `data-contrast-bg="#RRGGBB"` from
the semantic panel on which it is read. The linter resolves:

- CSS custom properties;
- tag and class declarations with selector specificity;
- presentation attributes and inline style;
- inherited fill and font weight;
- nested `scale(...)` transforms; and
- effective text size at the configured 1,400 px publication width.

The relative-luminance and contrast-ratio calculation follows the accessibility method
recorded in the architectural communication research. Normal text must reach 4.5:1. Text
rendering at least 24 px, or bold text rendering at least 18.66 px, may use the 3:1 large-
text threshold. Thresholds and large-text sizes remain configurable CLI/profile values.

Contrast findings fail closed:

- `SVG-C003`: presentation text has no typed contrast background;
- `SVG-C004`: foreground or background cannot resolve to a six-digit colour; and
- `SVG-C005`: computed ratio falls below the applicable threshold.

## 4. Defects found and corrected

### 4.1 GP05 rooflight labels

`RL-CAR` and `RL-RC` used near-white text over the two 66%-opacity cyan rooflight surfaces.
The composited surface is represented by `rooflight-surface: #9CC6CC`; the former pairing
measured 1.82:1 and failed normal-text contrast. The labels now use controlled dark ink,
measuring 8.04:1. Their wording, coordinates, rotation and rooflight geometry are unchanged.

### 4.2 GP05 calculation/status badges

The first contrast model exposed that a teal 10%-tint badge over an alternating evidence
row could reduce teal text to approximately 4.22:1. The final badge keeps its semantic
outline and explicit `PASS*`, `DEMAND`, `FAIL@550` or `BLOCKED` wording but uses no
translucent fill. Teal text over the darker alternating row now measures 4.81:1, and the
status remains redundant in grayscale.

### 4.3 Typed panel backgrounds

GP01–GP05 now distinguish paper headers, dark authority footers, white panels, hypothesis
panels, open-gate panels and alternating table/card surfaces in the SVG structure. These
attributes are QA evidence only: they introduce no shape, coordinate, dimension, model
status or construction authority.

## 5. Pilot baseline

| Pilot | Texts checked | Minimum contrast | Failures | Inherited colour debt |
| --- | ---: | ---: | ---: | ---: |
| GP01 ground floor | 67 | 4.78:1 | 0 | 275 literals / 88 colours |
| GP02 Side B | 37 | 4.78:1 | 0 | 36 literals / 17 colours |
| GP03 transverse section | 40 | 4.67:1 | 0 | 0 |
| GP04 P2 wall family | 96 | 4.78:1 | 0 | 0 |
| GP05 E1 synthesis | 133 | 4.78:1 | 0 | 52 literals / 9 colours |

The inherited counts are warnings, not palette failures. GP01 and GP02 remain adapters of
flat predecessor drawings, while GP05 copies calculation-linked shapes and source symbol
definitions. Canonicalising those colours belongs to controlled family migration with
geometry and grayscale review, not this editorial batch.

## 6. Reproducible command and report schema

```bash
python3 -m dreamhouse.svg.lint planos/piloto_grafico_v0.1 \
  --format markdown \
  --json-output .build/svg-lint/pilots.json \
  --markdown-output .build/svg-lint/pilots.md
```

Optional threshold controls are:

```bash
python3 -m dreamhouse.svg.lint planos/piloto_grafico_v0.1 \
  --normal-contrast 4.5 \
  --large-contrast 3 \
  --large-text-px 24 \
  --large-bold-text-px 18.66
```

Report schema version 2 records palette counts, inherited colour debt, checked/skipped
text counts, minimum contrast, failures and active threshold values. The Markdown summary
adds the minimum contrast for each file.

## 7. Automated and visual verification

Fixtures verify unapproved presentation colours, warning-only inherited colours, missing
background relationships, low contrast, configurable thresholds and deterministic output.
Theme tests verify unique six-digit uppercase values, complete shared-CSS registration and
fail-closed unknown tokens. Existing pilot tests still compare copied model geometry
attributes exactly; GP05 additionally locks the corrected rooflight/background relationship
and outline-only status badges.

All five pilots were regenerated and reviewed in colour and grayscale at 480, 800, 1,400
and 1,684 px. GP01–GP04 preserve their composition. GP05 passes with stronger rooflight
labels, clear outlined evidence statuses and unchanged seven-panel/evidence hierarchy.
Review files remain untracked under `.build/svg-pilot/`.

No decision-register or cost-control update is required. This batch adopts no graphic
system, drawing, product, quantity, scope or saving.

## 8. Next controlled batch

The next increment should implement safe sheet/panel bounds and typed collision detection.
It should begin with axis-aligned presentation text and panels, preserve explicit
text-to-marker/leader relationships and fail only on reproducible unresolved intersections.
Browser-versus-`resvg` font equivalence and the combined contact-sheet CI build remain
subsequent gates.
