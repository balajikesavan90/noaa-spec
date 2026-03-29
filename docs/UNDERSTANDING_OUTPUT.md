# Understanding the Output

This guide is for first-time users who want to understand what the canonical cleaned output contains and what the cleaner changed. The output described here is NOAA-Spec's stable cleaned representation for NOAA ISD / Global Hourly records, not a claim of community-wide standardization.

## What this file is

The canonical cleaned CSV is intentionally wide. It is a loss-preserving normalized representation of NOAA observations: cleaned measurement fields, preserved QC context, and supporting observation metadata live together in one deterministic source-of-truth layer.

That means most downstream workflows will not use every column. Analysts will usually select a relevant subset for a task, and broader repository workflows can also derive narrower domain datasets from the canonical layer.

## A 10-column subset

Here is a useful subset from the canonical cleaned sample:

| Column | Meaning |
| --- | --- |
| `STATION` | NOAA station identifier |
| `DATE` | observation timestamp |
| `LATITUDE` | station latitude from the source row |
| `LONGITUDE` | station longitude from the source row |
| `REPORT_TYPE` | NOAA report type |
| `temperature_c` | cleaned temperature in Celsius |
| `temperature_quality_code` | NOAA QC code for temperature |
| `dew_point_c` | cleaned dew point in Celsius |
| `wind_speed_ms` | cleaned wind speed in meters per second |
| `visibility_m` | cleaned visibility in meters |

## Where to start

Start with the measurement columns:

- `temperature_c`
- `dew_point_c`
- `wind_speed_ms`
- `visibility_m`

Many `*_quality_code`, `*_QC`, and `__qc_*` columns can be ignored initially unless you are filtering by quality or investigating why a cleaned value is missing (`NaN`).

## Sentinel handling

NOAA raw files use encoded missing-value sentinels such as `+9999,9` or `999999,9,N,1`.

NOAA-Spec does not leave those as misleading numbers.

- sentinel numeric values become missing values (`NaN`) in the canonical cleaned output
- the related NOAA quality code is still preserved
- the row itself is kept unless the underlying parser rules require something stricter

## QC flags

QC information is kept in explicit columns rather than being silently dropped.

Examples:

- `temperature_quality_code`
- `TMP__qc_pass`
- `TMP__qc_status`
- `TMP__qc_reason`

This lets you decide later whether to filter, inspect, or stratify by data quality.

## Missing values

In the canonical cleaned CSV, missing cleaned values appear as empty cells and will typically be read by pandas as missing values (`NaN`).

That usually means one of these:

- the source value was a documented NOAA sentinel
- the source token failed validation
- the source value carried a QC condition that prevented conversion into a usable numeric value

The supporting QC columns tell you which case happened.

## BEFORE -> AFTER example

Example raw row fragment:

```text
DATE=2000-03-17T09:00:00
TMP=+9999,9
DEW=+9999,9
VIS=999999,9,N,1
```

After cleaning:

```text
DATE=2000-03-17T09:00:00
temperature_c=NaN
temperature_quality_code=9
dew_point_c=NaN
visibility_m=NaN
TMP__qc_reason=SENTINEL_MISSING
```

What happened:

- `+9999` is a sentinel, so `temperature_c` becomes a missing value (`NaN`)
- the NOAA quality code `9` is preserved in `temperature_quality_code`
- the row remains available for downstream analysis
- QC sidecar columns explain why the cleaned value is missing

## What this output is good for

This canonical cleaned representation is a better starting point when you want:

- consistent field handling across many stations
- a reusable, deterministic source representation for downstream analysis
- QC-aware filtering after cleaning rather than ad hoc preprocessing before it

When you only need one part of the observational record, start from a subset of relevant columns. In broader repository workflows, NOAA-Spec can also emit narrower domain datasets for focused downstream use.

If you only need a quick notebook exploration of one file, this may be more structure than you need.
