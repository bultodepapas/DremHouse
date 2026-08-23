# SVG pilot contact audit v0.7 — reduced-set visual QA

**Status:** implemented locally for the five presentation pilots; not yet a current-set
or CI acceptance gate

**Version:** 0.7

**Date:** 2026-08-23

**Source:** `architectural_drawing_conventions_research.md`,
`svg_drawing_system_improvement_plan.md`, `svg_browser_resvg_equivalence_v0.5.md`,
`svg_rotated_text_bounds_v0.6.md` and GP01–GP05

**Implementation:** `dreamhouse/svg/audit.py`,
`.github/scripts/build_svg_audit.py` and `dreamhouse/svg/tests/test_audit.py`

**Authority boundary:** visual-review evidence only. This batch changes no pilot or
current SVG, model geometry, design value, evidence result, scope, cost, current alias or
construction authority.

## 1. Outcome

One command now produces a coordinated visual-audit set for GP01–GP05:

- colour and grayscale PNGs for every pilot at 480, 800 and 1,400 px width;
- one labelled 480 px-per-sheet colour contact sheet;
- one equivalent grayscale contact sheet; and
- one deterministic JSON report with identity, input SHA-256 and text-size metrics.

The contact builder orders inputs by declared revision, so the visual reading is always
GP01 → GP05 even though the filenames sort by discipline and sheet number. All generated
evidence stays under `.build/`; no review raster is promoted or tracked as a drawing.

## 2. Scope decision after the v0.6 inventory

The next item recorded by v0.6 was controlled support for transformed or path-based
registered editorial geometry. A structural inventory of the five generated pilots found
zero such elements outside `defs` and `layer-model`. All 62 currently registered
editorial primitives already use the supported untransformed line, rectangle, circle,
ellipse, polyline or polygon vocabulary.

Adding transform/path logic now would therefore create speculative support without a
real pilot consumer or renderer comparison. The existing linter remains deliberately
fail-closed for those inputs. The batch instead advances the next evidenced requirement:
R16 and improvement-plan §9.3 reduced contact review. Path/transform support should be
added only when a real editorial primitive requires it and can provide an integration
fixture.

## 3. Collection contract

The collection mode requires explicit existing `.svg` inputs, rejects duplicates and
requires positive, unique render widths. It reads each SVG title, revision and status,
sorts by revision, and records the exact input hash.

Each contact cell contains:

1. the accessible SVG title;
2. revision plus document status; and
3. the full reduced sheet image.

The contact-sheet header states `REVIEW EVIDENCE ONLY`. The source SVGs retain their own
`NOT CURRENT` and `NOT FOR CONSTRUCTION` declarations. The tool does not infer approval,
promotion or design authority from visual quality.

The legacy single-pilot `--before` / `--after` mode remains available. Collection mode
is additive and uses the same `resvg-py` rendering path as the earlier pilot reviews.

## 4. Reproducible command and outputs

```bash
python3 .github/scripts/build_svg_audit.py \
  --paths planos/piloto_grafico_v0.1/*.svg \
  --output-dir .build/svg-audit/v07 \
  --prefix pilots-v07
```

The command writes 30 individual renders, two contact sheets and one metrics report. The
final contact sheets are 1,008 × 1,294 px with two columns and 480 px-wide sheet images.
Running the complete command twice produced byte-identical outputs.

## 5. Metrics and visual review

The consolidated 1,400 px metrics report contains:

| Metric | Result |
| --- | ---: |
| Pilot SVGs | 5 |
| Visible text elements, including inherited model text | 492 |
| Effective text below 7 px | 42 |
| Effective text below 8 px | 42 |
| Effective text below 9 px | 413 |
| Minimum effective text | 4.59 px |

All 42 sub-8 px elements are the already reported inherited GP01 model microtexts. The
other four pilots have no visible text below 8 px; their minimums are 8.06–8.15 px. The
413 sub-9 px elements include ordinary pilot body roles intentionally set at the common
8.06–8.15 px preview floor and do not represent a new failure.

### 5.1 Colour contact sheet

The five sheets read as one family while retaining distinct view types. GP01 remains the
densest but its plan, keyed sidebar and authority footer are recognisable. GP02 and GP03
retain clear primary elevations/sections despite their sparse fields. GP04 preserves the
build-up/schedule split. GP05 preserves the plan, evidence matrix, reference truss and
four secondary evidence panels.

### 5.2 Grayscale contact sheet

Titles, primary geometry, panel hierarchy and dark authority bands remain recognisable
without colour. GP04 material distinctions retain pattern boundaries; GP05 statuses
retain badge shapes and wording; no open or blocked state depends on hue alone.

No drawing correction was required. The batch creates a coordinated overview, not a new
claim that detailed notes are readable at 480 px: that size is explicitly a navigation
and hierarchy check.

## 6. Regression evidence and limits

The unchanged pilot set retains:

- static SVG lint: five files, zero errors, zero safe-bound or collision failures and 11
  inherited warnings;
- Chrome/`resvg`: 533 text lines, six rotated lines measured, 62 registered primitives,
  zero mismatches beyond tolerance and zero untyped collisions in either engine;
- SVG-specific tests: 72 passing; and
- repository tests: 306 passing.

Three new fixtures cover ordered multi-scale/contact output, deterministic JSON and
hashing, plus fail-closed empty, duplicate, missing and invalid-width inputs.

This remains a five-pilot local build. It does not yet create family-separated contact
sheets for all 27 current identities, publish CI artifacts, compare current sources to
new issues, or replace manual visual judgement. The audit render uses `resvg`; the
separate v0.5/v0.6 profile remains the cross-engine control.

No decision-register or cost-control update is required. The batch adopts no graphic
system, drawing, product, quantity, scope, saving or cost.

## 7. Next controlled batch

The next small increment should measure the proposed 18-unit new-template safe inset
against GP01–GP05 as an opt-in profile, report every required relocation and avoid
silently rewriting the transitional 8-unit layouts. Once that profile is understood, the
contact builder can expand to family-labelled coverage of all 27 current identities and
CI artifact publication.
