# Parametric Structural Optimization Workflow

**Status:** active research workflow; no design authority  
**Version:** 0.2
**Date:** 2026-08-12  
**Decisions:** D-046 and D-047
**Source:** owner instruction, canonical E0 inputs, second structural-model audit, and the
external technical sources listed below.

## Outcome

Dream House now has a separate, deterministic structural-exploration layer. It generates
explicit mono-pitch roof-truss geometries, solves them as pin-jointed axial systems,
enumerates the permitted HSS catalogue pairs, and retains a Pareto set instead of naming
one opaque winner. It does not modify `structure_system.json` or select D-019.

The current reproducible run evaluates 144 combinations across M45/M60/M90, four web
patterns, three panel counts, and four depth hypotheses. Every candidate and rejection is
preserved in the JSON companion with an input SHA-256 hash.

Revision 0.2 adds the first E1 gates requested after the initial exploration: rectangular
HSS local slenderness and both principal buckling axes, top-chord bending between truss
nodes, axial–flexural interaction, reduced-Euler member magnification, generic gusset
components, diaphragm demand, elevated-temperature sensitivity, erection/lifting demand,
and base-plate/pad-foundation sensitivity. A calculation may pass its narrow screen while the overall
gate remains blocked by missing project inputs.

## Implemented architecture

1. `truss.py` provides a two-degree-of-freedom axial stiffness solver with validation for
   missing nodes, duplicate members, invalid properties, corrupt vectors, and mechanisms.
2. `truss_grammar.py` generates modified Warren, Pratt, Howe, and crossed-X systems with
   constant or variable depth while keeping the canonical mono-pitch top chord unchanged.
3. `roof_truss_space.json` is the research search-space contract. It references canonical
   modulation IDs rather than duplicating their dimensions.
4. `steel_checks.py` derives the missing weak-axis and local HSS geometry from the declared
   designation, while retaining the catalogue gross area and strong-axis inertia. It
   checks AISC-style compression, compact/noncompact flexure, H1 interaction, member
   second-order sensitivity, and generic bolt/plate/weld components.
5. `optimize_roof.py` applies roof dead/live loads, self-weight, global uplift, vertical
   projections of the E0 combinations, HSS local/biaxial stability, local chord bending,
   reduced-Euler magnification, L/180 deflection, equilibrium checks, catalogue
   enumeration, and Pareto filtering.
6. `systems_checks.py` contains explicit, fail-closed braced-bay, diaphragm,
   fire-temperature, erection/lift, base-plate, and pad-foundation sensitivity functions.
7. `e1_screening.py` coordinates those checks around a neutral M60 Warren specimen and
   publishes the resolved demands and unresolved gates without selecting D-019.
8. `roof_truss_exploration_e0.json`, `e1_structural_screening.json`, and their Markdown
   companions are generated evidence, not authority.
9. `ground_structure.py` uses SciPy/HiGHS linear programming to expose a continuous-area
   lower-bound load-path map. Its SVG is inspiration for new grammars, never a directly
   fabricable result.

The current objectives are all minimized:

- roof-truss mass, including the E0 principal-detail allowance;
- a transparent fabrication proxy equal to member count plus twice the number of
  unconnected diagonal crossings;
- the governing biaxial/local axial–flexural or deflection ratio.

This third objective deliberately retains some heavier candidates with greater screening
reserve. No weighted sum conceals the trade-off.

## Why deterministic enumeration comes first

The current model evaluates only 144 geometry candidates and nine profile pairs per
geometry. Exhaustive enumeration is therefore easier to audit than a stochastic search,
cannot miss a candidate in the declared finite space, and gives exact reproducibility.

The optional `optimization` dependency group prepares three later layers:

- SciPy `milp` or CVXPY/HiGHS for discrete profile/topology and constrained ground-structure
  studies;
- pymoo for larger mixed-variable, multi-objective spaces;
- SALib for Morris/Sobol sensitivity once the uncertain inputs and defensible bounds have
  been approved.

SciPy supports mixed-integer linear optimization and constrained differential evolution.
pymoo supports real, integer, binary, and choice variables in one problem. SALib separates
sampling, model evaluation, and sensitivity analysis, which matches the evaluator wrapper
used here.

## Structural families and interpretation

- **Modified Warren:** few web pieces and alternating diagonals; a strong fabrication
  baseline.
- **Pratt:** gravity-oriented diagonals; uplift reversals must remain in the envelope.
- **Howe:** the opposite orientation, useful as a control under gravity/uplift reversal.
- **Crossed X:** redundant axial paths but more pieces and crossings.
- **Variable-depth truss:** keeps the roof line straight and places more depth near
  midspan, where gravity bending demand is larger.

Vierendeel panels are intentionally excluded from this axial solver. They require member
bending and moment-joint stiffness and must be evaluated as frames. K-trusses, selective X
panels, tapered portal haunches, and a rationalized ground-structure heat map are valid next
extensions after the E1 loading and lateral-system basis is approved.

The first M60 ground-structure run starts from 87 short candidate bars and retains 39
above the declared display threshold under the gravity envelope and an uplift-reversal
probe. The map suggests a variable-depth chord field with asymmetric diagonal orientations
that reverse under uplift. It must be simplified—probably towards Warren/Howe hybrids with
six to eight panels—because the raw LP result contains overlapping paths and too many
member directions for economical fabrication.

## Current E1 screening result

The neutral M60 modified-Warren specimen has six panels, a 1.80 m centre depth, and trial
HSS120×120×6 / HSS100×100×6 chord/web sections. The earlier node-only, one-axis screen
would have retained HSS100 for the chord; local bending plus lateral/member stability now
changes that result. Its current maximum values are:

- 0.696 local-slenderness ratio;
- 0.325 axial ratio and 0.653 combined axial–flexural ratio;
- 12.51 kN·m chord local moment;
- 0.203 compression/reduced-Euler ratio and 1.255 member magnifier;
- 209.8 kN maximum absolute member force;
- 63.2 kN per active trial wall diagonal and a 0.622 L50×5 gross-yield ratio when
  four braced bays share the preliminary longitudinal action;
- 8.77 kN/m preliminary required roof-diaphragm shear flow.
- 0.057 trial base-plate concrete-bearing ratio and 4.1/20.0 mm required/provided plate
  thickness under centred roof-support compression; anchors, shear, moment, grout,
  pedestal, and concrete anchor failure modes remain unresolved.

The generic six-M20 trial gusset components have a 0.387 ratio, but the overall joint is
not resolved because HSS face/wall yielding, punching, shear lag, eccentricity, fatigue,
and seismic detailing depend on the actual joint. At 550 °C the conservative material-only
fire sensitivity ratio is 1.046; this is evidence that a fire strategy matters, not a fire
rating or a protection-thickness calculation.

## Important limitations

The current run is not a complete roof-frame comparison. It still omits columns, portal
action, global three-dimensional/direct-analysis stability, normative site wind and
seismic actions, local wind zones, actual purlin point reactions, HSS joint limit states,
fatigue, connection eccentricity, diaphragm product strength/stiffness and openings,
thermal analysis, corrosion, reinforced-concrete/anchor design, and code compliance.
Parsed nominal HSS geometry is a transparent bridge over the incomplete catalogue, not a
mill-certified section database.

The erection and foundation calculations are demand/sensitivity cases. The former does
not approve lift lugs, crane capacity, splices, temporary bracing, or wind limits. The
latter does not select a footing and excludes settlement, groundwater, passive resistance,
punching, shear, flexure, reinforcement, anchors, and interactions between foundations.

The mass objective is not total structural steel and the fabrication proxy is not money.
Supplier material rates, cutting/drilling/welding hours, connection families, transport
limits, crane picks, coating, and foundation consequences must be added before any cost
optimization.

## Reproduction

```powershell
python -m dreamhouse.structure.optimize_roof
python -m dreamhouse.structure.ground_structure
python -m dreamhouse.structure.e1_screening
python -m unittest discover -s dreamhouse/structure/tests -v
```

Optional research dependencies are isolated from the base model:

```powershell
python -m pip install -e ".[optimization]"
```

## Verified external sources

NSR-10 remains the Colombian regulatory route. The AISC 360-22 equations and current
errata below are used as a transparent technical cross-check and research implementation;
they are not silently substituted for the edition and provisions that the responsible
engineer and authority determine applicable under NSR-10 Title F.

- [Colombian NSR-10 adoption—Decree 926 of 2010](https://www1.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=39255)
- [Minvivienda NSR governance and current update process](https://www.minvivienda.gov.co/viceministerio-de-vivienda/espacio-urbano-y-territorial)
- [Current ANSI/AISC 360 standard page](https://www.aisc.org/aisc/publications/current-standards/aisc-360/)
- [AISC 2022 basic design-value cards for members, connections, stability, and HSS](https://www.aisc.org/aisc/publications/steel-construction-manual/basic-design-values-cards-for-16th-edition/)
- [AISC Design Guide 24, second edition, for complete HSS connections](https://www.aisc.org/modern-steel/news/second-edition-aisc-design-guide-for-hollow-structural-section-connections-now-available/)
- [AISC 360-22 and 303-22 revisions and January 2025 errata](https://www.aisc.org/aisc/publications/revisions-and-errata/)
- [AISC structural-fire engineering resources for Appendix 4](https://www.aisc.org/university-programs/educators/teaching-aids/ta-structural-fire-engineering-introduction-to-steel-framed-buildings/)
- [ANSI/AISC 303-22 erection and temporary-support responsibilities](https://www.aisc.org/globalassets/aisc/publications/standards/a303-22w.pdf)
- [Current Steel Deck Institute standards](https://sdi.org/codes-standards/sdi-standards/)
- [AISI S310 diaphragm standard route](https://sdi.org/codes-standards/related-standards/)

- [SciPy mixed-integer linear programming](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html)
- [SciPy constrained differential evolution](https://docs.scipy.org/doc/scipy-1.16.1/reference/generated/scipy.optimize.differential_evolution.html)
- [pymoo mixed-variable problems](https://pymoo.org/customization/mixed.html)
- [SALib model-wrapping and Sobol workflow](https://salib.readthedocs.io/en/latest/user_guide/basics_with_interface.html)
- [CVXPY mixed-integer solver interfaces](https://www.cvxpy.org/tutorial/constraints/index.html)
- [MILP discrete sizing and topology optimization of trusses](https://doi.org/10.1007/s00158-022-03325-7)
- [AISC Design Guide 14 scope for staggered trusses](https://account.aisc.org/ItemDetail?Category=BOOKS&WebsiteKey=3d6245c2-db4d-4109-b6cf-42c3d4d6897a&iProductCode=D814-02)
- [Warren, Pratt, and Vierendeel behaviour](https://steelconstruction.info/sectors/bridges/design-of-steel-footbridges/)
- [OpenSeesPy elastic beam-column element](https://openseespydoc.readthedocs.io/en/latest/src/elasticBeamColumn.html)
