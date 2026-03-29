# INTERNAL DEVELOPMENT RECORD — NOT REVIEWER EVIDENCE

# Post-Run Audit Report

Local-path note: `<EXTERNAL_STORAGE>` references below describe a machine-local audit target and are not required for reproduction from this repository.

## Overview

| Check | Result |
| --- | --- |
| Build root | <EXTERNAL_STORAGE>/NOAA_CLEANED_DATA/build_20260319T150502Z |
| Build id | 20260319T150502Z |
| Build timestamp | 2026-03-19T15:05:02+00:00 |
| Run state | completed |
| Finalized | True |
| Completed stations | 100 / 100 |
| Canonical station dirs | 100 |
| Domain station dirs | 100 |
| Station quality profiles | 100 |
| Release manifest rows | 790 |
| File manifest rows | 1099 |

## Contract Checks

| Check | Result |
| --- | --- |
| Release manifest columns | pass |
| Release artifact types | pass |
| Required quality artifacts | pass |
| Release artifact_id unique | pass |
| File manifest artifact_id unique | pass |
| Release artifact paths exist | pass |
| File artifact paths exist | pass |

## Lineage Checks

| Check | Result |
| --- | --- |
| Raw source lineage non-empty | pass |
| Canonical lineage -> raw_source | pass |
| Domain lineage -> canonical_dataset | pass |
| Quality lineage references release artifacts | pass |

## Checksum Checks

| Check | Result |
| --- | --- |
| Embedded publication gate checksum check | fail |
| Recomputed checksum check | fail |
| Release manifest checksum mismatches | 3 |
| File manifest checksum mismatches | 1 |
| Cross-manifest checksum disagreements | 2 |
| Gate/report mismatch set | build_file/20260319T150502Z/canonical_cleaned/15168099999/LocationData_Cleaned.parquet |

## Key Findings

- Run completed and finalization artifacts were written.
- Station-level artifact families are complete across canonical, domain, and quality-profile outputs.
- Embedded publication gate failed.
- Embedded publication gate checksum findings are stale relative to the final manifest set.
- Recomputed checksum mismatches remain for: build_file/20260319T150502Z/canonical_cleaned/07335099999/LocationData_Cleaned.parquet, canonical_dataset/20260319T150502Z/07335099999, canonical_dataset/20260319T150502Z/15168099999, raw_source/20260319T150502Z/62007099999.
- Release and file manifests disagree on the checksum for the same artifact path in 2 cases.
- Quality assessment is advisory-only and does not block publication integrity checks.

## Recomputed Checksum Mismatches

### Release Manifest

- canonical_dataset/20260319T150502Z/07335099999
- canonical_dataset/20260319T150502Z/15168099999
- raw_source/20260319T150502Z/62007099999

### File Manifest

- build_file/20260319T150502Z/canonical_cleaned/07335099999/LocationData_Cleaned.parquet

## Cross-Manifest Checksum Disagreements

- <EXTERNAL_STORAGE>/NOAA_CLEANED_DATA/build_20260319T150502Z/canonical_cleaned/07335099999/LocationData_Cleaned.parquet
- <EXTERNAL_STORAGE>/NOAA_CLEANED_DATA/build_20260319T150502Z/canonical_cleaned/15168099999/LocationData_Cleaned.parquet

## Embedded Gate Snapshot

```json
{
  "checks": {
    "artifact_manifest_coverage": {
      "expected_count": 1097,
      "manifest_count": 1098,
      "missing_paths": [],
      "passed": true
    },
    "artifact_structural_sanity": {
      "domain_usable_row_rate_bounds_ok": true,
      "field_completeness_ratio_bounds_ok": true,
      "passed": true,
      "quality_code_exclusion_rate_bounds_ok": true,
      "required_columns_present": {
        "domain_usable_row_rate": true,
        "field_completeness_ratio": true,
        "quality_code_exclusion_rate": true,
        "sentinel_row_rate": true,
        "station_year_usable_row_rate": true
      },
      "required_quality_artifacts_present": {
        "domain_usability_summary": true,
        "field_completeness": true,
        "quality_code_exclusions": true,
        "sentinel_frequency": true,
        "station_year_quality": true
      },
      "sentinel_row_rate_bounds_ok": true,
      "station_year_usable_row_rate_bounds_ok": true
    },
    "build_metadata_completeness": {
      "build_timestamp_valid": true,
      "exists": true,
      "missing_source_scope_fields": [],
      "missing_top_level_fields": [],
      "passed": true
    },
    "checksum_policy_conformance": {
      "invalid_rows": [
        "build_file/20260319T150502Z/canonical_cleaned/07335099999/LocationData_Cleaned.parquet",
        "build_file/20260319T150502Z/canonical_cleaned/15168099999/LocationData_Cleaned.parquet",
        "canonical_dataset/20260319T150502Z/07335099999",
        "canonical_dataset/20260319T150502Z/15168099999",
        "raw_source/20260319T150502Z/62007099999"
      ],
      "passed": false
    },
    "run_completion": {
      "completed": 100,
      "failed": 0,
      "passed": true,
      "skipped": 0,
      "total": 100
    },
    "timestamp_validity": {
      "build_timestamp_valid": true,
      "invalid_file_manifest_rows": [],
      "invalid_release_manifest_rows": [],
      "passed": true
    }
  },
  "generated_at": "2026-03-19T15:05:02+00:00",
  "passed": false,
  "quality_assessment_generated": true,
  "quality_assessment_path": "<EXTERNAL_STORAGE>/NOAA_CLEANED_DATA/build_20260319T150502Z/quality_reports/quality_assessment.json",
  "run_id": "20260319T150502Z",
  "scores": {
    "integrity_components": {
      "artifact_manifest_coverage": 1.0,
      "artifact_structural_sanity": 1.0,
      "build_metadata_completeness": 1.0,
      "checksum_policy_conformance": 0.0,
      "run_completion": 1.0,
      "timestamp_validity": 1.0
    },
    "integrity_score": 0.8333333333333334,
    "overall_score": 0.8333333333333334,
    "scale": "0_to_1"
  }
}
```

## Recomputed Checksum Snapshot

```json
{
  "passed": false,
  "invalid_rows": [
    "build_file/20260319T150502Z/canonical_cleaned/07335099999/LocationData_Cleaned.parquet",
    "canonical_dataset/20260319T150502Z/07335099999",
    "canonical_dataset/20260319T150502Z/15168099999",
    "raw_source/20260319T150502Z/62007099999"
  ]
}
```
