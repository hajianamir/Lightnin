# Step 6.2 H10 claim audit — INCOMPLETE

**Count so far: 15 reviewed claims: 5 consistent, 7 contradicted by code, 3 unsourced. Total claims in scope remains unknown.**

Base: `d9f5383`. This is a partial audit, **not** a one-row-per-claim inventory; H10 remains open. Do not infer that unlisted claims are consistent. The table records only claims individually checked so far. Standard texts cited below are in the repository's `origin/main` tree, which was inspected with `git show` (they are not present in the current branch's `docs/`). `unsourced` means the cited claim's independent primary source has not been established here, not that its code necessarily differs.

| Document | Section | Claim | Code location | Status | Evidence / disposition |
|---|---|---|---|---|---|
| 28 | IEC parameters | Class I/II/III–IV `ki` values 0.08/0.06/0.04 | `packages/standards-data/aegislps_standards/repository.py:34–56` | consistent | Table references corrected from Table 10 to IEC 62305-3:2024 Clause 6.3 Table 11 (`origin/main:docs/62305-3-2024.md`). |
| 28 | IEC parameters | Air and solid `km` values 1.0 and 0.5 | `packages/standards-data/aegislps_standards/repository.py:58–74` | consistent | Table references corrected from Table 11 to IEC 62305-3:2024 Clause 6.3 Table 12 (`origin/main:docs/62305-3-2024.md`). |
| 29 | §1 | `s = ki * kc / km * l` | `services/calculation-engine/aegislps_engine/separation.py:177` | consistent | IEC 62305-3:2024 Clause 6.3.2 equation (6), the simplified special case. |
| 29 | §1 | Old defect label says kc uses segment count and l always uses node z | `services/calculation-engine/aegislps_engine/separation.py:69–106, 158–177` | contradicted by code | Historical label is stale: current kc uses down-conductor configuration or a fallback. Route length is used when supplied; node height is still a fallback. Documentation correction still required after complete review. |
| 33 | §2.1 | Segment-by-segment separation sum is implemented | `services/calculation-engine/aegislps_engine/separation.py:158–177` | contradicted by code | Single-path calculation, not the multi-segment sum. Existing H2 open note already tracks Eq. (5) as deferred; expected sum per IEC 62305-3:2024 Clause 6.3. Do not modify code in this step. |
| 33 | §2.3 | Inverted-cap rolling-sphere formula is implemented | `packages/geometry/aegislps_geometry/rolling_sphere.py:53–95` | contradicted by code | Historical formula and C1 defect label are stale; code now uses the ground-referenced radius. Standard/geometry basis and full document correction need further review. |
| 33 | §2.5 | Type B compliance compares circumference with `l1`, rather than ring equivalent radius | `services/calculation-engine/aegislps_engine/earthing.py:433–436, 524` | consistent | Known code-side open sub-item C4-b: compare Type B equivalent radius with `l1` and account for any additional electrodes per IEC 62305-3:2024 Clause 5.4.2.3. Code left unchanged. |
| 33 | §2.5 | Type B ring resistance is the stated two-log Dwight formula | `services/calculation-engine/aegislps_engine/earthing.py:437–443` | contradicted by code | Current code uses the Sunde candidate; primary-source confirmation is pending under H5. No unsupported choice of correct formula made here. |
| 33 | §2.7 | Maximum protective distance is `(Uw-Up)*10 m` | `services/calculation-engine/aegislps_engine/spd_coordination.py:196–239` | contradicted by code | Historic claim conflicts with the adjacent H15 correction note. IEC 62305-4:2024 Annex C.2.3 and C.2.5 are cited by that note; document reconciliation remains to be completed. |
| 35 | §1.1 | Segment-by-segment separation sum is implemented | `services/calculation-engine/aegislps_engine/separation.py:158–177` | contradicted by code | Same deferred H2 sub-item as 33 §2.1; expected IEC 62305-3:2024 Clause 6.3 Eq. (5). |
| 35 | §2.1 | Type B ring and rod array use printed historical formulas | `services/calculation-engine/aegislps_engine/earthing.py:64–111, 437–459` | contradicted by code | Current code uses a Sunde candidate and pairwise coupling; primary-source confirmation pending under H4/H5. No code change. |
| 35 | §2.3 | Copper-coated steel rod minimum diameter 14 mm | `services/calculation-engine/aegislps_engine/earth_rod_sizing.py:152–158` | consistent | Corrected obsolete 16 mm document value using IEC 62305-3:2024 Clause 5.6.2 Table 8 (`origin/main:docs/62305-3-2024.md`); coating source still requires independent check. |
| 35 | §2.3 | Copper coating thickness 250 µm | `services/calculation-engine/aegislps_engine/earth_rod_sizing.py:152–158` | unsourced | Implemented value; IEC 62305-3:2024 Table 8 supports 14 mm diameter but does not establish this coating thickness in the available text. Independent source confirmation needed. |
| 35 | §2.3 | Rod spacing `2L` guarantees efficiency > 80% | `services/calculation-engine/aegislps_engine/earth_rod_sizing.py:199–210` | unsourced | Code sets spacing to `2L`, but no efficiency guarantee or cited primary source has been established; existing H4 note flags this. |
| 35 | §3.2 | Neumann double integral | `services/calculation-engine/aegislps_engine/peec_thermal.py` | unsourced | M2 records that a primary source is not in repository docs. |

Next work: finish a claim-by-claim inventory across all four documents, resolve each contradiction with the actual standard text or record a specific code-side item, and only then determine whether H10 can be closed. The two code-side issues above are already recorded under C4-b and H2; no new formula change was made.

## Proposed diffs for code-side H10 items — not applied

These are design sketches for owner review, not drop-in patches. No formula or physics change is authorized here.

### H10-a (C4-b): Type B radius and supplemental electrodes

IEC 62305-3:2024 **§5.4.2.3**, Eqs. (1)–(3), not §5.4.2.2 (which is Type A), specifies `r_e >= l1`, or supplemental electrodes if `r_e < l1`: each horizontal length `l1-r_e` or vertical length `(l1-r_e)/2`, with at least two additional electrodes. The present `earthing.py:435–436,524` compares circumference instead.

```diff
- meets_l1 = effective_len >= l1
+ if inp.electrode_type == "type_b_ring":
+     # Proposed circular-ring case only; r_e = ring_radius_m.
+     # Resolve and validate supplementary-electrode layout and lengths first.
+     meets_l1 = ring_radius_m >= l1 or supplemental_electrodes_compliant
+ else:
+     meets_l1 = type_a_or_foundation_compliance_from_explicit_geometry
```

The input/output schema currently does not encode sufficient supplemental-electrode geometry, counts, and foundation area for a complete implementation. Those inputs, Type A criteria, warnings, compatibility and boundary tests require an owner decision. Do not replace the present check with the undefined names above.

### H10-b (H2): multi-segment separation

IEC 62305-3:2024 **§6.3.1 Eq. (5)** specifies `s = (ki/km) * sum(kc_j * l_j)`; §6.3.2 Eq. (6) is the simplified single-`kc` case used today at `separation.py:177`.

```diff
- s_m = (ki / km) * kc * l_m
+ if segment_path_is_explicit_and_validated:
+     s_m = (ki / km) * sum(segment.kc * segment.length_m for segment in path)
+ else:
+     s_m = (ki / km) * kc * l_m  # existing simplified case, retain warnings
```

The `path` and current-partition factors need a validated representation, route/bonding-point rules and owner-approved fallback semantics. This sketch does not authorize implementation.
