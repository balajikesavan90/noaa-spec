# First Output Guide

The full cleaned CSV is intentionally wide because NOAA-Spec preserves decoded
measurements, NOAA quality codes, validation sidecars, and row-level usability
signals. Start with decoded measurement columns and their NOAA quality-code
columns. Ignore `__qc_*` sidecars on the first pass unless a decoded value is
empty or surprising.

| Column | Meaning | Why it matters first |
| --- | --- | --- |
| `STATION` | NOAA station identifier | Row traceability back to the source observation. |
| `DATE` | Observation timestamp | Primary time key for downstream analysis. |
| `temperature_c` | Decoded air temperature in degrees C | Main example of signed tenths-degree NOAA decoding. |
| `temperature_quality_code` | NOAA quality code for `TMP` | Shows that QC survives sentinel/null cleaning. |
| `dew_point_c` | Decoded dew point in degrees C | Common paired meteorological measurement. |
| `visibility_m` | Decoded visibility distance in meters | Common sentinel case; `999999` becomes null. |
| `visibility_quality_code` | NOAA quality code for visibility distance | Explains visibility measurement state. |
| `wind_speed_ms` | Decoded wind speed in m/s | Common packed-field measurement from `WND`. |
| `wind_speed_quality_code` | NOAA quality code for wind speed | Keeps NOAA QC separate from the decoded value. |
| `sea_level_pressure_hpa` | Decoded sea-level pressure in hPa | Common pressure sentinel and scaling example. |

Empty cells in decoded measurement columns are expected when NOAA sentinels are normalized to null. If a decoded value is empty, then inspect the matching sidecar columns such as `TMP__qc_status`, `TMP__qc_reason`, `VIS__part1__qc_status`, or `SLP__qc_reason`.

## Compact First View

This excerpt is from the tracked primary expected output,
`reproducibility/minimal/station_cleaned_expected.csv`. It is not a separate
schema; it is the recommended first view before inspecting the full wide CSV.

| STATION | DATE | temperature_c | temperature_quality_code | visibility_m | visibility_quality_code | wind_speed_ms | wind_type_code | TMP__qc_reason | VIS__part1__qc_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 40435099999 | 2000-01-10T06:00:00 | 18.0 | 1 | 10000.0 | 1.0 | 0.0 | C |  |  |
| 40435099999 | 2000-03-17T09:00:00 |  | 9 |  | 9.0 |  |  | SENTINEL_MISSING | SENTINEL_MISSING |
| 40435099999 | 2000-03-20T14:00:00 |  | 9 | 9900.0 | 1.0 |  |  | SENTINEL_MISSING |  |

Read empty decoded measurements together with their quality-code and sidecar
columns. For example, the second row shows sentinel-coded temperature and
visibility normalized to null while preserving the source QC code and parser
reason.
