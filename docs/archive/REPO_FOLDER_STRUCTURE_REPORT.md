# Repository Folder Structure Report

This report reflects the current repository structure as of 2026-03-21 in the local workspace.

Scope:
- Includes tracked files and unignored untracked files.
- Excludes files ignored by Git.
- Generated from `git ls-files --cached --others --exclude-standard`.

Summary:
- Files: 203
- Directories: 40

```text
.
├── .github/
│   ├── prompts/
│   │   ├── plan-numericRangeValidationQcSignals.prompt.md
│   │   ├── plan-qcMissingStatusAndTests.prompt.md
│   │   └── plan-strictNoaaParserGateA.prompt.md
│   ├── workflows/
│   │   └── suspicious_coverage.yml
│   └── copilot-instructions.md
├── .vscode/
│   ├── settings.json
│   └── tasks.json
├── docs/
│   ├── examples/
│   │   ├── noaa_demo/
│   │   │   ├── data_dictionary.html
│   │   │   └── pipeline_overview.html
│   │   └── station_reports/
│   │       ├── 01116099999/
│   │       │   ├── LocationData_AggregationReport.json
│   │       │   ├── LocationData_AggregationReport.md
│   │       │   ├── LocationData_QualityReport.json
│   │       │   └── LocationData_QualityReport.md
│   │       ├── 03041099999/
│   │       │   ├── LocationData_AggregationReport.json
│   │       │   ├── LocationData_AggregationReport.md
│   │       │   ├── LocationData_QualityReport.json
│   │       │   └── LocationData_QualityReport.md
│   │       ├── 16754399999/
│   │       │   ├── LocationData_AggregationReport.json
│   │       │   ├── LocationData_AggregationReport.md
│   │       │   ├── LocationData_QualityReport.json
│   │       │   └── LocationData_QualityReport.md
│   │       ├── 27679099999/
│   │       │   ├── LocationData_AggregationReport.json
│   │       │   ├── LocationData_AggregationReport.md
│   │       │   ├── LocationData_QualityReport.json
│   │       │   └── LocationData_QualityReport.md
│   │       ├── 34880099999/
│   │       │   ├── LocationData_AggregationReport.json
│   │       │   ├── LocationData_AggregationReport.md
│   │       │   ├── LocationData_QualityReport.json
│   │       │   └── LocationData_QualityReport.md
│   │       ├── 40435099999/
│   │       │   ├── LocationData_AggregationReport.json
│   │       │   ├── LocationData_AggregationReport.md
│   │       │   ├── LocationData_QualityReport.json
│   │       │   └── LocationData_QualityReport.md
│   │       ├── 57067099999/
│   │       │   ├── LocationData_AggregationReport.json
│   │       │   ├── LocationData_AggregationReport.md
│   │       │   ├── LocationData_QualityReport.json
│   │       │   └── LocationData_QualityReport.md
│   │       ├── 78724099999/
│   │       │   ├── LocationData_AggregationReport.json
│   │       │   ├── LocationData_AggregationReport.md
│   │       │   ├── LocationData_QualityReport.json
│   │       │   └── LocationData_QualityReport.md
│   │       ├── 82795099999/
│   │       │   ├── LocationData_AggregationReport.json
│   │       │   ├── LocationData_AggregationReport.md
│   │       │   ├── LocationData_QualityReport.json
│   │       │   └── LocationData_QualityReport.md
│   │       ├── 83692099999/
│   │       │   ├── LocationData_AggregationReport.json
│   │       │   ├── LocationData_AggregationReport.md
│   │       │   ├── LocationData_QualityReport.json
│   │       │   └── LocationData_QualityReport.md
│   │       └── 94368099999/
│   │           ├── LocationData_AggregationReport.json
│   │           ├── LocationData_AggregationReport.md
│   │           ├── LocationData_QualityReport.json
│   │           └── LocationData_QualityReport.md
│   ├── validation_artifacts/
│   │   └── suspicious_coverage/
│   │       └── suspicious_summary.md
│   ├── validation_reports/
│   │   ├── artifact_semantics_doc_consistency_check.md
│   │   ├── build_20260319T150502Z_post_run_audit.md
│   │   ├── build_20260320T040852Z_post_run_audit.md
│   │   ├── checksum_finalization_integrity_fix.md
│   │   ├── implementation_update_after_first_100_station_audit.md
│   │   ├── large_station_oom_and_chunking_assessment.md
│   │   ├── quality_artifact_language_cleanup_20260320.md
│   │   └── subprocess_station_runner_refactor.md
│   ├── ARTIFACT_BOUNDARY_POLICY.md
│   ├── CLEANING_RUN_MODES.md
│   ├── CURRENT_PROJECT_STATE.md
│   ├── DOMAIN_DATASET_REGISTRY.md
│   ├── PARSER_ENGINEERING_GUARDS.md
│   ├── PIPELINE_DESIGN_RATIONALE.md
│   ├── PIPELINE_VALIDATION_PLAN.md
│   ├── REPO_CLEANUP_RECOMMENDATIONS.md
│   ├── UNSPECIFIED_RULES_ANALYSIS.md
│   └── spec_coverage_unspecified_fix.md
├── spec_sources/isd-format-document-parts/
│   ├── isd-format-document.deterministic.md
│   ├── isd-format-document.pdf
│   ├── isd-format-document.txt
│   ├── part-01-preface-and-dataset-overview.md
│   ├── part-02-control-data-section.md
│   ├── part-03-mandatory-data-section.md
│   ├── part-04-additional-data-section.md
│   ├── part-05-weather-occurrence-data.md
│   ├── part-06-climate-reference-network-unique-data.md
│   ├── part-07-network-metadata.md
│   ├── part-08-crn-control-section.md
│   ├── part-09-subhourly-temperature-section.md
│   ├── part-10-hourly-temperature-section.md
│   ├── part-11-hourly-temperature-extreme-section.md
│   ├── part-12-subhourly-wetness-section.md
│   ├── part-13-hourly-geonor-vibrating-wire-summary-section.md
│   ├── part-14-runway-visual-range-data.md
│   ├── part-15-cloud-and-solar-data.md
│   ├── part-16-sunshine-observation-data.md
│   ├── part-17-solar-irradiance-section.md
│   ├── part-18-net-solar-radiation-section.md
│   ├── part-19-modeled-solar-irradiance-section.md
│   ├── part-20-hourly-solar-angle-section.md
│   ├── part-21-hourly-extraterrestrial-radiation-section.md
│   ├── part-22-hail-data.md
│   ├── part-23-ground-surface-data.md
│   ├── part-24-temperature-data.md
│   ├── part-25-sea-surface-temperature-data.md
│   ├── part-26-soil-temperature-data.md
│   ├── part-27-pressure-data.md
│   ├── part-28-weather-occurrence-data-extended.md
│   ├── part-29-wind-data.md
│   └── part-30-marine-data.md
├── noaa_file_index/
│   └── 20260207/
│       └── README.md
├── old_r_files/
│   ├── FileList Creation.R
│   ├── LocationID_Creation.R
│   └── Template.R
├── paper/
│   ├── README.md
│   ├── paper-preview.html
│   ├── paper.bib
│   └── paper.md
├── reproducibility/
│   ├── README.md
│   ├── environment.txt
│   ├── pipeline_snapshot.json
│   ├── minimal/
│   │   ├── station_cleaned.csv
│   │   ├── station_cleaned_expected.csv
│   │   └── station_raw.csv
│   ├── full_station/
│   │   ├── station_cleaned.csv
│   │   ├── station_cleaned_expected.csv
│   │   └── station_raw.csv
│   ├── run_pipeline_example.py
│   └── sample_station_raw.txt  [historical, removed from active layout]
├── scripts/
│   ├── audit_build.py
│   ├── convert_output_raw_csv_to_parquet.py
│   ├── recover_build_finalization.py
│   ├── run_pick_location_cron.sh
│   ├── split_cleaned_by_domain.py
│   └── split_domains_by_station.py
├── src/
│   └── noaa_spec/
│       ├── contract_schemas/
│       │   └── v1/
│       │       ├── canonical_dataset.json
│       │       ├── domain_dataset.json
│       │       ├── quality_report.json
│       │       └── release_manifest.json
│       ├── domains/
│       │   ├── __init__.py
│       │   ├── clouds_visibility.py
│       │   ├── core_meteorology.py
│       │   ├── precipitation.py
│       │   ├── pressure_temperature.py
│       │   ├── publisher.py
│       │   ├── registry.py
│       │   ├── remarks.py
│       │   └── wind.py
│       ├── __init__.py
│       ├── build_audit.py
│       ├── cleaning.py
│       ├── cleaning_runner.py
│       ├── cli.py
│       ├── constants.py
│       ├── contract_validation.py
│       ├── contracts.py
│       ├── deterministic_io.py
│       ├── domain_split.py
│       ├── noaa_client.py
│       ├── pdf_markdown.py
│       ├── pipeline.py
│       └── research_reports.py
├── tests/
│   ├── fixtures/
│   │   └── release_manifest_v1_snapshot.csv
│   ├── __init__.py
│   ├── test_aggregation.py
│   ├── test_artifact_contracts.py
│   ├── test_check_station_sync.py
│   ├── test_cleaning.py
│   ├── test_cleaning_runner.py
│   ├── test_contract_validation.py
│   ├── test_deterministic_io.py
│   ├── test_documentation_integrity.py
│   ├── test_domain_publisher.py
│   ├── test_domain_registry.py
│   ├── test_domain_split.py
│   ├── test_integration.py
│   ├── test_noaa_client_cli.py
│   ├── test_parser_spec_guardrails.py
│   ├── test_pdf_markdown.py
│   ├── test_publication_schema_ci.py
│   ├── test_qc_comprehensive.py
│   ├── test_reproducibility_example.py
│   ├── test_research_reports.py
│   ├── test_rule_impact_report.py
│   ├── test_rule_provenance_ledger.py
│   ├── test_spec_coverage_generator.py
│   └── test_suspicious_coverage_integrity.py
├── tools/
│   ├── reproducibility/
│   │   └── export_pipeline_snapshot.py
│   ├── rule_impact/
│   │   └── generate_rule_impact_report.py
│   └── spec_coverage/
│       ├── export_suspicious_summary.py
│       ├── generate_rule_provenance_ledger.py
│       └── generate_spec_coverage.py
├── .gitignore
├── AGENTS.md
├── ARCHITECTURE_NEXT_STEPS.md
├── CLEANING_RECOMMENDATIONS.md
├── LICENSE
├── NEXT_STEPS.md
├── P3_EXPAND_RESEARCH_VALUE.md
├── QC_SIGNALS_ARCHITECTURE.md
├── README.md
├── REPO_CLEANUP_AUDIT.md
├── REPO_PUBLICATION_CLEANUP_AUDIT.md
├── RULE_IMPACT_REPORT.md
├── RULE_PROVENANCE_LEDGER.md
├── SPEC_COVERAGE_REPORT.md
├── UNDOCUMENTED_RULES_REVIEW.md
├── check_station_sync.py
├── generate_audit_queue.py
├── monitor_latest_build.py
├── poetry.lock
├── poetry.toml
├── pyproject.toml
└── rerun_stations.py
```
