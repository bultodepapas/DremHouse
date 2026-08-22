# SVG graphic pilot 04 — P2 wall-family visual review

**Status:** reviewed presentation pilot; not current; not approved for rollout  
**Version:** 0.1  
**Date:** 2026-08-21  
**Source drawing:** `planos/actual/DH-ARQ-DET-003_CURRENT-P2-ACOUSTIC-PARTITION.svg`  
**Source revision:** DET-003-R22 / 0.3-draft-25-P2  
**Pilot drawing:** `planos/piloto_grafico_v0.1/DH-ARQ-DET-003-GP04_P2-WALL-FAMILY-READABILITY-PILOT.svg`  
**Generator:** `dreamhouse/svg/pilot_p2_wall_family.py`  
**Authority boundary:** presentation and annotation only. The pilot is not the current
drawing, changes no wall type, thickness, build-up, scope or cost, closes no conflict or
professional design gate, and has no procurement or construction authority.

## 1. Review outcome

GP04 passes as the fourth graphic-language prototype. It makes the two controlled dry-wall
build-ups and the eight-type D-080 coordination schedule readable at normal review width,
while using pattern, number and text together so material differences do not depend on
colour.

The current R22 sheet already has a strong accessible root and a coherent modern frame.
Its weakness is scale: 59 of 72 text elements fall below 8 effective pixels at the 1,400
px review width, including schedule rows, hold points and layer numbers. GP04 reduces that
count to zero and separates the active schematic D-080 coordination basis from the
performance, product and professional gates that remain open.

GP04 remains presentation evidence only. It does not pass SVG-G0 or SVG-G1, does not
authorise rollout and must not be promoted to `planos/actual/`.

## 2. Changes implemented

- Reused the common 1,684 × 1,191 pilot root, accessible title/description, structured
  metadata, header and no-construction footer.
- Copied 61 source nodes forming the P2-W01A and P2-W01B controlled build-ups into two
  independent uniform sheet transforms; no non-text source coordinate was edited.
- Enlarged inherited layer numbers and dimension strings while retaining `90 mm NOMINAL ·
  89 mm ILLUSTRATIVE SUM` and `200 mm NOMINAL · 198 mm ILLUSTRATIVE SUM`.
- Rebuilt the schedule annotation layer at readable size and retained all eight R22 types,
  nominal values and duties: P2-W01A, P2-W01B, P2-W02, P2-W02S, P2-W03, P2-W04R, P2-W05
  and P2-W06.
- Added separate numbered legends for W01A and W01B. New board, reclaimed concealed board,
  insulated frame and clear cavity are each identified by a pattern and an explicit text
  label.
- Kept the 90 mm wall visibly restricted to same-suite low-risk dry boundaries and the
  200 mm twin-frame wall associated with privacy duty.
- Separated `ACTIVE SCHEMATIC COORDINATION`, `OPEN · DO NOT FREEZE`, no-rating language and
  the no-product/no-booked-saving boundary.
- Added fail-closed source checks for source topology, reference-build-up values and all
  schedule rows before the generator will produce a pilot.
- Generated repeatable colour, grayscale, 480/800/1400/1684 px and before/after review
  files through `dreamhouse/svg/audit.py`.

## 3. Measured comparison at the 1,400 px review width

| Measure | Current R22 | GP04 pilot | Interpretation |
| --- | ---: | ---: | --- |
| Canvas | 1,684 × 1,191 | 1,684 × 1,191 | Shared sheet size retained |
| Visible text elements | 72 | 108 | Schedule and evidence are explicitly separated |
| Effective text below 7 px | 50 | 0 | Tiny source captions and schedule text removed |
| Effective text below 8 px | 59 | 0 | Required pilot text meets the preview floor |
| Minimum effective text size | 5.49 px | 8.06 px | Layer keys are the smallest retained role |
| Accessible root and structured metadata | present | present and extended | Pilot/source identity and authority remain explicit |
| Controlled build-up geometry differences | not applicable | 0 | Exact non-text attribute comparison for 61 copied nodes |

The pilot has more visible text because it adds a redundant layer legend and separates
authority evidence; it does not add wall types or technical requirements.

## 4. Visual review record

### 4.1 Full colour at 1,400 px

Passed for pilot use:

- W01A and W01B build-ups, nominal dimensions and illustrative sums read before prose;
- the type schedule is legible as one eight-row family rather than as fine-print evidence;
- new, reclaimed, insulated and clear layers remain distinct through pattern plus label;
- the same-suite limitation and privacy-duty distinction are locally visible; and
- pilot identity, source basis and no-construction authority remain immediate.

### 4.2 Grayscale at 1,400 px

Passed for pilot use. Board, reclaimed-board, insulated-frame and cavity patterns remain
distinct without hue. Row alternation, lineweight, number keys and explicit material names
preserve the information hierarchy.

### 4.3 Reduced overview at 800 px

Passed as a navigation/overview image. Both build-ups, the eight schedule rows, three lower
evidence panels and the authority footer remain recognisable. Detailed layer and hold-point
text correctly remains zoom content.

### 4.4 Defects found and corrected during the loop

1. The first GP04 render inherited 6.6-unit layer numbers. Seven W01B keys fell below 7 px
   and 45 pilot texts fell below 8 px at the review width. The final adapter enlarges only
   copied text presentation attributes and raises every visible role above 8 px; model
   geometry remains unchanged.
2. Subtle fills in the current sheet could merge in grayscale. The final pilot adds four
   deterministic material patterns and repeats every distinction in the layer-key text.
3. The source sheet visually grouped active thickness values and unresolved performance
   work at similar scale. GP04 places D-080 coordination and open professional gates in
   separate labelled panels.

## 5. Automated checks

Eight GP04 checks pass:

1. every non-text geometry attribute in the 61 copied W01A/W01B source nodes is unchanged;
2. accessible identity, status, source SHA-256, D-080 and no-construction authority are
   explicit;
3. all eight wall IDs, nominal values and duty/limit descriptions are retained;
4. both illustrative sums and room-side-to-room-side layer order are retained;
5. pattern IDs and explicit material labels provide redundant non-colour coding;
6. schematic/open/no-rating/no-product/no-saving authority limits remain visible; and
7. every copied node carries a stable wall-family model reference; and
8. copied model geometry retains non-scaling strokes under the enlarged sheet transforms.

The GP01–GP03 focused checks remain part of the same SVG test set. The 27 current aliases
and their promoted versioned sources remain untouched.

## 6. Known limitations and next batch

- GP04 shows only the controlled W01A and W01B reference build-ups. W02, W02S, W03, W04R,
  W05 and W06 remain schedule entries because their tested or discipline-specific details
  are not selected.
- Nominal thickness does not establish STC/Rw, fire resistance, U-value, wind capacity,
  anchorage, moisture performance or product approval.
- Pattern scale is deterministic in the generated SVG, but cross-browser print and font
  metrics remain rollout gates.
- Collision resolution remains curated; the fail-closed label registry is not yet
  implemented.
- No decision-register or cost-control edit is required: this pilot changes neither scope
  nor cost and books no saving.
- The next pilot should address `DH-EST-E1-001`, the dense structural synthesis sheet,
  before any shared-system rollout proposal.
