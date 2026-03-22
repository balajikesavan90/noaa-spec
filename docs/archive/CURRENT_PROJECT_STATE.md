# Current Project State

Last updated: 2026-03-14

## Executive summary

This repository is now operating as a specification-constrained NOAA ISD publication pipeline, not just a raw-data cleaning script collection.

The current system can:

- parse NOAA ISD / Global Hourly raw records into a canonical cleaned dataset,
- publish observation-level domain datasets,
- generate quality evidence artifacts,
- emit deterministic manifests and checksums for reproducible builds,
- measure implementation/test alignment against the NOAA specification.

The strongest current signals are:

- full repository tests were last recorded as passing,
- spec coverage is currently reported as 3536/3536 implemented and strictly tested,
- suspicious coverage is currently 0,
- recent contract-check cleaning runs completed successfully on 11 local station datasets,
- `publication_readiness_gate.json` now serves as an integrity/build-readiness artifact, while descriptive quality diagnostics are emitted separately in `quality_reports/quality_assessment.json`.

## Where the project stands today

At a high level, the repository has moved beyond a simple ETL prototype and now has four active publication surfaces:

1. **Canonical cleaned observations**
2. **Domain datasets**
3. **Quality evidence artifacts**
4. **Release and file manifests**

The core repository framing is documented in [README.md](../README.md), [docs/PIPELINE_DESIGN_RATIONALE.md](PIPELINE_DESIGN_RATIONALE.md), [docs/PIPELINE_VALIDATION_PLAN.md](PIPELINE_VALIDATION_PLAN.md), and [docs/DOMAIN_DATASET_REGISTRY.md](DOMAIN_DATASET_REGISTRY.md).

The manuscript in [paper/paper.md](../paper/paper.md) presents the software under the name **NOAA-Spec**, which is the paper-facing name for the same system.

## Recent run snapshot

Two recent contract-check runs are especially useful for understanding the current operational state.

### 1. March 11, 2026 contract check

Run artifacts live under [artifacts/test_runs/contract_check_20260311T231501-0700](../artifacts/test_runs/contract_check_20260311T231501-0700).

Key facts from the run:

- mode: `test_parquet_dir`
- input format: parquet
- input station count: 11
- total raw rows processed: 1,310,114
- total cleaned rows written: 1,310,114
- completed stations: 11/11
- failed stations: 0
- release/file manifest coverage check: passed
- timestamp validity: passed
- checksum policy conformance: passed
- publication gate: passed
- integrity score: 1.0000
- max observed quality-code exclusion rate: 0.6330

Important interpretation:

- The run is **operationally healthy**: all stations completed, manifests matched expectations, timestamps and checksums validated.
- The run is **scientifically transparent rather than aggressively filtered**: observed exclusion and sparsity metrics are surfaced explicitly in `quality_reports/quality_assessment.json` as descriptive diagnostics rather than as repository-defined acceptability decisions.

Supporting artifacts:

- [run configuration](../artifacts/test_runs/contract_check_20260311T231501-0700/manifests/run_config.json)
- [run status](../artifacts/test_runs/contract_check_20260311T231501-0700/manifests/run_status.csv)
- [publication gate](../artifacts/test_runs/contract_check_20260311T231501-0700/manifests/publication_readiness_gate.json)
- [release manifest](../artifacts/test_runs/contract_check_20260311T231501-0700/manifests/release_manifest.csv)
- [quality summary](../artifacts/test_runs/contract_check_20260311T231501-0700/quality_reports/quality_reports_summary.md)

The run wrote:

- 11 canonical cleaned station outputs,
- domain splits for the enabled domains,
- station quality profiles,
- station quality reports,
- mandatory run-level quality artifacts,
- deterministic release and file manifests.

The publication gate expected 361 artifacts and found all 361.

### 2. March 8, 2026 contract check

Run artifacts live under [artifacts/test_runs/contract_check_20260308T183600-0700](../artifacts/test_runs/contract_check_20260308T183600-0700).

This run processed the same 11 stations and the same 1,310,114 rows, but its top-level publication gate still returned `passed: false` under the older semantics because a quality-evaluation rule was still influencing gating logic rather than being separated into descriptive diagnostics.

Supporting artifact:

- [publication gate](../artifacts/test_runs/contract_check_20260308T183600-0700/manifests/publication_readiness_gate.json)

### What changed between March 8 and March 11

The important project-state change is not the raw data volume. It is the publication policy.

By March 11, the artifact split was updated so that:

- integrity checks remained in the publication gate,
- observed quality-related metrics were emitted separately as descriptive diagnostics,
- quality-related outputs no longer determined whether a completed build was publication-ready.

That behavior is documented in [docs/CLEANING_RUN_MODES.md](CLEANING_RUN_MODES.md).

This is a meaningful maturity step: the pipeline now preserves transparency about quality attrition without imposing repository-defined quality judgments on the data.

## How the data cleaning works

The cleaning engine lives in [src/noaa_spec/cleaning.py](../src/noaa_spec/cleaning.py) and is driven by declarative rules in [src/noaa_spec/constants.py](../src/noaa_spec/constants.py).

The main entry point is `clean_noaa_dataframe()`.

### Cleaning model

The pipeline treats NOAA documentation as the governing contract, then applies those rules in code through two layers:

1. **Constants layer**
   - defines field structure, expected part counts, missing sentinels, ranges, domains, patterns, token widths, scale factors, and quality-code behavior.
2. **Cleaning layer**
   - parses row values, applies rule checks, nulls invalid values, emits QC signals, and returns a canonical cleaned table.

### Cleaning sequence

In practical terms, `clean_noaa_dataframe()` does the following:

1. **Validate record structure when raw-line data is available**
   - control header validation,
   - whole-record structure validation,
   - parse errors recorded in `__parse_error`.

2. **Apply special-case parsers first**
   - `REM` remarks are parsed into structured outputs,
   - `QNN` original-observation payloads are parsed into repeated structured outputs.

3. **Expand comma-encoded NOAA fields**
   - two-part fields become `<field>__value`, `<field>__quality`, and QC columns,
   - multi-part fields become `<field>__partN` plus part-level QC signals.

4. **Apply strict identifier gating**
   - in `strict_mode`, only known NOAA identifiers are expanded.

5. **Enforce missing-value semantics**
   - field-specific sentinels are detected before numeric conversion,
   - detected sentinels become nulls,
   - text-level sentinel remnants are cleaned again after parsing.

6. **Apply scale factors**
   - for example temperatures, pressures, gusts, wave heights, and several derived measures are scaled after sentinel handling.

7. **Validate quality codes**
   - governing quality parts are mapped to the correct value parts,
   - invalid quality flags null only the affected value,
   - unaffected sibling values are preserved.

8. **Validate domains, ranges, widths, and arity**
   - categorical codes must match allowed sets or patterns,
   - numeric values must remain within defined bounds,
   - malformed token widths and bad part counts generate QC failures or strict-mode rejection behavior.

9. **Rename into stable friendly columns**
   - internal parsed names are normalized into researcher-facing columns such as `temperature_c`, `wind_speed_ms`, and `visibility_m`.

10. **Emit row-level usability summaries**
    - `row_has_any_usable_metric`
    - `usable_metric_count`
    - `usable_metric_fraction`

### What the cleaned output is meant to be

The cleaned canonical dataset is intended to preserve NOAA semantics while making them usable:

- no sentinel leakage into numeric outputs,
- explicit null semantics,
- quality codes still visible,
- stable column naming,
- deterministic serialization,
- QC pass/fail signals attached to values.

This design is intentionally conservative. The system prefers to null or flag bad values while preserving the rest of the row, instead of silently dropping observations.

## What gets published from a cleaning run

The cleaning runner in [src/noaa_spec/cleaning_runner.py](../src/noaa_spec/cleaning_runner.py) turns station inputs into deterministic publication artifacts.

The current publication contract is:

- canonical cleaned station datasets,
- domain datasets,
- quality evidence reports,
- station quality profiles,
- success markers,
- release manifests,
- file manifests,
- publication readiness gate output.

The domain dataset surface currently includes the domains documented in [docs/DOMAIN_DATASET_REGISTRY.md](DOMAIN_DATASET_REGISTRY.md):

- core_meteorology
- wind
- precipitation
- clouds_visibility
- pressure_temperature
- remarks

These remain observation-level slices keyed for joins by `station_id` and `DATE`.

## How the project is verified

Verification happens at four levels.

### 1. Repository tests

The repository has an extensive automated test suite, including:

- cleaning logic tests in [tests/test_cleaning.py](../tests/test_cleaning.py)
- runner/orchestration tests in [tests/test_cleaning_runner.py](../tests/test_cleaning_runner.py)
- aggregation tests in [tests/test_aggregation.py](../tests/test_aggregation.py)
- integration tests in [tests/test_integration.py](../tests/test_integration.py)
- spec coverage generator tests
- suspicious coverage integrity tests
- documentation integrity tests

The latest recorded full-suite run in the workspace context completed successfully with `poetry run pytest tests/ -v`.

### 2. Contract validation at runtime

The runner validates publication requirements during execution, including:

- sentinel leakage checks via [src/noaa_spec/contract_validation.py](../src/noaa_spec/contract_validation.py)
- canonical schema checks,
- deterministic output writing,
- expected artifact existence,
- `_SUCCESS.json` marker validation,
- checksum generation,
- manifest completeness checks.

This means the pipeline is not relying on tests alone. It also validates publication constraints while a run is executing.

### 3. Specification coverage system

The current verification story is heavily centered on the specification coverage artifacts:

- [spec_coverage.csv](../spec_coverage.csv)
- [SPEC_COVERAGE_REPORT.md](../SPEC_COVERAGE_REPORT.md)
- [RULE_PROVENANCE_LEDGER.csv](../RULE_PROVENANCE_LEDGER.csv)
- [RULE_PROVENANCE_LEDGER.md](../RULE_PROVENANCE_LEDGER.md)
- [RULE_IMPACT_REPORT.md](../RULE_IMPACT_REPORT.md)

Current headline values from the generated artifacts:

- total extracted spec rules: 3536
- rules implemented in code: 3536
- strict test-covered rules: 3536
- suspicious coverage entries: 0

This is the repository’s strongest formal claim today: specification-derived rules, implementation evidence, and test evidence are currently aligned according to the project’s rule-matching system.

### 4. Quality evidence artifacts

Every cleaning run also produces empirical evidence about what the cleaning is doing to the data, for example:

- field completeness,
- sentinel frequency,
- quality-code exclusions,
- domain usability,
- station-year QC attrition.

The latest March 11 run produced:

- 315 `field_completeness` rows,
- 11 `sentinel_frequency` rows,
- 11 `quality_code_exclusions` rows,
- 64 `domain_usability_summary` rows,
- 250 `station_year_quality` rows.

This is important because the system is designed for transparency, not just validity. It records the effect of cleaning decisions rather than hiding them.

## What the paper is about

The manuscript in [paper/paper.md](../paper/paper.md) is a software paper, not a climate-results paper.

Its title is:

**NOAA-Spec: A Specification-Constrained Pipeline for Processing NOAA Integrated Surface Database Observations**

### Core claim of the paper

The paper argues that NOAA ISD preprocessing should be treated as a specification-constrained software problem.

Its main contribution is not a new climate finding. It is a reproducible software architecture for turning NOAA documentation into executable cleaning and publication behavior.

### Main concepts emphasized in the paper

1. **Specification-constrained processing**
   - the NOAA format documentation is treated as the governing source.

2. **Deterministic publication artifacts**
   - identical inputs and configuration should produce identical outputs.

3. **Verification Triangle**
   - Specification Rule Graph,
   - Implementation Alignment Map,
   - Test Coverage Verification.

4. **Transparent quality evidence**
   - cleaning decisions should be measurable and inspectable.

5. **Reusable scientific software**
   - the software is intended for climate researchers, atmospheric scientists, and data scientists who need auditable NOAA preprocessing.

### What the paper is not claiming

The manuscript is not claiming:

- a new climatological scientific conclusion,
- a probabilistic error-repair model,
- a generic data quality framework for all domains.

Instead, it presents this repository as a domain-specific scientific data publication framework for NOAA ISD.

## Current strengths

- deterministic run layout and manifest model are in place,
- domain datasets are now formalized as public contracts,
- quality artifacts are first-class outputs,
- spec coverage and suspicious coverage reporting are mature,
- cleaning-run orchestration is resumable and publication-oriented,
- recent local contract-check runs are operationally successful.

## Current cautions and open edges

- quality-code exclusion rates can still be high in some station/domain slices,
- the provenance ledger still contains a large `needs_manual_review` surface,
- many provenance rows are `documented_inferred` rather than `documented_exact`,
- the project still carries some naming duality between the repository name and the paper name,
- aggregation remains intentionally secondary to the publication-grade canonical/domain artifact contract.

## Bottom line

The current state of the project is strong on reproducibility, verification plumbing, and publication artifact structure.

The most notable recent step is the split between an integrity-only publication gate and a separate advisory quality assessment artifact. That change better matches the project’s philosophy: preserve data lineage, expose cleaning effects, and let researchers judge quality with evidence rather than hidden transformations.
