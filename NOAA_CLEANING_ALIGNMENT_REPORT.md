# NOAA Cleaning Alignment Report (ISD Parts 01-30)

Date: 2026-02-14

## Scope

Compared `isd-format-document-parts/part-01-*.md` through `part-30-*.md` against:

- `src/noaa_climate_data/cleaning.py`
- `src/noaa_climate_data/constants.py`
- `tests/test_cleaning.py`

## Recheck Summary (2026-03-01)

This report is now materially stale. A recheck against the current repository shows that most of the unresolved February 14 findings have been fixed in code and tests.

- Current baseline: `poetry run pytest -q` passes (`2120 passed, 18 skipped`).
- Current generated coverage: `SPEC_COVERAGE_REPORT.md` reports `3536/3536` strict rules implemented and test-covered.
- Confirmed fixed since this report:
  - Part 4 range/date enforcement outside `AH/AI`.
  - Part 17/18/20/21 solar and radiation numeric range enforcement (`GM/GN/GO/GQ/GR`).
  - Part 23/26 ground-surface and soil-temperature numeric range enforcement (`IA/IB/IC/ST1`).
  - Part 6 CRN numeric range enforcement (`CI1`, `CN1-CN4`).
  - Strict malformed identifier rejection in the main strict parse path for cases such as `CO02`, `OA01`, `RH0001`, `Q100`, and `N001`.
  - REM priority parsing before generic comma expansion.

Status update (2026-03-01, post-fix): the four remaining issues from the March 1 recheck have now been resolved in code and regression tests:

- Part 30 `QNN` parsing now preserves raw ASCII/case for source-flag and data-value tokens, and valid all-9 `REM`/`QNN` text payloads are no longer erased by blanket object-column nulling.
- `AH*` and `AI*` friendly-column mappings are now distinct, with legacy ambiguous aliases kept only as reverse-mapping compatibility aliases for `AH*`.
- Pipeline hour extraction now combines split `DATE` + `TIME` inputs while preserving existing timestamp-in-`DATE` behavior.
- Helper-level EQD lookup now rejects malformed identifiers such as `Q01A` instead of allowing prefix fallback.

Unless re-listed above, treat the unresolved items in the older sections below as historical and superseded by this recheck.

## Part-by-Part Alignment and Misalignment

| Part | Alignment snapshot | Misalignment snapshot |
| --- | --- | --- |
| 01 Preface | Record/section concepts reflected in pipeline structure. | Record/section length enforcement remains backlog (`NEXT_STEPS.md`). |
| 02 Control | DATE/TIME, lat/lon/elev, source/report/QC normalization is implemented and tested. | No net-new gap from this pass. |
| 03 Mandatory | `WND`, `CIG`, `VIS`, `TMP`, `DEW`, `SLP` decoding, calm/clamp behavior, quality gating are implemented and tested. | Remaining hard min/max enforcement is still a known backlog item. |
| 04 Additional | AA/AP/AJ/AH/AI/etc. groups exist and are quality/sentinel-aware. | New: Part 4 `AH/AI` numeric/time ranges are not enforced, and broad prefix matching can accept out-of-domain repeat IDs (for families with fixed limits). |
| 05 Weather Occurrence | `AT/AU/AX/AY/AZ/AW` parsing exists with broad test coverage. | New: exact repeater cardinality is not enforced for several groups (e.g., `AT9`, `AU10`, `AW5`, `AX7`, `AZ3`). |
| 06 CRN Unique | `CB/CF/CG/CH/CI/CN` sections and QC/flag handling are implemented. | New: many documented MIN/MAX bounds in `CI1` and `CN1-CN4` are still not encoded. |
| 07 Network Metadata | `CO1`, `CO2-CO9` support exists with tests. | New: exact identifier cardinality is not enforced (e.g., broad prefix matching can accept out-of-domain `CO*` identifiers). |
| 08 CRN Control | `CR1` parsing and QC handling implemented. | No net-new gap from this pass. |
| 09 Subhourly Temp | `CT1-CT3` implemented and tested. | New: Part 9 temperature value bounds are not enforced (`CT` allows extreme out-of-range values). |
| 10 Hourly Temp | `CU1-CU3` implemented and tested. | New: Part 10 average/std-dev temperature bounds are not enforced for `CU*`. |
| 11 Hourly Temp Extreme | `CV1-CV3` implemented with HHMM checks and QC tests. | New: Part 11 min/max temperature bounds are not enforced for `CV*` values (time fields are checked). |
| 12 Subhourly Wetness | `CW1` implemented and tested. | No net-new gap from this pass. |
| 13 Geonor Summary | `CX1-CX3` implemented and tested. | New: Part 13 precipitation/frequency numeric bounds are only partially enforced (`CX*` accepts out-of-range numeric values). |
| 14 Runway Visual Range | `ED1` implemented with domain and quality checks. | No net-new gap from this pass. |
| 15 Cloud and Solar | `GA/GD/GE1/GF1/GG/GH1` sections are present with core code-domain validation. | Resolved (February 22, 2026): Part 15 cloud-height and `GH1` solar-radiation numeric MIN/MAX constraints are enforced in cleaning rules/tests. |
| 16 Sunshine | `GJ/GK/GL` sections implemented and range-tested. | No net-new gap from this pass. |
| 17 Solar Irradiance | `GM1/GN1` parsing and quality domains are implemented. | New: irradiance value ranges (and GN zenith-angle range) are largely unchecked beyond sentinel handling. |
| 18 Net Solar Radiation | `GO1` implemented with time-period checks. | New: GO component value ranges (`-999..9998`) are not enforced. |
| 19 Modeled Solar Irradiance | `GP1` source flags/uncertainty bounds implemented and tested. | No net-new gap from this pass. |
| 20 Hourly Solar Angle | `GQ1` implemented with QC and period checks. | New: documented angle-value bounds (`0000-3600`) are not enforced for mean zenith/azimuth fields. |
| 21 Hourly Extraterrestrial Radiation | `GR1` implemented with QC and period checks. | New: documented radiation-value bounds (`0000-9998`) are not enforced for horizontal/normal fields. |
| 22 Hail | `HAIL` section implemented with range/quality tests. | No net-new gap from this pass. |
| 23 Ground Surface | `IA/IB/IC` sections implemented with code/quality/sentinel handling. | New: many Part 23 numeric MIN/MAX bounds (IA2/IB1/IB2/IC1) are not enforced. |
| 24 Temperature | `KA/KB/KC/KD/KE/KF/KG` sections implemented and broadly tested for sentinels/quality/code domains. | Resolved (February 22, 2026): Part 24 numeric MIN/MAX constraints and KC date-token validation are enforced, including KA exact `-0932..+0618` bounds. |
| 25 Sea Surface Temp | `SA1` implemented with quality and range checks. | No net-new gap from this pass. |
| 26 Soil Temp | `ST1` implemented with categorical and quality-domain checks. | New: soil-temperature and depth numeric MIN/MAX bounds are not enforced. |
| 27 Pressure | `MA/MD/ME/MF/MG/MH/MK` sections implemented with quality and core code-domain checks. | Resolved (February 22, 2026): pressure numeric MIN/MAX bounds and `MK1` DDHHMM occurrence-time bounds are enforced. |
| 28 Weather Extended | `MV/MW` sections implemented with code-domain checks. | No net-new gap from this pass. |
| 29 Wind | `OA/OB/OC/OD/OE/RH` sections implemented and tested. | Resolved (February 22, 2026): `OC1` and `RH*` MIN/MAX ranges are enforced, and `OE` occurrence time enforces real HHMM minute semantics (rejects `0060`/`1261`). |
| 30 Marine | `UA/UG/WA/WD/WG/WJ/EQD/REM/QNN` sections are present; `QNN` parsing now enforces structured element/value grouping. | New: REM parsing order conflicts with generic comma-splitting; comma-bearing remarks can lose typed REM outputs when `keep_raw=False`. |

## Net-New Misalignments Identified

1. Identifier family cardinality is over-permissive.
   - Spec bounds are explicit for repeated identifiers: `CO2-CO9` (`isd-format-document-parts/part-07-network-metadata.md:43`), `OA1-OA3`/`OD1-OD3`/`OE1-OE3`/`RH1-RH3` (`isd-format-document-parts/part-29-wind-data.md:9`, `isd-format-document-parts/part-29-wind-data.md:245`, `isd-format-document-parts/part-29-wind-data.md:311`, `isd-format-document-parts/part-29-wind-data.md:387`), and `Q01-99`/`N01-99` families (`isd-format-document-parts/part-30-marine-data.md:794`, `isd-format-document-parts/part-30-marine-data.md:803`).
   - Current matching uses broad `startswith` lookup (`src/noaa_climate_data/constants.py:3123`) fed by coarse prefixes (`src/noaa_climate_data/constants.py:3114`), so out-of-domain IDs can still resolve to rules.
   - Tests validate valid suffix examples only (`tests/test_cleaning.py:94`) and do not assert rejection of invalid suffixes.

2. Resolved (February 22, 2026): Part 15 cloud-height ranges are enforced for GA/GD/GE1/GF1/GG.
   - Spec ranges remain: GA/GD heights to `+35000`, GE1 upper/lower ranges to `+15000`, GF1 lowest cloud base to `15000`, and GG height to `35000`.
   - Enforcement is encoded in `FIELD_RULES` with min/max checks and covered by cleaning tests.

3. Resolved (February 22, 2026): Part 15 `GH1` solar-radiation value ranges are enforced.
   - Spec bounds remain: `0000/00000..99998` with `99999` missing across average/min/max/std components.
   - Enforcement is encoded in `FIELD_RULES` min/max and reflected in tests.

4. Parts 17-18 `GM/GN/GO` numeric component ranges are only partially enforced.
   - Spec ranges include `GM/GN` irradiance components (`0000-9998`), `GN` solar zenith angle (`000-998`) (`isd-format-document-parts/part-17-solar-irradiance-section.md:41`, `isd-format-document-parts/part-17-solar-irradiance-section.md:219`, `isd-format-document-parts/part-17-solar-irradiance-section.md:306`), and `GO` net radiation components (`-999..9998`) (`isd-format-document-parts/part-18-net-solar-radiation-section.md:28`, `isd-format-document-parts/part-18-net-solar-radiation-section.md:47`, `isd-format-document-parts/part-18-net-solar-radiation-section.md:65`).
   - Current rules constrain time-period part 1 but leave many component numeric parts without min/max bounds (`src/noaa_climate_data/constants.py:2232`, `src/noaa_climate_data/constants.py:2244`, `src/noaa_climate_data/constants.py:2256`, `src/noaa_climate_data/constants.py:2268`, `src/noaa_climate_data/constants.py:2285`, `src/noaa_climate_data/constants.py:2291`, `src/noaa_climate_data/constants.py:2297`, `src/noaa_climate_data/constants.py:2303`, `src/noaa_climate_data/constants.py:2309`, `src/noaa_climate_data/constants.py:2326`, `src/noaa_climate_data/constants.py:2332`, `src/noaa_climate_data/constants.py:2338`).
   - Tests currently focus on flag/quality/time-period behavior (`tests/test_cleaning.py:1307`, `tests/test_cleaning.py:1326`, `tests/test_cleaning.py:1330`, `tests/test_cleaning.py:1334`).

5. Resolved (February 22, 2026): Part 27 pressure ranges are enforced for MA/MD/ME/MF/MG/MH/MK.
   - Spec ranges remain explicit across station pressure, pressure change, and sea-level pressure fields.
   - Enforcement is now encoded in `FIELD_RULES` min/max (including `ME1` geopotential meters `0000..9998`) and covered by tests.

6. Resolved (February 22, 2026): Part 27 `MK1` occurrence date-time fields are range-validated.
   - Spec DDHHMM bounds remain `MIN 010000` and `MAX 312359`.
   - Enforcement uses DDHHMM pattern validation in cleaning rules and is test-covered.

7. Resolved (February 22, 2026): Part 24 temperature ranges/dates are enforced.
   - KA/KB/KC/KD/KF/KG numeric ranges and KC date-token checks are encoded in rules.
   - KA bounds now follow spec exactly (`-0932..+0618`), with regression tests updated accordingly.

8. Part 23 ground-surface numeric ranges are only partially enforced.
   - Spec provides explicit bounds for IA2/IB1/IB2/IC1 numeric fields (e.g., IA2 period `001-480`, IA2 minimum temperature `-1100..+1500`, IB temperature fields `-9999..+9998`, IB standard deviation `0000..9998`, IC period `01-98`, IC wind movement `0000..9998`, IC evaporation `000..998`, IC pan-water temperatures `-100..+500`) (`isd-format-document-parts/part-23-ground-surface-data.md:89`, `isd-format-document-parts/part-23-ground-surface-data.md:97`, `isd-format-document-parts/part-23-ground-surface-data.md:144`, `isd-format-document-parts/part-23-ground-surface-data.md:168`, `isd-format-document-parts/part-23-ground-surface-data.md:193`, `isd-format-document-parts/part-23-ground-surface-data.md:226`, `isd-format-document-parts/part-23-ground-surface-data.md:266`, `isd-format-document-parts/part-23-ground-surface-data.md:299`, `isd-format-document-parts/part-23-ground-surface-data.md:346`, `isd-format-document-parts/part-23-ground-surface-data.md:354`, `isd-format-document-parts/part-23-ground-surface-data.md:388`, `isd-format-document-parts/part-23-ground-surface-data.md:415`, `isd-format-document-parts/part-23-ground-surface-data.md:450`).
   - Current rules for these fields are largely sentinel/quality-based without min/max constraints (`src/noaa_climate_data/constants.py:2460`, `src/noaa_climate_data/constants.py:2461`, `src/noaa_climate_data/constants.py:2472`, `src/noaa_climate_data/constants.py:2479`, `src/noaa_climate_data/constants.py:2486`, `src/noaa_climate_data/constants.py:2493`, `src/noaa_climate_data/constants.py:2505`, `src/noaa_climate_data/constants.py:2512`, `src/noaa_climate_data/constants.py:2524`, `src/noaa_climate_data/constants.py:2525`, `src/noaa_climate_data/constants.py:2538`, `src/noaa_climate_data/constants.py:2551`, `src/noaa_climate_data/constants.py:2564`).

9. Part 26 `ST1` numeric ranges are only partially enforced.
   - Spec defines `ST1` soil temperature range `-1100..+0630` and depth range `0000..9998` (`isd-format-document-parts/part-26-soil-temperature-data.md:34`, `isd-format-document-parts/part-26-soil-temperature-data.md:52`).
   - Current `ST1` numeric parts carry sentinels/quality links but no min/max checks (`src/noaa_climate_data/constants.py:2031`, `src/noaa_climate_data/constants.py:2037`), and tests focus on sentinel/quality behavior (`tests/test_cleaning.py:397`, `tests/test_cleaning.py:1470`).

10. Part 20/21 `GQ1` and `GR1` value ranges are not enforced.
   - Spec defines `GQ1` mean zenith/azimuth `0000..3600` (`isd-format-document-parts/part-20-hourly-solar-angle-section.md:32`, `isd-format-document-parts/part-20-hourly-solar-angle-section.md:50`) and `GR1` horizontal/normal radiation `0000..9998` (`isd-format-document-parts/part-21-hourly-extraterrestrial-radiation-section.md:27`, `isd-format-document-parts/part-21-hourly-extraterrestrial-radiation-section.md:53`).
   - Current rules validate time period and quality but not those value bounds (`src/noaa_climate_data/constants.py:2418`, `src/noaa_climate_data/constants.py:2424`, `src/noaa_climate_data/constants.py:2441`, `src/noaa_climate_data/constants.py:2447`); tests likewise cover missing/quality/time period only (`tests/test_cleaning.py:1367`, `tests/test_cleaning.py:1378`, `tests/test_cleaning.py:1382`, `tests/test_cleaning.py:1393`).

11. Resolved (February 22, 2026): Part 24 `KE1` day-count ranges are enforced.
   - Spec day-count bounds `00..31` (`99` missing) are encoded in all four `KE1` count parts.
   - Cleaning tests assert out-of-range rejection for each count position.

12. Part 30 `REM` parsing can be bypassed by generic comma expansion.
   - Spec defines REM as typed remark blocks (`REM` + type + length + text), where free-text remark content is ASCII and can include punctuation (`isd-format-document-parts/part-30-marine-data.md:731`, `isd-format-document-parts/part-30-marine-data.md:737`, `isd-format-document-parts/part-30-marine-data.md:760`, `isd-format-document-parts/part-30-marine-data.md:766`).
   - Current flow parses any comma-bearing object column first (`src/noaa_climate_data/cleaning.py:506`, `src/noaa_climate_data/cleaning.py:511`, `src/noaa_climate_data/cleaning.py:524`) and runs REM-specific parsing later only if raw `REM` still exists (`src/noaa_climate_data/cleaning.py:530`).
   - Reproduced: `clean_noaa_dataframe(pd.DataFrame({'REM':['SYN 005 hello,world']}), keep_raw=False)` yields only `REM__part*` columns (no `remarks_type_code`/`remarks_text`); existing test coverage checks a simple REM case only (`tests/test_cleaning.py:1751`).

13. Resolved (February 22, 2026): Part 29 `OE` time-of-occurrence validation enforces real HHMM semantics.
   - Spec summary wind occurrence time remains `MIN 0000` to `MAX 2359` in HHMM format.
   - Validation rejects invalid-minute tokens such as `0060` and `1261`, with explicit regression tests.

14. Resolved (February 22, 2026): Part 29 `OC1` wind-gust numeric range is enforced.
   - Spec gust bounds `MIN 0050` and `MAX 1100` are encoded in rules.
   - Tests cover boundary pass and out-of-range rejection behavior.

15. Resolved (February 22, 2026): Part 29 `RH1-RH3` period and humidity bounds are enforced.
   - Spec bounds remain period `001..744` hours and humidity `000..100` percent.
   - Min/max checks are encoded in rules and covered by tests.

16. Part 4 `AH/AI` short-duration precipitation ranges are not enforced.
   - Spec defines `AH` period `005..045`, `AI` period `060..180`, depth `0000..3000`, and ending date-time `010000..312359` (`isd-format-document-parts/part-04-additional-data-section.md:485`, `isd-format-document-parts/part-04-additional-data-section.md:493`, `isd-format-document-parts/part-04-additional-data-section.md:510`, `isd-format-document-parts/part-04-additional-data-section.md:561`, `isd-format-document-parts/part-04-additional-data-section.md:569`, `isd-format-document-parts/part-04-additional-data-section.md:586`).
   - Current `AH*`/`AI*` rules use sentinels and condition/quality domains but no min/max or DDHHMM range validation for these parts (`src/noaa_climate_data/constants.py:1163`, `src/noaa_climate_data/constants.py:1166`, `src/noaa_climate_data/constants.py:1167`, `src/noaa_climate_data/constants.py:1174`, `src/noaa_climate_data/constants.py:1186`, `src/noaa_climate_data/constants.py:1189`, `src/noaa_climate_data/constants.py:1190`, `src/noaa_climate_data/constants.py:1197`).
   - Existing tests focus on missing/quality behavior (`tests/test_cleaning.py:1589`, `tests/test_cleaning.py:1596`, `tests/test_cleaning.py:1600`, `tests/test_cleaning.py:1607`).

17. Remaining Part 6/9/10/11/13 numeric range enforcement is incomplete.
   - Specs define explicit numeric bounds for `CI1`/`CN1-CN4` diagnostics in Part 6 (`isd-format-document-parts/part-06-climate-reference-network-unique-data.md:243`, `isd-format-document-parts/part-06-climate-reference-network-unique-data.md:269`, `isd-format-document-parts/part-06-climate-reference-network-unique-data.md:303`, `isd-format-document-parts/part-06-climate-reference-network-unique-data.md:329`, `isd-format-document-parts/part-06-climate-reference-network-unique-data.md:381`, `isd-format-document-parts/part-06-climate-reference-network-unique-data.md:437`, `isd-format-document-parts/part-06-climate-reference-network-unique-data.md:479`, `isd-format-document-parts/part-06-climate-reference-network-unique-data.md:511`, `isd-format-document-parts/part-06-climate-reference-network-unique-data.md:537`, `isd-format-document-parts/part-06-climate-reference-network-unique-data.md:584`, `isd-format-document-parts/part-06-climate-reference-network-unique-data.md:609`, `isd-format-document-parts/part-06-climate-reference-network-unique-data.md:711`, `isd-format-document-parts/part-06-climate-reference-network-unique-data.md:743`), plus temperature/frequency bounds for `CT/CU/CV/CX` in Parts 9-13 (`isd-format-document-parts/part-09-subhourly-temperature-section.md:29`, `isd-format-document-parts/part-10-hourly-temperature-section.md:22`, `isd-format-document-parts/part-10-hourly-temperature-section.md:54`, `isd-format-document-parts/part-11-hourly-temperature-extreme-section.md:28`, `isd-format-document-parts/part-11-hourly-temperature-extreme-section.md:84`, `isd-format-document-parts/part-13-hourly-geonor-vibrating-wire-summary-section.md:33`, `isd-format-document-parts/part-13-hourly-geonor-vibrating-wire-summary-section.md:56`, `isd-format-document-parts/part-13-hourly-geonor-vibrating-wire-summary-section.md:87`, `isd-format-document-parts/part-13-hourly-geonor-vibrating-wire-summary-section.md:110`).
   - Current rules for these sections largely apply sentinels + quality domains but omit many explicit min/max checks (`src/noaa_climate_data/constants.py:1625`, `src/noaa_climate_data/constants.py:1637`, `src/noaa_climate_data/constants.py:1656`, `src/noaa_climate_data/constants.py:1720`, `src/noaa_climate_data/constants.py:2964`, `src/noaa_climate_data/constants.py:2997`, `src/noaa_climate_data/constants.py:3023`, `src/noaa_climate_data/constants.py:3049`, `src/noaa_climate_data/constants.py:3068`).

18. Repeated-identifier cardinality remains over-permissive for many families outside current gated ranges.
   - Spec cardinality is explicit in multiple sections: e.g., `AH1-AH6`/`AI1-AI6`/`AL1-AL4`/`AO1-AO4` (`isd-format-document-parts/part-04-additional-data-section.md:474`, `isd-format-document-parts/part-04-additional-data-section.md:550`, `isd-format-document-parts/part-04-additional-data-section.md:787`, `isd-format-document-parts/part-04-additional-data-section.md:992`), `AT1-AT8`/`AU1-AU9`/`AW1-AW4`/`AX1-AX6`/`AZ1-AZ2` (`isd-format-document-parts/part-05-weather-occurrence-data.md:8`, `isd-format-document-parts/part-05-weather-occurrence-data.md:108`, `isd-format-document-parts/part-05-weather-occurrence-data.md:218`, `isd-format-document-parts/part-05-weather-occurrence-data.md:353`, `isd-format-document-parts/part-05-weather-occurrence-data.md:482`), `GA1-GA6`/`GD1-GD6`/`GG1-GG6` (`isd-format-document-parts/part-15-cloud-and-solar-data.md:9`, `isd-format-document-parts/part-15-cloud-and-solar-data.md:131`, `isd-format-document-parts/part-15-cloud-and-solar-data.md:626`), and `MV1-MV7`/`MW1-MW7` (`isd-format-document-parts/part-28-weather-occurrence-data-extended.md:9`, `isd-format-document-parts/part-28-weather-occurrence-data-extended.md:53`).
   - `_REPEATED_IDENTIFIER_RANGES` currently enforces bounds for a small subset only (`src/noaa_climate_data/constants.py:3147`), while generic prefix matching still resolves out-of-domain IDs for other families (`src/noaa_climate_data/constants.py:3190`, `src/noaa_climate_data/constants.py:3193`).
   - Reproduced with `get_field_rule(...)`: `AT9`, `AU10`, `AW5`, `AX7`, `AZ3`, `AH7`, `AL5`, `AO5`, `GA7`, `GD7`, `GG7`, `MV8`, and `MW8` all currently resolve as valid.

## Added to Next Steps

These eighteen items were recorded under `P0` in `NEXT_STEPS.md`.

## Follow-Up Pass: Additional Net-New Misalignments (All 30 Parts Re-Read)

Date: 2026-02-14 (follow-up pass)

### Part-by-Part Delta (New Findings Only)

| Part | Delta |
| --- | --- |
| 01 Preface | No additional misalignment beyond existing length/structure backlog. |
| 02 Control | No additional misalignment beyond existing backlog. |
| 03 Mandatory | No additional misalignment beyond existing backlog. |
| 04 Additional | **New**: remaining `AB/AD/AE/AJ/AK/AL/AM/AN` numeric/date bounds are still not enforced; **new** `AH`/`AI` friendly-column collisions. |
| 05 Weather Occurrence | No additional misalignment beyond existing backlog. |
| 06 CRN Unique | No additional misalignment beyond existing backlog. |
| 07 Network Metadata | No additional misalignment beyond existing backlog. |
| 08 CRN Control | No additional misalignment beyond existing backlog. |
| 09 Subhourly Temperature | No additional misalignment beyond existing backlog. |
| 10 Hourly Temperature | No additional misalignment beyond existing backlog. |
| 11 Hourly Temperature Extreme | No additional misalignment beyond existing backlog. |
| 12 Subhourly Wetness | No additional misalignment beyond existing backlog. |
| 13 Geonor Summary | No additional misalignment beyond existing backlog. |
| 14 Runway Visual Range | No additional misalignment beyond existing backlog. |
| 15 Cloud and Solar | No additional misalignment beyond existing backlog. |
| 16 Sunshine | No additional misalignment beyond existing backlog. |
| 17 Solar Irradiance | No additional misalignment beyond existing backlog. |
| 18 Net Solar Radiation | No additional misalignment beyond existing backlog. |
| 19 Modeled Solar Irradiance | No additional misalignment beyond existing backlog. |
| 20 Hourly Solar Angle | No additional misalignment beyond existing backlog. |
| 21 Hourly Extraterrestrial Radiation | No additional misalignment beyond existing backlog. |
| 22 Hail | No additional misalignment beyond existing backlog. |
| 23 Ground Surface | No additional misalignment beyond existing backlog. |
| 24 Temperature | No additional misalignment beyond existing backlog. |
| 25 Sea Surface Temperature | No additional misalignment beyond existing backlog. |
| 26 Soil Temperature | No additional misalignment beyond existing backlog. |
| 27 Pressure | No additional misalignment beyond existing backlog. |
| 28 Weather Extended | No additional misalignment beyond existing backlog. |
| 29 Wind | No additional misalignment beyond existing backlog. |
| 30 Marine | **New**: `QNN` parser applies non-spec normalization/constraints and ambiguous tokenization; **new** global all-9 nulling can erase valid `REM`/`QNN` text payloads. |

### Additional Misalignments Identified In This Follow-Up Pass

1. Part 4 still has multiple unencoded numeric/date bounds outside `AH/AI`.
   - Spec ranges include: `AB1` max `50000`, `AD1` max `20000` and date tokens `0101..3131`, `AE1` counts `00..31`, `AJ1` max depth/equivalent water (`1200`/`120000`), `AK1` max depth `1500` and day tokens `01..31`, `AL*` period/depth `00..72` and `000..500`, `AM1` max `2000` with date tokens `0101..3131`, `AN1` period `001..744` (`isd-format-document-parts/part-04-additional-data-section.md:120`, `isd-format-document-parts/part-04-additional-data-section.md:222`, `isd-format-document-parts/part-04-additional-data-section.md:249`, `isd-format-document-parts/part-04-additional-data-section.md:316`, `isd-format-document-parts/part-04-additional-data-section.md:636`, `isd-format-document-parts/part-04-additional-data-section.md:687`, `isd-format-document-parts/part-04-additional-data-section.md:736`, `isd-format-document-parts/part-04-additional-data-section.md:796`, `isd-format-document-parts/part-04-additional-data-section.md:804`, `isd-format-document-parts/part-04-additional-data-section.md:860`, `isd-format-document-parts/part-04-additional-data-section.md:879`, `isd-format-document-parts/part-04-additional-data-section.md:936`).
   - Current rules remain sentinel/quality-centric without those bounds (`src/noaa_climate_data/constants.py:1074`, `src/noaa_climate_data/constants.py:1110`, `src/noaa_climate_data/constants.py:1112`, `src/noaa_climate_data/constants.py:1125`, `src/noaa_climate_data/constants.py:1212`, `src/noaa_climate_data/constants.py:1234`, `src/noaa_climate_data/constants.py:1256`, `src/noaa_climate_data/constants.py:1276`, `src/noaa_climate_data/constants.py:1329`, `src/noaa_climate_data/constants.py:1340`).
   - Existing tests validate missing/quality behavior but not these min/max/date constraints (`tests/test_cleaning.py:1562`, `tests/test_cleaning.py:1575`, `tests/test_cleaning.py:1580`, `tests/test_cleaning.py:1612`, `tests/test_cleaning.py:1622`, `tests/test_cleaning.py:1632`, `tests/test_cleaning.py:1644`).

2. Part 4 `AH*` and `AI*` friendly-column mappings collide.
   - NOAA defines `AH1-AH6` and `AI1-AI6` as distinct repeating groups (5-45 minute vs 60-180 minute periods) (`isd-format-document-parts/part-04-additional-data-section.md:474`, `isd-format-document-parts/part-04-additional-data-section.md:485`, `isd-format-document-parts/part-04-additional-data-section.md:550`, `isd-format-document-parts/part-04-additional-data-section.md:561`).
   - Friendly mapping assigns both families to identical output names (`src/noaa_climate_data/constants.py:3441`, `src/noaa_climate_data/constants.py:3446`), and reverse mapping resolves those names back to `AH*` only (`src/noaa_climate_data/constants.py:3802`).
   - Practical effect: duplicate column names when both `AH*` and `AI*` are present, and loss of unambiguous round-trip semantics.

3. Part 30 `QNN` parser currently mutates/constrains data beyond spec text.
   - Spec keeps source/flag and data value domains at ASCII (`isd-format-document-parts/part-30-marine-data.md:1149`, `isd-format-document-parts/part-30-marine-data.md:1152`, `isd-format-document-parts/part-30-marine-data.md:1156`, `isd-format-document-parts/part-30-marine-data.md:1193`, `isd-format-document-parts/part-30-marine-data.md:1194`, `isd-format-document-parts/part-30-marine-data.md:1197`).
   - Current parser strips all whitespace and uppercases payload (`src/noaa_climate_data/cleaning.py:176`), and rejects source/flag tokens unless strictly alphanumeric (`src/noaa_climate_data/cleaning.py:187`).
   - Greedy 5-char block parsing can also consume leading `A`-`Y` data-value text as extra element blocks before validating 6-char data groups (`src/noaa_climate_data/cleaning.py:182`, `src/noaa_climate_data/cleaning.py:197`, `src/noaa_climate_data/cleaning.py:200`).

4. Blanket all-9 post-clean nulling can erase valid Part 30 text payloads.
   - Part 30 `REM` text and `QNN` data value fields are ASCII payloads, not global all-9 sentinels (`isd-format-document-parts/part-30-marine-data.md:768`, `isd-format-document-parts/part-30-marine-data.md:1194`).
   - Current dataframe-wide object-column pass nulls any all-9 string regardless of field semantics (`src/noaa_climate_data/cleaning.py:553`, `src/noaa_climate_data/cleaning.py:559`).
   - Reproduced locally: `REM__text='999'` and `QNN__data_values='999999'` are converted to null after parsing.

### Added to Next Steps (Follow-Up Pass)

Added these new items to `NEXT_STEPS.md`:

- Remaining Part 4 range/date enforcement outside `AH/AI`.
- `AH/AI` friendly-column collision disambiguation.
- `QNN` ASCII-preserving/non-greedy parsing hardening.
- Restricting blanket all-9 nulling to spec-governed fields.
- New regression tests for these scenarios.

## Third Pass: New Misalignments Beyond Existing NEXT_STEPS

Date: 2026-02-14 (third pass)

Scope for this pass:

- Re-read `part-01` through `part-30` one-by-one.
- Compared against current code and tests:
  - `src/noaa_climate_data/cleaning.py`
  - `src/noaa_climate_data/constants.py`
  - `src/noaa_climate_data/pipeline.py`
  - `tests/test_cleaning.py`
- Filtered out all misalignments already tracked in `NEXT_STEPS.md`.

### Part-by-Part Snapshot (New Findings Only)

| Part | Alignment | New misalignment in this pass |
| --- | --- | --- |
| 01 Preface | Section model and overall parsing structure remain aligned. | None newly identified. |
| 02 Control | DATE/TIME format validation exists in cleaning (`YYYYMMDD`/`HHMM`). | **New:** Part 2 split `DATE`+`TIME` semantics are not preserved in hour extraction; `_extract_time_columns` uses `DATE` only and ignores `TIME` (`src/noaa_climate_data/pipeline.py:404`). |
| 03 Mandatory | Mandatory groups (`WND/CIG/VIS/TMP/DEW/SLP`) remain implemented and tested. | None newly identified. |
| 04 Additional | Existing Part 4 coverage and prior gaps are already tracked in `NEXT_STEPS.md`. | None newly identified beyond existing backlog. |
| 05 Weather Occurrence | Existing AT/AU/AW/AX/AY/AZ implementation remains aligned with prior tracking. | None newly identified. |
| 06 CRN Unique | Existing CRN groups remain implemented as previously documented. | None newly identified. |
| 07 Network Metadata | `CO1` and `CO2-CO9` rule families exist. | **New (shared identifier-format issue):** malformed token shapes are accepted (e.g., `CO02`) even though identifiers are fixed-length 3-char tokens in spec (`isd-format-document-parts/part-07-network-metadata.md:5`, `isd-format-document-parts/part-07-network-metadata.md:43`). |
| 08 CRN Control | `CR1` remains implemented and tested. | None newly identified. |
| 09 Subhourly Temperature | `CT1-CT3` support remains in place. | None newly identified beyond existing backlog. |
| 10 Hourly Temperature | `CU1-CU3` support remains in place. | None newly identified beyond existing backlog. |
| 11 Hourly Temp Extreme | `CV1-CV3` support remains in place. | None newly identified beyond existing backlog. |
| 12 Subhourly Wetness | `CW1` support remains in place. | None newly identified. |
| 13 Geonor Summary | `CX1-CX3` support remains in place. | None newly identified beyond existing backlog. |
| 14 Runway Visual Range | `ED1` support remains in place. | None newly identified. |
| 15 Cloud and Solar | `GA/GD/GE1/GF1/GG/GH` remain implemented with prior tracked gaps. | None newly identified beyond existing backlog. |
| 16 Sunshine | `GJ/GK/GL` support remains in place. | None newly identified. |
| 17 Solar Irradiance | `GM/GN` support remains in place. | None newly identified beyond existing backlog. |
| 18 Net Solar Radiation | `GO` support remains in place. | None newly identified beyond existing backlog. |
| 19 Modeled Solar Irradiance | `GP1` support remains in place. | None newly identified. |
| 20 Hourly Solar Angle | `GQ1` support remains in place. | None newly identified beyond existing backlog. |
| 21 Hourly Extraterrestrial Radiation | `GR1` support remains in place. | None newly identified beyond existing backlog. |
| 22 Hail | `HAIL` support remains in place. | None newly identified. |
| 23 Ground Surface | `IA/IB/IC` support remains in place. | None newly identified beyond existing backlog. |
| 24 Temperature | `KA/KB/KC/KD/KE/KF/KG` support remains in place. | None newly identified beyond existing backlog. |
| 25 Sea Surface Temperature | `SA1` support remains in place. | None newly identified. |
| 26 Soil Temperature | `ST1` support remains in place. | None newly identified beyond existing backlog. |
| 27 Pressure | `MA/MD/ME/MF/MG/MH/MK` support remains in place. | None newly identified beyond existing backlog. |
| 28 Weather Extended | `MV/MW` support remains in place. | None newly identified beyond existing backlog. |
| 29 Wind | `OA/OB/OC/OD/OE/RH` support remains in place. | **New (shared identifier-format issue):** malformed suffix width/shape forms (e.g., `OA01`, `RH0001`) are accepted although identifiers are fixed-width 3-char tokens (`isd-format-document-parts/part-29-wind-data.md:5`, `isd-format-document-parts/part-29-wind-data.md:9`, `isd-format-document-parts/part-29-wind-data.md:245`, `isd-format-document-parts/part-29-wind-data.md:311`, `isd-format-document-parts/part-29-wind-data.md:387`). |
| 30 Marine | Marine groups, EQD, REM, QNN support remain in place with prior tracked gaps. | **New (shared identifier-format issue):** malformed EQD identifiers (e.g., `Q100`, `Q01A`, `N001`) are accepted, despite Part 30 defining `Q01-Q99`/`N01-N99` as 3-char identifiers (`isd-format-document-parts/part-30-marine-data.md:790`, `isd-format-document-parts/part-30-marine-data.md:794`, `isd-format-document-parts/part-30-marine-data.md:803`). |

### Net-New Misalignments (Third Pass)

1. Identifier token format is not strictly enforced for currently-gated families (Parts 7/29/30 + EQD).
   - NOAA docs define these identifiers as fixed-length 3-character tokens with explicit suffix ranges (`CO2-CO9`, `OA1-OA3`, `OD1-OD3`, `OE1-OE3`, `RH1-RH3`, `Q01-Q99`, `N01-N99`).
   - Current validation accepts malformed variants because:
     - repeated-ID checks allow any numeric suffix width (`int(suffix)` only), and
     - prefix fallback in `get_field_rule` matches with `startswith(...)`.
   - Relevant code: `src/noaa_climate_data/constants.py:3162`, `src/noaa_climate_data/constants.py:3172`, `src/noaa_climate_data/constants.py:3182`.
   - Reproduced with `get_field_rule(...)` / `clean_value_quality(...)`: `CO02`, `OA01`, `RH0001`, `Q100`, `Q01A`, `N001` currently parse as valid.

2. Part 2 split `DATE`+`TIME` semantics are lost when deriving hourly timestamps.
   - Part 2 defines date and time as separate control fields (`POS: 16-23` and `POS: 24-27`) (`isd-format-document-parts/part-02-control-data-section.md:32`, `isd-format-document-parts/part-02-control-data-section.md:39`).
   - Current `_extract_time_columns` derives datetime from `DATE` alone and sets `Hour` from that timestamp; `TIME` is not fused into datetime.
   - Relevant code: `src/noaa_climate_data/pipeline.py:404`.
   - Reproduced: with `DATE='20240101'` and `TIME='2300'`, parsed `Hour` remains `0` instead of `23`.

### Added to Next Steps (Third Pass)

Added new checklist items in `NEXT_STEPS.md`:

- Strict identifier token-shape enforcement for already-gated Part 7/29/30 + EQD families (`NEXT_STEPS.md:109`).
- Use control `DATE`+`TIME` jointly during timestamp/hour derivation (`NEXT_STEPS.md:114`).
- Regression tests for both new gaps (`NEXT_STEPS.md:178`).

## Fourth Pass: New Misalignments Beyond Current NEXT_STEPS

Date: 2026-02-15 (fourth pass)

Scope for this pass:

- Re-read `part-01` through `part-30` one-by-one.
- Re-checked parsing behavior and tests:
  - `src/noaa_climate_data/cleaning.py`
  - `src/noaa_climate_data/constants.py`
  - `tests/test_cleaning.py`
- Filtered out items already present in `NEXT_STEPS.md`.

### Part-by-Part Snapshot (Fourth Pass)

| Part | Alignment | New misalignment in this pass |
| --- | --- | --- |
| 01 Preface | Existing parser/readme structure remains aligned with document framing. | None newly identified. |
| 02 Control | Control normalization for `DATE`/`TIME`/lat/lon/elevation/source/report/QC remains implemented. | **Cross-cutting parser strictness gap applies:** parser expansion is driven by comma presence, not NOAA identifier allowlist. |
| 03 Mandatory | `WND/CIG/VIS/TMP/DEW/SLP` parsing, quality gating, and key edge rules remain implemented. | **Cross-cutting structural gaps apply:** strict arity and fixed-width token compliance are not enforced. |
| 04 Additional | Additional groups are broadly implemented with sentinel/quality handling and many range checks. | **Cross-cutting structural gap applies:** exact expected part-count per identifier is not enforced. |
| 05 Weather Occurrence | `AT/AU/AW/AX/AY/AZ` support remains implemented. | Cross-cutting arity/width strictness gap applies. |
| 06 CRN Unique | `CB/CF/CG/CH/CI/CN` support remains implemented. | Cross-cutting arity/width strictness gap applies. |
| 07 Network Metadata | `CO*/CR1/CT*/CU*/CV*/CW1/CX*` support remains implemented. | Cross-cutting arity/width strictness gap applies. |
| 08 CRN Control | `CR1` support remains implemented. | Cross-cutting arity/width strictness gap applies. |
| 09 Subhourly Temperature | `CT1-CT3` support remains implemented. | Cross-cutting arity/width strictness gap applies. |
| 10 Hourly Temperature | `CU1-CU3` support remains implemented. | Cross-cutting arity/width strictness gap applies. |
| 11 Hourly Temperature Extreme | `CV1-CV3` support remains implemented. | Cross-cutting arity/width strictness gap applies. |
| 12 Subhourly Wetness | `CW1` support remains implemented. | Cross-cutting arity/width strictness gap applies. |
| 13 Geonor Summary | `CX1-CX3` support remains implemented. | Cross-cutting arity/width strictness gap applies. |
| 14 Runway Visual Range | `ED1` support remains implemented. | Cross-cutting arity/width strictness gap applies. |
| 15 Cloud and Solar | `GA/GD/GE1/GF1/GG/GH1` support remains implemented. | Cross-cutting arity/width strictness gap applies. |
| 16 Sunshine | `GJ/GK/GL` support remains implemented. | Cross-cutting arity/width strictness gap applies. |
| 17 Solar Irradiance | `GM/GN` support remains implemented. | Cross-cutting arity/width strictness gap applies. |
| 18 Net Solar Radiation | `GO` support remains implemented. | Cross-cutting arity/width strictness gap applies. |
| 19 Modeled Solar Irradiance | `GP1` support remains implemented. | Cross-cutting arity/width strictness gap applies. |
| 20 Hourly Solar Angle | `GQ1` support remains implemented. | Cross-cutting arity/width strictness gap applies. |
| 21 Hourly Extraterrestrial Radiation | `GR1` support remains implemented. | Cross-cutting arity/width strictness gap applies. |
| 22 Hail | `HAIL` support remains implemented. | Cross-cutting arity/width strictness gap applies. |
| 23 Ground Surface | `IA/IB/IC` support remains implemented. | Cross-cutting arity/width strictness gap applies. |
| 24 Temperature | `KA/KB/KC/KD/KE/KF/KG` support remains implemented. | Cross-cutting arity/width strictness gap applies. |
| 25 Sea Surface Temperature | `SA1` support remains implemented. | Cross-cutting arity/width strictness gap applies. |
| 26 Soil Temperature | `ST1` support remains implemented. | Cross-cutting arity/width strictness gap applies. |
| 27 Pressure | `MA/MD/ME/MF/MG/MH/MK` support remains implemented. | Cross-cutting arity/width strictness gap applies. |
| 28 Weather Extended | `MV/MW` support remains implemented. | Cross-cutting arity/width strictness gap applies. |
| 29 Wind | `OA/OB/OC/OD/OE/RH` support remains implemented. | Cross-cutting arity/width strictness gap applies. |
| 30 Marine | `UA/UG/WA/WD/WG/WJ/EQD/REM/QNN` support remains implemented. | Cross-cutting arity/width strictness gap applies. |

### Net-New Misalignments (Fourth Pass)

1. Comma-driven expansion is not restricted to known NOAA field identifiers.
   - NOAA sections are identifier-defined (`ADD`, `AA1-AA4`, etc.) and fixed-format (`isd-format-document-parts/part-04-additional-data-section.md:25`, `isd-format-document-parts/part-04-additional-data-section.md:37`; similarly `OA1-OA3` in `isd-format-document-parts/part-29-wind-data.md:5`, `isd-format-document-parts/part-29-wind-data.md:9`).
   - Current cleaner expands *any* object column with commas (`src/noaa_climate_data/cleaning.py:506`, `src/noaa_climate_data/cleaning.py:511`, `src/noaa_climate_data/cleaning.py:519`), and unknown prefixes are still parsed via generic expansion path (`src/noaa_climate_data/cleaning.py:362`, `src/noaa_climate_data/cleaning.py:371`, `src/noaa_climate_data/cleaning.py:373`).
   - Reproduced: `clean_noaa_dataframe(... {'NAME': 'CHARLOTTESVILLE, VA US'})` creates synthetic `NAME__part1`/`NAME__part2` columns (and drops raw `NAME` when `keep_raw=False`).

2. Field arity (expected part count) is not enforced for known identifiers.
   - Spec structures are fixed by position/field definitions (for example WND spans fixed components at `POS: 61-70` in `isd-format-document-parts/part-03-mandatory-data-section.md:22`, `isd-format-document-parts/part-03-mandatory-data-section.md:76`; Part 4 groups define explicit `FLD LEN` and item counts in `isd-format-document-parts/part-04-additional-data-section.md:33`, `isd-format-document-parts/part-04-additional-data-section.md:43`).
   - Current logic accepts malformed/truncated payloads because any non-2-part input is expanded without expected-count validation (`src/noaa_climate_data/cleaning.py:370`, `src/noaa_climate_data/cleaning.py:371`, `src/noaa_climate_data/cleaning.py:373`), and missing quality parts return `None` instead of hard failure (`src/noaa_climate_data/cleaning.py:75`, `src/noaa_climate_data/cleaning.py:77`).
   - Reproduced: `TMP='+0250'` and `WND='180,1,N,0050'` are accepted and emit partial parsed values.

3. Fixed-width token-format enforcement is limited to Part 4 additional numeric prefixes.
   - NOAA docs use fixed-width fields broadly (for example WND direction/speed widths in `isd-format-document-parts/part-03-mandatory-data-section.md:22`, `isd-format-document-parts/part-03-mandatory-data-section.md:60`; Part 4 explicitly states per-item `FLD LEN` in `isd-format-document-parts/part-04-additional-data-section.md:43`, `isd-format-document-parts/part-04-additional-data-section.md:51`).
   - Current width enforcement is scoped only through `_additional_data_fixed_width` and `ADDITIONAL_DATA_PREFIXES` (`src/noaa_climate_data/cleaning.py:101`, `src/noaa_climate_data/cleaning.py:107`, `src/noaa_climate_data/cleaning.py:309`).
   - Reproduced: shortened non-conformant tokens like `WND='1,1,N,5,1'` and `TMP='250,1'` are accepted and scaled into valid outputs.

### Test Coverage Gap (Fourth Pass)

- `tests/test_cleaning.py` does not currently include regression cases for:
  - unknown comma-bearing metadata columns being expanded,
  - malformed/truncated part-count payload rejection,
  - non-conformant fixed-width token rejection outside Part 4 additional numeric fields.

### Added to Next Steps (Fourth Pass)

Added checklist items in `NEXT_STEPS.md` for:

- strict per-identifier arity enforcement,
- fixed-width token-format enforcement outside Part 4 additional numerics,
- restricting comma expansion to known NOAA identifiers,
- regression tests for the above parser-structure strictness gaps.

## Fifth Pass: New Misalignments Beyond Current NEXT_STEPS

Date: 2026-02-15 (fifth pass)

Scope for this pass:

- Re-read `part-01` through `part-30` one-by-one.
- Re-validated parser behavior and tests with emphasis on data-cleaning type semantics:
  - `src/noaa_climate_data/cleaning.py`
  - `src/noaa_climate_data/constants.py`
  - `tests/test_cleaning.py`
- Filtered out all issues already tracked in `NEXT_STEPS.md`.

### Part-by-Part Snapshot (Fifth Pass)

| Part | Alignment | New misalignment in this pass |
| --- | --- | --- |
| 01 Preface | Existing dataset framing and section model remain aligned. | None newly identified. |
| 02 Control | Control-field normalization (DATE/TIME/lat/lon/source/report/QC) remains implemented. | None newly identified. |
| 03 Mandatory | Mandatory section parsing remains implemented with prior constraints. | **New:** numeric-domain parts can retain malformed non-numeric tokens as raw strings instead of being nulled/rejected. |
| 04 Additional | Additional section remains broadly implemented with prior tracked gaps. | None newly identified beyond existing backlog. |
| 05 Weather Occurrence | AT/AU/AW/AX/AY/AZ support remains implemented. | **New (shared categorical-coercion issue):** numeric-like code-domain values are emitted as floats, losing fixed-width code semantics. |
| 06 CRN Unique | CB/CF/CG/CH/CI/CN support remains implemented. | **New:** CRN QC code `9` (“Missing”) is treated as acceptable for value retention instead of nulling paired values. |
| 07 Network Metadata | CO/CR/CT/CU/CV/CW/CX support remains implemented. | None newly identified beyond existing backlog. |
| 08 CRN Control | CR1 support remains implemented. | None newly identified beyond existing backlog. |
| 09 Subhourly Temperature | CT1-CT3 support remains implemented. | None newly identified beyond existing backlog. |
| 10 Hourly Temperature | CU1-CU3 support remains implemented. | None newly identified beyond existing backlog. |
| 11 Hourly Temperature Extreme | CV1-CV3 support remains implemented. | None newly identified beyond existing backlog. |
| 12 Subhourly Wetness | CW1 support remains implemented. | None newly identified beyond existing backlog. |
| 13 Geonor Summary | CX1-CX3 support remains implemented. | None newly identified beyond existing backlog. |
| 14 Runway Visual Range | ED1 support remains implemented. | None newly identified beyond existing backlog. |
| 15 Cloud and Solar | GA/GD/GE/GF/GG/GH support remains implemented. | None newly identified beyond existing backlog. |
| 16 Sunshine | GJ/GK/GL support remains implemented. | None newly identified beyond existing backlog. |
| 17 Solar Irradiance | GM/GN support remains implemented. | None newly identified beyond existing backlog. |
| 18 Net Solar Radiation | GO support remains implemented. | None newly identified beyond existing backlog. |
| 19 Modeled Solar Irradiance | GP1 support remains implemented. | None newly identified beyond existing backlog. |
| 20 Hourly Solar Angle | GQ1 support remains implemented. | None newly identified beyond existing backlog. |
| 21 Hourly Extraterrestrial Radiation | GR1 support remains implemented. | None newly identified beyond existing backlog. |
| 22 Hail | HAIL support remains implemented. | None newly identified beyond existing backlog. |
| 23 Ground Surface | IA/IB/IC support remains implemented. | None newly identified beyond existing backlog. |
| 24 Temperature | KA/KB/KC/KD/KE/KF/KG support remains implemented. | None newly identified beyond existing backlog. |
| 25 Sea Surface Temperature | SA1 support remains implemented. | None newly identified beyond existing backlog. |
| 26 Soil Temperature | ST1 support remains implemented. | None newly identified beyond existing backlog. |
| 27 Pressure | MA/MD/ME/MF/MG/MH/MK support remains implemented. | None newly identified beyond existing backlog. |
| 28 Weather Extended | MV/MW support remains implemented. | **New (shared categorical-coercion issue):** weather code fields defined as 2-char ASCII codes are emitted as floats when numeric-like. |
| 29 Wind | OA/OB/OC/OD/OE/RH support remains implemented. | None newly identified beyond existing backlog. |
| 30 Marine | UA/UG/WA/WD/WG/WJ/EQD/REM/QNN support remains implemented. | **New:** EQD original-value text loses 6-char ASCII fidelity when numeric-like (leading zeros/sign formatting dropped by float coercion). |

### Net-New Misalignments (Fifth Pass)

1. Numeric-domain parts can preserve malformed text instead of enforcing numeric compliance.
   - NOAA numeric parts are documented as numeric-only domains (e.g., WND direction/speed in Part 3: `DOM` numeric characters) (`isd-format-document-parts/part-03-mandatory-data-section.md:27`, `isd-format-document-parts/part-03-mandatory-data-section.md:65`).
   - Current expansion stores raw token text whenever float parsing fails (`src/noaa_climate_data/cleaning.py:328`, `src/noaa_climate_data/cleaning.py:329`), including numeric-designated parts.
   - Reproduced: `clean_value_quality("A90,1,N,0050,1", "WND")` emits `WND__part1="A90"` and `clean_value_quality("180,1,N,0A50,1", "WND")` emits `WND__part4="0A50"` instead of null/reject.

2. Part 30 EQD original value text is not preserved as 6-character ASCII text when numeric-like.
   - Part 30 defines EQD original value as `FLD LEN: 6` with ASCII-domain text (`isd-format-document-parts/part-30-marine-data.md:808`, `isd-format-document-parts/part-30-marine-data.md:811`, `isd-format-document-parts/part-30-marine-data.md:1010`, `isd-format-document-parts/part-30-marine-data.md:1013`).
   - EQD part 1 is configured as categorical (`src/noaa_climate_data/constants.py:428`, `src/noaa_climate_data/constants.py:441`), but generic parse/coercion converts numeric-like tokens to float (`src/noaa_climate_data/cleaning.py:220`, `src/noaa_climate_data/cleaning.py:222`, `src/noaa_climate_data/cleaning.py:339`).
   - Reproduced: `clean_value_quality("001234,1,APC3", "Q01")` emits `Q01__part1=1234.0`, losing leading zeros from the original 6-char text.

3. Numeric-like categorical code fields lose fixed-width code semantics through float coercion.
   - NOAA code fields are specified as fixed-width ASCII codes (for example Part 5/28 weather code fields are `FLD LEN: 2` with explicit `00..` code domains) (`isd-format-document-parts/part-05-weather-occurrence-data.md:31`, `isd-format-document-parts/part-05-weather-occurrence-data.md:33`, `isd-format-document-parts/part-28-weather-occurrence-data-extended.md:72`, `isd-format-document-parts/part-28-weather-occurrence-data-extended.md:75`).
   - Current parser converts any numeric-like token to float regardless of categorical kind (`src/noaa_climate_data/cleaning.py:220`, `src/noaa_climate_data/cleaning.py:222`, `src/noaa_climate_data/cleaning.py:339`).
   - Existing tests currently encode float expectations for such codes (e.g., `AT1__part2 == 1.0`, `AW1__part1 == 99.0`) (`tests/test_cleaning.py:1069`, `tests/test_cleaning.py:1078`), confirming representation drift from fixed-width code semantics.

4. Part 6 CRN QC code `9` (“Missing”) does not null associated value components.
   - Part 6 CRN QC definitions repeatedly specify `1 = Passed`, `3 = Failed`, `9 = Missing` (e.g., CB/CF/CG/CH sections) (`isd-format-document-parts/part-06-climate-reference-network-unique-data.md:36`, `isd-format-document-parts/part-06-climate-reference-network-unique-data.md:38`, `isd-format-document-parts/part-06-climate-reference-network-unique-data.md:80`, `isd-format-document-parts/part-06-climate-reference-network-unique-data.md:82`, `isd-format-document-parts/part-06-climate-reference-network-unique-data.md:117`, `isd-format-document-parts/part-06-climate-reference-network-unique-data.md:119`, `isd-format-document-parts/part-06-climate-reference-network-unique-data.md:174`, `isd-format-document-parts/part-06-climate-reference-network-unique-data.md:176`).
   - Current rules allow `{1,3,9}` as valid QC-domain values (`src/noaa_climate_data/constants.py:1526`, `src/noaa_climate_data/constants.py:1544`, `src/noaa_climate_data/constants.py:1562`, `src/noaa_climate_data/constants.py:1586`, `src/noaa_climate_data/constants.py:2968`, `src/noaa_climate_data/constants.py:3001`), and value gating only drops on out-of-domain quality (`src/noaa_climate_data/cleaning.py:286`, `src/noaa_climate_data/cleaning.py:287`, `src/noaa_climate_data/cleaning.py:288`).
   - Reproduced: `clean_value_quality("05,+000123,9,0", "CB1")` retains `CB1__part2=12.3` even though QC is `9` (missing).

### Test Coverage Gap (Fifth Pass)

- `tests/test_cleaning.py` does not currently include regression cases for:
  - malformed alpha tokens in numeric-domain parts falling through as raw strings,
  - EQD original-value text fidelity (6-char text preservation, including leading zeros),
  - CRN QC `9` missing-semantics behavior for associated values.

### Added to Next Steps (Fifth Pass)

Added checklist items in `NEXT_STEPS.md` for:

- strict numeric-domain type enforcement (no raw-text fallback in numeric parts),
- EQD original-value text fidelity preservation,
- categorical code representation preservation for fixed-width code fields,
- CRN QC `9` missing-semantics enforcement,
- targeted regression tests for these cases.

## Sixth Pass: New Misalignments Beyond Current NEXT_STEPS

Date: 2026-02-20 (sixth pass)

Scope for this pass:

- Re-read `part-01` through `part-30` sequentially (one part at a time).
- Re-checked control normalization and pipeline timestamp derivation:
  - `src/noaa_climate_data/cleaning.py`
  - `src/noaa_climate_data/pipeline.py`
  - `tests/test_cleaning.py`
- Filtered out issues already tracked in `NEXT_STEPS.md`.

### Part-by-Part Snapshot (Sixth Pass)

| Part | Alignment | New misalignment in this pass |
| --- | --- | --- |
| 01 Preface | Existing section model and dataset framing remain aligned. | None newly identified. |
| 02 Control | Core control normalization (`DATE`/`TIME`/lat/lon/elevation/source/report/QC) remains present. | **New:** longitude lower bound is off by 0.001 degrees; **new:** pipeline `DATE_PARSED` fallback re-accepts non-`YYYYMMDD` dates; **new:** `CALL_SIGN` fixed-width/domain constraints are not enforced. |
| 03 Mandatory | Mandatory groups and core parsing behavior remain implemented. | None newly identified beyond existing backlog. |
| 04 Additional | Additional groups remain implemented with prior tracked gaps. | None newly identified beyond existing backlog. |
| 05 Weather Occurrence | AT/AU/AW/AX/AY/AZ remain implemented. | None newly identified beyond existing backlog. |
| 06 CRN Unique | CB/CF/CG/CH/CI/CN remain implemented. | None newly identified beyond existing backlog. |
| 07 Network Metadata | CO/CR/CT/CU/CV/CW/CX remain implemented. | None newly identified beyond existing backlog. |
| 08 CRN Control | CR1 remains implemented. | None newly identified beyond existing backlog. |
| 09 Subhourly Temperature | CT1-CT3 remain implemented. | None newly identified beyond existing backlog. |
| 10 Hourly Temperature | CU1-CU3 remain implemented. | None newly identified beyond existing backlog. |
| 11 Hourly Temperature Extreme | CV1-CV3 remain implemented. | None newly identified beyond existing backlog. |
| 12 Subhourly Wetness | CW1 remains implemented. | None newly identified beyond existing backlog. |
| 13 Geonor Summary | CX1-CX3 remain implemented. | None newly identified beyond existing backlog. |
| 14 Runway Visual Range | ED1 remains implemented. | None newly identified beyond existing backlog. |
| 15 Cloud and Solar | GA/GD/GE1/GF1/GG/GH1 remain implemented. | None newly identified beyond existing backlog. |
| 16 Sunshine | GJ/GK/GL remain implemented. | None newly identified beyond existing backlog. |
| 17 Solar Irradiance | GM1/GN1 remain implemented. | None newly identified beyond existing backlog. |
| 18 Net Solar Radiation | GO1 remains implemented. | None newly identified beyond existing backlog. |
| 19 Modeled Solar Irradiance | GP1 remains implemented. | None newly identified beyond existing backlog. |
| 20 Hourly Solar Angle | GQ1 remains implemented. | None newly identified beyond existing backlog. |
| 21 Hourly Extraterrestrial Radiation | GR1 remains implemented. | None newly identified beyond existing backlog. |
| 22 Hail | HAIL remains implemented. | None newly identified beyond existing backlog. |
| 23 Ground Surface | IA/IB/IC remain implemented. | None newly identified beyond existing backlog. |
| 24 Temperature | KA/KB/KC/KD/KE/KF/KG remain implemented. | None newly identified beyond existing backlog. |
| 25 Sea Surface Temperature | SA1 remains implemented. | None newly identified beyond existing backlog. |
| 26 Soil Temperature | ST1 remains implemented. | None newly identified beyond existing backlog. |
| 27 Pressure | MA/MD/ME/MF/MG/MH/MK remain implemented. | None newly identified beyond existing backlog. |
| 28 Weather Extended | MV/MW remain implemented. | None newly identified beyond existing backlog. |
| 29 Wind | OA/OB/OC/OD/OE/RH remain implemented. | None newly identified beyond existing backlog. |
| 30 Marine | UA/UG/WA/WD/WG/WJ/EQD/REM/QNN remain implemented. | None newly identified beyond existing backlog. |

### Net-New Misalignments (Sixth Pass)

1. Part 2 longitude minimum is too permissive by one scaled unit.
   - Spec sets longitude to `MIN: -179999` and `MAX: +180000` (scaled by 1000), i.e. `[-179.999, +180.000]` (`isd-format-document-parts/part-02-control-data-section.md:102`, `isd-format-document-parts/part-02-control-data-section.md:106`, `isd-format-document-parts/part-02-control-data-section.md:107`).
   - Current normalization uses `between(-180.0, 180.0)` (`src/noaa_climate_data/cleaning.py:450`), so `-180.000` is retained even though it is below spec minimum.
   - Reproduced: `clean_noaa_dataframe(pd.DataFrame({'LONGITUDE':['-180.000']}))` keeps `-180.000`.

2. Part 2 strict `DATE` format enforcement is bypassed in pipeline processing.
   - Spec defines control date as numeric `YYYYMMDD` (`isd-format-document-parts/part-02-control-data-section.md:32`, `isd-format-document-parts/part-02-control-data-section.md:36`).
   - Cleaning correctly rejects ISO timestamps (`tests/test_cleaning.py:1890`), but pipeline precomputes `DATE_PARSED` from raw `DATE` (`src/noaa_climate_data/pipeline.py:742`) and `_extract_time_columns` backfills `DATE` from that fallback (`src/noaa_climate_data/pipeline.py:407`, `src/noaa_climate_data/pipeline.py:409`).
   - Reproduced: `process_location_from_raw` accepts `DATE='2024-01-01T01:00:00Z'` and emits `Hour=1`, despite Part 2 format rules.

3. Part 2 `CALL_SIGN` field-width/domain constraints are not enforced.
   - Spec defines call letters at `POS: 52-56` (5-character field) with ASCII-domain text and `99999` missing (`isd-format-document-parts/part-02-control-data-section.md:173`, `isd-format-document-parts/part-02-control-data-section.md:174`, `isd-format-document-parts/part-02-control-data-section.md:177`).
   - Current logic only strips whitespace and nulls sentinel/blank values (`src/noaa_climate_data/cleaning.py:464`, `src/noaa_climate_data/cleaning.py:466`), allowing non-5-character values through.
   - Reproduced: values like `"A"` and `"@@@@@@"` survive normalization.

### Test Coverage Gap (Sixth Pass)

- `tests/test_cleaning.py` currently lacks regression cases for:
  - Part 2 longitude lower-bound edge (`-180.000` should null; `-179.999` should pass),
  - `CALL_SIGN` fixed-width/domain validation,
  - pipeline-level rejection of non-`YYYYMMDD` control dates when using `process_location_from_raw`.

### Added to Next Steps (Sixth Pass)

Added checklist items in `NEXT_STEPS.md` for:

- exact Part 2 longitude lower-bound enforcement (`-179.999` minimum),
- preventing `DATE_PARSED` fallback from bypassing strict control-date format rules,
- enforcing Part 2 `CALL_SIGN` field-width/domain constraints,
- regression tests for those three gaps.
