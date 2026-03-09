# Next steps: ISD alignment checklist

## Status split (why open items still exist)

### Spec-rule compliance (complete)

- `SPEC_COVERAGE_REPORT.md` currently reports **100% implemented** and **100% strict-tested** coverage for extracted ISD rule types (`range`, `sentinel`, `allowed_quality`, `domain`, `cardinality`, `width`, `arity`).
- Treat that report as the completion gate for **rule-level spec coverage**.

### Post-spec semantic/architecture work (still open)

- Remaining unchecked items below are primarily **semantic fidelity**, **pipeline behavior**, and **regression hardening** tasks that are intentionally broader than the spec-coverage KPI.
- Architecture/productization backlog is tracked separately in `ARCHITECTURE_NEXT_STEPS.md`.

## Production readiness findings (contract_check_20260308T104353-0700, 2026-03-08)

### Latest run snapshot

- [x] Contract-check execution stability improved: latest run completed `11/11` stations (`contract_check_20260308T104353-0700`) versus `7 completed / 4 failed` in the earlier run (`contract_check_20260308T014542-0800`).
- [x] Station-level expected outputs were present for all completed rows in `run_status.csv`.

### P0 blockers before production publication

- [x] Fix `field_completeness` semantics so `field_completeness_ratio` is never negative; current aggregation mixes identifier-level null counts across multiple parts and produces invalid ratios.
- [x] Add regression tests that enforce `0.0 <= field_completeness_ratio <= 1.0` for all rows in `field_completeness.csv`.
- [x] Fix release/build metadata timestamp semantics for non-`YYYYMMDDTHHMMSSZ` run IDs; `build_timestamp` and `creation_timestamp` must be real timestamps, not run-id strings.
- [ ] Add validation/tests for timestamp format in `build_metadata.json` and `release_manifest.csv`.
- [ ] Resolve release-manifest scope gap: include all produced publishable artifacts (station-level reports, station split manifests, success markers), or explicitly define and implement a dual-manifest model (publication manifest + full file manifest).
- [ ] Add CI coverage asserting manifest completeness against produced artifact sets for the configured write flags.
- [ ] Decide and document checksum policy for publication artifacts (content hash vs path+content bundle hash), then enforce it consistently in docs and CI.
- [ ] Adjust domain usability logic for text-first domains (e.g., `remarks`) so they are not incorrectly reported as `0` usable rows purely due numeric-only metric detection.

### P1 hardening follow-up

- [ ] Add an end-to-end contract-check CI scenario that uses a prefixed run ID (e.g., `contract_check_*`) to prevent timestamp and metadata regressions that are currently missed by `YYYYMMDDTHHMMSSZ`-only test IDs.
- [ ] Add a publication-readiness gate report combining: run completion, artifact-manifest coverage, timestamp validity, checksum policy conformance, and quality-artifact sanity checks.
- [ ] Add a reproducibility rerun gate that executes the same input/configuration twice and asserts identical artifact checksums (excluding explicitly time-variant metadata fields).
- [ ] Add run recovery/idempotency coverage: simulate interruption, rerun with the same run ID, and assert no duplicate/partial artifacts plus correct `run_status` transitions.
- [ ] Formalize and test `run_manifest` versus `run_status` semantics (discovery snapshot vs execution truth), including explicit docs and CI assertions.
- [ ] Define publication quality thresholds (for example maximum exclusion rates and minimum domain usability by domain) and enforce them as go/no-go gates.
- [ ] Add artifact write-atomicity checks (temporary write + atomic rename) and CI validation that interrupted runs cannot leave publishable partial files.
- [ ] Add schema compatibility checks against the previous release manifest and fail CI on contract-breaking changes unless a schema version bump is explicit.

## P0: Spec-rule implementation vs official ISD docs

- [x] Enforce per-field allowed-quality sets for 2-part value/quality fields (e.g., GJ/GK/GL/MV/MW) instead of the generic `QUALITY_FLAGS` gate.
- [x] Apply field-specific sentinel detection (including leading-zero normalization) for 2-part value/quality fields to match ISD/README rules.
- [x] Respect signed missing sentinels where spec uses +9999/+99999 only; current normalization strips signs and can drop valid negative extremes (e.g., CRN temps).
- [x] Allow valid negative all-9 minima (e.g., -999, -9999, -99999) where spec defines negative ranges and missing uses +9999/+99999; current `_to_float` treats any all-9s as missing.
- [x] Align 2-part field naming with ISD semantics and friendly maps: `clean_value_quality` always emits `__value`, which conflicts with `__part1` expectations for MV/GJ/GK/GL and bypasses their per-part metadata.
- [x] Apply GE1 convective cloud missing sentinel (`9`) from Part 15 in `FIELD_RULES`/cleaning.
- [x] Apply GE1 vertical datum missing sentinel (`999999`) from Part 15 in `FIELD_RULES`/cleaning.
- [x] Enforce GE1 convective cloud code domain (0-7, 9) per Part 15.
- [x] Enforce GE1 vertical datum code domain (AGL/ALAT/.../WGS84G; 999999 missing) per Part 15.
- [x] Restrict GF1 quality parts to Part 15 cloud quality codes (currently defaults to `QUALITY_FLAGS`).
- [x] Apply GA cloud-layer type missing sentinel (`99`) from Part 15.
- [x] Apply GF1 low/mid/high cloud genus missing sentinels (`99`) from Part 15.
- [x] Apply AJ snow-depth condition missing sentinels (`9`) for depth/equivalent water codes.
- [x] Apply UA1 wave-measurement missing sentinels (method `9`, sea state `99`) from Part 30.
- [x] Restrict AU present-weather quality codes to Part 5 values (0-7, 9, M) and apply missing sentinels to AU parts (9/99 per field).
- [x] Restrict AY past-weather quality codes to Part 5 values (0-3, 9).
- [x] Restrict OC1 wind-gust quality codes to Part 29 values (0-7, 9, M).
- [x] Apply AU present-weather missing sentinels for descriptor/obscuration/other/combination codes (`9`) and precipitation code (`99`).
- [x] Enforce AY manual past-weather condition code domain (0-9) and period quantity range (01-24; 99 missing) per Part 5.
- [x] Restrict AA/AJ quality codes to Part 4 precipitation/snow sets (drop unsupported `C`).
- [x] Apply Part 29 calm-condition rule for OD: direction `999` with speed `0000` indicates calm wind.
- [x] Add Part 5 past-weather groups AX1-AX6 (summary-of-day) and AZ1-AZ2 (automated past weather).
- [x] Restrict OA/OD supplementary wind type codes to Part 29 values (1-6; `9` missing).
- [x] Enforce OA/OD period quantity ranges (01-48 hours; 99 missing) and OD direction range (001-360; 999 missing) per Part 29.
- [x] Enforce OA supplementary wind speed range (0000-2000; 9999 missing) per Part 29.
- [x] Enforce OB1/OB2 wind section ranges (period 001-998; max gust 0000-9998; direction 001-360; std 00000-99998; 999/9999/99999 missing) per Part 29.
- [x] Ensure OA/OD/OB/OE/RH identifiers with numeric suffixes (OA1-OA3, OD1-OD3, OB1-OB2, OE1-OE3, RH1-RH3) map to field rules.
- [x] Enforce OE1-OE3 summary-of-day constraints from Part 29 (period fixed at `24`; speed range `00000-20000`; occurrence time `0000-2359`; calm rule remains `direction=999` with `speed=00000`).
- [x] Restrict MA1 station pressure quality codes to Part 27 values (exclude unsupported `C`).
- [x] Tighten MA1 station pressure quality codes to {0-7, 9, M} (currently allows A/I/P/R/U via `QUALITY_FLAGS`).
- [x] Restrict MA1 altimeter quality codes to Part 27 values (0-7, 9, M) instead of default `QUALITY_FLAGS`.
- [x] Restrict MD1 quality codes to Part 27 values (0-3, 9 only).
- [x] Enforce MD1 pressure tendency code domain (0-8; 9 missing) per Part 27.
- [x] Restrict SA1 sea-surface temperature quality codes to Part 29 values (0-3, 9 only).
- [x] Enforce UA1 method code domain (M/I) and sea-state code domain (00-09) from Part 30.
- [x] Enforce UA1 wave period range (00-30 sec; 99 missing) and wave height range (000-500; 999 missing) per Part 30.
- [x] Enforce UG1/UG2 swell period range (00-14 sec; 99 missing), height range (000-500; 999 missing), and direction range (001-360; 999 missing) per Part 30.
- [x] Enforce WA1 platform-ice source/tendency code domains (source 1-5; tendency 0-4) from Part 30.
- [x] Enforce WD1/WG1 water-surface ice domain codes (edge bearing, non-uniform code, ship position/penetrability, ice trend/development, growler presence, etc.) per Part 30.
- [x] Enforce WD1/WG1 numeric ranges (concentration 000-100; growler/iceberg quantity 000-998; WG1 edge distance 00-98) per Part 30.
- [x] Enforce WJ1 water-level ice domain codes (primary/secondary ice phenomena, slush condition, water level state) per Part 30.
- [x] Enforce WA1 platform-ice thickness range (000-998; 999 missing) per Part 30.
- [x] Enforce WJ1 numeric ranges (ice thickness 000-998; discharge 00000-99998; stage height -999 to +9998) per Part 30.
- [x] Validate Control Data Section code domains (data source flag, report type code, QC process V01/V02/V03) and missing sentinels for lat/lon/elev/call letters.
- [x] Remove or explicitly document QC-process truncation behavior (e.g., `V020` -> `V02`) so non-spec lengths do not silently coerce.
- [x] Validate Control Data Section DATE/TIME domains (YYYYMMDD/HHMM ranges) per Part 2.
- [x] Restrict control DATE parsing to `YYYYMMDD` only (reject ISO timestamps and other formats).
- [x] Validate Mandatory Data Section domain codes and sentinels (wind type codes, CAVOK, ceiling determination, visibility variability, special missing rules like variable wind direction).
- [x] Restrict Mandatory Data Section quality codes for WND/CIG/VIS to {0-7, 9} (currently accepts extended `QUALITY_FLAGS`).
- [x] Encode Mandatory Data Section edge rules (ceiling unlimited=22000, visibility >160000 clamp, wind type 9 with speed 0000 indicates calm).
- [x] Fill in remaining Mandatory Data Section fields from master spec (dew point + quality, sea level pressure + quality, and any trailing mandatory positions missing in part-03 file).
- [x] Enforce IA1 ground-surface observation code domain (00-31; 99 missing) from Part 23.
- [x] Enforce KA extreme-air-temperature code domain (N/M/O/P) and tighten KA temperature quality codes to {0-7, 9, M} per Part 24.
- [x] Enforce MV present-weather-in-vicinity codes (00-09; 99 missing) and MW manual present-weather codes per Part 28.
- [x] Ensure MV/MW/AY identifiers with numeric suffixes (MV1-MV7, MW1-MW7, AY1-AY2) map to field rules.
- [x] Enforce AU present-weather component code domains (intensity/descriptor/precip/obscuration/other/combination) per Part 5.
- [x] Enforce AW automated present-weather code domain (00-99; 99 missing) and quality code set (0-7, 9, M) per Part 5.
- [x] Tighten AW automated present-weather code validation to the explicit Part 5 code list (not all `00-98` values).
- [x] Enforce CO1 climate division number domain (00-09; 99 missing) per Part 7.
- [x] Enforce CO1 UTC-LST offset range (-12 to +12; +99 missing) per Part 7.
- [x] Enforce CO2-CO9 element time-offset ranges (-9999 to +9998; +9999 missing) and element-id domain per Part 7.
- [x] Ensure network metadata identifiers with numeric suffixes are matched (CO2-CO9, CT1-CT3, CU1-CU3, CV1-CV3, CW1, CX1-CX3).
- [x] Enforce CV1-CV3 hourly temperature extreme time fields (HHMM 0000-2359; 9999 missing) per Part 11.
- [x] Enforce ED1 runway direction range (01-36 tens of degrees; 99 missing) and visibility range (0000-5000; 9999 missing) per Part 14.
- [x] Enforce ME1 geopotential level codes (1-5; 9 missing) per Part 27.
- [x] Enforce fixed-width/format constraints for additional-data numerics (e.g., AA* width and max `9998`) where NOAA specifies explicit field widths.
- [x] Enforce AP1-AP4 HPD gauge condition code as fixed missing (`9` only) per Part 4 ("not used at this time").
- [x] Enforce CRN period quantity ranges (e.g., CB/CH/CF/CG) and sensor value ranges per Part 6.
- [x] Enforce CRN QC/FLAG domains for CB/CF/CG/CH/CI/CN/CR/CT/CU/CV/CW/CX (QC in {1,3,9}; FLAG in 0-9) per Parts 6-8.
- [x] Enforce GM solar irradiance data flag domains (00-99, with 99 missing) for global/direct/diffuse/UVB flags per Part 17.
- [x] Align GM1 field layout with Part 17: UVB global irradiance has no data flag (only value + quality), so parsing should not expect a UVB data-flag part.
- [x] Enforce GH1 solar radiation flag domains (0-9, with 9 missing) per Part 15.
- [x] Ensure solar/sunshine identifiers with numeric suffixes are matched by parsing rules (GH1, GJ1, GK1, GL1, GM1, GN1, GO1) so scaling/quality/sentinels apply.
- [x] Enforce GP1 modeled solar irradiance source flag domains (01-03, 99 missing) per Part 19.
- [x] Enforce GP1 modeled solar irradiance time-period min/max (0001-9998) and uncertainty ranges (000-100; 999 missing) per Part 19.
- [x] Enforce GJ/GK/GL sunshine value ranges (duration/percent/month totals) per Part 16.
- [x] Enforce HAIL size range (000-200; 999 missing) per Part 22.
- [x] Enforce SA1 sea-surface temperature range (-050 to +450; +999 missing) per Part 25.
- [x] Enforce GM/GN/GO solar time-period min/max ranges (0001-9998) per Parts 17–18.
- [x] Enforce GQ1/GR1 quality codes and time-period min/max ranges (0001-9998; quality 0-3, 9) per Parts 20–21.
- [x] Enforce Part 15 cloud code domains for GA/GD/GG/GF1 coverage, summation, and cloud-type characteristics.
- [x] Align EQD parameter-code validation by identifier family: Q/P/R/C/D should accept Part 30 legacy parameter-code domains (e.g., `APC3`, `PRSWA1`, `A01xxx` patterns), while N-codes use the element+Flag1+Flag2 schema.
- [x] Treat AW automated-weather code `99` as a valid tornado code (Part 5) instead of a missing sentinel.
- [x] Fix GM1 UVB friendly-column mapping drift: parser emits UVB value + quality (no UVB data-flag part), but friendly maps still label part12 as `uvb_global_irradiance_flag_*` and expect a non-existent part13 quality column.
- [x] Parse QNN original-observation blocks to the Part 30 tokenized format (`QNN@1234...` plus 6-char data values), including repeated element blocks and strict token-width validation.
- [x] Enforce exact repeated-identifier bounds from spec (Parts 7/29/30) instead of broad prefix matching: reject out-of-domain IDs such as `CO10`, `OA4`/`OD4`/`OE4`/`RH4`, and `Q00`/`P00`/`R00`/`C00`/`D00`/`N00`.
- [x] Enforce Part 15 cloud-height numeric ranges for GA/GD/GG/GE1/GF1 (currently sentinel handling exists, but documented MIN/MAX bounds are not applied).
- [x] Enforce Part 15 `GH1` solar-radiation value ranges (`0000/00000-99998`, `99999` missing) for average/min/max/std components.
- [x] Enforce Part 17-18 `GM/GN/GO` numeric component ranges beyond time-period checks (irradiance values, GN zenith angle, GO net-radiation min/max).
- [x] Enforce Part 27 pressure numeric MIN/MAX ranges for MA1/MD1/MF1/MG1/MH1/MK1 values (currently mostly sentinel + quality gating only).
- [x] Validate Part 27 `MK1` max/min sea-level-pressure occurrence timestamps as DDHHMM in `010000-312359` (with `999999` missing) instead of accepting arbitrary 6-char tokens.
- [x] Enforce Part 24 numeric/day ranges for KA/KB/KC/KD/KF/KG, including KC date-token validation (`01-31` per token) and documented period/value min/max bounds.
- [x] Enforce Part 23 numeric MIN/MAX ranges for IA2/IB1/IB2/IC1 fields (period/temperature/std-dev/wind-movement/evaporation/pan-water temperatures), not just sentinel and quality gating.
- [x] Enforce Part 26 `ST1` numeric MIN/MAX ranges for soil temperature (`-1100..+0630`) and temperature depth (`0000..9998`) in addition to sentinel/quality checks.
- [x] Enforce Part 20/21 value bounds for `GQ1`/`GR1`: mean zenith/azimuth angles `0000..3600` and extraterrestrial radiation fields `0000..9998` (beyond existing time-period checks).
- [x] Enforce Part 24 `KE1` day-count field ranges (`00..31`, `99` missing) for all four threshold-count parts.
- [x] Tighten Part 29 `OE1-OE3` occurrence-time validation to true HHMM semantics (reject invalid minute values like `0060`/`1261`, not just values above `2359`).
- [x] Enforce Part 29 `OC1` wind-gust numeric range (`0050..1100`, `9999` missing) in addition to existing quality gating.
- [x] Enforce Part 29 `RH1-RH3` period/humidity numeric ranges (period `001..744`, humidity `000..100`, with `999` missing sentinels).
- [x] Enforce Part 4 `AH1-AH6` and `AI1-AI6` numeric/date-time ranges (period, depth, and ending DDHHMM occurrence in `010000..312359`).
- [x] Enforce remaining Part 4 precipitation/snow bounds outside `AH/AI`: `AB1` monthly total max (`50000`), `AD1` amount/date ranges (`00000..20000`, `0101..3131` tokens), `AE1` day-count ranges (`00..31`), `AJ1` depth/equivalent-water maxima (`1200`/`120000`), `AK1` depth/date ranges (`0000..1500`, day tokens `01..31`), `AL1-AL4` period/depth ranges (`00..72`, `000..500`), `AM1` amount/date ranges (`0000..2000`, `0101..3131`), and `AN1` period range (`001..744`).
- [x] Enforce remaining Part 6 CRN numeric ranges for `CI1` and `CN1-CN4` diagnostics (temperature, humidity/std-dev, voltages, resistor/signature, minutes-open, and wattage bounds).
- [x] Enforce Parts 9/10/11/13 numeric bounds for `CT*`/`CU*`/`CV*`/`CX*` value components (temperature/standard deviation/precipitation/frequency limits), not only quality and sentinel checks.
- [x] Extend exact repeated-identifier bound enforcement beyond Parts 7/29/30 to other fixed-cardinality families (e.g., `AH/AI/AL/AO`, `AT/AU/AW/AX/AZ`, `GA/GD/GG`, `MV/MW`).
- [x] Enforce exact identifier token format (field-length + suffix shape) for already-gated Part 7/29/30 and EQD families: reject malformed IDs that currently pass via prefix fallback (e.g., `CO02`, `OA01`, `RH0001`, `Q100`, `Q01A`, `N001`). **(A2)** Enhanced `is_valid_eqd_identifier()` and `is_valid_repeated_identifier()` in [constants.py](src/noaa_climate_data/constants.py) to reject wrong-length suffixes; added `is_valid_identifier()` combining function. Validation logs `[PARSE_STRICT]` warnings in [cleaning.py](src/noaa_climate_data/cleaning.py). Tests in [test_cleaning.py::TestA2MalformedIdentifierFormat](tests/test_cleaning.py).

### P0 open items: post-spec semantic fidelity / pipeline behavior

- These are intentionally kept open because they target parser/pipeline semantics and data-fidelity edge cases that are not fully represented by the spec-coverage KPI rows.

- [x] Disambiguate Part 4 `AH*` vs `AI*` friendly-column naming: generated outputs now use distinct `precip_5_to_45_min_*` and `precip_60_to_180_min_*` aliases, while legacy ambiguous `precip_short_duration_*` reverse aliases remain mapped to `AH*` for compatibility.
- [x] Fix `REM` parsing order so comma-bearing remark text does not get consumed by generic comma expansion before typed REM parsing (especially when `keep_raw=False`). **REM priority parsing implemented:** [cleaning.py](src/noaa_climate_data/cleaning.py) now processes REM column before generic expansion loop (lines 531-546).
- [x] Rework Part 30 `QNN` parsing to preserve raw ASCII payload semantics, allow non-alphanumeric printable source/flag tokens, and avoid greedy tokenization that can misread data values beginning with `A`-`Y` as extra element blocks.
- [x] Limit generic all-9 post-clean nulling to schema-governed parsed fields only; valid free-text Part 30 payloads such as `REM__text='999'` and `QNN__data_values='999999'` are now preserved.
- [x] Use Part 2 control `DATE` + `TIME` together when deriving timestamps/hours, while preserving existing timestamp-in-`DATE` compatibility for non-strict pipeline inputs.
- [x] Enforce exact Part 2 longitude domain bounds from scaled values: accept `-179.999..+180.000` and reject `-180.000` (current normalization uses `-180.0..180.0`). `clean_noaa_dataframe()` now normalizes `LONGITUDE` with a lower bound of `-179.999`, matching the raw control-field integer domain.
- [x] Prevent pipeline fallback from bypassing Part 2 `DATE` format rules: `process_location_from_raw` currently pre-parses raw `DATE` and `_extract_time_columns` backfills rejected non-`YYYYMMDD` values via `DATE_PARSED`. Strict mode now disables the `DATE_PARSED` fallback path; non-strict mode retains legacy timestamp compatibility.
- [x] Enforce Part 2 `CALL_SIGN` structural constraints for `POS 52-56` (5-character ASCII field; `99999` missing) instead of accepting arbitrary non-empty string lengths. Control-field normalization now requires exact 5-character printable ASCII tokens, accepts space-padded values, and rejects short/long/non-ASCII inputs.
- [x] Enforce strict field arity per identifier (expected comma-part count): reject truncated/extra payloads (e.g., `TMP` without quality, `WND` missing speed quality) instead of emitting partial parsed values. **(A3)** Added `get_expected_part_count()` in [constants.py](src/noaa_climate_data/constants.py); `clean_value_quality()` validates part count in [cleaning.py](src/noaa_climate_data/cleaning.py) with special handling for value/quality fields. Logs `[PARSE_STRICT]` warnings. Tests in [test_cleaning.py::TestA3ArityValidation](tests/test_cleaning.py).
- [x] Enforce fixed-width token formats beyond Part 4 additional numerics: validate documented POS/width/sign conventions for mandatory and other sections so shortened tokens like `WND=1,1,N,5,1` or `TMP=250,1` are not accepted as valid measurements. **(A4)** Added `token_width` and `token_pattern` fields to `FieldPartRule` dataclass; added `get_token_width_rules()` in [constants.py](src/noaa_climate_data/constants.py); validation implemented in `_expand_parsed()` and `clean_value_quality()` in [cleaning.py](src/noaa_climate_data/cleaning.py). Token width rules defined for WND (3/1/1/4/1 digits), TMP/DEW (4 digits after sign), SLP (5 digits). Tests in [test_cleaning.py::TestA4TokenWidthValidation](tests/test_cleaning.py).
- [x] Restrict comma-field expansion to known NOAA coded identifiers only; current generic parsing can split non-spec metadata columns (e.g., `NAME`) into synthetic `__part*` outputs and mutate schema. **(A1)** Added KNOWN_IDENTIFIERS allowlist (867 identifiers) via `_build_known_identifiers()` in [constants.py](src/noaa_climate_data/constants.py); `clean_noaa_dataframe()` in [cleaning.py](src/noaa_climate_data/cleaning.py) uses `get_field_rule()` for prefix-aware validation and skips unknown identifiers in strict mode. Logs `[PARSE_STRICT]` warnings. Tests in [test_cleaning.py::TestA1UnknownIdentifierAllowlist](tests/test_cleaning.py).
- [x] Enforce numeric-domain type strictness: for parts documented as numeric-only domains, reject/null malformed non-numeric tokens instead of preserving raw text fallback (e.g., `WND__part1='A90'`, `WND__part4='0A50'`). Numeric parts now null on parse failure and emit `MALFORMED_TOKEN` QC instead of leaking raw text.
- [x] Preserve Part 30 EQD original-value text fidelity (`FLD LEN: 6`, ASCII domain): keep `Q##/P##/R##/C##/D##/N##` part1 as text (including leading zeros/sign formatting) rather than float-coercing numeric-like values. `Q##` part1 payloads now preserve fixed-width raw text such as `001234` and `+01234`.
- [x] Preserve fixed-width categorical code representation for numeric-like code domains (e.g., Part 5/28 `AT/AW/MV/MW` weather codes): avoid float coercion that collapses `01` to `1.0`. Weather-type/code outputs now retain zero-padded string tokens.
- [x] Enforce Part 6 CRN QC missing semantics: when QC code is `9` (`Missing`), null associated measurement values for CRN unique groups (`CB/CF/CG/CH/CI/CN`) instead of retaining them. Associated measurement parts now resolve to missing when their governing CRN QC part is `9`.

## P1: Missing ISD groups and sections (implementation gaps)

- [x] Add Part 4 additional data section identifier ADD (section boundary for variable groups).
- [x] Add precipitation groups from Part 4 beyond AA/AJ/AU (e.g., AB1 monthly total, AC1 precipitation history, AD1 greatest 24-hour amount).
- [x] Add Part 4 additional precipitation groups: AE1, AG1.
- [x] Add Part 4 additional precipitation groups: AH1-AH6, AI1-AI6, AK1, AL1-AL4, AM1, AN1, AO1-AO4, AP1-AP4.
- [x] Add Part 4 snow-accumulation groups AL1-AL4 (accumulation period/depth), AM1 (greatest 24-hour amount), AN1 (day/month totals).
- [x] Add Part 4 additional liquid-precip groups AO1-AO4 (minutes-based), AP1-AP4 (HPD 15-min gauges with quality codes).
- [x] Add Part 5 weather occurrence groups AT1-AT8 (daily present weather) and AU1-AU9 (present weather observation components).
- [x] Add Part 5 automated present-weather groups AW1-AW4 (automated atmospheric condition codes).
- [x] Add Part 6 CRN unique groups CB1-CB2 (secondary precip), CF1-CF3 (fan speed), CG1-CG3 (primary precip), CH1-CH2 (RH/Temp), CI1 (hourly RH/Temp stats), and CN1-CN4 (battery + diagnostics).
- [x] Add Part 7 network metadata groups CO1 (climate division + UTC offset), CO2-CO9 (element time offsets), CR1 (CRN control), CT1-CT3 (subhourly temp), CU1-CU3 (hourly temp + std dev).
- [x] Add Part 7 network metadata groups CV1-CV3 (hourly temp extremes + times), CW1 (subhourly wetness), CX1-CX3 (hourly Geonor vibrating wire summary).
- [x] Add Part 8 CRN control section fields (air temp QC, dew point + QC, sea level pressure + QC).
- [x] Add Part 14 runway visual range group ED1 (runway designator, direction, visibility, quality).
- [x] Implement remaining cloud/solar groups from Part 15 (e.g., below-station cloud layer sections not yet mapped).
- [x] Add Part 15 below-station cloud layer group GG1-GG6 (coverage, heights, type/top codes, and quality flags).
- [x] Add Part 15 modeled solar irradiance group GP1 (modeled global/direct/diffuse values, flags, and uncertainties).
- [x] Add Part 20 hourly solar angle group GQ1 (time period, mean zenith/azimuth angles, QC).
- [x] Add Part 20 hourly extraterrestrial radiation group GR1 (time period, horizontal/normal values, QC).
- [x] Add Hail data group from Part 20/22 (identifier + hail size/quality); master doc labels a HAIL identifier but does not show its code.
- [x] Add Part 23 ground surface groups IA1/IA2, IB1/IB2, IC1 (ground condition, min/max temps, snow depth), with quality codes.
- [x] Add Part 23 air temperature groups KB1-KB3 (average air temperature) with scaling/sentinels.
- [x] Add Part 23 ground/soil temperature groups KC1-KC2, KD1-KD2, KE1, KF1, KG1-KG2 (soil/ground temps and quality flags).
- [x] Add Part 24 temperature groups KC1-KC2 (extreme air temperature for month) and KD1-KD2 (heating/cooling degree days).
- [x] Add Part 24 temperature groups KF1 (derived hourly air temperature) and KG1-KG2 (average dew point/wet bulb).
- [x] Add Part 26 soil temperature group ST1 (type, temp, depth, cover, subplot, quality codes).
- [x] Add Part 27 pressure groups beyond MA1/MD1 (ME1, MF1, MG1, MH1, MK1).
- [x] Add Part 28 relative humidity group RH1-RH3 (period, code, derived, QC).
- [x] Add Part 29 hourly/sub-hourly wind section OB1-OB2.
- [x] Add Part 29 supplementary wind group OE1-OE3 (summary-of-day wind).
- [x] Add remaining marine groups from Part 30 (e.g., WA1 platform ice accretion, other marine sections listed in Part 30).
- [x] Add Part 30 secondary swell group UG2 and remaining marine groups (WA1, WD1, WG1, WJ1).
- [x] Add Part 30 element quality data section (EQD with Q01-P01-R01/C01/D01/N01 identifiers, parameter/units codes, and marine-specific QC definitions).
- [x] Add EQD element-units table plus parameter-code flag conventions (Flag-1/Flag-2 definitions and element-name codes).
- [x] Add Part 30 remarks data section (REM) and remark type identifiers (SYN/AWY/MET/SOD/SOM/HPD).
- [x] Add Original Observation Data Section identifiers QNN (original NCEI surface hourly source codes/flags).
- [x] Add QNN original observation element identifiers (A-Y mapping for DS3280 elements) and data value format.

## P2: README alignment (implementation vs README)

- [x] Clarify README vs implementation for multi-part fields: code only emits a single `__quality` column when all parts share one `quality_part`; most multi-part ISD groups only expose per-part quality columns.
- [x] Align `LocationData_Hourly.csv` definition with behavior: either apply completeness filters to hourly output or update README to state it is best-hour only.
- [x] Update README aggregation section to reflect `sum`, `mode`, and `circular_mean` where used (precip totals, wind direction).
- [x] Update README field reference for OD* wind direction to reflect `circular_mean` aggregation (not plain mean).
- [x] Document `REM`/`QNN` parsing outputs (e.g., `REM__type`, `REM__text`, `QNN__elements`, `QNN__source_flags`, `QNN__data_values`).
- [x] Document the `WND__direction_variable` flag for variable wind direction rows.
- [x] Update README sentinel list to include GE1 vertical datum missing sentinel (`999999`) and convective cloud missing sentinel (`9`).
- [x] Expand README field reference / parsed group list to cover newly supported sections (CRN/network metadata, marine, solar/sunshine, runway visual range, soil/ground/pressure extensions).

## P3: Supporting docs, validation, and tests (post-spec hardening)

- [x] Populate missing ISD docs in-repo (Parts 10/11/16/17/18/19/21/22/24/25) to verify KA*/SA1 scaling/sentinels and solar/sunshine/hail sections.
- [x] Add tests for new groups to ensure sentinel removal and quality filtering are applied consistently.
- [x] Add exact-ID tests for under-covered sections (GM1/GN1/GO1, GH1, GD*, CO3-CO9, Q01-Q99/P01-P99/R01-R99/C01-C99/D01-D99/N01-N99).
- [x] Capture Domain Value ID tables for code validation (e.g., pressure tendency, geopotential levels, weather codes) if used in parsing. Added doc-backed definition tables in [constants.py](src/noaa_climate_data/constants.py) for `MD1`, `ME1`, and the Part 5/28 weather-code families (`AT/AU/AW/AX/MV/MW/AY/AZ`); field rules now derive allowed-value sets from those named tables, with alignment regressions in [test_cleaning.py](tests/test_cleaning.py).
- [x] Enforce numeric MIN/MAX ranges from the ISD spec (beyond current CIG/VIS clamping), or document why range checks are intentionally skipped. **Verified (2026-02-28):** `SPEC_COVERAGE_REPORT.md` reports `range` coverage at `361/361` implemented and strict-tested, with no strict implementation/test gaps.
- [x] Consider enforcing record/section length constraints (control=60, mandatory=45, max record 2844, max block 8192) if parser validates structure. Strict raw-line validation now rejects records shorter than the fixed 105-character control+mandatory prefix, records longer than 2,844 characters, and oversized 8,192+ character blocks before field expansion; focused regression coverage was added in [test_cleaning.py](tests/test_cleaning.py).
- [x] Parse and validate REM remark length quantity (Part 30) instead of only splitting type/text. `clean_noaa_dataframe()` now validates `TYPE(3)+LEN(3)+TEXT(LEN)` REM blocks, treats malformed typed payloads as unparsed raw text, and keeps compatibility via first-entry `remarks_type_code` / `remarks_text` columns.
- [x] Parse repeated REM remark entries in a single REM section (typed remark + length + text blocks), not just a single prefix/text split. Repeated Part 30 REM entries are now parsed losslessly into `REM__types` / `REM__texts_json` (friendly: `remarks_type_codes` / `remarks_text_blocks_json`) while preserving the first parsed entry in existing columns.
- [x] Add targeted tests for newly identified gaps: OE period/time range enforcement, AP condition code fixed-to-9 behavior, AW sparse domain validation, and Q/P/R/C/D EQD parameter-code acceptance rules.
- [x] Add regression tests for remaining Part 4 range/date validation (`AB/AD/AE/AJ/AK/AL/AM/AN`).
- [x] Add regression tests for `AH`/`AI` friendly-column collision detection. Existing friendly-name disambiguation coverage in [test_cleaning.py](tests/test_cleaning.py) now also asserts the cleaned dataframe has no duplicate columns and retains distinct `AH1`/`AI1` values after rename.
- [x] Add regression tests for `QNN` ASCII-preservation/token-boundary handling. Added multi-block parser coverage in [test_cleaning.py](tests/test_cleaning.py) using printable punctuation in source/data tokens and a second data value that begins with an identifier-like letter to pin the non-greedy boundary logic.
- [x] Add regression tests for protection against blanket all-9 nulling of valid REM/QNN text payloads. Added dataframe-level regressions in [test_cleaning.py](tests/test_cleaning.py) confirming `remarks_text='999999'`, `qnn_source_flags='9999'`, and `qnn_data_values='999999'` survive post-cleanup text normalization.
- [x] Add regression tests for malformed identifier rejection in currently-gated families (`CO02`/`OA01`/`Q100`/`Q01A`/`N001`) and for Part 2 split `DATE`+`TIME` hour extraction behavior.
- [x] Add regression tests for sixth-pass Part 2 control gaps: longitude lower-bound edge handling (`-180.000` vs `-179.999`), `CALL_SIGN` width/domain enforcement, and pipeline-level rejection of non-`YYYYMMDD` dates despite `DATE_PARSED` fallback. Added targeted cases in [test_cleaning.py](tests/test_cleaning.py) and [test_aggregation.py](tests/test_aggregation.py).
- [x] Add regression tests for parser strictness on field structure: unknown comma-bearing metadata columns should not be expanded, malformed/truncated part-count payloads should be rejected, and non-conformant token widths should not be coerced into valid values. **Gate A validation tests added:** [TestA1UnknownIdentifierAllowlist](tests/test_cleaning.py), [TestA2MalformedIdentifierFormat](tests/test_cleaning.py), [TestA3ArityValidation](tests/test_cleaning.py), [TestA4TokenWidthValidation](tests/test_cleaning.py) with 27 comprehensive tests covering allowlist, format, arity, and token width validation.
- [x] Add regression tests for fifth-pass issues: numeric-domain malformed-token rejection (no raw-text fallback), EQD part1 6-char text preservation (`001234` stays text), categorical code-width preservation (`01` not coerced to `1.0`), and CRN QC=`9` missing-value nulling behavior. Added focused parser regressions in [test_cleaning.py](tests/test_cleaning.py) covering WND/TMP malformed numerics, EQD text fidelity, AT/AW/MV/MW code preservation, and CRN missing-by-QC semantics.
