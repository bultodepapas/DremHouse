# SVG browser–resvg render equivalence v0.5 — measured pilot evidence

**Status:** implemented for the five presentation pilots; local fail-closed profile, not
approved for current-drawing rollout

**Version:** 0.5

**Date:** 2026-08-22

**Source:** `architectural_drawing_conventions_research.md`,
`svg_drawing_system_improvement_plan.md`, `svg_static_lint_v0.1.md`,
`svg_safe_bounds_collision_lint_v0.3.md`, `svg_text_geometry_collision_lint_v0.4.md`
and GP01–GP05

**Implementation:** `dreamhouse/svg/render_equivalence.py`

**Authority boundary:** presentation-render verification only. This batch changes no
model geometry, design value, evidence result, scope, cost, current alias or construction
authority.

## 1. Outcome

The five pilots now pass a measured Chrome/`resvg` equivalence profile. The tool renders
each explicit SVG text line and each registered editorial primitive with a unique probe
colour at 2× native resolution, recovers its actual paint box in each engine and compares
the four box edges.

The final run measured:

- 533 visual line runs from 492 visible text elements;
- all 373 text elements covered by the axis-aligned layout contract;
- 62 registered editorial primitives;
- zero missing browser or `resvg` lines;
- zero text-line box mismatches beyond the 5 px probe tolerance;
- zero geometry box mismatches beyond the 2 px probe tolerance; and
- zero untyped measured layout collisions in either engine.

The maximum observed text-edge delta is 5 px at 2×, equivalent to 2.5 sheet user units.
The maximum geometry-edge delta is 2 px at 2×, equivalent to one user unit. The 18
intentional GP05 badge text/marker intersections retain their exact typed relationships
in both engines.

## 2. Fail-closed render contract

The profile requires all of the following:

1. Chrome or Chromium must be available locally or passed with `--browser`;
2. the primary `Inter` family must resolve through the host font configuration;
3. browser and `resvg` probe images must have identical 2× pixel dimensions;
4. every logical line and registered primitive must produce an identifiable paint box in
   both engines;
5. corresponding text edges may differ by no more than 5 px at 2×;
6. corresponding editorial-geometry edges may differ by no more than 2 px at 2×; and
7. renderer-measured text/text and text/geometry boxes must retain the v0.3/v0.4 typed
   6-unit and 3-unit clearance contracts.

The 5 px text limit is smaller than half of the 6-unit text-gap requirement when measured
at 2×. The 2 px geometry limit is similarly smaller than half of the 3-unit geometry gap.
The limits admit ordinary glyph rasterisation differences without allowing an engine
change to consume the full static-layout clearance.

Missing fonts, missing colours, missing elements, malformed canvas sizes, browser
failure, image-size disagreement, excessive edge deltas or untyped measured collisions
all fail the command. No browser package was added to the project dependencies: the tool
discovers an existing Chrome/Chromium executable or accepts one explicitly.

## 3. Probe method

### 3.1 Text-line probe

Non-text paint is removed from a temporary SVG copy. Every single-line text element or
direct multiline `tspan` receives one of 511 deterministic, separated colours. Rendering
at 2× ensures even the inherited 6.8-unit microtext retains solid probe pixels.

The comparison is per explicit line, not only per parent text box. This means a changed
line baseline, horizontal extent, anchor or font metric is measured independently. A
small remote exact-colour cluster may arise from antialias blending between other probe
colours; the decoder removes only negligible clusters separated by more than 32 px while
retaining material word or glyph groups. Unit fixtures lock this behaviour.

### 3.2 Editorial-geometry probe

The second probe retains only the 62 primitives explicitly registered by v0.4. It uses
the same colour and paint-box recovery method for keepouts, leaders and markers. Copied
technical model geometry remains outside this editorial-geometry claim.

### 3.3 Measured clearance replay

Recovered line boxes are reunited by parent text. The tool then replays the same-region
text/text and text/geometry gap rules separately for Chrome and `resvg`. Exact matching
relations remain the only way to accept an intentional marker or leader intersection;
keepout rules cannot bypass the clearance.

The six rotated GP05 labels remain explicitly tagged `rotated-skip`. They are measured for
cross-engine paint-box equivalence, but they do not enter the axis-aligned collision
replay. This preserves the declared v0.3/v0.4 boundary instead of silently claiming a
transform-aware collision result.

## 4. Pilot results

| Pilot | Text | Lines | Multi | Text Δ px | Geom. | Geom. Δ px | Untyped B / R |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GP01 ground floor | 154 | 175 | 15 | 5 | 8 | 0 | 0 / 0 |
| GP02 Side B | 52 | 54 | 1 | 2 | 1 | 0 | 0 / 0 |
| GP03 transverse section | 45 | 49 | 4 | 4 | 5 | 2 | 0 / 0 |
| GP04 P2 wall family | 108 | 116 | 5 | 2 | 16 | 1 | 0 / 0 |
| GP05 E1 synthesis | 133 | 139 | 1 | 4 | 32 | 1 | 0 / 0 |
| **Total / maximum** | **492** | **533** | **26** | **5** | **62** | **2** | **0 / 0** |

The collision column reports Chrome / `resvg`. GP05 additionally reports six rotated
lines measured for equivalence and skipped by the collision replay, plus 18 typed
text/marker intersections accepted in both engines.

## 5. Reproducible command and environment

```bash
python3 -m dreamhouse.svg.render_equivalence \
  planos/piloto_grafico_v0.1 \
  --output-dir .build/svg-render-equivalence/v05 \
  --browser /path/to/chrome
```

The accepted local run used:

- Google Chrome for Testing 152.0.7977.42;
- `resvg-py` 0.4.0;
- Pillow 11.3.0; and
- system-resolved `Inter-Regular.otf` from `/usr/share/fonts/opentype/inter/`.

Omitting `--browser` activates discovery for normal Chrome/Chromium commands and existing
Puppeteer or Playwright browser caches. The JSON schema version 1 report records the
resolved executable, browser and library versions, font path, thresholds, file metrics
and largest observed deltas.

## 6. Full-render visual review

The tool also writes native-size Chrome, `resvg` and amplified difference images for each
pilot. Full-raster differences are diagnostic rather than pass/fail because browser and
`resvg` use different antialiasing for glyphs, thin rules and hatches.

| Pilot | Mean absolute channel delta | Pixels with any channel Δ > 16 |
| --- | ---: | ---: |
| GP01 | 2.4925 | 5.1479% |
| GP02 | 1.7387 | 4.2853% |
| GP03 | 1.4654 | 3.2115% |
| GP04 | 4.2286 | 7.8847% |
| GP05 | 2.2953 | 4.8280% |

The larger GP04 diagnostic percentage follows its dense hatch fields. Side-by-side
review confirms the same text lines, panel hierarchy, dimensions, status distinctions,
geometry extents and clipping state in both engines. No pilot SVG required an editorial
or technical change. Review files remain untracked under
`.build/svg-render-equivalence/v05/`.

## 7. Automated verification and limits

Eight new fixtures cover colour uniqueness, explicit `tspan` lines, geometry isolation,
paint-box recovery, remote blend-noise rejection, fail-closed deltas, typed measured
clearance, primary-font failure and browser-path resolution. The SVG-specific suite
contains 67 passing tests; the repository suite contains 301 passing tests.

This is local cross-engine evidence, not yet a CI browser job. It does not establish
cross-platform equivalence for hosts without Inter, does not cover automatic HTML/CSS
text wrapping and does not extend static layout authority to transformed text or paths.
The SVG pilots use explicit `tspan` lines, so automatic wrapping is intentionally absent.

No decision-register or cost-control update is required. This batch adopts no graphic
system, drawing, product, quantity, scope, saving or cost.

## 8. Next controlled batch

The next increment should replace the six `rotated-skip` declarations with measured,
transform-aware text boxes and then extend registered geometry to controlled transforms
and paths. The 18-unit new-template profile and combined 27-sheet contact-sheet CI build
remain subsequent gates.
