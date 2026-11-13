# Step 6.4 full inverse-diff checks

Baseline: `ec54036`; pytest: `/tmp/step64-venv/bin/pytest`. Each commit is tested independently in a fresh archive. Code means all changed files under `packages/` and `services/`; test and baseline changes are excluded. No rejected or partial hunks are applied.

| Item | Fix | Code files | Total hunks | Reverted hunks | Result |
|---|---|---|---:|---:|---|
| C1 | `2e3188a` | 2 | 6 | 0 | **partial / not applied**; reverse check failed, tests not run. |
| C2 | `19a607a` | 1 | 4 | 0 | **partial / not applied**; reverse check failed, tests not run. |
| C3 | `1347b14` | 1 | 2 | 0 | **partial / not applied**; reverse check failed, tests not run. |
| C3 follow-up | `434a727` | 1 | 1 | 0 | **partial / not applied**; reverse check failed, tests not run. |
| C3-b | `215c248` | 1 | 6 | 0 | **partial / not applied**; reverse check failed, tests not run. |
| C3-b follow-up | `6719bb9` | 1 | 8 | 0 | **partial / not applied**; reverse check failed, tests not run. |
| C4 | `ec571e8` | 4 | 10 | 0 | **partial / not applied**; reverse check failed, tests not run. |
| C4-b | `3343007` | 3 | 5 | 0 | **partial / not applied**; reverse check failed, tests not run. |
| H3 | `44ec813` | 3 | 9 | 0 | **partial / not applied**; reverse check failed, tests not run. |
| H4 | `16fa0ed` | 2 | 4 | 0 | **partial / not applied**; reverse check failed, tests not run. |
| H5 | `dcc070d` | 1 | 6 | 0 | **partial / not applied**; reverse check failed, tests not run. |
| H5 follow-up | `4235bd6` | 1 | 2 | 0 | **partial / not applied**; reverse check failed, tests not run. |
| H8 | `3343007` | 3 | 5 | 0 | **partial / not applied**; reverse check failed, tests not run. |
| H9 B1 | `d7a2556` | 2 | 3 | 0 | **partial / not applied**; reverse check failed, tests not run. |
| H9 B2 | `73c7cdc` | 2 | 11 | 11 | Full inverse applied; 22 failed, 835 passed, 1 xfailed, 1 warning in 4.60s. |
| H9 B3 | `70627fc` | 5 | 33 | 0 | **partial / not applied**; reverse check failed, tests not run. |
| H9 B3 baseline | `dbb14da` | none | 0 | 0 | No code diff; baseline-only commit. |
| H9 B4 | `bb20a92` | 3 | 26 | 0 | **partial / not applied**; reverse check failed, tests not run. |
| H9 B5 | `a5b5bee` | 10 | 36 | 0 | **partial / not applied**; reverse check failed, tests not run. |
| H9 B6 | `78d94c3` | 10 | 39 | 0 | **partial / not applied**; reverse check failed, tests not run. |
| H15 | `b1114b2` | 2 | 5 | 0 | **partial / not applied**; reverse check failed, tests not run. |

## Files, commands and diagnostics

### C1 — `2e3188a`

Files (2), 6 total hunks: `packages/geometry/aegislps_geometry/mesh_rolling_sphere.py`, `packages/geometry/aegislps_geometry/rolling_sphere.py`

Patch: `git diff 2e3188a^ 2e3188a -- packages/ services/` → `git apply --whitespace=nowarn --reverse --check -` and, only if clean, `git apply --whitespace=nowarn --reverse -`.

Pinning files: `tests/test_rolling_sphere_reference.py`, `tests/test_optimization_conservative.py`

Reverse check errors:

```text
error: patch failed: packages/geometry/aegislps_geometry/rolling_sphere.py:1
error: packages/geometry/aegislps_geometry/rolling_sphere.py: patch does not apply
error: patch failed: packages/geometry/aegislps_geometry/mesh_rolling_sphere.py:1
error: packages/geometry/aegislps_geometry/mesh_rolling_sphere.py: patch does not apply
```

### C2 — `19a607a`

Files (1), 4 total hunks: `services/calculation-engine/aegislps_engine/touch_step.py`

Patch: `git diff 19a607a^ 19a607a -- packages/ services/` → `git apply --whitespace=nowarn --reverse --check -` and, only if clean, `git apply --whitespace=nowarn --reverse -`.

Pinning files: `tests/test_touch_step_physics.py`

Reverse check errors:

```text
error: patch failed: services/calculation-engine/aegislps_engine/touch_step.py:1
error: services/calculation-engine/aegislps_engine/touch_step.py: patch does not apply
```

### C3 — `1347b14`

Files (1), 2 total hunks: `services/calculation-engine/aegislps_engine/lemp_engine.py`

Patch: `git diff 1347b14^ 1347b14 -- packages/ services/` → `git apply --whitespace=nowarn --reverse --check -` and, only if clean, `git apply --whitespace=nowarn --reverse -`.

Pinning files: `tests/test_lemp_heidler_physics.py`, `tests/test_lemp_induction_physics.py`

Reverse check errors:

```text
error: patch failed: services/calculation-engine/aegislps_engine/lemp_engine.py:1
error: services/calculation-engine/aegislps_engine/lemp_engine.py: patch does not apply
```

### C3 follow-up — `434a727`

Files (1), 1 total hunks: `services/calculation-engine/aegislps_engine/lemp_engine.py`

Patch: `git diff 434a727^ 434a727 -- packages/ services/` → `git apply --whitespace=nowarn --reverse --check -` and, only if clean, `git apply --whitespace=nowarn --reverse -`.

Pinning files: `tests/test_lemp_heidler_physics.py`, `tests/test_lemp_induction_physics.py`

Reverse check errors:

```text
error: patch failed: services/calculation-engine/aegislps_engine/lemp_engine.py:141
error: services/calculation-engine/aegislps_engine/lemp_engine.py: patch does not apply
```

### C3-b — `215c248`

Files (1), 6 total hunks: `services/calculation-engine/aegislps_engine/lemp_engine.py`

Patch: `git diff 215c248^ 215c248 -- packages/ services/` → `git apply --whitespace=nowarn --reverse --check -` and, only if clean, `git apply --whitespace=nowarn --reverse -`.

Pinning files: `tests/test_lemp_induction_physics.py`

Reverse check errors:

```text
error: patch failed: services/calculation-engine/aegislps_engine/lemp_engine.py:81
error: services/calculation-engine/aegislps_engine/lemp_engine.py: patch does not apply
```

### C3-b follow-up — `6719bb9`

Files (1), 8 total hunks: `services/calculation-engine/aegislps_engine/lemp_engine.py`

Patch: `git diff 6719bb9^ 6719bb9 -- packages/ services/` → `git apply --whitespace=nowarn --reverse --check -` and, only if clean, `git apply --whitespace=nowarn --reverse -`.

Pinning files: `tests/test_lemp_induction_physics.py`

Reverse check errors:

```text
error: patch failed: services/calculation-engine/aegislps_engine/lemp_engine.py:1
error: services/calculation-engine/aegislps_engine/lemp_engine.py: patch does not apply
```

### C4 — `ec571e8`

Files (4), 10 total hunks: `packages/geometry/aegislps_geometry/mesh_rolling_sphere.py`, `packages/geometry/aegislps_geometry/rolling_sphere.py`, `packages/reporting/aegislps_reporting/docx_renderer.py`, `services/calculation-engine/aegislps_engine/optimization.py`

Patch: `git diff ec571e8^ ec571e8 -- packages/ services/` → `git apply --whitespace=nowarn --reverse --check -` and, only if clean, `git apply --whitespace=nowarn --reverse -`.

Pinning files: `tests/test_rolling_sphere_edition2024.py`

Reverse check errors:

```text
error: patch failed: services/calculation-engine/aegislps_engine/optimization.py:1
error: services/calculation-engine/aegislps_engine/optimization.py: patch does not apply
error: patch failed: packages/reporting/aegislps_reporting/docx_renderer.py:126
error: packages/reporting/aegislps_reporting/docx_renderer.py: patch does not apply
error: patch failed: packages/geometry/aegislps_geometry/rolling_sphere.py:1
error: packages/geometry/aegislps_geometry/rolling_sphere.py: patch does not apply
error: patch failed: packages/geometry/aegislps_geometry/mesh_rolling_sphere.py:3
error: packages/geometry/aegislps_geometry/mesh_rolling_sphere.py: patch does not apply
```

### C4-b — `3343007`

Files (3), 5 total hunks: `packages/geometry/aegislps_geometry/protective_angle.py`, `packages/reporting/aegislps_reporting/docx_renderer.py`, `services/calculation-engine/aegislps_engine/earthing.py`

Patch: `git diff 3343007^ 3343007 -- packages/ services/` → `git apply --whitespace=nowarn --reverse --check -` and, only if clean, `git apply --whitespace=nowarn --reverse -`.

Pinning files: `tests/test_minimum_length_l1_figure5.py`

Reverse check errors:

```text
error: patch failed: services/calculation-engine/aegislps_engine/earthing.py:151
error: services/calculation-engine/aegislps_engine/earthing.py: patch does not apply
error: patch failed: packages/geometry/aegislps_geometry/protective_angle.py:1
error: packages/geometry/aegislps_geometry/protective_angle.py: patch does not apply
```

### H3 — `44ec813`

Files (3), 9 total hunks: `services/calculation-engine/aegislps_engine/comprehensive_risk.py`, `services/calculation-engine/aegislps_engine/risk.py`, `services/calculation-engine/aegislps_engine/risk_factors.py`

Patch: `git diff 44ec813^ 44ec813 -- packages/ services/` → `git apply --whitespace=nowarn --reverse --check -` and, only if clean, `git apply --whitespace=nowarn --reverse -`.

Pinning files: `tests/test_risk_factors_2024.py`

Reverse check errors:

```text
error: patch failed: services/calculation-engine/aegislps_engine/risk.py:1
error: services/calculation-engine/aegislps_engine/risk.py: patch does not apply
error: patch failed: services/calculation-engine/aegislps_engine/comprehensive_risk.py:1
error: services/calculation-engine/aegislps_engine/comprehensive_risk.py: patch does not apply
```

### H4 — `16fa0ed`

Files (2), 4 total hunks: `services/calculation-engine/aegislps_engine/earth_rod_sizing.py`, `services/calculation-engine/aegislps_engine/earthing.py`

Patch: `git diff 16fa0ed^ 16fa0ed -- packages/ services/` → `git apply --whitespace=nowarn --reverse --check -` and, only if clean, `git apply --whitespace=nowarn --reverse -`.

Pinning files: `tests/test_multi_rod_mutual.py`

Reverse check errors:

```text
error: patch failed: services/calculation-engine/aegislps_engine/earthing.py:10
error: services/calculation-engine/aegislps_engine/earthing.py: patch does not apply
error: patch failed: services/calculation-engine/aegislps_engine/earth_rod_sizing.py:2
error: services/calculation-engine/aegislps_engine/earth_rod_sizing.py: patch does not apply
```

### H5 — `dcc070d`

Files (1), 6 total hunks: `services/calculation-engine/aegislps_engine/earthing.py`

Patch: `git diff dcc070d^ dcc070d -- packages/ services/` → `git apply --whitespace=nowarn --reverse --check -` and, only if clean, `git apply --whitespace=nowarn --reverse -`.

Pinning files: `tests/test_earthing_ring_strip.py`

Reverse check errors:

```text
error: patch failed: services/calculation-engine/aegislps_engine/earthing.py:2
error: services/calculation-engine/aegislps_engine/earthing.py: patch does not apply
```

### H5 follow-up — `4235bd6`

Files (1), 2 total hunks: `services/calculation-engine/aegislps_engine/earthing.py`

Patch: `git diff 4235bd6^ 4235bd6 -- packages/ services/` → `git apply --whitespace=nowarn --reverse --check -` and, only if clean, `git apply --whitespace=nowarn --reverse -`.

Pinning files: `tests/test_earthing_ring_strip.py`

Reverse check errors:

```text
error: patch failed: services/calculation-engine/aegislps_engine/earthing.py:6
error: services/calculation-engine/aegislps_engine/earthing.py: patch does not apply
```

### H8 — `3343007`

Files (3), 5 total hunks: `packages/geometry/aegislps_geometry/protective_angle.py`, `packages/reporting/aegislps_reporting/docx_renderer.py`, `services/calculation-engine/aegislps_engine/earthing.py`

Patch: `git diff 3343007^ 3343007 -- packages/ services/` → `git apply --whitespace=nowarn --reverse --check -` and, only if clean, `git apply --whitespace=nowarn --reverse -`.

Pinning files: `tests/test_protective_angle_figure1.py`

Reverse check errors:

```text
error: patch failed: services/calculation-engine/aegislps_engine/earthing.py:151
error: services/calculation-engine/aegislps_engine/earthing.py: patch does not apply
error: patch failed: packages/geometry/aegislps_geometry/protective_angle.py:1
error: packages/geometry/aegislps_geometry/protective_angle.py: patch does not apply
```

### H9 B1 — `d7a2556`

Files (2), 3 total hunks: `packages/reporting/aegislps_reporting/docx_renderer.py`, `services/api/aegislps_api/main.py`

Patch: `git diff d7a2556^ d7a2556 -- packages/ services/` → `git apply --whitespace=nowarn --reverse --check -` and, only if clean, `git apply --whitespace=nowarn --reverse -`.

Pinning files: `tests/test_advanced_modules.py`, `tests/test_api_error_mapping.py`, `tests/test_bom_pv_hvi_opt_peec_nodal_b6.py`, `tests/test_earth_pit_and_rod_sizing.py`, `tests/test_earthing_and_spd.py`, `tests/test_earthing_ring_strip.py`, `tests/test_earthing_spd_earth_b3.py`, `tests/test_geometry_domain_b5.py`, `tests/test_lemp_engine.py`, `tests/test_lemp_heidler_physics.py`, `tests/test_lemp_induction_physics.py`, `tests/test_mesh_method_and_hvi.py`, `tests/test_minimum_length_l1_figure5.py`, `tests/test_multi_rod_mutual.py`, `tests/test_nodal_solver.py`, `tests/test_optimization_and_pv.py`, `tests/test_optimization_conservative.py`, `tests/test_peec_and_mesh_rolling_sphere.py`, `tests/test_project_io.py`, `tests/test_risk_factors_2024.py`, `tests/test_risk_inputs_b2.py`, `tests/test_separation_distance.py`, `tests/test_spd_coordination_annex_c.py`, `tests/test_touch_lemp_uq_b4.py`, `tests/test_touch_step_physics.py`, `tests/test_uq_engine.py`

Reverse check errors:

```text
error: patch failed: services/api/aegislps_api/main.py:1
error: services/api/aegislps_api/main.py: patch does not apply
```

### H9 B2 — `73c7cdc`

Files (2), 11 total hunks: `services/calculation-engine/aegislps_engine/comprehensive_risk.py`, `services/calculation-engine/aegislps_engine/risk.py`

Patch: `git diff 73c7cdc^ 73c7cdc -- packages/ services/` → `git apply --whitespace=nowarn --reverse --check -` and, only if clean, `git apply --whitespace=nowarn --reverse -`.

Pinning files: `tests/test_advanced_modules.py`, `tests/test_api_error_mapping.py`, `tests/test_bom_pv_hvi_opt_peec_nodal_b6.py`, `tests/test_earth_pit_and_rod_sizing.py`, `tests/test_earthing_and_spd.py`, `tests/test_earthing_ring_strip.py`, `tests/test_earthing_spd_earth_b3.py`, `tests/test_geometry_domain_b5.py`, `tests/test_lemp_engine.py`, `tests/test_lemp_heidler_physics.py`, `tests/test_lemp_induction_physics.py`, `tests/test_mesh_method_and_hvi.py`, `tests/test_minimum_length_l1_figure5.py`, `tests/test_multi_rod_mutual.py`, `tests/test_nodal_solver.py`, `tests/test_optimization_and_pv.py`, `tests/test_optimization_conservative.py`, `tests/test_peec_and_mesh_rolling_sphere.py`, `tests/test_project_io.py`, `tests/test_risk_factors_2024.py`, `tests/test_risk_inputs_b2.py`, `tests/test_separation_distance.py`, `tests/test_spd_coordination_annex_c.py`, `tests/test_touch_lemp_uq_b4.py`, `tests/test_touch_step_physics.py`, `tests/test_uq_engine.py`

Pytest failing/error names:

```text
FAILED tests/test_risk_factors_2024.py::test_t_occupancy_consistency_at_8760_hours
FAILED tests/test_risk_inputs_b2.py::test_a1_a2_risk_hours_default_8760_and_range_validation
FAILED tests/test_risk_inputs_b2.py::test_a3_risk_lps_class_required_and_validated
FAILED tests/test_risk_inputs_b2.py::test_a4_risk_has_coordinated_spd_required_and_strict_bool
FAILED tests/test_risk_inputs_b2.py::test_a5_risk_positive_numeric_fields_required_and_validated[structure_length_m]
FAILED tests/test_risk_inputs_b2.py::test_a5_risk_positive_numeric_fields_required_and_validated[structure_width_m]
FAILED tests/test_risk_inputs_b2.py::test_a5_risk_positive_numeric_fields_required_and_validated[structure_height_m]
FAILED tests/test_risk_inputs_b2.py::test_a5_risk_positive_numeric_fields_required_and_validated[ng_flashes_per_km2_year]
FAILED tests/test_risk_inputs_b2.py::test_a5_risk_positive_numeric_fields_required_and_validated[environmental_cd]
FAILED tests/test_risk_inputs_b2.py::test_a6_risk_requires_explicit_fire_risk_level_or_rf
FAILED tests/test_risk_inputs_b2.py::test_b1_incoming_service_line_length_validation_and_unclamped_short_line
FAILED tests/test_risk_inputs_b2.py::test_b2_comprehensive_risk_required_fields[structure_length_m]
FAILED tests/test_risk_inputs_b2.py::test_b2_comprehensive_risk_required_fields[structure_width_m]
FAILED tests/test_risk_inputs_b2.py::test_b2_comprehensive_risk_required_fields[structure_height_m]
FAILED tests/test_risk_inputs_b2.py::test_b2_comprehensive_risk_required_fields[ng_flashes_per_km2_year]
FAILED tests/test_risk_inputs_b2.py::test_b2_comprehensive_risk_required_fields[environmental_cd]
FAILED tests/test_risk_inputs_b2.py::test_b2_comprehensive_risk_required_fields[lps_class]
FAILED tests/test_risk_inputs_b2.py::test_b2_comprehensive_risk_required_fields[has_coordinated_spd]
FAILED tests/test_risk_inputs_b2.py::test_b2_comprehensive_risk_required_fields[has_tws_early_warning]
FAILED tests/test_risk_inputs_b2.py::test_b2_comprehensive_risk_field_validators
FAILED tests/test_risk_inputs_b2.py::test_b3_b4_b5_comprehensive_risk_hours_fire_and_standard_defaults
FAILED tests/test_risk_inputs_b2.py::test_risk_and_comprehensive_risk_http_endpoints
```

### H9 B3 — `70627fc`

Files (5), 33 total hunks: `services/calculation-engine/aegislps_engine/diagnostics.py`, `services/calculation-engine/aegislps_engine/earth_pit.py`, `services/calculation-engine/aegislps_engine/earth_rod_sizing.py`, `services/calculation-engine/aegislps_engine/earthing.py`, `services/calculation-engine/aegislps_engine/spd_coordination.py`

Patch: `git diff 70627fc^ 70627fc -- packages/ services/` → `git apply --whitespace=nowarn --reverse --check -` and, only if clean, `git apply --whitespace=nowarn --reverse -`.

Pinning files: `tests/test_advanced_modules.py`, `tests/test_api_error_mapping.py`, `tests/test_bom_pv_hvi_opt_peec_nodal_b6.py`, `tests/test_earth_pit_and_rod_sizing.py`, `tests/test_earthing_and_spd.py`, `tests/test_earthing_ring_strip.py`, `tests/test_earthing_spd_earth_b3.py`, `tests/test_geometry_domain_b5.py`, `tests/test_lemp_engine.py`, `tests/test_lemp_heidler_physics.py`, `tests/test_lemp_induction_physics.py`, `tests/test_mesh_method_and_hvi.py`, `tests/test_minimum_length_l1_figure5.py`, `tests/test_multi_rod_mutual.py`, `tests/test_nodal_solver.py`, `tests/test_optimization_and_pv.py`, `tests/test_optimization_conservative.py`, `tests/test_peec_and_mesh_rolling_sphere.py`, `tests/test_project_io.py`, `tests/test_risk_factors_2024.py`, `tests/test_risk_inputs_b2.py`, `tests/test_separation_distance.py`, `tests/test_spd_coordination_annex_c.py`, `tests/test_touch_lemp_uq_b4.py`, `tests/test_touch_step_physics.py`, `tests/test_uq_engine.py`

Reverse check errors:

```text
error: patch failed: services/calculation-engine/aegislps_engine/earth_rod_sizing.py:1
error: services/calculation-engine/aegislps_engine/earth_rod_sizing.py: patch does not apply
error: patch failed: services/calculation-engine/aegislps_engine/earth_pit.py:99
error: services/calculation-engine/aegislps_engine/earth_pit.py: patch does not apply
```

### H9 B4 — `bb20a92`

Files (3), 26 total hunks: `services/calculation-engine/aegislps_engine/lemp_engine.py`, `services/calculation-engine/aegislps_engine/touch_step.py`, `services/calculation-engine/aegislps_engine/uq_engine.py`

Patch: `git diff bb20a92^ bb20a92 -- packages/ services/` → `git apply --whitespace=nowarn --reverse --check -` and, only if clean, `git apply --whitespace=nowarn --reverse -`.

Pinning files: `tests/test_advanced_modules.py`, `tests/test_api_error_mapping.py`, `tests/test_bom_pv_hvi_opt_peec_nodal_b6.py`, `tests/test_earth_pit_and_rod_sizing.py`, `tests/test_earthing_and_spd.py`, `tests/test_earthing_ring_strip.py`, `tests/test_earthing_spd_earth_b3.py`, `tests/test_geometry_domain_b5.py`, `tests/test_lemp_engine.py`, `tests/test_lemp_heidler_physics.py`, `tests/test_lemp_induction_physics.py`, `tests/test_mesh_method_and_hvi.py`, `tests/test_minimum_length_l1_figure5.py`, `tests/test_multi_rod_mutual.py`, `tests/test_nodal_solver.py`, `tests/test_optimization_and_pv.py`, `tests/test_optimization_conservative.py`, `tests/test_peec_and_mesh_rolling_sphere.py`, `tests/test_project_io.py`, `tests/test_risk_factors_2024.py`, `tests/test_risk_inputs_b2.py`, `tests/test_separation_distance.py`, `tests/test_spd_coordination_annex_c.py`, `tests/test_touch_lemp_uq_b4.py`, `tests/test_touch_step_physics.py`, `tests/test_uq_engine.py`

Reverse check errors:

```text
error: patch failed: services/calculation-engine/aegislps_engine/uq_engine.py:1
error: services/calculation-engine/aegislps_engine/uq_engine.py: patch does not apply
```

### H9 B5 — `a5b5bee`

Files (10), 36 total hunks: `packages/domain-model/aegislps_domain/models.py`, `packages/geometry/aegislps_geometry/mesh_method.py`, `packages/geometry/aegislps_geometry/mesh_rolling_sphere.py`, `packages/geometry/aegislps_geometry/protective_angle.py`, `packages/geometry/aegislps_geometry/rolling_sphere.py`, `services/api/aegislps_api/main.py`, `services/calculation-engine/aegislps_engine/cad_export.py`, `services/calculation-engine/aegislps_engine/diagnostics.py`, `services/calculation-engine/aegislps_engine/dxf_exporter.py`, `services/calculation-engine/aegislps_engine/separation.py`

Patch: `git diff a5b5bee^ a5b5bee -- packages/ services/` → `git apply --whitespace=nowarn --reverse --check -` and, only if clean, `git apply --whitespace=nowarn --reverse -`.

Pinning files: `tests/test_advanced_modules.py`, `tests/test_api_error_mapping.py`, `tests/test_bom_pv_hvi_opt_peec_nodal_b6.py`, `tests/test_earth_pit_and_rod_sizing.py`, `tests/test_earthing_and_spd.py`, `tests/test_earthing_ring_strip.py`, `tests/test_earthing_spd_earth_b3.py`, `tests/test_geometry_domain_b5.py`, `tests/test_lemp_engine.py`, `tests/test_lemp_heidler_physics.py`, `tests/test_lemp_induction_physics.py`, `tests/test_mesh_method_and_hvi.py`, `tests/test_minimum_length_l1_figure5.py`, `tests/test_multi_rod_mutual.py`, `tests/test_nodal_solver.py`, `tests/test_optimization_and_pv.py`, `tests/test_optimization_conservative.py`, `tests/test_peec_and_mesh_rolling_sphere.py`, `tests/test_project_io.py`, `tests/test_risk_factors_2024.py`, `tests/test_risk_inputs_b2.py`, `tests/test_separation_distance.py`, `tests/test_spd_coordination_annex_c.py`, `tests/test_touch_lemp_uq_b4.py`, `tests/test_touch_step_physics.py`, `tests/test_uq_engine.py`

Reverse check errors:

```text
error: patch failed: services/calculation-engine/aegislps_engine/dxf_exporter.py:1
error: services/calculation-engine/aegislps_engine/dxf_exporter.py: patch does not apply
error: patch failed: services/calculation-engine/aegislps_engine/cad_export.py:1
error: services/calculation-engine/aegislps_engine/cad_export.py: patch does not apply
error: patch failed: services/api/aegislps_api/main.py:1
error: services/api/aegislps_api/main.py: patch does not apply
```

### H9 B6 — `78d94c3`

Files (10), 39 total hunks: `packages/geometry/aegislps_geometry/protective_angle.py`, `services/api/aegislps_api/main.py`, `services/calculation-engine/aegislps_engine/bom_engine.py`, `services/calculation-engine/aegislps_engine/diagnostics.py`, `services/calculation-engine/aegislps_engine/hvi_conductor.py`, `services/calculation-engine/aegislps_engine/ifc_importer.py`, `services/calculation-engine/aegislps_engine/nodal.py`, `services/calculation-engine/aegislps_engine/optimization.py`, `services/calculation-engine/aegislps_engine/peec_thermal.py`, `services/calculation-engine/aegislps_engine/pv_module.py`

Patch: `git diff 78d94c3^ 78d94c3 -- packages/ services/` → `git apply --whitespace=nowarn --reverse --check -` and, only if clean, `git apply --whitespace=nowarn --reverse -`.

Pinning files: `tests/test_advanced_modules.py`, `tests/test_api_error_mapping.py`, `tests/test_bom_pv_hvi_opt_peec_nodal_b6.py`, `tests/test_earth_pit_and_rod_sizing.py`, `tests/test_earthing_and_spd.py`, `tests/test_earthing_ring_strip.py`, `tests/test_earthing_spd_earth_b3.py`, `tests/test_geometry_domain_b5.py`, `tests/test_lemp_engine.py`, `tests/test_lemp_heidler_physics.py`, `tests/test_lemp_induction_physics.py`, `tests/test_mesh_method_and_hvi.py`, `tests/test_minimum_length_l1_figure5.py`, `tests/test_multi_rod_mutual.py`, `tests/test_nodal_solver.py`, `tests/test_optimization_and_pv.py`, `tests/test_optimization_conservative.py`, `tests/test_peec_and_mesh_rolling_sphere.py`, `tests/test_project_io.py`, `tests/test_risk_factors_2024.py`, `tests/test_risk_inputs_b2.py`, `tests/test_separation_distance.py`, `tests/test_spd_coordination_annex_c.py`, `tests/test_touch_lemp_uq_b4.py`, `tests/test_touch_step_physics.py`, `tests/test_uq_engine.py`

Reverse check errors:

```text
error: patch failed: services/calculation-engine/aegislps_engine/pv_module.py:1
error: services/calculation-engine/aegislps_engine/pv_module.py: patch does not apply
error: patch failed: services/calculation-engine/aegislps_engine/peec_thermal.py:124
error: services/calculation-engine/aegislps_engine/peec_thermal.py: patch does not apply
error: patch failed: services/calculation-engine/aegislps_engine/optimization.py:1
error: services/calculation-engine/aegislps_engine/optimization.py: patch does not apply
error: patch failed: services/calculation-engine/aegislps_engine/nodal.py:1
error: services/calculation-engine/aegislps_engine/nodal.py: patch does not apply
error: patch failed: services/calculation-engine/aegislps_engine/ifc_importer.py:4
error: services/calculation-engine/aegislps_engine/ifc_importer.py: patch does not apply
error: patch failed: services/calculation-engine/aegislps_engine/hvi_conductor.py:1
error: services/calculation-engine/aegislps_engine/hvi_conductor.py: patch does not apply
error: patch failed: services/calculation-engine/aegislps_engine/bom_engine.py:58
error: services/calculation-engine/aegislps_engine/bom_engine.py: patch does not apply
error: patch failed: services/api/aegislps_api/main.py:4
error: services/api/aegislps_api/main.py: patch does not apply
```

### H15 — `b1114b2`

Files (2), 5 total hunks: `services/api/aegislps_api/main.py`, `services/calculation-engine/aegislps_engine/spd_coordination.py`

Patch: `git diff b1114b2^ b1114b2 -- packages/ services/` → `git apply --whitespace=nowarn --reverse --check -` and, only if clean, `git apply --whitespace=nowarn --reverse -`.

Pinning files: `tests/test_spd_coordination_annex_c.py`

Reverse check errors:

```text
error: patch failed: services/calculation-engine/aegislps_engine/spd_coordination.py:1
error: services/calculation-engine/aegislps_engine/spd_coordination.py: patch does not apply
error: patch failed: services/api/aegislps_api/main.py:97
error: services/api/aegislps_api/main.py: patch does not apply
```

All scratch trees removed; repository status unchanged by the checks.
