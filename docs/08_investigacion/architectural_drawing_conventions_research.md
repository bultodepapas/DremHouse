# Architectural drawing communication research

**Status:** comparative research and proposed project guidance; not adopted and not
construction authority
**Version:** 0.1
**Date:** 2026-08-21
**Source:** owner request of 2026-08-21; sixteen targeted reviews of primary standards
pages, standards-body material, public-sector CAD requirements, professional process
guides, accessibility guidance and W3C specifications; related SVG audit v0.2.
**Authority boundary:** this research concerns how information is represented and read.
It does not establish code compliance, approve an egress solution, select a structural
system, change model geometry or convert preliminary information into a requirement.

## 1. Research question and method

The owner asked for drawings that are more didactic and understandable than a purely
conventional architectural set, while remaining precise and professional. The research
question is therefore not “Which standard should Dream House copy?” It is:

> Which conventions make a drawing dependable for a professional, and which additional
> communication devices make the same drawing easier for an owner or non-specialist to
> understand without changing its technical meaning?

Sixteen focused studies were made. Each study distinguishes:

1. **professional convention:** the stable grammar expected in technical information;
2. **didactic value:** the part that reduces reader effort or ambiguity;
3. **Dream House adaptation:** a proportionate proposal for this repository; and
4. **guardrail:** what must not be inferred or copied blindly.

Sources were limited to primary or issuing-body material: ISO public records, W3C
specifications, the National Institute of Building Sciences/National CAD Standard,
United States public-agency deliverable manuals, RIBA, BIMForum and government
accessibility/design guidance. Public ISO pages normally expose scope and status rather
than the paid normative clauses. This is therefore a comparative research review, not a
claim of ISO, NCS, VA, USACE, RIBA, BIMForum or WCAG conformance.

NCS Version 7 is the current paid release. Detailed publicly accessible UDS examples used
here are from Version 6 and are treated as comparative implementation examples, not as a
complete review of the current NCS.

The foreign guides are communication references, not Colombian regulatory authority.
Their useful patterns are adapted only when they fit the project Constitution, language
policy, source precedence and current non-construction status.

## 2. Executive conclusion

The best fit for Dream House is a **professional core plus a didactic overlay**.

The professional core should carry meaning without colour: view type, cut hierarchy,
line type, dimensions, levels, IDs, symbols, scale, orientation, references, source,
revision and status. The didactic overlay should help the reader enter the sheet:
restrained semantic colour, direct labels, plain-language explanations, short evidence
panels and an explicit reading order. If the overlay is removed or printed in grayscale,
the drawing must remain technically intelligible.

The research supports twelve project principles:

1. **Hierarchy before decoration.** Lineweight, position and scale carry the first level
   of meaning; colour is secondary.
2. **One visual cue is not enough for status.** Pair hue with wording, line pattern,
   shape or icon.
3. **Measure at the delivery condition.** Font and stroke quality must be tested at the
   intended print size and at the 1,400 px publication preview, not only in source units.
4. **Use one sheet grammar, not one inflexible composition.** Plans, sections, details
   and schedules share identity regions but need different content allocations.
5. **Label important things directly.** A reader should not repeatedly scan between a
   small mark and a distant legend.
6. **Keep identifiers stable.** Sheet, view, room, opening, grid, decision and conflict
   IDs should survive redesign and translation.
7. **Show information reliability.** Adopted, verified input, open, trial, excluded and
   not-for-construction are different states and must look different.
8. **Do not manufacture detail.** Graphic polish must be proportional to the information
   actually available at the project stage.
9. **Use a small semantic palette.** Name colours by purpose, test their exact foreground
   and background pair, and forbid one-off literals.
10. **Make SVG structure meaningful.** A sheet should have a scalable viewport,
    descriptive metadata, semantic groups and reusable symbols.
11. **Test failure modes.** Review grayscale, reduced size, browser zoom, text overflow,
    collisions and model-space equality.
12. **Adopt incrementally.** A five-sheet pilot and reduced contact set are more reliable
    and economical than a simultaneous rewrite of all active generators.

## 3. Sixteen targeted research studies

### R01 — Line types and lineweight hierarchy

**Primary basis:** [ISO 128-2:2022](https://www.iso.org/standard/83355.html) defines the
scope of line types, designations, configurations, leaders and reference lines for
technical drawings. The [National CAD Standard drafting FAQ](https://www.nationalcadstandard.org/ncs6/faqs.php)
publishes a controlled series of line widths—0.18, 0.25, 0.35, 0.50, 0.70, 1.00,
1.40 and 2.00 mm—and explains that scale and view type determine which one is
appropriate.

**Finding:** a professional drawing does not use arbitrary stroke widths. A small set of
related widths distinguishes cut elements, visible outlines, secondary detail, hidden
information, grids and annotation. The same object may require a different weight in a
plan, section or enlarged detail because its role in that view changes.

**Didactic value:** readers understand a drawing faster when cut or primary geometry is
visually dominant and furniture, hatches and reference grids recede. This is figure–ground
separation, not ornament.

**Dream House adaptation:** use five semantic tiers based on the professional sequence:
0.70, 0.50, 0.35, 0.25 and 0.18 mm as reference plotted widths. Map them to each SVG
output profile and verify the raster result. Do not use a heavy stroke to imply that an
open or trial condition is approved.

**Guardrail:** `vector-effect="non-scaling-stroke"` is a display behaviour, not proof of
a physical plotted width. Print and screen profiles require separate verification.

### R02 — Sheet size, drawing area and information regions

**Primary basis:** [ISO 5457:1999](https://www.iso.org/standard/29017.html) covers sizes
and layout of drawing sheets, while [ISO 9431:1990](https://www.iso.org/standard/17133.html)
covers the placement and content of drawing space, text space and title blocks on
construction drawings. [NCS UDS Module 2](https://www.nationalcadstandard.org/ncs6/pdfs/ncs6_uds2.pdf)
uses a modular drawing area and reduced mock-up sheets to plan content before production.

**Finding:** consistency means predictable regions and margins, not forcing every sheet
into the same panel proportions. A drawing area, text/reference area and document-control
area are distinct responsibilities.

**Didactic value:** predictable regions answer three questions immediately: “What am I
looking at?”, “What evidence or explanation accompanies it?” and “What is the sheet’s
identity and status?”

**Dream House adaptation:** retain a common A-series landscape frame, safe margins,
header and authority/footer region. Use family layouts for plans, elevations/sections,
details, schedules and structural evidence. Create quarter-size contact mock-ups before
issuing full drawings.

**Guardrail:** SVG `viewBox` units are abstract. An A-series aspect ratio does not by
itself establish a physical A3 sheet or a drawing scale. The export profile must define
the physical page and the drawing block must state its scale.

### R03 — Title blocks, identity and revision data

**Primary basis:** [ISO 7200:2004](https://www.iso.org/standard/35446.html) standardizes
data fields in title blocks and document headers to support exchange and reuse.
[ISO 9431:1990](https://www.iso.org/standard/17133.html) places that information within
the construction sheet layout.

**Finding:** the title block is a document-control interface, not a branding panel. Its
essential value is consistent identity: document, title, revision, date, responsibility
and status.

**Didactic value:** a non-specialist should not need to inspect filenames or Git history
to know which sheet, issue and authority state is open.

**Dream House adaptation:** make the following fields mandatory and structured in both
visible SVG and metadata: project, sheet ID, title, revision, issue date, source/model
revision, prepared/reviewed state, scale or `NTS`, decision/conflict references, status
and `construction_authority: false`.

**Guardrail:** a polished title block must never upgrade an unreviewed sheet. The status
field and authority sentence are more important than logo area.

### R04 — Lettering, text size and sentence case

**Primary basis:** [ISO 3098-1:2015](https://www.iso.org/standard/65679.html) sets general
lettering requirements for technical documentation. The
[VA Drawing Deliverable Requirements](https://www.cfm.va.gov/til/bim/DwgDelivRqmts.pdf)
use sans-serif text and cite a 3/32 inch, approximately 2.4 mm, minimum plotted height
for general text, with larger headings. ISO’s public
[graphics directives](https://www.iso.org/home.isoDocumentsDownload.do?t=B97mphuEqSP77WOjHJNmVWGBX4NZYSBUTaOa8qeBYoyj2jIZ3j3ix5_3wHTYn3GR)
show a practical 3.5/2.5/1.8 mm hierarchy. Government accessible-document guidance
recommends [sentence case and avoiding all caps](https://www.gov.uk/guidance/publishing-accessible-documents).

**Finding:** technical lettering needs consistency, adequate plotted height and stable
font metrics. Traditional all-capital drawing text is recognizable, but long all-capital
notes are slower to read and are not required for professionalism.

**Didactic value:** sentence case, short lines and clear levels of heading allow the
owner to scan a sheet without losing technical terms or IDs.

**Dream House adaptation:** use a metric type specification: 3.5 mm panel headings,
2.75 mm primary annotations, 2.5 mm body/dimensions and 2.4 mm absolute minimum for
required text. Use sentence case for titles and prose; reserve uppercase for short status
badges and established identifiers. Test the chosen open font in `resvg` and browsers.

**Guardrail:** no generator may shrink a label below its role minimum to resolve an
overfull panel. Recompose, wrap, key or create a companion sheet.

### R05 — Dimensions, units and associative values

**Primary basis:** [ISO 129-1:2018](https://www.iso.org/standard/64007.html) establishes
general principles for presenting dimensions and tolerances in 2D technical drawings.
The [VA requirements](https://www.cfm.va.gov/til/bim/DwgDelivRqmts.pdf) prohibit
dimension overrides and require dimensions to be associated with the object. The
[USACE A/E/C Graphics Standard](https://www.saj.usace.army.mil/Portals/44/docs/Engineering/AECStandardR5.pdf)
shows the common practice of declaring the drawing unit once and avoiding repetitive unit
suffixes when the context is unambiguous.

**Finding:** a dimension is dependable when it is model-derived, attached to its target,
unambiguous about units and not manually falsified to look correct.

**Didactic value:** consistent placement and a visible unit declaration reduce clutter.
Explicit suffixes remain necessary when units are mixed or when a value is isolated from
its drawing block.

**Dream House adaptation:** source every displayed value from controlled model data;
forbid text overrides; type the relationships between extension lines, dimension line,
ticks and target geometry; state the unit per drawing block; add suffixes for mixed or
exceptional units; preserve project decimal precision.

**Guardrail:** a prettier dimension string cannot resolve a discrepancy. Conflicting
source values must remain a conflict under project precedence rules.

### R06 — Drawing-set organization, sheet IDs and cross-references

**Primary basis:** [NCS UDS Module 1](https://www.nationalcadstandard.org/ncs6/pdfs/ncs6_uds1.pdf)
separates discipline, sheet type and sequence in a stable sheet identifier. The
[NCS content overview](https://www.nationalcadstandard.org/ncs6/content.php) treats set
organization, sheet organization, drafting conventions, symbols, notation and code
information as coordinated modules.

**Finding:** a drawing set is easier to navigate when the identifier reveals discipline
and information type, sequences are stable, and detail/view references resolve to a
specific location.

**Didactic value:** stable IDs create a vocabulary the owner can use in discussion:
“PLN-001”, “ELE-004” and “CF-012” are less ambiguous than visual descriptions.

**Dream House adaptation:** retain the established `DH-<discipline>-<type>-<sequence>`
grammar and current catalog rather than importing NCS numbering. Standardize view IDs,
detail bubbles and reciprocal cross-references within that project grammar.

**Guardrail:** changing the visual system is not permission to renumber active evidence
or break existing links.

### R07 — Layers and semantic grouping

**Primary basis:** [ISO 13567-1:2017](https://www.iso.org/standard/70181.html) states that
layers control visibility and manage/communicate CAD data; layer names represent that
structure. [ISO 13567-2:2017](https://www.iso.org/standard/70182.html) applies the concept
to construction documentation.

**Finding:** layers are information semantics, not merely z-order. A useful layer system
supports visibility, responsibility, checking, exchange and reuse.

**Didactic value:** semantic SVG groups allow a reviewer or future interface to isolate
model geometry, dimensions, furniture, routes, annotations and status without decoding
hundreds of individual elements.

**Dream House adaptation:** use stable `<g>` groups with IDs and `data-layer` roles for
background, reference, model, openings, equipment, dimensions, annotations, status and
sheet control. Add stable `data-model-id` values to model-derived objects.

**Guardrail:** do not imitate a full CAD layer code inside every SVG ID. The project needs
a small interoperable semantic vocabulary, not an expensive taxonomy it will not use.

### R08 — Symbols, grids, scale and orientation

**Primary basis:** the [NCS Symbols module](https://www.nationalcadstandard.org/ncs6/pdfs/ncs6_uds6.pdf)
organizes reference, object, material, line and text symbols. [ISO 8560:2019](https://www.iso.org/standard/72755.html)
covers representation of modular sizes, lines and grids, and
[ISO 128-3:2022](https://www.iso.org/standard/83356.html) covers views, sections and cuts.

**Finding:** symbols work when their meaning, insertion, plotted size and use are stable.
Scales, grids, north/orientation and section/elevation references provide navigation and
must not be reinvented sheet by sheet.

**Didactic value:** a shared symbol plus a short direct label teaches the convention the
first time and becomes faster thereafter. Graphic scales remain useful when a sheet is
resized, provided the scale bar is generated with the view and not pasted decoratively.

**Dream House adaptation:** maintain one reusable SVG symbol library for grid bubbles,
levels, section/elevation marks, doors, windows, stairs, north/orientation, scale bars and
status badges. Include a compact legend only for symbols actually present on the sheet.

**Guardrail:** do not invent look-alike life-safety symbols or imply a valid scale when a
view is `NTS` or published at an uncontrolled size.

### R09 — General arrangement, views, sections and cuts

**Primary basis:** [ISO 7519:2025](https://www.iso.org/standard/89718.html) establishes
general presentation principles for building general-arrangement and assembly drawings.
[ISO 128-3:2022](https://www.iso.org/standard/83356.html) applies general view, section
and cut principles across architectural and civil drawings.

**Finding:** plans, elevations and sections are related but different statements. Cut
geometry, viewed geometry and elements beyond the cut require a deliberate hierarchy;
view labels and reference arrows preserve their relationship.

**Didactic value:** the owner can read a section when cut elements are dominant, levels
align, view direction is explicit and only the relevant background is shown.

**Dream House adaptation:** create family renderers that share symbols and metadata but
encode view-specific hierarchy. Increase the useful scale of sparse elevations and
sections instead of filling their sheets with unrelated notes.

**Guardrail:** a diagrammatic section remains diagrammatic. Added poche or texture must
not claim a wall build-up or structural selection that the source has not established.

### R10 — Project stage, information need and reliability

**Primary basis:** the [RIBA Plan of Work](https://www.riba.org/work/insights-and-resources/riba-plan-of-work/)
organizes outcomes, tasks and information exchanges by stage. The
[BIMForum LOD Specification](https://bimforum.org/resource/lod-level-of-development-lod-specification/)
states that geometry should communicate what downstream users may rely on and what its
limitations are; it does not prescribe one LOD for every stage.
[ISO 19650-1:2018](https://www.iso.org/standard/68078.html) addresses recording,
versioning and organizing information across the asset life cycle in a way proportionate
to project scale and complexity.

**Finding:** more detail is not automatically better. A professional deliverable exposes
what information is required now, its reliability, source, version and permitted use.

**Didactic value:** explicit statuses prevent the owner from confusing an attractive
trial profile, render or preliminary figure with an adopted requirement.

**Dream House adaptation:** use a controlled visual state set: `ADOPTED`, `VERIFIED
INPUT`, `OPEN`, `CONFLICT`, `TRIAL / NOT SELECTED`, `NOT ADOPTED` and `NOT FOR
CONSTRUCTION`. Record the state in both visible text and metadata.

**Guardrail:** `VERIFIED INPUT` means a cited value or check was verified; it does not
mean that design, product or construction is approved.

### R11 — Colour semantics and contrast

**Primary basis:** [WCAG 2.2](https://www.w3.org/TR/WCAG22/) sets a 4.5:1 minimum for
normal text, 3:1 for large text and 3:1 for required graphical objects under the relevant
success criteria. Its [use-of-colour explanation](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color)
requires information not to depend on colour alone. The
[Office for National Statistics colour guidance](https://service-manual.ons.gov.uk/data-visualisation/colours/using-colours-in-charts)
recommends sufficient contrast, distinguishable categories and consistent colour use.

**Finding:** colour is effective for grouping and emphasis, but becomes ambiguous when
many similar hues carry unrecorded meanings. Contrast must be tested as a pair, not
assumed from a colour name.

**Didactic value:** a restrained accent system can immediately distinguish reference,
structure, verified evidence, open gates, conflict and hypotheses. Direct labels reduce
legend lookup.

**Dream House adaptation:** keep primary geometry and text in dark neutral ink; use the
small tested semantic palette in the SVG plan; require wording plus dash, hatch, shape or
icon for every state; generate pale fills only from named tokens; run colour and
grayscale tests.

**Guardrail:** WCAG is a web-accessibility framework, not an architectural plotting
standard. Its contrast criteria are adopted as conservative communication tests, not as
a claim that a drawing set is WCAG-conformant in every delivery context.

### R12 — Diagram reading order and plain-language explanation

**Primary basis:** the [ONS diagram guidance](https://service-manual.ons.gov.uk/content/content-types/diagrams)
calls for a clear starting point, normal reading direction, simple shapes, minimal text
and a genuine user need. Government
[accessible communication guidance](https://www.gov.uk/government/publications/inclusive-communication/accessible-communication-formats)
recommends concise plain language and legible base formats.

**Finding:** a diagram is not clearer merely because it is colourful. It should explain
a relationship that prose alone cannot show and should still have a concise textual
summary.

**Didactic value:** numbered panels, short headings, direct annotation and a left-to-right
or top-to-bottom evidence sequence help non-specialists without diluting technical terms.

**Dream House adaptation:** every multi-panel sheet gets an intentional reading path:
identity/status, primary drawing, dimensions/IDs, evidence or schedule, then open gates.
Use plain technical English, expand uncommon abbreviations locally and keep paragraphs
out of the drawing viewport.

**Guardrail:** “didactic” does not mean adding tutorial prose to every empty area. If a
note does not change interpretation or action, remove it from the sheet.

### R13 — Escape and evacuation communication

**Primary basis:** [ISO 23601:2020](https://www.iso.org/standard/80678.html) establishes
design principles for displayed escape and evacuation plan signs intended for occupants;
its scope explicitly distinguishes those signs from detailed professional drawings for
specialists.

**Finding:** an occupant evacuation sign and an architectural egress-coordination sheet
serve different audiences and authority purposes. Similar green routes and exit symbols
can make a preliminary coordination diagram look operational.

**Didactic value:** routes need strong continuity, clear origin/destination, arrow
direction, direct labels and unobstructed contrast. Required, supplementary and unresolved
routes must be distinguishable without relying on colour.

**Dream House adaptation:** keep `DH-ARQ-DIA-001` explicitly titled as a design/access
coordination diagram, show unapproved exits and conflicts in blocking status, use route
halos and labels, and do not style it as a posted evacuation sign unless a separate
professional process establishes that deliverable.

**Guardrail:** this research does not validate egress, occupant load, travel distance,
exit capacity or a safety-sign installation.

### R14 — Scalable SVG geometry and stroke behaviour

**Primary basis:** the W3C [SVG 2 `viewBox` specification](https://www.w3.org/TR/SVG2/coords.html#ViewBoxAttribute)
defines how a user-space rectangle maps to a viewport. The
[SVG 2 vector-effect specification](https://www.w3.org/TR/SVG2/painting.html#VectorEffects)
defines non-scaling strokes whose widths remain independent of element transformations
and zoom.

**Finding:** `viewBox` is essential for predictable scaling and aspect preservation.
Non-scaling strokes are useful for digital maps/diagrams, but they deliberately decouple
stroke width from geometric transforms.

**Didactic value:** the same sheet can remain usable at full-screen zoom and publication
preview without disappearing grids or grossly enlarged linework.

**Dream House adaptation:** require width, height, `viewBox` and
`preserveAspectRatio="xMidYMid meet"`. Use semantic stroke tokens and choose non-scaling
behaviour by output role/profile. Test print-equivalent weights and screen visibility
rather than applying `vector-effect` indiscriminately to every stroke.

**Guardrail:** the viewport transform is presentation. It cannot become dimensional
authority or conceal a change to model-space coordinates.

### R15 — SVG structure, accessible names and descriptions

**Primary basis:** W3C SVG 2 defines [`g`, `defs`, `symbol`, `use`, `title`, `desc` and
metadata](https://www.w3.org/TR/SVG2/struct.html). The
[SVG Accessibility API Mappings](https://www.w3.org/TR/svg-aam-1.0/) place ARIA labels,
direct-child `title` and direct-child `desc` in the accessible-name/description process.
W3C guidance for [complex images](https://www.w3.org/WAI/tutorials/images/complex/)
calls for a short identification and a longer description of essential information.

**Finding:** a valid XML graphic can still be structurally opaque. Descriptive elements,
semantic groups and reusable definitions make the file more understandable to assistive
technology, code review and future automation.

**Didactic value:** a concise sheet summary can explain the main view, adopted content,
open gates and reading order when the full visual cannot be perceived at once.

**Dream House adaptation:** every root receives `role="img"`, a stable accessible name,
`title`, `desc`, structured metadata and a link to a longer Markdown description when the
sheet is information-dense. Use `defs`/`symbol`/`use` for repeated symbols and semantic
`g` groups for layers and panels.

**Guardrail:** a generic description such as “architectural plan” is insufficient. It
must identify the sheet and its essential purpose without pretending to replace exact
geometry or dimensions.

### R16 — Reduced-size review, visual QA and incremental adoption

**Primary basis:** [NCS UDS Module 4](https://www.nationalcadstandard.org/ncs6/pdfs/ncs6_uds4.pdf)
describes reduced mock-up sets used to allocate views, schedules, notes and details. The
[NCS implementation guidance](https://www.nationalcadstandard.org/ncs6/implementing.php)
recommends step-by-step adoption beginning with easier organizational components and a
pilot project.

**Finding:** sheet quality must be evaluated as a coordinated set. Full-zoom review alone
misses hierarchy, repeated clutter and unreadable thumbnail behaviour; a big-bang rewrite
raises risk and cost.

**Didactic value:** contact sheets reveal whether titles, primary views and status can be
recognized before the reader zooms. Before/after review makes presentation changes
auditable.

**Dream House adaptation:** retain the planned five-sheet pilot, add full-size and
quarter-size contact sheets, grayscale output, 480/800/1,400 px renders, bounding-box and
contrast reports, and model-space equality checks. Promote only after graphic review.

**Guardrail:** visual approval is not architectural approval. The existing source,
decision, conflict, catalog and current-alias processes remain in force.

## 4. Derived Dream House convention

### 4.1 Two-layer communication model

| Professional core — always authoritative for reading | Didactic overlay — helps interpretation | Guardrail |
| --- | --- | --- |
| Dark neutral model geometry and view-specific lineweight | Restrained programme/reference tints | Fill never hides geometry |
| Dimensions, levels, grids, opening/room IDs | Direct plain-language labels | Overlay never replaces a value or ID |
| Standard view, section, elevation and orientation symbols | One-time local legend and short explanation | No invented life-safety symbol |
| Sheet ID, revision, source, scale and status | Clear header hierarchy and reading order | Branding remains subordinate |
| Solid/dashed/dotted/hatch distinctions | Stable semantic colour | Meaning survives grayscale |
| Explicit information state and authority | Concise “why this matters” note where useful | No status inflation |

### 4.2 Recommended type specification

The existing plan should use physical intent first and SVG/raster thresholds second:

| Role | Reference plotted height | Approximate use |
| --- | ---: | --- |
| Sheet title | 5.5–6.0 mm | Sheet identity, one line |
| Sheet/revision ID | 3.75–4.25 mm | Header/footer identity |
| Panel heading | 3.5 mm | Numbered view or evidence panel |
| Primary annotation | 2.75 mm | Main dimensions, room names, warnings |
| Body/dimension | 2.5 mm | Ordinary technical content |
| Minimum required text | 2.4 mm | Secondary caption or symbol ID only |

At the current 1,400 px publication width, critical text should render at approximately
9 px or larger, ordinary body at approximately 8 px or larger, and no required text
below approximately 8 px. Exact conversion depends on the accepted viewBox/export
profile and must be calculated by the linter.

### 4.3 Recommended plotted lineweight sequence

| Semantic role | Reference width | Typical content |
| --- | ---: | --- |
| Cut / principal section profile | 0.70 mm | Elements physically cut; dominant envelope |
| Major outline | 0.50 mm | Walls, openings, main elevation silhouette |
| Primary visible object | 0.35 mm | Equipment, furniture, main leaders |
| Secondary / hidden / dimension | 0.25 mm | Internal detail, dimensions, symbols |
| Grid / projection / background | 0.18 mm | Grids, overhead/reference information |

The SVG theme should retain semantic names and map them to screen and print profiles.
The ratios are the convention; the export acceptance test establishes the rendered
result.

### 4.4 Recommended colour behaviour

The proposed SVG palette is suitable as a pilot because its dark foreground tokens pass
4.5:1 against both current light backgrounds in the audit calculation. Continue to use:

- neutral ink for primary geometry and text;
- teal/blue for reference and structural families;
- green only for a verified check, paired with `VERIFIED INPUT`;
- amber for open gates, paired with `OPEN` and a dashed/dotted boundary;
- red for conflict/hold, paired with an ID and cross-hatch/cross marker;
- purple for trial/reserve, paired with `TRIAL / NOT SELECTED`; and
- brown only for material/finish communication, never status.

The calculated contrast ratios below use the WCAG relative-luminance formula. They apply
only to these exact solid foreground/background pairs:

| Foreground token | On `#F4F0E7` paper | On `#FFFDFA` panel |
| --- | ---: | ---: |
| `#172A32` ink | 13.06:1 | 14.63:1 |
| `#536168` muted | 5.63:1 | 6.31:1 |
| `#1D7480` information | 4.78:1 | 5.36:1 |
| `#3D7186` structure | 4.73:1 | 5.30:1 |
| `#2F7859` verified input | 4.67:1 | 5.23:1 |
| `#8A5A16` open | 5.19:1 | 5.82:1 |
| `#A33F31` conflict | 5.57:1 | 6.24:1 |
| `#66538A` hypothesis | 5.83:1 | 6.53:1 |
| `#74543C` material | 6.00:1 | 6.72:1 |

Every generated tint and every text/background pair still requires an automated test.
Direct labels are preferred to a legend when space permits.

### 4.5 Units and dimensions

- Declare the principal unit once per drawing block.
- Repeat a suffix when units are mixed, a value is isolated or the unit could be missed.
- Generate displayed values from the model and prohibit manual overrides.
- Keep dimension text horizontal where practical and outside dense geometry.
- Protect extension lines, ticks, text and their targets as one typed annotation object.
- State `NTS` when scale is not controlled; never add a decorative scale bar.

### 4.6 Reader paths by sheet family

| Family | Intended reading sequence |
| --- | --- |
| Plan | sheet status → orientation/scale → envelope and circulation → rooms/openings → dimensions → open gates |
| Elevation | sheet status → façade orientation → levels/openings → material/finish note → unresolved interfaces |
| Section | sheet status → cut hierarchy → levels and vertical relationships → assembly hypothesis → gates |
| Detail | status → enlarged condition → numbered components → dimensions → interface risks/holds |
| Schedule | identity/status → grouped rows → quantities/totals → exceptions → source/gates |
| Structural evidence | status → load path/geometry → checked values → result limits → open professional verification |

## 5. Changes this research makes to the SVG improvement plan

| Previous direction | Research-backed refinement |
| --- | --- |
| “A3” inferred from a 1684 × 1191 viewBox | Treat `viewBox` as abstract; define A3 only in the physical export profile and keep the G0 canvas decision explicit |
| Any text down to an 8.5-unit micro role | Set required text by plotted intent: 2.4 mm absolute minimum, approximately 8 px at the accepted preview profile |
| Critical preview text at 8.5 px | Raise the target to approximately 9 px; ordinary required text remains approximately 8 px or larger |
| Arbitrary SVG stroke values | Base semantic tiers on the 0.18/0.25/0.35/0.50/0.70 mm professional sequence and map/test per output profile |
| `vector-effect` mandatory for all geometry | Use it deliberately for screen behaviour; verify print-equivalent lineweights separately |
| Explicit unit on every dimension | Declare units per drawing block; repeat only where ambiguity or mixed units requires it |
| Accessible `title`/`desc` only | Add a longer companion description for information-dense sheets and define an intentional visual reading order |
| Access/egress styling as a route overlay | Explicitly distinguish the coordination diagram from a posted evacuation sign and retain all approval gates |
| Colour legend as principal decoder | Prefer direct labels; keep colour redundant with text, pattern, line type or symbol |
| All-capital technical appearance left open | Use sentence case for prose and reserve uppercase for short states and IDs |

## 6. Source register

All sources were accessed on 2026-08-21.

| Ref. | Issuing body and source | Research use |
| --- | --- | --- |
| S01 | ISO, [ISO 128-2:2022](https://www.iso.org/standard/83355.html) | Lines, leaders and reference-line scope |
| S02 | ISO, [ISO 128-3:2022](https://www.iso.org/standard/83356.html) | Views, sections and cuts |
| S03 | ISO, [ISO 129-1:2018](https://www.iso.org/standard/64007.html) | Dimension-presentation principles |
| S04 | ISO, [ISO 5457:1999](https://www.iso.org/standard/29017.html) | Sheet size and layout scope |
| S05 | ISO, [ISO 7200:2004](https://www.iso.org/standard/35446.html) | Title-block and header data fields |
| S06 | ISO, [ISO 9431:1990](https://www.iso.org/standard/17133.html) | Drawing/text/title-block regions |
| S07 | ISO, [ISO 3098-1:2015](https://www.iso.org/standard/65679.html) | Technical lettering |
| S08 | ISO, [ISO 7519:2025](https://www.iso.org/standard/89718.html) | Architectural general-arrangement presentation |
| S09 | ISO, [ISO 8560:2019](https://www.iso.org/standard/72755.html) | Modular lines and grids |
| S10 | ISO, [ISO 13567-1:2017](https://www.iso.org/standard/70181.html) | CAD layer principles |
| S11 | ISO, [ISO 19650-1:2018](https://www.iso.org/standard/68078.html) | Proportionate information management and versioning |
| S12 | ISO, [ISO 23601:2020](https://www.iso.org/standard/80678.html) | Escape/evacuation sign scope |
| S13 | NIBS/NCS, [content overview](https://www.nationalcadstandard.org/ncs6/content.php) and [UDS Module 1](https://www.nationalcadstandard.org/ncs6/pdfs/ncs6_uds1.pdf) | Drawing-set grammar and IDs |
| S14 | NIBS/NCS, [UDS Module 2](https://www.nationalcadstandard.org/ncs6/pdfs/ncs6_uds2.pdf) and [UDS Module 4](https://www.nationalcadstandard.org/ncs6/pdfs/ncs6_uds4.pdf) | Sheet modules and reduced mock-ups |
| S15 | NIBS/NCS, [drafting FAQ](https://www.nationalcadstandard.org/ncs6/faqs.php) and [implementation guide](https://www.nationalcadstandard.org/ncs6/implementing.php) | Linewidth series and incremental adoption |
| S16 | U.S. Department of Veterans Affairs, [Drawing Deliverable Requirements](https://www.cfm.va.gov/til/bim/DwgDelivRqmts.pdf) | Text, dimensions and deliverable controls |
| S17 | USACE CAD/BIM Technology Center, [A/E/C Graphics Standard](https://www.saj.usace.army.mil/Portals/44/docs/Engineering/AECStandardR5.pdf) | Metric text/scale and unit conventions |
| S18 | RIBA, [Plan of Work](https://www.riba.org/work/insights-and-resources/riba-plan-of-work/) | Stage outcomes and information exchanges |
| S19 | BIMForum, [LOD Specification](https://bimforum.org/resource/lod-level-of-development-lod-specification/) | Geometric reliability and limitations |
| S20 | W3C, [WCAG 2.2](https://www.w3.org/TR/WCAG22/) and [use of colour](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color) | Contrast and redundant visual encoding |
| S21 | W3C, [SVG 2 structure](https://www.w3.org/TR/SVG2/struct.html), [`viewBox`](https://www.w3.org/TR/SVG2/coords.html#ViewBoxAttribute) and [vector effects](https://www.w3.org/TR/SVG2/painting.html#VectorEffects) | SVG document/scaling/stroke behaviour |
| S22 | W3C, [SVG Accessibility API Mappings](https://www.w3.org/TR/svg-aam-1.0/) and [complex-image guidance](https://www.w3.org/WAI/tutorials/images/complex/) | Accessible names and descriptions |
| S23 | UK Office for National Statistics, [diagram guidance](https://service-manual.ons.gov.uk/content/content-types/diagrams) and [colour guidance](https://service-manual.ons.gov.uk/data-visualisation/colours/using-colours-in-charts) | Reading order, simplicity and colour consistency |
| S24 | UK Government, [accessible documents](https://www.gov.uk/guidance/publishing-accessible-documents) and [communication formats](https://www.gov.uk/government/publications/inclusive-communication/accessible-communication-formats) | Sentence case, plain language and legibility |

## 7. Decision and implementation boundary

This research recommends but does not adopt the project graphic system. SVG-G0 in the
improvement plan should decide:

1. the physical sheet/export profile and whether the existing 1684 × 1191 viewBox is
   retained;
2. the plotted typography and lineweight mappings;
3. the semantic palette and redundant status vocabulary;
4. the professional-core/didactic-overlay contract; and
5. the five-sheet pilot acceptance method.

If adopted, the graphic-system decision must be recorded in the project decision
register. Any resulting scope or cost change must follow the existing cost-control
process. Until then, these are source-grounded proposals only.

## 8. Research definition of done

The research objective is satisfied when the pilot can demonstrate, without changing
architectural geometry, that a professional can still rely on conventional linework,
dimensions, IDs, views and document control; an owner can identify the subject, reading
order, adopted content and open questions with less effort; the sheet remains meaningful
in grayscale and at reduced size; and its SVG structure exposes the same identity,
status and essential description to software.
