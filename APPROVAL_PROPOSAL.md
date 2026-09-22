# Instructor Approval Proposal

**Proposed project:** Used-Car Listing Price Assessment

Given a vehicle's details and a seller's asking price, the service will:

1. Estimate the vehicle's market value with a lightweight tabular regression pipeline.
2. Apply an explicit, configurable domain policy to classify the asking price as `BELOW_RANGE`, `WITHIN_RANGE`, or `ABOVE_RANGE`.

The asking price will not be used as a model feature. It will only be compared with the estimated value by the decision policy. The policy thresholds will be documented as business policy bands, not statistical confidence intervals.

The project fits Track B because it uses tabular data, produces one of three deterministic decisions, needs only a lightweight CPU-friendly model, and supports deterministic behavioural tests. For example, with all vehicle details fixed, increasing only the asking price must never move the result toward a cheaper band. A separate invariance test will confirm that changing an irrelevant request identifier does not alter the result.

The implementation will use a public used-car dataset only after its provenance, permitted usage, market, currency, mileage units, collection period, columns, and price semantics have been verified and documented.

**Approval requested:** May I proceed with this Track B capstone idea under the SDA-AIE-113 requirements?

## Approval Record

- Status: Approved
- Instructor: Not identified in the supplied confirmation
- Date: 2026-09-21 (confirmation supplied to the implementation partner)
- Evidence/reference: The project owner explicitly confirmed in the working session that the instructor approved the idea. Preserve the original instructor message/email separately if formal evidence is required.
