# SVG rotated-text bounds v0.6 — transform-aware pilot layout

**Status:** implemented for the five presentation pilots; transitional profile, not
approved for current-drawing rollout

**Version:** 0.6

**Date:** 2026-08-22

**Source:** `architectural_drawing_conventions_research.md`,
`svg_drawing_system_improvement_plan.md`, `svg_safe_bounds_collision_lint_v0.3.md`,
`svg_text_geometry_collision_lint_v0.4.md`,
`svg_browser_resvg_equivalence_v0.5.md` and GP01–GP05

**Implementation:** `dreamhouse/svg/layout.py`, `dreamhouse/svg/lint.py`,
`dreamhouse/svg/render_equivalence.py` and `dreamhouse/svg/pilot_e1_synthesis.py`

**Authority boundary:** presentation-layout quality control only. This batch changes no
model geometry, design value, evidence result, scope, cost, current alias or construction
authority.

## 1. Outcome

The six vertical GP05 labels now enter the same safe-bound, text-to-text and
text-to-geometry checks as every other presentation label. Their former
`rotated-skip` declarations have been replaced by `rotated-measured`, leaving no
presentation text outside the layout gate.

The final static run covers:

- 373 presentation text elements: 367 axis-aligned and six rotated;
- all 62 registered editorial primitives from v0.4;
- zero safe-bound failures;
- zero untyped text-to-text collisions; and
- zero untyped text-to-geometry collisions.

All five pilots pass the required checks. Eleven inherited-model warnings remain: three
lineweight-policy warnings, three colour-debt warnings, four source-precision warnings
and one inherited-microtext warning. They predate this increment and remain visible
rather than being suppressed.

## 2. Strict rotation contract

Presentation text may use either no transform or exactly one explicit
`rotate(angle cx cy)` transform. Spaces or commas may separate the three finite numeric
arguments. A missing pivot, a second transform, `translate`, `scale`, `skew`, `matrix`,
invalid syntax or a non-finite value fails closed.

Registration assigns `data-layout-policy="rotated-measured"` only after the transform
passes this parser. Untransformed text may not retain a layout-policy declaration. This
makes the measured claim explicit in the generated SVG and prevents a future composite
transform from being treated as if its bounds were understood.

For each explicit text line, the existing conservative ink-and-halo rectangle is
calculated first. All four corners are then rotated about the declared pivot using the
standard SVG rotation matrix. The axis-aligned union of those transformed corners enters
the region, clearance and collision checks. Multiline text retains one transformed box
per explicit line before the parent union is calculated.

This batch does not extend the contract to transformed registered geometry or SVG
paths. Those inputs continue to fail closed.

## 3. Findings and limited drawing correction

Activating the six boxes exposed two previously deferred GP05 annotation contacts:

1. vertical `RL-RC` against `DIAPHRAGM DEMAND · 8.77 kN/m`; and
2. the demand label against vertical `EDGE · X=21`.

Only annotation coordinates were corrected:

| Annotation | Before | After | Purpose |
| --- | ---: | ---: | --- |
| `RL-RC` baseline | `y=372` | `y=382` | separate the vertical label from the demand label |
| diaphragm-demand centre | `x=496` | `x=466` | restore the renderer-measured 6-unit text gap to `EDGE` |

The first demand-label move to `x=470` passed the conservative static estimate but the
actual Chrome and `resvg` ink boxes still left less than the required gap. The final
4-unit move to `x=466` passes both engines. No technical path, source-model coordinate,
load, dimension, status or evidence value changed.

## 4. Browser and resvg verification

The v0.5 paint-box replay now includes rotated parents and fails if any
`rotated-skip` line remains. Report schema version 2 exposes measured and skipped counts
separately.

The final 2× run produced:

| Check | Result |
| --- | ---: |
| Explicit text lines | 533 |
| Rotated text lines measured / skipped | 6 / 0 |
| Registered editorial primitives | 62 |
| Text-line mismatches above 5 px | 0 |
| Geometry mismatches above 2 px | 0 |
| Maximum text / geometry edge delta | 5 px / 2 px |
| Chrome untyped layout collisions | 0 |
| `resvg` untyped layout collisions | 0 |
| Files passed | 5 / 5 |

`Inter` resolved to the required system family. The accepted environment used Google
Chrome for Testing 152.0.7977.42, `resvg-py` 0.4.0 and Pillow 11.3.0.

## 5. Visual review and determinism

The final native-size GP05 Chrome image and the Chrome/`resvg` comparison were reviewed.
The demand annotation reads continuously above its leader, clears both vertical labels
and remains associated with the same diaphragm arrow. `RL-RC` remains centred inside its
cyan bay. The roof plan, seven-panel hierarchy, evidence matrix and fail-closed authority
band remain legible and unchanged.

Against the v0.5 renders, GP01–GP04 are pixel-identical in both engines. GP05 changes are
confined to the annotation area: browser difference bounds `(376, 346)–(588, 397)` and
`resvg` bounds `(377, 348)–(585, 397)` at native resolution. Regenerating all five pilots
modifies only the GP05 SVG and its own manifest.

Repeatable evidence remains untracked under:

- `.build/svg-lint/pilots-v06.json` and `.build/svg-lint/pilots-v06.md`; and
- `.build/svg-render-equivalence/v06/`.

## 6. Automated verification and limits

Two new fixtures cover rotation parsing/bounds and fail-closed transform handling. The
SVG-specific suite contains 69 passing tests; the repository suite contains 303 passing
tests. Generated SVG output was regenerated from its source before both suites ran.

This is still a local browser verification step, not a browser CI job. It validates the
current explicit `rotate(angle cx cy)` vocabulary, not arbitrary SVG transform lists,
transformed registered geometry, path bounds or automatic HTML/CSS wrapping. The
8-unit pilot panel inset remains transitional; it does not adopt the proposed 18-unit
new-template target.

No decision-register or cost-control update is required. The batch adopts no graphic
system, drawing, product, quantity, scope, saving or cost.

## 7. Next controlled batch

The next increment should add measured, fixture-backed support for the controlled
transforms and paths actually needed by registered editorial geometry. The 18-unit
new-template profile and combined 27-sheet contact-sheet CI build remain subsequent
gates.
