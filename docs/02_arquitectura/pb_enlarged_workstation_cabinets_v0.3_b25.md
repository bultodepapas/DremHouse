# PB enlarged workstation cabinets — draft 25

**Status:** active schematic coordination hypothesis under D-069; not for construction
**Version:** 0.3-draft-25-PB
**Date:** 2026-08-20
**Scope:** ground floor, paired wall-integrated workstations and cabinet storage
**Source:** owner visual review of PB b24, D-068, D-069 and the b24 parametric model.

## Purpose

Give the two permanent ground-floor workstations a scale appropriate to the 18 × 36 m
hall without creating excessively deep work surfaces. PB b25 retains the D-068 mirrored
wall/window concept and enlarges only the joinery assembly. Both workstations remain
reflections across Y=9.00 m and both face equal 3.00 × 1.65 m side windows.

PB b25 supersedes PB b24 only for worktop and cabinet test geometry. The open hall,
programme bands, 3 × 3 m workstation clearance envelopes, facade openings, main glazing,
technical benches, roof and all unaffected ground-floor geometry remain inherited.

## Active test geometry

| Item | Each workstation | Pair total | Status |
| --- | ---: | ---: | --- |
| Worktop | 3.00 × 0.90 m at 0.75 m high | 5.40 m² | full-bay test geometry |
| Suspended cabinet units | 2 × 0.70 × 0.75 × 0.62 m | 4 units | powder-coated steel hypothesis |
| Drawers | 3 per cabinet | 12 drawers | large cabinet-style storage |
| Central knee/chair opening | 1.60 m clear | 2 openings | minimum coordination clearance |
| Window | 3.00 × 1.65 m; sill 0.90 m | 9.90 m² glazing | unchanged from D-068 |

The 0.90 m worktop depth is intentionally less than 1.00 m. It adds useful monitor,
model-making and document depth without making the rear portion difficult to reach. The
two 0.70 m drawer banks occupy the ends of the full-width worktop, leaving a generous
1.60 m central position for a chair, computer equipment and lateral movement.

## Architectural assembly

- A 3.00 m replaceable timber top reads as one continuous horizontal element aligned with
  the full window bay.
- Two large three-drawer powder-coated-steel cabinets hang below the outer ends. Their
  0.75 m depth remains inside the worktop projection and their nominal 0.62 m height
  leaves a small cleanable shadow gap above the finished floor.
- The worktop, cabinets and accessible power/data tray attach to the dedicated bolted
  secondary-steel workstation frame established by D-068.
- The cabinets are part of the permanent architectural metalwork family shared with the
  workshop benches, but they are not primary gravity, lateral, facade or window structure.
- Drawer fronts, pulls and exposed fasteners should be robust, simple and replaceable;
  avoid decorative domestic millwork that weakens the industrial-house language.

## Coordination holds

Loaded drawer, eccentric, impact and racking demands are materially greater than the b24
open-worktop hypothesis. A structural engineer must define the secondary frame, brackets,
fasteners, local deflection and vibration criteria. Do not load window frames or
unverified facade girts and do not field-weld to primary steel.

Before fabrication, verify a full-scale mock-up with the real chair, monitors, computer,
task equipment and cable routes. Confirm drawer extension does not conflict with knees or
circulation; maintain access to power/data and window drainage; coordinate locks, slides,
handles, cleaning, corrosion protection and replacement of the timber top.

## Parametric controls and evidence

PB b25 adds fail-closed checks for full-bay length, depth below 1.00 m, equal cabinetry,
two three-drawer banks per side, a 1.60 m central opening and cabinets contained within
the worktop envelope. All PB b24 symmetry, glazing and professional-interface checks
remain active.

The issued evidence is in `planos/conceptual_v0.3_b25_pb/`, comprising the coordinated
ground-floor plan, both side elevations, the revised workstation/cabinet detail,
`compliance.json` and `manifest.json`. The source delta is
`dreamhouse/pb_b25_delta.json`; generation is deterministic through
`python -m dreamhouse.generate_pb_b25`.
