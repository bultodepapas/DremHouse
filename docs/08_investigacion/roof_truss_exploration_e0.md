# E0 Parametric Roof-Truss Exploration

**Status:** research hypothesis; not for design, pricing, fabrication, or construction
**Version:** 0.2
**Date:** 2026-08-12
**Input SHA-256:** `ab24628bb9a6413dac7c9523e889f6ce868be2dbb6db9e15d16f89fc494f404a`

## Outcome

The deterministic explorer evaluated **144** geometries; **144** passed the defined enhanced roof subproblem and **18** remain non-dominated under the three declared proxies.
No candidate selects D-019. The table is a shortlist for a competent structural engineer and a later E1 model.

| Candidate                        | Module | Topology                   | Panels |  Depth | Chord / web                 | Roof truss mass | Members + crossings | Governing ratio |
| -------------------------------- | ------ | -------------------------- | -----: | -----: | --------------------------- | --------------: | ------------------: | --------------: |
| M90-HOWE-3bdc910d7303            | M90    | HOWE / VARIABLE            |     10 | 1.50 m | HSS100x100x6 / HSS100x100x6 |       6729.1 kg |              41 + 0 |           0.954 |
| M90-WARREN_MODIFIED-f166d3ae441c | M90    | WARREN_MODIFIED / VARIABLE |     10 | 1.50 m | HSS100x100x6 / HSS100x100x6 |       6771.0 kg |              41 + 0 |           0.932 |
| M90-HOWE-dada4f7a017e            | M90    | HOWE / VARIABLE            |     10 | 1.80 m | HSS100x100x6 / HSS100x100x6 |       7090.5 kg |              41 + 0 |           0.832 |
| M90-WARREN_MODIFIED-e461c27f472e | M90    | WARREN_MODIFIED / VARIABLE |     10 | 1.80 m | HSS100x100x6 / HSS100x100x6 |       7147.3 kg |              41 + 0 |           0.814 |
| M90-HOWE-9dcd9d6d990f            | M90    | HOWE / VARIABLE            |      8 | 1.50 m | HSS120x120x6 / HSS100x100x6 |       7204.7 kg |              33 + 0 |           0.793 |
| M90-HOWE-42df12c7e5b8            | M90    | HOWE / VARIABLE            |      8 | 1.80 m | HSS120x120x6 / HSS100x100x6 |       7481.7 kg |              33 + 0 |           0.696 |
| M60-HOWE-db90adfb4327            | M60    | HOWE / VARIABLE            |     10 | 1.50 m | HSS100x100x6 / HSS100x100x6 |       9420.7 kg |              41 + 0 |           0.633 |
| M60-WARREN_MODIFIED-e27ac59dbcae | M60    | WARREN_MODIFIED / VARIABLE |     10 | 1.50 m | HSS100x100x6 / HSS100x100x6 |       9479.4 kg |              41 + 0 |           0.619 |
| M60-HOWE-9f884166a9d5            | M60    | HOWE / VARIABLE            |      6 | 1.50 m | HSS120x120x6 / HSS100x100x6 |       9649.6 kg |              25 + 0 |           0.756 |
| M60-WARREN_MODIFIED-d03ad67a517b | M60    | WARREN_MODIFIED / VARIABLE |      6 | 1.50 m | HSS120x120x6 / HSS100x100x6 |       9693.2 kg |              25 + 0 |           0.734 |
| M60-HOWE-6d02d14551ed            | M60    | HOWE / VARIABLE            |      6 | 1.80 m | HSS120x120x6 / HSS100x100x6 |       9926.7 kg |              25 + 0 |           0.672 |
| M60-HOWE-55b6e7b141fe            | M60    | HOWE / VARIABLE            |     10 | 1.80 m | HSS100x100x6 / HSS100x100x6 |       9926.7 kg |              41 + 0 |           0.555 |
| M60-WARREN_MODIFIED-6ed6749977a0 | M60    | WARREN_MODIFIED / VARIABLE |      6 | 1.80 m | HSS120x120x6 / HSS100x100x6 |       9987.6 kg |              25 + 0 |           0.653 |
| M60-WARREN_MODIFIED-6f28eb546646 | M60    | WARREN_MODIFIED / VARIABLE |     10 | 1.80 m | HSS100x100x6 / HSS100x100x6 |      10006.2 kg |              41 + 0 |           0.544 |
| M90-WARREN_MODIFIED-02ca47195595 | M90    | WARREN_MODIFIED / VARIABLE |      6 | 1.50 m | HSS150x150x8 / HSS100x100x6 |      10034.8 kg |              25 + 0 |           0.506 |
| M90-WARREN_MODIFIED-c42968ca2e38 | M90    | WARREN_MODIFIED / VARIABLE |      6 | 1.80 m | HSS150x150x8 / HSS100x100x6 |      10247.0 kg |              25 + 0 |           0.451 |
| M45-HOWE-f229c612ef25            | M45    | HOWE / VARIABLE            |     10 | 1.80 m | HSS100x100x6 / HSS100x100x6 |      12762.9 kg |              41 + 0 |           0.423 |
| M45-WARREN_MODIFIED-ae23bdcfdf03 | M45    | WARREN_MODIFIED / VARIABLE |     10 | 1.80 m | HSS100x100x6 / HSS100x100x6 |      12865.1 kg |              41 + 0 |           0.415 |

## Objective interpretation

- `total_roof_truss_mass_kg`: all roof-truss lines plus the E0 principal-detail allowance; it is not total building steel.
- `fabrication_proxy`: member count plus twice the number of unconnected diagonal crossings; it is dimensionless and is not a price.
- `governing_ratio`: the larger of HSS biaxial/local axial–flexural interaction and L/180 roof-deflection ratios; lower means more screening reserve.

## Mandatory E1 progression

- vertical gravity and global roof uplift components only
- linear elastic pin-jointed global model; no frame action or joint eccentricity
- HSS biaxial and local slenderness use nominal parsed dimensions, a 0.93 wall-thickness factor, and the catalogue strong-axis inertia
- top-chord local bending is a simply supported segment screen under the vertical line load; actual purlin reactions and joint load introduction remain pending
- member B1-style magnification uses reduced Euler stiffness; a complete global direct second-order analysis remains pending
- trial joints, diaphragm, full lateral system, fire, erection, foundations, fatigue, seismic detailing, and code compliance are evaluated only in the separate E1 gate report or remain blocked
- mass covers roof trusses and the configured principal-detail allowance only; columns, secondary steel, connections, coatings, transport, and foundations are excluded

The JSON companion contains every candidate, rejected alternatives, profile pair count, controlling combination, equilibrium residual, and reproducibility hash.
