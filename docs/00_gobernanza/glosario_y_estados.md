# Glossary and document statuses

**Status:** active  
**Version:** 0.5
**Date:** 2026-10-03
**Language note:** controlled English translation under D-044; no change in meaning.
**Source of coordination vocabulary:** D-084 and the implemented candidate workflow,
including [increment 02](../06_gestion_y_obra/connected_coordination_increment_02.md).

## Commitment hierarchy

- **Hard rule:** a condition confirmed by the owner. It changes only through an explicit,
  recorded decision.
- **Technical requirement:** performance required for safety, code compliance,
  durability, or operation. It changes only with support from the competent professional
  and continued regulatory compliance.
- **Design Control Value (DCV):** a strong value used to coordinate schematic design. It
  applies by default but may be adjusted if the plan, structure, site, or cost analysis
  demonstrates a clear improvement.
- **Preference:** a desired direction that allows comparison with alternatives.
- **Hypothesis:** an idea to be studied; it does not authorize procurement, a final
  quotation, or construction.
- **Pending input:** external information required before a decision can be made.

## Decision statuses

- **Proposed:** not yet accepted.
- **Active:** governs the current work.
- **Frozen:** cannot be changed within the current stage without change control.
- **Superseded:** replaced by a later decision but retained for historical traceability.
- **Rejected:** must not reappear unless the decision is formally reopened.

## Document statuses

- **Draft:** incomplete; suitable for discussion.
- **Active:** current working reference.
- **Issued for coordination:** suitable for interdisciplinary coordination, not for
  construction.
- **Issued for permit:** professionally signed package for regulatory submission.
- **Issued for Construction (IFC):** approved, coordinated, and signed document suitable
  for execution.
- **As-built:** records work actually built and verified.
- **Historical:** retained for traceability; does not govern current work.

## Connected coordination states

These states describe different questions; none upgrades a schematic model to construction
authority. See the [workflow](../06_gestion_y_obra/connected_coordination_workflow.md) for
their actual JSON fields and commands.

| Term | Meaning in the implemented workflow |
| --- | --- |
| Resolved snapshot | Independently constructed model for a named scenario; shared by checks and renderers; generated evidence, not a second editable master |
| Active / study / context entity | Inclusion/role in the selected baseline: active input, excluded proposal, or contextual geometry; not approval or engineering readiness |
| Review release | Verified immutable baseline candidate selected by a separate current pointer; may retain OPEN findings; does not adopt a study or replace the historical drawing catalog |
| Rollback selection | Re-selection of an intact retained review; freshness is explicitly not revalidated until checked against current sources |
| Capability report | Actual entity operations, occurrences and rule coverage; context records and unsupported geometry remain explicit |
| Complete candidate | Required artifacts were generated and verified together; OPEN or FAIL findings may remain |
| Fresh / stale | Current input and artifact hashes match / differ from the recorded build; freshness alone proves no design adequacy |
| PASS / OPEN / FAIL finding | A named rule passed within its supported scope / remains unresolved / found a supported violation |
| Evaluated / unsupported / inapplicable / not_run coverage | Whether the rule could actually evaluate its inputs; missing geometry never becomes a clearance pass |
| Plan reservation | Located coordination allowance without a selected structural member; plan overlap can require review while solid interference stays unverified |
| Published current alias | Copy of an explicitly catalogued issue; the latest candidate is not automatically this issue |
| Model / input fingerprint | Hash of normalized model meaning and captured discipline context / conservative source and code dependencies; both differ from an element's persistent identity |
| Issue identity | Identity of a complete review package, including source inputs and rendering configuration; visual and nonvisual packages may represent the same model |
| Captured discipline context | Source evidence held with a scenario for its checks; it is not another editable master or adoption of a historical benchmark |
| Named anchor | Stable reference to a meaningful element or context location used by a dimension or callout; missing evidence cannot be silently replaced by a graphic position |
| Pixel comparison | Exact difference between declared visual exports; labels and annotations can change too, so it is neither a geometric-only comparison nor automatic design approval |

Finding lifecycle compares named scenarios. A previous non-passing finding is resolved
only by a supported, evaluated PASS for the same rule/entity pair. Missing elements,
lost applicability or unavailable evidence remain separately identified. The CLI compares
each study with the archived current baseline, not automatically with the last candidate.

The installed workflow retains `engineering_approval=false` and
`construction_authority=false`. A successful build command or a zero-FAIL result does
not close the recorded professional gates.

## Rule against false precision

A number does not become more reliable because it has decimal places. Every quantity must
state whether it is nominal, net, gross, calculated, quoted, or field-measured.
