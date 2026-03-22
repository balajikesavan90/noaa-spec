# P3 — Expand Research Value

Checklist for P3 workstream to make the pipeline more useful for researchers.

---

## Research-focused deliverables

### 1) Data quality report (raw vs cleaned)
- [ ] Produce a per-station report comparing raw vs cleaned data.
- [ ] Include row counts (raw vs cleaned) and reasons for row drops.
- [ ] Include missingness summary (percent missing per column after cleaning).
- [ ] Include sentinel replacement counts per column.
- [ ] Include quality-flag filtering counts per column.
- [ ] Include list of fields with applied scale factors (and scale used).
- [ ] Include coverage completeness (percent of hours/days/months retained).
- [ ] Include notable data gaps (longest missing spans per field) if feasible.
- [ ] Output `LocationData_QualityReport.json`.
- [ ] Output `LocationData_QualityReport.md`.
- [ ] Output `LocationData_QualitySummary.csv`.

### 2) Aggregation assumptions report
- [ ] Document aggregation strategy (`best_hour`, `fixed_hour`, `hour_day_month_year`, `weighted_hours`, `daily_min_max_mean`).
- [ ] If `best_hour`, include chosen hour and day-coverage counts per hour.
- [ ] If `fixed_hour`, include chosen hour.
- [ ] Include completeness filters (min days/month, min months/year, filtered counts).
- [ ] Include aggregation function per column (mean/min/max/sum/circular_mean/drop).
- [ ] Include dropped columns (categorical codes and quality columns).
- [ ] Output `LocationData_AggregationReport.json`.
- [ ] Output `LocationData_AggregationReport.md`.

---

## Data additions

### Add precipitation fields (AA1–AA4)
- [ ] Parse AA groups when present in raw data.
- [ ] Apply scale 0.1 and missing value `9999`.
- [ ] Aggregate hourly precipitation by **sum** (monthly/yearly).

### Add snow depth (AJ1)
- [ ] Parse snow depth values (scale 1, missing `9999`).
- [ ] Keep snow depth numeric for aggregation by **mean** (or **max** if needed).

### Add precipitation estimate fields (AU1–AU5)
- [ ] Parse AU groups as categorical condition codes.
- [ ] Keep in cleaned output and **drop** from aggregation.

---

## Derived quantities

### Temperature and humidity
- [ ] Add relative humidity (%) via Magnus formula using TMP and DEW.
- [ ] Add wet-bulb temperature derived from TMP and RH.

### Heat stress and cold stress
- [ ] Add wind chill for TMP < 10 C and wind speed > 4.8 km/h.
- [ ] Add heat index for TMP > 27 C and RH > 40%.
- [ ] Ensure derived fields include unit suffixes (e.g., `relative_humidity_pct`, `wet_bulb_c`, `wind_chill_c`, `heat_index_c`).

---

## Multi-occurrence field handling

- [ ] GA1–GA6: derive total cloud cover and lowest base height.
- [ ] MW1–MW7: compute categorical count of unique codes per day or month.
- [ ] KA1–KA4: separate min vs max into distinct columns using part2 code (N=minimum, M=maximum).

---

## Output and documentation

- [ ] Add README section for derived fields and data quality report.
- [ ] Add a "Data Quality" section in each station output folder.

---

## Citation

- [ ] Add `CITATION.cff` at repo root.
- [ ] Embed station-level citation text in report outputs.
- [ ] Include version, run date, data access date, and station ID in reports.
- [ ] Include runtime citation template:

```
Author(s). (YYYY). noaa-climate-data (Version X.Y.Z). NOAA ISD Global Hourly data processed for station {STATION_ID}. Retrieved {ACCESS_DATE} from https://www.ncei.noaa.gov/products/land-based-station/integrated-surface-database
```

- [ ] If applicable, include DOI (Zenodo) and a "How to cite" README section.

---

## Acceptance criteria

- [ ] A researcher can see data quality changes, aggregation assumptions, and derived metrics in the station folder.
- [ ] Reports are deterministic and reproducible across runs.
- [ ] Derived fields include units in names or documentation.
