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
