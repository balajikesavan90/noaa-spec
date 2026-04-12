# Cleaned CSV Schema

The output schema is deterministic for a given input file and version, but the full set of columns depends on which NOAA fields are present in the input.

The public NOAA-Spec output contract is the cleaned CSV produced by:

```bash
noaa-spec clean INPUT.csv OUTPUT.csv
```

This CSV remains at the observation-row level. It does not aggregate observations or select a single analysis subset. Its purpose is to make NOAA ISD / Global Hourly encoded fields easier to inspect while preserving the quality context needed for downstream scientific filtering.

NOAA-Spec provides a consistent and reproducible interpretation of NOAA ISD CSV fields, rather than asserting a single authoritative canonical schema for all possible NOAA data.

## Why The Output Is Wide

NOAA source rows can contain many optional encoded fields. NOAA-Spec expands each encoded field that is present in the input into decoded value columns, quality-code columns, and a small set of validation sidecar columns. As a result, output width varies with the source fields present in the input file. A file containing only `TMP` and `VIS` will produce fewer columns than one containing precipitation, cloud layers, present weather, pressure, and extreme-temperature fields.

## Column Groups

- Core decoded scientific fields: measurement columns with units in the name, such as `temperature_c`, `visibility_m`, `wind_speed_ms`, `sea_level_pressure_hpa`, and `precip_amount_1`.
- Preserved NOAA quality-code columns: NOAA quality/status codes kept in explicit columns, such as `temperature_quality_code`, `visibility_quality_code`, `precip_quality_code_1`, and `cloud_layer_base_height_quality_code_1`.
- Internal validation and QC sidecar columns: NOAA-Spec validation signals such as `TMP__qc_pass`, `TMP__qc_status`, `TMP__qc_reason`, `VIS__part1__qc_pass`, and `AA1__part2__qc_reason`.
- Row-level usability/status fields: public cleaned-output summaries such as `row_has_any_usable_metric`, `usable_metric_count`, and `usable_metric_fraction`.
- Original row identifiers and unexpanded source fields: columns such as `STATION`, `DATE`, `REPORT_TYPE`, `REM`, and some optional source-field columns may remain so the cleaned row can still be related to the original observation.

## Naming Conventions

- Plain scientific names use lower snake case and usually include units: `temperature_c`, `dew_point_c`, `visibility_m`, `wind_speed_ms`.
- NOAA quality codes use a `_quality_code` suffix: `temperature_quality_code`, `wind_speed_quality_code`, `precip_quality_code_1`.
- Repeating NOAA field families keep a numeric suffix: `AA1` becomes `precip_amount_1`, `AA2` becomes `precip_amount_2`; `GA1` becomes `cloud_layer_base_height_m_1`, `GA2` becomes `cloud_layer_base_height_m_2`.
- Validation sidecars retain the NOAA source identifier and part where needed: `TMP__qc_reason`, `VIS__part1__qc_status`, `AA1__part2__qc_pass`.
- Empty CSV cells represent null values in the deterministic output.

## Examples

| Raw NOAA-style token | Cleaned columns | Interpretation |
| --- | --- | --- |
| `TMP=+9999,9` | `temperature_c=` empty, `temperature_quality_code=9`, `TMP__qc_status=MISSING`, `TMP__qc_reason=SENTINEL_MISSING` | The sentinel value is normalized to null, while the NOAA quality code is preserved. |
| `TMP=+0180,1` | `temperature_c=18.0`, `temperature_quality_code=1`, `TMP__qc_status=PASS` | The signed tenths-of-degrees value is scaled to degrees C and its quality code remains explicit. |
| `VIS=010000,1,N,1` | `visibility_m=10000.0`, `visibility_quality_code=1`, `visibility_variability_code=N`, `visibility_variability_quality_code=1`, `VIS__part1__qc_status=PASS` | The composite visibility field is split into distance, quality, variability, and variability-quality columns. |
| `AA1=24,0000,9,1` | `precip_period_hours_1=24.0`, `precip_amount_1=0.0`, `precip_condition_code_1=9`, `precip_quality_code_1=1` | The repeating precipitation field is decoded with the repeat index preserved in the column names. |

## Stability Contract

The intentional stable patterns are:

- decoded measurement names such as `temperature_c`, `visibility_m`, and `precip_amount_1`;
- NOAA quality-code columns ending in `_quality_code`;
- repeated-field suffixes such as `_1`, `_2`, and `_3` when the corresponding NOAA source identifier is present;
- sidecar validation columns named from the NOAA identifier, such as `{IDENTIFIER}__qc_status` or `{IDENTIFIER}__partN__qc_reason`;
- row-level usability columns named `row_has_any_usable_metric`, `usable_metric_count`, and `usable_metric_fraction`.

Columns appear when the corresponding source fields are present in the input and recognized by the parser. For the same input file, NOAA-Spec version, and execution environment, the output CSV serialization is deterministic.

## What Is Guaranteed

- Naming conventions are stable.
- QC columns follow consistent patterns.
- Column ordering is deterministic.
- The same input, NOAA-Spec version, and execution environment produce the same output serialization.

## What Is NOT Guaranteed

- A fixed global column set across all possible inputs.
- Exhaustive schema enumeration in this document.
