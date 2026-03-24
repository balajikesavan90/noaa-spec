# SPEC Coverage Report

## How to run

```bash
poetry run python tools/spec_coverage/generate_spec_coverage.py
```

## Overall coverage

- Total spec rules extracted: **3536**
- Structural rules (control-position rules like `POS 1-4 width 4`): **12**
- Documentation rules count (excluded): **0**
- Metric-eligible rules (excluding `unknown`): **3536**
- Unknown/noisy rows excluded from %: **0**
- Rules implemented in code: **3536** (100.0%)
- Progress KPI (`tested_strict`): **3536** (100.0%)
- Weak coverage (`tested_any`, includes wildcard): **3536** (100.0%)
- tested_any from non-wild matches only: **3536** (100.0%)
- Wildcard-only tested_any (not counted toward progress): **0** (0.0%)
- Coverage progress is measured with `tested_strict` only.
- `test_covered` in CSV mirrors `test_covered_any` for backward compatibility.

## Top 50 real gaps (strict)

Strict gaps are metric spec-rule rows where `code_implemented=FALSE` or `test_covered_strict=FALSE`.
Rows with `identifier=UNSPECIFIED` or `synthetic_unmapped` notes are excluded from this actionable list.

| rank | spec_part | identifier | rule_type | enforcement_layer | implemented | test_strict | test_any | match_strength | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| - | - | - | - | - | - | - | - | - | (none) |

### Implementation gaps (strict): Not implemented + not tested_strict

| rank | spec_part | identifier | rule_type | enforcement_layer | implemented | test_strict | test_any | match_strength | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| - | - | - | - | - | - | - | - | - | (none) |

### Missing tests (strict): Implemented + not tested_strict

| rank | spec_part | identifier | rule_type | enforcement_layer | implemented | test_strict | test_any | match_strength | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| - | - | - | - | - | - | - | - | - | (none) |

## Rule Identity & Provenance

- `rule_id` format for spec rows: `{spec_file}::{stable_id}::{identifier}::{rule_type}::{payload_hash}`.
- `stable_id` is derived from normalized rule text plus canonical payload data, so line-only shifts do not churn IDs.
- Provenance remains in `spec_line_start`/`spec_line_end`, which point to global lines in `isd-format-document.deterministic.md`.

## Enforcement layer breakdown

- constants_only: **2644** (74.8%)
- cleaning_only: **4** (0.1%)
- both: **888** (25.1%)
- neither: **0** (0.0%)

## Confidence breakdown

- Cleaning-implemented metric rules: **892** (25.2%)
- high: **3** (0.3%)
- medium: **889** (99.7%)
- low: **0** (0.0%)

## Match quality

| Match strength | Count | % of metric rules |
| --- | --- | --- |
| exact_signature | 1560 | 44.1% |
| exact_assertion | 1972 | 55.8% |
| family_assertion | 4 | 0.1% |
| wildcard_assertion | 0 | 0.0% |
| none | 0 | 0.0% |

## Precision warnings

- Wildcard policy: `wildcard_assertion` counts as tested-any only; it never counts as strict.
- Tested-any rows matched by `exact_signature`: **1560** (44.1%)
- Tested-any rows matched by `exact_assertion`: **1972** (55.8%)
- Tested-any rows matched by `family_assertion`: **4** (0.1%)
- Tested-any rows matched by `wildcard_assertion`: **0** (0.0%)
- Unknown rule rows excluded from percentages: **0**
- Arity rules tested (strict): **170/170** (100.0%)
- Arity rules tested (any): **170/170** (100.0%)
- Arity tests detected in `tests/test_cleaning.py`: **YES**

## Suspicious coverage

- tested_any=TRUE and code_implemented=FALSE: **0** (0.0%)
| Rule ID | Identifier family | Rule type | Notes |
| --- | --- | --- | --- |
| (none) | - | - | - |

- tested_any=TRUE and match_strength=`wildcard_assertion`: **0** (0.0%)
| Rule ID | Identifier family | Rule type | Notes |
| --- | --- | --- | --- |
| (none) | - | - | - |

## Breakdown by ISD part

| Part | Rules | Metric rules | Implemented | Tested strict | Tested any (weak) | Implemented % | Tested strict % | Tested any (weak) % |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 01 | 0 | 0 | 0 | 0 | 0 | 0.0% | 0.0% | 0.0% |
| 02 | 31 | 31 | 31 | 31 | 31 | 100.0% | 100.0% | 100.0% |
| 03 | 54 | 54 | 54 | 54 | 54 | 100.0% | 100.0% | 100.0% |
| 04 | 603 | 603 | 603 | 603 | 603 | 100.0% | 100.0% | 100.0% |
| 05 | 451 | 451 | 451 | 451 | 451 | 100.0% | 100.0% | 100.0% |
| 06 | 287 | 287 | 287 | 287 | 287 | 100.0% | 100.0% | 100.0% |
| 07 | 81 | 81 | 81 | 81 | 81 | 100.0% | 100.0% | 100.0% |
| 08 | 11 | 11 | 11 | 11 | 11 | 100.0% | 100.0% | 100.0% |
| 09 | 30 | 30 | 30 | 30 | 30 | 100.0% | 100.0% | 100.0% |
| 10 | 57 | 57 | 57 | 57 | 57 | 100.0% | 100.0% | 100.0% |
| 11 | 111 | 111 | 111 | 111 | 111 | 100.0% | 100.0% | 100.0% |
| 12 | 20 | 20 | 20 | 20 | 20 | 100.0% | 100.0% | 100.0% |
| 13 | 111 | 111 | 111 | 111 | 111 | 100.0% | 100.0% | 100.0% |
| 14 | 15 | 15 | 15 | 15 | 15 | 100.0% | 100.0% | 100.0% |
| 15 | 472 | 472 | 472 | 472 | 472 | 100.0% | 100.0% | 100.0% |
| 16 | 24 | 24 | 24 | 24 | 24 | 100.0% | 100.0% | 100.0% |
| 17 | 84 | 84 | 84 | 84 | 84 | 100.0% | 100.0% | 100.0% |
| 18 | 27 | 27 | 27 | 27 | 27 | 100.0% | 100.0% | 100.0% |
| 19 | 38 | 38 | 38 | 38 | 38 | 100.0% | 100.0% | 100.0% |
| 20 | 20 | 20 | 20 | 20 | 20 | 100.0% | 100.0% | 100.0% |
| 21 | 20 | 20 | 20 | 20 | 20 | 100.0% | 100.0% | 100.0% |
| 22 | 8 | 8 | 8 | 8 | 8 | 100.0% | 100.0% | 100.0% |
| 23 | 109 | 109 | 109 | 109 | 109 | 100.0% | 100.0% | 100.0% |
| 24 | 245 | 245 | 245 | 245 | 245 | 100.0% | 100.0% | 100.0% |
| 25 | 7 | 7 | 7 | 7 | 7 | 100.0% | 100.0% | 100.0% |
| 26 | 29 | 29 | 29 | 29 | 29 | 100.0% | 100.0% | 100.0% |
| 27 | 109 | 109 | 109 | 109 | 109 | 100.0% | 100.0% | 100.0% |
| 28 | 17 | 17 | 17 | 17 | 17 | 100.0% | 100.0% | 100.0% |
| 29 | 299 | 299 | 299 | 299 | 299 | 100.0% | 100.0% | 100.0% |
| 30 | 166 | 166 | 166 | 166 | 166 | 100.0% | 100.0% | 100.0% |

## Breakdown by identifier family

| Identifier family | Rules | Metric rules | Implemented | Tested strict | Tested any (weak) | Implemented % | Tested strict % | Tested any (weak) % |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AA | 69 | 69 | 69 | 69 | 69 | 100.0% | 100.0% | 100.0% |
| AB | 12 | 12 | 12 | 12 | 12 | 100.0% | 100.0% | 100.0% |
| AC | 10 | 10 | 10 | 10 | 10 | 100.0% | 100.0% | 100.0% |
| AD | 23 | 23 | 23 | 23 | 23 | 100.0% | 100.0% | 100.0% |
| AE | 26 | 26 | 26 | 26 | 26 | 100.0% | 100.0% | 100.0% |
| AG | 9 | 9 | 9 | 9 | 9 | 100.0% | 100.0% | 100.0% |
| AH | 126 | 126 | 126 | 126 | 126 | 100.0% | 100.0% | 100.0% |
| AI | 126 | 126 | 126 | 126 | 126 | 100.0% | 100.0% | 100.0% |
| AJ | 22 | 22 | 22 | 22 | 22 | 100.0% | 100.0% | 100.0% |
| AK | 16 | 16 | 16 | 16 | 16 | 100.0% | 100.0% | 100.0% |
| AL | 64 | 64 | 64 | 64 | 64 | 100.0% | 100.0% | 100.0% |
| AM | 23 | 23 | 23 | 23 | 23 | 100.0% | 100.0% | 100.0% |
| AN | 15 | 15 | 15 | 15 | 15 | 100.0% | 100.0% | 100.0% |
| AO | 64 | 64 | 64 | 64 | 64 | 100.0% | 100.0% | 100.0% |
| AP | 10 | 10 | 10 | 10 | 10 | 100.0% | 100.0% | 100.0% |
| AT | 80 | 80 | 80 | 80 | 80 | 100.0% | 100.0% | 100.0% |
| AU | 225 | 225 | 225 | 225 | 225 | 100.0% | 100.0% | 100.0% |
| AW | 8 | 8 | 8 | 8 | 8 | 100.0% | 100.0% | 100.0% |
| AX | 84 | 84 | 84 | 84 | 84 | 100.0% | 100.0% | 100.0% |
| AY | 26 | 26 | 26 | 26 | 26 | 100.0% | 100.0% | 100.0% |
| AZ | 28 | 28 | 28 | 28 | 28 | 100.0% | 100.0% | 100.0% |
| CALL_SIGN | 2 | 2 | 2 | 2 | 2 | 100.0% | 100.0% | 100.0% |
| CB | 28 | 28 | 28 | 28 | 28 | 100.0% | 100.0% | 100.0% |
| CF | 33 | 33 | 33 | 33 | 33 | 100.0% | 100.0% | 100.0% |
| CG | 30 | 30 | 30 | 30 | 30 | 100.0% | 100.0% | 100.0% |
| CH | 46 | 46 | 46 | 46 | 46 | 100.0% | 100.0% | 100.0% |
| CI | 36 | 36 | 36 | 36 | 36 | 100.0% | 100.0% | 100.0% |
| CIG | 12 | 12 | 12 | 12 | 12 | 100.0% | 100.0% | 100.0% |
| CN | 114 | 114 | 114 | 114 | 114 | 100.0% | 100.0% | 100.0% |
| CO | 81 | 81 | 81 | 81 | 81 | 100.0% | 100.0% | 100.0% |
| CONTROL | 17 | 17 | 17 | 17 | 17 | 100.0% | 100.0% | 100.0% |
| CR | 11 | 11 | 11 | 11 | 11 | 100.0% | 100.0% | 100.0% |
| CT | 30 | 30 | 30 | 30 | 30 | 100.0% | 100.0% | 100.0% |
| CU | 57 | 57 | 57 | 57 | 57 | 100.0% | 100.0% | 100.0% |
| CV | 111 | 111 | 111 | 111 | 111 | 100.0% | 100.0% | 100.0% |
| CW | 20 | 20 | 20 | 20 | 20 | 100.0% | 100.0% | 100.0% |
| CX | 111 | 111 | 111 | 111 | 111 | 100.0% | 100.0% | 100.0% |
| DATE | 1 | 1 | 1 | 1 | 1 | 100.0% | 100.0% | 100.0% |
| DEW | 5 | 5 | 5 | 5 | 5 | 100.0% | 100.0% | 100.0% |
| ED | 15 | 15 | 15 | 15 | 15 | 100.0% | 100.0% | 100.0% |
| ELEVATION | 2 | 2 | 2 | 2 | 2 | 100.0% | 100.0% | 100.0% |
| GA | 24 | 24 | 24 | 24 | 24 | 100.0% | 100.0% | 100.0% |
| GD | 216 | 216 | 216 | 216 | 216 | 100.0% | 100.0% | 100.0% |
| GE | 11 | 11 | 11 | 11 | 11 | 100.0% | 100.0% | 100.0% |
| GF | 39 | 39 | 39 | 39 | 39 | 100.0% | 100.0% | 100.0% |
| GG | 144 | 144 | 144 | 144 | 144 | 100.0% | 100.0% | 100.0% |
| GH | 38 | 38 | 38 | 38 | 38 | 100.0% | 100.0% | 100.0% |
| GJ | 8 | 8 | 8 | 8 | 8 | 100.0% | 100.0% | 100.0% |
| GK | 8 | 8 | 8 | 8 | 8 | 100.0% | 100.0% | 100.0% |
| GL | 8 | 8 | 8 | 8 | 8 | 100.0% | 100.0% | 100.0% |
| GM | 43 | 43 | 43 | 43 | 43 | 100.0% | 100.0% | 100.0% |
| GN | 41 | 41 | 41 | 41 | 41 | 100.0% | 100.0% | 100.0% |
| GO | 27 | 27 | 27 | 27 | 27 | 100.0% | 100.0% | 100.0% |
| GP | 38 | 38 | 38 | 38 | 38 | 100.0% | 100.0% | 100.0% |
| GQ | 20 | 20 | 20 | 20 | 20 | 100.0% | 100.0% | 100.0% |
| GR | 20 | 20 | 20 | 20 | 20 | 100.0% | 100.0% | 100.0% |
| HAIL | 8 | 8 | 8 | 8 | 8 | 100.0% | 100.0% | 100.0% |
| IA | 16 | 16 | 16 | 16 | 16 | 100.0% | 100.0% | 100.0% |
| IB | 54 | 54 | 54 | 54 | 54 | 100.0% | 100.0% | 100.0% |
| IC | 39 | 39 | 39 | 39 | 39 | 100.0% | 100.0% | 100.0% |
| KA | 60 | 60 | 60 | 60 | 60 | 100.0% | 100.0% | 100.0% |
| KB | 45 | 45 | 45 | 45 | 45 | 100.0% | 100.0% | 100.0% |
| KC | 38 | 38 | 38 | 38 | 38 | 100.0% | 100.0% | 100.0% |
| KD | 30 | 30 | 30 | 30 | 30 | 100.0% | 100.0% | 100.0% |
| KE | 26 | 26 | 26 | 26 | 26 | 100.0% | 100.0% | 100.0% |
| KF | 8 | 8 | 8 | 8 | 8 | 100.0% | 100.0% | 100.0% |
| KG | 38 | 38 | 38 | 38 | 38 | 100.0% | 100.0% | 100.0% |
| LATITUDE | 2 | 2 | 2 | 2 | 2 | 100.0% | 100.0% | 100.0% |
| LONGITUDE | 2 | 2 | 2 | 2 | 2 | 100.0% | 100.0% | 100.0% |
| MA | 13 | 13 | 13 | 13 | 13 | 100.0% | 100.0% | 100.0% |
| MD | 18 | 18 | 18 | 18 | 18 | 100.0% | 100.0% | 100.0% |
| ME | 10 | 10 | 10 | 10 | 10 | 100.0% | 100.0% | 100.0% |
| MF | 16 | 16 | 16 | 16 | 16 | 100.0% | 100.0% | 100.0% |
| MG | 15 | 15 | 15 | 15 | 15 | 100.0% | 100.0% | 100.0% |
| MH | 14 | 14 | 14 | 14 | 14 | 100.0% | 100.0% | 100.0% |
| MK | 23 | 23 | 23 | 23 | 23 | 100.0% | 100.0% | 100.0% |
| MV | 12 | 12 | 12 | 12 | 12 | 100.0% | 100.0% | 100.0% |
| MW | 5 | 5 | 5 | 5 | 5 | 100.0% | 100.0% | 100.0% |
| N | 11 | 11 | 11 | 11 | 11 | 100.0% | 100.0% | 100.0% |
| OA | 51 | 51 | 51 | 51 | 51 | 100.0% | 100.0% | 100.0% |
| OB | 48 | 48 | 48 | 48 | 48 | 100.0% | 100.0% | 100.0% |
| OC | 8 | 8 | 8 | 8 | 8 | 100.0% | 100.0% | 100.0% |
| OD | 63 | 63 | 63 | 63 | 63 | 100.0% | 100.0% | 100.0% |
| OE | 69 | 69 | 69 | 69 | 69 | 100.0% | 100.0% | 100.0% |
| QC_PROCESS | 1 | 1 | 1 | 1 | 1 | 100.0% | 100.0% | 100.0% |
| REPORT_TYPE | 3 | 3 | 3 | 3 | 3 | 100.0% | 100.0% | 100.0% |
| RH | 60 | 60 | 60 | 60 | 60 | 100.0% | 100.0% | 100.0% |
| SA | 7 | 7 | 7 | 7 | 7 | 100.0% | 100.0% | 100.0% |
| SLP | 6 | 6 | 6 | 6 | 6 | 100.0% | 100.0% | 100.0% |
| ST | 29 | 29 | 29 | 29 | 29 | 100.0% | 100.0% | 100.0% |
| TIME | 1 | 1 | 1 | 1 | 1 | 100.0% | 100.0% | 100.0% |
| TMP | 5 | 5 | 5 | 5 | 5 | 100.0% | 100.0% | 100.0% |
| UA | 19 | 19 | 19 | 19 | 19 | 100.0% | 100.0% | 100.0% |
| UG | 30 | 30 | 30 | 30 | 30 | 100.0% | 100.0% | 100.0% |
| VIS | 10 | 10 | 10 | 10 | 10 | 100.0% | 100.0% | 100.0% |
| WA | 13 | 13 | 13 | 13 | 13 | 100.0% | 100.0% | 100.0% |
| WD | 35 | 35 | 35 | 35 | 35 | 100.0% | 100.0% | 100.0% |
| WG | 11 | 11 | 11 | 11 | 11 | 100.0% | 100.0% | 100.0% |
| WJ | 30 | 30 | 30 | 30 | 30 | 100.0% | 100.0% | 100.0% |
| WND | 21 | 21 | 21 | 21 | 21 | 100.0% | 100.0% | 100.0% |

## Breakdown by rule type

| Rule type | Rules | Implemented | Tested strict | Tested any (weak) | Implemented % | Tested strict % | Tested any (weak) % |
| --- | --- | --- | --- | --- | --- | --- | --- |
| range | 361 | 361 | 361 | 361 | 100.0% | 100.0% | 100.0% |
| sentinel | 687 | 687 | 687 | 687 | 100.0% | 100.0% | 100.0% |
| allowed_quality | 80 | 80 | 80 | 80 | 100.0% | 100.0% | 100.0% |
| domain | 889 | 889 | 889 | 889 | 100.0% | 100.0% | 100.0% |
| cardinality | 128 | 128 | 128 | 128 | 100.0% | 100.0% | 100.0% |
| width | 1221 | 1221 | 1221 | 1221 | 100.0% | 100.0% | 100.0% |
| arity | 170 | 170 | 170 | 170 | 100.0% | 100.0% | 100.0% |
| unknown | 0 | 0 | 0 | 0 | excluded | excluded | excluded |

## Wildcard-only coverage (not counted toward progress)

- Wildcard-only rows (`test_covered_any=TRUE` and `test_covered_strict=FALSE`): **0** (0.0%)

| Part | Wildcard-only rows | % of metric rules |
| --- | --- | --- |
| (none) | 0 | 0.0% |

| Rule type | Wildcard-only rows | % of metric rules |
| --- | --- | --- |
| range | 0 | 0.0% |
| sentinel | 0 | 0.0% |
| allowed_quality | 0 | 0.0% |
| domain | 0 | 0.0% |
| cardinality | 0 | 0.0% |
| width | 0 | 0.0% |
| arity | 0 | 0.0% |

## How to extend

- Add or tweak regexes in `parse_spec_doc()` for new rule text patterns.
- Update `SPEC_PART_ANCHORS` and `segment_spec_doc_lines()` if the deterministic source layout changes.
- Extend `infer_rule_types_from_text()` if new rule classes appear.
- Extend `coverage_in_constants_for_row()` and `coverage_in_cleaning_for_row()` for new enforcement metadata.
- Extend `parse_tests_evidence()` value-token and assertion-intent hooks for new test styles.
- Keep deterministic ordering by preserving `sort_key()` and fixed table order.
