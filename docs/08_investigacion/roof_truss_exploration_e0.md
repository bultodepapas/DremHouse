# E0 Parametric Roof-Truss Exploration

**Status:** research hypothesis; not for design, pricing, fabrication, or construction  
**Version:** 0.1  
**Date:** 2026-08-12  
**Input SHA-256:** `5fc236d3733eba9d656c60f3f6e64f5c5ec9a3477014e220afde384262deb0a1`

## Outcome

The deterministic explorer evaluated **144** geometries; **144** passed the defined axial subproblem and **18** remain non-dominated under the three declared proxies.
No candidate selects D-019. The table is a shortlist for a competent structural engineer and a later E1 model.

| Candidate | Module | Topology | Panels | Depth | Chord / web | Roof truss mass | Members + crossings | Governing ratio |
|---|---|---|---:|---:|---|---:|---:|---:|
| M90-HOWE-bd1fe9338054 | M90 | HOWE / VARIABLE | 6 | 1.50 m | HSS100x100x6 / HSS100x100x6 | 6083.7 kg | 25 + 0 | 0.653 |
| M90-WARREN_MODIFIED-02ca47195595 | M90 | WARREN_MODIFIED / VARIABLE | 6 | 1.50 m | HSS100x100x6 / HSS100x100x6 | 6114.8 kg | 25 + 0 | 0.624 |
| M90-HOWE-3ec5ac606829 | M90 | HOWE / VARIABLE | 6 | 1.80 m | HSS100x100x6 / HSS100x100x6 | 6281.1 kg | 25 + 0 | 0.545 |
| M90-WARREN_MODIFIED-c42968ca2e38 | M90 | WARREN_MODIFIED / VARIABLE | 6 | 1.80 m | HSS100x100x6 / HSS100x100x6 | 6324.6 kg | 25 + 0 | 0.521 |
| M90-HOWE-42df12c7e5b8 | M90 | HOWE / VARIABLE | 8 | 1.80 m | HSS100x100x6 / HSS100x100x6 | 6672.4 kg | 33 + 0 | 0.449 |
| M90-WARREN_MODIFIED-74f328f7de28 | M90 | WARREN_MODIFIED / VARIABLE | 8 | 1.80 m | HSS100x100x6 / HSS100x100x6 | 6711.0 kg | 33 + 0 | 0.446 |
| M60-HOWE-9f884166a9d5 | M60 | HOWE / VARIABLE | 6 | 1.50 m | HSS100x100x6 / HSS100x100x6 | 8517.1 kg | 25 + 0 | 0.447 |
| M60-WARREN_MODIFIED-d03ad67a517b | M60 | WARREN_MODIFIED / VARIABLE | 6 | 1.50 m | HSS100x100x6 / HSS100x100x6 | 8560.8 kg | 25 + 0 | 0.427 |
| M60-HOWE-6d02d14551ed | M60 | HOWE / VARIABLE | 6 | 1.80 m | HSS100x100x6 / HSS100x100x6 | 8793.5 kg | 25 + 0 | 0.373 |
| M60-WARREN_MODIFIED-6ed6749977a0 | M60 | WARREN_MODIFIED / VARIABLE | 6 | 1.80 m | HSS100x100x6 / HSS100x100x6 | 8854.5 kg | 25 + 0 | 0.357 |
| M60-HOWE-97316945027c | M60 | HOWE / VARIABLE | 8 | 1.80 m | HSS100x100x6 / HSS100x100x6 | 9341.3 kg | 33 + 0 | 0.308 |
| M60-WARREN_MODIFIED-a22a85d9e6b7 | M60 | WARREN_MODIFIED / VARIABLE | 8 | 1.80 m | HSS100x100x6 / HSS100x100x6 | 9395.5 kg | 33 + 0 | 0.306 |
| M45-HOWE-a8a3026537e1 | M45 | HOWE / VARIABLE | 6 | 1.50 m | HSS100x100x6 / HSS100x100x6 | 10950.6 kg | 25 + 0 | 0.344 |
| M45-WARREN_MODIFIED-04679c6dd641 | M45 | WARREN_MODIFIED / VARIABLE | 6 | 1.50 m | HSS100x100x6 / HSS100x100x6 | 11006.7 kg | 25 + 0 | 0.329 |
| M45-HOWE-ee27f6911b35 | M45 | HOWE / VARIABLE | 6 | 1.80 m | HSS100x100x6 / HSS100x100x6 | 11306.0 kg | 25 + 0 | 0.288 |
| M45-WARREN_MODIFIED-f9d2fb4285c5 | M45 | WARREN_MODIFIED / VARIABLE | 6 | 1.80 m | HSS100x100x6 / HSS100x100x6 | 11384.4 kg | 25 + 0 | 0.275 |
| M45-HOWE-0d5a66797e69 | M45 | HOWE / VARIABLE | 8 | 1.80 m | HSS100x100x6 / HSS100x100x6 | 12010.2 kg | 33 + 0 | 0.238 |
| M45-WARREN_MODIFIED-314ffe6b1fcc | M45 | WARREN_MODIFIED / VARIABLE | 8 | 1.80 m | HSS100x100x6 / HSS100x100x6 | 12079.9 kg | 33 + 0 | 0.236 |

## Objective interpretation

- `total_roof_truss_mass_kg`: all roof-truss lines plus the E0 principal-detail allowance; it is not total building steel.
- `fabrication_proxy`: member count plus twice the number of unconnected diagonal crossings; it is dimensionless and is not a price.
- `governing_ratio`: the larger of axial/Euler strength and L/180 roof-deflection ratios; lower means more screening reserve.

## Mandatory E1 progression

- vertical gravity and global roof uplift components only
- linear elastic pin-jointed axial model
- Euler screening uses the single catalogue Iy value and K=1.0 hypothesis
- no local buckling, connection, chord local bending, second-order, fatigue, fire, diaphragm, lateral-system, erection, foundation, or code-compliance design
- mass covers roof trusses and the configured principal-detail allowance only; columns, secondary steel, connections, coatings, transport, and foundations are excluded

The JSON companion contains every candidate, rejected alternatives, profile pair count, controlling combination, equilibrium residual, and reproducibility hash.
