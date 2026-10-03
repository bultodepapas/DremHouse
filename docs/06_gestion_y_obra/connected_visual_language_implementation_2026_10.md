# Connected visual-language implementation

**Version:** 0.1  
**Date:** 2026-10-03  
**Status:** implemented connected-review delivery; extended visual acceptance remains open  
**Source:** D-085; [visual audit and phased plan](../08_investigacion/connected_svg_visual_language_audit_and_plan_2026_10.md); generated review evidence.  
**Authority:** graphic/software change only; generated review, not construction acceptance.

## Scope

The implementation follows the researched warm technical atlas direction through the
existing generators. It preserves the physical model, quantities, source identities,
findings and historical drawing lineage. SVGs remain output artifacts.

## Delivery components

- Portable SVG styles resolve supported custom-property colour references before export.
  Unknown or unsupported style expressions fail explicitly. The raster boundary rejects
  uncompiled variables rather than silently producing black content.
- Check-result and selection roles are independent from material roles. Cobalt identifies
  focus/selection; OPEN and study retain separate wording and symbols.
- Coordination projections and native architectural/discipline consumers retain their
  separate representation purposes, with local graphic keys and clearer presentation.
- The connected reader pairs architecture and coordination for PB, P2 and four façades.
  `reading-guide.html` supplies all-sheet descriptions and links; `print.html` supplies a
  vector A3 landscape fit-to-page companion with no numerical scale claim.
- `visual_quality.json` records every generated SVG's delivery checks and remaining
  review tasks. Missing accessible roots, invalid viewports, unresolved style variables
  or missing non-construction wording block candidate generation. All SVG navigation
  links are checked against actual package files and target IDs; URL-encoded traversal
  is rejected. The authority check excludes explicitly hidden/definition subtrees but
  deliberately does not claim CSS cascade, clipping or rendered-visibility certification.

## Verification and phase reconciliation

| Plan stage | Delivered coverage | Remaining acceptance / work |
| --- | --- | --- |
| 0 — Baseline and export | Retained before-package identity; portable colour compiler; raster rejection of unresolved variables; exact original-colour swatch and glyph checks in resvg and available Chromium. | Full browser/font equivalence for every historical native annotation remains separate. |
| 1 — Visual contract | D-085 records the graphic direction; material, narrow PASS, OPEN, study and cobalt selection roles are separate; generated roots declare language/purpose. | Owner reading preference and physical plotting are not inferred from implementation authorization. |
| 2 — Shared rendering and QA | Shared literal-style compilation, role legends, local/global evidence counts, independent selection, authority and source-link checks; per-sheet review tasks. | Exhaustive computed local contrast and geometry/text collision coverage is not claimed for inherited native content. |
| 3 — Pilots | P2 architecture/coordination pair; PB, Side B, E1 and window-card review; live browser selection preserves study paint. | Formal timed owner reading tasks and colour-vision user review remain open. |
| 4 — Family rollout | All 36 connected sheets receive the shared delivery checks; nine review projections share roles, and 27 native consumers receive presentation metadata, the authority frame and bounded texture treatment. Native P2 has a source-derived wall-duty key. | Other native legends retain source-specific coverage. Complete re-composition of sparse elevations, dense schedules and other native families is not represented as finished. |
| 5 — Publication | Verified connected package, purpose-paired reader, text descriptions, vector print companion and refreshed review previews. | No adopted-alias promotion. A3 fit-to-page output is not a construction plotting profile; long detail sheets still need dedicated print pagination. |
| 6 — Maintenance | Regression tests cover style failures, source-role/geometry preservation, study/focus distinction, link integrity and regenerated artifact freshness. | Continue explicit per-sheet review tasks; do not automatically accept pixel baselines or claim full visual acceptance. |

This is a connected visual-language delivery across the complete review set, with bounded
family refinements. It is **not a statement that every subphase of the larger aesthetic,
accessibility and plotting roadmap has closed**. The remaining work above is observable
and separated from completed generation and delivery checks.
Human reading preference, detailed physical plotting and adopted-alias promotion remain
separate from software completion. A checked delivery profile does not assert universal
contrast, collision-free inherited annotations or architectural acceptance.

## Recorded delivery evidence

The local candidate is
`2924aa20a09b4bf95f9bd5cc746b5dd891ec12798716917e6c35624276e0909d`;
the verified review release is
`6d3de073dc7333a0afd32ec30ae8c8c5ed09ff5156be7f13e5b183cbd7d129bb`.
These identify this delivery, not a permanently current issue after future source edits.

| Verification | Observed result |
| --- | --- |
| Regression and lint | Full repository discovery: 575 tests passed in 196.250 seconds. Ruff passed for coordination, quantities and the modified SVG modules/tests. This does not claim the unrelated historical SVG files are lint-clean. |
| Physical model | Hash unchanged: `7386d33026a4a1e22f5b68df1c4187a18a9d01831c5f1f53f2bf06d3010fb6d3`. Geometry, entity records and discipline inputs compare equal to the retained before-package. |
| Quantities and cost | Complete JSON contents unchanged. No scope, quantity or budget adoption. |
| Findings | All 243 records unchanged except their top-level `input_hash`, which correctly identifies the revised build inputs. Counts remain 57 PASS / 186 OPEN / 0 FAIL. |
| Annotation contract | 322 source-bound anchors, 166 evaluated dimensions and verified visible labels, five callouts; no unresolved anchors. Technical projection purposes remain unchanged; presentation wording is recorded separately. |
| Graphic delivery | 36 SVGs; zero unresolved style variables or delivery-fundamental errors; 148 SVG navigation destinations checked against actual package files and fragment IDs. |
| Browser interaction | Selecting `GLZ-DINING-STUDY-B` selects three occurrences. Its violet stroke and `6px, 4px` study dash remain unchanged; the independent focus layer conveys selection. |
| Print smoke test | Chromium produced a 36-page A3 landscape PDF (1191.12 × 841.92 pt) from the final `print.html`; no JavaScript in the PDF. This confirms page delivery, not small-text or construction plotting acceptance. |
| Visual inspection | All 36 sheets inspected as three contact sheets, with enlarged P2 architecture/coordination review and representative PB, Side B, E1, stair and opening-detail checks. Contact-sheet inspection establishes composition coverage, not every annotation's legibility. |

Local reproducibility evidence is retained under `.build/visual-language-implementation/`;
the authoritative generated evidence travels inside the release as `visual_quality.json`,
`view_inventory.json`, manifests and source-derived ledgers. README snapshots retain
their own tracked release manifest. They are image excerpts: use the complete generated
reader for cross-sheet and finding-register links.

## Rebuild and maintenance

Edit repository sources or generators, then run:

```bash
python3 -m unittest discover -s dreamhouse -p 'test_*.py'
python3 -m dreamhouse.coordination --visuals --require-no-fail --release
python3 -m dreamhouse.coordination --check --visuals --require-no-fail
python3 -m dreamhouse.coordination --check-release
python3 .github/scripts/sync_coordination_previews.py --write
python3 .github/scripts/sync_coordination_previews.py --check
python3 .github/scripts/build_showcase.py --write-readme
```

Inspect the generated PNGs, `reading-guide.html`, `print.html` and
`visual_quality.json` before treating another issue as visually reviewed. Do not edit
generated SVGs directly or accept a changed screenshot solely because generation passed.
Portable colour compilation is exercised with resvg and available Chromium; a machine
without Chromium cannot establish the optional browser comparison from that test run.

The next graphic refinement should paginate the long opening-detail sheet and improve
the sparse native elevation layouts. Preserve source-bound geometry and named dimensions;
move editorial frames, legends and text only through the generator. After those pilots,
extend source-derived legends and measured local text/contrast checks to the remaining
native families. Physical plotting and owner reading tasks then supply the separate
acceptance evidence listed in the phase table.
