# Connected SVG visual-language research

**Status:** research and project-specific recommendations; not adopted as a graphic standard
**Version:** 0.1
**Date:** 2026-10-03
**Source:** owner request for a research-backed visual review; repository reading of the
current drawing-system plan, palette/contrast lint and five graphic pilots; fourteen
targeted reviews of primary W3C, public-agency, statistical-design, design-system and
buildingSMART sources accessed on 2026-10-03.
**Authority boundary:** this document addresses visual communication, SVG delivery and
review. It changes no model, drawing, palette, geometry, scope, quantity, cost, decision,
conflict, professional gate or construction authority. All recommendations remain
proposals for the existing SVG-G0 adoption gate.

## 1. Question and conclusion

Dream House already has two complementary graphic directions: the published drawing set
contains traceable but visually inconsistent SVG/PNG pairs, while five presentation
pilots test a calmer sheet frame, readable evidence panels, semantic colours, patterns,
metadata and accessibility. The next useful step is to bring that evidence into one
reviewable visual-language decision without confusing a software candidate with an
adopted drawing rule.

The best fit for this project is a **quiet architectural core with a precise explanatory
layer**. The core should remain recognizable as professional architectural and
engineering drawing: dark neutral geometry, view-appropriate lineweight, dimensions,
levels, IDs, symbols, readable notes, provenance and explicit authority. A second layer
can make the same content easier to enter through restrained zone tints, local keys,
short evidence cards, a clear reading order, selected patterns and a few deliberately
composed overview diagrams. The explanatory layer must remain traceable to the active
source and must not make unresolved geometry appear selected.

For Dream House, the visual signature should come from the one simple industrial hall,
the large front void, visible structure, light, and the technical-to-monumental-to-
domestic-to-core sequence already established by the Project Constitution. Added shapes,
colour or perspective do not improve that story if they invent an opening, structure,
product, site orientation, performance value or material finish.

This review supports a small, role-based palette and view-specific layouts, not a new
palette of decorative colours. The project's candidate neutral, teal, amber and red
roles are useful only when their meaning is stable across a sheet family and repeated
with direct wording and a non-colour cue. Existing source sheets and pilots do not yet
share one stable meaning for those hues, so a whole-set semantic comparison remains a
decision-gate item.

## 2. Repository evidence and limits

The retained full visual audit reports 27 current drawing identities and 217 SVG files
under <code>planos/</code>, with four drawing grammars, three canvas sizes, 352 distinct
inline colours in the current set, 1,271 current-set text elements and 860 texts below
8 effective pixels at the 1,400 px preview width. It also records 18 of 27 current
drawings without a complete accessible root. Those measurements belong to the
2026-08-23 audit scope. The 2026-10-03 plan reconciliation explicitly says it is not a
new census of all historical SVGs. New connected-renderer totals describe a different
generated consumer set and must not be substituted for the 27 current aliases or the
217-file historical corpus. [SVG drawing-system improvement plan](svg_drawing_system_improvement_plan.md)

The five graphic pilots establish useful evidence, but their colour lint is deliberately
narrow: 373 presentation text elements are checked against typed backgrounds, while 119
inherited model-text elements whose backgrounds vary with source geometry are excluded.
The pilots report contrast passes, but that result does not characterize all model text,
all current aliases, all raster exports, or every browser/renderer combination. The
same lint report states that the five pilots are not approved for current-drawing
rollout. [SVG palette and contrast lint v0.2](svg_palette_contrast_lint_v0.2.md)

The pilots have exercised grayscale and 480, 800, 1,400 and 1,684 px output, stable IDs,
visible status labels, descriptive roots, patterns and model-geometry comparisons.
Their review documents still identify cross-browser font metrics and renderer
equivalence as open acceptance gates. That is useful pilot evidence, not proof that
every published SVG has the same visual result in every renderer.
[Graphic pilot 01](svg_graphic_pilot_01_visual_review.md) · [Graphic pilot 05](svg_graphic_pilot_05_visual_review.md) · [Browser/Resvg equivalence audit](svg_browser_resvg_equivalence_v0.5.md)

The palette mismatch is visible in source evidence. The pilot theme assigns
<code>#8A5A16</code> to open, <code>#A33F31</code> to conflict and <code>#BD7626</code>
to trial; the current <code>DH-ARQ-SEC-CUB-003</code> uses a red
<code>#A63F31</code> for an OPEN label, while <code>DH-ARQ-DET-004</code> uses amber for
open balcony geometry and red for open professional gates. This shows semantic drift
across drawing generations, not that one use should be silently rewritten. The palette
lint correctly keeps inherited model colour as a warning rather than mutating it.
Reconcile these meanings before promoting a shared theme.
[Pilot theme](../../dreamhouse/svg/theme.py) · [Current daylight section](../../planos/actual/DH-ARQ-SEC-CUB-003_CURRENT-DAYLIGHT.svg) · [Current P2 hall-edge detail](../../planos/actual/DH-ARQ-DET-004_CURRENT-P2-HALL-EDGE.svg)

The companion [October visual-language audit](connected_svg_visual_language_audit_and_plan_2026_10.md)
now supplies the fresh census: 231 tracked SVGs plus 36 current release SVGs, 267 file
occurrences and 227 distinct contents. Its inventory and colour-renderer experiment
supersede any assumption that the older corpus count or bounds-equivalence checks
describe current whole-set colour fidelity. The older measurements above retain their
historical scope.

## 3. Research method and transfer limits

The investigations below use issuing-body sources, specifications, public manuals and
first-party design systems. Each entry separates the source finding from a project
recommendation. WCAG addresses web content, including SVG delivered in a browser; it is
used here as a conservative digital communication benchmark, not as proof of complete
WCAG conformance or an architectural plotting rule. Statistical chart guidance is
transferred only to graphics that encode categories, quantities or uncertainty. USACE
and VA documents govern their own public-agency deliverables; they are comparative
communication sources, not Colombian requirements. IFC representation concepts are
used as a view-and-scale model, not as an IFC authoring requirement.

No paywalled ISO provision is inferred. No foreign guide resolves a Colombian code,
professional-design, construction or procurement question.

## 4. Findings by investigation

### R01 — Colour is a redundant cue, not a status system by itself

**Source finding.** WCAG 2.2 explains that users on monochrome displays or with limited
colour perception may miss information conveyed by hue; a visible secondary cue can
preserve it. A luminance difference can count as another visual distinction when it is
strong enough, but when meaning depends on recognizing a particular hue, an additional
cue is still required. [W3C, Understanding SC 1.4.1: Use of Color](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html)

**Project recommendation.** Keep OPEN, CONFLICT, TRIAL, NOT ADOPTED, VERIFIED INPUT and
similar words legible without hue. Pair an amber or red boundary with its word, stable
decision/conflict ID, and a dash, hatch or marker. Check monochrome output for legible
hierarchy, not merely a technically non-empty page.

**Palette implication.** Teal, amber and red may reinforce an existing meaning; they
must not create that meaning on their own. Red and green cannot be the only distinction
between failure and success.

### R02 — Text colour must be checked against its local surface

**Source finding.** WCAG 2.2 SC 1.4.3 sets a minimum 4.5:1 text/background ratio for
normal text and 3:1 for large text, subject to stated exceptions. The criterion is about
web-content text and does not itself set print lineweight or sheet font size.
[W3C, WCAG 2.2 SC 1.4.3](https://www.w3.org/TR/WCAG22/#contrast-minimum)

**Project recommendation.** Preserve the existing linter's pair-based method: resolve
the actual foreground, opacity-composited surface, font role and effective size for each
presentation label. Add no contrast credit for a hue name such as teal or dark amber.
Keep exact tested values and surface relationships within the SVG-G0 decision record if
the owner adopts them.

**Palette implication.** Dark neutral ink remains the strongest default for geometry
and text. The existing pilot info teal, amber open and red conflict tokens have
computed pair results on the two declared light pilot surfaces; that result does not
automatically transfer to a translucent fill, another background or a very small line.
[SVG palette and contrast lint v0.2](svg_palette_contrast_lint_v0.2.md)

### R03 — Thin lines need a stronger practical test than their colour value

**Source finding.** WCAG 2.2 SC 1.4.11 sets 3:1 contrast for meaningful graphical
objects against adjacent colour. W3C also warns that antialiasing can make particularly
thin lines appear fainter than their nominal CSS colour; a line may pass a computed
ratio and remain weak in practice. [W3C, Understanding SC 1.4.11: Non-text Contrast](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html)

**Project recommendation.** Test a critical cut edge, dimension line, door swing,
stair edge, rooflight outline and uncertainty boundary at normal preview width, at
100% print, and in grayscale. If a cue disappears when reduced, adjust its semantic
lineweight, dash/pattern or direct label. Do not make every line heavy to compensate.

**Texture and lineweight implication.** Hatch spacing, boundary contrast and stroke
width are part of meaning. Pattern keys should survive downsampling without merging
into a dark fill; fills should not mask the edge they explain.

### R04 — SVG accessibility needs meaningful groups and text alternatives

**Source finding.** SVG 2 says a meaningful rendered object can be described by a
container group; empty title or description children should not be emitted. The SVG
Accessibility API Mappings describe how aria-labelledby, aria-describedby, title and
desc contribute names and descriptions. The 2026-09 SVG-AAM publication is a Working
Draft, and W3C accessibility guidance notes inconsistent support across browser and
assistive-technology combinations. [W3C, SVG 2 document structure](https://www.w3.org/TR/SVG2/struct.html) · [W3C, SVG-AAM Working Draft](https://www.w3.org/TR/2026/WD-svg-aam-1.0-20260924/) · [W3C ACT Rule: SVG accessible names](https://www.w3.org/WAI/standards-guidelines/act/rules/7d6734/)

**Project recommendation.** Give each sheet a concise title and description that states
view, project status and the main reading order. Give meaningful groups stable names
such as hall envelope, P2 edge, opening family or evidence matrix; avoid accessible
names for decorative frame elements. For dense sheets, provide a companion plain-text
summary of the main relationship and unresolved gates rather than relying on a screen
reader to traverse hundreds of SVG primitives.

**Legend implication.** SVG metadata and visible key text serve different readers.
Keep both where useful: metadata for machine/accessibility context and a nearby visible
legend for readers examining the drawing.

### R05 — Use chart colours according to the data relationship

**Source finding.** ONS guidance distinguishes categorical colours from ordered colour
scales, asks that repeated categories keep the same colour between charts, recommends
limiting category colours, and identifies a diverging palette for categories that move
from a meaningful midpoint toward two extremes. Its guidance recommends five or fewer
colours for ordinary categorical charts and a scale for naturally ordered categories.
[ONS, Using colours in charts](https://service-manual.ons.gov.uk/data-visualisation/colours/using-colours-in-charts) · [ONS, Choropleth maps](https://service-manual.ons.gov.uk/data-visualisation/chart-types/choropleth-maps)

**Project recommendation.** Apply this logic to analytic side graphics, not as a
direct colour specification for plans. A phase comparison can use a stable categorical
key; a measured quantity gradient needs an ordered variable; a diverging scale is
appropriate only where a real neutral threshold or midpoint exists. Architectural
programme zones should use a few restrained family fills and direct room labels, not a
new hue for each object.

**Palette implication.** Do not import ONS colour literals into the Dream House theme.
The useful transfer is matching palette type to data type, consistent mapping, fewer
categories, adequate contrast and local annotation.

### R06 — Uncertainty graphics must earn their visual complexity

**Source finding.** ONS says to show an uncertainty range when it changes the
interpretation, omit ranges that add noise without changing it, and avoid charting data
so uncertain that meaningful comparison is impossible. Its examples use a shaded band
around a central estimate or a point with a range and recommend a plain-language legend
or annotation. [ONS, Showing uncertainty in charts](https://service-manual.ons.gov.uk/data-visualisation/guidance/showing-uncertainty-in-charts)

**Project recommendation.** Separate a quantified interval from an unresolved design
state. If a cost or performance estimate has a defensible numeric range and the range
could alter a decision, show its basis, units, date, central estimate if valid, and
range together. If a door span, structural system or product is unresolved, label it
open or conflicting; do not draw a pseudo-statistical band around a guessed position.
An evidence card can list known input, open assumption, what would close it and the
responsible discipline without manufacturing probabilities.

**Texture and colour implication.** Use a light band only for a real interval.
Unresolved geometry can use a labelled dashed envelope or hatched region only if the
envelope itself is traceable to a source or declared study boundary.

### R07 — Every explanatory graphic should make one point and provide it in text

**Source finding.** USWDS recommends a central idea and no more than two or three
concepts in one visualization, avoiding colour reuse across variables, and providing
both a plain-language message and equivalent accessible content. It cautions that a
data table provides underlying values but does not replace the narrative a visualization
communicates; it also calls for manual review of meaning and context. [U.S. Web Design System, Data visualizations](https://designsystem.digital.gov/components/data-visualizations/)

**Project recommendation.** Make each added graphic answer one owner-relevant question:
How does the hall change from technical to domestic use? What is open at this interface?
Which values are measured and which remain provisional? Keep detailed drawings
authoritative for geometry and the small companion summary clear about intent, evidence
and open work.

**Aesthetic implication.** A restrained overview can be more memorable than a crowded
rendering. Use one primary view, a small number of accents, whitespace and direct
labels; do not fill available space with unrelated symbols or prose.

### R08 — Categorical, sequential and diverging palettes mean different things

**Source finding.** IBM Carbon distinguishes qualitative colours for uncorrelated
categories, sequential palettes for ordered values, and diverging palettes around
two-sided concepts. Its data-visualization guidance warns against using multiple
gradients and says a gradient should not replace a sequential palette. [IBM Carbon, Data visualization color palettes](https://v10.carbondesignsystem.com/data-visualization/color-palettes/)

**Project recommendation.** Keep a single stable accent for cross-sheet navigation or
discipline context; reserve distinct colours for genuinely separate categories or a
defined numeric variable. Use pattern or line type to distinguish assembly layers, and
text/IDs to distinguish statuses. Gradients are not a substitute for component
legends or uncertainty evidence.

**Palette implication.** Teal can act as an information/navigation accent when it
remains consistent. Amber and red should not alternate as decoration; their
interpretation must remain stable across all current and candidate sheets. Existing
role drift means that the exact mapping needs explicit adoption, not an aesthetic guess.

### R09 — Lineweight is a hierarchy with a limited number of useful tiers

**Source finding.** The USACE A/E/C Graphics Standard says varied widths substantially
improve readability and that its eight-width series is sufficient for most A/E/C
drawings unless additional widths produce a material clarity or contrast improvement.
This is agency drafting guidance, not a Colombian standard. [USACE, A/E/C Graphics Standard](https://www.saj.usace.army.mil/Portals/44/docs/Engineering/AECStandardR5.pdf)

**Project recommendation.** Retain the five semantic plotted tiers already proposed in
the repository roadmap (cut, outline, primary, secondary and grid/reference) and map
them separately to screen and print output. Vary weight by view role: a wall cut is
strong in plan; a furniture symbol, hidden edge or grid remains subordinate. Use dash
and pattern for state or visibility; do not use a heavy red outline as a generic alert.
[SVG drawing-system improvement plan, lineweight hierarchy](svg_drawing_system_improvement_plan.md)

**Monochrome implication.** Strong hierarchy, not an expanded hue count, should carry
the professional drawing when printed without colour.

### R10 — A print package should preserve vector geometry and searchable text

**Source finding.** The U.S. Department of Veterans Affairs Drawing Deliverable
Requirements apply to VA projects. They call for a full-size PDF consistent with the
corresponding drawing file, vector-based scale-independent linework, selectable text,
and sheet references that can be bookmarked or hyperlinked. These are VA-specific
deliverable rules; they are a print-quality precedent only. [U.S. Department of Veterans Affairs, Drawing Deliverable Requirements](https://www.cfm.va.gov/til/bim/DwgDelivRqmts.pdf)

**Project recommendation.** Keep SVG as the scalable source and make any future PDF
companion from the same pinned issue, retaining vector linework and selectable text
where the export path allows. If a physical paper size is adopted, declare it in the
print profile and label scale only after the export has been checked at actual size.
Preserve an easy full-sheet view and a detail/zoom view for digital review.

**Provenance implication.** A print PDF needs the same issue ID, source revision, date,
status and non-construction wording as its source SVG. A beautiful thumbnail is not a
replacement for a full-size deliverable.

### R11 — A view and target scale should determine how much geometry is shown

**Source finding.** buildingSMART IFC 4.3 defines representation sub-contexts with a
TargetView and optional TargetScale; an application can choose the most appropriate
representation for the selected view and scale. Its view enumeration distinguishes
plan, section, elevation, model and sketch representations, with examples of different
wall detail by view and scale. [buildingSMART, IfcGeometricRepresentationSubContext](https://standards.buildingsmart.org/IFC/RELEASE/IFC4_3/HTML/lexical/IfcGeometricRepresentationSubContext.htm) · [buildingSMART, IfcGeometricProjectionEnum](https://standards.buildingsmart.org/IFC/RELEASE/IFC4_3/HTML/lexical/IfcGeometricProjectionEnum.htm)

**Project recommendation.** Define each SVG view by purpose and reading scale before
choosing lineweight, pattern density or detail. Keep a clean overview for spatial
relationships; provide a separate enlarged detail for construction interfaces; do not
shrink every assembly onto the overview plan. A schematic overview may omit layer detail
only when a linked schedule/detail carries it and the omission is stated.

**Responsive-detail implication.** Responsive output should preserve the view's
information role. At small size, maintain the silhouette, primary labels and status;
let fine annotations be read by opening or linking to a dedicated detail view rather
than automatically shrinking the whole drawing.

### R12 — SVG viewport scaling does not establish physical print size

**Source finding.** SVG 2 defines viewBox as a user-space rectangle mapped through a
viewport transform, with preserveAspectRatio affecting that mapping. CSS Values and
Units fixes the CSS-inch to CSS-pixel ratio at 96:1, but notes that print media at normal
viewing distance should use physical units as the anchor; pixel and physical units can
diverge with output-device characteristics. [W3C, SVG 2 coordinate systems](https://www.w3.org/TR/SVG2/coords.html#ViewBoxAttribute) · [W3C, CSS Values and Units Level 3](https://www.w3.org/TR/css-values-3/#absolute-lengths)

**Project recommendation.** Treat viewBox dimensions as an abstract sheet coordinate
system. Keep width and height for stable rasterization, and define a separate physical
export profile in millimetres or inches if print is required. Test lineweight and text
at the intended paper size as well as the 1,400 px preview. The existing 1684 × 1191
frame is not A3 by virtue of its pixel dimensions; the roadmap keeps A3 as a candidate
physical profile pending SVG-G0.
[SVG drawing-system improvement plan, sheet frame and type roles](svg_drawing_system_improvement_plan.md)

### R13 — Font family names alone do not lock text layout

**Source finding.** CSS Fonts describes an ordered font-matching process. If a declared
or downloadable face is missing, invalid or lacks a glyph, the user agent proceeds to
a fallback; the final system fallback may vary by user agent. [W3C, CSS Fonts Module Level 3](https://www.w3.org/TR/css-fonts-3/)

**Project recommendation.** Use a pinned font file and version in each controlled raster
or PDF build, with a checked font hash and a tested fallback policy. Test glyph
coverage for English technical text, symbols, degree signs and units. Record renderer
and font inputs with generated previews. Keep browser and resvg comparison as an open
acceptance gate until actual source colours, text bounds and representative sheets agree.
[Browser/resvg equivalence audit](svg_browser_resvg_equivalence_v0.5.md)

**Responsive-text implication.** A fallback font can change glyph width and line
wrapping; a label that fits at one size or renderer may collide at another. Prefer
explicit wrapping and a dedicated detail panel over shrinking text to fit.

### R14 — Browser print settings may suppress backgrounds

**Source finding.** CSS Color Adjustment Level 1 defines print-color-adjust as a hint
about automatic browser changes, including suppressing backgrounds in print to save
ink; the user's print preference has priority over the author hint. [W3C, CSS Color Adjustment Module Level 1](https://www.w3.org/TR/css-color-adjust-1/#print-color-adjust)

**Project recommendation.** Make grayscale and economy-print output intelligible if
subtle fills disappear. Keep type dark on light surfaces; use boundaries, hatch, dash,
lineweight and labels for essential relationships. When exact-colour print is needed,
provide a PDF/export path and test whether the user's print dialog retains the important
marks.

**Texture implication.** Light surface tints are grouping aids, not essential encodings.
A legend that only differentiates pastel squares is fragile; pair each sample with a
label or pattern.

## 5. Project-specific palette and linework guidance

This section interprets the sources for Dream House. It proposes no new colour tokens
and does not adopt the existing pilot palette.

| Visual role | Proposed reading | Useful redundant cue | Current limitation |
| --- | --- | --- | --- |
| Neutral ink | Primary architecture, dimensions, identifiers and evidence text | View hierarchy and lineweight | Keep warm paper only if text and key edges remain legible when its fill is removed |
| Teal / blue-green | Information, cross-view references or a defined discipline accent | Stable ID, leader, line style and legend | Do not use it as an unlabelled status or imply that geometry is selected |
| Amber | Open coordination item or provisional condition, if adopted at SVG-G0 | OPEN or PROVISIONAL, dashed edge, hatch and local source/gate ID | Current drawings and pilot theme do not share one amber/red mapping |
| Red | A recorded conflict, hold or prohibited inference, if adopted at SVG-G0 | CONFLICT/HOLD, CF ID, cross marker or cross-hatch | Red used as general emphasis can imply failure or emergency |
| Green | Verified input/check only, if adopted | VERIFIED INPUT or narrow check result plus scope | Never imply design approval, code compliance or construction readiness |
| Purple / trial accent | Option, reserve or study, if retained | TRIAL, NOT SELECTED or NOT ADOPTED | A familiar design-system hue does not authorize product or geometry selection |
| Material fill/pattern | Material family only when supported by the active source | Pattern key, layer number and material wording | A polished swatch must not create an unselected assembly |

The palette should remain small because the current drawing audit found many
uncontrolled literals and chart-design guidance links excessive category colours with
harder discrimination. Keep programme fills pale and subordinate. Use dark neutral
foregrounds for most labels. For each exact text/surface pair, preserve the automated
contrast result, then inspect thin lines and patterns at actual output size.

Keep lineweight distinct from evidence confidence. A heavier line should describe what
the view cuts or foregrounds, not how certain the design is. Use line type, label, local
key and evidence wording to distinguish open, conflicting, trial or excluded
information. The plotted values already in the plan (0.70, 0.50, 0.35, 0.25 and
0.18 mm) are candidate screen/print mapping anchors; no value is adopted by this
research.

### Legend design

- Use a direct label when one object or a small number of conditions can be named locally.
- Use a compact local legend for repeated patterns, line types, material layers or status
  keys; repeat all status wording in text.
- Keep pattern sample, line sample, label and applicable IDs adjacent so a reader does
  not have to infer a connection across the page.
- State units and scope in the legend where values could be misread. A nominal layer
  thickness and an illustrative sum must remain separately named.
- Distinguish “not shown”, “not selected”, “open” and “conflict”; do not use one blank
  swatch for all missing information.
- Keep legends subordinate to the primary view and preserve enough sample size for a
  hatch or dash to remain visible at the 1,400 px preview.

## 6. Useful architectural graphic candidates

The following are candidates for a future graphic plan. They reuse project information
and visual-review practices already in the repository; they do not authorize new views
or design claims.

| Candidate graphic | Question it can answer | Composition | Authority guardrail |
| --- | --- | --- | --- |
| **One-hall overview** | How does the industrial hall become a home while retaining its one-room character? | A clean axonometric or cutaway beside an orthographic PB plan; restrained bands identify technical, monumental, domestic and core sequence; stable IDs connect the views. | Build from one declared model issue. Show the partial P2 and great void as governed. The axonometric is explanatory, not dimensional authority. |
| **The great void and daylight** | How do roof, P2 edge, visible structure and rooflights relate to the double-height space? | Pair one longitudinal and one transverse section with a small rooflight key. Use a neutral cut profile and restrained light cue; label design-intent lighting separately from tested daylight results. | Do not invent a north arrow, sun angle, glare result or illuminance map while site orientation and building-physics evidence remain open. |
| **Workshop-to-home sequence** | How do the project car, RC/DIY work, central axis and domestic transition coexist? | Keep a readable plan as the base; use numbered callouts for the workbench family and vehicle/lift envelopes; show one circulation path only when its endpoints and clearances are source-backed. | Equipment envelopes remain schematic until products and safety/MEP checks are resolved. |
| **P2 edge and wall family** | Where is the family balcony open, where are suites enclosed, and what do the controlled wall types contain? | Use a plan strip plus an enlarged section or exploded keyed build-up; pair each pattern with a layer name and stated nominal value. GP04 demonstrates a readable pattern-plus-label treatment. | Do not add ratings, product names, fire/acoustic performance or final build-up where the current record leaves them open. |
| **Evidence and uncertainty card** | What is known, what is assumed, and what closes the next decision? | A compact card separates source/verified input, open question and required evidence/owner; a measured range appears only when there is a defensible numeric interval. | Never turn an open conflict into a range, infer probability, or let a badge imply professional sign-off. |
| **F1/F2 phase comparison** | What is delivered in each phase and what must remain ready for the next? | Matched plans or an indexed schedule with identical crop and view order; a stable phase key and direct labels show phase differences. | Use active phase and cost records. Do not imply saving, quantity or completion date not authorized and measured. |
| **Material and light board** | What quiet interior/exterior material contrast is intended? | A small family of flat swatches or hatch samples beside the related section/elevation; label illustrative finishes where no product is selected. | A rendering or swatch is not a specification and cannot override the active design basis or product gates. |

The strongest graphic opportunities combine two views that answer different questions,
such as the one-hall overview plus its plan, or the P2 edge plan plus an enlarged
section. Avoid one all-purpose hero image that tries to encode geometry, material, cost,
lighting, structure, construction sequence and status at once.

## 7. Responsive, accessible and print review profile

The following is a proposed review profile to carry into SVG-G0, not an added repository
gate:

1. **Source identity:** source revision, source hash, decision/conflict references,
   issue status and construction authority remain explicit.
2. **View purpose:** identify plan, elevation, section, detail, schedule, model overview
   or evidence graphic and its intended reading scale.
3. **Colour and grayscale:** review full colour and grayscale; test the normal 1,400 px
   publication width plus the existing 480/800 px overview outputs.
4. **Critical content:** keep title, sheet identity, principal geometry, key dimensions,
   IDs and authority status readable at the declared output; allow detail text to be
   opened at full SVG size or moved to a linked detail.
5. **Contrast and graphics:** calculate exact text/background ratios; inspect critical
   lines and hatch at output size because thin-line antialiasing can weaken the apparent
   result.
6. **Accessible alternative:** provide a meaningful SVG name and description, semantic
   groups where they improve navigation, and a concise text summary of the view's
   central message and unresolved gates.
7. **Font and renderer:** pin font files and renderer inputs; compare browser and
   rasterizer output for actual hue, text layout, symbols, line pattern and boundaries.
8. **Print:** define a physical page profile separately from viewBox; preserve vector
   linework and selectable text in a print export where supported; inspect full-size and
   economy/grayscale output.
9. **Geometry and authority:** compare model-space content and all source values
   independently from presentation changes; keep hypotheses and render-only cues
   explicitly non-dimensional.
10. **Manual review:** inspect reading order, status meaning, line hierarchy and the
    effect of missing fills. Automated checks cannot judge whether a polished view
    implies unsupported certainty.

The existing improvement plan already contains candidate frame, typography, lineweight,
palette, collision and migration proposals. This research strengthens their evidence
and clarifies their boundaries; it does not approve them.

## 8. Decisions left open

- The 1684 × 1191 viewBox may remain a digital sheet coordinate system; physical paper
  size and print scale still require the SVG-G0 decision.
- The proposed semantic palette needs one cross-sheet mapping review against current
  aliases, connected views and all five pilots.
- Status colours used by current source drawings need reconciliation with the pilot
  open/conflict roles before shared-theme promotion.
- Required publication, full-size print and compact overview profiles need agreement and
  renderer-specific evidence.
- SVG accessibility metadata should be validated in the target browser and assistive
  technology; valid markup alone does not prove an understandable reading experience.
- Visual refactoring remains presentation-only. A need to change a model coordinate,
  value, product, scope, cost or design status must go through the project's source,
  decision and conflict controls.

This document records no new owner decision. The pilot palette remains a tested
presentation candidate, not an adopted current-drawing standard. No decision-register
or cost-control entry is warranted until an owner-approved graphic-system decision
changes scope or cost.

## 9. Source register

All web pages below were accessed on 2026-10-03. The source findings in R01–R14 link
directly to the relevant issuing-body pages.

| Ref. | Primary source | Use in this review |
| --- | --- | --- |
| R01 | W3C, [WCAG 2.2: Use of Color](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html) | Hue is not a sufficient sole cue; visible alternatives |
| R02 | W3C, [WCAG 2.2: Contrast (Minimum)](https://www.w3.org/TR/WCAG22/#contrast-minimum) | Text/background contrast thresholds and applicability |
| R03 | W3C, [WCAG 2.2: Non-text Contrast](https://www.w3.org/WAI/WCAG22/understanding/non-text-contrast.html) | Meaningful graphical objects and thin-line antialiasing |
| R04 | W3C, [SVG 2 document structure](https://www.w3.org/TR/SVG2/struct.html), [SVG-AAM Working Draft, 2026-09-24](https://www.w3.org/TR/2026/WD-svg-aam-1.0-20260924/) and [ACT SVG accessible-name rule](https://www.w3.org/WAI/standards-guidelines/act/rules/7d6734/) | Accessible names/descriptions and browser-support caveat |
| R05 | UK Office for National Statistics, [Using colours in charts](https://service-manual.ons.gov.uk/data-visualisation/colours/using-colours-in-charts) and [Choropleth maps](https://service-manual.ons.gov.uk/data-visualisation/chart-types/choropleth-maps) | Category, ordered and diverging data palette roles |
| R06 | UK Office for National Statistics, [Showing uncertainty in charts](https://service-manual.ons.gov.uk/data-visualisation/guidance/showing-uncertainty-in-charts) | Whether and how to show ranges |
| R07 | U.S. General Services Administration, [U.S. Web Design System: Data visualizations](https://designsystem.digital.gov/components/data-visualizations/) | Simplicity, narrative, accessible equivalents and manual review |
| R08 | IBM, [Carbon Design System: Data visualization color palettes](https://v10.carbondesignsystem.com/data-visualization/color-palettes/) | Categorical, sequential and diverging palette distinctions |
| R09 | U.S. Army Corps of Engineers, [A/E/C Graphics Standard](https://www.saj.usace.army.mil/Portals/44/docs/Engineering/AECStandardR5.pdf) | Limited plotted-lineweight hierarchy |
| R10 | U.S. Department of Veterans Affairs, [Drawing Deliverable Requirements](https://www.cfm.va.gov/til/bim/DwgDelivRqmts.pdf) | Full-size PDF, vector linework and searchable-text precedent |
| R11 | buildingSMART, [IfcGeometricRepresentationSubContext](https://standards.buildingsmart.org/IFC/RELEASE/IFC4_3/HTML/lexical/IfcGeometricRepresentationSubContext.htm) and [IfcGeometricProjectionEnum](https://standards.buildingsmart.org/IFC/RELEASE/IFC4_3/HTML/lexical/IfcGeometricProjectionEnum.htm) | View purpose and target scale as representation controls |
| R12 | W3C, [SVG 2 coordinate systems and viewBox](https://www.w3.org/TR/SVG2/coords.html#ViewBoxAttribute) and [CSS Values and Units Level 3](https://www.w3.org/TR/css-values-3/#absolute-lengths) | Viewport transform, CSS reference and physical print units |
| R13 | W3C, [CSS Fonts Module Level 3](https://www.w3.org/TR/css-fonts-3/) | Font matching, glyph coverage and fallback variation |
| R14 | W3C, [CSS Color Adjustment Module Level 1](https://www.w3.org/TR/css-color-adjust-1/#print-color-adjust) | Print colour adjustment and user preference precedence |
