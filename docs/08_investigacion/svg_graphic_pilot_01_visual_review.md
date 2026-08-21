# SVG graphic pilot 01 — ground-floor visual review

**Status:** reviewed presentation pilot; not current; not approved for rollout  
**Version:** 0.1  
**Date:** 2026-08-21  
**Source drawing:** `planos/actual/DH-ARQ-PLN-001_CURRENT-GROUND-FLOOR.svg`  
**Source revision:** PLN-001-R15 / 0.3-draft-37-PB  
**Pilot drawing:** `planos/piloto_grafico_v0.1/DH-ARQ-PLN-001-GP01_GROUND-FLOOR-READABILITY-PILOT.svg`  
**Generator:** `dreamhouse/svg/pilot_ground_floor.py`  
**Authority boundary:** presentation and annotation only. The pilot is not the current
drawing, changes no architectural geometry or value, closes no conflict or professional
design gate, and has no procurement or construction authority.

## 1. Review outcome

GP01 is suitable as the first graphic-language prototype and as evidence for the next
pilot batch. It is not yet suitable for promotion as the current drawing because the
remaining legacy micro-labels, complete colour-token migration and general collision
engine are intentionally deferred.

The strongest improvement is not cosmetic. Eleven long equipment/furniture annotations,
five narrow service-core room labels and one obstructed programme-zone label now use
short plan keys with their complete source wording in a dedicated evidence panel. This
removes the most consequential label/object conflicts while retaining the same plan
information.

## 2. Changes implemented

- Reframed the sheet on the candidate `1684 × 1191` landscape canvas with a consistent
  header, content panels, reading legend and explicit authority footer.
- Added an accessible root, linked `title`/`desc`, structured metadata, source hash,
  status and `construction_authority: false`.
- Copied the promoted source geometry into a single documented canvas transform; no
  source-space coordinate is edited.
- Replaced the principal programme fills with restrained technical, buffer, living and
  kitchen/dining tints.
- Replaced the two confirmed low-contrast label combinations with dark ink and a paper
  halo.
- Increased primary, secondary and opening-label roles without enlarging model objects.
- Replaced dense equipment annotations with `P01–P11` and retained their complete source
  wording in the sidebar.
- Replaced the service-core names/areas with `R01–R05`, preventing sanitary, stair and
  cabinet graphics from covering the room text.
- Relocated the project-car area label as `Z01`, because the vehicle occupies the only
  useful centred label position.
- Relocated `P04` out of the `C1–C6` module row and incorporated both 1.20 m operating-strip
  notes into `P01`/`P04` instead of leaving unreadable duplicate text in the plan.
- Corrected the two remaining visible Spanish appliance labels to `COLD` and `CLEAN`.
- Added a grayscale-readable line/status explanation; colour is explicitly described as
  an entry aid rather than technical authority.

## 3. Measured comparison at the 1,400 px review width

| Measure | Current R15 | GP01 pilot | Interpretation |
| --- | ---: | ---: | --- |
| Canvas | 1400 × 900 | 1684 × 1191 | Candidate common sheet frame |
| Visible text elements | 102 | 154 | Additional readable sidebar evidence, not annotation duplication |
| Effective text below 7 px | 57 | 42 | Fifteen fewer; remaining cases are mostly module/symbol micro-labels |
| Effective text below 8 px | 67 | 48 | Nineteen fewer despite the added sidebar content |
| Minimum primary-label size | not role-controlled | 9.94 px | Meets the pilot target at publication width |
| Minimum secondary-label size | not role-controlled | 8.41 px | Meets the ordinary required-text target |
| Minimum key-label size | not applicable | 8.41 px | Keys remain readable without masking model geometry |
| Minimum opening-label size | not role-controlled | 8.03 px | Meets the pilot preview threshold |
| Distinct six-digit colour literals | 110 | 106 | Only principal semantic colours migrated; full tokenisation remains open |
| Known failing text pairs | 2 | 0 | The two confirmed PB failures are removed |

Effective pilot sizes account for both the model-group transform and the 1,400/1,684
publication reduction. Seven original area/operating-strip text elements are intentionally
hidden only after their complete information is relocated to keyed notes.

## 4. Visual review record

### 4.1 Full colour at 1,400 px

Passed for pilot use:

- title, sheet ID, pilot status and authority boundary are immediately visible;
- primary spaces and the 4.00 m pedestrian axis read before furniture details;
- key tags are locally identifiable and the sidebar sequence is easy to scan;
- opening labels and global/bay dimensions remain attached to the plan;
- the service core no longer contains labels hidden behind fixtures; and
- warm domestic zones remain recognisable without overpowering technical linework.

### 4.2 Grayscale at 1,400 px

Passed for pilot use. Principal enclosure lines, fine reference geometry, dashed
clearance/exclusion envelopes, keys and status wording remain distinguishable. The plan
does not require colour to identify an open envelope or the non-construction status.

### 4.3 Reduced overview at 800 px

Passed as a navigation/overview image. The title, plan massing, principal zones, axis,
keys, panel hierarchy and authority footer remain identifiable. Detailed notes and
module IDs are correctly treated as zoom content rather than thumbnail content.

### 4.4 Defects found and corrected during the loop

1. The first dark footer render inherited the default ink fill and had inadequate
   contrast. Dedicated on-dark text classes corrected it.
2. The enlarged pantry label was still covered by cleaning/cold-storage fixtures. The
   full service core was converted to `R01–R05` instead of forcing labels over symbols.
3. The project-car zone name remained hidden by the car model. It was relocated to `Z01`.
4. `P04` initially covered the `C3/C4` workbench modules. The key was moved into the free
   strip east of the vehicle while its complete wording remained in the sidebar.
5. Two 1.20 m operating-strip notes competed with their new keys. Their complete wording
   was consolidated into `P01` and `P04` and the redundant in-plan strings were removed.

## 5. Automated checks

Four pilot checks pass:

1. every source geometry attribute in all 244 copied top-level content nodes and their
   descendants is unchanged;
2. accessible identity, status, source SHA-256 and no-construction authority are present;
3. every keyed source label remains in the output sidebar and every key remains in the
   plan; and
4. the two known low-contrast PB text colours are absent from pilot text.

The pilot source manifest records the exact current-source and generated-output SHA-256
hashes. The current alias and its R15 source remain untouched.

## 6. Known limitations and next batch

- Forty-two visible text elements remain below 7 effective pixels at 1,400 px. These are
  primarily `R1–R6`, `C1–C6`, appliance abbreviations, equipment micro-labels and stair
  micro-evidence. They require a compact symbol/module schedule, not indiscriminate font
  enlargement.
- The source still carries 106 literal colours because GP01 tokenises only the most
  important semantic surfaces and text pairs. Full palette consolidation should follow
  after the graphic direction is accepted.
- Collision handling is curated for this sheet; a measured, fail-closed label registry
  is not yet implemented.
- Rendering was checked with `resvg` in colour, grayscale and 480/800/1400/1684 px
  outputs. Cross-browser font metrics remain an acceptance gate.
- The next recommended sheet is `DH-ARQ-ELE-004` Side B. Its sparse elevation tests the
  same frame in the opposite condition and provides a safe place to formalise shared
  title/footer, status and callout components before attempting a general plan renderer.

