# Coordinated Upper Floor v0.3 — Draft 09

**Status:** superseded by D-050 / b10-R09; retained as the direct predecessor
**Version:** 0.3-draft-09-P2 / R08  
**Date:** 2026-08-13  
**Source:** D-049; owner preference for b04/R03; verified b06/R05 controls; D-042;
D-048  
**Supersedes:** 0.3-draft-06-P2 / R05, retained as a traceable predecessor  
**Approval pending:** owner, architect of record, structural engineer, and fire and
life-safety professional

## Architectural position

This issue makes the preferred b04 spatial logic the active upper-floor hypothesis
without reintroducing its dimensional and access ambiguities. The centre of the plan is
again a sequence of **acoustic mini deck → family lounge/library → private gallery →
protected stair arrival**. The b06 corrections remain where they were demonstrably
stronger: equivalent child bedrooms, a usable Phase 2 lobby, coordinated guest and
wellness areas, explicit measurement bases, and the rear protected stair.

The P2 envelope remains **15.00 × 18.00 m = 270.00 m² gross**, from X=21.00 to 36.00 m.
This issue changes the internal organization, not the project envelope or nominal gross
floor area. It therefore creates no independent cost-baseline change.

## Spatial organization

- **Phase 1 / family side:** Child Suite 1 is connected to the family lounge; the 9.8 m²
  acoustic mini deck overlooks the double-height hall; laundry and linen storage sit on
  the private gallery rather than inside a suite.
- **Primary suite:** a 7.40 × 4.20 m bedroom retains the wide proportion and two exterior
  glazed fronts. A filter separates the bedroom, bathroom, dressing room, and common
  arrival.
- **Shared arrival:** the stair opens into a protected common arrival. Access to the
  primary suite, family centre, Phase 2, and stair is no longer implied or routed through
  a bathroom, dressing room, or bedroom.
- **Phase 2:** a single full-width, isolatable lobby remains behind Y=11.00 m and serves
  Child Suite 2, the guest suite, and the wellness room.
- **Stair and structure:** the stair footprint remains X=31.50→36.00 m and
  Y=7.40→11.00 m. The four D-048 full-height column reservations remain at its corners;
  no section, bracing system, joint, base, or foundation is selected.

## Programme and measurement snapshot

| Element                        |    Coordinated value | Reading                                           |
| ------------------------------ | -------------------: | ------------------------------------------------- |
| Child Suite 1                  |        38.0 m² gross | Bedroom, wardrobe, and private bathroom           |
| Child Suite 2                  |        38.1 m² gross | Bedroom, wardrobe, and private bathroom           |
| Child bedrooms                 | 23.46 / 23.22 m² net | Difference 0.24 m²; D-042 passes                  |
| Guest suite                    |        29.1 m² gross | Bedroom, filter, bathroom, and wardrobe           |
| Primary private rooms          |        54.8 m² gross | Bedroom, filter, bathroom, and dressing room      |
| Mini deck                      |         9.8 m² gross | Acoustically glazed toward the double-height hall |
| Wellness                       |        16.8 m² gross | Includes a 2.40 m sauna study reserve             |
| Narrowest declared circulation |         1.20 m clear | Guest-suite filter; Phase 2 lobby is 1.25 m clear |

Programme comparisons use gross areas, child-bedroom equivalence uses net usable area,
and circulation uses net clear width. These bases are declared in the parametric model
and may not be interchanged.

## Access and phasing control

The model contains **23 explicit doors or openings**. Each one is checked against the
shared boundary of the two spaces it connects, and the resulting graph proves that every
enclosed space reaches the protected stair. The separate access/egress diagram makes
that topology visible; it is not a professional egress approval.

The F1/F2 boundary remains one line at Y=11.00 m. A temporary closure at that line must
eventually resolve fire separation, weather, dust, noise, security, and temporary MEP
conditions. D-049 does not close the need for a second independent upper-floor exit.

## Deterministic control result

**Result at 2026-08-13: 16 PASS · 0 FAIL · 4 OPEN.**

The passes cover unique identifiers, finite positive geometry, envelope containment,
non-overlap, exact 270.00 m² tessellation, D-042 equivalence and proportions, circulation,
phasing, door geometry, whole-floor access connectivity, bedroom windows, PB stair
alignment, D-048 column coordinates, guest programme, and wellness capacity.

The four open gates are material and remain visible on the drawing:

1. The primary bathroom is 9.8 m² and the dressing room 9.6 m², below the original
   17–18 m² and 15–16 m² programme targets.
2. The second independent P2 exit awaits D-021 occupancy and fire review.
3. The X=21.00 m edge truss must preserve the mini-deck view, openings, ceiling, fire
   separation, and services.
4. Solar control, privacy, and final glazing await the selected site and orientation.

A `PASS` establishes internal consistency only. It is not evidence of regulatory
compliance, structural adequacy, or fitness for construction.

## Controlled files

- `dreamhouse/p2_b09.json`
- `dreamhouse/generate_p2_b09.py`
- `planos/conceptual_v0.3_b09_p2/DH-ARQ-PLN-002-R08_P2-COORDINATED.svg`
- `planos/conceptual_v0.3_b09_p2/DH-ARQ-DIA-001-R08_P2-ACCESS-EGRESS.svg`
- `planos/conceptual_v0.3_b09_p2/compliance.json`
- `planos/conceptual_v0.3_b09_p2/manifest.json`

Regenerate with:

```powershell
python dreamhouse/generate_p2_b09.py
```

## Next design work

1. Resolve the primary-suite programme by explicit owner decision: reduce the targets,
   enlarge P2, or change the stair/envelope strategy.
2. Obtain the professional fire/life-safety concept, including the second-exit decision.
3. Coordinate the X=21 edge truss, the mini-deck, ceilings, doors, fire separation, and
   services in section.
4. Develop 1:25 wet-room and sauna layouts, aligned shafts, hot-water demand, and
   ventilation.
5. Design the complete floor system for vibration, acoustics, fire, diaphragm action,
   and its connections to the Great Wall and stair-enclosure frame.
6. Freeze orientation only after site selection, then complete solar, privacy, and
   façade-glazing studies.
