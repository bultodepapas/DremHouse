# SVG graphic pilot 03 — transverse roof-section visual review

**Status:** reviewed presentation pilot; not current; not approved for rollout  
**Version:** 0.1  
**Date:** 2026-08-21  
**Source drawing:** `planos/actual/DH-ARQ-SEC-002_CURRENT-TRANSVERSE.svg`  
**Source revision:** SEC-002-R06 / 0.3-borrador-07-CUBIERTA  
**Pilot drawing:** `planos/piloto_grafico_v0.1/DH-ARQ-SEC-002-GP03_TRANSVERSE-SECTION-READABILITY-PILOT.svg`  
**Generator:** `dreamhouse/svg/pilot_transverse_section.py`  
**Authority boundary:** presentation and annotation only. The pilot is not the current
drawing, changes no architectural geometry or value, closes no conflict or professional
design gate, and has no procurement or construction authority.

## 1. Review outcome

GP03 passes as the third graphic-language prototype. It repairs the only current SVG
without a `viewBox`, translates the derived editorial layer into English under D-044,
and makes the difference between the active provisional D-039 geometry and its open
professional gates immediately visible.

The source section was already legible at full publication width. Its main defects were
structural rather than typographic: no scalable viewport, no accessible document root,
no metadata, one undifferentiated warning and an ambiguous relationship between the P2
floor line and the note about the horizontal P2 ceiling. GP03 addresses those defects
without changing the 11 copied technical-content nodes.

GP03 remains presentation evidence only. It does not pass SVG-G0 or SVG-G1, does not
authorise rollout and must not be promoted to `planos/actual/`.

## 2. Changes implemented

- Added an explicit `1684 × 1191` root with `viewBox`, `preserveAspectRatio`, accessible
  title/description, structured metadata and `construction_authority: false`.
- Copied the source baseline, roof plane, both side walls, P2 floor datum, five source
  annotations and hall-width dimension into one uniform transform; no non-text geometry
  coordinate was edited.
- Added stable `data-model-id` values for the baseline, roof plane, low/high sides, P2
  floor, vertical-zone notes, eave datums and hall-width dimension.
- Translated visible source annotations to professional technical English while retaining
  every numeric value and the reversible-direction warning.
- Added typed direct level markers for `PB reference · +0.00` and `P2 finished floor ·
  approx. +3.80 m`.
- Clarified the inherited P2 note as `PRIVATE P2 ZONE · horizontal ceiling not shown` so
  it cannot be mistaken for the +3.80 m floor line.
- Separated `ACTIVE PROVISIONAL DCV · D-039`, vertical reading and `OPEN · DO NOT FREEZE`
  evidence into three lower panels.
- Reused the GP02 shared document frame and extended it with a small typed level-marker
  primitive.
- Generated repeatable colour, grayscale, 480/800/1400/1684 px and before/after review
  files through `dreamhouse/svg/audit.py`.

## 3. Measured comparison at the 1,400 px review width

| Measure | Current R06 | GP03 pilot | Interpretation |
| --- | ---: | ---: | --- |
| Canvas | 1120 × 720, no `viewBox` | 1684 × 1191 with `viewBox` | Scalable pilot root repaired |
| Visible text elements | 8 | 45 | Evidence is separated from model geometry |
| Effective text below 7 px | 0 | 0 | No sub-7 px text |
| Effective text below 8 px | 0 | 0 | Required pilot text meets the preview floor |
| Minimum effective text size | 15.00 px | 8.15 px | Source was sparse; pilot adds compliant body/caption roles |
| Accessible root and structured metadata | absent | present | Machine-readable identity and authority added |
| Substantially Spanish visible text | yes | no | Editorial-only migration under D-044 |
| Model-space geometry differences | not applicable | 0 | Exact non-text attribute comparison |

The source's high minimum font size is not a quality advantage by itself: it contains
only eight text elements and omits the status/evidence structure introduced by the pilot.
The GP03 minimum belongs to ordinary lower-panel body text; principal section labels and
status headings remain larger.

## 4. Visual review record

### 4.1 Full colour at 1,400 px

Passed for pilot use:

- the single roof plane, 0.60 m transverse rise and low/high-side relationship read first;
- PB, P2 finished-floor and approximate eave datums are locally identifiable;
- the brown P2 floor datum remains subordinate to the principal cut/envelope profile;
- the provisional DCV, vertical interpretation and open gates remain separate; and
- document identity, pilot status and no-construction authority are immediately visible.

### 4.2 Grayscale at 1,400 px

Passed for pilot use. Lineweight, position, panel separation and explicit wording retain
the full reading without hue. The purple and amber states do not depend on colour to
communicate `ACTIVE PROVISIONAL DCV` and `OPEN · DO NOT FREEZE`.

### 4.3 Reduced overview at 800 px

Passed as a navigation/overview image. The title, roof pitch, P2 datum, PB/P2 zones,
three evidence panels and authority footer remain recognisable. Evidence paragraphs are
correctly treated as zoom content.

### 4.4 Defects found and corrected during the loop

1. The inherited `P2 private · horizontal ceiling` note appeared immediately above the
   +3.80 m line and could imply that the floor line represented a ceiling. The final text
   states `horizontal ceiling not shown`; the direct level marker identifies the line as
   the P2 finished floor.
2. The source combined provisional geometry, system selection and rainfall in one amber
   warning. GP03 separates the active provisional D-039 geometry from the open direction,
   system, structure, wind, drainage and building-physics gates.
3. The source had no scalable viewport. GP03 adds one only in the new pilot root; the
   current R06 alias and preserved source remain unchanged.

## 5. Automated checks

Seven GP03 checks pass:

1. the missing source `viewBox` is repaired in the pilot root with explicit aspect-ratio
   behaviour;
2. every non-text geometry attribute in the 11 copied source nodes is unchanged;
3. accessible identity, status, decision references, source SHA-256 and no-construction
   authority are explicit;
4. all source/DCV values and provisional/open statuses remain visible;
5. visible editorial text is English and explicitly states that the P2 ceiling is not
   shown;
6. every copied node has a stable `data-model-id`; and
7. both added level markers declare a typed relationship to their source model datum.

The GP01 and GP02 focused checks also remain part of the SVG test set. The current aliases
and their promoted sources remain untouched.

## 6. Known limitations and next batch

- GP03 remains a diagrammatic section. It selects no roof panel, build-up, structural
  member, ceiling detail, insulation or drainage component.
- The source depicts one low/high direction while D-039 keeps Side A / Side B assignment
  reversible until site, orientation and drainage are known.
- Long binary-float source strings remain preserved to maintain exact source-attribute
  equality. Canonical numeric serialization belongs to the shared renderer rollout.
- Collision resolution remains curated; the fail-closed label registry is not yet
  implemented.
- Cross-browser font metrics remain an acceptance gate.
- The next pilot should address `DH-ARQ-DET-003`, the modern P2 wall-family detail, before
  applying the system to the dense E1 structural synthesis sheet.

