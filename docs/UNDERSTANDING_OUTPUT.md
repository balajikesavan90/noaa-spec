# Understanding the Output

This guide is for first-time users who want to understand what the canonical output contains, what NOAA-Spec changed, and when to use a narrower view instead of the full table. The output described here is NOAA-Spec's stable canonical representation for NOAA ISD / Global Hourly records, not a claim of community-wide standardization.

## What this file is

The canonical CSV is intentionally wide. It is a canonical, loss-preserving normalized representation of NOAA observations: cleaned measurement fields, preserved QC context, and supporting observation metadata live together in one deterministic source-of-truth layer.

NOAA ISD is structurally rich and heavily encoded. The width is intentional because canonicalization preserves reusable semantics that would otherwise remain buried in compact field tokens and project-local parsing rules.

Most users will work with a subset of fields or a domain-specific projection. Treat the canonical table as the stable intermediate contract rather than the final analysis surface for every task.

The canonical dataset defines the reproducible interpretation contract. Optional `--view` outputs are derived projections for usability and do not modify the underlying contract.

The public CLI also exposes optional canonical-derived views such as `metadata`, `wind`, `precipitation`, `clouds_visibility`, `pressure_temperature`, and `remarks`. Those narrower views exist to make common workflows easier to approach while keeping the canonical table as the authoritative source layer.

## Optional views

If the full canonical CSV feels too wide after your canonical first pass, write a view directly:

```bash
noaa-spec clean reproducibility/minimal/station_raw.csv /tmp/station_pressure_temperature.csv --view pressure_temperature
```

How the two layers relate:

- canonical output: the primary, loss-preserving contract
- `--view` output: an optional usability layer derived from the canonical table
- reproducibility verification: still based on the canonical output, not on a view

Use `metadata` when you want station/time context and identifying fields only. For compatibility, `core` and `core_meteorology` remain accepted aliases for that same metadata view.

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

For the bundled reviewer fixture, this subset is usually enough for a first read:

| `STATION` | `DATE` | `temperature_c` | `temperature_quality_code` | `visibility_m` | `TMP__qc_reason` |
| --- | --- | --- | --- | --- | --- |
| `40435099999` | `2000-01-10T06:00:00` | `18.0` | `1` | `10000.0` | |
| `40435099999` | `2000-03-17T09:00:00` | | `9` | | `SENTINEL_MISSING` |

## How most users should approach this output

- treat the canonical table as the source-of-truth intermediate representation
- inspect a subset of relevant fields for your task
- use a `--view` projection when you want a narrower convenience output for a common workflow
- use the preserved QC columns when filtering or auditing missing values
- derive narrower projections where appropriate instead of carrying all columns into every downstream step

## Practical downstream subset

For a station-year comparison workflow, a first pass often needs only:

- `STATION`
- `DATE`
- `temperature_c`
- `temperature_quality_code`
- `visibility_m`
- `TMP__qc_reason`

For example, two analyses can begin from the same canonical subset:

- a looser pass that keeps rows where `temperature_c` is present
- a stricter pass that also requires `temperature_quality_code == 1`

The downstream choice changes, but the interpretation layer stays shared and explicit.

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

That means downstream users can tell the difference between a sentinel-coded missing value and later quality-based exclusion logic. It also lets multiple projects begin from the same decoded interpretation instead of carrying slightly different local missingness rules forward.

## What this output is good for

This canonical representation is a better starting point when you want:

- consistent field handling across many stations
- a reusable, deterministic source representation for downstream analysis
- QC-aware filtering after cleaning rather than ad hoc preprocessing before it

When you only need one part of the observational record, start from a subset of relevant columns or from an existing `--view` projection. Narrower downstream tables can be derived from the canonical layer, but the defended public contribution is the canonical contract itself.

If you only need a quick notebook exploration of one file, this may be more structure than you need.
