# Owner-Priority Architectural Coordination — b10/R09 and b11/R10

**Status:** active schematic coordination hypotheses; not for construction  
**Version:** 0.3-b10-P2 / R09 and 0.3-b11-rooflights / R10  
**Date:** 2026-08-13  
**Sources:** D-050, D-051, D-052, D-053; D-042; D-048; b09/R08 predecessor  
**Approval pending:** owner, architect of record, structural engineer, fire/life-safety
professional, MEP engineer, envelope consultant, and cost review

## Coordinated outcome

This issue converts the owner's four priorities into explicit geometry without changing
the 18 × 36 m hall, the 270 m² P2 envelope, or the total rooflight glass area.

1. The primary suite becomes clearly dominant and now meets the original bathroom and
   dressing-room programme minimums.
2. Laundry leaves P2 and is reserved inside PB storage behind the Great Wall.
3. A rear retractable exterior-stair envelope is reserved for security and second-route
   study, but is not counted as an approved exit.
4. The X=21 mini-deck view remains primary; one large exposed industrial truss is
   architecturally acceptable, while small decorative trusses are rejected.
5. The two rooflights are recentered as a group over the exact centre of the double-height
   volume.

## P2 b10/R09

The P2 tessellation still closes at **270.000 m²**. The primary suite now comprises:

| Component        | Gross area | Reading                                                                       |
| ---------------- | ---------: | ----------------------------------------------------------------------------- |
| Primary bedroom  |    31.1 m² | Existing wide 7.40 × 4.20 m room retained                                     |
| Primary bathroom |    17.6 m² | One L-shaped room across a wet salon and service band                         |
| Dressing/filter  |    17.6 m² | Exceeds the original 15–16 m² range by 1.6 m²; accepted as a priority reserve |

The bathroom is L-shaped because the released former laundry zone is joined to the
primary wet band. Its two rectangles are one programmed bathroom, connected by a
1.00 m opening; detailed fixtures, privacy screens, waterproofing, and ceiling/service
continuity remain subject to 1:25 design.

Removing upstairs laundry releases the centre of P2 for the primary suite while retaining
the mini deck, an enlarged family lounge/library, linen/cleaning storage, protected main
stair, the Phase 2 lobby, both child suites, guest suite, and wellness room. Child-bedroom
net areas remain 23.46 and 23.22 m², a 0.24 m² difference under D-042.

The model reports **20 PASS · 0 FAIL · 3 OPEN**. The three open gates are professional
acceptance of the retractable stair as a second exit, the detailed structural design of
the large exposed X=21 truss, and final site orientation/solar/privacy design.

## Laundry behind the Great Wall

The preferred reserve is **3.40 × 1.30 m** inside the existing PB storage room, behind its
flush Great Wall door. This is architecturally stronger than a visible cabinet opposite
the kitchen because it:

- preserves the ground floor as one continuous hall without another visible domestic box;
- contains appliance noise and visual clutter;
- reuses a service/storage room rather than consuming living frontage; and
- sits below the enlarged primary wet band, creating a plausible vertical MEP stack.

The reserve includes a washer, dryer, utility sink, and tall cleaning store. It does not
yet prove drainage gradients, venting, trap protection, acoustic isolation, waterproofing,
dryer exhaust, replacement path, or door/appliance working clearances.

## Retractable exterior-stair reserve

The reserve is placed on the rear façade from the common Phase 2 lobby, clear of the
D-048 rear-north column. Its security intent is explicit: while stored, the lower end
remains approximately 2.40 m above grade and cannot be used as a ladder from outside.

This device is **not yet a compliant second exit**. A life-safety system cannot depend on
an occupant finding a key, on grid power, or on a mechanism that can jam. Professional
review must establish at least:

- fail-safe manual deployment from the occupied side;
- clear width, slope, treads, landings, guards, handrails, headroom, and structural loads;
- operation under fire, smoke, wind, ice/rain, corrosion, power loss, and poor maintenance;
- protection from unauthorized exterior deployment without blocking emergency use;
- travel distance, exit separation, discharge, accessible means, and fire exposure; and
- inspection, testing, rescue access, and long-term maintenance.

Until those gates close, the main protected stair remains the only represented approved
circulation concept and D-021/D-038 remain open.

## X=21 edge-truss brief

The view from the mini deck is primary. The architectural brief allows the structure to
be visible when it is **one large, deep, credible industrial truss** whose scale expresses
real load transfer. Small repeated or ornamental trusses are rejected.

No structural topology has been selected. The engineer must coordinate member depth,
panel points, load introduction, lateral restraint, vibration, joints, fire protection,
erection splices, ceiling edges, doors, MEP, and the protected view cone. The large-truss
preference may not be used to bypass the E1/E2 gates.

## Rooflights b11/R10

The double-height volume occupies X=0.00→21.00 m and Y=0.00→18.00 m, so its exact centre
is **X=10.50/Y=9.00 m**. The previous pair had a group centre at X=3.60/Y=9.00 m: correct
transversely but **6.90 m forward** longitudinally.

The new equal rooflights are:

| ID             | Rectangle                    | Centre               |
| -------------- | ---------------------------- | -------------------- |
| RL-CAR         | X=8.10→12.90; Y=6.00→8.40 m  | X=10.50/Y=7.20 m     |
| RL-RC          | X=8.10→12.90; Y=9.60→12.00 m | X=10.50/Y=10.80 m    |
| Combined group | X=8.10→12.90; Y=6.00→12.00 m | **X=10.50/Y=9.00 m** |

The calculated offset is **0.00 m in X and 0.00 m in Y**, within the owner's ±0.10 m
tolerance. The glazing remains two separated 4.80 × 2.40 m events totaling 23.04 m².
This fixes the architectural position, not the construction system: purlin trimmers,
diaphragm interruption, crickets, secondary overflow, curb, glass, solar control,
condensation, cleaning, and replacement remain open.

## Controlled files

- `dreamhouse/p2_b10.json`
- `dreamhouse/generate_p2_b10.py`
- `planos/conceptual_v0.3_b10_p2/DH-ARQ-PLN-002-R09_P2-COORDINATED.svg`
- `planos/conceptual_v0.3_b10_p2/DH-ARQ-DIA-001-R09_P2-ACCESS-EGRESS.svg`
- `planos/conceptual_v0.3_b10_p2/DH-ARQ-DET-002-R09_OWNER-PRIORITIES.svg`
- `dreamhouse/rooflight_b11.json`
- `dreamhouse/generate_rooflight_b11.py`
- `planos/conceptual_v0.3_b11_rooflights/DH-ARQ-PLN-CUB-001-R10_CENTRAL-ROOFLIGHTS.svg`
- `planos/conceptual_v0.3_b11_rooflights/DH-ARQ-SEC-CUB-003-R10_CENTRAL-DAYLIGHT.svg`

Regenerate with:

```powershell
python dreamhouse/generate_p2_b10.py
python dreamhouse/generate_rooflight_b11.py
```
