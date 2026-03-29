# Canonical Walkthrough

This walkthrough shows what NOAA-Spec adds beyond ad hoc row handling.

It is illustrative only. It uses a small slice from a local station output pair under `output/40435099999/` to explain the canonical contract. It is not part of the minimal reproducibility guarantee, which remains the tracked fixture in [../../REPRODUCIBILITY.md](../../REPRODUCIBILITY.md).

## Why this example

NOAA ISD rows encode multiple meanings inside compact tokens:

- numeric measurements
- sentinel-coded missing values
- field-specific quality codes
- repeated substructures such as cloud layers

NOAA-Spec turns that encoded row structure into a deterministic canonical representation with stable columns.

## Raw Slice

Representative raw rows:

```text
STATION,DATE,TMP,DEW,VIS,WND,SLP,GA1
40435099999,2000-01-10T06:00:00,"+0180,1","+0100,1","010000,1,N,1","999,9,C,0000,1","10165,1","00,1,+99999,9,99,9"
40435099999,2000-03-17T09:00:00,"+9999,9","+9999,9","999999,9,N,1","999,9,9,9999,9","99999,9",
40435099999,2000-04-01T00:00:00,"+0190,1","-0080,1","020000,1,N,1","999,9,9,9999,9","10114,1",
```

## Canonical Slice

Corresponding canonical fields:

```text
STATION,DATE,temperature_c,temperature_quality_code,TMP__qc_reason,dew_point_c,visibility_m,wind_direction_deg,wind_speed_ms,sea_level_pressure_hpa,cloud_layer_coverage_1,cloud_layer_base_height_m_1
40435099999,2000-01-10 06:00:00+00:00,18.0,1,,10.0,10000.0,,0.0,1016.5,0.0,
40435099999,2000-03-17 09:00:00+00:00,,9,SENTINEL_MISSING,,,,,,,
40435099999,2000-04-01 00:00:00+00:00,19.0,1,,-8.0,20000.0,,,1011.4,,
```

## What Changed and Why

1. `TMP=+0180,1` becomes `temperature_c=18.0` with `temperature_quality_code=1`.
2. `TMP=+9999,9` does not remain a misleading number. It becomes a null temperature with `temperature_quality_code=9` and `TMP__qc_reason=SENTINEL_MISSING`.
3. `VIS=010000,1,N,1` becomes `visibility_m=10000.0` while preserving the related quality semantics in stable sidecar columns.
4. `WND=999,9,C,0000,1` does not force a fake wind direction value into the canonical table. Calm and missing-direction semantics stay explicit rather than being hidden in project-local parsing.
5. `GA1=00,1,+99999,9,99,9` is split into stable cloud fields so encoded repeated structure can be reused across projects without rewriting token logic.

## What the User Gains

- one deterministic interpretation of sentinel-coded values instead of per-project judgment calls
- explicit preservation of NOAA QC meaning instead of dropping it during cleaning
- stable column names that downstream code can depend on
- a canonical, loss-preserving normalized representation that different projects can share as an intermediate contract

This is why the canonical output is wide. The width is intentional: NOAA ISD is structurally rich, and the canonical layer preserves reusable semantics that would otherwise remain buried inside compact row tokens.

Most users should not treat the full canonical table as their final analysis table. The usual pattern is:

- inspect a subset of relevant fields
- filter or stratify using the preserved QC columns when needed
- derive narrower task-specific tables from the canonical representation
