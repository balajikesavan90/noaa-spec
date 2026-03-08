# Domain Dataset Registry

This document publishes researcher-facing domain dataset definitions from
`src/noaa_climate_data/domains/`.

All domain datasets are observation-level slices derived from canonical cleaned
observations and are joinable using shared identity keys:

- `station_id`
- `DATE`

## core_meteorology

- Join keys: `station_id`, `DATE`
- Output columns: `station_id`, `DATE`, `YEAR`, `LATITUDE`, `LONGITUDE`, `ELEVATION`, `REPORT_TYPE`, `CALL_SIGN`
- Quality rules: `station_id_required`, `date_required`, `location_fields_nullable_not_sentinel`

## wind

- Join keys: `station_id`, `DATE`
- Output columns: `station_id`, `DATE`, `wind_speed_ms`, `wind_direction_deg`, `wind_gust_ms`, `wind_type_code`, `WND__part4__qc_pass`
- Quality rules: `wind_qc_pass_preserved`, `wind_direction_domain_validated`, `wind_speed_no_sentinel`

## precipitation

- Join keys: `station_id`, `DATE`
- Output columns: `station_id`, `DATE`, `precip_amount_1`, `precip_period_hours_1`, `snow_accum_depth_cm_1`, `AA1__part2__qc_pass`
- Quality rules: `precip_qc_pass_preserved`, `precip_amount_no_sentinel`, `precip_period_hours_domain_validated`

## clouds_visibility

- Join keys: `station_id`, `DATE`
- Output columns: `station_id`, `DATE`, `visibility_m`, `ceiling_height_m`, `cloud_total_coverage`, `VIS__part1__qc_pass`, `CIG__part1__qc_pass`
- Quality rules: `visibility_qc_pass_preserved`, `ceiling_qc_pass_preserved`, `cloud_fraction_domain_validated`

## pressure_temperature

- Join keys: `station_id`, `DATE`
- Output columns: `station_id`, `DATE`, `temperature_c`, `dew_point_c`, `station_pressure_hpa`, `sea_level_pressure_hpa`, `altimeter_setting_hpa`, `TMP__qc_pass`, `SLP__qc_pass`
- Quality rules: `temperature_qc_pass_preserved`, `pressure_qc_pass_preserved`, `pressure_fields_no_sentinel`

## remarks

- Join keys: `station_id`, `DATE`
- Output columns: `station_id`, `DATE`, `remarks_text`
- Quality rules: `remarks_preserved_raw_semantics`, `remarks_nullable`

## Design Constraints

- Domain datasets are not aggregate products.
- Aggregated rollups (hourly/monthly/yearly summaries) are intentionally out of
  scope for domain dataset contracts.
- Downstream researchers compose domain joins and analysis on top of canonical
  and domain publication artifacts.
