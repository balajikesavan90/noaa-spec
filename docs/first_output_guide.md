# First Output Guide

Start with decoded measurement columns and their NOAA quality-code columns. Ignore `__qc_*` sidecars on the first pass unless a decoded value is empty or surprising.

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
