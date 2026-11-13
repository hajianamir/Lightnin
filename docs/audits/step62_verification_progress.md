# Step 6.2 verification progress — incomplete

Base `d9f5383`. The table below records tests run against the current branch and scratch mutation checks, but the mutation changes were selected perturbations and are **not all reversions to the original fix's key line**. They therefore do not satisfy the requested mutation method. Scratch copy was made with `git archive HEAD`, Python package paths were explicitly set to the copy, and it was deleted afterward. Tests of the unmutated branch passed except the already strict-xfailed H7 test. Counts are pytest tests per file; warnings omitted below. No item is promoted to verified on this evidence alone.

| Item | Pinning tests run (exact counts) | Scratch perturbation; representative detected failure | Register status |
|---|---|---|---|
| C1 / C1b | `test_rolling_sphere_reference.py` 14; `test_optimization_conservative.py` 6 | `rho_c - offset` → `rho_c + offset`; `test_reference_points_r20_h10` fails; not the original code | open; H7 roof coverage remains open |
| C2 | `test_touch_step_physics.py` 9 | divide prospective touch by 10; `test_manual_hemispherical_prospective_voltages` fails; not exact original implementation | open |
| C3 | `test_lemp_heidler_physics.py` 13 | first-stroke tau1 19 → 10; parameter-table test fails | open; C3-b mutation below is not exact |
| C3-b | `test_lemp_induction_physics.py` 20 | Table A.4 factor 8.5 → 1; `test_01_copper_w2m_unbonded` fails | open (C3) |
| C4 | `test_rolling_sphere_edition2024.py` 28 | class III radius 45 → 46; `test_table_2_radii_by_lps_class[III-45.0]` fails | fixed in code, pending verification; C4-b Type A/Type B compliance open |
| C4-b | `test_minimum_length_l1_figure5.py` 40 | class I `l1` slope 0.03 → 0.02; `test_class_i_l1_figure5_values[1000.0-20.0]` fails | fixed in code, pending verification; Type A/Type B compliance open |
| H3 | `test_risk_factors_2024.py` 331 | framework `P_S` 0.5 → 0.1; `test_table_b4_row2_continuous_rc_or_metal_framework` fails | fixed in code, pending verification; P_A, R_M/R_U/R_W/R_Z, P_SPD source and removed 0.5 factor open |
| H4 | `test_multi_rod_mutual.py` 17 | pairwise prefactor halved; `test_r_m_reference_values` fails | fixed in code, pending verification; primary-source confirmation open |
| H5 | `test_earthing_ring_strip.py` 19 | ring prefactor halved; independent ring values fail | fixed in code, pending verification; ring primary source and flat-strip model open |
| H8 | `test_protective_angle_figure1.py` 137 | class I 10 m anchor 45.3 → 35.3; anchor test fails | fixed in code, pending verification; exact fix reversion still needed |
| H9 | `test_api_error_mapping.py` 11; `test_risk_inputs_b2.py` 21; `test_earthing_spd_earth_b3.py` 13; `test_touch_lemp_uq_b4.py` 45; `test_geometry_domain_b5.py` 185; `test_bom_pv_hvi_opt_peec_nodal_b6.py` 22 | remove strict-bool check in risk input; `test_a4_risk_has_coordinated_spd_required_and_strict_bool` fails | fixed in code, pending verification; clamp, 20 °C citation, 13 defaults, H13 open |
| H15 | `test_spd_coordination_annex_c.py` 23 | conservative `Uw` factor 0.5 → 0.8; `test_rule1_simplified_up_limit` fails | fixed in code, pending verification; induced voltage, propagation length, distance-dependent and two-port rules open |

Additional pinning files identified in the original step commits, and exact reversion-style mutations, remain to be checked. The existing strict xfail is unchanged. See full pytest results in the step report.
