# RULE_IMPACT_REPORT

## Sample Description

Representative bounded sample from local station raw files under `output/<station>/LocationData_Raw.csv`.
No remote data was fetched.

| station_id | sample_rows |
|---|---|
| 01116099999 | 1500 |
| 03041099999 | 1500 |
| 16754399999 | 1500 |
| 27679099999 | 1500 |

Total sampled rows: **6000**

## Methodology

1. Read deterministic station sample in sorted station-id order with fixed row cap per station.
2. Build staged views on the same sampled rows:
   - raw input
   - parsed/minimally normalized (`clean_noaa_dataframe(..., strict_mode=False)`)
   - canonical cleaned (`clean_noaa_dataframe(..., strict_mode=True)`)
   - QC-flag summaries from canonical outputs
3. Compute row retention/exclusion, field null rates, QC reason counts, and identifier/family trigger rates.
4. Bucket impacts into structural parser effects, spec-supported cleaning effects, and stricter/flag-only effects.

## Overall Row/Field Impact Summary

| stage | rows_processed | rows_retained | rows_excluded |
|---|---|---|---|
| raw_input | 6000 | 6000 | 0 |
| parsed_minimal | 6000 | 6000 | 0 |
| cleaned_canonical | 6000 | 6000 | 0 |

Rows excluded in canonical stage: **0**
Rows with any cleaning/QC impact signal: **1.000000**
Field-cell impacts (signals over evaluated cells): **0.179488**

## Top Fields With Highest Nullification Rates

| identifier | count | denominator | rate |
|---|---|---|---|
| cloud_layer_type_code_3 | 6000 | 6000 | 1.000000 |
| cloud_layer_type_code_4 | 6000 | 6000 | 1.000000 |
| cloud_opaque_coverage | 6000 | 6000 | 1.000000 |
| pressure_change_24hr_hpa | 6000 | 6000 | 1.000000 |
| cloud_layer_base_height_m_4 | 5997 | 6000 | 0.999500 |
| cloud_layer_base_height_quality_code_4 | 5997 | 6000 | 0.999500 |
| cloud_layer_coverage_4 | 5997 | 6000 | 0.999500 |
| cloud_layer_coverage_quality_code_4 | 5997 | 6000 | 0.999500 |
| cloud_layer_type_quality_code_4 | 5997 | 6000 | 0.999500 |
| precip_condition_code_1 | 5972 | 6000 | 0.995333 |
| cloud_layer_type_code_2 | 5961 | 6000 | 0.993500 |
| ground_surface_observation_code | 5894 | 6000 | 0.982333 |
| ground_surface_observation_quality_code | 5894 | 6000 | 0.982333 |
| MW2__part2 | 5873 | 6000 | 0.978833 |
| present_weather_code_2 | 5873 | 6000 | 0.978833 |

## Top Identifiers With Highest QC-Flag Rates

| identifier | count | denominator | rate |
|---|---|---|---|
| GF1 | 9825 | 6000 | 1.637500 |
| CONTROL | 6000 | 6000 | 1.000000 |
| SLP | 4517 | 6000 | 0.752833 |
| MA1 | 3329 | 6000 | 0.554833 |
| CIG | 1972 | 6000 | 0.328667 |
| VIS | 1505 | 6000 | 0.250833 |
| MD1 | 1497 | 6000 | 0.249500 |
| AA1 | 459 | 6000 | 0.076500 |
| WND | 377 | 6000 | 0.062833 |
| KA1 | 313 | 6000 | 0.052167 |
| GA1 | 227 | 6000 | 0.037833 |
| DEW | 76 | 6000 | 0.012667 |
| TMP | 57 | 6000 | 0.009500 |

## Impact Buckets

| bucket | count | rate_vs_rows |
|---|---|---|
| structural_parser_integrity | 18235 | 3.039167 |
| spec_supported_cleaning | 24154 | 4.025667 |
| stricter_or_flag_only | 6000 | 1.000000 |

## Rule Family Impact Summary

| rule_family | cells_affected | fraction_of_total_cells | fraction_of_total_impacts |
|---|---|---|---|
| sentinel_handling | 24154 | 0.075494 | 0.499163 |
| quality_code_handling | 0 | 0.000000 | 0.000000 |
| domain_validation | 6000 | 0.018753 | 0.123995 |
| range_validation | 0 | 0.000000 | 0.000000 |
| pattern_validation | 0 | 0.000000 | 0.000000 |
| arity_validation | 18235 | 0.056994 | 0.376842 |
| width_validation | 0 | 0.000000 | 0.000000 |
| structural_parser_guard | 0 | 0.000000 | 0.000000 |

## Interpretation

- What changes most: fields/identifiers listed above with highest strict-cleaning nullification and QC trigger rates.
- What changes little: fields with near-zero newly-null rates and low QC trigger counts in `rule_impact_summary.csv`.
- Conservativeness vs destructiveness: compare `altered_row_fraction`, `altered_field_fraction`, and bucket magnitudes; this report provides empirical counts only.

## Notes

- `width/structure` counts are reported from parse/QC signals when available in sampled data.
- This artifact quantifies cleaning-rule impact; it does not rate NOAA data quality.
