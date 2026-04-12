# Cleaned CSV Interpretation Guide

This guide explains how to read a cleaned CSV produced by:

```bash
noaa-spec clean INPUT.csv OUTPUT.csv
```

For the versioned supported-field contract, use [supported_fields.md](supported_fields.md). That registry defines the recognized NOAA field families, public decoded column patterns, QC columns, sentinel handling, and provenance links for NOAA-Spec 1.0.0.

The output schema is deterministic for a given input file and NOAA-Spec version, but the full set of columns depends on which supported NOAA fields are present in the input. NOAA-Spec does not claim a fixed global column set for all possible NOAA ISD / Global Hourly data.

## Start Here

For a first pass, inspect decoded measurement columns such as `temperature_c`, `dew_point_c`, `visibility_m`, `wind_speed_ms`, `sea_level_pressure_hpa`, and `precip_amount_1`. Then inspect the nearby NOAA quality-code columns such as `temperature_quality_code`, `visibility_quality_code`, and `precip_quality_code_1`.

If a decoded measurement is empty, check sidecars such as `TMP__qc_status`, `TMP__qc_reason`, `VIS__part1__qc_status`, or `AA1__part2__qc_reason`. These sidecars distinguish sentinel missingness, bad quality codes, range failures, and malformed tokens where the parser has enough information to do so.

Raw NOAA identifier/source columns such as `STATION`, `REPORT_TYPE`, `REM`, or original encoded field names are mainly for traceability back to the source observation.

## Why The Output Is Wide

NOAA source rows can contain many optional encoded fields. NOAA-Spec expands recognized encoded fields that are present in the input into decoded value columns, quality-code columns, and validation sidecar columns. A file containing only `TMP` and `VIS` will produce fewer columns than one containing precipitation, cloud layers, present weather, pressure, and extreme-temperature fields.

Use [supported_fields.md](supported_fields.md) to determine which wide-column groups are part of the supported cleaned-output surface for this release.

## Column Groups

- Core decoded scientific fields: measurement columns with units in the name, such as `temperature_c`, `visibility_m`, `wind_speed_ms`, `sea_level_pressure_hpa`, and `precip_amount_1`.
- Preserved NOAA quality-code columns: NOAA quality/status codes kept in explicit columns, such as `temperature_quality_code`, `visibility_quality_code`, `precip_quality_code_1`, and `cloud_layer_base_height_quality_code_1`.
- Internal validation and QC sidecar columns: NOAA-Spec validation signals such as `TMP__qc_pass`, `TMP__qc_status`, `TMP__qc_reason`, `VIS__part1__qc_pass`, and `AA1__part2__qc_reason`.
- Row-level usability/status fields: interpretive summaries such as `row_has_any_usable_metric`, `usable_metric_count`, and `usable_metric_fraction`.
- Original row identifiers and unexpanded source fields: columns such as `STATION`, `DATE`, `REPORT_TYPE`, `REM`, and some optional source-field columns.

## Naming Conventions

- Plain scientific names use lower snake case and usually include units: `temperature_c`, `dew_point_c`, `visibility_m`, `wind_speed_ms`.
- NOAA quality codes use a `_quality_code` suffix when a friendly name exists: `temperature_quality_code`, `wind_speed_quality_code`, `precip_quality_code_1`.
- Some supplemental quality/flag columns keep shorter `_qc` or `_flag` suffixes, especially where the NOAA field already distinguishes QC and source flag parts.
- Repeating NOAA field families keep a numeric suffix: `AA1` becomes `precip_amount_1`, `AA2` becomes `precip_amount_2`; `GA1` becomes `cloud_layer_base_height_m_1`, `GA2` becomes `cloud_layer_base_height_m_2`.
- Validation sidecars retain the NOAA source identifier and part where needed: `TMP__qc_reason`, `VIS__part1__qc_status`, `AA1__part2__qc_pass`.
- Empty CSV cells represent null values in the deterministic output.

## Worked Examples

| Raw NOAA-style token | Cleaned columns | Interpretation |
| --- | --- | --- |
| `TMP=+9999,9` | `temperature_c=` empty, `temperature_quality_code=9`, `TMP__qc_status=MISSING`, `TMP__qc_reason=SENTINEL_MISSING` | The sentinel value is normalized to null, while the NOAA quality code is preserved. |
| `TMP=+0180,1` | `temperature_c=18.0`, `temperature_quality_code=1`, `TMP__qc_status=PASS` | The signed tenths-of-degrees value is scaled to degrees C and its quality code remains explicit. |
| `VIS=010000,1,N,1` | `visibility_m=10000.0`, `visibility_quality_code=1`, `visibility_variability_code=N`, `visibility_variability_quality_code=1`, `VIS__part1__qc_status=PASS` | The composite visibility field is split into distance, quality, variability, and variability-quality columns. |
| `AA1=24,0000,9,1` | `precip_period_hours_1=24.0`, `precip_amount_1=0.0`, `precip_condition_code_1=9`, `precip_quality_code_1=1` | The repeating precipitation field is decoded with the repeat index preserved in the column names. |

## Stability Notes

The intentional stable patterns are:

- decoded measurement names listed in [supported_fields.md](supported_fields.md);
- NOAA quality-code columns ending in `_quality_code` or documented supplemental `_qc`/`_flag` columns;
- repeated-field suffixes such as `_1`, `_2`, and `_3` when the corresponding supported NOAA source identifier is present;
- sidecar validation columns named from the NOAA identifier, such as `{IDENTIFIER}__qc_status` or `{IDENTIFIER}__partN__qc_reason`;
- row-level usability columns named `row_has_any_usable_metric`, `usable_metric_count`, and `usable_metric_fraction`.

For the same input file, NOAA-Spec version, and execution environment, the output CSV serialization is deterministic.

## What Is Guaranteed

- The supported field surface for NOAA-Spec 1.0.0 is documented in [supported_fields.md](supported_fields.md).
- Naming conventions for supported decoded fields are stable within this release.
- QC columns follow consistent documented patterns.
- Column ordering and CSV serialization are deterministic for the same input and version.

## What Is Not Guaranteed

- A fixed global column set across all possible NOAA inputs.
- Decoding for unsupported NOAA identifiers.
- End-to-end NOAA data download or multi-station orchestration.
