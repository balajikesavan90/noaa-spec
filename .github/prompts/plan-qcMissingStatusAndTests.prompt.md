# Plan: Add MISSING status to QC signals and expand test coverage

Enhance the existing QC signal system to distinguish intentional missing data (sentinels) from invalid/bad data by introducing a "MISSING" status. Add comprehensive test coverage for all specified fields (OC1, MA1, GE1/GF1/GG, GH1, KA/KB) to validate the enhanced QC logic.

**Context:** The QC infrastructure is fully operational ([_compute_qc_signals](src/noaa_spec/cleaning.py#L462-L505), emission at [value/quality fields](src/noaa_spec/cleaning.py#L654-L665) and [multi-part fields](src/noaa_spec/cleaning.py#L435-L443), row metrics at [clean_noaa_dataframe](src/noaa_spec/cleaning.py#L853-L860)). Currently, sentinel values are marked as `qc_status="INVALID"` with `qc_reason="SENTINEL_MISSING"`. This change provides semantic clarity: **MISSING** = no data collected (sentinel), **INVALID** = data collected but problematic (range/quality/format violations).

## Steps

### 1. Update [constants.py](src/noaa_spec/constants.py#L469-L476): Add "MISSING" to `QC_STATUS_VALUES`

- Change line 469: `QC_STATUS_VALUES = frozenset({"PASS", "INVALID", "MISSING"})`
- Update documentation comments to clarify: MISSING for sentinels, INVALID for range/quality/format failures

### 2. Modify [_compute_qc_signals](src/noaa_spec/cleaning.py#L462-L505) in cleaning.py: Return "MISSING" status when `is_sentinel=True`

- Current logic: `if is_sentinel: return False, "INVALID", "SENTINEL_MISSING"`
- Change to: `if is_sentinel: return False, "MISSING", "SENTINEL_MISSING"`
- Update docstring examples to reflect new behavior (line 492: `(False, 'MISSING', 'SENTINEL_MISSING')`)
- Ensure priority order remains: `bad_quality > is_sentinel > out_of_range`

### 3. Update existing QC tests in [TestQCSignalsValueQualityFields](tests/test_cleaning.py#L2561-L2635)

- Line 2604: Change `test_oc1_missing_sentinel` assertion from `"INVALID"` to `"MISSING"`
- Scan [TestQCSignalsMultipartFields](tests/test_cleaning.py#L2637-L2734) and [TestQCSignalsRegressions](tests/test_cleaning.py#L2736-L2799) for any sentinel assertions
- Update [test row-level metrics](tests/test_cleaning.py#L2692-L2733) if they reference INVALID for sentinels

### 4. Add comprehensive QC tests in new test class `TestQCSignalsComprehensive` (after line 2799)

- **Per-field test groups**: OC1 (already covered, update), MA1, GE1, GF1, GG*, GH*, KA*, KB*
- **Test matrix for each field's numeric parts** (5 tests per numeric output):
  - **PASS**: In-range value + allowed quality → `qc_pass=True, status="PASS", reason=None`
  - **OUT_OF_RANGE**: Value just below `min_value` or above `max_value` → `qc_pass=False, status="INVALID", reason="OUT_OF_RANGE"`
  - **SENTINEL_MISSING**: Field-specific sentinel (e.g., "99999" for MA1 part 1) → `qc_pass=False, status="MISSING", reason="SENTINEL_MISSING"`
  - **BAD_QUALITY_CODE**: Quality code outside `allowed_quality` → `qc_pass=False, status="INVALID", reason="BAD_QUALITY_CODE"`
  - **MALFORMED_TOKEN**: Malformed numeric (non-sentinel, strict mode) → `qc_pass=False, status="INVALID", reason="MALFORMED_TOKEN"`

- **Field-specific details**:
  - **MA1**: Test both pressure parts (altimeter part1, station part3) separately with their unique ranges/sentinels
  - **GE1**: Test parts 3-4 (cloud heights, numeric, sentinel "99999", range -400 to 15000)
  - **GF1**: Test part 8 (low cloud base height, sentinel "99999", quality at part 9, range -400 to 15000)
  - **GG***: Test part 3 (cloud layer base, sentinel "99999", quality at part 4, range -400 to 35000); use "GG1" or "GG2" as prefix
  - **GH***: Test parts 1,4,7,10 (irradiance values, sentinel "99999", quality at parts 2,5,8,11, range 0 to 99998, scale 0.1); use "GH1" as prefix
  - **KA***: Test parts 1,3 (period & temperature, sentinels "999"/"9999", quality at part 4 for temp, distinct ranges); use "KA1" or "KA2"
  - **KB***: Test parts 1,3 (period & temperature, sentinels "999"/"9999", quality at part 4 for temp, scale 0.01 for temp); use "KB1"

- **Row-level metrics tests**:
  - Mixed `qc_pass` values (some True, some False) → `row_has_any_usable_metric=True`, correct `usable_metric_count` and `usable_metric_fraction`
  - All `qc_pass=False` → `row_has_any_usable_metric=False`, `usable_metric_count=0`, `fraction=0.0`
  - No QC columns present → `fraction` is `NaN` (verify current behavior at [line 859](src/noaa_spec/cleaning.py#L859): `total_qc_columns or pd.NA`)

### 5. Validation sweep: Grep for hardcoded `"INVALID"` assertions tied to sentinels

- Search pattern: `SENTINEL_MISSING.*INVALID` in tests to catch missed updates
- Check documentation/docstrings that reference the two-value QC_STATUS_VALUES

## Verification

Run full test suite and new tests:
```bash
poetry run pytest tests/test_cleaning.py::TestQCSignalsValueQualityFields -v
poetry run pytest tests/test_cleaning.py::TestQCSignalsComprehensive -v
poetry run pytest tests/test_cleaning.py -v  # Full suite
```

Confirm:
- All existing tests pass with MISSING status for sentinels
- New field-specific QC tests cover PASS/OUT_OF_RANGE/SENTINEL/BAD_QUALITY/MALFORMED for OC1, MA1, GE1, GF1, GG*, GH*, KA*, KB*
- Row-level metrics accurately reflect usable data proportions
- No breaking changes to existing column names or data values (backwards compatible: only adds semantic distinction between INVALID and MISSING)

## Decisions

- **MISSING vs INVALID**: MISSING used exclusively for sentinel values (intentional absence); INVALID used for range, quality, and format violations (data quality problems)
- **Priority order preserved**: BAD_QUALITY_CODE > SENTINEL_MISSING > OUT_OF_RANGE (first failure wins)
- **Multi-part fields**: QC columns emitted only for numeric parts; categorical and quality parts omitted (existing behavior)
- **Backwards compatibility**: All existing columns preserved; only QC status values change from INVALID→MISSING for sentinel cases
