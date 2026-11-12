# Known Issues Register

This register tracks all known engineering, mathematical-formulation, security, build, integration, and test findings identified in the AegisLPS codebase review, recording each finding's base ID, severity, affected module or file(s), current remediation status, and planned remediation step.

> Status `open` means the finding is not yet fixed in code. A finding can be documented-as-unverified (step 0.3) and still be `open`.
>
> Status `fixed in code, pending verification` means the code change has passed supervisor review at the stated commit, but the finding is not yet closed in the register.

## Findings

| ID | Severity | Module / file(s) | Status | Planned step | Note |
|---|---|---|---|---|---|
| C1 | Critical | `rolling_sphere.py`, `mesh_rolling_sphere.py`, `optimization.py` | open | 1.1, 1.2 | Also tracked as C1b in step 1.1. Documented as UNVERIFIED in step 0.3. Progress: 1.1 PASS 31796ba; 1.2 PASS ed7f69d (strict xfail, see H7). |
| C2 | Critical | `touch_step.py` | open | 1.3 | Documented as UNVERIFIED in step 0.3. Progress: 1.3 PASS 19a607a. |
| C3 | Critical | `lemp_engine.py` | open | 1.4 | Sub-item C3-b (K_MS) is planned in step 1.5. Progress: 1.4 PASS 434a727. C3-b: 1.5 PASS 6719bb9. |
| C4 | Critical | `rolling_sphere.py`, `mesh_rolling_sphere.py`, `earthing.py`, `docx_renderer.py` | fixed in code, pending verification | 1.6 (done), 2.4 | Base C4: rolling-sphere radius per IEC 62305-3:2024, Clause 5.2.2.1, Table 2. Step 1.6 verified at f9d880b: 154 passed, 1 xfailed in clean venv; mutation check (class III 45→46) fails 2 edition tests. Non-blocking: lookup accepts surrounding spaces and lower case. Sub-item C4-b (`earthing.py` `get_iec_min_length_l1`, `docx_renderer.py`): fixed in code, pending verification at 3343007 (step 2.4). Figure 1 and Figure 5 values are graphical readings (±1.5°, ±0.5 m); tabulated values not in repo. Open: Type A vertical `0.5·l1` and Type B `r_e >= l1` compliance rules not changed in step 2.4. |
| H1 | High | `separation.py` | fixed in code, pending verification | 1.7 | kc from segment count. Step 1.7 PASS at 8e422f8 (Table 11–13 k_c by conductor count, 6.3.1). Status stays until verification is closed. |
| H2 | High | `separation.py` | fixed in code, pending verification | 1.7 | l in s equals node height, not route length. Step 1.7 PASS at 8e422f8 (route length used when given, otherwise node height with WARNING). Open notes: Eq. (5) multi-segment deferred; 6.3.1 NOTE 1 and bonded-framework exemption not implemented. |
| H3 | High | `risk.py`, `comprehensive_risk.py`, `risk_factors.py` | fixed in code, pending verification | 2.5 | Step 2.5 at 44ec813: Shared helper risk_factors.py (IEC 62305-2:2024 Tables B.3–B.7, C.2). Open items: P_A, R_M/R_U/R_W/R_Z constants, source of P_SPD (S1 vs. per-component), and the removed 0.5 factor (see report). |
| H4 | High | `earthing.py`, `earth_rod_sizing.py` | fixed in code, pending verification | 2.3 | Multi-rod coupling term. Step 2.3 at 16fa0ed: pairwise uniform-leakage mutual coupling, equal-current approximation; reference error at s = L about +14% in R_m and +1.7% in R_2; primary-source confirmation pending. |
| H5 | High | `earthing.py` | fixed in code, pending verification | 2.1, 2.2 | Ring and strip prefactors. Step 2.1 at dcc070d: Ring: Sunde candidate, primary-source pending. Strip: L is now an explicit input. 2.2 (4235bd6): strip model is the round-conductor form, exact with k = 2 − ln 2; flat-strip model not implemented (needs width input and primary source). |
| H6 | High | `uq_engine.py`, `earthing.py` | open | 2.1, 3.2 | UQ inconsistent with earthing. Sobol approximation. |
| H7 | High | `optimization.py` | open | 1.2, 3.3 | Sub-items H7-a to H7-d. Strict xfail `test_design_optimization_coverage_improvement` accepted by the owner (step 1.2, ed7f69d). The label 'roof coverage not verified' is still to be added to the report and UI (later step). Status remains open. |
| H8 | High | `protective_angle.py` | fixed in code, pending verification | 2.4 | Step 2.4 at 3343007: IEC 62305-3:2024 Clause 5.2.2.1 Figure 1 digitized anchors and height domain rules. Figure 1 and Figure 5 values are graphical readings (±1.5°, ±0.5 m); tabulated values not in repo. |
| H9 | High | All modules | fixed in code, pending verification | 2.7 | Step 2.7-B1..B6 commits: d7a2556 (B1), 73c7cdc (B2), 70627fc & dbb14da (B3), bb20a92 (B4), a5b5bee (B5), 78d94c3 (B6). Open sub-items: (a) `touch_step.py` line ~213: `min(1.0, max(0.1, c_s))` clamps a derived value (not user input); to be reviewed. (b) `peec_thermal.py` `initial_temperature_c = 20.0`: quoted text for "20 °C" not found literally in `docs/62305-1-2024.md`; the default is retained as the reference ambient temperature; citation to be grounded. (c) 13 inventory items marked "keep default with documented basis" (listed in the B1–B6 reports) remain subject to supervisor review. (d) H13 (IFC stub) is NOT resolved by B6; only empty and non-STEP inputs are rejected. |
| H10 | High | `docs/33`, `docs/35`, `docs/28`, `docs/29` | open | 0.3 (documentation part only) | Documentation labelled in 0.3. Entry stays `open` until the claims are corrected by code. Progress: 0.3 PASS 171daed (documentation labels). |
| H11 | High | `packages/domain-model/aegislps_domain/integrity.py` | open | 4.3 | Hard-coded HMAC secret. |
| H12 | High | `apps/web/src/App.tsx`, `services/api/aegislps_api/main.py` | open | 4.1, 4.2 | localhost fetch and CORS. |
| H13 | High | `ifc_importer.py` | open | 4.4 | Stub returns fixed dimensions. |
| H14 | High | `tests/` | open | 5.1, 3.4 | Tautological assertions. |
| H15 | High | `spd_coordination.py`, `services/api/aegislps_api/main.py` | fixed in code, pending verification | 2.6 | Step 2.6 at b1114b2: Replaced empirical `l_prot` (`(U_w - U_p) * 10` clamped `[5, 30]`) with IEC 62305-4:2024 Annex C.2.3 & C.2.5 SPD connecting-lead relations (`max_connecting_lead_length_m`, conservative screening bound (C.2.3.1.4) `U_p <= 0.5 * U_w`, Eq. C.1–C.5, required `induced_voltage_kv`). Open items: Annex C.2.3.5 `U_i` calculation not yet automated; Clause C.2.3.4: propagation-length criterion is qualitative; only C.5 (`U_p/f <= U_w`) is implemented. No line-length gate formula is in the standard text; Clause C.2.3.1.2 (≤ 10 m, 80 % of `U_w`) and C.2.3.1.4 (> 10 m, one-port 50 % of `U_w`): code uses `0.5·U_w` for all cases (conservative); distance-dependent rule not modeled; Annex C.2.4 two-port SPD rules not modeled. |
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

## Open pre-existing test items

- `tests/test_distribution.py::test_isolated_clean_wheel_installation_and_smoke_calculation` (`open`): Pre-existing failure (`ModuleNotFoundError: No module named 'aegislps_standards'` in the isolated wheel smoke calculation when `pytest` runs with repository `PYTHONPATH`; also fails at `f6410b3` and `7d9138c`, predating step 2.4). Left open and unmodified in step 2.5.
