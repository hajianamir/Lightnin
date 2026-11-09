# Known Issues Register

This register tracks all known engineering, mathematical-formulation, security, build, integration, and test findings identified in the AegisLPS codebase review, recording each finding's base ID, severity, affected module or file(s), current remediation status, and planned remediation step.

> Status `open` means the finding is not yet fixed in code. A finding can be documented-as-unverified (step 0.3) and still be `open`.

## Findings

| ID | Severity | Module / file(s) | Status | Planned step | Note |
|---|---|---|---|---|---|
| C1 | Critical | `rolling_sphere.py`, `mesh_rolling_sphere.py`, `optimization.py` | open | 1.1, 1.2 | Also tracked as C1b in step 1.1. Documented as UNVERIFIED in step 0.3. Progress: 1.1 PASS 31796ba; 1.2 PASS ed7f69d (strict xfail, see H7). |
| C2 | Critical | `touch_step.py` | open | 1.3 | Documented as UNVERIFIED in step 0.3. Progress: 1.3 PASS 19a607a. |
| C3 | Critical | `lemp_engine.py` | open | 1.4 | Sub-item C3-b (K_MS) is planned in step 1.5. Progress: 1.4 PASS 434a727. C3-b: 1.5 PASS 6719bb9. |
| C4 | Critical | `rolling_sphere.py`, `mesh_rolling_sphere.py` | open | 1.6 (done) | Base C4: rolling-sphere radius per IEC 62305-3:2024, Clause 5.2.2.1, Table 2. Step 1.6 PASS at f9d880b. Sub-item C4-b (l1 table, `earthing.py`, `get_iec_min_length_l1`) is planned in step 2.4. The earlier file list (`earthing.py`, `earth_pit.py`, `separation.py`) was incorrect; those files are covered by H1, H2, H4, H5 and M6. |
| H1 | High | `separation.py` | open | 1.7 | kc from segment count. |
| H2 | High | `separation.py` | open | 1.7 | l in s equals node height, not route length. |
| H3 | High | `risk.py`, `comprehensive_risk.py` | open | 2.5 | |
| H4 | High | `earthing.py`, `earth_rod_sizing.py` | open | 2.3 | Multi-rod coupling term. |
| H5 | High | `earthing.py` | open | 2.1, 2.2 | Ring and strip prefactors. |
| H6 | High | `uq_engine.py`, `earthing.py` | open | 2.1, 3.2 | UQ inconsistent with earthing. Sobol approximation. |
| H7 | High | `optimization.py` | open | 1.2, 3.3 | Sub-items H7-a to H7-d. Strict xfail `test_design_optimization_coverage_improvement` accepted by the owner (step 1.2, ed7f69d). The label 'roof coverage not verified' is still to be added to the report and UI (later step). Status remains open. |
| H8 | High | `protective_angle.py` | open | 2.4 | Table values. |
| H9 | High | All modules | open | 2.7 | Invalid inputs silently defaulted. |
| H10 | High | `docs/33`, `docs/35`, `docs/28`, `docs/29` | open | 0.3 (documentation part only) | Documentation labelled in 0.3. Entry stays `open` until the claims are corrected by code. Progress: 0.3 PASS 171daed (documentation labels). |
| H11 | High | `packages/domain-model/aegislps_domain/integrity.py` | open | 4.3 | Hard-coded HMAC secret. |
| H12 | High | `apps/web/src/App.tsx`, `services/api/aegislps_api/main.py` | open | 4.1, 4.2 | localhost fetch and CORS. |
| H13 | High | `ifc_importer.py` | open | 4.4 | Stub returns fixed dimensions. |
| H14 | High | `tests/` | open | 5.1, 3.4 | Tautological assertions. |
| H15 | High | `spd_coordination.py` | open | 2.6 | Empirical l_prot. Documented in step 0.3. |
| M1 | Medium | `nodal.py` | open | 3.1 | Y = 1/abs(Z). |
| M2 | Medium | `peec_thermal.py` | open | 3.4 | Neumann singularity. |
| M3 | Low | `bom_engine.py` | open | UNASSIGNED | Plan gap. Offset comment and formula mismatch. Assign in phase 6 review. |
| M4 | Low | `hvi_conductor.py` | open | UNASSIGNED | Plan gap. Unused inputs. |
| M5 | Low | `pv_module.py` | open | UNASSIGNED | Plan gap. kc fixed at 0.5, unused inputs. |
| M6 | Low | `earth_pit.py` | open | UNASSIGNED | Plan gap. rho_c values need a source. |
| M7 | Low | `earth_rod_sizing.py` | open | UNASSIGNED | Plan gap. Copper-clad diameter mismatch between docstring and code. |
| M8 | Medium | `.github/workflows/ci.yml` | open | 5.2 | build step uses `\|\| true`. |
| M9 | Medium | `apps/desktop/tauri.conf.json` | open | 5.3 | Old schema, missing sidecar, unsafe-eval in CSP. |
| M10 | Low | `run_aegislps.py` | open | 4.5 | Message says server is running but it is not started. |
| M11 | Low | Git index | open | 0.2 | Bytecode removed from the index in step 0.2. Entry stays `open` until verified in the phase 6 review. Progress: 0.2 PASS 6197cb7, bb824b1. |
| M12 | Low | `apps/web/src/App.tsx` | open | 4.4 | DXF/glTF buttons only alert. |
| M13 | Low | `dxf_exporter.py`, `cad_export.py` | open | 4.4 | Only points are drawn. |

Total base IDs: 32 (Critical 4, High 15, Medium 4, Low 9)

All rows remain `open` until the finding is verified in code, regardless of documentation progress.

## Unassigned items

These findings have no step in the remediation plan. The supervisor will assign them.

- `M3` (`bom_engine.py`): Offset comment and formula mismatch.
- `M4` (`hvi_conductor.py`): Unused inputs.
- `M5` (`pv_module.py`): `kc` fixed at `0.5`, unused inputs.
- `M6` (`earth_pit.py`): `rho_c` values need a source.
- `M7` (`earth_rod_sizing.py`): Copper-clad diameter mismatch between docstring and code.

## Plan corrections

- The register has 32 base IDs: C1–C4 (4), H1–H15 (15), M1–M13 (13). Severity counts: Critical 4, High 15, Medium 4, Low 9.
- Sub-items C1b, C3-b, C4-b, and H7-a to H7-d are not counted separately.
- Correction recorded in step 0.4: the plan header previously stated 40 IDs. The correct count is 32.
