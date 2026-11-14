# Step 6.6 independent-oracle and semantic-mutation review

Baseline `d9ee3ab`. Tests and mutations ran in archive scratch trees with scratch paths first in `PYTHONPATH`; mutations were reverted between cases and scratch trees deleted. No test files were adapted. Where a listed historical code block spans several statements, all substituted statements are shown. Full H3 failures include unrelated interface incompatibilities and must not be counted as independent physics evidence. A verified label is narrowly scoped to the tested behavior, not other open sub-items.

| Item | Fix | Oracle test/source | Failures | Decision |
|---|---|---|---:|---|
| C1 | `2e3188a` | tests/test_rolling_sphere_reference.py::test_reference_points_r20_h10 | 5 | pending: no independent oracle; numeric boundary values lack a test-comment derivation or independently cited formula; C1b/H7 also remain open |
| C2 | `19a607a` | tests/test_touch_step_physics.py::test_no_zero_by_flag_path — hand calculation in test comment, V(x)=GPR·r/(r+x), 3333.3 V and 1666.7 V | 3 | verified (step 6.6, independent oracle + semantic mutation) |
| C3 | `1347b14, 434a727` | tests/test_lemp_heidler_physics.py::test_heidler_parameter_table_matches_iec_62305_1 — IEC 62305-1:2024 Annex B Table B.1 (test docstring incorrectly says A.1) | 4 | verified (step 6.6, independent oracle + semantic mutation) |
| C3-b | `215c248, 6719bb9` | tests/test_lemp_induction_physics.py::test_07_table_a6_shielded_magnetic_field_cases — IEC 62305-4:2024 Annex A Table A.6 | 9 | verified (step 6.6, independent oracle + semantic mutation) |
| C4 | `ec571e8` | tests/test_rolling_sphere_edition2024.py::test_table_2_radii_by_lps_class — IEC 62305-3:2024 §5.2.2.1 Table 2 | 2 | verified (step 6.6, independent oracle + semantic mutation) for radii only; C4-b compliance remains open |
| C4-b | `3343007` | tests/test_minimum_length_l1_figure5.py::test_class_i_l1_figure5_values — claimed graphical IEC 62305-3 §5.4.2.2 Figure 5; curve missing from available text | 4 | pending: no independent oracle; original Figure 5 graph and independent graphical readings required; Type A/B compliance also open |
| H3 | `44ec813` | tests/test_risk_factors_2024.py::test_table_c2_row3_normal_upper_bound — IEC 62305-2:2024 Annex C Table C.2 | 58 | pending: failing end-to-end tests compare two engines; independently sourced table oracle does not fail this legacy-loss mutation, and other risk-factor scope remains open |
| H4 | `16fa0ed` | tests/test_multi_rod_mutual.py::test_r_m_reference_values — numerical approximation, primary source not established | 1 | pending: no independent oracle; primary source for uniform-leakage mutual model required |
| H5 | `dcc070d, 4235bd6` | tests/test_earthing_ring_strip.py::test_ring_sunde_matches_independent_values_within_1e6_rel — formula hand calculations; independent primary-source confirmation pending | 4 | pending: no independent oracle; primary source for Sunde ring and flat-strip formula required; flat-strip model not implemented |
| H8 | `3343007` | tests/test_protective_angle_figure1.py::test_figure1_anchor_values — claimed digitized IEC 62305-3 §5.2.2.1 Figure 1; curve missing from available text | 2 | pending: no independent oracle; original Figure 1 graph and independent digitization required |
| H9 | `73c7cdc and B1–B6` | tests/test_risk_inputs_b2.py::test_a3_risk_lps_class_required_and_validated — explicit missing-field validation contract, no independent physics-value source | 1 | pending: no independent oracle and no physics expression mutation for strict validation; other B1–B6 cases remain |
| H15 | `b1114b2` | tests/test_spd_coordination_annex_c.py::test_equation_c4_lead_voltage_drop_10ka_1m — IEC 62305-4:2024 §C.2.3.3 Eq. (C.4), 10 kA × 0.1 kV/kA/m × 1 m = 1 kV; end-to-end Lmax = 1 m | 4 | verified (step 6.6, independent oracle + semantic mutation) for connecting-lead formula; other Annex C rules remain open |

## Mutations and first three failures

### C1 — `packages/geometry/aegislps_geometry/rolling_sphere.py:148–153`

Before:

```python
max_axial_protected_z = min(h_val, 2.0 * r_val - h_val)
        is_protected = (
            z_val <= h_val
            and d_horiz <= rho_allowed
            and (rho_allowed > 0.0 or (d_horiz == 0.0 and z_val <= max_axial_protected_z))
        )
```

After (scratch only):

```python
z_protect = rod_height_m - (self.r - np.sqrt(max(0.0, self.r**2 - d_horiz**2)))

        is_protected = point_z <= z_protect
```

5 failed tests. First 3:

- `tests/test_rolling_sphere_reference.py::test_reference_points_r20_h10`
- `tests/test_rolling_sphere_reference.py::test_counterexample_edge_midpoint_exposed_public_api`
- `tests/test_optimization_conservative.py::test_regression_h7a_preserves_best_state_after_late_degradation`

### C2 — `services/calculation-engine/aegislps_engine/touch_step.py:312`

Before:

```python
touch_controlled = prospective_touch <= u_touch_tol
```

After (scratch only):

```python
if inp.has_physical_insulation_barrier:
    prospective_touch = 0.0
    prospective_step = min(prospective_step, u_step_tol * 0.5)
if inp.has_restricted_access_perimeter:
    prospective_touch = 0.0
    prospective_step = 0.0
touch_controlled = prospective_touch <= u_touch_tol
```

3 failed tests. First 3:

- `tests/test_touch_step_physics.py::test_mitigation_flags_do_not_change_voltages`
- `tests/test_touch_step_physics.py::test_fence_only_scenario_is_not_compliant`
- `tests/test_touch_step_physics.py::test_no_zero_by_flag_path`

### C3 — `services/calculation-engine/aegislps_engine/lemp_engine.py:10`

Before:

```python
"tau1": 19.0
```

After (scratch only):

```python
"tau1": 10.0  # 1347b14^ uses tau1 = 10.0
```

4 failed tests. First 3:

- `tests/test_lemp_heidler_physics.py::test_heidler_parameter_table_matches_iec_62305_1`
- `tests/test_lemp_heidler_physics.py::test_heidler_peak_current_within_one_percent[first_positive_10_350-100.0]`
- `tests/test_lemp_heidler_physics.py::test_max_di_dt_matches_reference_values`

### C3-b — `services/calculation-engine/aegislps_engine/lemp_engine.py:495`

Before:

```python
kms = float(10.0 ** (-sf_db / 20.0))
```

After (scratch only):

```python
kms = float(min(1.0, max(0.005, 0.01 * shield.mesh_width_w_m)))  # from 215c248^
```

9 failed tests. First 3:

- `tests/test_lemp_induction_physics.py::test_01_copper_w2m_unbonded`
- `tests/test_lemp_induction_physics.py::test_02_copper_w2m_meshed_bonding`
- `tests/test_lemp_induction_physics.py::test_03_copper_w10m_negative_sf_clamped_to_zero`

### C4 — `packages/geometry/aegislps_geometry/rolling_sphere.py:20`

Before:

```python
"III": 45.0,
```

After (scratch only):

```python
"III": 200.0,
```

2 failed tests. First 2:

- `tests/test_rolling_sphere_edition2024.py::test_table_2_radii_by_lps_class[III-45.0]`
- `tests/test_rolling_sphere_edition2024.py::test_no_radius_outside_table_2_for_classes_i_through_iv`

### C4-b — `services/calculation-engine/aegislps_engine/earthing.py:413`

Before:

```python
return 5.0 if rho_f <= 500.0 else float(0.03 * rho_f - 10.0)
```

After (scratch only):

```python
return float(min(20.0, max(5.0, 20.0 * (rho / 800.0)))) if rho >= 100.0 else 5.0
```

4 failed tests. First 3:

- `tests/test_minimum_length_l1_figure5.py::test_class_i_l1_figure5_values[500.0-5.0]`
- `tests/test_minimum_length_l1_figure5.py::test_class_i_l1_figure5_values[2000.0-50.0]`
- `tests/test_minimum_length_l1_figure5.py::test_class_i_l1_figure5_values[3000.0-80.0]`

### H3 — `services/calculation-engine/aegislps_engine/risk.py:229`

Before:

```python
l_f = loss_vals.l_f1 * t_occupancy
```

After (scratch only):

```python
l_f = 0.1 * inputs.fire_risk_rf * (0.5 if inputs.has_automatic_fire_system else 1.0) * t_occupancy
```

58 failed tests. First 3:

- `tests/test_risk_factors_2024.py::test_rp_applied_once_in_pb_and_legacy_half_factor_removed`
- `tests/test_risk_factors_2024.py::test_cross_engine_consistency_pb_pspd_and_loss[True-very_high-none-standard]`
- `tests/test_risk_factors_2024.py::test_cross_engine_consistency_pb_pspd_and_loss[True-very_high-IV-standard]`

### H4 — `services/calculation-engine/aegislps_engine/earthing.py:459`

Before:

```python
r_dc = array_resistance_identical_rods(rho, l_rod, r_cond, n_rods, s_spacing)
```

After (scratch only):

```python
r_single = (rho / (2.0 * np.pi * l_rod)) * (np.log(4.0 * l_rod / r_cond) - 1.0)

            # Mutual coupling array efficiency factor eta (IEEE 80 / Tagg model)
            # eta ~ (1 + alpha * (L / s)) / N
            if n_rods > 1:
                coupling_factor = (l_rod / (2.0 * np.pi * s_spacing)) * np.log(1.0 + (s_spacing / l_rod))
                r_dc = float((r_single / n_rods) * (1.0 + (n_rods - 1) * coupling_factor))
            else:
                r_dc = float(r_single)
```

1 failed tests. First 1:

- `tests/test_multi_rod_mutual.py::test_earthing_engine_vertical_multi_rod_uses_pairwise_mutual`

### H5 — `services/calculation-engine/aegislps_engine/earthing.py:437–443`

Before:

```python
r_dc = float(
                (rho / ((np.pi ** 2) * d_ring))
                * np.log((4.0 * d_ring) / equiv_radius)
            )
```

After (scratch only):

```python
term1 = np.log((8.0 * d_ring) / r_cond)
            term2 = np.log((4.0 * d_ring) / h_depth)
            r_dc = float((rho / (2.0 * (np.pi ** 2) * d_ring)) * (term1 + term2))
```

4 failed tests. First 3:

- `tests/test_earthing_ring_strip.py::test_ring_sunde_matches_independent_values_within_1e6_rel[100.0-15.0-0.01-0.5-2.512-2.511634078340987]`
- `tests/test_earthing_ring_strip.py::test_ring_sunde_matches_independent_values_within_1e6_rel[250.0-8.0-0.016-0.8-10.03-10.034023844537897]`
- `tests/test_earthing_ring_strip.py::test_ring_sunde_matches_independent_values_within_1e6_rel[50.0-30.0-0.008-0.6-0.6882-0.688157318897246]`

### H8 — `packages/geometry/aegislps_geometry/protective_angle.py:29`

Before:

```python
(20.0, 22.4)
```

After (scratch only):

```python
(20.0, 25.0)
```

2 failed tests. First 2:

- `tests/test_protective_angle_figure1.py::test_figure1_anchor_values[I-20.0-22.4-False]`
- `tests/test_protective_angle_figure1.py::test_figure1_endpoints_at_h_max[I-20.0-22.4]`

### H9 — `services/calculation-engine/aegislps_engine/risk.py:111`

Before:

```python
lps_class: str  # Required: one of {"none", "I", "II", "III", "IV"}
```

After (scratch only):

```python
lps_class: str = "I"  # Class I, II, III, IV, or none
```

1 failed tests. First 1:

- `tests/test_risk_inputs_b2.py::test_a3_risk_lps_class_required_and_validated`

### H15 — `services/calculation-engine/aegislps_engine/spd_coordination.py:305`

Before:

```python
return float(numerator_kv / denom_kv_per_m)
```

After (scratch only):

```python
return float(max(5.0, min(30.0, (u_req_kv - up_kv) * 10.0)))  # historical heuristic, current u_req used as a proxy for former uw
```

4 failed tests. First 3:

- `tests/test_spd_coordination_annex_c.py::test_equation_c4_lead_voltage_drop_10ka_1m`
- `tests/test_spd_coordination_annex_c.py::test_limiting_vs_switching_give_distinct_l_max_for_identical_inputs`
- `tests/test_spd_coordination_annex_c.py::test_equipment_side_stage_selects_smallest_up_type2_or_type3_and_missing_stage_fails`

The H15 heuristic maps current `u_req_kv` to the former `uw_kv`; it is a deliberately wrong semantic analogue, not a claim of an exact historical interface. H9 mutates a validation default rather than a physics expression and cannot satisfy the physics-mutation criterion. H3 uses an old expression referencing later optional inputs; its failure count contains interface failures. H4/H5 numerical tests do not establish the correctness of their unsourced primary formulas. Figure 1 and Figure 5 graphical readings require the missing graph, not just their text captions.

## Baseline and acceptance notes

- A1: The table contains every requested item and sub-item, with failures and candidate oracles; H4/H5 and other pending rows explicitly identify missing sources. Details above contain before/after expressions and first three failures.
- A2: Verified labels apply only to the indicated behaviors with independent value checks and mutation failures. Pending items were not promoted; H9 is a validation default mutation, not a physics mutation.
- A3: The H10 batches cover all 99 marker lines; see `step65_h10_claim_inventory.md` for 143 claim rows, status counts, non-claim reasons, and unapplied proposals.
- A4: Register reflects those scoped results; H10 remains open. M1, M2 and M6 remain fixed in code, pending verification.
- A5: `npm run build --workspace=apps/web` exited 0 with a large-chunk warning.
- B1: `/tmp/step66-venv/bin/pytest -q` at repository root: 1 failed (`tests/test_distribution.py::test_isolated_clean_wheel_installation_and_smoke_calculation`), 1146 passed, 1 xfailed, 1 warning; exit 1. No tests were changed, deleted or newly marked xfail.
- B2: No characterization baseline JSON changes against `d9ee3ab`.
- B3: `git grep -n SECRET_SALT -- . ':!docs'` returned no matches.
- B4: `pgrep -af '[u]vicorn'` returned no stray processes.
- B5: No changes under `packages/` or `services/`; final stat is included in the step report.

The H10 inventory identifies potential density/line-exposure and fastener-spacing issues in addition to H10-a and H10-b. These are design proposals, not implemented changes or owner deferrals. The standard text supplied here contains Figure 1 and Figure 5 captions but not their plotted curves. The isolated-wheel distribution failure and CI triggers are unchanged.
