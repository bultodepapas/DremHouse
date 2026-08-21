# Visualization control and ChatGPT image prompt kit

**Status:** active; schematic-design communication only; not for construction<br>
**Version:** 0.4<br>
**Date:** 2026-08-21<br>
**Sources:** Project Constitution; D-033, D-039, D-052, D-054, D-056, D-059,
D-063, D-067–D-076; current-drawing catalog; and the six-source current OpenAI research
matrix below<br>
**Supersedes:** visualization control v0.3 for prompt method and wording only; no design,
geometry, scope, or cost change

## Authority

A visualization tests perception, hierarchy, material character, and atmosphere. It does
not define area, dimensions, structure, room count, compliance, cost, procurement, or
construction information. If an image contradicts the governing documents or active
coordinated drawings, the image is wrong.

The stable files under [`planos/actual/`](../../planos/actual/) are the required visual
reference set. Their SVGs remain schematic coordination drawings with exactly the
authority and limitations of their preserved versioned sources. PNGs are previews. An
AI-generated image is lower in precedence than every drawing and project document.

## Research basis — six current official sources

The following sources were reviewed on 2026-08-21. The first is a dated April 2026
production guide for GPT Image 2; the other five are the current official OpenAI product
and API documentation. The research is deliberately limited to primary OpenAI sources
because this kit is intended for ChatGPT Images, not for a model-agnostic prompt contest.

| # | Current source | Finding adopted in this kit |
| ---: | --- | --- |
| 1 | [GPT Image Generation Models Prompting Guide](https://learn.chatgpt.com/cookbook/examples/multimodal/image-gen-models-prompting-guide), 2026-04-21 | Use **photorealistic** explicitly; describe the capture as a real photograph; specify observable framing, light, materials, wear and imperfections; treat lens specifications as a look rather than exact optical simulation. |
| 2 | [Image generation in ChatGPT](https://learn.chatgpt.com/docs/image-generation), current at review | State purpose, subject, setting, composition, visual style and only the relevant framing/material constraints. Use concrete visual language and repeat requirements that must remain fixed. |
| 3 | [Image generation API guide](https://developers.openai.com/api/docs/guides/tools-image-generation), current at review | Prefer the verbs **create**, **draw** or **edit**; use multi-turn editing for refinement; change one item per follow-up. Where an API workflow is used, test composition economically before a final high-fidelity render. |
| 4 | [Images and vision guide](https://developers.openai.com/api/docs/guides/images-vision), current at review | Multiple images can be supplied together, but they consume context and must be selected deliberately. Keep the reference set small and relevant. |
| 5 | [Image inputs in ChatGPT](https://learn.chatgpt.com/docs/image-inputs), current at review | Identify every uploaded image and explain what it controls and how the images relate; never assume the model will infer reference precedence. |
| 6 | [Prompting guide](https://developers.openai.com/api/docs/guides/prompting), current at review | Treat prompts like controlled project artifacts: version them, use representative acceptance checks, review every change and retain a rollback path. |

### Adopted prompt protocol

Every master prompt therefore uses the same information order:

1. **Purpose and reference map:** what the image evaluates and what each numbered drawing
   controls.
2. **Capture:** viewpoint, framing, perspective and visible spatial sequence.
3. **Architecture:** only the programme and geometry that must read in that view.
4. **Photographic reality:** physically plausible daylight, contact shadows, reflections,
   joints, seams, texture, wear and tonal range.
5. **Invariants and exclusions:** the small set of conditions that would make an image
   false if violated.
6. **Output:** one image and its aspect ratio.

Long architectural prompts are justified only because each view reconciles several
drawings and hard constraints. Do not add decorative adjectives, duplicate prohibitions,
exact camera jargon that cannot be visually assessed, or instructions unrelated to the
acceptance checklist. Generate the base composition once, then use surgical edits instead
of repeatedly replacing the whole prompt.

## How to use this kit in ChatGPT Images

1. Start a new chat for each view so instructions from a previous image do not drift into
   the next one.
2. Upload only the reference images listed for that prompt, in the stated order. Four
   well-chosen references are preferable to a large, ambiguous set.
3. Paste the prompt without deleting its geometry or exclusion clauses. Select a
   landscape `16:9` aspect ratio when the interface offers an aspect-ratio control. If an
   API workflow exposes quality, prove composition first at low or medium quality and use
   high quality only for the accepted final composition.
4. Review the result against the acceptance checklist. If one item is wrong, use one
   targeted correction prompt; do not request a broad restyle at the same time.
5. Treat all landscape, furniture, lighting, equipment, and material detail beyond the
   sources as an illustrative visualization hypothesis.

Each prompt names what the references control and what must remain unchanged. Lens values
communicate approximate field of view and perspective only; they are not an assertion that
the generated image obeys an exact physical camera model.

## Current design controls that every relevant view must preserve

- One nominal `18.00 × 36.00 m` rectangular industrial hall and one simple continuous
  mono-pitch roof; no gable, secondary roof, or fragmented volumes.
- A nominal `21.00 m` double-height front zone and a partial upper floor (P2) only within
  the rear `15.00 m`.
- Exactly three legible front entrances: one large project-car door, one central
  pedestrian door, and one large RC/DIY-workshop door.
- One project car and a realistically scaled automotive-lift envelope on Side A; the
  open RC/electronics workshop on Side B. No wall divides the two technical areas.
- One `9.00 m` wall-integrated technical bench beginning at each front interior corner,
  below its respective technical window.
- A clear `4.00 m` perceptual pedestrian axis, with no constructed corridor, furniture,
  vehicle, island, or partition blocking it.
- Two mirrored wall-integrated workstations in the `X=13.00–16.00 m` band, each facing
  an equal side window and reading as permanent house-scale infrastructure.
- The living group in the double-height Side B zone, facing a `100-inch` television
  mounted directly on the Side B perimeter wall. There is no freestanding media wall.
- The independent 12-seat dining group beside the kitchen; the kitchen and rear domestic
  zone sit below P2.
- The Great Wall at `X=31.50 m` reads as one warm timber/acoustic plane with flush service
  doors and a more legible protected-stair portal.
- The shared P2 family centre has one `7.45 m` open internal-balcony frontage with a
  continuous guard. Full-height P2-W04R remains at both bedroom ends; the complete `18 m`
  edge is not open. All four suites remain private and enclosed.
- One large, authentic exposed industrial edge truss at `X=21.00 m`, subject to unresolved
  structural, fire, movement, and guard coordination. Do not multiply it into decorative
  trusses.
- Two separated rooflight events within the double-height zone, one near the centre of
  each longitudinal half. Their positions and dimensions remain coordination hypotheses.
- Dark visible steel in the hall, polished industrial concrete at ground level, restrained
  warm timber, and limited high-impact glazing. Private P2 interiors use smooth, quiet,
  domestic finishes and conceal framing and services.

## Prompt 01 — Mandatory master interior view

### Upload these references in this order

1. [`DH-ARQ-PLN-001_CURRENT-GROUND-FLOOR.png`](../../planos/actual/DH-ARQ-PLN-001_CURRENT-GROUND-FLOOR.png)
2. [`DH-ARQ-PLN-002_CURRENT-UPPER-FLOOR.png`](../../planos/actual/DH-ARQ-PLN-002_CURRENT-UPPER-FLOOR.png)
3. [`DH-ARQ-SEC-001_CURRENT-LONGITUDINAL.png`](../../planos/actual/DH-ARQ-SEC-001_CURRENT-LONGITUDINAL.png)
4. [`DH-ARQ-ELE-INT-001_CURRENT-GREAT-WALL.png`](../../planos/actual/DH-ARQ-ELE-INT-001_CURRENT-GREAT-WALL.png)

### Paste this prompt

```text
Create one photorealistic architectural photograph for schematic-design communication,
captured as if the completed space were photographed on site rather than rendered as CGI.
Image 1 controls the ground-floor layout, Image 2 controls the partial upper floor and open
family balcony, Image 3 controls the longitudinal proportions and heights, and Image 4
controls the Great Wall. Treat the drawings as geometry references, not as graphic style.

Scene and composition: stand just inside the central pedestrian entrance, at a natural
1.65 m eye level, looking straight along the clear central axis toward the rear Great Wall.
Use a level, rectilinear architectural-photography view with a natural wide-angle field of
view, approximately a 24–28 mm full-frame lens. Keep verticals vertical, avoid fisheye
distortion, and preserve the genuine long 36 m depth. Make this single view clearly explain
the sequence technical zone → breathing space → double-height living hall → dining and
kitchen below P2 → Great Wall and protected stair.

Architecture and programme: show one 18 m-wide industrial hall under one continuous
mono-pitch roof. In the front technical band, place the single project car and automotive
lift on the right and the open RC/electronics workshop on the left, with no partition
between them. Keep one 9 m wall-integrated workbench along each side, beginning at its
front interior corner below the technical window. Farther inside, retain the two mirrored
wall-integrated workstations and their equal side windows. Keep the 4 m central axis fully
clear. Place the living group in the double-height Side B zone facing the 100-inch TV fixed
directly to the Side B perimeter wall. Keep the 12-seat dining table independent beside
the kitchen. P2 begins only after the first 21 m; show its guarded 7.45 m open family
balcony between two full-height enclosed suite ends and one large exposed industrial edge
truss. Finish the view with the warm timber/acoustic Great Wall and its flush doors.

Material and light: use honest, economical industrial materials—dark exposed primary steel
with a clear regular-bay rhythm, lightly worn polished concrete, insulated metal envelope,
replaceable timber worktops, powder-coated steel cabinets, and timber concentrated at the Great Wall and
selected domestic elements. Use cool, soft Boyacá highland daylight through the limited
side glazing and the two separated rooflights, balanced by restrained warm task lighting.
Include physically plausible seams, fasteners, contact shadows, restrained reflections,
slight surface variation, and normal wear. Use a natural tonal range without artificial
bloom, excessive sharpening, or perfectly polished CGI surfaces. The image must feel
quiet, inhabited, durable, and exceptionally well proportioned, not like a glossy showroom
or a luxury hotel.

Hard constraints: do not shorten the hall; do not widen P2 or move it to the front; do not
add interior rooms on the open ground floor; do not block the central axis; do not add a
freestanding TV wall; do not open the full 18 m P2 edge; do not add a side stair, extra
columns, rooflights, balconies, vehicles, or decorative structure. No people, text,
dimension strings, labels, logos, or watermark. Produce one landscape 16:9 image, not a
collage, plan, axonometric, cutaway, or mood board.
```

## Prompt 02 — Living room, Side B media wall, and domestic transition

### Upload these references in this order

1. [`DH-ARQ-PLN-001_CURRENT-GROUND-FLOOR.png`](../../planos/actual/DH-ARQ-PLN-001_CURRENT-GROUND-FLOOR.png)
2. [`DH-ARQ-ELE-INT-002_CURRENT-PB-MEDIA-WALL.png`](../../planos/actual/DH-ARQ-ELE-INT-002_CURRENT-PB-MEDIA-WALL.png)
3. [`DH-ARQ-PLN-002_CURRENT-UPPER-FLOOR.png`](../../planos/actual/DH-ARQ-PLN-002_CURRENT-UPPER-FLOOR.png)
4. [`DH-ARQ-DET-004_CURRENT-P2-HALL-EDGE.png`](../../planos/actual/DH-ARQ-DET-004_CURRENT-P2-HALL-EDGE.png)

### Paste this prompt

```text
Create one photorealistic interior architectural photograph for evaluating the Dream House
living zone and its relationship to the open hall, captured as a believable real camera
image rather than polished CGI. Image 1 controls the ground-floor
layout, Image 2 controls the TV wall and furniture relationship, Image 3 controls P2, and
Image 4 controls the open family-balcony edge. Preserve their geometry and do not copy
their drawing graphics or labels.

Scene and composition: place the camera at approximately 1.60 m eye level near the dining
side of the domestic transition, looking diagonally across the double-height living group
toward the Side B perimeter wall. Use a level 28–35 mm architectural-photography view with
verticals vertical. Include enough depth to show the nearby independent 12-seat dining
table, the living group beyond the central route, the adjacent wall-integrated workstation,
the high hall volume, and part of the guarded P2 family balcony above.

Subject: the 100-inch 16:9 television is mounted directly on a warm, matte acoustic field
within the existing Side B exterior wall, above a low accessible 3.40 m AV console. There
is no freestanding wall or room divider. The approximately 4 m sofa, chaise, two chairs,
and rug form one coherent group facing the television while remaining completely outside
the clear 4 m pedestrian axis. The workstation remains a separate permanent 3 m-wide
wall-integrated element under its own equal landscape window. Dining remains an independent
12-seat group beside the kitchen rather than an extension of the media wall.

Material and light: combine dark exposed structural steel, lightly worn polished concrete,
warm timber or slatted acoustic lining at the TV field, robust neutral upholstery, and a
restrained palette of charcoal, warm brown, off-white, and muted green. Use soft overcast
Boyacá daylight, controlled screen reflections, warm localized lighting, realistic material
imperfections, correct contact shadows, restrained reflections, and natural contrast.
Avoid artificial bloom, excessive sharpening, and uniformly perfect surfaces. Keep the
mood domestic and calm inside the large industrial volume.

Hard constraints: keep the television on the Side B perimeter wall; keep the adjacent
workstation and window; keep the central route unobstructed; retain the partial P2 and only
the 7.45 m guarded family opening. Do not invent a media partition, fireplace, extra
glazing, staircase, mezzanine, decorative trusses, suspended ceiling, or luxury finishes.
No people, text, logos, labels, or watermark. Produce one landscape 16:9 image only.
```

## Prompt 03 — P2 family balcony looking into the hall

### Upload these references in this order

1. [`DH-ARQ-PLN-002_CURRENT-UPPER-FLOOR.png`](../../planos/actual/DH-ARQ-PLN-002_CURRENT-UPPER-FLOOR.png)
2. [`DH-ARQ-DET-004_CURRENT-P2-HALL-EDGE.png`](../../planos/actual/DH-ARQ-DET-004_CURRENT-P2-HALL-EDGE.png)
3. [`DH-ARQ-SEC-001_CURRENT-LONGITUDINAL.png`](../../planos/actual/DH-ARQ-SEC-001_CURRENT-LONGITUDINAL.png)
4. [`DH-ARQ-PLN-001_CURRENT-GROUND-FLOOR.png`](../../planos/actual/DH-ARQ-PLN-001_CURRENT-GROUND-FLOOR.png)

### Paste this prompt

```text
Create one photorealistic architectural photograph of the shared P2 family centre as an
internal balcony overlooking the double-height hall, captured as a real built interior
rather than polished CGI. Image 1 controls the upper-floor
rooms and family centre, Image 2 controls the retained enclosed ends and open guarded edge,
Image 3 controls the section, and Image 4 controls the hall below. Use the references as
spatial control for this visualization and do not reproduce their annotations.

Scene and composition: stand inside the furnished P2 family distributor/lounge at natural
eye level, close to but safely behind the open edge, looking diagonally across and down the
36 m hall toward the front doors. Use a rectilinear 24–28 mm architectural-photography
view, with verticals vertical and no fisheye. Frame the open family lounge in the foreground,
the continuous guard and exposed edge truss in the middle ground, and the technical,
breathing, and living zones below in their true longitudinal sequence.

Architecture: the open frontage is one deliberate 7.45 m-wide opening only. It sits between
two full-height, smooth, enclosed suite-end walls; do not open the full 18 m edge. Use one
visually quiet, continuous, non-climbable guard and one large, deep, authentic exposed
industrial truss at the X=21 edge. The four suites remain private behind smooth domestic
walls and acoustic doors. The family area may contain a restrained lounge, fitted library,
and study edge, but it must remain one connected shared room and circulation space. Below,
retain the clear central route, Side B living/TV group, opposite technical zones, and only
one project car.

Material and light: the family level feels refined, warm, and quiet with smooth off-white
walls, timber joinery, acoustic textiles, and durable neutral furniture. The hall remains
honestly industrial with dark exposed steel and polished concrete. Use cool diffuse daylight
from the limited side windows and two separated rooflights, with warm localized light at
the family lounge. Show believable scale, construction joints, contact shadows, restrained
reflections, slight material variation, and normal wear. Avoid artificial bloom and
uniformly perfect surfaces.

Hard constraints: do not turn P2 into a full-width mezzanine or hotel gallery; do not use
glass to close the 7.45 m opening; do not expose corrugated metal, framing, bracing, ducts,
or services inside the private P2 rooms; do not add a second truss, decorative cross-bracing,
an open stair, a balcony outside the hall, or extra rooflights. No people, text, dimensions,
logos, or watermark. Produce one landscape 16:9 image only.
```

## Prompt 04 — Front exterior and three-door identity

### Upload these references in this order

1. [`DH-ARQ-ELE-001_CURRENT-FRONT.png`](../../planos/actual/DH-ARQ-ELE-001_CURRENT-FRONT.png)
2. [`DH-ARQ-ELE-003_CURRENT-SIDE-A.png`](../../planos/actual/DH-ARQ-ELE-003_CURRENT-SIDE-A.png)
3. [`DH-ARQ-ELE-004_CURRENT-SIDE-B.png`](../../planos/actual/DH-ARQ-ELE-004_CURRENT-SIDE-B.png)
4. [`DH-ARQ-PLN-CUB-001_CURRENT-ROOF.png`](../../planos/actual/DH-ARQ-PLN-CUB-001_CURRENT-ROOF.png)

### Paste this prompt

```text
Create one photorealistic exterior architectural photograph for evaluating the Dream House
front identity, captured as if the completed building were photographed on site rather
than rendered as CGI. Image 1 controls the front façade and exactly three openings. Image 2
controls Side A, Image 3 controls Side B, and Image 4 controls the mono-pitch roof and
exactly two separated rooflights. Preserve the drawings' geometry and proportions, not
their linework, colors, text, or graphic style. Treat every landscape element as
illustrative because the actual site is not yet selected.

Scene and composition: show a human-eye-level three-quarter view from the continuous front
concrete apron, far enough away to include the complete 18 m front façade and enough of one
36 m side wall to communicate the building's exceptional length. Use a level rectilinear
architectural-photography view with the natural perspective of an approximately 35 mm
full-frame lens, verticals vertical, no fisheye stretching, and no dramatic tilt. Let the
long side recede naturally without making the front appear wider than the drawing. The
building must read immediately as one sober rectangular industrial hall converted into a
home, not as a conventional house with an attached garage.

Architecture: preserve exactly three front entrances—one large industrial project-car door,
one central pedestrian door, and one equally legible large RC/DIY-workshop door. Preserve
the simple continuous mono-pitch roof, the low-to-high side relationship shown in the
elevations, the restrained side glazing, and only two separated rooflights. Use a continuous
insulated corrugated-metal envelope, crisp dark steel trims, robust industrial doors, a
simple central pedestrian portal, and a continuous drained concrete apron meeting level
grass. Show plausible panel modules, flashings, closures, gutters, downpipes, door tracks,
thresholds, sealant joints, and slab-to-wall contact. Keep the mass calm, repetitive,
economical, and nearly monolithic.

Material and atmosphere: matte medium-grey metal, charcoal frames and doors, subtle warm
timber only at the pedestrian threshold, subtle coating variation, restrained weathering,
and cool overcast Boyacá highland daylight. Use a neutral white balance, soft physically
consistent shadows, believable reflections, contact darkening at joints, and natural tonal
range without artificial bloom, HDR halos, excessive sharpening, or uniformly perfect CGI
surfaces. Use restrained native grass and a few distant highland trees only as atmosphere,
with no claim of actual site conditions. The result should feel durable, quiet, precise,
photographically believable, and buildable rather than glamorous or futuristic.

Invariants and exclusions: keep exactly three front entrances, one continuous mono-pitch
roof, two rooflights, restrained side glazing, one rectangular volume, and the continuous
front apron. Do not add a gable, porch, canopy, dormer, chimney, external balcony, side
stair, extra opening, glass-box façade, exposed domestic room, daily-use vehicle, perimeter
wall, ornamental landscaping, dominant mountain backdrop, or decorative structural
gesture. Do not place the project car outside. No people, signage, text, logos, dimensions,
or watermark. Produce one landscape 16:9 image only, not a collage or alternate option.
```

## Targeted correction prompts

Use only one correction at a time in the same image conversation. Each instruction is an
edit request: it must preserve the current camera, crop, lighting, color, and all unrelated
content.

### Restore the master depth and section

```text
Edit only the spatial proportions. Restore the long 18 × 36 m single-hall volume, keep the
first 21 m double height, and keep P2 only over the rear 15 m. Restore a clear uninterrupted
central axis from the pedestrian entrance to the Great Wall. Keep the camera, crop,
materials, lighting, furniture, and every correctly placed element exactly unchanged.
```

### Restore the P2 family edge

```text
Edit only the P2 edge facing the hall. Create one 7.45 m open internal-balcony frontage with
a continuous guard between two full-height enclosed suite-end walls. Remove any glazing or
wall across that opening, but do not open the complete 18 m edge. Keep the single exposed
edge truss and preserve every other element, including camera, light, materials, and rooms.
```

### Restore the technical band

```text
Edit only the front technical band. Keep one project car and lift on Side A and the open
RC/electronics workshop on Side B, with no dividing wall. Restore one 9 m wall-integrated
bench along each side, beginning at its front interior corner below its technical window.
Keep the 4 m central pedestrian axis empty and preserve the camera and all later zones.
```

### Restore the Side B media wall

```text
Edit only the living and media arrangement. Mount the 100-inch television directly on the
existing Side B perimeter wall above the low AV console; remove any freestanding media wall.
Keep the living furniture facing that wall and outside the central axis. Preserve the nearby
wall-integrated workstation, dining group, camera, materials, lighting, and all other areas.
```

### Restore the three-door front façade

```text
Edit only the front façade. Restore exactly three openings: two equally legible large
industrial doors flanking one central pedestrian door. Remove every additional door,
window, porch, canopy, sign, or vehicle from the front. Preserve the mono-pitch roof,
continuous metal envelope, concrete apron, camera, crop, lighting, and side elevation.
```

### Remove invented features

```text
Remove only the invented architectural features: extra rooflights, extra columns or trusses,
side stairs, exterior balconies, secondary roofs, added rooms, added vehicles, signage, and
decorative glazing. Reconstruct the affected surfaces consistently with the existing hall.
Keep the approved geometry, camera, crop, lighting, palette, and all unrelated content
exactly unchanged.
```

### Restore photographic realism

```text
Edit only the photographic realism. Preserve the exact building geometry, openings, roof,
camera position, crop, object placement, landscape extent, and lighting direction. Replace
uniformly perfect CGI surfaces with physically plausible panel seams, fasteners, flashings,
sealant joints, subtle coating variation, restrained weathering, correct contact shadows,
believable reflections, and a natural camera tonal range. Remove artificial bloom, HDR
halos, excessive sharpening, plastic textures, and dramatic cinematic grading. Do not add,
remove, or relocate any architectural or landscape element.
```

## Acceptance checklist

Reject or correct the image if any applicable answer is **no**.

- [ ] Does the building read as one long `18 × 36 m` hall rather than a compressed room?
- [ ] Is there one continuous mono-pitch roof and no unapproved secondary volume?
- [ ] Is P2 confined to the rear `15 m`, leaving approximately `21 m` double height?
- [ ] Are there exactly three front entrances?
- [ ] Are the project car/lift and RC workshop on opposite sides of one open technical band?
- [ ] Do both `9 m` technical benches begin at the front corners below their side windows?
- [ ] Is the `4 m` central axis clear?
- [ ] Are both mirrored workstations present and outside the dirty technical strip?
- [ ] Is the living group oriented to the TV directly on the Side B perimeter wall?
- [ ] Are dining and kitchen independent of any invented media partition?
- [ ] Does the Great Wall read as one continuous warm rear plane with flush doors?
- [ ] Is only the `7.45 m` family frontage open, with both bedroom ends still enclosed?
- [ ] Is there only one large exposed edge truss?
- [ ] Are there exactly two separated rooflight events when the roof is visible?
- [ ] Is glazing limited and intentional rather than a transparent-box treatment?
- [ ] Are private P2 interiors smooth and domestic rather than exposed corrugated metal?
- [ ] Do construction joints, contacts, shadows, and reflections look physically plausible?
- [ ] Are materials naturally varied rather than uniformly perfect or plastic-looking?
- [ ] Is the image free of artificial bloom, HDR halos, fisheye distortion, and excessive
      sharpening?
- [ ] Are there no labels, dimensions, logos, watermark, or invented programme elements?

## Publication rule

Renderings may be stored only as versioned visual evidence with their prompt version,
reference list, generation date, and a visible statement that they are schematic and not
for construction. They must not replace technical drawings in `planos/actual/`.

If an issued drawing changes a required view, first promote that drawing through the
current-drawing catalog and regenerate its stable aliases. Then update this prompt kit,
issue a new version, and regenerate the affected render. Never edit a prompt silently to
override an unresolved conflict or a current drawing.
