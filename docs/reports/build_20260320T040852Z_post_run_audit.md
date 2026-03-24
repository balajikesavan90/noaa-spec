# Post-Run Audit Report

Local-path note: `<EXTERNAL_STORAGE>` references below describe a machine-local audit target and are not required for reproduction from this repository.

## Overview

| Check | Result |
| --- | --- |
| Build root | <EXTERNAL_STORAGE>/NOAA_CLEANED_DATA/build_20260320T040852Z |
| Build id | 20260320T040852Z |
| Build timestamp | 2026-03-20T04:08:52+00:00 |
| Run state | completed |
| Finalized | True |
| Completed stations | 100 / 100 |
| Canonical station dirs | 100 |
| Domain station dirs | 100 |
| Station quality profiles | 100 |
| Release manifest rows | 791 |
| File manifest rows | 1100 |

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
| Embedded publication gate checksum check | pass |
| Recomputed checksum check | pass |
| Release manifest checksum mismatches | 0 |
| File manifest checksum mismatches | 0 |
| Cross-manifest checksum disagreements | 0 |
| Gate/report mismatch set | none |

## Key Findings

- Run completed and finalization artifacts were written.
- Station-level artifact families are complete across canonical, domain, and quality-profile outputs.
- Embedded publication gate passed.
- Recomputed checksum validation passed for all release and file-manifest rows.
- Quality assessment is advisory-only and does not block publication integrity checks.

## Recomputed Checksum Mismatches

### Release Manifest

- none

### File Manifest

- none

## Cross-Manifest Checksum Disagreements

- none

## Embedded Gate Snapshot

```json
{
  "checks": {
    "artifact_manifest_coverage": {
      "expected_count": 1098,
      "manifest_count": 1099,
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
      "invalid_rows": [],
      "passed": true
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
  "generated_at": "2026-03-20T04:08:52+00:00",
  "passed": true,
  "quality_assessment_generated": true,
  "quality_assessment_path": "<EXTERNAL_STORAGE>/NOAA_CLEANED_DATA/build_20260320T040852Z/quality_reports/quality_assessment.json",
  "run_id": "20260320T040852Z",
  "scores": {
    "integrity_components": {
      "artifact_manifest_coverage": 1.0,
      "artifact_structural_sanity": 1.0,
      "build_metadata_completeness": 1.0,
      "checksum_policy_conformance": 1.0,
      "run_completion": 1.0,
      "timestamp_validity": 1.0
    },
    "integrity_score": 1.0,
    "overall_score": 1.0,
    "scale": "0_to_1"
  }
}
```

## Recomputed Checksum Snapshot

```json
{
  "passed": true,
  "invalid_rows": []
}
```
