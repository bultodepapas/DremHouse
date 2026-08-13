# Structural Research Memo — 10 Wise Topics to Improve the E0 Model (English)

**Status:** research input / hypothesis; no design value; nothing here authorizes construction.
**Version:** 0.1 · **Date:** 2026-08-11
**Language:** English (requested by owner)
**Purpose:** improve the structural model (`dreamhouse/structure/`) for the 18 m mono-pitch
nave (Boyacá altiplano, no snow, wind-governed) with a column-free interior and an 18 × 15 m
P2 floor without interior columns.
**Sources:** SCI/steelconstruction.info, ESDEP, AISC, AISC Design Guide 11, Tata Steel ComFlor,
Fielders SlimDek, Building Science Corp (BSD-011, BSI-062), ASCE 7-16 / NSR-10 A.3.

> **Supersession notice — 2026-08-12:** this memo records the state of the first E0
> investigation. Its former three-beam/5.9 t Great Wall result and description of the wall
> as a longitudinal shear core are superseded by D-043 and D-045. The active E0 hypothesis
> uses six continuous beams with a rear overhang, reports approximately 11.6 t for the P2
> Great Wall floor subsystem, and assigns no longitudinal-X resistance to the transverse
> wall. The separate D-047 E1 gate report now screens member local/biaxial stability,
> chord bending, second-order sensitivity, generic joint components, diaphragm demand,
> fire, erection, and foundations without claiming that those systems are resolved. See
> `modelo_estructural_e0.md`, `roof_truss_exploration_e0.md`, and
> `e1_structural_screening.md`.

---

## 1. Stressed skin diaphragm action (cladding as bracing)

Profiled steel sheeting, positively fastened to purlins/rails/frames, acts as a shear
diaphragm (roof = deep plate girder; sheeting = web, braced/sheeted gables = flanges).

- Savings: roof plan bracing eliminated and/or frame sizes reduced; frame sidesway moments
  can drop by large factors depending on relative stiffness (psi = c/k).
- Validity: mechanical fastening (screws, not friction); sheet shear stress ≤ 25% of bending;
  openings < 3% of area (≤15% with detailed calc); end gables braced or sheeted; sheet removal
  is a controlled structural action.
- Fasteners: every corrugation much stiffer than alternate; typical shear resistance ≈ 5–6
  kN/mm sheet thickness (sheet/purlin screws), ≈ 2.5 kN/mm (seams); sheet 0.5–0.7 mm.

**Impact on our model:** the roof + walls can share lateral load with the frame. Our
`bracing_total` is a flat 1.0 t — replace with a real stressed-skin/stiffness-share estimate
and re-run the CERCHA (HEA200 columns may go lighter). The claraboyas b08 (2.4 m openings in a
6 m bay) stay under the 3% opening limit per bay.

## 2. Mono-pitch portal vs truss economy

- Mono-pitch portals are economical only to ≈ 15 m span; at 18 m the truss (or tied portal)
  is the rational choice — confirms our current approach.
- Pinned-base beam-and-column frames are economic only to ≈ 10–12 m; portal frames to ≈ 40 m;
  lattice trusses lighter than portals beyond ≈ 25 m but cost-effective beyond ≈ 50 m
  (fabrication dominates). Our 18 m case is the "borderline" band where truss is justified.
- Eaves haunch ≈ 10% of span; depth from rafter axis to haunch underside ≈ 2% of span;
  column/rafter stiffness ratio ≈ 1.5; column plastic modulus ≈ 50% > rafter.
- Tied portal: reduces eaves spread and moments, but requires 2nd-order analysis (we already
  found the tie is near-inactive for wind sway — consistent with theory: ties act on gravity
  thrust/spread, not same-direction sway).

**Impact:** keep CERCHA as primary candidate; treat PORTICO-T as marginal (documented);
use the haunch proportions (10% span, 2% depth) if a portal is ever retained.

## 3. Wind girder and longitudinal bracing

- Roof wind girder = horizontal truss in the roof plane; depth ≈ span/15; diagonals 34–45°
  (45° ≈ 1.5× deflection of 34°; 63° ≈ 4.5× — keep diagonals steep-to-45°).
- Eaves strut mandatory when roof and wall bracing bays differ; purlins between braced bays
  act as compression struts.
- Equivalent horizontal forces for frame imperfections: Φ₀ = 1/200, EHF = Φ·N_Ed; may be
  neglected when horizontal load > 15% of vertical load.
- Portalised bays: elastic analysis, SLS ≤ h/300, under EHF ≤ h/1000.
- Mid-length vertical bracing preferred over end bracing to limit thermal restraint (long
  36 m building, cold nights → thermal movement matters).

**Impact:** add a wind-girder member to `quantities.py` (≈ span/15 depth truss in first two
bays per end) and replace the flat 1.0 t bracing with a computed weight; document EHF in the
stability section.

## 4. Wind drift limits and sway control

- Practical drift limits: h/150 (metal-clad industrial), h/300 general steel, h/500
  cladding-sensitive; roller-shutter doors/crane rails drive tighter limits. At 7.2–7.8 m
  eaves: h/300 ≈ 24–26 mm; h/200 = 36–39 mm (our current limit).
- Knee braces (diagonals at the knee) control sway and cut column size; side-rail restraint
  needs stays sized for 2.5% of the max compression-flange force; interrupted rails near
  doors cannot restrain columns.
- Fixed bases reduce steel but raise base shear and foundation cost; pinned + braced bays is
  the efficient norm for single-storey (validates our PORTICO-F finding).
- When SLS deflection governs, plastic design gives no ULS advantage — elastic sizing wins.

**Impact:** revisit the H/200 drift assumption → document h/200 as conservative, note h/300
for metal-clad would allow smaller columns (HEA300 range for the portal); keep PORTICO-F as
the portal-frame answer, CERCHA as the truss answer.

## 5. Staggered truss: real design parameters

- Story-high trusses span the full width between exterior columns only; trusses stagger one
  half-module per floor (module ≈ 3.7 m; trusses ≈ 7.3 m apart); floor spans between the
  bottom chord of one truss and the top chord of the next.
- **Truss depth = full storey height** (d/L ≈ 0.13–0.19) — the P2 case (2.4–3.4 m available in
  the wall height) gives an extremely stiff, light truss; columns stay near-axial; whole P2
  acts as a cantilever truss (small drift); foundations = strip footings.
- Floors: 8″ hollow-core spans ≈ 9 m, 10″ ≈ 11 m; deep deck/composite slab alternatives.
- Fire rating achieved by enclosing trusses in the demising walls (gypsum) — no intumescent.
- Our current E0 model uses truss depth = L/16 ≈ 1.12 m — **too shallow vs the real system**;
  this overestimates chord forces and weight.

**Impact:** re-model the staggered P2 floor with **full-depth trusses (≈ 2.4 m)** spanning the
18 m width, staggered, hidden in the re-articulated partition walls; floor panels (deep deck
or hollow-core) span ≈ 6 m between trusses without joists. Expect a weight reduction vs our
13.1 t estimate. This is the single biggest model improvement.

## 6. Residential floor vibration (AISC DG11)

- Walking force ≈ 1.8–2.2 Hz with harmonics at 2/4/6/8 Hz; avoid resonance on low harmonics.
- Criteria: fn ≥ 5 Hz for office/residential (DG11); 8 Hz only for rhythmic activity
  (EN 1990); residential tolerance ≈ 0.2% g (offices 0.5% g); damping β ≈ 0.01 bare, 0.02 +
  ceiling, 0.03–0.05 with full-height partitions.
- fn = 0.18·√(g/Δ) with Δ from sustained load; spans > 12 m are usually vibration-governed;
  **the panel spanning between trusses is the critical element, not the truss itself.**

**Impact:** add a frequency check to the P2 floor: the ≈ 6 m panel between trusses with deep
deck/partitions will give fn well above 5 Hz — verify numerically (target ≥ 5–8 Hz) and report
it in the model instead of assuming compliance.

## 7. Long-span composite floors & deep deck spanning

- Economical ranges: parallel beams to ≈ 14 m; composite with web openings/cellular 10–16 m;
  tapered girders 10–20 m; stub/haunched/composite trusses > 20 m.
- Deep deck: 80 mm to ≈ 4.5 m unpropped; deep deck > 200 mm to ≈ 6–7 m unpropped (9–10 m
  propped); ComFlor 210/225 and SlimDek 210 up to 7 m unpropped / 10 m propped; hollow-core
  9–11 m.
- Slab weight ≈ 47 psf NW / 38 psf LW at 4.5 in; 2-hr fire rating without protection at
  ≈ 5.5 in total slab.

**Impact:** at 6 m truss spacing a deep deck works unpropped; at 7.3 m use hollow-core or
propping. The X = 21 edge (18 m span) should be a composite truss or haunched beam — add to
the alternatives table.

## 8. Seismic coefficients for low-rise steel (NSR-10 A.3 / ASCE 7)

- R factors: steel special moment frames R = 8.0; intermediate 4.5; ordinary 3.0. Braced:
  special CBF 6.0, intermediate 4.0, ordinary 3.25; eccentrically braced 8.0.
- Base shear Cs = SDS/(R/Ie): higher R lowers base shear, but braced/truss systems are stiffer
  (shorter period → may increase spectral demand); low-rise is usually stiffness/drift
  governed, and light roof mass keeps seismic weight low.
- Pinned bases + dedicated braced bays = efficient norm; fixed bases raise base shear and
  foundation demands; chevron CBFs have unbalanced-post-buckling issues.
- 2nd-order effects sensitive to imperfections/tapering in pitched portal frames.

**Impact:** replace our `cs = 0.1` hypothesis with an R/Cd factor per system (CERCHA as braced
system, R ≈ 4–6 per NSR-10) once the municipality is known; document that braced CERCHA may
attract more base shear than a moment portal despite lower seismic weight.

## 9. Steel weight & cost benchmarks (validating our targets)

- Portal frames most economical to ≈ 50 m; minimum unit cost at 30–35 m span; frames at
  6–10 m (usually 8 m) spacing.
- Frame weights: **30–40 kg/m² GIFA at low eaves (4–8 m)**; **40–50 kg/m² at high eaves
  (10–13 m)**; ≈ 20% penalty for high eaves. Example 36 m span × 12 m: ≈ 35 kg/m².
- Cost split: material 30–40%, fabrication 30–40%, erection 10–15% — **minimum tonnage ≠
  minimum cost**.
- Secondary steelwork = 15–25% of total weight; complex/northlight roofs +30–35%.

**Impact:** our CERCHA M60 = 39.4 kg/m² sits inside the 30–50 kg/m² benchmark band for
single-storey (and the total 36.2 t is within the 30–45 t target). The fabrication-vs-material
split confirms we must decide E1 on fabricated cost, not kg.

## 10. Thermal bridging & condensation (cold high-altitude envelope)

- Unbroken steel at the envelope cuts insulation performance by **50–80%** (R-value) and
  creates cold interior surfaces → condensation at near-0 °C nights with a heated interior
  (Building Science BSD-011, BSI-062).
- Fixes: continuous exterior insulation running past members; stand-off brackets; stainless
  fasteners (conductivity < ½ carbon steel); thermal-break elements at penetrations.
- Double-skin systems (liner tray + insulation + outer sheet; composite panels; standing seam)
  keep the insulation layer continuous; purlins/rails are the main bridges → thermal-break
  washers or insulated rail systems at the 7.2–7.8 m eave zone.

**Impact:** coordinate with MEP/envelope: continuous exterior insulation + thermal-break
washers on rails and eave members; this is an envelope rule, not a structural one, but it
affects member placement (avoid through-insulation columns) and is part of the D-039/D-017
coordination set.

---

## Prioritized next steps for the model

1. ✅ **DONE (2026-08-11):** re-modeled the staggered P2 floor with **full-depth trusses
   (≈ 3.0 m = P2 wall height, d/L ≈ 0.167)** + deep-deck panels (5.0 m, no joists) and a
   frequency check ≥ 5 Hz (≈ 14.9 Hz). Result: ≈ 3.8 t of floor steel vs 12.4–17.1 t
   METALDECK (corrected L/240 floor beams), zero interior columns. Ver el modelo
   `dreamhouse/structure/staggered.py`.
2. ⚠️ **SUPERSEDED (2026-08-12):** the former three-beam, 5.9 t Great Wall scheme omitted
   its real rear support condition and incorrectly implied longitudinal shear-core action.
   D-043/D-045 now govern the E0 hypothesis: six continuous beams from X=21.00 to X=36.00,
   supported at X=21.00 and X=31.50 with a 4.50 m rear overhang; approximately 11.6 t for
   the P2 Great Wall subsystem; no longitudinal-X resistance assigned to the wall. These
   remain lower-bound screening quantities, not a selected design.
3. Add a **wind girder** + computed bracing weight and document EHF (topic 3) — the great
   wall simplifies the longitudinal wind girder.
4. Document drift limits h/200 vs h/300 for metal-clad and re-check column sizes (topic 4).
5. Add **R/Cd seismic factors per system** for the CERCHA-vs-portal comparison (topic 8).
6. Re-run with **stressed-skin diaphragm** load share (topic 1) — validate with the engineer.
7. Validate weight targets against the 30–50 kg/m² benchmark at E1 (topic 9) and fold the
   thermal-break envelope rule into the coordination doc (topic 10).

All of the above remain hypotheses for the engineer; nothing here is a frozen requirement.
