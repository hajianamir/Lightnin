# Step 6.5 H10 claim inventory — INCOMPLETE

**99 source marker lines; total distinct claims unknown.** Ten reviewed rows below: 7 consistent, 3 contradicted by code, 0 unsourced. These counts cover only the table below and are not counts for the 99 lines. The marker tracking table explicitly distinguishes reviewed coverage from lines not yet audited. A marker can contain multiple claims; full contextual splitting, source checking, and a total claim count remain unfinished. H10 stays open.

Reference source is the marker file at baseline `ea77582`; code references below are from that baseline. Standards text is `origin/main:docs/62305-3-2024.md`; standard references are not inferred for other rows. `consistent` here means the stated code behavior matches the claim; it is not a certification.

| Source line | Claim | Code location | Status | Standard and clause | Action |
|---|---|---|---|---|---|
| 28:12 | Class I ki is 0.08 | `packages/standards-data/aegislps_standards/repository.py:34–40` | consistent | IEC 62305-3:2024 §6.3.1 Table 11 | retain; independent verification pending |
| 28:13 | Class II ki is 0.06 | `packages/standards-data/aegislps_standards/repository.py:42–48` | consistent | IEC 62305-3:2024 §6.3.1 Table 11 | retain; independent verification pending |
| 28:14 | Classes III and IV ki are 0.04 | `packages/standards-data/aegislps_standards/repository.py:50–56` | consistent | IEC 62305-3:2024 §6.3.1 Table 11 | retain; independent verification pending |
| 28:15 | Air km is 1.0 | `packages/standards-data/aegislps_standards/repository.py:58–64` | consistent | IEC 62305-3:2024 §6.3.1 Table 12 | retain; independent verification pending |
| 28:16 | Concrete and brick km is 0.5 | `packages/standards-data/aegislps_standards/repository.py:66–72` | consistent | IEC 62305-3:2024 §6.3.1 Table 12 | retain; independent verification pending |
| 29:10 | Single-kc equation s = ki × kc × l / km | `services/calculation-engine/aegislps_engine/separation.py:177` | consistent | IEC 62305-3:2024 §6.3.2 Eq. (6) | retain as simplified case; track multi-segment case |
| 29:14,16 | Listed ki and km values | `packages/standards-data/aegislps_standards/repository.py:34–72` | consistent | IEC 62305-3:2024 §6.3.1 Tables 11–12 | individual values covered above; retain |
| 29:15 | Separation kc comes from topology or admittance | `services/calculation-engine/aegislps_engine/separation.py:70–107` | contradicted by code | IEC 62305-3:2024 §6.3.2 Table 13 | correct stale description; current lookup uses conductor count and assumptions |
| 29:19 | Separation kc is selected from segment count | `services/calculation-engine/aegislps_engine/separation.py:70–107` | contradicted by code | IEC 62305-3:2024 §6.3.2 Table 13 | replace stale historical defect note with current behavior |
| 29:19 | Separation always uses node z instead of route length | `services/calculation-engine/aegislps_engine/separation.py:109–154` | contradicted by code | IEC 62305-3:2024 §6.3.2 Eq. (6) | describe explicit route length and the warned node-z fallback |

The seven consistent rows include a composite duplicate row (29:14,16), so **the actual number of distinct individual claims is not known** and the 10 rows must not be treated as an exhaustive claim count. The previous partial audit `step62_h10_claim_audit.md` contains 17 additional reviewed *rows*, some overlapping or aggregate, not included in the counts above.

## Marker tracking

`reviewed partially` means at least one claim on that line appears above; it does not mean all claims on that line were split. `not audited` includes both unreviewed claims and potential non-claim lines: neither may be labeled unsourced without review.

| Source line | Coverage |
|---|---|
| `28:10` | not audited |
| `28:12` | reviewed partially |
| `28:13` | reviewed partially |
| `28:14` | reviewed partially |
| `28:15` | reviewed partially |
| `28:16` | reviewed partially |
| `29:10` | reviewed partially |
| `29:14` | reviewed partially |
| `29:15` | reviewed partially |
| `29:16` | reviewed partially |
| `29:19` | reviewed partially |
| `29:22` | not audited |
| `33:10` | not audited |
| `33:31` | not audited |
| `33:33` | not audited |
| `33:40` | not audited |
| `33:47` | not audited |
| `33:48` | not audited |
| `33:50` | not audited |
| `33:52` | not audited |
| `33:55` | not audited |
| `33:56` | not audited |
| `33:62` | not audited |
| `33:64` | not audited |
| `33:65` | not audited |
| `33:66` | not audited |
| `33:67` | not audited |
| `33:70` | not audited |
| `33:81` | not audited |
| `33:84` | not audited |
| `33:87` | not audited |
| `33:89` | not audited |
| `33:91` | not audited |
| `33:99` | not audited |
| `33:101` | not audited |
| `33:102` | not audited |
| `33:104` | not audited |
| `33:106` | not audited |
| `33:108` | not audited |
| `33:111` | not audited |
| `33:113` | not audited |
| `33:122` | not audited |
| `33:124` | not audited |
| `33:125` | not audited |
| `33:128` | not audited |
| `33:142` | not audited |
| `33:145` | not audited |
| `33:152` | not audited |
| `33:153` | not audited |
| `33:155` | not audited |
| `33:156` | not audited |
| `33:165` | not audited |
| `33:189` | not audited |
| `35:26` | not audited |
| `35:28` | not audited |
| `35:29` | not audited |
| `35:30` | not audited |
| `35:33` | not audited |
| `35:36` | not audited |
| `35:40` | not audited |
| `35:45` | not audited |
| `35:46` | not audited |
| `35:48` | not audited |
| `35:50` | not audited |
| `35:51` | not audited |
| `35:61` | not audited |
| `35:62` | not audited |
| `35:64` | not audited |
| `35:69` | not audited |
| `35:70` | not audited |
| `35:73` | not audited |
| `35:76` | not audited |
| `35:78` | not audited |
| `35:85` | not audited |
| `35:86` | not audited |
| `35:87` | not audited |
| `35:89` | not audited |
| `35:90` | not audited |
| `35:93` | not audited |
| `35:95` | not audited |
| `35:96` | not audited |
| `35:97` | not audited |
| `35:98` | not audited |
| `35:103` | not audited |
| `35:111` | not audited |
| `35:114` | not audited |
| `35:117` | not audited |
| `35:119` | not audited |
| `35:121` | not audited |
| `35:124` | not audited |
| `35:128` | not audited |
| `35:131` | not audited |
| `35:132` | not audited |
| `35:134` | not audited |
| `35:138` | not audited |
| `35:139` | not audited |
| `35:140` | not audited |
| `35:141` | not audited |
| `35:145` | not audited |

## Unapplied code proposals

- **H10-a / C4-b:** IEC 62305-3:2024 §5.4.2.3 Eqs. (1)–(3) requires comparison of effective radius with `l1`, with supplemental electrodes where applicable. The current code uses ring circumference. The design sketch in `step62_h10_claim_audit.md` is unapplied; supplemental geometry requires owner decisions.
- **H10-b / H2:** IEC 62305-3:2024 §6.3.1 Eq. (5) gives the weighted segment sum; §6.3.2 Eq. (6) is the simplified single-kc case used in code. The design sketch in `step62_h10_claim_audit.md` is unapplied; path representation and fallback require owner decisions.

No physics code changes are authorized by this inventory.

## Step 6.6 batch 1 of 5: marker lines 1–20

This batch supersedes the overlapping Step 6.5 rows above; it does not establish completeness beyond these markers. Citations `none` mean no applicable primary-source clause was established for that particular claim, not that a physical equation is necessarily wrong. Line numbers refer to `d9ee3ab`. Sections 6.3.1–6.3.2, including Tables 11–13, of `origin/main:docs/62305-3-2024.md` were inspected. For the 250 kHz and inductance assumptions, the source remains unresolved under M1/M2; no IEC citation is inferred.

| Marker | Source | Claim | Code location | Status | Standard / clause | Action |
|---:|---|---|---|---|---|---|
| 1 | 28:10 | Table column headings only; no value asserted | none | non-claim | none | no action |
| 2 | 28:12 | Class I ki = 0.08 | `packages/standards-data/aegislps_standards/repository.py:34–40` | consistent | IEC 62305-3:2024 §6.3.1 Table 11 | retain |
| 3 | 28:13 | Class II ki = 0.06 | `packages/standards-data/aegislps_standards/repository.py:42–48` | consistent | IEC 62305-3:2024 §6.3.1 Table 11 | retain |
| 4 | 28:14 | Classes III and IV ki = 0.04 | `packages/standards-data/aegislps_standards/repository.py:50–56` | consistent | IEC 62305-3:2024 §6.3.1 Table 11 | retain |
| 5 | 28:15 | Air km = 1.0 | `packages/standards-data/aegislps_standards/repository.py:58–64` | consistent | IEC 62305-3:2024 §6.3.1 Table 12 | retain |
| 6 | 28:16 | Concrete and brick km = 0.5 | `packages/standards-data/aegislps_standards/repository.py:66–72` | consistent | IEC 62305-3:2024 §6.3.1 Table 12 | retain |
| 7 | 29:10 | Single-kc separation s = ki × kc × l / km | `services/calculation-engine/aegislps_engine/separation.py:173–177` | consistent | IEC 62305-3:2024 §6.3.2 Eq. (6) | state simplified scope |
| 8 | 29:14 | Class I ki = 0.08 | `packages/standards-data/aegislps_standards/repository.py:34–40` | consistent | IEC 62305-3:2024 §6.3.1 Table 11 | retain |
| 8 | 29:14 | Class II ki = 0.06 | `packages/standards-data/aegislps_standards/repository.py:42–48` | consistent | IEC 62305-3:2024 §6.3.1 Table 11 | retain |
| 8 | 29:14 | Classes III/IV ki = 0.04 | `packages/standards-data/aegislps_standards/repository.py:50–56` | consistent | IEC 62305-3:2024 §6.3.1 Table 11 | retain |
| 9 | 29:15 | Separation engine derives kc from topology or nodal matrix | `services/calculation-engine/aegislps_engine/separation.py:69–106` | contradicted by code | IEC 62305-3:2024 §6.3.2 Table 13 | correct stale description: conductor count and resistance fallback |
| 10 | 29:16 | Air km = 1.0 | `packages/standards-data/aegislps_standards/repository.py:58–64` | consistent | IEC 62305-3:2024 §6.3.1 Table 12 | retain |
| 10 | 29:16 | Solid concrete km = 0.5 | `packages/standards-data/aegislps_standards/repository.py:66–72` | consistent | IEC 62305-3:2024 §6.3.1 Table 12 | retain |
| 11 | 29:19 | Separation selects kc from segment count | `services/calculation-engine/aegislps_engine/separation.py:69–106` | contradicted by code | IEC 62305-3:2024 §6.3.2 Table 13 | replace stale defect label |
| 11 | 29:19 | Node z is used instead of supplied route length | `services/calculation-engine/aegislps_engine/separation.py:108–151` | contradicted by code | IEC 62305-3:2024 §6.3.2 Eq. (6) | describe explicit route and warned vertical fallback |
| 12 | 29:22 | Sparse nodal system YV = I | `services/calculation-engine/aegislps_engine/nodal.py:301–333` | unsourced | none | retain as experimental; establish independent network-theory source |
| 13 | 33:10 | Section heading only | none | non-claim | none | no action |
| 14 | 33:31 | Single-kc separation equation | `services/calculation-engine/aegislps_engine/separation.py:173–177` | consistent | IEC 62305-3:2024 §6.3.2 Eq. (6) | state simplified scope |
| 15 | 33:33 | Engine implements weighted segment sum | `services/calculation-engine/aegislps_engine/separation.py:158–177` | contradicted by code | IEC 62305-3:2024 §6.3.1 Eq. (5) | H10-b proposal below; not applied |
| 16 | 33:40 | Separation selects kc from segment count | `services/calculation-engine/aegislps_engine/separation.py:69–106` | contradicted by code | IEC 62305-3:2024 §6.3.2 Table 13 | correct stale defect label |
| 16 | 33:40 | Engine uses node z instead of summing path segments | `services/calculation-engine/aegislps_engine/separation.py:108–151,173–177` | contradicted by code | IEC 62305-3:2024 §6.3.1 Eq. (5) | explicit length takes precedence; warned z fallback remains; H10-b tracks missing sum |
| 17 | 33:47 | Sparse nodal system YV = I | `services/calculation-engine/aegislps_engine/nodal.py:301–333` | unsourced | none | establish source; model is experimental |
| 18 | 33:48 | Branch impedance magnitude sqrt(Rdc² + (ωL)²) | `services/calculation-engine/aegislps_engine/nodal.py:215–237` | unsourced | none | document complex phasor and explicit surge-impedance override; M1 source review remains pending |
| 19 | 33:50 | Segment self-inductance is unclamped printed expression | `services/calculation-engine/aegislps_engine/nodal.py:203–213` | contradicted by code | none | document lower clamps; primary-source review remains pending |
| 20 | 33:52 | kc equals unclamped branch-current/total-current ratio | `services/calculation-engine/aegislps_engine/nodal.py:349–356` | contradicted by code | none | document magnitude ratio clamped to [0, 1]; primary-source review pending |

Marker lines 1–20 are accounted for by these rows or explicit non-claim reasons. A contradiction identifies a mismatch, not automatically a code defect. In particular, changing the nodal clamps or phasor model is not authorized without an owner decision and a source.

## Step 6.6 batch 2 of 5: marker lines 21–40

Baseline source references use `d9ee3ab`. IEC 62305-3:2024 §5.2.2.1, Table 2, Figure 1 notes, §5.2.2.2 and §5.4.2.2–§5.4.2.3 were read from `origin/main:docs/62305-3-2024.md`. The available text contains the Figure 1 and Figure 5 captions and notes but not their curves; numerical graphical readings are therefore not independently confirmed here. No IEEE 80, Dwight, Sunde, Laurent, Nieman or Bellaschi primary text was found in the four IEC documents for the formulas below.

| Marker | Source | Claim | Code location | Status | Standard / clause | Action |
|---:|---|---|---|---|---|---|
| 21 | 33:55 | Local KCL residuals are checked | `services/calculation-engine/aegislps_engine/nodal.py:358–375,397–400` | unsourced | none | document warning threshold and experimental status; source pending |
| 21 | 33:55 | Global convergence requires residual below 2% | `services/calculation-engine/aegislps_engine/nodal.py:377–395` | unsourced | none | threshold is model-specific; source pending |
| 22 | 33:56 | Diagonal-ratio condition estimate alerts users | `services/calculation-engine/aegislps_engine/nodal.py:322–330,390–400` | contradicted by code | none | estimate is returned; no direct condition-number warning; correct description |
| 23 | 33:62 | Rolling sphere governed by IEC 62305-3 §5.2.2 and Table 2 | `packages/geometry/aegislps_geometry/rolling_sphere.py:5–22` | consistent | IEC 62305-3:2024 §5.2.2.1–5.2.2.2, Table 2 | retain, without implying certification |
| 24 | 33:64 | Class I radius 20 m | `packages/geometry/aegislps_geometry/rolling_sphere.py:18` | consistent | IEC 62305-3:2024 §5.2.2.1 Table 2 | retain |
| 25 | 33:65 | Class II radius 30 m | `packages/geometry/aegislps_geometry/rolling_sphere.py:19` | consistent | IEC 62305-3:2024 §5.2.2.1 Table 2 | retain |
| 26 | 33:66 | Class III radius 45 m | `packages/geometry/aegislps_geometry/rolling_sphere.py:20` | consistent | IEC 62305-3:2024 §5.2.2.1 Table 2 | retain |
| 27 | 33:67 | Class IV radius 60 m | `packages/geometry/aegislps_geometry/rolling_sphere.py:21` | consistent | IEC 62305-3:2024 §5.2.2.1 Table 2 | retain |
| 28 | 33:70 | Inverted cap is current protection formula | `packages/geometry/aegislps_geometry/rolling_sphere.py:53–116,170–210` | contradicted by code | IEC 62305-3:2024 §5.2.2.2 | replace stale historical formula with current ground-referenced model and disclose limitations |
| 29 | 33:81 | Protective-angle source is Table 2 and Figure 1 | `packages/geometry/aegislps_geometry/protective_angle.py:4–17` | consistent | IEC 62305-3:2024 §5.2.2.1 Table 2 and Figure 1 | retain; graphical values need independent review |
| 30 | 33:84 | Interpolation is between Table 2 anchor points | `packages/geometry/aegislps_geometry/protective_angle.py:13–29,110–132` | contradicted by code | IEC 62305-3:2024 §5.2.2.1 Figure 1 | anchors are digitized from Figure 1 rather than tabled angle values; correct description |
| 31 | 33:87 | Angle anchors and interpolation remain unverified | `packages/geometry/aegislps_geometry/protective_angle.py:13–18,110–132` | unsourced | IEC 62305-3:2024 §5.2.2.1 Figure 1 | independent graphical source check pending |
| 32 | 33:89 | Angle lookup is not independently verified | `packages/geometry/aegislps_geometry/protective_angle.py:13–18` | unsourced | IEC 62305-3:2024 §5.2.2.1 Figure 1 | retain pending graphical review |
| 33 | 33:91 | Coarse anchor list [2, 10, 20, 30, 45, 60] m is used | `packages/geometry/aegislps_geometry/protective_angle.py:18–106` | contradicted by code | IEC 62305-3:2024 §5.2.2.1 Figure 1 | replace stale description; actual anchors are denser |
| 34 | 33:99 | Printed two-log ring resistance is implemented | `services/calculation-engine/aegislps_engine/earthing.py:433–443` | contradicted by code | none | correct to current Sunde candidate; primary source pending H5 |
| 35 | 33:101 | Printed vertical-rod self resistance | `services/calculation-engine/aegislps_engine/earthing.py:61` | unsourced | none | code matches expression; obtain primary-source confirmation |
| 36 | 33:102 | Printed array mutual-coupling formula is implemented | `services/calculation-engine/aegislps_engine/earthing.py:64–111,448–459` | contradicted by code | none | describe pairwise coupling; independent primary source pending H4 |
| 37 | 33:104 | Foundation resistance rho/(4 re) + rho/P | `services/calculation-engine/aegislps_engine/earthing.py:487–498` | unsourced | none | code matches expression; establish primary source |
| 38 | 33:106 | Two-layer apparent resistivity exponential form | `services/calculation-engine/aegislps_engine/earthing.py:354–383` | unsourced | none | code matches expression; establish primary source and applicability |
| 38 | 33:106 | Two-layer reflection coefficient (rho2 − rho1)/(rho2 + rho1) | `services/calculation-engine/aegislps_engine/earthing.py:377–378` | unsourced | none | code matches expression; establish primary source |
| 39 | 33:108 | Impulse impedance Zp = Rdc/sqrt(1 + I/Icritical) | `services/calculation-engine/aegislps_engine/earthing.py:520–522` | unsourced | none | code matches expression; establish primary source |
| 39 | 33:108 | Icritical equals unclamped Ec rho/(2π Rdc²) | `services/calculation-engine/aegislps_engine/earthing.py:509–518` | contradicted by code | none | document lower guards and source uncertainty |
| 40 | 33:111 | Type B compliance compares circumference with l1 | `services/calculation-engine/aegislps_engine/earthing.py:433–436,524` | consistent | IEC 62305-3:2024 §5.4.2.3 Eq. (1) | H10-a proposal: compare effective radius, account for supplemental electrodes; not applied |
| 40 | 33:111 | l1(rho) slope is unverified | `services/calculation-engine/aegislps_engine/earthing.py:385–420` | unsourced | IEC 62305-3:2024 §5.4.2.2 Figure 5 | numerical curves unavailable in text; independent graphical verification pending |

Marker lines 21–40 are accounted for above. Both H10-a and H10-b remain unapplied; code-side proposal sketches appear in `step62_h10_claim_audit.md`. No nodal or earthing model change is authorized by the documentary mismatches.

## Step 6.6 batch 3 of 5: marker lines 41–60

Line references use `d9ee3ab`. IEC 62305-4:2024 Annex C.2.3.1.2–C.2.3.5, C.2.4 and C.2.5; IEC 62305-2:2024 §7.3, Annex A.2.1.2 and A.2.4; and IEC 62305-3:2024 §6.3.1–6.3.2 were read from `origin/main`. The IEEE 80 primary text is not among the four IEC documents and was not independently obtained.

| Marker | Source | Claim | Code location | Status | Standard / clause | Action |
|---:|---|---|---|---|---|---|
| 41 | 33:113 | Engine uses historical logarithmic mutual-coupling expression | `services/calculation-engine/aegislps_engine/earthing.py:64–111,448–459` | contradicted by code | none | replace stale label; pairwise model and its primary source remain under H4 |
| 41 | 33:113 | Historical expression disagrees with IEEE 80/Dwight datasets | none | unsourced | none | obtain actual primary dataset and comparison |
| 42 | 33:122 | Surface derating uses IEEE 80 Eq. 27 | `services/calculation-engine/aegislps_engine/touch_step.py:195–213` | unsourced | none | closed-form implementation includes guards; obtain IEEE 80 source |
| 43 | 33:124 | 70 kg tolerable touch formula with 0.157 coefficient | `services/calculation-engine/aegislps_engine/touch_step.py:287–302` | unsourced | none | code matches; verify IEEE 80 source and limits |
| 44 | 33:125 | 70 kg tolerable step formula with 0.157 coefficient | `services/calculation-engine/aegislps_engine/touch_step.py:287–302` | unsourced | none | code matches; verify IEEE 80 source and limits |
| 45 | 33:128 | Surface layer series summation is discarded | `services/calculation-engine/aegislps_engine/touch_step.py:195–213` | contradicted by code | none | describe current closed-form model rather than obsolete series claim |
| 45 | 33:128 | Prospective voltage is divided by ten | `services/calculation-engine/aegislps_engine/touch_step.py:304–310` | contradicted by code | none | remove stale historical claim |
| 45 | 33:128 | Fence and barrier flags zero or halve prospective voltages | `services/calculation-engine/aegislps_engine/touch_step.py:304–313` | contradicted by code | none | remove stale historical claim; mitigation remains advisory |
| 46 | 33:142 | Historical protective distance equals (Uw − Up) × 10 m | `services/calculation-engine/aegislps_engine/spd_coordination.py:288–310` | contradicted by code | IEC 62305-4:2024 §C.2.3.2–C.2.3.3 Eqs. (C.1)–(C.4) | remove stale heuristic; lead length differs from propagation distance |
| 47 | 33:145 | Heuristic replaced by connecting-lead calculation | `services/calculation-engine/aegislps_engine/spd_coordination.py:288–310` | consistent | IEC 62305-4:2024 §C.2.3.2–C.2.3.3 Eqs. (C.1)–(C.4) | retain with scope disclosure |
| 47 | 33:145 | Conservative screen Up ≤ 0.5 Uw applies in code for all cases | `services/calculation-engine/aegislps_engine/spd_coordination.py:195–211` | consistent | IEC 62305-4:2024 §C.2.3.1.4 | clarify conditional standard rule and conservative software simplification |
| 47 | 33:145 | Code implements required effective protection level Eq. (C.1) | `services/calculation-engine/aegislps_engine/spd_coordination.py:213–239` | consistent | IEC 62305-4:2024 §C.2.3.2 Eq. (C.1) | retain |
| 47 | 33:145 | Code implements limiting and switching SPD equations (C.2) and (C.3) | `services/calculation-engine/aegislps_engine/spd_coordination.py:250–265` | consistent | IEC 62305-4:2024 §C.2.3.3 Eqs. (C.2)–(C.3) | retain |
| 47 | 33:145 | Code implements connecting-lead voltage drop Eq. (C.4) | `services/calculation-engine/aegislps_engine/spd_coordination.py:241–248` | consistent | IEC 62305-4:2024 §C.2.3.3 Eq. (C.4) | retain |
| 47 | 33:145 | Code implements oscillation bound Eq. (C.5) | `services/calculation-engine/aegislps_engine/spd_coordination.py:267–270` | consistent | IEC 62305-4:2024 §C.2.3.4 Eq. (C.5) | retain; propagation analysis remains incomplete |
| 47 | 33:145 | Induced voltage Ui is required rather than automatically calculated | `services/calculation-engine/aegislps_engine/spd_coordination.py:213–239` | consistent | IEC 62305-4:2024 §C.2.3.5 | retain open limitation |
| 47 | 33:145 | Propagation-length criterion is qualitative and distance-dependent rule is not modeled | `services/calculation-engine/aegislps_engine/spd_coordination.py:195–211,267–270` | consistent | IEC 62305-4:2024 §C.2.3.1.2, §C.2.3.1.4, §C.2.3.4 | retain open limitation |
| 47 | 33:145 | Below 10 m, protection level should not exceed 80% of rated impulse voltage | `services/calculation-engine/aegislps_engine/spd_coordination.py:195–211` | consistent | IEC 62305-4:2024 §C.2.3.1.2 | qualify standard exceptions and category conditions; code uses 50% for all cases |
| 47 | 33:145 | Above 10 m, 50% bound is an option for a one-port SPD at origin | `services/calculation-engine/aegislps_engine/spd_coordination.py:195–211` | consistent | IEC 62305-4:2024 §C.2.3.1.4 | mention the accompanying shielding condition |
| 47 | 33:145 | Two-port SPD rules are not modeled | `services/calculation-engine/aegislps_engine/spd_coordination.py:195–211` | consistent | IEC 62305-4:2024 §C.2.3.1.4, §C.2.4 | retain open limitation |
| 47 | 33:145 | No numerical line-length gate formula is stated in the standard text | none | unsourced | IEC 62305-4:2024 §C.2.3.4 | manual text review is not proof of absence across the full standard; retain as bounded review finding |
| 48 | 33:152 | Rectangular structure Ad = LW + 6H(L+W) + 9πH² | `services/calculation-engine/aegislps_engine/risk.py:192–193` | consistent | IEC 62305-2:2024 Annex A.2.1.2 Eq. (A.3) | state rectangular isolated-structure scope |
| 49 | 33:153 | ND = Ng Ad Cd × 10⁻⁶ | `services/calculation-engine/aegislps_engine/risk.py:195–196` | contradicted by code | IEC 62305-2:2024 Annex A.1 Eq. (A.1), A.2.4 Eq. (A.5) | code uses input named Ng directly; 2024 uses strike-point density Nsg = k Ng, so terminology/input convention needs owner review; no formula change authorized |
| 50 | 33:155 | Legacy engine direct-strike subtotal RA + RB + RC | `services/calculation-engine/aegislps_engine/risk.py:232–237` | consistent | IEC 62305-2:2024 §6.3 | clarify that this is a partial direct-strike subtotal, not the complete risk |
| 51 | 33:156 | Representative tolerable risk is 1 × 10⁻⁵ per year | `services/calculation-engine/aegislps_engine/risk.py:238–239` | consistent | IEC 62305-2:2024 §7.3 Note 1 | qualify representative value; owner may select otherwise |
| 52 | 33:165 | Optimizer is experimental and outputs require deterministic review | `services/calculation-engine/aegislps_engine/optimization.py` | unsourced | none | maintain disclosure; not an IEC formula claim |
| 53 | 33:189 | Section heading only | none | non-claim | none | no action |
| 54 | 35:26 | Single-kc separation s = ki kc l / km | `services/calculation-engine/aegislps_engine/separation.py:173–177` | consistent | IEC 62305-3:2024 §6.3.2 Eq. (6) | specify simplified case |
| 55 | 35:28 | Class I ki = 0.08 | `packages/standards-data/aegislps_standards/repository.py:34–40` | consistent | IEC 62305-3:2024 §6.3.1 Table 11 | retain |
| 55 | 35:28 | Class II ki = 0.06 | `packages/standards-data/aegislps_standards/repository.py:42–48` | consistent | IEC 62305-3:2024 §6.3.1 Table 11 | retain |
| 55 | 35:28 | Classes III/IV ki = 0.04 | `packages/standards-data/aegislps_standards/repository.py:50–56` | consistent | IEC 62305-3:2024 §6.3.1 Table 11 | retain |
| 56 | 35:29 | Air km = 1.0 | `packages/standards-data/aegislps_standards/repository.py:58–64` | consistent | IEC 62305-3:2024 §6.3.1 Table 12 | retain |
| 56 | 35:29 | Solid concrete/masonry km = 0.5 | `packages/standards-data/aegislps_standards/repository.py:66–72` | consistent | IEC 62305-3:2024 §6.3.1 Table 12 | retain |
| 57 | 35:30 | Separation kc derives from network topology or nodal solver | `services/calculation-engine/aegislps_engine/separation.py:69–106` | contradicted by code | IEC 62305-3:2024 §6.3.2 Table 13 | correct to conductor-count lookup and fallback |
| 58 | 35:33 | Separation kc comes from segment count | `services/calculation-engine/aegislps_engine/separation.py:69–106` | contradicted by code | IEC 62305-3:2024 §6.3.2 Table 13 | replace obsolete defect note |
| 58 | 35:33 | Separation does not evaluate weighted segment sum | `services/calculation-engine/aegislps_engine/separation.py:158–177` | consistent | IEC 62305-3:2024 §6.3.1 Eq. (5) | H10-b proposal, not applied |
| 59 | 35:36 | Segment-by-segment varying-km sum is implemented | `services/calculation-engine/aegislps_engine/separation.py:158–177` | contradicted by code | IEC 62305-3:2024 §6.3.1 Eq. (5) | no implementation; standard Eq. (5) has one km outside the sum; do not attribute varying-km form to it |
| 60 | 35:40 | Compliance compares actual distance with s via margin ≥ 0 | `services/calculation-engine/aegislps_engine/separation.py:179–181,201–206` | consistent | IEC 62305-3:2024 §6.3.1 | retain; warnings can affect overall status |

Marker lines 41–60 are accounted for above. The Ng/Nsg distinction is a newly identified potential code/document convention issue: proposed design only is to represent the density type and conversion factor explicitly before applying Eq. (A.5); the schema, jurisdiction and source require owner review. No change is applied.
