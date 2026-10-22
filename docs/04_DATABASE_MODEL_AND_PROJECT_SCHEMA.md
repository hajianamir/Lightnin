# Database Model & JSON Project Schema Specification

- **Document ID**: DOC-DB-001
- **Version**: 1.0.0-draft
- **Status**: Stage 0 Approved Baseline
- **Product Name**: AegisLPS (Provisional Working Title)

---

## 1. Project JSON Schema (`.lps`)
The `.lps` format is the authoritative portable project exchange representation.
- Required Schema Identifier: `https://schema.aegislps.org/v1/project.json`
- Root Attributes:
  - `schema_version`: "1.0.0"
  - `project_id`: UUIDv4
  - `metadata`: Name, client, designer, checker, approver, status.
  - `standards_config`: Selected standard parts and corrigenda.
  - `building`: Geometry, dimensions, materials.
  - `network`: Conductors, nodes, segments, earth points.
  - `separation_points`: Target objects, insulation medium, spatial distance.
  - `calculations`: Snapshots of engine runs, safety margins, formula traces.
  - `checksum`: SHA-256 HMAC for approved calculation revisions.

## 2. Standards Data Representation Model
```json
{
  "standards": [
    {
      "standard_id": "IEC 62305-1",
      "edition": "2024",
      "corrigenda": [],
      "data_package_version": "1.0.0-draft",
      "verification_status": "pending"
    },
    {
      "standard_id": "IEC 62305-2",
      "edition": "2024",
      "corrigenda": ["COR1:2024"],
      "data_package_version": "1.0.0-draft",
      "verification_status": "pending"
    },
    {
      "standard_id": "IEC 62305-3",
      "edition": "2024",
      "corrigenda": [],
      "data_package_version": "1.0.0-draft",
      "verification_status": "pending"
    },
    {
      "standard_id": "IEC 62305-4",
      "edition": "2024",
      "corrigenda": [],
      "data_package_version": "1.0.0-draft",
      "verification_status": "pending"
    }
  ]
}
```
