# Step 5.1 — H14 Test Suite Audit (`tests/`, excluding `tests/characterization/baseline/*.json`)

- **Base commit audited**: `026cd60` (`026cd60c2e1463c373c5bd10e6dccde78ab9f59c`)
- **Scope**: All 41 Python files under `tests/` (`tests/characterization/baseline/*.json` untouched; `test_design_optimization_coverage_improvement` strict `xfail` for `H7` in `tests/test_optimization_and_pv.py:25-28` preserved unchanged per Step 5.1 Part A.4).
- **Categories**:
  - **(a)** Self-referential or algebraically trivial assertions.
  - **(b)** Hard-clamp or range checks that only confirm the code's own clamp or floor.
  - **(c)** Weak assertions checking only type, existence, sign, finiteness, or wide heuristic bands where an independent reference value is available (or requiring explicit sanity-check disclosure where no independent reference exists).
  - **(d)** Assertions that can never fail (`assert True`, `or True`, conditions guarded by an early `return`, `abs(...) >= 0.0`).

## Summary Counts

| Category | Description | Total Findings | Replaced with Independent Reference | Removed (Redundant with Stronger Assertion) | Not Tightened (No Reference Available; Annotated) |
|---|---|---:|---:|---:|---:|
| **(a)** | Self-referential / algebraically trivial | 1 | 1 | 0 | 0 |
| **(b)** | Code-clamp / floor-confirming range checks | 3 | 2 | 0 | 1 |
| **(c)** | Weak sign / type / finiteness / wide-band checks in calculation tests | 53 | 28 | 2 | 23 |
| **(d)** | Assertions that can never fail | 1 | 1 | 0 | 0 |
| **Total** | **All audited calculation-test findings** | **58** | **32** | **2** | **24** |

- **Files modified in Part A (14 files)**:
  `tests/test_advanced_modules.py`, `tests/test_bom_pv_hvi_opt_peec_nodal_b6.py`, `tests/test_earth_pit_and_rod_sizing.py`, `tests/test_earthing_and_spd.py`, `tests/test_lemp_engine.py`, `tests/test_mesh_method_and_hvi.py`, `tests/test_multi_rod_mutual.py`, `tests/test_nodal_solver.py`, `tests/test_peec_and_mesh_rolling_sphere.py`, `tests/test_risk_inputs_b2.py`, `tests/test_rolling_sphere_reference.py`, `tests/test_touch_lemp_uq_b4.py`, `tests/test_touch_step_physics.py`, `tests/test_uq_engine.py`.
- **Remaining 27 Python files under `tests/`**: Audited line-by-line; 0 additional `(a)`–`(d)` calculation-test findings (`tests/test_optimization_and_pv.py` L25–L28 strict `xfail` for `H7` preserved verbatim per Part A.4; `tests/test_distribution.py` L41 PEP 427 wheel-tag `or` check is a valid packaging check, not tautological).
- `git grep -n -E "assert True|or True" -- tests`: **0 hits**.
- **Possible production defects uncovered by independent-oracle tightening in Part A**: **0** (all 32 tightened reference-value assertions pass; **0** new `H14` `xfail` marks needed).

---

## Complete Finding Table (1 Row per Assertion, Line Numbers at Base `026cd60`)

| # | File | Line (`026cd60`) | Category | Original Assertion | Action Taken | Independent Reference / Basis |
|---:|---|---:|:---:|---|---|---|
| 1 | `tests/test_advanced_modules.py` | 67 | c | `assert res.collection_area_ad_m2 > 0` | Replaced | `pytest.approx(11461.7, abs=0.1)` — IEC 62305-2:2024 Annex A `A_D = L*W + 6H(L+W) + 9*pi*H^2` (`30*20 + 6*15*50 + 9*pi*225 = 11461.725 m^2`) |
| 2 | `tests/test_advanced_modules.py` | 68 | c | `assert res.annual_strikes_nd > 0` | Replaced | `pytest.approx(0.028654312809, rel=1e-6)` (`N_D = N_G*A_D*C_D*1e-6`), plus `R_B = 7.1635782022e-8` and `R_C = 3.5817891011e-8` per IEC 62305-2:2024 Tables B.3–B.7 & C.2 |
| 3 | `tests/test_advanced_modules.py` | 69 | c | `assert isinstance(res.risk_acceptable, bool)` | Replaced | `assert res.risk_acceptable is True` — IEC 62305-2 Table 4 tolerable threshold `R_T = 1e-5` |
| 4 | `tests/test_bom_pv_hvi_opt_peec_nodal_b6.py` | 493 | c | `assert m_ij > 0.0 and math.isfinite(m_ij)` | Replaced | `pytest.approx(2.093235388186e-06, rel=1e-6)` — closed-form parallel-filament double integral `2e-7 * [5*asinh(10) - sqrt(25.25) + 0.5]` (`formula and source to be confirmed by owner`) |
| 5 | `tests/test_earth_pit_and_rod_sizing.py` | 19 | b | `assert res.pit_inner_diameter_mm >= 250.0` | Not tightened (annotated) | Sanity check only — `earth_pit.py` maps all valid loading classes to `{250, 300, 320}` mm; no IEC 62561-5 / EN 124 inner-diameter table in `docs/` |
| 6 | `tests/test_earth_pit_and_rod_sizing.py` | 20 | c | `assert res.backfill_volume_m3 > 0.01` | Replaced | `pytest.approx(0.023, abs=1e-3)` — cylindrical annulus `pi*(0.05^2 - 0.008^2)*3.0 = 0.022959 m^3` (plus Dwight `unconditioned_resistance_single_rod_ohm == pytest.approx(50.24, abs=0.01)`) |
| 7 | `tests/test_earth_pit_and_rod_sizing.py` | 21 | c | `assert res.number_of_25kg_bags > 0` | Not tightened (annotated) | Sanity check only — backfill density/`rho_c` values have no primary source in `docs/` (open `M6`) |
| 8 | `tests/test_earth_pit_and_rod_sizing.py` | 23 | c | `assert res.resistance_reduction_percentage > 20.0` | Not tightened (annotated) | Sanity check only — conditioned resistance reduction depends on unsourced `rho_c` (open `M6`) |
| 9 | `tests/test_earth_pit_and_rod_sizing.py` | 40 | b | `assert res_cu.coating_thickness_um >= 250.0` | Replaced | `assert res_cu.coating_thickness_um == 250.0` — IEC 62561-2 Table 1 minimum copper-coating thickness (`250 um`) |
| 10 | `tests/test_earth_pit_and_rod_sizing.py` | 42 | c | `assert res_cu.required_number_of_rods >= 2` | Replaced | `assert res_cu.required_number_of_rods == 5` (plus `single_rod_resistance_ohm == pytest.approx(40.19, abs=0.01)` from Dwight `R_1 = 40.1912 ohm`; even zero-coupling `R_1/4 = 10.048 > 10.0 ohm` requires `N >= 5`) |
| 11 | `tests/test_earth_pit_and_rod_sizing.py` | 43 | c | `assert res_cu.total_array_resistance_ohm <= 10.0` | Not tightened (annotated) | Sanity check only — multi-rod mutual-coupling primary source pending (`H4`); checks sizing target `<= 10.0 ohm` (IEC 62305-3:2024 Clause 5.4.1) |
| 12 | `tests/test_earth_pit_and_rod_sizing.py` | 58 | c | `assert res_galv.total_array_resistance_ohm <= 10.0` | Not tightened (annotated) | Sanity check only — multi-rod mutual-coupling primary source pending (`H4`), supplemented with Dwight `single_rod_resistance_ohm == pytest.approx(25.85, abs=0.01)` |
| 13 | `tests/test_earthing_and_spd.py` | 20 | c | `assert res.minimum_length_l1_m > 0` | Replaced | `assert res.minimum_length_l1_m == 5.0` — IEC 62305-3:2024 Clause 5.4.2.2 Figure 5 (Class I at `rho = 100 <= 500 ohm.m`) |
| 14 | `tests/test_earthing_and_spd.py` | 21 | c | `assert res.actual_effective_length_m > res.minimum_length_l1_m` | Not tightened (annotated) | Sanity check only — Type B `r_e >= l1` vs circumference rule is open under `C4` |
| 15 | `tests/test_earthing_and_spd.py` | 22 | c | `assert res.stationary_resistance_r_ohm > 0` | Not tightened (annotated) | Sanity check only — Sunde ring primary source pending under `H5` |
| 16 | `tests/test_earthing_and_spd.py` | 23 | c | `assert res.impulse_impedance_z_ohm <= res.stationary_resistance_r_ohm` | Not tightened (annotated) | Sanity check only — soil-ionization impulse reduction has no primary source in `docs/` |
| 17 | `tests/test_earthing_and_spd.py` | 40 | c | `assert res.stationary_resistance_r_ohm > 0` | Not tightened (annotated) | Sanity check only — no independent multi-rod reference at `s/L = 5/3` (open `H4`) |
| 18 | `tests/test_earthing_and_spd.py` | 41 | c | `assert res.impulse_efficiency_factor < 1.0` | Not tightened (annotated) | Sanity check only — soil-ionization impulse efficiency has no primary source in `docs/` |
| 19 | `tests/test_earthing_and_spd.py` | 119 | c | `assert angle_2m > angle_18m` | Removed | Redundant with tightened `70.0 ± 1.5°` and `27.4 ± 1.5°` assertions in `test_protective_angle_non_linear_decay` |
| 20 | `tests/test_earthing_and_spd.py` | 120 | c | `assert 60.0 <= angle_2m <= 75.0` | Replaced | `pytest.approx(70.0, abs=1.5)` — IEC 62305-3:2024 Clause 5.2.2.1 Figure 1 (`±1.5°` graphical digitization tolerance) |
| 21 | `tests/test_earthing_and_spd.py` | 121 | c | `assert 20.0 <= angle_18m <= 35.0` | Replaced | `pytest.approx(27.4, abs=1.5)` — IEC 62305-3:2024 Clause 5.2.2.1 Figure 1 (`±1.5°` graphical digitization tolerance) |
| 22 | `tests/test_earthing_and_spd.py` | 147 | c | `assert res.collection_area_ad_m2 > 0` | Replaced | `pytest.approx(20109.7, abs=0.1)` (plus `N_D = 0.050274333882`, `R_B = 1.2568583471e-7`, `R_C = 6.2842917353e-8`) — IEC 62305-2:2024 Annex A & Tables B.3–B.7, C.2 |
| 23 | `tests/test_earthing_and_spd.py` | 148 | c | `assert res.risk_r1_loss_of_life > 0` | Not tightened (annotated) | Sanity check only — total `R_1` includes `R_A` whose `P_A` factor is open under `H3` |
| 24 | `tests/test_earthing_and_spd.py` | 149 | a | `assert res.risk_r1_loss_of_life == pytest.approx(res.risk_ra_touch_step + res.risk_rb_physical_damage + res.risk_rc_internal_systems)` | Replaced | Anchored non-zero `R_B` and `R_C` against independent IEC 62305-2:2024 Tables B.3–B.7 & C.2 references so Clause 4.3 additivity check cannot pass on all-zero outputs |
| 25 | `tests/test_lemp_engine.py` | 20 | c | `assert 28.0 <= peak_time <= 35.0` | Replaced | `pytest.approx(31.4278, abs=0.11)` — exact stationary root of IEC 62305-1:2024 Table A.1 Heidler 10/350 (`tau1=19 us, tau2=485 us, n=10`) on `0.1001 us` grid |
| 26 | `tests/test_lemp_engine.py` | 21 | c | `assert max_di_dt > 0.0` | Replaced | `pytest.approx(13.6624, rel=1e-3)` — closed-form maximum `di/dt` of IEC 62305-1:2024 Table A.1 Heidler 10/350 at `I = 100 kA` |
| 27 | `tests/test_lemp_engine.py` | 52 | c | `assert res_unshielded.unattenuated_peak_h_field_a_per_m > 0` | Replaced | `pytest.approx(7967.9, abs=0.2)` — IEC 62305-4:2024 Annex A Eq. (A.6) `H_0,max = i_max / (2*pi*s_a)` at `s_a = 2.0 m` |
| 28 | `tests/test_lemp_engine.py` | 66 | c | `assert res_shielded.peak_induced_voltage_kv < res_unshielded.peak_induced_voltage_kv` | Replaced | `pytest.approx(0.3215, abs=2e-3)` and `(2.0/8.5) * unshielded` — Faraday-Maxwell loop induction + IEC 62305-4:2024 Table A.4 `K_MS = 2.0 / 8.5` |
| 29 | `tests/test_lemp_engine.py` | 67 | c | `assert len(res_shielded.current_waveform_ka) > 0` | Not tightened (annotated) | Sanity check only — UI downsampled waveform serialization length, not a standard value |
| 30 | `tests/test_lemp_engine.py` | 68 | c | `assert len(res_shielded.induced_voltage_waveform_kv) > 0` | Not tightened (annotated) | Sanity check only — UI downsampled waveform serialization length, not a standard value |
| 31 | `tests/test_mesh_method_and_hvi.py` | 81 | c | `assert bom.total_components_count > 0` | Not tightened (annotated) | Sanity check only — no standard defines BOM catalog line-item count (see `M3`) |
| 32 | `tests/test_multi_rod_mutual.py` | 105 | c | `assert math.isfinite(f_new) and f_new >= 1.0` | Not tightened (annotated) | Sanity check only — diagnostic report-only table at `s = 2L`; primary source pending (`H4`) |
| 33 | `tests/test_nodal_solver.py` | 36 | c | `assert pytest.approx(res["kc_factors"]["s1"], 0.05) == 0.5` | Replaced | `pytest.approx(0.5, rel=1e-12)` — exact two-branch symmetry |
| 34 | `tests/test_nodal_solver.py` | 37 | c | `assert pytest.approx(res["kc_factors"]["s2"], 0.05) == 0.5` | Replaced | `pytest.approx(0.5, rel=1e-12)` — exact two-branch symmetry |
| 35 | `tests/test_nodal_solver.py` | 38 | c | `assert res["relative_residual"] < 0.01` | Replaced | `assert res["relative_residual"] <= 1e-12` — exact linear KCL residual |
| 36 | `tests/test_nodal_solver.py` | 75 | c | `assert res["kc_factors"]["s_low_res"] > res["kc_factors"]["s_high_res"]` | Replaced | Closed-form AC parallel current divider (`kc_low = 0.584648271409`, `kc_high = 0.415351732210`, `rel=1e-9`) |
| 37 | `tests/test_nodal_solver.py` | 93 | c | `assert len(res["warnings"]) > 0` | Replaced | `assert any("galvanically isolated" in w for w in res["warnings"])` |
| 38 | `tests/test_nodal_solver.py` | 159 | c | `assert "down1" in res["kc_factors"]` | Replaced | `pytest.approx(0.667434596333, rel=1e-9)` — closed-form symmetric half-ring series-parallel reduction |
| 39 | `tests/test_nodal_solver.py` | 160 | c | `assert "down2" in res["kc_factors"]` | Replaced | `pytest.approx(0.332565403667, rel=1e-9)` — closed-form symmetric half-ring series-parallel reduction |
| 40 | `tests/test_nodal_solver.py` | 161 | d | `assert res["conservation_residual_a"] >= 0.0` | Replaced | Cannot fail (`abs(...) >= 0.0`); replaced with KCL phasor earth-current conservation `<= 1e-9 * 100000.0` |
| 41 | `tests/test_nodal_solver.py` | 163 | c | `assert res["condition_number_estimate"] > 0` | Not tightened (annotated) | Sanity check only (`>= 1.0`) — solver-internal diagonal-ratio heuristic (`max|Y_ii| / min|Y_ii|`), no physical reference |
| 42 | `tests/test_peec_and_mesh_rolling_sphere.py` | 25 | c | `assert m_val > 0.0` | Removed | Redundant with tightened `2.093235388186e-06 H` assertion in `test_neumann_mutual_inductance_parallel_segments` |
| 43 | `tests/test_peec_and_mesh_rolling_sphere.py` | 27 | c | `assert 1e-7 <= m_val <= 1e-5` | Replaced | `pytest.approx(2.093235388186e-06, rel=1e-6)` — closed-form parallel-filament double integral (`formula and source to be confirmed by owner`) |
| 44 | `tests/test_peec_and_mesh_rolling_sphere.py` | 135 | c | `assert res.peak_repulsive_force_n_per_m > 0.0` | Replaced | `pytest.approx(20000.0, rel=1e-6)` — Ampère parallel-filament force `(mu_0/(2*pi))*i_1*i_2/d` for IEC 62305-1:2024 Table 3 Class I `I = 200 kA` (`i_1 = i_2 = 100 kA`, `d = 0.1 m`) |
| 45 | `tests/test_peec_and_mesh_rolling_sphere.py` | 179 | c | `assert comp.r_a_touch_step > 0` | Not tightened (annotated) | Sanity check only — `P_A` / `C_TWS` constants open under `H3` |
| 46 | `tests/test_peec_and_mesh_rolling_sphere.py` | 180 | c | `assert comp.r_b_physical_damage > 0` | Replaced | `pytest.approx(3.3029312809e-7, rel=1e-6)` (plus `A_D = 13211.7 m^2`, `R_C = 1.6514656404e-7`) — IEC 62305-2:2024 Annex A & Tables B.3–B.7, C.2 |
| 47 | `tests/test_peec_and_mesh_rolling_sphere.py` | 181 | c | `assert comp.r_u_touch_voltage_service > 0` | Not tightened (annotated) | Sanity check only — `R_U` service-line factor open under `H3` |
| 48 | `tests/test_peec_and_mesh_rolling_sphere.py` | 182 | c | `assert comp.total_risk_r1 > 0` | Not tightened (annotated) | Sanity check only — total `R_1` sums open `H3` components alongside verified `R_B`/`R_C` |
| 49 | `tests/test_peec_and_mesh_rolling_sphere.py` | 183 | c | `assert res.collection_area_al_services_m2 > 0` | Not tightened (annotated) | Sanity check only — service-line collection width constant pending `H3` verification |
| 50 | `tests/test_risk_inputs_b2.py` | 294 | c | `assert resp_risk_ok.json()["risk_r1_loss_of_life"] > 0.0` | Not tightened (annotated) | Sanity check retained for total `R_1` (open `H3` component `R_A`), supplemented with IEC 62305-2:2024 `A_D = 11461.7` and `R_B = 2.8654312809e-7` |
| 51 | `tests/test_risk_inputs_b2.py` | 301 | c | `assert resp_comp_ok.json()["risk_components"]["total_risk_r1"] > 0.0` | Not tightened (annotated) | Sanity check retained for total `R_1` (open `H3` components), supplemented with IEC 62305-2:2024 `A_D = 13211.7` and `R_B = 3.3029312809e-7` |
| 52 | `tests/test_rolling_sphere_reference.py` | 84 | c | `assert math.isfinite(rho_ground) and rho_ground > 0.0` | Not tightened (annotated) | Sanity check only — no independent IEC 62305-3 reference for point-tip vs mast-shaft contact when `R < h <= 2R` (`h = 1.5 R`) |
| 53 | `tests/test_rolling_sphere_reference.py` | 85 | c | `assert math.isfinite(rho_mid) and rho_mid >= 0.0` | Not tightened (annotated) | Sanity check only — no independent IEC 62305-3 reference for point-tip vs mast-shaft contact when `R < h <= 2R` (`h = 1.5 R`) |
| 54 | `tests/test_touch_lemp_uq_b4.py` | 162 | b | `assert 0.1 <= res.surface_derating_factor_cs < 1.0` | Replaced | Only confirmed `touch_step.py:213` clamp `[0.1, 1.0]`; replaced with IEEE Std 80-2013 Eq. (27) `1 - 0.09*(1 - 100/2500)/(2*0.05 + 0.09) = 0.545` (`abs=1e-3`) |
| 55 | `tests/test_touch_lemp_uq_b4.py` | 485 | c | `assert res_shielded.grid_shielding_factor_kms < 1.0` | Replaced | `pytest.approx(2.0 / 8.5, abs=1e-3)` — IEC 62305-4:2024 Table A.4 (`SF = 20*log10(8.5/2.0) = 12.5678 dB`, `K_MS = 2.0/8.5 = 0.2353`) |
| 56 | `tests/test_touch_step_physics.py` | 195 | c | `assert res.prospective_touch_voltage_v > 0.0` | Replaced | `pytest.approx(3333.3, abs=0.1)` — hemispherical potential `GPR - GPR*r_e/(r_e + 1) = 10000 - 20000/3` |
| 57 | `tests/test_touch_step_physics.py` | 196 | c | `assert res.prospective_step_voltage_v > 0.0` | Replaced | `pytest.approx(1666.7, abs=0.1)` — hemispherical potential `V(1) - V(2) = 20000/3 - 5000` |
| 58 | `tests/test_uq_engine.py` | 25 | c | `assert res.mean_s_req_m > 0.4` | Replaced | `pytest.approx(0.6501, abs=0.02)` — closed-form expectation `0.08 * 0.5 * 15.0 * (ln(1/0.85)/0.15) = 0.6501 m` |

---

## Items Not Tightened — No Independent Reference Available (24 Assertions)

1. `tests/test_earth_pit_and_rod_sizing.py:19` (`pit_inner_diameter_mm >= 250.0`, Category b) — no IEC 62561-5 / EN 124 inner-diameter table in `docs/`.
2. `tests/test_earth_pit_and_rod_sizing.py:21` (`number_of_25kg_bags > 0`, Category c) — backfill density/`rho_c` values unsourced (`M6`).
3. `tests/test_earth_pit_and_rod_sizing.py:23` (`resistance_reduction_percentage > 20.0`, Category c) — depends on unsourced `rho_c` (`M6`).
4. `tests/test_earth_pit_and_rod_sizing.py:43` (`res_cu.total_array_resistance_ohm <= 10.0`, Category c) — multi-rod mutual-coupling primary source pending (`H4`).
5. `tests/test_earth_pit_and_rod_sizing.py:58` (`res_galv.total_array_resistance_ohm <= 10.0`, Category c) — multi-rod mutual-coupling primary source pending (`H4`).
6. `tests/test_earthing_and_spd.py:21` (`actual_effective_length_m > minimum_length_l1_m`, Category c) — Type B `r_e >= l1` vs circumference rule open (`C4`).
7. `tests/test_earthing_and_spd.py:22` (`stationary_resistance_r_ohm > 0`, Category c) — Sunde ring primary source pending (`H5`).
8. `tests/test_earthing_and_spd.py:23` (`impulse_impedance_z_ohm <= stationary_resistance_r_ohm`, Category c) — soil-ionization model has no primary source in `docs/`.
9. `tests/test_earthing_and_spd.py:40` (`stationary_resistance_r_ohm > 0`, Category c) — no independent multi-rod reference at `s/L = 5/3` (`H4`).
10. `tests/test_earthing_and_spd.py:41` (`impulse_efficiency_factor < 1.0`, Category c) — soil-ionization model has no primary source in `docs/`.
11. `tests/test_earthing_and_spd.py:148` (`risk_r1_loss_of_life > 0`, Category c) — total `R_1` includes `R_A` whose `P_A` factor is open (`H3`).
12. `tests/test_lemp_engine.py:67` (`len(current_waveform_ka) > 0`, Category c) — downsampled UI serialization length, not a standard value.
13. `tests/test_lemp_engine.py:68` (`len(induced_voltage_waveform_kv) > 0`, Category c) — downsampled UI serialization length, not a standard value.
14. `tests/test_mesh_method_and_hvi.py:81` (`bom.total_components_count > 0`, Category c) — no standard defines BOM catalog line-item count (`M3`).
15. `tests/test_multi_rod_mutual.py:105` (`math.isfinite(f_new) and f_new >= 1.0`, Category c) — report-only diagnostic table at `s = 2L`; primary source pending (`H4`).
16. `tests/test_nodal_solver.py:163` (`condition_number_estimate > 0`, updated to `>= 1.0`, Category c) — solver-internal diagonal-ratio heuristic.
17. `tests/test_peec_and_mesh_rolling_sphere.py:179` (`comp.r_a_touch_step > 0`, Category c) — `P_A` / `C_TWS` constants open (`H3`).
18. `tests/test_peec_and_mesh_rolling_sphere.py:181` (`comp.r_u_touch_voltage_service > 0`, Category c) — `R_U` service-line factor open (`H3`).
19. `tests/test_peec_and_mesh_rolling_sphere.py:182` (`comp.total_risk_r1 > 0`, Category c) — total `R_1` sums open `H3` components.
20. `tests/test_peec_and_mesh_rolling_sphere.py:183` (`res.collection_area_al_services_m2 > 0`, Category c) — service-line collection width constant pending `H3`.
21. `tests/test_risk_inputs_b2.py:294` (`risk_body["risk_r1_loss_of_life"] > 0.0`, Category c) — total `R_1` includes open `H3` component `R_A` (supplemented with verified `A_D` and `R_B`).
22. `tests/test_risk_inputs_b2.py:301` (`comp_body["risk_components"]["total_risk_r1"] > 0.0`, Category c) — total `R_1` includes open `H3` components (supplemented with verified `A_D` and `R_B`).
23. `tests/test_rolling_sphere_reference.py:84` (`math.isfinite(rho_ground) and rho_ground > 0.0`, Category c) — no independent IEC 62305-3 reference for `R < h <= 2R` point-tip vs mast-shaft contact.
24. `tests/test_rolling_sphere_reference.py:85` (`math.isfinite(rho_mid) and rho_mid >= 0.0`, Category c) — no independent IEC 62305-3 reference for `R < h <= 2R` point-tip vs mast-shaft contact.
