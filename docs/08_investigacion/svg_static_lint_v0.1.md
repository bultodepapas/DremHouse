# SVG static lint v0.1 — pilot fail-closed gate

**Status:** implemented for the five presentation pilots; not approved for current-drawing
rollout  
**Version:** 0.1  
**Date:** 2026-08-22  
**Source:** `svg_drawing_system_improvement_plan.md`,
`architectural_drawing_conventions_research.md` and GP01–GP05  
**Implementation:** `dreamhouse/svg/lint.py`  
**Authority boundary:** quality-control infrastructure only. This gate changes no model
geometry, design decision, scope, cost, current alias or construction authority.

## 1. Outcome

`python3 -m dreamhouse.svg.lint` now provides one deterministic, fail-closed static check
for SVG publication candidates. It emits human-readable Markdown or machine-readable JSON
and returns a non-zero process status when any required rule fails.

The first profile passes all five presentation pilots with zero errors. GP04 passes with
no findings; GP01, GP02, GP03 and GP05 retain explicit warnings for inherited numeric,
lineweight or microtext debt. Warnings are visible without falsely blocking the pilot
baseline, and CI may promote them to failures with `--warnings-as-errors`.

This result does not pass SVG-G0, SVG-G1 or SVG-G2 and does not promote a pilot into
`planos/actual/`.

## 2. Implemented checks

The v0.1 profile checks:

- valid XML, the SVG namespace, positive `width`/`height` and a finite `viewBox`;
- accessible `role="img"`, exactly referenced title/description IDs and non-empty
  accessible text;
- unique IDs and one structured metadata object with sheet, revision, source, status and
  `construction_authority: false`;
- agreement between metadata and root sheet/revision fields plus an explicit root status
  and non-construction authority;
- absence of scripts, `foreignObject`, event handlers, external links, external CSS/images
  and unsafe `url(...)` references;
- an embedded font-family declaration and an explicit lineweight/profile rule;
- the four direct semantic layers: background, model, annotations and sheet;
- stable `data-model-id` references on every direct model node;
- non-finite numbers as errors, and scientific notation or precision beyond six decimals
  as configurable warnings/errors;
- explicit font sizes and effective text size at a 1,400 px publication width; and
- required-role and sheet/evidence text below 8 px as errors, while inherited model
  microtext remains a quantified warning.

Finding codes are grouped by concern: `SVG-X` parsing, `SVG-R` root geometry, `SVG-A`
accessibility, `SVG-I` identity, `SVG-M` metadata, `SVG-S` security, `SVG-P` presentation,
`SVG-L` layers/model references, `SVG-N` numbers and `SVG-T` text.

## 3. Deliberate v0.1 boundary

The following controls from the complete improvement plan remain follow-on gates and are
not claimed by this implementation:

- approved palette/theme-token validation;
- computed foreground/background contrast;
- visible content and text bounds against sheet and panel safe areas;
- typed text/geometry collision detection;
- separate approximately 9 px thresholds for critical roles;
- browser-versus-`resvg` font and line-break equivalence;
- geometry baselines for drawing families beyond the five pilot-specific tests; and
- the 27-sheet contact-sheet and visual-difference CI build.

This staged boundary keeps the first gate auditable and avoids presenting a partial
geometric heuristic as a complete collision or bounds authority.

## 4. Reproducible commands and process status

Run the pilot profile from the repository root:

```bash
python3 -m dreamhouse.svg.lint planos/piloto_grafico_v0.1 \
  --format markdown \
  --json-output .build/svg-lint/pilots.json \
  --markdown-output .build/svg-lint/pilots.md
```

Use strict canonical-number enforcement or treat every warning as a CI failure:

```bash
python3 -m dreamhouse.svg.lint planos/piloto_grafico_v0.1 --strict-precision
python3 -m dreamhouse.svg.lint planos/piloto_grafico_v0.1 --warnings-as-errors
```

The ordinary profile returns `0` when there are no errors and `1` when any error exists.
`--warnings-as-errors` also returns `1` for a warning-only report. JSON has a stable
`schema_version`, profile, aggregate summary, per-file metrics and ordered findings.

## 5. Five-pilot baseline

| Pilot | Result | Errors | Warnings | Minimum text | Required below 8 px |
| --- | --- | ---: | ---: | ---: | ---: |
| GP01 ground floor | WARN | 0 | 3 | 4.59 px | 0 |
| GP02 Side B | WARN | 0 | 2 | 8.15 px | 0 |
| GP03 transverse section | WARN | 0 | 2 | 8.15 px | 0 |
| GP04 P2 wall family | PASS | 0 | 0 | 8.06 px | 0 |
| GP05 E1 synthesis | WARN | 0 | 1 | 8.15 px | 0 |

GP01's 4.59 px minimum belongs to 42 retained source-model microtexts, not required or
sheet/evidence roles. They are reported by `SVG-T004` and remain zoom content. The GP01
generator now assigns a stable reference to every one of its 244 copied direct model
nodes. Six non-model labels initially failed at 7.98 px; increasing only those labels from
9.6 to 9.7 sheet units cleared the required 8 px floor without changing geometry or
composition.

The other baseline warnings are:

- `SVG-P003`: GP01–GP03 use a scaled model group without an explicit non-scaling-stroke
  policy; and
- `SVG-N003`: GP01, GP02, GP03 and GP05 retain long floating-point artefacts inherited
  from their source or pilot calculations.

These warnings identify migration work. They are not silently normalised in this batch
because numeric rewriting and lineweight policy require their own geometry/presentation
regression checks.

## 6. Automated and visual verification

The test suite includes complete and malformed fixtures. It verifies all five pilot files,
parse failure, duplicate IDs, executable/foreign content, event handlers, external
resources, undersized required and microtext roles, non-finite values, configurable strict
precision, deterministic reports and warning-to-error CI behaviour.

GP01 was regenerated and reviewed after the six-label correction at 1,400 px, 800 px and
in grayscale. The reading-hierarchy swatches and explanatory line remain separated, the
sidebar introduction remains inside its panel and the model composition is unchanged.
The repeatable review files remain untracked under `.build/svg-pilot/gp01/`.

No decision-register or cost-control update is required. The batch adds a verification
tool and metadata hardening only; it adopts no graphic system, drawing, quantity, scope or
cost.

## 7. Next controlled batch

The planned palette/contrast increment was subsequently implemented as
[`svg_palette_contrast_lint_v0.2.md`](svg_palette_contrast_lint_v0.2.md). Bounds and typed-
collision checks remain the next separate geometric batch so their tolerances and
exceptions remain reviewable.
