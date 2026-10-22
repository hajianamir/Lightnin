# Requirements Traceability Matrix

- **Document ID**: DOC-RTM-001
- **Version**: 1.0.0-prototype
- **Status**: Implemented Engineering Prototype
- **Product Name**: AegisLPS (Provisional Working Title)

| Requirement ID | Standard Ref | Description | Source Module | Test Case | Status |
|---|---|---|---|---|---|
| `SYS-001` | Multi-Platform | Support Windows x64 native desktop, web browser, and local service | `apps/desktop`, `services/api` | `test_health_endpoint` | Implemented, unverified |
| `CALC-001` | IEC 62305-3 §6.3 | Simplified separation distance $s = k_i \cdot \frac{k_c}{k_m} \cdot l$ | `aegislps_engine/separation.py` | `test_simplified_separation_distance_class_I` | Implemented, unverified |
| `CALC-002` | IEC 62305-3 §6.3 | Segment-by-segment separation distance | `aegislps_engine/separation.py` | `test_simplified_separation_distance_class_III_solid_medium` | Implemented, unverified |
| `CALC-003` | IEC 62305-3 App C | Nodal current sharing $k_c$ sparse matrix solver | `aegislps_engine/nodal.py` | `test_nodal_solver_current_sharing` | Implemented, unverified |
| `GEO-001` | IEC 62305-3 App A | 3D Rolling sphere protection clearance check | `aegislps_geometry/rolling_sphere.py` | `test_rolling_sphere_protection` | Implemented, unverified |
| `RISK-001` | IEC 62305-2 | Loss of human life risk $R_1$ assessment prototype | `aegislps_engine/risk.py` | `test_risk_management_engine` | Implemented, unverified (Legacy/Partial) |
| `REP-001` | Professional Docs | ReportLab PDF generation with formula step trace | `services/api/main.py` | `test_pdf_report_endpoint` | Implemented, unverified |
| `IMP-001` | DXF Export | 2D CAD DXF polyline export | `aegislps_engine/dxf_exporter.py` | `test_dxf_exporter` | Implemented, unverified |
| `IMP-002` | IFC/BIM Import | Clean-room IFC file parse interface stub | `aegislps_engine/ifc_importer.py` | `test_ifc_importer_stub` | Interface stub, not validated |
