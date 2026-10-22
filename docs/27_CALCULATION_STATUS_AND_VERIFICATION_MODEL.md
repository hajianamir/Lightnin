# Calculation Status & Verification State Model

- **Document ID**: DOC-STAT-001
- **Version**: 1.0.0-draft
- **Status**: Stage 0 Approved Baseline
- **Product Name**: AegisLPS (Provisional Working Title)

---

## 1. Calculation Lifecycle States
Every calculation run and associated result record in AegisLPS MUST carry one of the following explicit states:

1. `NOT_CALCULATED`: Initial state when inputs are entered but no solver has run.
2. `CALCULATED`: Solved numerically, awaiting validation against standards criteria.
3. `WARNING`: Calculated successfully, but one or more input parameters or intermediate values hit a soft boundary condition.
4. `FAILED`: Calculation failed due to network non-convergence, topological disconnected components, or negative spatial distances.
5. `UNVERIFIED`: Result produced using unverified user-entered standards data packages.
6. `VERIFIED_AGAINST_REF`: Numerical result validated against an official engineering benchmark reference case.
7. `REVIEWED`: Reviewed by a qualified engineering checker.
8. `APPROVED`: Formally signed off by an authorized approver; state becomes immutable.
9. `SUPERSEDED`: Replaced by a newer approved revision.
10. `INVALIDATED_BY_INPUT`: Input geometry or material changed after calculation execution.
11. `INVALIDATED_BY_STANDARDS`: Standards configuration package updated after execution.
12. `INVALIDATED_BY_ENGINE`: Calculation engine code version updated.
