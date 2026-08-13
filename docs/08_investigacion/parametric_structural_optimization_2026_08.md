# Parametric Structural Optimization Workflow

**Status:** active research workflow; no design authority  
**Version:** 0.1  
**Date:** 2026-08-12  
**Decision:** D-046  
**Source:** owner instruction, canonical E0 inputs, second structural-model audit, and the
external technical sources listed below.

## Outcome

Dream House now has a separate, deterministic structural-exploration layer. It generates
explicit mono-pitch roof-truss geometries, solves them as pin-jointed axial systems,
enumerates the permitted HSS catalogue pairs, and retains a Pareto set instead of naming
one opaque winner. It does not modify `structure_system.json` or select D-019.

The first reproducible run evaluates 144 combinations across M45/M60/M90, four web
patterns, three panel counts, and four depth hypotheses. Every candidate and rejection is
preserved in the JSON companion with an input SHA-256 hash.

## Implemented architecture

1. `truss.py` provides a two-degree-of-freedom axial stiffness solver with validation for
   missing nodes, duplicate members, invalid properties, corrupt vectors, and mechanisms.
2. `truss_grammar.py` generates modified Warren, Pratt, Howe, and crossed-X systems with
   constant or variable depth while keeping the canonical mono-pitch top chord unchanged.
3. `roof_truss_space.json` is the research search-space contract. It references canonical
   modulation IDs rather than duplicating their dimensions.
4. `optimize_roof.py` applies roof dead/live loads, self-weight, global uplift, vertical
   projections of the E0 combinations, Euler screening, L/180 deflection, equilibrium
   checks, catalogue enumeration, and Pareto filtering.
5. `roof_truss_exploration_e0.json` and `.md` are generated evidence, not authority.
6. `ground_structure.py` uses SciPy/HiGHS linear programming to expose a continuous-area
   lower-bound load-path map. Its SVG is inspiration for new grammars, never a directly
   fabricable result.

The current objectives are all minimized:

- roof-truss mass, including the E0 principal-detail allowance;
- a transparent fabrication proxy equal to member count plus twice the number of
  unconnected diagonal crossings;
- the governing axial/Euler or deflection ratio.

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

## Important limitations

The current run is not a complete roof-frame comparison. It omits columns, portal action,
longitudinal stability, diaphragm and collectors, local wind zones, purlin-to-chord local
bending, connection eccentricity, member and joint local buckling, geometric nonlinearity,
erection, transport, fire, corrosion, foundations, and code compliance. The catalogue has
only one `Iy` value per HSS; the Euler check therefore cannot establish real biaxial member
stability. All three available square HSS choices pass the narrow subproblem, so the
HSS100×100×6 catalogue floor governs the current inner selection. That is a search-space
limit, not proof that the section is adequate.

The mass objective is not total structural steel and the fabrication proxy is not money.
Supplier material rates, cutting/drilling/welding hours, connection families, transport
limits, crane picks, coating, and foundation consequences must be added before any cost
optimization.

## Reproduction

```powershell
python -m dreamhouse.structure.optimize_roof
python -m dreamhouse.structure.ground_structure
python -m unittest discover -s dreamhouse/structure/tests -v
```

Optional research dependencies are isolated from the base model:

```powershell
python -m pip install -e ".[optimization]"
```

## Verified external sources

- [SciPy mixed-integer linear programming](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html)
- [SciPy constrained differential evolution](https://docs.scipy.org/doc/scipy-1.16.1/reference/generated/scipy.optimize.differential_evolution.html)
- [pymoo mixed-variable problems](https://pymoo.org/customization/mixed.html)
- [SALib model-wrapping and Sobol workflow](https://salib.readthedocs.io/en/latest/user_guide/basics_with_interface.html)
- [CVXPY mixed-integer solver interfaces](https://www.cvxpy.org/tutorial/constraints/index.html)
- [MILP discrete sizing and topology optimization of trusses](https://doi.org/10.1007/s00158-022-03325-7)
- [AISC Design Guide 14 scope for staggered trusses](https://account.aisc.org/ItemDetail?Category=BOOKS&WebsiteKey=3d6245c2-db4d-4109-b6cf-42c3d4d6897a&iProductCode=D814-02)
- [Warren, Pratt, and Vierendeel behaviour](https://steelconstruction.info/sectors/bridges/design-of-steel-footbridges/)
- [OpenSeesPy elastic beam-column element](https://openseespydoc.readthedocs.io/en/latest/src/elasticBeamColumn.html)
