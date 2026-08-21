# SVG drawing-system audit and improvement plan

**Status:** proposed implementation plan; no drawing or construction authority
**Version:** 0.2
**Date:** 2026-08-21
**Source:** owner request of 2026-08-21; code and rendered-output audit of the 27
current sheets in `planos/actual/`; statistical audit of the 217 SVG files under
`planos/`; current drawing catalog v1.25; sixteen-topic comparative research in
`architectural_drawing_conventions_research.md`.
**Authority boundary:** this plan changes presentation, SVG engineering and quality
control only. It does not change architectural geometry, programme, structure, cost,
scope, status, open conflicts or professional design gates.

## 1. Outcome

The current drawing set is technically traceable and all 27 current SVG files are valid
XML, but it is not yet one coherent drawing system. At least four visual grammars, three
canvas sizes and two language states coexist. Recent P2 and E1 sheets establish a strong
direction, while several PB, elevation, section and E0 sheets retain older title blocks,
very small text, mixed notation and incomplete SVG metadata.

The recommended outcome is one reusable, fail-closed SVG drawing library that:

- preserves the exact architectural and engineering model values;
- separates model geometry from presentation and annotation;
- uses one sheet frame, typography scale, semantic palette and lineweight hierarchy;
- prevents labels, dimensions, leaders and symbols from obscuring each other;
- emits accessible, deterministic, reviewable and standalone SVG;
- validates readability at the 1,400 px publication-preview width and at full SVG zoom;
- makes hypotheses, open gates and conflicts visually distinct without implying approval;
- creates new versioned issues and promotes them through the existing catalog; and
- leaves every historical SVG untouched.

Implementation should be accepted through a graphic-system decision gate before the
pilot is promoted. Until that gate is passed, the tokens and thresholds in this document
are recommendations, not frozen project requirements.

The proposed system follows a **professional core plus didactic overlay**: conventional
linework, dimensions, IDs, symbols and document control must remain intelligible in
monochrome; restrained colour, direct labels and plain-language evidence panels may make
the same content easier to enter, but never replace its technical grammar. The research
basis and source limitations are recorded in
[`architectural_drawing_conventions_research.md`](architectural_drawing_conventions_research.md).

## 2. Scope and non-scope

### 2.1 In scope

- All 27 current drawing identities listed in `planos/actual/catalog.json`.
- Shared SVG document creation, number formatting, escaping, metadata and accessibility.
- Sheet frames, title blocks, revision/status fields, notes, legends and authority bands.
- Typography, colour, patterns, lineweights, leaders, dimensions, grids and symbols.
- Label placement, text wrapping, collision/keep-out checks and safe margins.
- SVG source readability, deterministic serialization and elimination of float noise.
- Raster-preview generation, visual audit pages and CI quality checks.
- New versioned source issues, manifests, catalog promotion and current aliases.
- Professional technical English for new derived sheets under D-044.

### 2.2 Out of scope

- Moving walls, openings, furniture, equipment, structure or circulation routes.
- Changing dimensions, areas, quantities, decisions, conflicts or design-control values.
- Selecting products, materials, structural systems, member sizes or construction details.
- Closing CF-009, CF-010, CF-011, CF-012 or any other professional design gate.
- Rewriting or normalising preserved historical SVG issues.
- Editing anything under `docs/BORN_Legacy/`.

### 2.3 Graphic-only change contract

Every migrated sheet must demonstrate that the following remain unchanged:

1. model input files and their hashes;
2. world-space coordinates and dimensions;
3. room/opening/equipment/member identifiers and quantities;
4. adopted versus non-adopted status;
5. decision and conflict references;
6. construction-authority value (`false`); and
7. all warnings and open professional gates.

Allowed changes are canvas transforms, panel allocation, annotation placement, text
wrapping, English editorial migration, lineweights, colours, patterns, metadata and
accessibility. If a readability fix appears to require moving a modelled object or
changing a value, stop and open a separate design issue rather than hiding the change in
the SVG refactor.

## 3. Audit method

The audit used four complementary readings:

1. **Governance:** project Constitution, source precedence, open conflicts, language
   policy, current catalog and source-promotion rules.
2. **Code:** 42 `generate_*.py` modules, 12,702 lines of generator code, the P2 and E1
   sheet builders, the current-drawing synchroniser and existing SVG tests.
3. **Static SVG:** XML parsing, root attributes, element counts, IDs, metadata, styles,
   fonts, font sizes, colour literals, coordinate precision and external dependencies.
4. **Rendered output:** all 27 committed PNG previews, reviewed individually and in three
   nine-sheet contact sheets at their publication width.

The audit did not use render imagery as dimensional evidence. The underlying models,
decisions and current manifests remain the authority appropriate to their status.

## 4. Baseline evidence

### 4.1 Strengths to retain

- All 27 current SVG files and all 217 SVG files under `planos/` parse as valid XML.
- No duplicate IDs were detected in the current set.
- No current SVG depends on external images, scripts or linked resources.
- The 27 current SVG/PNG pairs pass the existing provenance, hash and metadata check.
- Current SVG aliases are byte-for-byte copies of explicitly promoted sources.
- P2 and E1 generators already demonstrate accessible roots, embedded metadata,
  semantic classes, deterministic output and explicit `NOT FOR CONSTRUCTION` status.
- Existing geometry and design-rule tests provide a strong base for a presentation-only
  refactor.

### 4.2 Measured inconsistencies

| Measure | Current result | Significance |
| --- | ---: | --- |
| Current SVG sheets | 27 | Controlled implementation scope |
| SVG files under `planos/` | 217 | Historical evidence; do not bulk-rewrite |
| Canvas families | 14 at 1400 × 900; 11 at 1684 × 1191; 2 at 1120 × 720 | Inconsistent scale, margins and preview behaviour |
| Current sheets without complete accessible root | 18 / 27 | Missing `role`, ARIA link, `title` and `desc` |
| Current sheets without document metadata | 18 / 27 | Weak machine-readable sheet identity/status |
| Current sheets without embedded style or `vector-effect` | 18 / 27 | Inconsistent scaling and browser behaviour |
| Current sheets missing `viewBox` | 1 / 27 | Transverse section is not reliably scalable |
| All `planos/` sheets missing `viewBox` | 4 / 217 | Historical issue; only supersede if promoted |
| Text elements in current set | 1,271 | Large annotation surface |
| Effective text below 8 px in 1,400 px previews | 860 / 1,271 (67.7%) | Preview readability is structurally weak |
| Distinct inline hex values in current set | 352 | Palette is uncontrolled and hard to maintain |
| Distinct inline hex values in PB plan | 110 | Similar colours carry unclear or duplicate meaning |
| Current sheets with long float artefacts | 27 / 27 | No canonical numeric serializer |
| Current sheets substantially retaining Spanish | 7 / 27 | Derived-sheet language migration is incomplete |
| Generator `.replace(...)` calls | 44 | Revision and visible-text changes are brittle |

The text-size count is based on the effective size after the 1,400 px publication render.
It does not mean every micro-label must be readable in a gallery thumbnail. It does mean
critical status, dimensions, identifiers and coordination warnings cannot rely on text
that rasterises to approximately 5–7 px.

### 4.3 Confirmed contrast examples

Two PB plan combinations used for small text fail a 4.5:1 normal-text contrast target:

- `#F9F3E8` on `#AA9077`: approximately 2.73:1; and
- `#332923` on `#75583F`: approximately 2.18:1.

The E1 muted text `#627078` on `#F4F0E7` is approximately 4.49:1, effectively on the
threshold and too fragile for the smallest labels. These examples justify semantic
tokens with explicit foreground/background pair tests rather than unrestricted hex
literals.

## 5. Prioritised findings

| ID | Priority | Finding | Required response |
| --- | --- | --- | --- |
| SVG-01 | P0 | Labels and model graphics have no common collision system; dense plans show text over furniture, service symbols and other annotations. | Add measured label boxes, keep-outs, candidate placement and fail-closed collision tests. |
| SVG-02 | P0 | Critical information frequently renders below a useful preview size. | Define type roles and prohibit automatic shrinking below the role minimum. |
| SVG-03 | P0 | Four visual systems and three canvases make the coordinated set look like unrelated projects. | Adopt one A-series landscape digital grammar, a controlled physical export profile, discipline accents and family layouts. |
| SVG-04 | P0 | Refactoring presentation could accidentally alter geometry because geometry and rendering are interleaved. | Add a graphic-only change contract, semantic model IDs and geometry regression checks before rollout. |
| SVG-05 | P1 | Eighteen current sheets lack accessible roots, metadata, embedded style and an explicit stroke-scaling policy. | Make the root, metadata and style mandatory in a shared `SvgDocument`; apply the accepted screen/print stroke profile. |
| SVG-06 | P1 | One current section has no `viewBox`; four historical drawings have the same defect. | Fix through new versioned issues; never patch current aliases or preserved history directly. |
| SVG-07 | P1 | The palette contains hundreds of one-off values and some low-contrast text pairs. | Replace literals with tested semantic tokens and tints. |
| SVG-08 | P1 | Seven current sheets remain substantially in Spanish or mixed notation. | Translate visible derived-sheet text without changing meaning, identifiers or values. |
| SVG-09 | P1 | Title blocks, status bands, sheet IDs and authority warnings differ by generator family. | Use one controlled title/footer component. |
| SVG-10 | P1 | Sparse elevations/sections underuse the canvas while dense plans and schedules compress annotations. | Use family-specific content frames and measured content-bound targets. |
| SVG-11 | P1 | SVG revisions are built through raw strings and 44 replacement calls. | Pass structured `SheetMeta`/model data; prohibit revision-by-string-replacement. |
| SVG-12 | P2 | Every current sheet contains long binary-float strings and many outputs are one unreviewable line. | Add canonical formatting and stable, one-element-per-line serialization. |
| SVG-13 | P2 | Colour carries some status and material distinctions without a redundant line/pattern/text cue. | Pair colour with labels, dash patterns, hatches or icons. |
| SVG-14 | P2 | Current CI validates provenance and XML but not readability, contrast, bounds or visual change. | Add an SVG linter, contact-sheet build and controlled visual review gate. |

## 6. Proposed graphic system

### 6.1 Canonical sheet and safe regions

Use one A-series landscape digital coordinate system for new issues and define its
physical page separately in the accepted export profile. Retaining the strongest current
1684 × 1191 canvas minimizes migration cost; SVG-G0 must confirm whether it remains the
canonical abstract `viewBox` and whether the physical issue is exported as nominal A3
landscape. A `viewBox` is not a millimetre declaration or scale authority.

```text
candidate viewBox: 0 0 1684 1191
sheet margin: 36
header: y=0..104
content frame: y=124..1050
footer / authority band: y=1066..1191
safe content inset: 18 inside each panel
```

The root should retain explicit width and height for deterministic rasterisation and add
`preserveAspectRatio="xMidYMid meet"`. The physical print interpretation and any stated
scale remain sheet-specific; the SVG canvas itself never becomes dimensional authority.

Family layouts should share the frame but allocate content differently:

| Family | Default allocation |
| --- | --- |
| Floor plan | 56–62% plan viewport; 38–44% evidence, legend and open gates |
| Elevation / section | 70–78% enlarged view; 22–30% dimensions, keynotes and status |
| Detail | Two or three measured panels plus one compact authority band |
| Schedule | Full-width table with fixed numeric columns and separated totals/gates |
| Structural evidence | Existing E1 panel grammar, with larger body text and reduced repetition |

No generator may fill unused space by enlarging text or graphics arbitrarily. Conversely,
no generator may shrink critical text to make an overfull panel pass. It must wrap,
reallocate panels or move secondary information to a keyed note region.

### 6.2 Typographic roles

Use one embedded CSS font stack throughout:

```css
font-family: Inter, "IBM Plex Sans", "Liberation Sans", Arial, sans-serif;
```

The pilot must verify the same line breaks in `resvg` and a browser. If fallback metrics
are not stable enough, select and package one open-licence font before rollout rather
than accepting unpredictable label collisions.

| Role | Proposed A3 user-unit size | Rule |
| --- | ---: | --- |
| Sheet title | 23–24 | One line; shorten subtitle, never title |
| Sheet / revision ID | 15–17 | Always visible in header and footer |
| Panel heading | 13–14 | Numbered, consistent baseline |
| Primary annotation | 11 minimum | Approximately 2.75 mm plotted intent; dimensions, room names, key warnings |
| Body / schedule row | 10 minimum | Approximately 2.5 mm plotted intent; ordinary technical content |
| Caption / secondary datum | 9.6 minimum | Approximately 2.4 mm plotted intent; required secondary content |
| Micro-label | 9.6 minimum | Non-critical symbol IDs only; never status or dimension authority |

At 1,400 px preview width, every critical label should rasterise at approximately 9 px
or larger and ordinary required text at approximately 8 px or larger. The linter must
derive the exact threshold from the accepted `viewBox` and export profile. Required text
below 8 px effective size fails the preview lint. Use `tspan`-based wrapping with explicit
line height; do not squeeze text using transforms or `textLength`. Use sentence case for
prose and reserve uppercase for short status badges and established identifiers.

### 6.3 Lineweight hierarchy

Use a semantic lineweight series based on conventional plotted widths. Map the tokens to
the accepted screen and print profiles, with explicit joins and caps. Use
`vector-effect: non-scaling-stroke` deliberately where digital zoom/transform behaviour
requires it; it is not a substitute for verifying plotted widths.

| Token | Reference plotted width | Use |
| --- | ---: | --- |
| `--lw-cut` | 0.70 mm | Cut/envelope geometry and principal section profile |
| `--lw-outline` | 0.50 mm | Major walls, openings and principal structural outline |
| `--lw-primary` | 0.35 mm | Furniture/equipment outline and principal leaders |
| `--lw-secondary` | 0.25 mm | Internal detail, dimensions, treads, mullions and symbols |
| `--lw-grid` | 0.18 mm | Grids, projections and background coordination |

Lineweights express view hierarchy, not certainty. Hypotheses, open items and conflicts
use dash/pattern/marker plus a textual status; they do not receive a unique heavier
“alert” width that could make preliminary content appear selected.

### 6.4 Semantic colour tokens

The strongest existing P2/E1 colours should be consolidated, not expanded. Proposed
base tokens for the pilot are:

| Token | Value | Meaning / restriction |
| --- | --- | --- |
| `--paper` | `#F4F0E7` | Sheet background |
| `--panel` | `#FFFDFA` | Panel background |
| `--ink` | `#172A32` | Primary text and geometry |
| `--muted` | `#536168` | Secondary text; darker than the current borderline muted value |
| `--info` | `#1D7480` | Openings, reference information and discipline accent |
| `--structure` | `#3D7186` | Structural geometry/evidence only |
| `--verified` | `#2F7859` | Verified check only; never design approval |
| `--open` | `#8A5A16` | Open gate text/outline; pale amber tint for fill |
| `--conflict` | `#A33F31` | Conflict, prohibited inference or blocking hold |
| `--hypothesis` | `#66538A` | Reserved/trial/hypothesis geometry |
| `--material` | `#74543C` | Material/finish accent, not status |

Only tokens approved by the theme module may be used. Light tints are generated from
named tokens and used as fills only. Amber should not be used for small text unless the
tested foreground is dark enough. Status may never be conveyed by colour alone:

- verified: green + `VERIFIED` label + solid marker;
- open: amber + `OPEN` label + dotted or dashed border;
- conflict: red + conflict ID + cross-hatch or cross marker;
- hypothesis: purple + `TRIAL`/`RESERVE` label + dashed outline; and
- excluded study: neutral/amber tint + `NOT ADOPTED` wording.

### 6.5 Annotation and collision rules

Every visible text block must be registered with a bounding box and priority:

1. construction-authority/status warnings;
2. conflict and decision identifiers;
3. dimensions, levels and opening IDs;
4. room/zone names;
5. equipment/furniture names;
6. secondary descriptions.

The placement engine should:

- calculate a conservative text box from font role, characters, explicit wrapping and
  chosen font metrics;
- reserve keep-outs for walls, openings, doors/arcs, stairs, equipment, symbols,
  dimensions, panel boundaries and other labels;
- try approved candidates: centred inside, upper-left inside, outside with orthogonal
  leader, keyed note, or legend reference;
- keep a minimum 6-unit gap between text and unrelated strokes;
- add an opaque or 92% paper halo when text must cross a hatch or zone fill;
- route leaders orthogonally and prohibit leaders through text or critical symbols;
- never solve a collision by reducing text below its role minimum; and
- fail generation with sheet ID, element IDs and intersecting boxes if no valid placement
  exists.

Intentional intersections, such as a dimension tick meeting its dimension line, must be
typed relationships rather than blanket collision exceptions.

### 6.6 Layer and z-order convention

Each sheet should emit semantic groups in a fixed order:

```xml
<g id="layer-background" data-layer="background">...</g>
<g id="layer-reference" data-layer="reference">...</g>
<g id="layer-model" data-layer="model-geometry">...</g>
<g id="layer-openings" data-layer="openings">...</g>
<g id="layer-equipment" data-layer="equipment">...</g>
<g id="layer-dimensions" data-layer="dimensions">...</g>
<g id="layer-annotations" data-layer="annotations">...</g>
<g id="layer-status" data-layer="status-and-conflicts">...</g>
<g id="layer-sheet" data-layer="titleblock">...</g>
```

Modelled elements receive stable `data-model-id` values. Status overlays are last so a
conflict cannot be hidden by furniture or fill. Background territory fills must never
cover walls, dimensions or text.

### 6.7 Drawing conventions

- Dimensions use decimal points in visible English derived sheets. Declare the principal
  unit once per drawing block and repeat suffixes wherever units are mixed, isolated or
  could be misread.
- Model coordinates are formatted to at most three decimals; displayed metric dimensions
  normally use two decimals.
- Grid bubbles, section/elevation marks, north/orientation notes, levels, arrows, doors
  and windows use shared symbols from one library.
- Door swings and direction arrows must have their own keep-outs.
- Hatches are quiet enough to preserve text contrast and should not create moire in the
  1,400 px preview.
- Room fills identify programme family; they do not imply material specification.
- Opening colour identifies a void/glazing family; fixed/operable status uses a symbol or
  line pattern as well.
- Furniture and equipment remain visually subordinate to walls, openings and circulation.
- Trial structural profiles always carry `TRIAL / NOT SELECTED` adjacent wording.
- Every sheet has an unambiguous `NOT FOR CONSTRUCTION` footer and authority sentence.
- Access/egress coordination sheets must not look like posted evacuation signs unless a
  separately authorised life-safety deliverable is created.
- Dense sheets receive an essential-information description and intentional reading
  order in addition to root `title`/`desc` metadata.

## 7. Proposed code architecture

Create a small shared package rather than another generator-specific helper collection:

```text
dreamhouse/svg/
  __init__.py
  document.py       # root, metadata, IDs, escaping, canonical serialization
  numbers.py        # finite-value validation and coordinate/dimension formatting
  theme.py          # typography, colours, lineweights, spacing and discipline accents
  primitives.py     # rect, line, path, circle, polygon, text and multiline
  layout.py         # frames, panels, bounds, keep-outs and collision registry
  annotations.py    # dimensions, leaders, callouts, labels and note keys
  symbols.py        # grids, doors, windows, stairs, levels, arrows and status badges
  sheet.py          # header, footer, authority and common family layouts
  lint.py           # static SVG and publication quality checks
```

### 7.1 Core data structures

Use typed, immutable presentation data separate from model dictionaries:

```python
@dataclass(frozen=True)
class SheetMeta:
    sheet_id: str
    revision: str
    title: str
    subtitle: str
    date: str
    source_revision: str
    status: str
    decision_ids: tuple[str, ...]
    conflict_ids: tuple[str, ...]
    construction_authority: bool = False

@dataclass(frozen=True)
class TextBox:
    id: str
    bounds: Bounds
    role: TextRole
    priority: int
    relationships: tuple[str, ...] = ()
```

`SvgDocument` should reject duplicate IDs, non-finite values, missing title/description,
construction authority other than `false`, unknown theme tokens and unescaped attribute
values.

### 7.2 Canonical numeric and XML output

- Reject `NaN`, infinity and scientific notation.
- Round canvas coordinates deterministically, normally to 0.001 user units.
- Strip negative zero and insignificant trailing zeroes.
- Keep displayed dimensions separate from raw coordinate serialization.
- Emit the XML declaration, root metadata and one logical element per line.
- Sort metadata JSON keys and relevant non-geometric attributes.
- Keep geometry order intentional; do not sort elements and break z-order.

This removes strings such as `159.85999999999999` and turns SVG diffs into reviewable
changes.

### 7.3 Remove brittle inheritance

The current chain often produces a predecessor SVG and then changes revisions, titles or
visible labels with `.replace(...)`. Refactor in this order:

1. pass `SheetMeta` and current model values into the renderer;
2. extract reusable symbols and panels from the proven P2/E1 generators;
3. replace translated-text substitution maps with structured English labels;
4. replace SVG-string revision edits with model deltas plus render parameters; and
5. retain current geometry validation independently of the presentation library.

Do not rewrite all 42 generator modules at once. Migrate active sheet families, keep
superseded generators as historical reproduction tools and document their legacy status.

## 8. Sheet-by-sheet treatment plan

The table covers every current drawing identity. `P0` means pilot/blocking, `P1` means
main rollout and `P2` means consolidation after the system is stable.

| Current sheet | Priority | Observed visual/code issue | Planned treatment without geometry change |
| --- | --- | --- | --- |
| `DH-ARQ-PLN-001` ground floor | P0 | Densest architectural sheet; 57 of 102 texts below 7 user units; 110 colour literals; labels compete with workbenches, kitchen modules, furniture and core symbols. | Recompose on A3 frame; retain exact plan transform; reduce programme fills to controlled tints; place room labels before equipment labels; move minor equipment text to keyed notes; protect axis, door swings, stair and opening IDs; add modern footer/metadata. |
| `DH-ARQ-PLN-002` upper floor | P0 | Strongest architectural plan baseline, but small-room labels, fixtures, door arcs and wall/opening annotations remain crowded; much evidence text is below preview size. | Use as architectural style reference; enlarge critical plan labels; give tiny bathroom/wardrobe data keyed notes; run full collision registry; preserve D-080/D-082/D-083 wording and all wall/opening geometry. |
| `DH-ARQ-PLN-CUB-001` roof | P1 | Modern frame direction but incomplete accessible root/style; notes and result text are small relative to a large simple plan. | Add shared root/footer; enlarge rooflights, grid and decision callouts; distinguish adopted rooflights, rear P2 roof and open drainage/structure gates by pattern plus label. |
| `DH-ARQ-SEC-001` longitudinal section | P1 | Legacy 1120 × 720 Spanish sheet; large blank field; no common title/footer or section hierarchy. | Reissue in English on A3; enlarge section; add shared level/dimension symbols and status footer; preserve 21 m void, 15 m P2 and all approximate level wording. |
| `DH-ARQ-SEC-002` transverse section | P0 | Only current sheet without `viewBox`; legacy Spanish; minimal context and inconsistent dimension grammar. | Pilot root repair through a new revision; recompose on A3 with floor/roof levels, high/low-side labels and authority band; retain 0.60 m/18.00 m schematic pitch and open drainage/system status. |
| `DH-ARQ-SEC-CUB-003` daylight | P1 | Underuses the sheet; daylight opening and note block are small; incomplete accessible root. | Enlarge transverse profile and rooflight; use restrained daylight cone/ray convention; place structure, drainage, glare and maintenance gates in a readable side panel; retain hypothesis status. |
| `DH-ARQ-ELE-001` front | P1 | Legacy Spanish title/notes; incomplete metadata; no common footer; façade could use more of the content frame. | Translate editorial text; adopt shared elevation dimensions, levels and footer; enlarge the façade; preserve exactly three legible entrances and all provisional manufacturer/engineering notes. |
| `DH-ARQ-ELE-002` rear | P1 | Very sparse layout; ladder/rescue labels are tiny; limited dimensional context; incomplete root. | Enlarge façade and critical D-082/CF-012 callouts; add opening IDs/levels with collision-safe leaders; keep grade, transfer, safe glass and authority gates explicit. |
| `DH-ARQ-ELE-003` Side A | P1 | Façade is compressed vertically; glazing/worktop text overlaps dense detail; large unused field; incomplete root. | Increase elevation scale; move detailed glazing/worktop notes to keyed callouts; add consistent high/low eave and P2 datums; preserve all D-083 openings and desk datum. |
| `DH-ARQ-ELE-004` Side B | P0 | Same sparse/dense imbalance as Side A; dining-window study could be misread if colour/status is weak. | Pilot family elevation layout; enlarge adopted openings; show dining study only in an explicitly excluded keyed panel, never as façade geometry; preserve solid dining bay. |
| `DH-ARQ-ELE-INT-001` Great Wall | P1 | Legacy Spanish; incomplete root; warm finish dominates while authority and structural relationship are visually secondary. | Translate without altering intent; retain continuous slat rhythm and five openings; add concise D-043/CF-008 cross-reference panel without implying the architectural finish is structural. |
| `DH-ARQ-ELE-INT-002` PB media wall | P1 | Clear concept but separate legacy frame; small schedule text and low-contrast brown-on-brown labels. | Adopt shared frame and tested material tints; enlarge primary TV/view dimensions; move secondary AV/backing/envelope notes to a readable schedule; preserve direct Side B mounting and 4.10 m view. |
| `DH-ARQ-DET-001` ground-floor core | P1 | Core plan occupies a narrow strip; 30 of 43 texts below 9 units; CF-011 can be lost among equal-weight study notes. | Enlarge plan, split notes into verified geometry versus blocking gates, and give CF-011 a dominant conflict panel; preserve SC-01 and all four column coordinates. |
| `DH-ARQ-DET-002` owner priorities | P1 | Good modern frame, but narrative and ladder details are small; three subjects have uneven visual weight. | Retain panel grammar; enlarge the ladder/window interface and edge-truss diagram; shorten prose into keyed notes; keep supplementary-rescue and open-gate wording prominent. |
| `DH-ARQ-DET-003` P2 wall family | P0 | Strong visual system but schedule rows and hold points are too small; hatch and colour differences are subtle at preview width. | Pilot modern detail template; enlarge wall sections and table text; add numbered layer keys and redundant hatch labels; retain all 90/150/200/230 mm nominal, untested statuses. |
| `DH-ARQ-DET-004` P2 hall edge | P1 | Main diagram is clear; small labels and colour-only distinctions weaken the open/retained-edge reading. | Enlarge section and add guard/wall/open-edge pattern conventions; preserve 7.45 m open family frontage, retained suite ends and all CF-010 gates. |
| `DH-ARQ-DET-005` P2 exterior wall | P1 | Assembly is relatively small in a large panel; layer legend and authority text are tiny. | Enlarge build-up; use numbered layers, tested tints and explicit `ILLUSTRATIVE / NOT SELECTED`; preserve 230 mm nominal coordination and open core/product gates. |
| `DH-ARQ-DET-006` PB workstation | P1 | Clear concept but legacy frame/root; side section callouts cluster at sill/worktop; table text is small. | Move to modern detail frame; use shared level/dimension symbols and orthogonal leaders; preserve 0.75 m datum, 30–50 mm gap, independent structure, drainage and seals. |
| `DH-ARQ-DET-007` PB workbenches | P1 | Dense multi-panel sheet; 36 of 45 texts below 8 units; service principles and open gates compete with elevations. | Rebalance panels, enlarge bench modules, use keyed service/ESD notes and a dedicated hold panel; preserve all six-/three-module systems and equipment-clearance warnings. |
| `DH-ARQ-DET-008` P2 bedroom windows | P1 | Good modern direction; lower schedules and gates are small and fixed/operable distinctions need redundant cues. | Enlarge window families; use symbols/patterns for panel operation; increase schedule text; preserve repeated 1.20 m modules and +0.05/+2.95 m datums. |
| `DH-ARQ-SCH-001` window schedule | P0 | 77 of 99 texts below 7 units; table is technically ordered but visually compressed; no common title/footer. | Use full A3 table grid, fixed column widths, right-aligned numeric values, larger rows, grouped PB/P2/rooflight sections and a distinct excluded-study band; preserve all quantities and totals. |
| `DH-ARQ-DIA-001` access/egress | P1 | Strong status logic, but route lines/arrows approach labels and wall geometry; most route evidence is small. | Add route halo/underlay, leader keep-outs and typed intersections; enlarge supplementary-versus-required wording; preserve unapproved exit and CF-011/CF-012 status. |
| `DH-EST-E0-002` structure plan | P1 | Legacy Spanish; trial alternatives and audit text are small/dense; visual hierarchy can make trial profiles look selected. | Reissue in E1 grammar; mark all trial members with hypothesis pattern and `NOT SELECTED`; enlarge structural view and reduce repeated audit prose; retain all E0 limitations. |
| `DH-EST-E0-003` lateral A | P1 | Structural elevation uses a small fraction of the canvas; Spanish audit band; labels crowd bracing lines. | Enlarge elevation; use collision-safe callouts and E1 status tokens; translate editorial text; preserve gravity/lateral distinction and rejected alternatives. |
| `DH-EST-E0-004` Great Wall study | P1 | Large blank upper field; Spanish; trial profiles and load arrows need stronger authority separation. | Enlarge concealed frame; move reactions and profile trials into an explicit evidence panel; retain door clearances and `trial only` status. |
| `DH-EST-E1-001` synthesis | P0 | Best structural baseline, but 122 of 144 texts are below 9 units and several panels are dense at preview size. | Pilot structural template constraints; keep all eight evidence panels but enlarge critical values/status, reduce repeated prose and verify every panel bound; preserve calculation-linked content exactly. |
| `DH-EST-E1-002` vertical continuity | P1 | Strong panel grammar; dense candidate matrix and stair-interface text; many labels below preview size. | Increase matrix row height, shorten repeated reasons through keyed notes and enlarge blocked conditions; preserve four compatible lines, rejected lines and fail-closed status. |

## 9. Automated quality gates

### 9.1 Static SVG lint

Add `python -m dreamhouse.svg.lint` with machine-readable JSON and human Markdown output.
For every promoted source it must verify:

- valid XML and SVG namespace;
- explicit width, height and `viewBox`;
- `role="img"`, `aria-labelledby`, unique `title`/`desc` IDs and non-empty text;
- machine-readable metadata containing sheet, revision, source, status and
  `construction_authority: false`;
- no duplicate IDs, scripts, event handlers, external resources or unsafe links;
- embedded font/style declaration and lineweight/profile rules, including deliberate
  non-scaling-stroke use where applicable;
- finite numeric values, no scientific notation and no coordinate precision beyond the
  configured serializer limit;
- approved theme tokens only;
- normal-text contrast at least 4.5:1 and large-text contrast at least 3:1;
- required semantic layers and stable `data-model-id` attributes;
- no visible text outside safe sheet/panel bounds;
- no unresolved collisions except typed relationships; and
- no critical or required text below the configured effective preview sizes.

### 9.2 Geometry preservation tests

Before changing a sheet family, record a structured geometry baseline from the active
model, not from raster pixels. Compare before/after values for:

- envelope, grids, walls and openings;
- room and programme bounds;
- equipment/furniture coordination envelopes;
- stairs, routes and column reservations;
- roof/eave/level datums; and
- structural nodes, members and trial-profile labels.

The test should ignore canvas transforms, label positions, colour and lineweight. Any
model-space delta fails closed and requires a separate architectural/engineering review.

### 9.3 Render and visual-review build

Add `.github/scripts/build_svg_audit.py` to create, under `.build/svg-audit/`:

- individual PNGs at 480, 800 and 1,400 px width;
- one labelled contact sheet per drawing family;
- grayscale contact sheets;
- a before/after overlay and difference image for each migrated identity;
- a CSV/JSON scorecard for text size, contrast, content bounds and collisions; and
- an HTML index linking the current alias, new source, model evidence and metrics.

The build should use the existing `resvg-py` and Pillow presentation dependencies. Keep
the visual review output untracked unless an issue needs preserved evidence.

### 9.4 Manual acceptance checklist

Automation cannot decide architectural legibility alone. A reviewer must confirm:

- the same architectural story, proportions and programme remain visible;
- no label, fill, hatch, route or note hides relevant model geometry;
- open gates are more visible, never less visible;
- trial or excluded content cannot be mistaken for adopted design;
- red/amber/green/purple semantics still work in grayscale;
- titles, IDs, dimensions and authority are readable at 1,400 px;
- micro-detail remains readable when the SVG is zoomed;
- no browser-font substitution changes line breaks or causes overlap; and
- source, current alias, PNG and manifests agree after promotion.

## 10. Implementation sequence

### WP0 — Freeze the graphic-only baseline

**Size:** S
**Deliverables:** audit command, geometry manifests, current contact sheets, metrics JSON.
**Exit:** all 27 current sheets reproducible; no model change; current sync/check remains green.

### WP1 — Shared SVG foundation

**Size:** M
**Deliverables:** `dreamhouse/svg/` package, type/theme tokens, numeric serializer,
accessible root, title/footer, layers, symbols and linter.
**Exit:** unit tests cover escaping, IDs, metadata, float formatting, theme restrictions,
bounds and collision failures.

### WP2 — Five-sheet pilot

**Size:** M
**Pilot sheets:** `DH-ARQ-PLN-001`, `DH-ARQ-ELE-004`, `DH-ARQ-SEC-002`,
`DH-ARQ-DET-003` and `DH-EST-E1-001`.
**Reason:** these exercise a dense plan, sparse elevation, malformed legacy section,
modern architectural detail and dense structural evidence.
**Exit:** owner/reviewer accepts the graphic language from before/after contact sheets;
all model-space comparisons are identical; no current alias is promoted yet.

### WP3 — Architecture rollout

**Size:** L
**Order:** plans and schedule; elevations and sections; architectural details and access
diagram.
**Exit:** all architecture identities have new versioned sources, complete metadata,
English visible text, no untyped collisions and family acceptance checks.

### WP4 — Structural rollout

**Size:** M
**Order:** E0 sheets into the E1 grammar; E1 typography/bounds refinement.
**Exit:** trial versus verified evidence remains explicit; no member/system appears
selected; calculation-linked tests are unchanged.

### WP5 — Publication and CI

**Size:** S
**Deliverables:** updated source manifests/catalog entries, regenerated aliases/previews,
audit build in CI and updated drawing indexes.
**Exit:** `sync_current_drawings.py --check`, showcase check, full unit tests, SVG lint and
manual 27-sheet contact-sheet review all pass.

### WP6 — Legacy containment

**Size:** S
Mark predecessor generator modules as legacy reproduction paths where appropriate. Do
not modify their preserved outputs. Route all future active issues through the shared SVG
package and document the migration rule for contributors.

## 11. Acceptance metrics

The rollout is complete only when all targets below are met for the newly issued current
set:

| Metric | Target |
| --- | ---: |
| Valid XML | 27 / 27 |
| Explicit `viewBox` | 27 / 27 |
| Accessible root/title/description | 27 / 27 |
| Complete structured metadata | 27 / 27 |
| Required semantic layers | 27 / 27 |
| Duplicate IDs / external dependencies | 0 |
| Non-finite values / long float artefacts | 0 |
| Unapproved colour literals | 0 |
| Critical text below approximately 9 px at 1,400 px render | 0 |
| Required text below approximately 8 px at 1,400 px render | 0 |
| Text contrast failures | 0 |
| Untyped text/geometry collisions | 0 |
| Text outside safe bounds | 0 |
| Substantially Spanish current derived sheets | 0 |
| Model-space geometry differences caused by refactor | 0 |
| Sheets missing explicit `NOT FOR CONSTRUCTION` authority | 0 |
| Current source/alias/PNG/manifest validation | PASS |

No acceptance metric may be met by deleting required coordination information. If a
sheet cannot fit, recompose it or create a controlled companion sheet through the normal
drawing/decision process; do not reduce the text until it disappears.

## 12. Risks and controls

| Risk | Control |
| --- | --- |
| Presentation refactor moves architecture | Model-space geometry baseline; zero-delta gate |
| Cleaner graphics make hypotheses look final | Mandatory status tokens, metadata and authority footer |
| Font fallback creates new overlaps | Pilot cross-render check; package an open font if required |
| Palette change weakens material/program reading | Grayscale and colour review; colour never sole cue |
| One large refactor breaks historical reproduction | Migrate only active families; preserve old generators and outputs |
| More QA increases maintenance cost | Reuse current `resvg-py`/Pillow; stdlib-first SVG package; one lint command |
| New frame reduces plan area | Family layouts and text reallocation; no global one-size content viewport |
| Translation changes meaning | D-044 editorial-only review against current source and IDs |
| Catalog promotion overwrites evidence | New versioned issues first; existing explicit promotion flow unchanged |

## 13. Decision gates and traceability

1. **SVG-G0 — graphic-system approval:** approve or revise the proposed frame, tokens,
   type scale and graphic-only contract. This is a presentation decision, not an
   architectural design change.
2. **SVG-G1 — pilot approval:** review the five before/after pilots and metrics. Reject
   any sheet with a geometry delta or weaker gate visibility.
3. **SVG-G2 — rollout approval:** allow migration of the remaining current identities
   after the pilot passes.
4. **SVG-G3 — promotion:** issue new sources and manifests, update the catalog and run
   the existing synchronisation/presentation workflow.

If G0 adopts the graphic system, record that decision in the project decision register.
If implementation changes scope or cost, record it in the cost-control document. This
audit alone adopts neither and therefore does not modify those registers.

## 14. Definition of done

The project has one coherent SVG drawing system when a contributor can create any active
plan, elevation, section, detail, schedule or structural evidence sheet from the same
document/theme/layout primitives; the generated result passes geometry, XML,
accessibility, bounds, collision, contrast, readability, render and provenance checks;
and a side-by-side review confirms that the architectural subject is unchanged while the
information is clearer, more precise and harder to misread.
