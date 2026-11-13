# AegisLPS Release Notes - Version 1.0.0-alpha.1

- **Product Name**: AegisLPS (Provisional Working Title)
- **Application Display Version**: 1.0.0-alpha.1
- **Python Distribution Version**: 1.0.0a1
- **Status**: Engineering Prototype Implemented; Formal Verification & Packaging Pending
- **Commit SHA**: 3a0e5fd34a07fd3d21fbce074f84f612060e7174

---

## 1. Prototype Scope
This release is an engineering prototype intended for internal review and architecture demonstration. It is:
- **NOT** independently verified by third-party testing bodies.
- **NOT** accepted for production engineering sign-off.
- Standards parameters (e.g. $k_i, k_m$) are classified as `pending_authoritative_review`.

## 2. Test Execution Baseline
- **Collected Tests**: 11 automated test cases.
- **Passed**: 11
- **Failed**: 0
- **Warnings**: 1 (FastAPI TestClient deprecation warning regarding httpx2)

## 3. Package Manifest & PEP 440 Versions
- `aegislps-standards-data` == 1.0.0a1
- `aegislps-domain-model` == 1.0.0a1
- `aegislps-geometry` == 1.0.0a1
- `aegislps-reporting` == 1.0.0a1
- `aegislps-calculation-engine` == 1.0.0a1
- `aegislps-api` == 1.0.0a1

## Step 6.1–6.2 compatibility and disclosure notes
- HVI selection no longer accepts `lps_class` or `ambient_installation_type`; PV clearance no longer accepts `id`, `tilt_angle_deg`, `panel_count`, `array_length_m`, `array_width_m`, or `metallic_frame_bonded`. Unknown fields are rejected with HTTP 422.
- PV clearance now defaults to `kc = 1.0` when `down_conductor_count` is omitted; results may be more conservative than the former fixed `0.5`.
- H7 remains open: roof coverage is not verified. The optimizer API, optimization view, and DOCX/PDF reports disclose this limitation; the reports do not include an optimization result.
