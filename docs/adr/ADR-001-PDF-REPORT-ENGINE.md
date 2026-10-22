# ADR-001: ReportLab as Primary PDF Report Generation Engine

- **Status**: Approved
- **Date**: 2025-05-15
- **Deciders**: Software Architect, Python Backend Engineer

## Context
AegisLPS requires formal, auditable engineering PDF reports containing project metadata, input values, calculation step traces, formula substitutions, 2D/3D visual diagrams, pass/fail status, and digital checksums.

## Decision
Use **ReportLab** (Python library) as the primary PDF report generation engine for Phase 1, wrapped behind an abstract `ReportRenderer` interface.

## Justification
1. Programmatic control over exact vector layout and deterministic page generation.
2. Direct compilation within the local Python service without requiring an HTML browser/rendering pipeline (such as Chromium or WeasyPrint).
3. Lightweight and clean packaging inside the Tauri desktop bundle.
