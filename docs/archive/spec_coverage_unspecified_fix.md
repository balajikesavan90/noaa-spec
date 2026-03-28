# INTERNAL DEVELOPMENT RECORD — NOT REVIEWER EVIDENCE

# Spec Coverage UNSPECIFIED Fix

## What Was Wrong

`spec_coverage.csv` had a 29-row `identifier=UNSPECIFIED` bucket from structural width extraction:

- 28 rows were `FLD LEN: 3` section/header identifier width statements across Parts 04-30.
- 1 row was Part 03 `POS: 61-63` (`WIND-OBSERVATION direction angle`).

The extractor captured width rules before identifier context was bound, so these rows were tagged `UNSPECIFIED` and marked `synthetic_unmapped`.

## Attribution Fix

Implemented deterministic attribution in `tools/spec_coverage/generate_spec_coverage.py`:

- Added explicit `(part, section-context-line) -> identifier` mapping table: `SECTION_IDENTIFIER_CONTEXT_MAP`.
- Added bounded lookahead resolver: `infer_identifiers_from_adjacent_structural_context(...)`.
- Applied fallback attribution when:
  - width line is `FLD LEN: 3` and no active identifier context, and
  - Part 03 `POS:` width line has no active identifier context.

This now maps the 29 rows to concrete identifiers (e.g., `AA1`, `AT1`, `CB1`, ..., `UA1`, `WND`, and `ADD`/`HAIL` where parser uses legacy/static identifiers).

## Enforcement Added

Added strict section-token enforcement in parser/cleaning path:

- `src/noaa_spec/constants.py`
  - Added `SECTION_IDENTIFIER_WIDTH_RULE_IDENTIFIERS`.
  - Added `is_valid_section_identifier_token(...)`.
- `src/noaa_spec/cleaning.py`
  - `clean_value_quality(...)`: rejects malformed section identifier tokens in strict mode.
  - `clean_noaa_dataframe(...)`: skips malformed section identifier columns in strict mode.

Validation rule:

- section tokens must be uppercase alphanumeric with width 3 for section-header families;
- legacy parser token `HAIL` is kept as explicit compatibility exception.

## Tests Added/Updated

### Generator attribution tests

- `tests/test_spec_coverage_generator.py`
  - `test_parse_spec_docs_maps_fld_len_three_header_context_rows`
  - `test_parse_spec_docs_part03_pos_width_uses_next_context_for_wnd`

### Parsing/strict enforcement tests

- `tests/test_cleaning.py`
  - `test_section_identifier_malformed_wndx_rejected`
  - `test_section_identifier_malformed_addx_rejected`
  - `test_wnd_direction_angle_token_width_rule_is_three`
  - `test_section_identifier_token_width_signature_table`

Also updated one control-header strict test expectation where deterministic rejection category is now `control_header_invalid_width`.

## Coverage Outcome

After regeneration (`poetry run python tools/spec_coverage/generate_spec_coverage.py`):

- 29-row metric `UNSPECIFIED` bucket is eliminated.
- `SPEC_COVERAGE_REPORT.md` no longer contains `| UNSPECIFIED | 29 | ... |`.
- Current `identifier=UNSPECIFIED` rows are synthetic alignment rows only:
  - `total_unspecified=4`
  - `metric_unspecified=0`

## Remaining Edge Cases

- Synthetic alignment hints with no identifier evidence still remain `UNSPECIFIED` by design.
- `HAIL` remains a legacy parser token exception for section-token width checks.
