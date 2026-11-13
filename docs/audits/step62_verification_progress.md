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

## Step 6.3 — historical-line reversion checks

Baseline: `1ddeaf2`. Run the exact commands below from the repository root; each script checks each historical fragment against `git show <fix>^:<file>`, creates an isolated `git archive 1ddeaf2` scratch tree, sets `PYTHONPATH` to that tree, runs tests, and removes it. The replacement strings and all commands are in the scripts. Output including **all** failing test names is in `docs/audits/step63_exact_reversions_results.txt`. For H9, all B1–B6 test files from the six step commits are run together; unmodified per-file counts are in `docs/audits/step63_h9_pinning_counts.txt`.

```sh
python3 scripts/step63_exact_reversions.py
python3 scripts/step63_exact_reversions_more.py
```

| Item | Original fix / exact historical fragment restored (see script for complete replacement) | Unmodified pinning counts | Mutated result; representative failure | Result/status |
|---|---|---|---|---|
| C1 | `2e3188a^` inverted-cap `z_protect` and `is_protected` lines | rolling sphere 14; optimizer conservative 6 | 5 failed, 15 passed; `test_counterexample_edge_midpoint_exposed_public_api` | open: H7 coverage remains open |
| C2 | `19a607a^` complete barrier/fence voltage-zeroing block | touch/step 9 | 3 failed, 6 passed; `test_mitigation_flags_do_not_change_voltages` | verified (step 6.3, exact reversion + pinning tests) |
| C3 | `1347b14^` first-stroke `tau1 = 10.0`, `tau2 = 350.0` lines restored under stroke-type branch | Heidler 13; induction 20 | 5 failed, 28 passed; `test_max_di_dt_matches_reference_values` | open: C3-b still needs exact whole-fix reversion |
| C3-b | `6719bb9^` no-credit `kms = 1.0` fallback moved into current branch | induction 20 | 8 failed, 12 passed; `test_01_copper_w2m_unbonded` | open: this is an interface-adapted historical line, not an exact whole-fix reversion |
| C4 | `ec571e8^` class III radius `200.0` from previous table | edition 28 | 2 failed, 26 passed; `test_no_radius_outside_table_2_for_classes_i_through_iv` | pending: Type A/B compliance sub-items open |
| C4-b | `3343007^` class I l1 capped expression | Figure 5 40 | 4 failed, 36 passed; `test_docx_renderer_prints_computed_l1_not_constant_5` | pending: Type A/B compliance sub-items open |
| H3 | `44ec813^` legacy `l_f` expression | risk factors 331 | 58 failed, 273 passed; `test_rp_applied_once_in_pb_and_legacy_half_factor_removed` (many others fail because the old expression cannot accept new optional inputs) | pending: probability and factor sub-items open |
| H4 | `16fa0ed^` complete former coupling block | mutual 17 | 1 failed, 16 passed; `test_earthing_engine_vertical_multi_rod_uses_pairwise_mutual` | pending: primary source open |
| H5 | `dcc070d^` original two-log ring block | ring/strip 19 | 4 failed, 15 passed; `test_ring_sunde_matches_independent_values_within_1e6_rel` | pending: primary source and flat-strip model open |
| H8 | `3343007^` Class I 20 m anchor `(20.0, 25.0)` | Figure 1 137 | 2 failed, 135 passed; `test_figure1_anchor_values[I-20.0-22.4-False]` | partial reversion only (anchor value); NOT verified until height-domain rules are also reverted; digitization uncertainty remains |
| H9 | `73c7cdc^` former `lps_class` default line; all B1–B6 test files | see `step63_h9_pinning_counts.txt` | 1 failed, 856 passed, 1 xfailed; `test_a3_risk_lps_class_required_and_validated` | pending: clamp, ambient source, defaults and H13 open |
| H15 | `b1114b2^` old `l_max` and clamp lines, with new-interface `u_req_kv` alias | Annex C 23 | 5 failed, 18 passed; `test_limiting_vs_switching_give_distinct_l_max_for_identical_inputs` | pending: interface-adapted, Annex C sub-items open |

No calculation source in the working branch was modified. C3-b and H15 require interface adapters, so their tests cannot be described as a complete exact reversal of the original commit. C1 remains open because its register note points to the roof-coverage defect.
