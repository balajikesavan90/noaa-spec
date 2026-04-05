# Canonical Walkthrough

This walkthrough shows the reviewer path explicitly:

1. raw encoded NOAA row
2. canonical normalized row
3. small practical subset for downstream analysis

It is illustrative only. It uses embedded raw and canonical snippets so the explanation does not depend on local `output/` artifacts. The reproducible reviewer path remains the tracked fixture in [../../REPRODUCIBILITY.md](../../REPRODUCIBILITY.md), and the public CLI can also write canonical-derived views directly with `--view`.

## Raw Snippet

```text
STATION,DATE,TMP,DEW,VIS,WND,SLP,GA1
40435099999,2000-01-10T06:00:00,"+0180,1","+0100,1","010000,1,N,1","999,9,C,0000,1","10165,1","00,1,+99999,9,99,9"
40435099999,2000-03-17T09:00:00,"+9999,9","+9999,9","999999,9,N,1","999,9,9,9999,9","99999,9",
```

## Canonical Snippet

```text
STATION,DATE,temperature_c,temperature_quality_code,TMP__qc_reason,dew_point_c,visibility_m,wind_direction_deg,wind_speed_ms,sea_level_pressure_hpa,cloud_layer_coverage_1,cloud_layer_base_height_m_1
40435099999,2000-01-10T06:00:00,18.0,1,,10.0,10000.0,,0.0,1016.5,0.0,
40435099999,2000-03-17T09:00:00,,9,SENTINEL_MISSING,,,,
```

## Practical Subset

The full canonical row is intentionally wider than this snippet. A reviewer can usually start with a small subset:

```text
STATION,DATE,temperature_c,temperature_quality_code,visibility_m,TMP__qc_reason
40435099999,2000-01-10T06:00:00,18.0,1,10000.0,
40435099999,2000-03-17T09:00:00,,9,,SENTINEL_MISSING
```

For a station-year comparison or QC-aware filtering workflow, this subset is often enough to decide whether to:

- keep all non-null `temperature_c` rows, or
- require a stricter quality condition before aggregation.

## Reuse Difference

Two downstream users can reuse the same canonical subset with different quality policies without reimplementing sentinel decoding or field renaming. See [../UNDERSTANDING_OUTPUT.md](../UNDERSTANDING_OUTPUT.md) for a worked example of divergent downstream filtering.

## What Changed

1. `TMP=+0180,1` becomes `temperature_c=18.0` with `temperature_quality_code=1`.
2. `TMP=+9999,9` becomes a null cleaned value instead of a fake extreme number, while preserving `temperature_quality_code=9` and `TMP__qc_reason=SENTINEL_MISSING`.
3. `VIS=010000,1,N,1` becomes `visibility_m=10000.0` in a normalized numeric column.
4. `WND=999,9,C,0000,1` keeps calm or missing-direction semantics explicit instead of forcing a misleading direction value.
5. `GA1=00,1,+99999,9,99,9` is split into stable cloud fields so repeated encoded structure becomes reusable columns.

## Why This Matters

- raw encoded tokens become stable named columns before downstream analysis begins
- sentinel handling becomes deterministic instead of project-local
- NOAA QC semantics stay visible instead of being dropped during cleaning
- users can inspect a small subset first, then expand to the full canonical row only when needed
