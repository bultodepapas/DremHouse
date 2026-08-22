# SVG text-to-geometry collision lint v0.4 — registered editorial primitives

**Status:** implemented for the five presentation pilots; transitional profile, not
approved for current-drawing rollout

**Version:** 0.4

**Date:** 2026-08-22

**Source:** `architectural_drawing_conventions_research.md`,
`svg_drawing_system_improvement_plan.md`, `svg_static_lint_v0.1.md`,
`svg_palette_contrast_lint_v0.2.md`, `svg_safe_bounds_collision_lint_v0.3.md` and
GP01–GP05

**Implementation:** `dreamhouse/svg/layout.py`, `dreamhouse/svg/lint.py`,
`dreamhouse/svg/sheet.py` and the five pilot generators

**Authority boundary:** presentation-layout quality control only. This batch changes no
model geometry, design value, evidence result, scope, cost, current alias or construction
authority.

## 1. Outcome

The static SVG gate now checks presentation text against explicitly registered editorial
geometry. The five pilots declare 62 primitives:

- 20 `keepout` rules that text must clear;
- 40 `marker` primitives with typed text relationships; and
- two `leader` lines with typed level-label relationships.

All five pilots pass with zero missing or malformed geometry contracts, zero dangling
relationships and zero untyped text-to-geometry collisions. Eighteen deliberate GP05
badge-label overlaps are accepted only because each badge outline and its text share one
explicit relationship.

The implementation deliberately does not register copied model geometry. It therefore
does not claim that every model line, hatch, symbol or technical shape has passed a
collision test. Passing this profile does not promote any pilot into `planos/actual/` and
does not pass SVG-G0, SVG-G1 or SVG-G2.

## 2. Registered editorial-geometry contract

An editorial primitive enters the gate only when it declares
`data-layout-geometry="keepout|leader|marker"`. Generation assigns its smallest containing
`data-layout-region` from the same region registry used for text.

The roles have distinct semantics:

- `keepout`: a rule or separator that no text box may enter;
- `leader`: a reference line that requires a same-region text target; and
- `marker`: a swatch, arrowhead or badge outline that requires a same-region text target.

Every leader and marker requires a non-empty `data-layout-relation`. Its related text must
carry the identical value in the same region. A spatial overlap is permitted only when
those values match. A keepout cannot use a relationship to bypass the required gap.

The generator rejects registered geometry inside `layer-model` or `defs`. This preserves
the graphic-only boundary: source model shapes remain evidence to be protected and are
not silently reclassified as editorial markers.

## 3. Conservative primitive bounds

The profile computes axis-aligned paint boxes for untransformed:

- lines;
- rectangles;
- circles and ellipses; and
- polylines and polygons.

The bounds include the resolved stroke halo. Registered paths, transformed primitives,
invalid dimensions and non-finite coordinates fail closed as unsupported contracts. They
may be added only through a later measured and tested profile.

Text must retain a 3-unit gap from registered geometry. This is intentionally smaller
than the 6-unit text-to-text gap because leader and marker systems need compact but
legible proximity. Existing 8-unit pilot panel insets and the 0.5-unit safe-bound
tolerance remain unchanged.

The new findings are:

- `SVG-B005`: registered geometry has a missing, malformed or unsupported contract;
- `SVG-B006`: leader or marker has no same-region text target; and
- `SVG-B007`: text breaches the geometry gap without a matching typed relationship.

## 4. Registered pilot coverage

| Pilot | Geometry | Keepouts | Typed leaders/markers | Typed overlaps | Untyped collisions |
| --- | ---: | ---: | ---: | ---: | ---: |
| GP01 ground floor | 8 | 4 | 4 | 0 | 0 |
| GP02 Side B | 1 | 1 | 0 | 0 | 0 |
| GP03 transverse section | 5 | 1 | 4 | 0 | 0 |
| GP04 P2 wall family | 16 | 6 | 10 | 0 | 0 |
| GP05 E1 synthesis | 32 | 8 | 24 | 18 | 0 |
| **Total** | **62** | **20** | **42** | **18** | **0** |

Coverage includes shared header rules, GP01 programme swatches, GP03 level leaders and
arrowheads, GP04 material-key swatches, GP04/GP05 panel-heading rules, GP05 graphic-status
markers and GP05 evidence badges.

Background panels, card surfaces and technical model geometry are not obstacles in this
staged profile. Text intentionally belongs inside those surfaces; registering them as
keepouts would produce false failures.

## 5. Defects found and corrected

The first v0.4 pass found two GP05 labels fractionally inside the 3-unit heading-rule gap:

- `≈ HEA200` in panel 05 moved from baseline 680 to 681; and
- `HOOK 15.8 kN` in panel 06 moved from baseline 885 to 886.

The one-unit adjustments leave every value and technical shape unchanged. No other pilot
required a positional correction.

## 6. Reproducible command and report schema

```bash
python3 -m dreamhouse.svg.lint planos/piloto_grafico_v0.1 \
  --format markdown \
  --json-output .build/svg-lint/pilots.json \
  --markdown-output .build/svg-lint/pilots.md \
  --min-geometry-gap 3
```

Report schema version 4 records registered geometry, keepout and relationship counts,
contract failures, dangling relationships, typed overlaps, untyped text-to-geometry
collisions and the active 3-unit threshold. The Markdown summary now reports
`Bounds / text / geometry` failures.

## 7. Automated and visual verification

Fixtures verify primitive bounds, unsupported paths, region registration, required
leader/marker relationships, missing contracts, dangling targets, keepout collisions and
typed marker overlaps. The SVG-specific suite contains 59 passing tests; the repository
suite contains 293 passing tests and continues to lock copied model geometry and technical
values.

All five pilots were regenerated and rendered in colour and grayscale at 480, 800, 1,400
and 1,684 px. At 1,400 px, GP01–GP04 are pixel-identical to v0.3. GP05 changes 493 pixels
within the two adjusted label zones only; both labels remain clear in colour and
grayscale. Review files remain untracked under `.build/svg-pilot/v04/`.

No decision-register or cost-control update is required. This batch adopts no graphic
system, drawing, product, quantity, scope, saving or cost.

## 8. Next controlled batch

Browser-versus-`resvg` text, line and registered-geometry equivalence was subsequently
measured in
[`svg_browser_resvg_equivalence_v0.5.md`](svg_browser_resvg_equivalence_v0.5.md). Rotated
text, transformed/path geometry, the 18-unit new-template profile and the combined
27-sheet contact-sheet CI build remain subsequent gates.
