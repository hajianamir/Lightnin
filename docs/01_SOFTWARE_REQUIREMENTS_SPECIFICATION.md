# Software Requirements Specification (SRS)

- **Document ID**: DOC-SRS-001
- **Version**: 1.0.0-draft
- **Status**: Stage 0 Approved Baseline
- **Product Name**: AegisLPS
- **Name Status**: Provisional working title, pending legal and trademark clearance
- **Author**: Lead Software & Systems Engineer
- **Reviewer**: Senior Lightning-Protection Engineer

---

## 1. Executive Product Overview
AegisLPS is an original, professional, advanced lightning-protection engineering application. It provides an independent engineering platform for separation-distance calculations, nodal current-sharing analysis, air-termination system design, 2D/3D visual modeling, and formal auditable reporting according to the IEC 62305 standard series (2024 baseline).

## 2. Deployment & Platform Matrix
- **Native Desktop Application**: Windows 11 x64 (Primary Native Target via Tauri + local Python calculation service sidecar).
- **Web Browser Application**: Modern evergreen browsers (Chrome, Edge, Firefox, Safari) on Windows, macOS, and Linux.
- **Private Network / On-Premises**: Containerized server deployment options.

## 3. High-Level Requirements Traceability
- `SYS-001`: Multi-platform architecture (Windows x64 desktop, Web, Private-Network).
- `SYS-002`: Clean-room implementation; zero proprietary competitor code or trademarked assets.
- `SYS-003`: Offline-first operation for Windows x64 native desktop.
- `CALC-001`: Simplified separation distance calculation ($s = k_i \cdot \frac{k_c}{k_m} \cdot l$).
- `CALC-002`: Segment-by-segment detailed separation distance calculation along 3D conductor paths.
- `CALC-003`: Graph-based nodal current-sharing solver for complex meshed conductor networks.
- `GEO-001`: Interactive 3D WebGL (Three.js/@react-three/fiber) building and conductor network viewer.
- `REP-001`: PDF calculation report generation with immutable calculation traces and digital checksums.
