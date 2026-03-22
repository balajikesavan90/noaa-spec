# Plan: Strict NOAA Parser (Gate A)

Implements parser strictness for NOAA comma-encoded field expansion by adding four validation gates: (A1) identifier allowlist restricts expansion to known NOAA codes only; (A2) exact token-shape validation rejects malformed suffixes like `CO02` or `Q100`; (A3) arity enforcement rejects truncated/extra comma-part payloads; (A4) fixed-width token validation for mandatory/additional data sections. Based on user decisions: invalid identifiers skip expansion and preserve raw values; malformed fields emit nulls with warning logs; REM fields get priority parsing before generic expansion; strict mode is default but opt-out via `strict_mode=False`.

The core changes centralize validation in [constants.py](src/noaa_spec/constants.py) through enhanced identifier resolution and introduce a `strict_mode` parameter threading through [cleaning.py](src/noaa_spec/cleaning.py) parsing flow. This satisfies P0 requirements from [NEXT_STEPS.md](NEXT_STEPS.md) while preserving spec-compliant record behavior.

## Steps

1. **Create identifier allowlist and validation registry** in [constants.py](src/noaa_spec/constants.py):
   - Add `KNOWN_IDENTIFIERS` set containing all valid identifier names (static from `FIELD_RULES`, repeated families from `_REPEATED_IDENTIFIER_RANGES`, EQD patterns `Q01-Q99`, `P01-P99`, etc.)
   - Enhance `is_valid_eqd_identifier()` to reject malformed EQD formats: suffix must be exactly 2 digits, not `00`, not letter-mixed (fixes `Q100`, `Q01A`, `N001`)
   - Enhance `is_valid_repeated_identifier()` to reject wrong-length suffixes (catches `OA01`, `CO02`, `RH0001`) and enforce exact digit-count per family
   - Add `get_expected_part_count(identifier: str) -> int | None` helper using `FieldRule.parts` keys to determine arity
   - Add `get_token_width_rules(identifier: str, part: int) -> dict | None` returning expected width/pattern for fixed-width sections

2. **Update `clean_noaa_dataframe()` in [cleaning.py](src/noaa_spec/cleaning.py#L490-L570)** to add strict mode parameter and REM priority:
   - Add `strict_mode: bool = True` parameter to function signature
   - Before generic comma-expansion loop, extract REM column and parse via `_parse_remarks()` early, then mark as processed
   - In column iteration loop (line 506-526), add allowlist gate:
     ```python
     if strict_mode and column not in KNOWN_IDENTIFIERS:
         logger.warning(f"Skipping unknown identifier: {column}")
         continue  # Skip expansion, keep raw
     ```
   - Thread `strict_mode` down to `clean_value_quality()`

3. **Enhance `clean_value_quality()` in [cleaning.py](src/noaa_spec/cleaning.py#L362-L410)** with arity and format checks:
   - Add `strict_mode` parameter
   - After identifier validation (lines 363-366), if `strict_mode` and identifier validation fails, log warning and return `{}` instead of proceeding
   - After `parse_field()` call (line 369), if `strict_mode`:
     - Get expected part count via `get_expected_part_count(column)`
     - If actual `len(parts) != expected`, log warning with truncated/extra label and return `{}`
   - For identifiers with fixed-width rules, validate token formats before numeric coercion (A4):
     - Call `get_token_width_rules(column, part_idx)` 
     - Check string length, sign conventions, numeric-only constraints
     - If mismatch, log warning and return `{}`

4. **Update `_expand_parsed()` in [cleaning.py](src/noaa_spec/cleaning.py#L227-L349)** to enforce token widths:
   - Add `strict_mode` parameter
   - For each part being processed (loop at line 251-349), if `strict_mode` and part has width rules:
     - Validate raw string before float conversion
     - Example: WND part 1 (direction) must be 3 digits, part 4 (speed) must be 4 digits
     - If invalid, log warning, skip that part (set to null)
   - Log malformed numeric tokens (like `WND='A90,1,N,0050,1'`) instead of storing as text

5. **Add width/format rules to `FieldRule` definitions in [constants.py](src/noaa_spec/constants.py)**:
   - Extend `FieldPartRule` dataclass with `token_width: int | None` and `token_pattern: re.Pattern | None` fields
   - Update key identifier rules (WND, TMP, DEW, SLP, etc.) with token width metadata from ISD format spec
   - Example: `WND.parts[1]` gets `token_width=3`, `WND.parts[4]` gets `token_width=4`

6. **Add comprehensive unit tests in [tests/test_cleaning.py](tests/test_cleaning.py)**:
   - **A1 tests** (unknown identifier rejection):
     - `test_unknown_identifier_no_expansion_strict()`: NAME with commas stays as single column, no `NAME__part*`
     - `test_unknown_identifier_expansion_permissive()`: Same input with `strict_mode=False` creates parts
   - **A2 tests** (malformed identifier rejection):
     - `test_eqd_malformed_suffix_Q100()`: `Q100` rejected (3 digits)
     - `test_eqd_malformed_suffix_Q01A()`: `Q01A` rejected (contains letter)
     - `test_eqd_malformed_suffix_N001()`: `N001` rejected (3 digits)
     - `test_repeated_malformed_CO02()`: `CO02` rejected (2 digits for 1-digit family)
     - `test_repeated_malformed_OA01()`: `OA01` rejected (2 digits for 1-digit family)
     - `test_repeated_malformed_RH0001()`: `RH0001` rejected (4 digits)
   - **A3 tests** (arity mismatch rejection):
     - `test_wnd_truncated_arity()`: `WND='180,1,N,0050'` rejected (4 parts, expects 5)
     - `test_tmp_truncated_arity()`: `TMP='+0250'` rejected (1 part, expects 2)
     - `test_wnd_extra_arity()`: `WND='180,1,N,0050,1,EXTRA'` rejected (6 parts, expects 5)
   - **A4 tests** (fixed-width token rejection):
     - `test_wnd_short_direction_token()`: `WND='1,1,N,0050,1'` rejected (1-char direction, expects 3)
     - `test_wnd_short_speed_token()`: `WND='180,1,N,50,1'` rejected (2-char speed, expects 4)
     - `test_tmp_short_value_token()`: `TMP='250,1'` rejected (3-char value, expects signed 4+)
   - Each test verifies logging output contains expected warning message

7. **Update helper validation functions**:
   - Modify `is_valid_eqd_identifier()` in [constants.py](src/noaa_spec/constants.py#L3733-L3741): tighten regex to exactly 2 digits, reject `00` suffix, reject letter suffixes
   - Modify `is_valid_repeated_identifier()` in [constants.py](src/noaa_spec/constants.py#L3723-L3731): check exact digit-count per family (e.g., OA must be 1 digit, not 2)
   - Add `is_valid_identifier()` that combines all checks (allowlist + EQD + repeated + static)

8. **Update [NEXT_STEPS.md](NEXT_STEPS.md)** with completion checkmarks:
   - Mark A1 complete: "✅ Restrict comma-field expansion to known identifiers ([cleaning.py](src/noaa_spec/cleaning.py) allowlist check)"
   - Mark A2 complete: "✅ Enforce exact identifier token format ([constants.py](src/noaa_spec/constants.py) validation tightening)"
   - Mark A3 complete: "✅ Enforce per-identifier arity ([cleaning.py](src/noaa_spec/cleaning.py) part-count validation)"
   - Mark A4 complete: "✅ Enforce fixed-width token formats ([constants.py](src/noaa_spec/constants.py) width rules + [cleaning.py](src/noaa_spec/cleaning.py) validation)"

9. **Add logging infrastructure**:
   - Import `logging` at top of [cleaning.py](src/noaa_spec/cleaning.py)
   - Create module-level logger: `logger = logging.getLogger(__name__)`
   - Emit `logger.warning()` for each rejection with structured message: `"[PARSE_STRICT] Rejected {identifier}: {reason}"`
   - Document in docstrings that strict mode logs to Python logging framework

10. **Thread `strict_mode` parameter through call stack**:
    - `clean_noaa_dataframe(df, strict_mode=True)` → `clean_value_quality(..., strict_mode)` → `_expand_parsed(..., strict_mode)`
    - Update [cli.py](src/noaa_spec/cli.py) `process_location()` command to accept `--permissive` flag that sets `strict_mode=False`
    - Update [pipeline.py](src/noaa_spec/pipeline.py) calls to `clean_noaa_dataframe()` to pass `strict_mode` parameter (default True)

## Verification

1. Run new tests in isolation: `poetry run pytest tests/test_cleaning.py::test_unknown_identifier_no_expansion_strict -v`
2. Run full cleaning test suite: `poetry run pytest tests/test_cleaning.py -v` (should pass; existing tests use valid identifiers)
3. Verify tests fail on current main: `git stash` changes, run tests, confirm failures, `git stash pop`
4. Manual check: Process a sample station CSV with logging enabled to observe rejection warnings
5. Integration test: Run `poetry run python -m noaa_spec.cli process-location <file>.csv` and verify output has no `NAME__part*` columns
6. Backward compatibility: Run with `--permissive` flag and verify old behavior preserved

## Decisions

- **Error representation**: Chose logging-only (no error flag columns) for simplicity; rejections emit `logger.warning()` with structured prefix `[PARSE_STRICT]`
- **Unknown identifiers**: Chose skip-expansion approach (A1) to preserve raw data fidelity; NAME column stays unchanged
- **REM priority parsing**: Chose early REM extraction before generic expansion to preserve typed parsing for remarks with embedded commas
- **Strictness opt-out**: Added `strict_mode` parameter (default True) for backward compatibility; CLI gets `--permissive` flag
- **Centralized validation**: Chose to enhance existing `is_valid_*` helpers and add `KNOWN_IDENTIFIERS` set rather than scattered checks
- **Token width enforcement**: Chose to add `token_width` and `token_pattern` to `FieldPartRule` dataclass for metadata-driven validation
