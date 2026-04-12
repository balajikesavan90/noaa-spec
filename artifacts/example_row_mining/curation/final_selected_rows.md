# NOAA-Spec — Final Curated Reviewer Fixture Candidates

**15 rows selected from the mined corpus across 6 distinct stations.**

Each row is traceable to its source file and line number. The `datetime` field is the full ISO-8601 observation timestamp from the NOAA ISD `DATE` column and together with `station_id` forms a stable unique row identifier.

Field encoding uses NOAA ISD composite tokens: values are scaled integers with appended quality codes (e.g. `+0280,1` = +28.0°C, QC=1).

---

## Group 1 — Temperature Sentinel (`tmp_missing_sentinel`)

### R04  ·  Station `72547299999`

| Field | Value |
|-------|-------|
| Pattern(s) | `tmp_missing_sentinel | mixed_validity` |
| Station | `72547299999` |
| Source file | `LocationData_Raw.parquet` |
| Line number | 344 |
| Datetime (UTC) | `1997-02-25T04:53:00` |
| TMP (raw) | `+9999,9` |
| VIS (raw) | `016093,1,N,1` |
| WND (raw) | `170,1,N,0021,1` |
| AA1 (raw) | `(absent)` |
| Score | 10 |

**Why selected:** TMP=+9999,9: the canonical temperature missing sentinel. Naive parsing yields +999.9°C — unphysical. VIS=016093 (16.1 km, valid) and WND=170,1,N,0021,1 (valid) in the same row. Clean mixed-validity example: NOAA-Spec nullifies TMP, preserves the rest.

---

## Group 2 — Visibility Sentinel and/or Fully-Missing Rows (`vis_missing_sentinel`, `wnd_fully_missing`)

### R01  ·  Station `63250099999`

| Field | Value |
|-------|-------|
| Pattern(s) | `vis_missing_sentinel | mixed_validity` |
| Station | `63250099999` |
| Source file | `LocationData_Raw.parquet` |
| Line number | 58 |
| Datetime (UTC) | `1978-08-18T06:00:00` |
| TMP (raw) | `+0280,1` |
| VIS (raw) | `999999,9,N,9` |
| WND (raw) | `160,1,N,0041,1` |
| AA1 (raw) | `(absent)` |
| Score | 10 |

**Why selected:** VIS=999999 (missing sentinel) while TMP and WND are valid. Naive parsing yields 999999 m (≈622 miles) visibility — an obvious absurdity. NOAA-Spec nullifies VIS while preserving valid TMP=+28.0°C and WND.

### R05  ·  Station `72547299999`

| Field | Value |
|-------|-------|
| Pattern(s) | `vis_missing_sentinel | wnd_fully_missing | aa1_valid_precip` |
| Station | `72547299999` |
| Source file | `LocationData_Raw.parquet` |
| Line number | 9451 |
| Datetime (UTC) | `1998-04-22T17:53:00` |
| TMP (raw) | `+0180,1` |
| VIS (raw) | `999999,9,N,9` |
| WND (raw) | `999,9,9,9999,9` |
| AA1 (raw) | `06,0000,9,1` |
| Score | 10 |

**Why selected:** Three-pattern row. VIS=999999 sentinel AND WND=999,9,9,9999,9 (direction, type, speed all missing/sentinel) while AA1=06,0000,9,1 is a valid precipitation record. NOAA-Spec must nullify two field families while correctly preserving AA1.

### R07  ·  Station `72214904899`

| Field | Value |
|-------|-------|
| Pattern(s) | `vis_missing_sentinel` |
| Station | `72214904899` |
| Source file | `LocationData_Raw.parquet` |
| Line number | 90 |
| Datetime (UTC) | `2006-01-02T05:59:00` |
| TMP (raw) | `+9999,9` |
| VIS (raw) | `999999,9,9,9` |
| WND (raw) | `999,9,9,9999,9` |
| AA1 (raw) | `(absent)` |
| Score | 8 |

**Why selected:** Fully degenerate row: TMP=+9999,9, VIS=999999,9,9,9, WND=999,9,9,9999,9 — all three core families are sentineled. Modern data (2006). Demonstrates that entire rows can be present in the dataset but carry no usable observations.

---

## Group 3 — Calm Wind Encoding (`wnd_missing_dir_valid_spd` — type=C)

### R06  ·  Station `72547299999`

| Field | Value |
|-------|-------|
| Pattern(s) | `wnd_missing_dir_valid_spd` |
| Station | `72547299999` |
| Source file | `LocationData_Raw.parquet` |
| Line number | 9 |
| Datetime (UTC) | `1997-02-01T11:40:00` |
| TMP (raw) | `+0000,1` |
| VIS (raw) | `000805,1,N,1` |
| WND (raw) | `999,1,C,0000,1` |
| AA1 (raw) | `06,0000,9,1` |
| Score | 9 |

**Why selected:** Calm wind encoding: WND=999,1,C,0000,1. Direction=999 but type_code=C (Calm) — NOT a missing observation. Speed=0.0 m/s, QC=1. TMP=+0.0°C, VIS=000805 m (heavy fog, 805 m). AA1=06,0000,9,1 valid. Demonstrates why type_code must be read, not just the direction field.

---

## Group 4 — Multi-Family Encoding Nuance (`multi_family_informative`)

### R03  ·  Station `63250099999`

| Field | Value |
|-------|-------|
| Pattern(s) | `multi_family_informative` |
| Station | `63250099999` |
| Source file | `LocationData_Raw.parquet` |
| Line number | 163 |
| Datetime (UTC) | `1978-11-02T15:00:00` |
| TMP (raw) | `+0260,1` |
| VIS (raw) | `020000,1,N,9` |
| WND (raw) | `999,1,V,0031,1` |
| AA1 (raw) | `99,0010,9,1` |
| Score | 8 |

**Why selected:** WND type_code=V (variable wind direction): direction field is 999 but semantically 'variable', not missing — requires type_code-aware parsing. Speed=3.1 m/s is valid. AA1=99,0010,9,1 contains a small non-zero traceable precip amount (1.0 mm) with a sentinel period (99 = unknown). Four families coexist with nuanced partial-sentinel state.

---

## Group 5 — Precipitation Family Sentinel (`aa1_missing_sentinel`)

### R08  ·  Station `72214904899`

| Field | Value |
|-------|-------|
| Pattern(s) | `aa1_missing_sentinel` |
| Station | `72214904899` |
| Source file | `LocationData_Raw.parquet` |
| Line number | 204397 |
| Datetime (UTC) | `2014-02-21T11:55:00` |
| TMP (raw) | `-0015,5` |
| VIS (raw) | `011265,5,N,5` |
| WND (raw) | `260,5,N,0139,5` |
| AA1 (raw) | `24,9999,1,9` |
| Score | 7 |

**Why selected:** QC=5 throughout (estimated values). TMP=-0.15°C (negative, valid). WND=260°, 13.9 m/s (strong wind, valid). AA1=24,9999,1,9: 24-hour accumulation window present but amount is sentinel. Shows partial AA1 nullification required — not whole-row drop.

### R09  ·  Station `72214904899`

| Field | Value |
|-------|-------|
| Pattern(s) | `aa1_missing_sentinel` |
| Station | `72214904899` |
| Source file | `LocationData_Raw.parquet` |
| Line number | 188987 |
| Datetime (UTC) | `2013-07-17T11:55:00` |
| TMP (raw) | `+0240,5` |
| VIS (raw) | `011265,5,N,5` |
| WND (raw) | `999,9,C,0000,5` |
| AA1 (raw) | `24,9999,1,9` |
| Score | 6 |

**Why selected:** QC=5 (estimated) with calm wind encoded as WND=999,9,C,0000,5. AA1=24,9999,1,9: 24-hour period present, amount sentinel. Third distinct station confirming aa1 amount-sentinel pattern with QC variation.

### R10  ·  Station `46737399999`

| Field | Value |
|-------|-------|
| Pattern(s) | `aa1_missing_sentinel` |
| Station | `46737399999` |
| Source file | `LocationData_Raw.parquet` |
| Line number | 536 |
| Datetime (UTC) | `1988-02-14T09:00:00` |
| TMP (raw) | `+0160,1` |
| VIS (raw) | `006000,1,N,1` |
| WND (raw) | `040,1,N,0098,1` |
| AA1 (raw) | `99,9999,2,9` |
| Score | 7 |

**Why selected:** All core fields valid (TMP=+16.0°C, VIS=6 km, WND=040° at 9.8 m/s, QC=1). AA1=99,9999,2,9: BOTH period (99) and amount (9999) are sentinels — precipitation family completely unobserved despite a valid meteorological row.

### R11  ·  Station `72344154921`

| Field | Value |
|-------|-------|
| Pattern(s) | `aa1_missing_sentinel` |
| Station | `72344154921` |
| Source file | `LocationData_Raw.parquet` |
| Line number | 195108 |
| Datetime (UTC) | `2013-06-05T11:55:00` |
| TMP (raw) | `+0111,5` |
| VIS (raw) | `016093,5,N,5` |
| WND (raw) | `330,5,N,0026,5` |
| AA1 (raw) | `24,9999,1,9` |
| Score | 6 |

**Why selected:** QC=5 throughout (estimated). TMP=+11.1°C, WND=330° at 2.6 m/s. AA1=24,9999,1,9: 24-hour accumulation window but amount sentinel. Fifth unique station confirming estimated-QC records still require AA1 amount nullification.

### R12  ·  Station `72344154921`

| Field | Value |
|-------|-------|
| Pattern(s) | `aa1_missing_sentinel` |
| Station | `72344154921` |
| Source file | `LocationData_Raw.parquet` |
| Line number | 225375 |
| Datetime (UTC) | `2014-07-31T11:55:00` |
| TMP (raw) | `+0161,5` |
| VIS (raw) | `016093,5,N,5` |
| WND (raw) | `999,9,C,0000,5` |
| AA1 (raw) | `24,9999,1,9` |
| Score | 5 |

**Why selected:** QC=5, calm wind (WND=999,9,C,0000,5). AA1=24,9999,1,9. Estimated-QC + calm-wind + AA1-sentinel combination from a fifth station.

### R13  ·  Station `55696099999`

| Field | Value |
|-------|-------|
| Pattern(s) | `aa1_missing_sentinel` |
| Station | `55696099999` |
| Source file | `LocationData_Raw.parquet` |
| Line number | 3 |
| Datetime (UTC) | `1975-01-01T06:00:00` |
| TMP (raw) | `-0010,1` |
| VIS (raw) | `020000,1,N,9` |
| WND (raw) | `200,1,N,0020,1` |
| AA1 (raw) | `06,9999,2,9` |
| Score | 8 |

**Why selected:** Earliest date in corpus sample (1975-01-01T03:00:00). TMP=-0.10°C (negative, near-freezing). WND=200° at 2.0 m/s (valid). AA1=06,9999,2,9: 6-hour window, amount sentinel. Historical data confirming sentinel conventions consistent across decades.

### R14  ·  Station `55696099999`

| Field | Value |
|-------|-------|
| Pattern(s) | `aa1_missing_sentinel` |
| Station | `55696099999` |
| Source file | `LocationData_Raw.parquet` |
| Line number | 32 |
| Datetime (UTC) | `1975-01-07T06:00:00` |
| TMP (raw) | `-0030,1` |
| VIS (raw) | `020000,1,N,9` |
| WND (raw) | `999,1,C,0000,1` |
| AA1 (raw) | `06,9999,2,9` |
| Score | 6 |

**Why selected:** Calm wind (WND=999,1,C,0000,1) paired with AA1 amount sentinel. TMP=-0.30°C (near-freezing). Shows calm-wind encoding in an early-record context.

### R15  ·  Station `55696099999`

| Field | Value |
|-------|-------|
| Pattern(s) | `aa1_missing_sentinel` |
| Station | `55696099999` |
| Source file | `LocationData_Raw.parquet` |
| Line number | 35 |
| Datetime (UTC) | `1975-01-08T00:00:00` |
| TMP (raw) | `-0110,1` |
| VIS (raw) | `020000,1,N,9` |
| WND (raw) | `999,1,C,0000,1` |
| AA1 (raw) | `06,9999,2,9` |
| Score | 7 |

**Why selected:** TMP=-1.10°C — coldest temperature in the selected fixture. Calm wind (WND=999,1,C,0000,1). AA1=06,9999,2,9. Provides temperature range contrast illustrating that sentinel cleaning is independent of meteorological conditions.

---

## Group 6 — Valid Precipitation Record (`aa1_valid_precip`, `multi_family_informative`)

### R02  ·  Station `63250099999`

| Field | Value |
|-------|-------|
| Pattern(s) | `aa1_valid_precip | multi_family_informative` |
| Station | `63250099999` |
| Source file | `LocationData_Raw.parquet` |
| Line number | 1987 |
| Datetime (UTC) | `1982-02-11T09:00:00` |
| TMP (raw) | `+0346,1` |
| VIS (raw) | `001800,1,N,9` |
| WND (raw) | `070,1,N,0050,1` |
| AA1 (raw) | `06,0000,9,1` |
| Score | 9 |

**Why selected:** All four field families populated (TMP, VIS, WND, AA1). AA1=06,0000,9,1: valid 6-hour accumulation window with confirmed zero precipitation (QC=1). Demonstrates that AA1 amount=0000 is a real, clean zero — not a sentinel.

---
