# Connected SVG set — architectural visual review

**Version:** 0.2<br>
**Date:** 2026-10-03<br>
**Status:** generator refinements implemented; verification evidence recorded below<br>
**Source:** owner-requested architectural visual inspection of the 36 SVG sheets through their generated PNG previews; subsequent instructions to retain the review in Markdown and repair the generated presentation.<br>
**Authority:** visual and spatial-reading review only. No design change, drawing promotion, scope or cost change, engineering acceptance or conflict closure is adopted.

## Original reviewed package and limits

- Candidate: `25acce0205999546149e5a01910e7eb165a6502fcc8273fa720d57eb96362060`.
- Review release: `b6d68cd34843fbe489a13cfdbfb25e2b5332065f6635242d39fb148d70f9fcf7`.
- Coverage: 27 catalog-derived review sheets and nine connected review projections.
- Method: visual inspection of the generated previews, comparing plans, elevations, sections, details and diagram composition. This was not a new dimensional, structural, regulatory or software audit.
- Drawing links below target the inspected local candidate under `.build/`. That directory is generated and untracked; links require the retained package. New sources may generate a different candidate. The [current drawing index](planos_actuales.md) identifies the separately adopted set and must not be confused with these review copies.

No files or geometry were changed during the original visual inspection. The subsequent presentation repairs are recorded separately below. Passing calculation and annotation tests does not establish that every sheet communicates clearly.

## Overall architectural assessment

The house's intent is legible, but the set still needs graphic refinement before it can be considered a finished architectural presentation.

The ground-floor plan communicates the continuous industrial hall, central axis and workshop–living–dining–service-core sequence. The front elevation retains three recognizable entrances and a simple industrial expression. The upper floor communicates the arrangement of bedrooms around the shared family space.

## Prioritized findings

| ID | Priority | Sheet or area | Visual observation and consequence | Proposed response |
| --- | --- | --- | --- | --- |
| VR-01 | High | [Upper-floor plan](../../.build/coordination/issues/25acce0205999546149e5a01910e7eb165a6502fcc8273fa720d57eb96362060/drawings/architecture-upper-floor.svg) | Primary-bathroom text overlaps furniture, area annotations and other labels. The room is difficult to interpret. The plan occupies relatively little space compared with the adjacent commentary. | Separate room names, areas and fixture labels; enlarge the plan or move supporting commentary to another panel. |
| VR-02 | High | [Ground-floor plan](../../.build/coordination/issues/25acce0205999546149e5a01910e7eb165a6502fcc8273fa720d57eb96362060/drawings/architecture-ground-floor.svg) and [technical workbench detail](../../.build/coordination/issues/25acce0205999546149e5a01910e7eb165a6502fcc8273fa720d57eb96362060/drawings/architecture-pb-technical-workbenches.svg) | The RC assembly island is labelled **3 × 1.50 m** on the general plan, while the technical detail announces **4.50 × 1.60 m** and retains overlapping text within the island. The sheets communicate conflicting dimensions. | Reconcile the printed labels against the governing source and remove overlapping inherited text. This observation does not select either dimension as authoritative. |
| VR-03 | High | [Side B elevation](../../.build/coordination/issues/25acce0205999546149e5a01910e7eb165a6502fcc8273fa720d57eb96362060/drawings/architecture-side-b-elevation.svg) | A dark vertical line crosses the guest-bedroom window. Its role as structure, reference or hypothesis is not sufficiently clear in the image. | Distinguish and label the line's meaning. The visible overlap alone does **not** establish a physical interference. |
| VR-04 | High | [Enlarged PB core](../../.build/coordination/issues/25acce0205999546149e5a01910e7eb165a6502fcc8273fa720d57eb96362060/drawings/architecture-ground-floor-core.svg) and [Great Wall elevation](../../.build/coordination/issues/25acce0205999546149e5a01910e7eb165a6502fcc8273fa720d57eb96362060/drawings/architecture-great-wall-elevation.svg) | Omitting unresolved doors makes the rooms appear completely enclosed and the Great Wall appear blind. The written warning does not immediately explain access in the drawing itself. | Identify unresolved access requirements graphically near the affected rooms, without inventing opening locations. Retain CF-013 and the independent stair-discharge uncertainty. |
| VR-05 | Medium | [Longitudinal section](../../.build/coordination/issues/25acce0205999546149e5a01910e7eb165a6502fcc8273fa720d57eb96362060/drawings/architecture-roof-longitudinal-section.svg), [structural alternatives](../../.build/coordination/issues/25acce0205999546149e5a01910e7eb165a6502fcc8273fa720d57eb96362060/drawings/structure-coordination-plan.svg) and [structural Side A](../../.build/coordination/issues/25acce0205999546149e5a01910e7eb165a6502fcc8273fa720d57eb96362060/drawings/structure-lateral-a.svg) | Large blank areas coexist with small drawings. In the structural-alternatives sheet, the right-hand section is too close to the page edge and several labels are crowded. | Rebalance panel sizes, margins and drawing scale; move annotations away from geometry and page edges. |
| VR-06 | Medium | [Connected P2 review](../../.build/coordination/issues/25acce0205999546149e5a01910e7eb165a6502fcc8273fa720d57eb96362060/plan-p2.svg), [Side A review](../../.build/coordination/issues/25acce0205999546149e5a01910e7eb165a6502fcc8273fa720d57eb96362060/elevation-side-a.svg) and [Side B review](../../.build/coordination/issues/25acce0205999546149e5a01910e7eb165a6502fcc8273fa720d57eb96362060/elevation-side-b.svg) | Question-mark markers and warning panels compete with the geometry. Some elevation dimensions and sill-datum labels overlap. | Reduce annotation collisions and strengthen the hierarchy between geometry, dimensions and findings while keeping uncertainty visible. |
| VR-07 | Medium | Drawing set as a whole | Orientation, visual scale and hierarchy vary between plans, details and elevations. Graphic references do not make every section-to-plan relationship immediately apparent. | Use clearer view-direction indicators, section references and consistent layout conventions. |

## Spatial reading

### Central ground-floor axis

The **4 m central axis** has a strong visual presence and expresses the intended monumental interior. It also visually separates activities on opposite sides. Retain that intention while studying how people cross and inhabit the space through furniture layouts and drawn circulation routes. This is a recommendation for clearer spatial evidence, not a decision to change the axis width.

### Stair and cross-level experience

The [SC-01 section](../../.build/coordination/issues/25acce0205999546149e5a01910e7eb165a6502fcc8273fa720d57eb96362060/stair-sections.svg) explains the levels, but remains a diagram of flight envelopes. It does not yet communicate a complete spatial experience between entry, intermediate landing, upper arrival and exterior discharge. The image cannot confirm unresolved clearance or exit geometry.

## Original recommended first intervention

Begin with drawing refinement:

1. Remove text and dimension overlaps.
2. Reconcile contradictory island labels against the governing source.
3. Enlarge the architectural plans and rebalance crowded or underused sheet areas.
4. Explain unresolved accesses and ambiguous projected lines at the point where they affect interpretation.
5. Strengthen plan–section–elevation references and reduce competing warning graphics.

These actions can improve understanding substantially without changing the architectural design. Any later geometry correction must follow project precedence and decision procedures; this review does not authorize silently resolving source conflicts.


## Implemented presentation repairs — 2026-10-03

The corrections live in the connected generators, not in manually edited SVGs or historical
sources. Regeneration applies them to subsequent review packages. The original findings
above remain the record of the inspected baseline, rather than descriptions of the repaired output.

| Finding | Implemented change | Boundary retained |
| --- | --- | --- |
| VR-01 | A clear BATH label replaces the crowded bathroom block; source-derived net/gross areas move to the commentary panel. | The P2 plan scale and fixture geometry remain unchanged; this is a targeted readability repair, not a complete sheet redesign. |
| VR-02 | The PB island and detail labels derive from the same equipment source: 4.50 × 1.60 m, three 1.50 m modules, top +0.84 m under D-079. The detail uses separate lines above the module seam. | Existing source authority establishes these dimensions; this repair does not adopt a new island design. |
| VR-03 | The inherited provisional downpipe line crossing W-G becomes dashed amber and receives an explicit unresolved-interface note. | Its source position is preserved. This is not a confirmed structural clash or a resolved downpipe position. |
| VR-04 | Core and Great Wall views explicitly state that required room access remains unlocated under CF-013. The Great Wall coordination notes are reflowed. | No door leaf, swing, opening position or stair discharge is invented. |
| VR-05 | The longitudinal roof profile uses a shorter canvas; structural B-B is stacked beneath its plan; structural Side A is enlarged uniformly and its long captions separated. | Model proportions and physical geometry remain unchanged. Schematic structural alternatives remain hypotheses. |
| VR-06 | OPEN markers use compact rings; FAIL markers retain a distinctive diamond and exclamation mark. Finding cards are quieter; elevation annotations use separated positions. | Finding identities, navigation and unresolved conditions remain visible. |
| VR-07 | Plans show positive model-axis directions; elevation titles identify view direction; SC-01 references connect the review plans to the stair projection; all 27 catalog sheets identify related views. | No geographic north or solid section cut is inferred. SVG references are visible labels and metadata; browser navigation remains in the connected viewer. |

### Implementation and maintenance

- [Native presentation refinements](../../dreamhouse/coordination/presentation_refinements.py)
  bind corrected text to the resolved sources and reject missing or ambiguous expected labels.
- [Sheet composition](../../dreamhouse/coordination/sheet_layout.py) repositions presentation
  panels and adds related-view references.
- [Review renderer](../../dreamhouse/coordination/render.py) controls finding hierarchy,
  coordinate cues, stair references and elevation annotations.
- [Context annotation checks](../../dreamhouse/coordination/context_annotations.py) use the
  revised longitudinal projection origin so dimensional verification follows the rendered view.
- [Preview exporter](../../.github/scripts/sync_coordination_previews.py) exports five
  SVG/PNG pairs from a fresh verified release, including both architectural floor plans.

Future source edits must regenerate the package and pass the annotation, navigation and
visual checks. Elevation annotation placement uses bounded clear-space searches, not a
general collision-proof layout solver; densely changed studies still require visual inspection.
These refinements do not create graphical editing or make PNG/SVG files inputs.

### Remaining architectural work

Study circulation and furniture use along the unchanged 4 m central axis, and develop
stair arrival, clearance and exterior discharge once the required source decisions exist.
CF-013 door positions and professional/site/product hold points remain open. A clearer
presentation does not constitute construction acceptance or resolve those design gaps.


## Repaired package and verification

- Candidate: `deb65118faab51e68f2c45fbf92c3f979dcd6e0eb080165d3ab0e26d0e81bc90` ([local connected reader](../../.build/coordination/issues/deb65118faab51e68f2c45fbf92c3f979dcd6e0eb080165d3ab0e26d0e81bc90/index.html)).
- Verified review release: `6f9ff2314f3bd7e2e2f2b9c15084b3375b6dec176a248457dd46af8ee751793e`.
- Physical model: `7386d33026a4a1e22f5b68df1c4187a18a9d01831c5f1f53f2bf06d3010fb6d3` — unchanged from the original reviewed package.
- Output: 36 current generated SVGs and their raster previews; 27 catalog-derived sheets
  and nine review projections. Reviewed changed layouts at full-sheet size after regeneration.
- Annotation coverage: 322 source-bound anchors, 166 evaluated dimensions/verified labels,
  and five callouts (including the two new plan-to-SC-01 references).
- Direct before/after comparison: entity records, physical geometry, quantity payloads,
  cost payloads and finding identities/statuses are unchanged. Build provenance hashes
  necessarily change. Findings remain **57 PASS / 186 OPEN / 0 FAIL**.
- Full repository regression: **545 tests passed** (`python3 -m unittest discover -s dreamhouse -p 'test_*.py'`).
  Ruff and `git diff --check` passed.
- Candidate integrity, visual artifact checks, fresh release verification, five exported
  SVG/PNG preview pairs, and README/showcase generation checks passed.
- The independently adopted 27 current SVG/PNG pairs retain their existing provenance;
  the repaired connected package remains explicitly a review release.

The checked-in [preview manifest](../../.github/assets/coordination/manifest.json) records
release identity and exported file hashes. Generated package links require the local
`.build/` output; the checked-in README previews remain available without that directory.
