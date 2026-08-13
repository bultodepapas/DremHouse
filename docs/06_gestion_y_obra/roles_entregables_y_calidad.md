# Roles, deliverables, and quality control

**Status:** organizational basis<br>
**Version:** 0.2<br>
**Date:** 2026-08-13<br>
**Sources:** prior organizational basis, D-044, and D-056<br>
**Language note:** controlled English translation; no change to responsibilities.

## Responsibility principle

The repository coordinates intent and evidence. Responsibilities reserved by law—such
as professional signatures, calculations, permits, direction, supervision, inspection,
and certification—remain with competent professionals and authorities. Artificial
intelligence neither signs documents nor assumes a professional licence.

## Minimum team to appoint

| Role | Primary responsibility |
| --- | --- |
| Owner/developer | Scope, budget, priorities, site, and decisions |
| Coordinating architect | Integrated design, programme, coordination, and permit |
| Geotechnical engineer | Ground, foundations, excavation, water, and recommendations |
| Structural engineer | System, calculations, drawings, details, and construction support |
| MEP engineers | Electrical, lighting, plumbing, drainage, HVAC/extraction |
| Fire/egress specialist | Classification, strategy, and life-safety coordination |
| Envelope/hygrothermal specialist | Insulation, air, vapour, condensation, seals, and bridges |
| Acoustic consultant | Hall, P2, rain, equipment, isolation, and absorption criteria |
| Cost planner / quantity surveyor | Quantities, rates, reconciliation, change, and forecast |
| Contractor / construction manager | Methods, safety, quality, programme, cost, and execution |
| Independent supervisor / reviewer | Verification under the applicable scope, rules, and contract |
| Commissioning authority | Integrated systems plan and verification |

One person may cover more than one role only when legally competent, sufficiently
resourced, and free from unacceptable contractual conflicts of interest.

## Master deliverable list

Every issue must state its code, title, discipline, version, status, date, author,
reviewer, approver, and superseded documents. Suggested convention:

`DH-[DISCIPLINE]-[TYPE]-[NUMBER]-[REV]`

Example disciplines: ARQ, EST, GEO, ELE, HID, MEC, PCI, ACO, ENV, COS, OBR.

### Current-drawing publication

The versioned issue is the retained technical record. If it becomes current for public
coordination, update its stable ID in [`planos/actual/catalog.json`](../../planos/actual/catalog.json)
and regenerate the SVG/PNG aliases and publication manifest. Promotion must be explicit;
revision sorting is not an approval method. The aliases inherit the source issue's
status and never create additional authority.

## Review by stage

- **Schematic design:** programme, dimensions, areas, furniture, sections, and hard rules.
- **Coordination:** interfaces, clashes, loads, shafts, tolerances, and maintenance.
- **Constructability:** sequence, access, erection, mock-ups, availability, and safety.
- **Cost:** common quantities, complete scope, exclusions, and risks.
- **Issued for construction (IFC):** signatures, reviews, permit, master list, and closed
  changes.

## Construction control

### Before work starts

- Current IFC document.
- Approved method statement and risk assessment.
- Material/equipment approved through the submittal process.
- Setting out, tolerances, and interfaces verified.

### Initial hold points

1. Setting out, levels, and drainage.
2. Excavation base and foundations before concrete placement.
3. Anchors/plates and lift reinforcement before casting.
4. Sub-base, barriers, joints, and PB slab reinforcement.
5. Steel receipt, joints, plumbness, bolts/welds, and protection.
6. Panel–flashing–window/door mock-up before mass production.
7. Envelope water/air tests under the approved plan.
8. Concealed services before closure.
9. Bathroom/sauna waterproofing before finishes.
10. Electrical, plumbing, extraction, controls, and life-safety testing.

### Records

Maintain daily reports, located photographs, inspections, tests, RFIs, submittals,
nonconformities, changes, quantities, progress, and weather. Any deviation affecting a
discipline must close with acceptance by its responsible designer.

## Handover

Do not accept only “the finished work.” Require as-builts, manuals, warranties,
certificates, training, inventory, secure keys/credentials, spares, test results, and a
maintenance plan.
