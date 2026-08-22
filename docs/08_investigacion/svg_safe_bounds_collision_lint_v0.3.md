# SVG safe-bounds and collision lint v0.3 — typed pilot layout gate

**Status:** implemented for the five presentation pilots; transitional profile, not
approved for current-drawing rollout  
**Version:** 0.3  
**Date:** 2026-08-22  
**Source:** `architectural_drawing_conventions_research.md`,
`svg_drawing_system_improvement_plan.md`, `svg_static_lint_v0.1.md`,
`svg_palette_contrast_lint_v0.2.md` and GP01–GP05  
**Implementation:** `dreamhouse/svg/layout.py`, `dreamhouse/svg/lint.py` and the five
pilot generators  
**Authority boundary:** presentation-layout quality control only. This batch changes no
model geometry, design value, evidence result, scope, cost, current alias or construction
authority.

## 1. Outcome

The static SVG gate now requires every visible presentation text to declare one typed
sheet or panel region and verifies conservative axis-aligned text boxes against its safe
bounds. Text pairs within the same region must retain at least 6 sheet units of separation
or share an explicit `data-layout-relation`.

All five pilots pass with:

- 373 presentation texts assigned to explicit regions;
- 367 axis-aligned texts checked and six rotated GP05 labels explicitly deferred;
- a minimum declared pilot-panel inset of 8 sheet units;
- zero missing, malformed or inconsistent layout contracts;
- zero text boxes outside safe bounds; and
- zero untyped text collisions.

The 8-unit panel inset is a transitional pilot floor, not the 18-unit target for new
rollout templates. Applying 18 units retroactively would require a broader panel
recomposition and is therefore kept behind SVG-G1/SVG-G2 review. Passing this profile
does not promote any pilot into `planos/actual/` and does not pass SVG-G0, SVG-G1 or
SVG-G2.

## 2. Typed region contract

`dreamhouse/svg/layout.py` defines validated `Bounds` and `LayoutRegion` values. During
generation, every presentation text receives:

- `data-layout-region`: stable sheet-local region identity;
- `data-layout-kind`: panel, sheet header or sheet footer;
- `data-panel-bounds`: declared panel rectangle; and
- `data-safe-bounds`: rectangle within which the estimated text box must remain.

Copied model text and text inside SVG definitions are excluded so the presentation
adapter cannot silently reinterpret model geometry. Header and footer regions are shared
across the five generators. Family-specific regions map the existing visible panels
without creating new shapes or altering copied source coordinates.

Rotated presentation text must declare `data-layout-policy="rotated-skip"`. Six GP05 plan
labels use this explicit staged exception. An untyped transform fails closed; the
exception is counted in the report and is not presented as a successful bounds check.

## 3. Conservative text-box and collision profile

The checker estimates deterministic Inter-like text advances without depending on an
installed host font. It accounts for:

- explicit font size, start/middle/end anchoring and multiline `tspan` baselines;
- character-class width factors and computed letter spacing;
- bold-width allowance; and
- half of the computed text stroke as a paint halo.

The default pilot profile uses an 8-unit panel inset, a 6-unit text gap and a 0.5-unit
box tolerance. Two estimated boxes collide when their gap-expanded rectangles intersect
inside the same region. A deliberate composite may pass only when both elements share
the same non-empty `data-layout-relation`; the report counts that exception. GP01–GP05
currently require no such exceptions.

The new fail-closed findings are:

- `SVG-B001`: missing, malformed or unsupported text-layout contract;
- `SVG-B002`: inconsistent region declarations or an insufficient panel inset;
- `SVG-B003`: estimated axis-aligned text box outside its safe bounds; and
- `SVG-B004`: text pair breaching the minimum gap without a shared typed relation.

This is not yet a measured browser text box, rotated-box or text-to-geometry collision
gate. Those boundaries remain explicit to prevent a heuristic from being described as
complete geometric authority.

## 4. Defects found and corrected

### 4.1 GP03 vertical-reading note

The two-line explanatory note ended fractionally below the vertical-reading safe area.
Its baseline moved from 986 to 985 sheet units. Wording, wrapping, status and source
section geometry are unchanged.

### 4.2 GP04 redundant P2-W01B key

The final numbered key and the explanatory note fell just inside the 6-unit paint-halo
gap. P2-W01B key spacing changed from 26 to 25.6 units and the note baseline from 988 to
989. All seven layers, numbers and material descriptions remain visible and in source
order.

### 4.3 GP05 dense plan and detail panels

The checker exposed three tight reading zones. The six 6.00 m bay labels moved from 588
to 581 and the 36.00 m overall label from 606 to 599, retaining their sequence below the
plan. The foundation evidence baseline changed from 798 to 797.5. The erection note moved
from 982 to 980, while the erection and fire blocked baselines moved from 1000 to 997.
These are presentation-text adjustments only; calculation-linked shapes, values,
evidence outcomes and blocked design status are unchanged.

## 5. Pilot baseline

| Pilot | Presentation texts | Axis-aligned checked | Rotated deferred | Safe-bound failures | Untyped collisions |
| --- | ---: | ---: | ---: | ---: | ---: |
| GP01 ground floor | 67 | 67 | 0 | 0 | 0 |
| GP02 Side B | 37 | 37 | 0 | 0 | 0 |
| GP03 transverse section | 40 | 40 | 0 | 0 | 0 |
| GP04 P2 wall family | 96 | 96 | 0 | 0 | 0 |
| GP05 E1 synthesis | 133 | 127 | 6 | 0 | 0 |

## 6. Reproducible command and report schema

```bash
python3 -m dreamhouse.svg.lint planos/piloto_grafico_v0.1 \
  --format markdown \
  --json-output .build/svg-lint/pilots.json \
  --markdown-output .build/svg-lint/pilots.md
```

The new profile controls are:

```bash
python3 -m dreamhouse.svg.lint planos/piloto_grafico_v0.1 \
  --min-panel-inset 8 \
  --min-text-gap 6 \
  --bounds-tolerance 0.5
```

Report schema version 3 records assigned and checked text counts, rotated deferrals,
contract failures, minimum declared panel inset, safe-bound failures, typed exceptions,
untyped collisions and the active threshold values. The Markdown summary adds one
`Bounds / collisions` column.

## 7. Automated and visual verification

Fixtures verify bounds validation and serialization, anchor and multiline estimates,
model-text exclusion, explicit rotated-text policy, missing contracts, out-of-bounds text,
untyped collisions and shared typed relationships. Existing pilot tests still compare
copied model geometry attributes exactly.

All five pilots were regenerated and rendered in colour and grayscale at 480, 800, 1,400
and 1,684 px. The corrected GP03–GP05 areas remain legible at 1,400 px, panel hierarchy
remains clear in grayscale, and no footer or open/conflict status is clipped. Review files
remain untracked under `.build/svg-pilot/v03/`.

No decision-register or cost-control update is required. This batch adopts no graphic
system, drawing, product, quantity, scope, saving or cost.

## 8. Next controlled batch

The next increment should extend collision QA from presentation text-to-text pairs to
typed text-to-marker, leader and geometry relationships, beginning with the five pilots.
Measured browser/`resvg` font equivalence, the 18-unit new-template profile and the
combined 27-sheet contact-sheet CI build remain subsequent gates.
