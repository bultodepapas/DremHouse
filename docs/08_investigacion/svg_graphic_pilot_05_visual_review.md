# SVG graphic pilot 05 — integrated E1 structural evidence visual review

**Status:** reviewed presentation pilot; not current; not approved for rollout  
**Version:** 0.1  
**Date:** 2026-08-22  
**Source drawing:** `planos/actual/DH-EST-E1-001_CURRENT-SYNTHESIS.svg`  
**Source revision:** E1-001-R01 / 0.3 + E1 0.2  
**Pilot drawing:** `planos/piloto_grafico_v0.1/DH-EST-E1-001-GP05_STRUCTURAL-EVIDENCE-READABILITY-PILOT.svg`  
**Generator:** `dreamhouse/svg/pilot_e1_synthesis.py`  
**Authority boundary:** presentation and annotation only. The pilot is not the current
drawing, changes no structural geometry, calculation result, system status, scope or cost,
closes no conflict or professional design gate, and has no selection, procurement,
fabrication or construction authority.

## 1. Review outcome

GP05 passes as the fifth and final sheet-family prototype defined for the initial graphic
pilot. It retains the seven technical panels and treats the no-construction footer as the
eighth authority block. Narrow component calculations remain visually separate from the
`BLOCKED` status of every system-level design decision.

The current R01 sheet is the strongest structural baseline in the drawing set, but its
compact evidence is difficult at repository-preview width. At 1,400 px, 122 of 144 source
texts fall below 7 effective pixels and 124 fall below 8. GP05 reduces both counts to zero
while retaining the calculation-linked plan, truss, joint, trial foundation, erection and
fire diagrams.

GP05 remains presentation evidence only. It does not pass SVG-G0 or SVG-G1, does not
authorise structural-system selection or rollout and must not be promoted to
`planos/actual/`.

## 2. Changes implemented

- Reused the common 1,684 × 1,191 pilot root, accessible title/description, structured
  metadata, header and no-construction footer.
- Copied 183 source shapes across six technical groups: 86 integrated-plan, 68 reference-
  truss, 10 generic-joint, 5 trial-foundation, 5 erection and 9 fire-sensitivity elements.
- Preserved every child geometry coordinate. Five groups retain identity placement; the
  erection group receives one whole-group `translate(0 -10)` sheet adjustment to clear its
  lower evidence line.
- Rebuilt the nine-row evidence matrix at the shared text-role floor, retaining every
  phenomenon, calculation status, numeric result and `BLOCKED` design result.
- Rebuilt technical labels and five truss metric cards without changing 36.00 × 18.00 m,
  P2 +3.80 m, 8.77 kN/m, the 4.50 m overhang, the six-panel truss geometry, trial sections,
  forces, reactions, interaction, second-order, mass, deflection, joint, base, erection or
  temperature-sensitivity values.
- Shortened repeated in-diagram prose through a status legend and direct keyed labels while
  keeping unresolved gates in the authority block.
- Corrected the source legend's stale `D-040 rooflight` reference to the active D-054
  rooflight provenance already governing the displayed positions. Geometry and diaphragm
  demand remain unchanged; the current R01 source is untouched.
- Added fail-closed checks for source topology, metadata, all evidence rows and every detail
  value before the generator will produce a pilot.
- Generated repeatable colour, grayscale, 480/800/1400/1684 px and before/after review
  files through `dreamhouse/svg/audit.py`.

## 3. Measured comparison at the 1,400 px review width

| Measure | Current R01 | GP05 pilot | Interpretation |
| --- | ---: | ---: | --- |
| Canvas | 1,684 × 1,191 | 1,684 × 1,191 | Shared sheet size retained |
| Visible text elements | 144 | 133 | Repeated prose reduced while values remain |
| Effective text below 7 px | 122 | 0 | Tiny matrix/detail text removed |
| Effective text below 8 px | 124 | 0 | Required pilot roles meet the preview floor |
| Effective text below 9 px | 125 | 122 | Dense body roles intentionally sit at the 8.15 px preview floor |
| Minimum effective text size | 5.65 px | 8.15 px | Shared pilot body minimum achieved |
| Calculation-linked geometry differences | not applicable | 0 | Exact child-attribute comparison for 183 copied shapes |

The remaining sub-9 px effective roles are ordinary body/table text at the common 9.8-unit
sheet role. Titles, critical values, statuses and authority text are larger. An 800 px
render remains an overview; detailed evidence is intentionally read by opening the SVG.

## 4. Visual review record

### 4.1 Full colour at 1,400 px

Passed for pilot use:

- the integrated plan and the calculation-versus-design matrix remain the primary reading;
- all nine matrix rows show calculation status, evidence and `BLOCKED` design independently;
- the reference truss retains restraint, panel-load and illustrative transport-split cues;
- `NOT SELECTED`, `TRIAL ONLY`, `NOT A RATING` and `NOT FOR CONSTRUCTION` remain explicit;
- the four detail panels remain subordinate but readable; and
- sheet identity, source basis and fail-closed authority are immediate.

### 4.2 Grayscale at 1,400 px

Passed for pilot use. Geometry class, lineweight, dash/hatch, badges, direct labels and
repeated `BLOCKED` wording preserve the hierarchy without hue. Passing a narrow component
screen cannot be confused with a released design.

### 4.3 Reduced overview at 800 px

Passed as a navigation/overview image. The integrated plan, evidence matrix, reference
truss, four detail panels and authority footer remain recognisable. Values and gate prose
remain zoom content, as expected for this evidence density.

### 4.4 Defects found and corrected during the loop

1. The first GP05 render placed the enlarged M60 specimen sentence across the upper grid
   bubbles. The final pilot removes that duplicate and retains `7 M60 ROOF` in the status
   legend.
2. Full vertical labels for the P2 edge, hidden frame and D-048 study competed in the narrow
   X=21–36 zone. The final direct labels are shortened to `EDGE · X=21`, `HIDDEN FRAME ·
   X=31.5` and `D-048 CORE`; their full decision context remains in the legend/footer.
3. The erection evidence lines approached the lower panel boundary. The complete copied
   erection geometry is translated upward by 10 sheet units; no child coordinate changes.
4. The combined chord/web trial-section line was tight inside its metric card. The final
   card separates both exact profile strings and keeps `NOT SELECTED` at heading level.
5. The current legend named D-040 although D-054 governs the displayed current rooflight
   positions. The pilot corrects only that editorial provenance reference.

## 5. Automated checks

Eight GP05 checks pass:

1. all six technical groups and 183 copied shapes retain exact source geometry attributes;
2. accessible identity, status, source/input SHA-256 and absence of selection/construction
   authority are explicit;
3. all nine evidence rows retain phenomenon, calculation, evidence and blocked-design data;
4. reference-truss and four detail-panel calculation values are retained;
5. plan dimensions, load-path values and active D-054 provenance are explicit;
6. seven numbered technical panels plus the eighth authority block remain present;
7. every visible text role is at least 9.8 sheet units; and
8. every copied shape has a stable model reference and non-scaling stroke behaviour.

The GP01–GP04 focused checks remain part of the same SVG test set. The 27 current aliases
and their promoted versioned sources remain untouched.

## 6. Known limitations and next batch

- GP05 remains a visual index of E1 screening. It selects no roof, gravity or lateral
  system, member, joint, base, footing, erection method, fire protection or product.
- `PASS*` remains a narrow calculation result. It is not a member release, code check,
  signed design or proof of system adequacy.
- The original E1 input set predates later architectural wall refinements; this pilot does
  not update the structural model or create a PE-1 quantity.
- Cross-browser print/font metrics and automated panel-bound/collision lint remain rollout
  gates.
- No decision-register or cost-control edit is required: this pilot changes neither scope
  nor cost and creates no quantity or booked saving.
- With all five planned pilot families now represented, the next batch should consolidate
  their shared acceptance rules into the fail-closed `dreamhouse.svg.lint` gate before any
  migration of current drawing families.
