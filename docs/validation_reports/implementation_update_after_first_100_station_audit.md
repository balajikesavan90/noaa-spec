# Implementation Update After First 100-Station Audit

## Summary

This pass implemented targeted changes to improve:

- batch sampling correctness
- default domain-split behavior
- per-station observability
- quality/profile semantics
- manifest coverage/provenance
- publication gate semantics
- report usefulness

Core scientific cleaning rules were not changed.

## Files Changed

- `.gitignore`
- `README.md`
- `docs/CLEANING_RUN_MODES.md`
- `docs/CURRENT_PROJECT_STATE.md`
- `src/noaa_climate_data/cli.py`
- `src/noaa_climate_data/cleaning_runner.py`
- `tests/test_cleaning_runner.py`
- `tests/test_noaa_client_cli.py`

## Behavior Changed

### 1. `size_quartiles` now spans each quartile instead of taking the smallest edge

Changed in `src/noaa_climate_data/cli.py`.

- inventory rows now carry:
  - `global_size_rank`
  - `global_size_percentile`
  - `quartile_rank`
  - `quartile_percentile`
- within each quartile, selection now uses deterministic spaced sampling across the quartile range
- quartile 4 also gets explicit deterministic top-tail picks from the largest available files
- `selected_stations.csv` now records:
  - `size_quartile`
  - `size_bytes`
  - `quartile_percentile`
  - `global_size_percentile`

### 2. Domain splits are now enabled by default for batch-style cleaning

Changed in `src/noaa_climate_data/cli.py`.

- `cleaning-run --mode batch_parquet_dir` now defaults to domain splits on
- `run-cleaning-batch` now defaults to domain splits on
- explicit disable path is now available as:
  - `--no-domain-splits`
- the existing `write_domain_splits` config field remains intact for run reproducibility

### 3. `run_status.csv` now captures per-station phase timings and workload metrics

Changed in `src/noaa_climate_data/cleaning_runner.py`.

Added columns:

- `elapsed_read_seconds`
- `elapsed_clean_seconds`
- `elapsed_domain_split_seconds`
- `elapsed_quality_profile_seconds`
- `elapsed_write_seconds`
- `elapsed_total_seconds`
- `raw_columns`
- `cleaned_columns`
- `input_size_bytes`
- `cleaned_size_bytes`

The existing `elapsed_seconds` field is preserved as an alias of total station elapsed time.

### 4. Quality-profile impact semantics were separated

Changed in `src/noaa_climate_data/cleaning_runner.py`.

- structural/control validation impacts are now tracked separately from substantive data impacts
- `qc_control_invalid_*` flags now map to `structural_validation` rather than blending into ordinary domain validation
- profiles now record:
  - `rows_with_structural_impacts`
  - `fraction_rows_structural_impacted`
  - `rows_with_sentinel_impacts`
  - `rows_with_quality_code_impacts`
  - `rows_with_other_substantive_impacts`
- `rows_with_qc_flags` / `fraction_rows_impacted` now reflect substantive impacts instead of any structural/control flag

### 5. Quality artifact semantics were clarified

Changed in `src/noaa_climate_data/cleaning_runner.py`.

`sentinel_frequency.csv`:

- kept the artifact name for compatibility
- replaced the ambiguous single “frequency” signal with explicit columns:
  - `sentinel_events`
  - `rows_with_sentinel_impacts`
  - `sentinel_row_rate`
  - `sentinel_events_per_row`

`quality_code_exclusions.csv`:

- now records both row-based and event-based views:
  - `quality_code_exclusions`
  - `rows_with_quality_code_exclusions`
  - `quality_code_exclusion_rate`
  - `quality_code_exclusion_events_per_row`

`domain_usability_summary.csv`:

- when domain splits are enabled, rows now carry:
  - `artifact_mode=domain_splits`
  - `advisory_only=false`
- when domain splits are disabled, fallback rows are still written but are explicitly marked:
  - `artifact_mode=fallback_no_domain_splits`
  - `advisory_only=true`
- fallback usability is now derived from canonical cleaned output rather than a synthetic all-zero placeholder

### 6. Publication and quality semantics were split

Changed in `src/noaa_climate_data/cleaning_runner.py`.

- `publication_readiness_gate.json` now focuses on build/package integrity only
- threshold-based quality findings now emit separately in `quality_reports/quality_assessment.json`
- the gate now includes:
  - `quality_assessment_generated`
  - `quality_assessment_path`
- quality thresholds remain visible, but are explicitly advisory rather than controlling top-level gate pass/fail
- gate timestamps now derive from build metadata for stable artifact generation

### 7. Manifests were strengthened

Changed in `src/noaa_climate_data/cleaning_runner.py`.

- `publication_readiness_gate.json` is now included in `file_manifest.csv`
- `quality_assessment.json` is now included in `file_manifest.csv`
- `file_manifest.csv` still does not include itself; this is now explicitly documented in code comments to avoid recursive self-checksum instability
- raw-source release-manifest lineage is now improved when batch staging metadata is available:
  - original `source_path`
  - staged `staged_path`

### 8. Report summaries were enriched without changing cleaning behavior

Changed in `src/noaa_climate_data/cleaning_runner.py`.

`quality_reports_summary.md` now includes concise anomaly-oriented sections for:

- largest input stations
- widest cleaned schemas
- highest quality-code exclusion rates
- highest sentinel event rates
- lowest field completeness
- fallback/advisory domain-usability mode when domain splits are disabled

`global_quality_summary.json` now also includes:

- `average_structural_impact_rate`
- stable operational outlier summaries for:
  - largest input stations
  - widest cleaned schemas

## Tests Added or Updated

Updated in `tests/test_cleaning_runner.py`:

- quality assessment now verifies advisory threshold behavior
- publication structural sanity now verifies integrity-only bounds behavior
- quality profile now verifies structural vs substantive separation
- `run_status.csv` now verifies phase timing and workload columns
- mandatory quality artifacts now verify clarified sentinel and domain-usability semantics
- file-manifest coverage now expects both `publication_readiness_gate` and `quality_assessment`
- release-manifest raw-source lineage now expects explicit source-path lineage

Updated in `tests/test_noaa_client_cli.py`:

- batch selection manifest now verifies percentile metadata
- batch default domain-split behavior now expects enabled
- new batch CLI test verifies `--no-domain-splits`
- new quartile-selection test verifies within-quartile spread plus top-tail inclusion

Validation run:

- `poetry run pytest tests/test_cleaning_runner.py tests/test_noaa_client_cli.py tests/test_publication_schema_ci.py tests/test_documentation_integrity.py -q`
- result: `94 passed`

## Unresolved Assumptions / Follow-Up

- Runtime phase timings are intentionally captured in `run_status.csv`, but not used to build deterministic “slowest station” rankings inside release-quality summary artifacts. This preserves reproducible release checksums while still exposing timing observability in the execution truth table.
- `sentinel_frequency.csv` keeps its historical filename for compatibility even though the internal columns are now more explicit.
- `file_manifest.csv` still omits self-inclusion by design because including its own checksum would create a recursive fixed-point problem.
