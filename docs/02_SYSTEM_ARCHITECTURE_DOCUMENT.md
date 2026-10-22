# System Architecture Document (SAD)

- **Document ID**: DOC-SAD-001
- **Version**: 1.0.0-draft
- **Status**: Stage 0 Approved Baseline
- **Product Name**: AegisLPS (Provisional Working Title)

---

## 1. Architectural Principles
1. **Strict Separation of Concerns**:
   - Domain & Calculation Engine (Pure Python 3.11+, typed, deterministic)
   - Standards Service (Versioned, abstracted parameter store)
   - API Layer (FastAPI, OpenAPI v3 REST contract)
   - Presentation Layer (React 18, TypeScript strict, Three.js 3D viewport)
   - Desktop Layer (Tauri, secure loopback sidecar)
   - Persistence (SQLAlchemy ORM, SQLite desktop / PostgreSQL server)

2. **Calculation Integrity**:
   - 3D visual meshes are derived from authoritative engineering domain entities; visual meshes NEVER determine compliance alone.
   - All compliance evaluations are backed by numerical calculation output.

## 2. Monorepo Structure
```text
/
├── apps/
│   ├── web/                     # React + Vite + TS + R3F Frontend
│   └── desktop/                 # Tauri Desktop Wrapper & App Config
├── services/
│   ├── api/                     # FastAPI Application, Routes, Dependencies
│   ├── calculation-engine/      # Python Core Domain, Solvers & Algorithms
│   └── r-adapter/               # Python R-Adapter Interface & Python Fallback
├── contracts/
│   └── java/                    # OpenAPI / gRPC Java Client Stubs
├── packages/
│   ├── domain-model/            # Pydantic Domain Schemas & Business Entities
│   ├── geometry/                # Spatial Algorithms, 3D Mesh & Spatial Indexing
│   ├── standards-data/          # Versioned Standards Parameter Repository
│   ├── project-schema/          # JSON Schema for .lps Project Files
│   └── ui/                      # Shared UI Components & Design System
├── database/
│   └── migrations/              # Alembic Migration Scripts
├── docs/                        # Specification Package, ADRs, Risk Register
├── tests/                       # Unit, Integration, E2E & Benchmark Tests
└── validation/                  # Reference Engineering Test Cases
```
