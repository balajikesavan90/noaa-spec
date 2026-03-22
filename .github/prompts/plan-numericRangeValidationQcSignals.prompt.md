# Plan: Numeric Range Validation & QC Signal Derivation

**TL;DR**
Extend the existing `FieldPartRule` range infrastructure (which already has `min_value`/`max_value`) to output accompanying QC signal columns (`*_qc_pass`, `*_qc_status`, `*_qc_reason`) for every numeric field. Add row-level usability metrics computed from all fields that have QC columns. Range validation (pre-scale) is already implemented; this work adds the derived usability signals and expands field coverage. Moderate first scope: OC1 + MA1 (wind/pressure) plus GE1/GF1/GG (cloud heights), GH1 (solar), and KA/KB (temperatures) to demonstrate the full pattern across diverse field types.

## Steps

### Phase 1: Data Model & Constants

1. **Add QC column naming constants to `src/noaa_spec/constants.py`**
   - Add a new dict `QC_STATUS_VALUES` with enum values: `{"PASS", "INVALID", "MISSING"}` (INVALID covers both bad quality and out-of-range; sentinel/missing tracked separately for clarity)
   - Add a companion dict `QC_REASON_ENUM` with detailed reason strings: `"OUT_OF_RANGE"`, `"BAD_QUALITY_CODE"`, `"SENTINEL_MISSING"`, `"MALFORMED_TOKEN"`, `None` (for PASS)

2. **Define the metrics config constant**
   - Add `USABILITY_METRIC_INDICATORS = ["qc_pass"]` — will auto-find all fields ending in `__qc_pass` and treat those as metrics

3. **Add/verify MIN/MAX bounds for initial scope fields in `src/noaa_spec/constants.py`**
   - **OC1** (wind gust): part 3, range 0050–1100 (already defined, verify)
   - **MA1** (station pressure): part 1 numeric, range 08635–10904 (already defined, verify)
   - **GE1/GF1** (cloud base/peak heights): parts 2–4 numeric, ranges -400 to 15000/-400 to 15000
   - **GG** (cloud coverage): part 1, range 0–100
   - **GH1** (solar radiation): all 4 parts (direct/diffuse/global/net), 0–99998 with 99999 missing
   - **KA/KB** (temperature): verify ranges in constants (KA: -1100 to +6300, KB: -9900 to +6300)

### Phase 2: QC Signal Generation in Cleaning

4. **Modify `src/noaa_spec/cleaning.py` `clean_value_quality()` to emit QC columns**
   - After the existing range validation (line ~514) and scaling, before emitting `__value` and `__quality` columns:
     - Compute `has_valid_quality` = (quality is None OR quality in `allowed_quality`)
     - Compute `has_valid_range` = (numeric part is not None after range check)
     - Compute `is_missing_sentinel` = (raw normalized to all-9s before parsing)
     - Derive: `qc_pass = (has_valid_quality AND has_valid_range AND NOT is_missing)` (bool)
     - Derive: `qc_status = "PASS" if qc_pass else "INVALID"` (string)
     - Derive: `qc_reason = None if qc_pass else ("OUT_OF_RANGE" | "BAD_QUALITY_CODE" | "SENTINEL_MISSING" | "MALFORMED_TOKEN")` (string or None)
   - Emit three new columns per value/quality field:
     - `{PREFIX}__qc_pass` (bool)
     - `{PREFIX}__qc_status` (string)
     - `{PREFIX}__qc_reason` (string or None)
   - For multi-part fields (e.g., WND with 5 parts), emit QC for each numeric part **independently**

5. **Preserve raw columns as-is**
   - Keep existing `{PREFIX}__value`, `{PREFIX}__quality`, `{PREFIX}__part{N}` columns unchanged
   - Raw layer unmodified
   - QC columns are additions only

### Phase 3: Row-Level Usability Metrics

6. **Add row-level summary columns in `src/noaa_spec/cleaning.py` after `clean_noaa_dataframe()` completes**
   - After the main cleaning loop, compute derived metrics once per row:
     - Find all columns matching pattern `*__qc_pass`
     - `row_has_any_usable_metric` = (at least one `*__qc_pass` is True) (bool)
     - `usable_metric_count` = (sum of True values in all `*__qc_pass` columns) (int, ≥0)
     - `usable_metric_fraction` = `usable_metric_count / total_qc_columns_present` (float in [0.0, 1.0])
     - Emit as three new columns on the cleaned DataFrame

### Phase 4: Testing

7. **Add test suite in `tests/test_cleaning.py`**
   - **Core QC pass tests** (for each field in scope):
     - In-range value with good quality → `qc_pass=True`, `qc_status="PASS"`, `qc_reason=None`
     - Out-of-range value → `qc_pass=False`, `qc_status="INVALID"`, `qc_reason="OUT_OF_RANGE"`
     - Missing sentinel (all-9s) → `qc_pass=False`, `qc_status="INVALID"`, `qc_reason="SENTINEL_MISSING"`
     - Bad quality code → `qc_pass=False`, `qc_status="INVALID"`, `qc_reason="BAD_QUALITY_CODE"`
   - **Boundary value tests**:
     - Exactly at `min_value` → PASS
     - Exactly at `max_value` → PASS
     - Just below `min_value` → OUT_OF_RANGE
     - Just above `max_value` → OUT_OF_RANGE
   - **Row summary tests**:
     - All metrics usable → `row_has_any_usable_metric=True`, `usable_metric_fraction=1.0`
     - All metrics invalid → `row_has_any_usable_metric=False`, `usable_metric_fraction=0.0`
     - Mixed usable/invalid → `usable_metric_fraction` in (0, 1)
     - No QC columns present → `usable_metric_fraction=None` or `NaN` (define behavior)
   - **Regression tests**:
     - Existing non-QC columns unchanged
     - Raw values preserved (NOT nulled in raw layer even if out-of-range)
   - **Test fixtures**:
     - Build minimal sample CSV with OC1 + MA1 + GE1 data, various ranges
     - Use existing `_build_full_raw_dataframe()` pattern

8. **Run full test suite to verify no regressions**
   - `pytest tests/test_cleaning.py -v` (new tests)
   - `pytest tests/ -v` (full suite)

### Phase 5: Documentation & Handoff

9. **Add docstring updates**
   - Update `clean_value_quality()` docstring to document QC column emission
   - Document new constants (QC_STATUS_VALUES, QC_REASON_ENUM, USABILITY_METRIC_INDICATORS)
   - Update `clean_noaa_dataframe()` docstring to mention row-level summary columns
   - Link to this work in relevant code comments (optional)

## Verification

Run `pytest tests/test_cleaning.py::TestQcSignals -v` (or whatever test class names we use) to verify:
- ✅ In-range values produce QC columns with PASS status
- ✅ Out-of-range values produce INVALID status with OUT_OF_RANGE reason
- ✅ Sentinels produce INVALID with SENTINEL_MISSING reason
- ✅ Bad quality codes produce INVALID with BAD_QUALITY_CODE reason
- ✅ Row-level metrics correctly computed
- ✅ Existing tests still pass (no regressions)

Then spot-check cleaned output CSV:
```python
df = clean_noaa_dataframe(raw_df)
# Verify these columns exist for OC1, MA1, GE1, GF1, GG, GH1, KA, KB:
# - {field}__qc_pass, {field}__qc_status, {field}__qc_reason
# Verify row summary columns exist:
# - row_has_any_usable_metric, usable_metric_count, usable_metric_fraction
```

## Decisions

- **Pre-scale range validation** (confirmed): MIN/MAX bounds represent raw NOAA values. Validation happens before scaling. Matches current implementation and simplifies rule definitions.
- **Two-tier QC status** (confirmed): `PASS` or `INVALID`, with optional `qc_reason` column for details. Simpler than five tiers, still preserves traceability.
- **Auto-derived metrics** (confirmed): All fields with `*__qc_pass` columns automatically count toward row summaries. No hardcoded list. Scales as new fields are added.
- **Moderate scope** (confirmed): Start with OC1 + MA1 + GE1/GF1/GG + GH1 + KA/KB. Spans wind, pressure, cloud, solar, temperature domains. Validates pattern across diverse field types before expanding to full backlog (18+ parts).
- **No raw-layer mutation**: Clean layer outputs QC signals; raw DataFrame unchanged. Preserves immutability contract and aids auditing.
