"""Production-safe orchestration for cleaning station batches.

This module intentionally focuses on orchestration, path hygiene, resumability,
and low-I/O execution. Cleaning semantics remain in ``clean_noaa_dataframe``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Any
import uuid

import pandas as pd

from . import __version__
from .cleaning import clean_noaa_dataframe
from .contract_validation import validate_no_sentinel_leakage
from .contracts import (
    CANONICAL_DATASET_CONTRACT,
    DOMAIN_DATASET_CONTRACT,
    QUALITY_REPORT_CONTRACT,
    REQUIRED_ARTIFACT_METADATA_FIELDS,
    RELEASE_MANIFEST_CONTRACT,
    SUCCESS_MARKER_SCHEMA_VERSION,
)
from .constants import to_internal_column
from .deterministic_io import write_deterministic_csv, write_deterministic_parquet
from .domain_split import sanitize_station_slug
from .domains.publisher import write_domain_datasets_from_registry
from .pipeline import _extract_time_columns
from .research_reports import (
    ResearchReportContext,
    domain_quality_report_names,
    generate_domain_quality_reports,
    generate_quality_report,
    write_research_reports,
)


STATION_ID_RE = re.compile(r"^\d{11}$")
PST = timezone(timedelta(hours=-8), name="PST")

MODE_TO_RAW_FILE = {
    "test_csv_dir": "LocationData_Raw.csv",
    "test_parquet_dir": "LocationData_Raw.parquet",
    "batch_parquet_dir": "LocationData_Raw.parquet",
}

MODE_TO_INPUT_FORMAT = {
    "test_csv_dir": "csv",
    "test_parquet_dir": "parquet",
    "batch_parquet_dir": "parquet",
}

RUN_MANIFEST_COLUMNS = [
    "run_id",
    "station_id",
    "input_path",
    "input_format",
    "discovered_at",
    "input_size_bytes",
    "status",
]

RUN_STATUS_COLUMNS = [
    "run_id",
    "station_id",
    "input_path",
    "output_path",
    "status",
    "started_at",
    "completed_at",
    "elapsed_seconds",
    "elapsed_read_seconds",
    "elapsed_clean_seconds",
    "elapsed_domain_split_seconds",
    "elapsed_quality_profile_seconds",
    "elapsed_write_seconds",
    "elapsed_total_seconds",
    "row_count_raw",
    "row_count_cleaned",
    "raw_columns",
    "cleaned_columns",
    "input_size_bytes",
    "cleaned_size_bytes",
    "station_quality_profile_path",
    "success_marker_path",
    "expected_outputs",
    "error_message",
]

RELEASE_MANIFEST_COLUMNS = [
    "artifact_id",
    "artifact_type",
    "artifact_path",
    "schema_version",
    "build_id",
    "input_lineage",
    "row_count",
    "checksum",
    "creation_timestamp",
]

RULE_FAMILIES = [
    "sentinel_handling",
    "arity_validation",
    "domain_validation",
    "range_validation",
    "pattern_validation",
    "width_validation",
    "structural_validation",
    "structural_parser_guard",
    "quality_code_handling",
]

MANDATORY_QUALITY_ARTIFACT_NAMES: tuple[str, ...] = (
    "field_completeness",
    "sentinel_frequency",
    "quality_code_exclusions",
    "domain_usability_summary",
    "station_year_quality",
)

MAX_QUALITY_CODE_EXCLUSION_RATE = 0.25
MIN_DOMAIN_USABLE_ROW_RATE_BY_DOMAIN: dict[str, float] = {
    "core_meteorology": 0.50,
    "wind": 0.00,
    "precipitation": 0.00,
    "clouds_visibility": 0.00,
    "pressure_temperature": 0.00,
    "remarks": 0.00,
}

QUALITY_SCORE_COMPONENT_WEIGHTS: dict[str, float] = {
    "bounds_validity": 0.20,
    "quality_code_exclusion": 0.50,
    "domain_usability": 0.30,
}

QC_REASON_TO_FAMILY = {
    "SENTINEL_MISSING": "sentinel_handling",
    "BAD_QUALITY_CODE": "quality_code_handling",
    "OUT_OF_RANGE": "range_validation",
    "MALFORMED_TOKEN": "width_validation",
}

QUALITY_ARTIFACT_SORT_KEYS: dict[str, tuple[str, ...]] = {
    "field_completeness": ("station_id", "field_identifier"),
    "sentinel_frequency": ("station_id",),
    "quality_code_exclusions": ("station_id",),
    "domain_usability_summary": ("station_id", "domain"),
    "station_year_quality": ("station_id", "year"),
}

TEST_MODES_WITH_HISTORICAL_ORDERING = {"test_csv_dir", "test_parquet_dir"}
TEST_MODE_STATION_ORDER: tuple[str, ...] = (
    "40435099999",
    "94368099999",
    "34880099999",
    "27679099999",
    "83692099999",
    "57067099999",
    "03041099999",
    "82795099999",
    "78724099999",
    "16754399999",
    "01116099999",
)
TEST_MODE_STATION_ORDER_INDEX = {
    station_id: index for index, station_id in enumerate(TEST_MODE_STATION_ORDER)
}


@dataclass(frozen=True)
class RunWriteFlags:
    write_cleaned_station: bool
    write_domain_splits: bool
    write_station_quality_profile: bool
    write_station_reports: bool
    write_global_summary: bool


@dataclass(frozen=True)
class CleaningRunConfig:
    mode: str
    input_root: Path
    input_format: str
    output_root: Path
    reports_root: Path
    quality_profile_root: Path
    manifest_root: Path
    run_id: str
    limit: int | None
    station_ids: tuple[str, ...]
    force: bool
    manifest_first: bool
    manifest_refresh: bool
    write_flags: RunWriteFlags


@dataclass(frozen=True)
class StationPaths:
    station_output_dir: Path
    cleaned_path: Path
    domain_dir: Path
    domain_manifest_path: Path
    quality_profile_path: Path
    reports_dir: Path
    success_marker_path: Path


@dataclass(frozen=True)
class _QualitySchema:
    qc_reason_columns: list[tuple[str, str | None]]
    qc_flag_columns: list[tuple[str, str | None, str | None]]
    null_value_columns: list[tuple[str, str]]
    parse_error_column: str | None


class _QualityProfileBuilder:
    """Build station quality profile summaries with schema-level caching."""

    def __init__(self) -> None:
        self._cache: dict[tuple[str, ...], _QualitySchema] = {}

    def build(self, cleaned: pd.DataFrame, station_id: str) -> dict[str, Any]:
        schema_key = tuple(cleaned.columns)
        schema = self._cache.get(schema_key)
        if schema is None:
            schema = self._build_schema(list(cleaned.columns))
            self._cache[schema_key] = schema

        rows_total = int(len(cleaned))
        structural_mask = pd.Series(False, index=cleaned.index)
        sentinel_mask = pd.Series(False, index=cleaned.index)
        quality_code_mask = pd.Series(False, index=cleaned.index)
        substantive_other_mask = pd.Series(False, index=cleaned.index)

        qc_flag_counts_by_identifier: dict[str, int] = {}
        null_counts_by_identifier: dict[str, int] = {}
        rule_family_impact_counts = {family: 0 for family in RULE_FAMILIES}

        for column, identifier in schema.qc_reason_columns:
            reason_series = cleaned[column].astype("string")
            non_null = reason_series.notna()
            count = int(non_null.sum())
            if identifier is not None and count > 0:
                qc_flag_counts_by_identifier[identifier] = (
                    qc_flag_counts_by_identifier.get(identifier, 0) + count
                )
            sentinel_mask = sentinel_mask | reason_series.eq("SENTINEL_MISSING").fillna(False)
            quality_code_mask = quality_code_mask | reason_series.eq("BAD_QUALITY_CODE").fillna(False)
            substantive_other_mask = substantive_other_mask | (
                non_null
                & ~reason_series.isin(["SENTINEL_MISSING", "BAD_QUALITY_CODE"]).fillna(False)
            )
            value_counts = reason_series.dropna().astype(str).value_counts()
            for reason, reason_count in value_counts.items():
                family = QC_REASON_TO_FAMILY.get(reason)
                if family is not None:
                    rule_family_impact_counts[family] += int(reason_count)

        for column, identifier, family in schema.qc_flag_columns:
            true_mask = cleaned[column].fillna(False).astype(bool)
            count = int(true_mask.sum())
            if identifier is not None and count > 0:
                qc_flag_counts_by_identifier[identifier] = (
                    qc_flag_counts_by_identifier.get(identifier, 0) + count
                )
            if family is not None:
                rule_family_impact_counts[family] += count
            if family == "structural_validation":
                structural_mask = structural_mask | true_mask
            else:
                substantive_other_mask = substantive_other_mask | true_mask

        if schema.parse_error_column is not None:
            parse_error_mask = cleaned[schema.parse_error_column].notna()
            structural_mask = structural_mask | parse_error_mask
            rule_family_impact_counts["structural_parser_guard"] += int(parse_error_mask.sum())

        # Track null impact per identifier at row granularity so repeated
        # multi-part fields do not over-count nulls across part columns.
        null_masks_by_identifier: dict[str, pd.Series] = {}
        for column, identifier in schema.null_value_columns:
            null_mask = cleaned[column].isna()
            if not bool(null_mask.any()):
                continue
            prior_mask = null_masks_by_identifier.get(identifier)
            if prior_mask is None:
                null_masks_by_identifier[identifier] = null_mask
            else:
                null_masks_by_identifier[identifier] = prior_mask | null_mask

        for identifier, null_mask in null_masks_by_identifier.items():
            null_counts_by_identifier[identifier] = int(null_mask.sum())

        substantive_mask = sentinel_mask | quality_code_mask | substantive_other_mask
        rows_with_qc_flags = int(substantive_mask.sum())
        fraction_rows_impacted = (
            float(rows_with_qc_flags) / float(rows_total) if rows_total > 0 else 0.0
        )
        rows_with_structural_impacts = int(structural_mask.sum())
        rows_with_sentinel_impacts = int(sentinel_mask.sum())
        rows_with_quality_code_impacts = int(quality_code_mask.sum())
        rows_with_other_substantive_impacts = int(substantive_other_mask.sum())

        return {
            "station_id": station_id,
            "rows_total": rows_total,
            "rows_with_qc_flags": rows_with_qc_flags,
            "fraction_rows_impacted": fraction_rows_impacted,
            "rows_with_structural_impacts": rows_with_structural_impacts,
            "fraction_rows_structural_impacted": (
                float(rows_with_structural_impacts) / float(rows_total) if rows_total > 0 else 0.0
            ),
            "rows_with_sentinel_impacts": rows_with_sentinel_impacts,
            "rows_with_quality_code_impacts": rows_with_quality_code_impacts,
            "rows_with_other_substantive_impacts": rows_with_other_substantive_impacts,
            "null_counts_by_identifier": dict(sorted(null_counts_by_identifier.items())),
            "qc_flag_counts_by_identifier": dict(sorted(qc_flag_counts_by_identifier.items())),
            "rule_family_impact_counts": rule_family_impact_counts,
        }

    def _build_schema(self, columns: list[str]) -> _QualitySchema:
        qc_reason_columns: list[tuple[str, str | None]] = []
        qc_flag_columns: list[tuple[str, str | None, str | None]] = []
        null_value_columns: list[tuple[str, str]] = []
        parse_error_column: str | None = None

        for column in columns:
            internal = to_internal_column(column)

            if internal == "__parse_error":
                parse_error_column = column
                continue

            if internal.endswith("__qc_reason"):
                qc_reason_columns.append((column, _identifier_from_qc_reason_column(internal)))
                continue

            if internal.startswith("qc_"):
                identifier = _identifier_from_qc_flag_column(internal)
                family = _family_from_qc_flag_column(internal)
                qc_flag_columns.append((column, identifier, family))
                continue

            if "__" not in internal:
                continue
            if internal.endswith("__quality"):
                continue
            if internal.endswith("__qc"):
                continue
            if internal.endswith("__qc_pass"):
                continue
            if internal.endswith("__qc_status"):
                continue

            prefix, suffix = internal.split("__", 1)
            if suffix == "value" or re.fullmatch(r"part\d+", suffix):
                null_value_columns.append((column, prefix))

        return _QualitySchema(
            qc_reason_columns=qc_reason_columns,
            qc_flag_columns=qc_flag_columns,
            null_value_columns=null_value_columns,
            parse_error_column=parse_error_column,
        )


def parse_station_filters(values: list[str] | None) -> tuple[str, ...]:
    if not values:
        return ()
    station_ids: set[str] = set()
    for value in values:
        for token in str(value).split(","):
            station_id = token.strip()
            if not station_id:
                continue
            if not STATION_ID_RE.fullmatch(station_id):
                raise ValueError(f"Invalid --station-id value (expected 11 digits): {station_id}")
            station_ids.add(station_id)
    return tuple(sorted(station_ids))


def default_roots_for_mode(mode: str, run_id: str) -> dict[str, Path]:
    if mode not in MODE_TO_RAW_FILE:
        raise ValueError(f"Unknown mode: {mode}")
    base = Path("release") / f"build_{run_id}"
    return {
        "output_root": base / "canonical_cleaned",
        "reports_root": base / "quality_reports",
        "quality_profile_root": base / "quality_reports" / "station_quality",
        "manifest_root": base / "manifests",
    }


def run_cleaning_run(config: CleaningRunConfig) -> dict[str, Any]:
    _validate_config(config)

    run_started_at = datetime.now(timezone.utc)

    _ensure_dir(config.output_root)
    _ensure_dir(config.reports_root)
    _ensure_dir(config.quality_profile_root)
    _ensure_dir(config.manifest_root)

    run_config_path = config.manifest_root / "run_config.json"
    run_manifest_path = config.manifest_root / "run_manifest.csv"
    run_status_path = config.manifest_root / "run_status.csv"
    build_metadata_path = config.manifest_root / "build_metadata.json"

    config_payload = _run_config_payload(config)
    _validate_or_write_run_config(
        run_config_path=run_config_path,
        config_payload=config_payload,
        manifest_refresh=config.manifest_refresh,
    )

    manifest_rows = _prepare_manifest(
        config=config,
        run_manifest_path=run_manifest_path,
        run_status_path=run_status_path,
    )
    build_timestamp = _resolve_build_timestamp(
        run_id=config.run_id,
        manifest_rows=manifest_rows,
        build_metadata_path=build_metadata_path,
        manifest_refresh=config.manifest_refresh,
    )
    build_metadata_payload = _build_metadata_payload(
        config=config,
        config_payload=config_payload,
        manifest_rows=manifest_rows,
        build_timestamp=build_timestamp,
    )
    _validate_or_write_build_metadata(
        build_metadata_path=build_metadata_path,
        payload=build_metadata_payload,
        manifest_refresh=config.manifest_refresh,
    )

    status_df = _load_status(run_status_path)

    if config.manifest_first and run_manifest_path.exists() and not config.manifest_refresh:
        _log_not_in_manifest_stations(config, manifest_rows)

    print(
        "Starting cleaning-run: "
        f"mode={config.mode} "
        f"input_root={config.input_root} "
        f"output_root={config.output_root} "
        f"reports_root={config.reports_root} "
        f"quality_profile_root={config.quality_profile_root} "
        f"manifest_root={config.manifest_root} "
        f"manifest_first={config.manifest_first} "
        f"write_flags={_write_flags_for_log(config.write_flags)} "
        f"discovered_stations={len(manifest_rows)}"
    )

    quality_builder = _QualityProfileBuilder()

    processed = 0
    skipped = 0
    failed = 0
    processed_for_limit = 0

    for idx, row in enumerate(manifest_rows, start=1):
        station_id = str(row["station_id"])
        input_path = Path(str(row["input_path"]))

        if config.station_ids and station_id not in set(config.station_ids):
            skipped += 1
            print(f"[{idx}/{len(manifest_rows)}] SKIP {station_id}: filtered by station-id")
            status_df = _upsert_status(
                status_df,
                {
                    "run_id": config.run_id,
                    "station_id": station_id,
                    "input_path": str(input_path),
                    "status": "skipped_filtered",
                    "error_message": "filtered by station-id",
                },
            )
            _write_status(run_status_path, status_df)
            continue

        if config.limit is not None and processed_for_limit >= config.limit:
            skipped += 1
            print(f"[{idx}/{len(manifest_rows)}] SKIP {station_id}: limit reached ({config.limit})")
            status_df = _upsert_status(
                status_df,
                {
                    "run_id": config.run_id,
                    "station_id": station_id,
                    "input_path": str(input_path),
                    "status": "skipped_limit",
                    "error_message": f"limit reached ({config.limit})",
                },
            )
            _write_status(run_status_path, status_df)
            continue

        paths = _station_paths(config, station_id)
        expected_outputs = _expected_output_paths(config, paths)

        if not input_path.exists():
            skipped += 1
            print(f"[{idx}/{len(manifest_rows)}] SKIP {station_id}: missing expected raw input")
            status_df = _upsert_status(
                status_df,
                {
                    "run_id": config.run_id,
                    "station_id": station_id,
                    "input_path": str(input_path),
                    "status": "skipped_missing_input",
                    "error_message": "missing expected raw input",
                    "expected_outputs": _json_compact([str(path) for path in expected_outputs]),
                    "success_marker_path": str(paths.success_marker_path),
                },
            )
            _write_status(run_status_path, status_df)
            continue

        prior_status = _status_row(status_df, station_id)
        if (
            not config.force
            and _is_station_completed(
                prior_status=prior_status,
                run_id=config.run_id,
                station_id=station_id,
                expected_outputs=expected_outputs,
                success_marker_path=paths.success_marker_path,
            )
        ):
            skipped += 1
            print(f"[{idx}/{len(manifest_rows)}] SKIP {station_id}: already completed")
            continue

        if (
            not config.force
            and prior_status is not None
            and str(prior_status.get("status", "")) == "completed"
        ):
            print(f"[{idx}/{len(manifest_rows)}] {station_id}: stale completion marker; recomputing")

        processed_for_limit += 1
        started_at = _pst_now_iso()
        station_start = datetime.now(timezone.utc)
        input_size_bytes = _safe_file_size(input_path)

        status_df = _upsert_status(
            status_df,
            {
                "run_id": config.run_id,
                "station_id": station_id,
                "input_path": str(input_path),
                "status": "running",
                "started_at": started_at,
                "input_size_bytes": input_size_bytes,
                "expected_outputs": _json_compact([str(path) for path in expected_outputs]),
                "success_marker_path": str(paths.success_marker_path),
                "error_message": "",
            },
        )
        _write_status(run_status_path, status_df)

        try:
            print(f"[{idx}/{len(manifest_rows)}] {station_id}: begin")
            print(f"[{idx}/{len(manifest_rows)}] {station_id}: read raw input")
            phase_start = datetime.now(timezone.utc)
            raw_df = _read_raw_input(input_path, config.input_format)
            elapsed_read_seconds = (
                datetime.now(timezone.utc) - phase_start
            ).total_seconds()
            row_count_raw = int(len(raw_df))
            raw_columns = int(len(raw_df.columns))

            print(f"[{idx}/{len(manifest_rows)}] {station_id}: clean canonical dataset")
            phase_start = datetime.now(timezone.utc)
            cleaned_df = _clean_canonical_dataset(raw_df)
            validate_no_sentinel_leakage(cleaned_df)
            elapsed_clean_seconds = (
                datetime.now(timezone.utc) - phase_start
            ).total_seconds()
            row_count_cleaned = int(len(cleaned_df))
            cleaned_columns = int(len(cleaned_df.columns))

            profile_payload: dict[str, Any] | None = None
            elapsed_quality_profile_seconds = 0.0
            if config.write_flags.write_station_quality_profile:
                phase_start = datetime.now(timezone.utc)
                profile_payload = quality_builder.build(cleaned_df, station_id)
                elapsed_quality_profile_seconds = (
                    datetime.now(timezone.utc) - phase_start
                ).total_seconds()

            elapsed_write_seconds = 0.0
            if config.write_flags.write_cleaned_station:
                print(f"[{idx}/{len(manifest_rows)}] {station_id}: write cleaned output")
                phase_start = datetime.now(timezone.utc)
                _ensure_dir(paths.station_output_dir)
                _write_cleaned_station(cleaned_df, paths.cleaned_path, config.input_format)
                elapsed_write_seconds += (
                    datetime.now(timezone.utc) - phase_start
                ).total_seconds()

            elapsed_domain_split_seconds = 0.0
            if config.write_flags.write_domain_splits:
                print(f"[{idx}/{len(manifest_rows)}] {station_id}: write domain splits")
                phase_start = datetime.now(timezone.utc)
                _ensure_dir(paths.domain_dir)
                station_name = _station_name(cleaned_df, station_id)
                station_slug = sanitize_station_slug(station_name)
                domain_rows = write_domain_datasets_from_registry(
                    cleaned_df,
                    station_slug=station_slug,
                    station_name=station_name,
                    output_dir=paths.domain_dir,
                    output_format=config.input_format,
                )
                write_deterministic_csv(
                    pd.DataFrame(domain_rows),
                    paths.domain_manifest_path,
                    sort_by=("domain",),
                )
                elapsed_domain_split_seconds = (
                    datetime.now(timezone.utc) - phase_start
                ).total_seconds()

            if config.write_flags.write_station_quality_profile and profile_payload is not None:
                print(f"[{idx}/{len(manifest_rows)}] {station_id}: write station quality profile")
                phase_start = datetime.now(timezone.utc)
                _ensure_dir(config.quality_profile_root)
                _write_json(paths.quality_profile_path, profile_payload)
                elapsed_quality_profile_seconds += (
                    datetime.now(timezone.utc) - phase_start
                ).total_seconds()

            if config.write_flags.write_station_reports:
                print(f"[{idx}/{len(manifest_rows)}] {station_id}: write station reports")
                phase_start = datetime.now(timezone.utc)
                _ensure_dir(paths.reports_dir)
                report_paths = _write_station_reports_from_memory(
                    raw=raw_df,
                    cleaned=cleaned_df,
                    station_id=station_id,
                    reports_dir=paths.reports_dir,
                )
                elapsed_write_seconds += (
                    datetime.now(timezone.utc) - phase_start
                ).total_seconds()

            phase_start = datetime.now(timezone.utc)
            _verify_outputs_exist(expected_outputs)
            _write_success_marker(
                success_path=paths.success_marker_path,
                run_id=config.run_id,
                station_id=station_id,
                input_path=input_path,
                input_format=config.input_format,
                expected_outputs=expected_outputs,
                row_count_raw=row_count_raw,
                row_count_cleaned=row_count_cleaned,
                write_flags=config.write_flags,
            )
            elapsed_write_seconds += (
                datetime.now(timezone.utc) - phase_start
            ).total_seconds()
            cleaned_size_bytes = _safe_file_size(paths.cleaned_path)

            elapsed_total_seconds = (
                datetime.now(timezone.utc) - station_start
            ).total_seconds()
            status_df = _upsert_status(
                status_df,
                {
                    "run_id": config.run_id,
                    "station_id": station_id,
                    "input_path": str(input_path),
                    "output_path": str(paths.cleaned_path if config.write_flags.write_cleaned_station else paths.station_output_dir),
                    "status": "completed",
                    "started_at": started_at,
                    "completed_at": _pst_now_iso(),
                    "elapsed_seconds": round(float(elapsed_total_seconds), 6),
                    "elapsed_read_seconds": round(float(elapsed_read_seconds), 6),
                    "elapsed_clean_seconds": round(float(elapsed_clean_seconds), 6),
                    "elapsed_domain_split_seconds": round(float(elapsed_domain_split_seconds), 6),
                    "elapsed_quality_profile_seconds": round(float(elapsed_quality_profile_seconds), 6),
                    "elapsed_write_seconds": round(float(elapsed_write_seconds), 6),
                    "elapsed_total_seconds": round(float(elapsed_total_seconds), 6),
                    "row_count_raw": row_count_raw,
                    "row_count_cleaned": row_count_cleaned,
                    "raw_columns": raw_columns,
                    "cleaned_columns": cleaned_columns,
                    "input_size_bytes": input_size_bytes,
                    "cleaned_size_bytes": cleaned_size_bytes,
                    "station_quality_profile_path": (
                        str(paths.quality_profile_path)
                        if config.write_flags.write_station_quality_profile
                        else ""
                    ),
                    "success_marker_path": str(paths.success_marker_path),
                    "expected_outputs": _json_compact([str(path) for path in expected_outputs]),
                    "error_message": "",
                },
            )
            _write_status(run_status_path, status_df)

            processed += 1
            print(
                f"[{idx}/{len(manifest_rows)}] DONE {station_id} "
                f"(elapsed={elapsed_total_seconds:.3f}s)"
            )
        except Exception as exc:  # pragma: no cover - branch validated by tests
            failed += 1
            elapsed_seconds = (
                datetime.now(timezone.utc) - station_start
            ).total_seconds()
            status_df = _upsert_status(
                status_df,
                {
                    "run_id": config.run_id,
                    "station_id": station_id,
                    "input_path": str(input_path),
                    "status": "failed",
                    "started_at": started_at,
                    "completed_at": _pst_now_iso(),
                    "elapsed_seconds": round(float(elapsed_seconds), 6),
                    "elapsed_total_seconds": round(float(elapsed_seconds), 6),
                    "input_size_bytes": input_size_bytes,
                    "success_marker_path": str(paths.success_marker_path),
                    "expected_outputs": _json_compact([str(path) for path in expected_outputs]),
                    "error_message": str(exc),
                },
            )
            _write_status(run_status_path, status_df)
            print(
                f"[{idx}/{len(manifest_rows)}] FAIL {station_id}: {exc} "
                f"(elapsed={elapsed_seconds:.3f}s)"
            )

    if config.write_flags.write_global_summary:
        print("Global summary: begin")
        summary = _build_global_summary_from_sidecars(config, status_df)
        global_summary_path = config.reports_root / "global_quality_summary.json"
        _ensure_dir(config.reports_root)
        _write_json(global_summary_path, summary)
        print(f"Global summary: wrote {global_summary_path}")

    quality_frames = _build_mandatory_quality_artifact_frames(config, status_df)
    for artifact_name, frame in quality_frames.items():
        output_path = config.reports_root / f"{artifact_name}.csv"
        write_deterministic_csv(
            frame,
            output_path,
            sort_by=QUALITY_ARTIFACT_SORT_KEYS.get(artifact_name, ("station_id",)),
        )
        print(f"Quality artifact: wrote {output_path}")
    summary_path = config.reports_root / "quality_reports_summary.md"
    _write_quality_reports_summary(summary_path, quality_frames, config.run_id, status_df)
    print(f"Quality artifact: wrote {summary_path}")

    release_manifest_path = config.manifest_root / "release_manifest.csv"
    release_manifest_rows = _build_release_manifest_rows(
        config=config,
        status_df=status_df,
        quality_frames=quality_frames,
        creation_timestamp=build_timestamp,
    )
    _write_release_manifest(release_manifest_path, release_manifest_rows)
    print(f"Release manifest: wrote {release_manifest_path}")

    quality_assessment_path = config.reports_root / "quality_assessment.json"
    quality_assessment = _build_quality_assessment(
        config,
        status_df,
        quality_frames,
        build_metadata_path=build_metadata_path,
    )
    _write_json(quality_assessment_path, quality_assessment)
    print(f"Quality assessment: wrote {quality_assessment_path}")

    file_manifest_path = config.manifest_root / "file_manifest.csv"
    file_manifest_rows = _build_full_file_manifest_rows(
        config=config,
        status_df=status_df,
        creation_timestamp=build_timestamp,
        run_manifest_path=run_manifest_path,
        run_status_path=run_status_path,
        run_config_path=run_config_path,
        build_metadata_path=build_metadata_path,
        release_manifest_path=release_manifest_path,
        quality_assessment_path=quality_assessment_path,
        publication_readiness_path=None,
    )
    _write_full_file_manifest(file_manifest_path, file_manifest_rows)
    print(f"File manifest: wrote {file_manifest_path}")

    publication_readiness_path = config.manifest_root / "publication_readiness_gate.json"
    publication_readiness = _build_publication_readiness_gate(
        config=config,
        status_df=status_df,
        quality_frames=quality_frames,
        run_manifest_path=run_manifest_path,
        run_status_path=run_status_path,
        run_config_path=run_config_path,
        build_metadata_path=build_metadata_path,
        release_manifest_path=release_manifest_path,
        file_manifest_path=file_manifest_path,
        quality_assessment_path=quality_assessment_path,
    )
    _write_json(publication_readiness_path, publication_readiness)
    print(f"Publication readiness: wrote {publication_readiness_path}")

    file_manifest_rows = _build_full_file_manifest_rows(
        config=config,
        status_df=status_df,
        creation_timestamp=build_timestamp,
        run_manifest_path=run_manifest_path,
        run_status_path=run_status_path,
        run_config_path=run_config_path,
        build_metadata_path=build_metadata_path,
        release_manifest_path=release_manifest_path,
        quality_assessment_path=quality_assessment_path,
        publication_readiness_path=publication_readiness_path,
    )
    _write_full_file_manifest(file_manifest_path, file_manifest_rows)
    print(f"File manifest: refreshed {file_manifest_path} with publication gate coverage")

    total_elapsed_seconds = (datetime.now(timezone.utc) - run_started_at).total_seconds()
    total_elapsed_minutes = total_elapsed_seconds / 60.0

    print(
        "cleaning-run summary: "
        f"processed={processed} skipped={skipped} failed={failed} total={len(manifest_rows)} "
        f"elapsed_seconds={total_elapsed_seconds:.3f} "
        f"elapsed_minutes={total_elapsed_minutes:.3f}"
    )
    return {
        "processed": processed,
        "skipped": skipped,
        "failed": failed,
        "total": len(manifest_rows),
        "run_manifest": run_manifest_path,
        "run_status": run_status_path,
        "release_manifest": release_manifest_path,
        "file_manifest": file_manifest_path,
        "publication_readiness_gate": publication_readiness_path,
        "build_metadata": build_metadata_path,
    }


def _write_flags_for_log(flags: RunWriteFlags) -> str:
    payload = {
        "cleaned_station": flags.write_cleaned_station,
        "domain_splits": flags.write_domain_splits,
        "station_quality_profile": flags.write_station_quality_profile,
        "station_reports": flags.write_station_reports,
        "global_summary": flags.write_global_summary,
    }
    return _json_compact(payload)


def _validate_config(config: CleaningRunConfig) -> None:
    if config.mode not in MODE_TO_RAW_FILE:
        raise ValueError(f"Unsupported mode: {config.mode}")
    expected_format = MODE_TO_INPUT_FORMAT[config.mode]
    if config.input_format != expected_format:
        raise ValueError(
            f"Mode {config.mode} requires --input-format {expected_format}, "
            f"got {config.input_format}"
        )
    if not config.input_root.exists() or not config.input_root.is_dir():
        raise FileNotFoundError(f"Input root not found or not a directory: {config.input_root}")
    if config.limit is not None and config.limit <= 0:
        raise ValueError("--limit must be a positive integer")

    input_root = config.input_root.resolve()
    write_roots = {
        "output_root": config.output_root.resolve(),
        "reports_root": config.reports_root.resolve(),
        "quality_profile_root": config.quality_profile_root.resolve(),
        "manifest_root": config.manifest_root.resolve(),
    }
    for label, root in write_roots.items():
        if root == input_root or root.is_relative_to(input_root):
            raise ValueError(
                f"Invalid path hygiene: {label} ({root}) must not be inside input_root ({input_root})."
            )

    _validate_release_layout_roots(config)


def _validate_release_layout_roots(config: CleaningRunConfig) -> None:
    output_root = config.output_root.resolve()
    reports_root = config.reports_root.resolve()
    quality_profile_root = config.quality_profile_root.resolve()
    manifest_root = config.manifest_root.resolve()

    build_root = output_root.parent
    expected_output_root = build_root / "canonical_cleaned"
    expected_reports_root = build_root / "quality_reports"
    expected_quality_profile_root = expected_reports_root / "station_quality"
    expected_manifest_root = build_root / "manifests"

    violations: list[str] = []
    if output_root != expected_output_root:
        violations.append(f"output_root={output_root} (expected {expected_output_root})")
    if reports_root != expected_reports_root:
        violations.append(f"reports_root={reports_root} (expected {expected_reports_root})")
    if quality_profile_root != expected_quality_profile_root:
        violations.append(
            f"quality_profile_root={quality_profile_root} (expected {expected_quality_profile_root})"
        )
    if manifest_root != expected_manifest_root:
        violations.append(f"manifest_root={manifest_root} (expected {expected_manifest_root})")

    if violations:
        raise ValueError(
            "Release layout contract violation: roots must be sibling paths under "
            "`<build_root>/{canonical_cleaned,quality_reports,manifests}` with "
            "`quality_profile_root=<build_root>/quality_reports/station_quality`. "
            + "; ".join(violations)
        )


def _validate_or_write_run_config(
    *,
    run_config_path: Path,
    config_payload: dict[str, Any],
    manifest_refresh: bool,
) -> None:
    incoming = _canonical_config_payload(config_payload)
    if run_config_path.exists():
        existing_raw = json.loads(run_config_path.read_text(encoding="utf-8"))
        existing = _canonical_config_payload(existing_raw)
        if incoming != existing and not manifest_refresh:
            diff = _config_diff(existing, incoming)
            raise ValueError(
                "run_id already exists with a different configuration. "
                "Use a new --run-id or pass --manifest-refresh to rebuild manifests/status. "
                f"Diff: {diff}"
            )
    _write_json(run_config_path, config_payload)


def _build_metadata_payload(
    *,
    config: CleaningRunConfig,
    config_payload: dict[str, Any],
    manifest_rows: list[dict[str, Any]],
    build_timestamp: str,
) -> dict[str, Any]:
    station_ids = sorted(str(row.get("station_id", "")) for row in manifest_rows)
    input_paths = sorted(str(row.get("input_path", "")) for row in manifest_rows)
    payload = {
        "build_id": config.run_id,
        "build_timestamp": build_timestamp,
        "code_revision": _resolve_code_revision(),
        "config_identity": str(config_payload.get("config_fingerprint", "")),
        "source_scope": {
            "mode": config.mode,
            "input_root": str(config.input_root.resolve()),
            "input_format": config.input_format,
            "manifest_station_count": len(manifest_rows),
            "station_ids": station_ids,
            "input_paths": input_paths,
        },
    }
    return payload


def _validate_or_write_build_metadata(
    *,
    build_metadata_path: Path,
    payload: dict[str, Any],
    manifest_refresh: bool,
) -> None:
    build_timestamp = _normalize_iso_timestamp(payload.get("build_timestamp", ""))
    if build_timestamp is None:
        raise ValueError("build_metadata build_timestamp must be an ISO-8601 timestamp with timezone")
    payload["build_timestamp"] = build_timestamp

    incoming = _canonical_build_metadata_payload(payload)
    if build_metadata_path.exists():
        existing_raw = json.loads(build_metadata_path.read_text(encoding="utf-8"))
        existing = _canonical_build_metadata_payload(existing_raw)
        if incoming != existing and not manifest_refresh:
            diff = _config_diff(existing, incoming)
            raise ValueError(
                "run_id already exists with different build metadata. "
                "Use a new --run-id or pass --manifest-refresh to rebuild metadata artifacts. "
                f"Diff: {diff}"
            )
    _write_json(build_metadata_path, payload)


def _prepare_manifest(
    *,
    config: CleaningRunConfig,
    run_manifest_path: Path,
    run_status_path: Path,
) -> list[dict[str, Any]]:
    refresh_manifest = (
        config.manifest_refresh
        or not run_manifest_path.exists()
    )

    if refresh_manifest:
        discovered = _discover_stations(config)
        manifest_rows = [
            {
                "run_id": config.run_id,
                "station_id": station["station_id"],
                "input_path": station["input_path"],
                "input_format": config.input_format,
                "discovered_at": station["discovered_at"],
                "input_size_bytes": station["input_size_bytes"],
                "status": "pending",
            }
            for station in discovered
        ]
        _write_manifest(run_manifest_path, manifest_rows)

        status_rows = [
            {
                "run_id": config.run_id,
                "station_id": row["station_id"],
                "input_path": row["input_path"],
                "output_path": "",
                "status": "pending",
                "started_at": "",
                "completed_at": "",
                "elapsed_seconds": "",
                "elapsed_read_seconds": "",
                "elapsed_clean_seconds": "",
                "elapsed_domain_split_seconds": "",
                "elapsed_quality_profile_seconds": "",
                "elapsed_write_seconds": "",
                "elapsed_total_seconds": "",
                "row_count_raw": "",
                "row_count_cleaned": "",
                "raw_columns": "",
                "cleaned_columns": "",
                "input_size_bytes": row["input_size_bytes"],
                "cleaned_size_bytes": "",
                "station_quality_profile_path": "",
                "success_marker_path": "",
                "expected_outputs": "",
                "error_message": "",
            }
            for row in manifest_rows
        ]
        _write_status(run_status_path, pd.DataFrame(status_rows, columns=RUN_STATUS_COLUMNS))
        return manifest_rows

    return _read_manifest(run_manifest_path)


def _discover_stations(config: CleaningRunConfig) -> list[dict[str, Any]]:
    expected_file = MODE_TO_RAW_FILE[config.mode]
    discovered_at = _pst_now_iso()

    rows: list[dict[str, Any]] = []
    for child in sorted(config.input_root.iterdir(), key=lambda path: path.name):
        if not child.is_dir():
            continue
        if not STATION_ID_RE.fullmatch(child.name):
            print(f"SKIP {child.name}: invalid station directory")
            continue
        input_path = child / expected_file
        if not input_path.exists():
            print(f"SKIP {child.name}: missing expected raw input")
            continue
        input_size_bytes: int | None
        try:
            input_size_bytes = int(input_path.stat().st_size)
        except OSError:
            input_size_bytes = None
        rows.append(
            {
                "station_id": child.name,
                "input_path": str(input_path.resolve()),
                "discovered_at": discovered_at,
                "input_size_bytes": input_size_bytes,
            }
        )
    rows.sort(key=lambda row: str(row["station_id"]))
    rows = _order_test_mode_stations_by_speed_priority(config, rows)
    return rows


def _order_test_mode_stations_by_speed_priority(
    config: CleaningRunConfig,
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if config.mode not in TEST_MODES_WITH_HISTORICAL_ORDERING or not rows:
        return rows
    return sorted(
        rows,
        key=lambda row: (
            TEST_MODE_STATION_ORDER_INDEX.get(
                str(row["station_id"]),
                len(TEST_MODE_STATION_ORDER_INDEX),
            ),
            str(row["station_id"]),
        ),
    )


def _log_not_in_manifest_stations(
    config: CleaningRunConfig,
    manifest_rows: list[dict[str, Any]],
) -> None:
    current = {row["station_id"] for row in _discover_stations(config)}
    snapshotted = {str(row["station_id"]) for row in manifest_rows}
    outside_manifest = sorted(current - snapshotted)
    for station_id in outside_manifest:
        print(f"SKIP {station_id}: not in manifest")


def _station_paths(config: CleaningRunConfig, station_id: str) -> StationPaths:
    station_output_dir = (config.output_root / station_id).resolve()
    cleaned_ext = "csv" if config.input_format == "csv" else "parquet"
    domains_root = config.output_root.parent / "domains"

    return StationPaths(
        station_output_dir=station_output_dir,
        cleaned_path=(station_output_dir / f"LocationData_Cleaned.{cleaned_ext}").resolve(),
        domain_dir=(domains_root / station_id).resolve(),
        domain_manifest_path=(domains_root / station_id / "station_split_manifest.csv").resolve(),
        quality_profile_path=(config.quality_profile_root / f"station_{station_id}.json").resolve(),
        reports_dir=(config.reports_root / station_id).resolve(),
        success_marker_path=(station_output_dir / "_SUCCESS.json").resolve(),
    )


def _expected_output_paths(config: CleaningRunConfig, paths: StationPaths) -> list[Path]:
    expected: list[Path] = []
    if config.write_flags.write_cleaned_station:
        expected.append(paths.cleaned_path)
    if config.write_flags.write_domain_splits:
        expected.append(paths.domain_manifest_path)
    if config.write_flags.write_station_quality_profile:
        expected.append(paths.quality_profile_path)
    if config.write_flags.write_station_reports:
        expected.extend(_station_report_expected_paths(paths.reports_dir))
    return [path.resolve() for path in expected]


def _station_report_expected_paths(reports_dir: Path) -> list[Path]:
    domain_quality_dir = reports_dir / "domain_quality"
    expected = [
        reports_dir / "LocationData_QualityReport.json",
        reports_dir / "LocationData_QualityReport.md",
        reports_dir / "LocationData_QualitySummary.csv",
    ]
    for domain_name in domain_quality_report_names():
        expected.append(domain_quality_dir / f"LocationData_DomainQuality_{domain_name}.json")
        expected.append(domain_quality_dir / f"LocationData_DomainQuality_{domain_name}.md")
    return expected


def _status_row(status_df: pd.DataFrame, station_id: str) -> dict[str, Any] | None:
    if status_df.empty:
        return None
    row = status_df[status_df["station_id"].astype(str) == station_id]
    if row.empty:
        return None
    return row.iloc[0].to_dict()


def _is_station_completed(
    *,
    prior_status: dict[str, Any] | None,
    run_id: str,
    station_id: str,
    expected_outputs: list[Path],
    success_marker_path: Path,
) -> bool:
    if prior_status is None:
        return False
    if str(prior_status.get("status", "")) != "completed":
        return False
    if not _all_exist(expected_outputs):
        return False
    return _validate_success_marker(
        success_path=success_marker_path,
        run_id=run_id,
        station_id=station_id,
        expected_outputs=expected_outputs,
    )


def _validate_success_marker(
    *,
    success_path: Path,
    run_id: str,
    station_id: str,
    expected_outputs: list[Path],
) -> bool:
    if not success_path.exists():
        return False
    try:
        payload = json.loads(success_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if str(payload.get("run_id", "")) != run_id:
        return False
    if str(payload.get("station_id", "")) != station_id:
        return False
    marker_outputs = sorted(str(value) for value in payload.get("expected_outputs", []))
    expected = sorted(str(path.resolve()) for path in expected_outputs)
    return marker_outputs == expected


def _write_success_marker(
    *,
    success_path: Path,
    run_id: str,
    station_id: str,
    input_path: Path,
    input_format: str,
    expected_outputs: list[Path],
    row_count_raw: int,
    row_count_cleaned: int,
    write_flags: RunWriteFlags,
) -> None:
    _ensure_dir(success_path.parent)
    creation_timestamp = _pst_now_iso()
    input_lineage = [str(input_path.resolve())]
    artifact_id = f"station_bundle/{run_id}/{station_id}"
    checksum = _checksum_for_output_bundle(expected_outputs)
    payload = {
        "run_id": run_id,
        "station_id": station_id,
        "artifact_id": artifact_id,
        "schema_version": SUCCESS_MARKER_SCHEMA_VERSION,
        "build_id": run_id,
        "input_lineage": input_lineage,
        "row_count": int(row_count_cleaned),
        "checksum": checksum,
        "creation_timestamp": creation_timestamp,
        "input_path": str(input_path.resolve()),
        "input_format": input_format,
        "completed_at": creation_timestamp,
        "expected_outputs": [str(path.resolve()) for path in expected_outputs],
        "row_count_raw": int(row_count_raw),
        "row_count_cleaned": int(row_count_cleaned),
        "write_flags": {
            "write_cleaned_station": write_flags.write_cleaned_station,
            "write_domain_splits": write_flags.write_domain_splits,
            "write_station_quality_profile": write_flags.write_station_quality_profile,
            "write_station_reports": write_flags.write_station_reports,
            "write_global_summary": write_flags.write_global_summary,
        },
    }
    _validate_release_metadata(payload)
    _write_json(success_path, payload)


def _validate_release_metadata(payload: dict[str, Any]) -> None:
    missing = [field for field in REQUIRED_ARTIFACT_METADATA_FIELDS if field not in payload]
    if missing:
        raise ValueError(f"Missing required release metadata fields: {missing}")


def _checksum_for_output_bundle(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted((item.resolve() for item in paths), key=lambda item: str(item)):
        digest.update(str(path).encode("utf-8"))
        digest.update(b"\0")
        with path.open("rb") as handle:
            while True:
                chunk = handle.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
        digest.update(b"\0")
    return digest.hexdigest()


def _read_raw_input(path: Path, input_format: str) -> pd.DataFrame:
    if input_format == "csv":
        return pd.read_csv(path, low_memory=False)
    if input_format == "parquet":
        return pd.read_parquet(path)
    raise ValueError(f"Unsupported input format: {input_format}")


def _clean_canonical_dataset(raw: pd.DataFrame) -> pd.DataFrame:
    if raw.empty:
        return raw

    strict_mode = True
    raw_for_cleaning = raw.copy()

    if "DATE" in raw_for_cleaning.columns:
        sample_dates = raw_for_cleaning["DATE"].dropna().astype(str).head(10)
        if not sample_dates.empty:
            if sample_dates.str.contains("T").any() or sample_dates.str.contains("-").any():
                strict_mode = False

    if not strict_mode and "DATE" in raw_for_cleaning.columns:
        raw_for_cleaning["DATE_PARSED"] = pd.to_datetime(
            raw_for_cleaning["DATE"], errors="coerce", utc=True
        )

    cleaned = clean_noaa_dataframe(raw_for_cleaning, keep_raw=True, strict_mode=strict_mode)
    cleaned = _extract_time_columns(cleaned, allow_date_parsed_fallback=not strict_mode)

    if strict_mode and len(raw_for_cleaning) > 0 and len(cleaned) == 0:
        permissive = raw.copy()
        if "DATE" in permissive.columns:
            permissive["DATE_PARSED"] = pd.to_datetime(
                permissive["DATE"], errors="coerce", utc=True
            )
        cleaned = clean_noaa_dataframe(permissive, keep_raw=True, strict_mode=False)
        cleaned = _extract_time_columns(cleaned, allow_date_parsed_fallback=True)

    return _normalize_canonical_contract_columns(cleaned)


def _normalize_canonical_contract_columns(cleaned: pd.DataFrame) -> pd.DataFrame:
    if cleaned.empty:
        return cleaned

    normalized = cleaned.copy()
    if "station_id" not in normalized.columns and "STATION" in normalized.columns:
        normalized["station_id"] = normalized["STATION"].astype(str)

    if "YEAR" not in normalized.columns:
        if "Year" in normalized.columns:
            normalized["YEAR"] = pd.to_numeric(normalized["Year"], errors="coerce")
        elif "DATE" in normalized.columns:
            parsed = pd.to_datetime(normalized["DATE"], errors="coerce")
            normalized["YEAR"] = pd.to_numeric(parsed.dt.year, errors="coerce")

    return normalized


def _write_cleaned_station(cleaned: pd.DataFrame, output_path: Path, input_format: str) -> None:
    if input_format == "csv":
        write_deterministic_csv(cleaned, output_path)
        return
    if input_format == "parquet":
        write_deterministic_parquet(_normalize_object_columns_for_parquet(cleaned), output_path)
        return
    raise ValueError(f"Unsupported input format: {input_format}")


def _normalize_object_columns_for_parquet(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame

    normalized = frame.copy()
    for column in normalized.columns:
        series = normalized[column]
        if not pd.api.types.is_object_dtype(series):
            continue
        normalized[column] = series.map(_coerce_to_nullable_text).astype("string")

    return normalized


def _coerce_to_nullable_text(value: object) -> object:
    if value is None:
        return pd.NA
    if isinstance(value, float) and pd.isna(value):
        return pd.NA
    if isinstance(value, (bytes, bytearray)):
        return value.decode("utf-8", errors="replace")
    return str(value)


def _station_name(cleaned: pd.DataFrame, station_id: str) -> str:
    if "station_name" in cleaned.columns and not cleaned["station_name"].dropna().empty:
        return str(cleaned["station_name"].dropna().iloc[0])
    if "NAME" in cleaned.columns and not cleaned["NAME"].dropna().empty:
        return str(cleaned["NAME"].dropna().iloc[0])
    return station_id


def _write_station_reports_from_memory(
    *,
    raw: pd.DataFrame,
    cleaned: pd.DataFrame,
    station_id: str,
    reports_dir: Path,
) -> list[Path]:
    station_name = _station_name(cleaned, station_id)
    context = ResearchReportContext(
        station_id=station_id,
        station_name=station_name,
        access_date=_pst_today(),
        run_date_utc=_pst_now_iso(),
        version=__version__,
        authors="Balaji Kesavan",
    )

    quality_report, quality_summary = generate_quality_report(raw, cleaned, context)
    domain_quality_reports = generate_domain_quality_reports(cleaned, context)

    report_paths = write_research_reports(
        reports_dir,
        quality_report,
        quality_summary,
        aggregation_report=None,
        domain_quality_reports=domain_quality_reports,
    )
    return [path.resolve() for path in report_paths.values()]


def _build_global_summary_from_sidecars(
    config: CleaningRunConfig,
    status_df: pd.DataFrame,
) -> dict[str, Any]:
    profiles = _load_station_quality_profiles(status_df)

    total_stations = len(profiles)
    total_rows = int(sum(int(profile.get("rows_total", 0)) for profile in profiles))

    if total_stations > 0:
        average_row_impact_rate = float(
            sum(float(profile.get("fraction_rows_impacted", 0.0)) for profile in profiles)
        ) / float(total_stations)
        average_structural_impact_rate = float(
            sum(float(profile.get("fraction_rows_structural_impacted", 0.0)) for profile in profiles)
        ) / float(total_stations)
    else:
        average_row_impact_rate = 0.0
        average_structural_impact_rate = 0.0

    identifier_counts: dict[str, int] = {}
    rule_family_totals = {family: 0 for family in RULE_FAMILIES}

    for profile in profiles:
        qc_counts = profile.get("qc_flag_counts_by_identifier", {})
        if isinstance(qc_counts, dict):
            for identifier, value in qc_counts.items():
                count = int(value)
                identifier_counts[str(identifier)] = identifier_counts.get(str(identifier), 0) + count

        family_counts = profile.get("rule_family_impact_counts", {})
        if isinstance(family_counts, dict):
            for family in RULE_FAMILIES:
                rule_family_totals[family] += int(family_counts.get(family, 0))

    top_identifiers = []
    for identifier, count in identifier_counts.items():
        rate = float(count) / float(total_rows) if total_rows > 0 else 0.0
        top_identifiers.append(
            {
                "identifier": identifier,
                "qc_count": int(count),
                "qc_rate": rate,
            }
        )
    top_identifiers.sort(key=lambda row: (row["qc_rate"], row["qc_count"], row["identifier"]), reverse=True)

    return {
        "run_id": config.run_id,
        "total_stations": total_stations,
        "total_rows": total_rows,
        "average_row_impact_rate": average_row_impact_rate,
        "average_structural_impact_rate": average_structural_impact_rate,
        "top_identifiers_by_qc_rate": top_identifiers[:10],
        "rule_family_impact_totals": rule_family_totals,
        "operational_outliers": _build_operational_outlier_summary(status_df),
    }


def _build_operational_outlier_summary(status_df: pd.DataFrame) -> dict[str, list[dict[str, Any]]]:
    if status_df.empty:
        return {
            "largest_input_stations": [],
            "widest_cleaned_schemas": [],
        }

    completed = status_df[status_df["status"].astype(str) == "completed"].copy()
    if completed.empty:
        return {
            "largest_input_stations": [],
            "widest_cleaned_schemas": [],
        }

    numeric_columns = (
        "input_size_bytes",
        "cleaned_columns",
    )
    for column in numeric_columns:
        completed[column] = pd.to_numeric(completed[column], errors="coerce").fillna(0.0)

    summary_columns = [
        "station_id",
        "input_size_bytes",
        "cleaned_columns",
        "row_count_raw",
        "row_count_cleaned",
    ]
    return {
        "largest_input_stations": completed.nlargest(5, "input_size_bytes")[summary_columns].to_dict(orient="records"),
        "widest_cleaned_schemas": completed.nlargest(5, "cleaned_columns")[summary_columns].to_dict(orient="records"),
    }


def _load_station_quality_profiles(status_df: pd.DataFrame) -> list[dict[str, Any]]:
    completed = status_df[status_df["status"].astype(str) == "completed"].copy()
    profile_paths = sorted(
        {
            str(path)
            for path in completed["station_quality_profile_path"].dropna().astype(str)
            if path
        }
    )

    profiles: list[dict[str, Any]] = []
    for path_text in profile_paths:
        path = Path(path_text)
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        profiles.append(payload)
    profiles.sort(key=lambda item: str(item.get("station_id", "")))
    return profiles


def _build_mandatory_quality_artifact_frames(
    config: CleaningRunConfig,
    status_df: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    profiles = _load_station_quality_profiles(status_df)

    field_completeness_rows: list[dict[str, Any]] = []
    sentinel_frequency_rows: list[dict[str, Any]] = []
    quality_code_rows: list[dict[str, Any]] = []
    domain_usability_rows: list[dict[str, Any]] = _build_domain_usability_rows(config, status_df)

    for profile in profiles:
        station_id = str(profile.get("station_id", ""))
        rows_total = int(profile.get("rows_total", 0))
        rows_with_qc = int(profile.get("rows_with_qc_flags", 0))
        rows_with_sentinel = int(profile.get("rows_with_sentinel_impacts", 0))
        rows_with_quality_code = int(profile.get("rows_with_quality_code_impacts", 0))
        null_counts = profile.get("null_counts_by_identifier", {})
        if isinstance(null_counts, dict) and null_counts:
            for field_identifier in sorted(str(identifier) for identifier in null_counts.keys()):
                null_count = int(null_counts.get(field_identifier, 0))
                field_completeness_rows.append(
                    {
                        "run_id": config.run_id,
                        "station_id": station_id,
                        "field_identifier": field_identifier,
                        "rows_total": rows_total,
                        "null_count": null_count,
                        "field_completeness_ratio": (
                            float(rows_total - null_count) / float(rows_total) if rows_total > 0 else 0.0
                        ),
                    }
                )
        else:
            field_completeness_rows.append(
                {
                    "run_id": config.run_id,
                    "station_id": station_id,
                    "field_identifier": "__all__",
                    "rows_total": rows_total,
                    "null_count": rows_with_qc,
                    "field_completeness_ratio": (
                        float(rows_total - rows_with_qc) / float(rows_total) if rows_total > 0 else 0.0
                    ),
                }
            )

        family_counts = profile.get("rule_family_impact_counts", {})
        sentinel_events = int(family_counts.get("sentinel_handling", 0)) if isinstance(family_counts, dict) else 0
        quality_code_events = int(family_counts.get("quality_code_handling", 0)) if isinstance(family_counts, dict) else 0

        sentinel_frequency_rows.append(
            {
                "run_id": config.run_id,
                "station_id": station_id,
                "rows_total": rows_total,
                "sentinel_events": sentinel_events,
                "rows_with_sentinel_impacts": rows_with_sentinel,
                "sentinel_row_rate": (float(rows_with_sentinel) / float(rows_total) if rows_total > 0 else 0.0),
                "sentinel_events_per_row": (float(sentinel_events) / float(rows_total) if rows_total > 0 else 0.0),
            }
        )
        quality_code_rows.append(
            {
                "run_id": config.run_id,
                "station_id": station_id,
                "rows_total": rows_total,
                "quality_code_exclusions": quality_code_events,
                "rows_with_quality_code_exclusions": rows_with_quality_code,
                "quality_code_exclusion_rate": (
                    float(rows_with_quality_code) / float(rows_total) if rows_total > 0 else 0.0
                ),
                "quality_code_exclusion_events_per_row": (
                    float(quality_code_events) / float(rows_total) if rows_total > 0 else 0.0
                ),
            }
        )
    if not domain_usability_rows:
        domain_usability_rows = _fallback_domain_usability_rows(config, status_df)

    field_completeness = _sorted_quality_frame(
        field_completeness_rows,
        ["run_id", "station_id", "field_identifier", "rows_total", "null_count", "field_completeness_ratio"],
    )
    sentinel_frequency = _sorted_quality_frame(
        sentinel_frequency_rows,
        [
            "run_id",
            "station_id",
            "rows_total",
            "sentinel_events",
            "rows_with_sentinel_impacts",
            "sentinel_row_rate",
            "sentinel_events_per_row",
        ],
    )
    quality_code_exclusions = _sorted_quality_frame(
        quality_code_rows,
        [
            "run_id",
            "station_id",
            "rows_total",
            "quality_code_exclusions",
            "rows_with_quality_code_exclusions",
            "quality_code_exclusion_rate",
            "quality_code_exclusion_events_per_row",
        ],
    )
    domain_usability_summary = _sorted_quality_frame(
        domain_usability_rows,
        [
            "run_id",
            "station_id",
            "domain",
            "rows_total",
            "usable_rows",
            "usable_row_rate",
            "artifact_mode",
            "advisory_only",
        ],
    )
    station_year_quality = _build_station_year_quality_frame(config, status_df)

    return {
        "field_completeness": field_completeness,
        "sentinel_frequency": sentinel_frequency,
        "quality_code_exclusions": quality_code_exclusions,
        "domain_usability_summary": domain_usability_summary,
        "station_year_quality": station_year_quality,
    }


def _sorted_quality_frame(rows: list[dict[str, Any]], columns: list[str]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(rows).sort_values("station_id").reset_index(drop=True)


def _build_station_year_quality_frame(
    config: CleaningRunConfig,
    status_df: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    completed = status_df[status_df["status"].astype(str) == "completed"].copy()
    station_ids = sorted(set(completed["station_id"].astype(str).tolist()))
    cleaned_ext = "csv" if config.input_format == "csv" else "parquet"

    for station_id in station_ids:
        cleaned_path = config.output_root / station_id / f"LocationData_Cleaned.{cleaned_ext}"
        if not cleaned_path.exists():
            continue
        try:
            cleaned = _read_raw_input(cleaned_path, config.input_format)
        except Exception:
            continue
        if cleaned.empty:
            continue

        year_series = _year_series(cleaned)
        usable_series = _usable_row_series(cleaned)
        frame = pd.DataFrame({"year": year_series, "usable": usable_series})
        frame = frame.dropna(subset=["year"])
        if frame.empty:
            continue

        grouped = frame.groupby("year", dropna=True)
        for year_value, group in grouped:
            rows_total = int(len(group))
            usable_rows = int(group["usable"].astype(bool).sum())
            rows.append(
                {
                    "run_id": config.run_id,
                    "station_id": station_id,
                    "year": int(year_value),
                    "rows_total": rows_total,
                    "usable_rows": usable_rows,
                    "qc_attrition_rows": rows_total - usable_rows,
                    "usable_row_rate": (float(usable_rows) / float(rows_total) if rows_total > 0 else 0.0),
                }
            )

    if not rows:
        return pd.DataFrame(
            columns=[
                "run_id",
                "station_id",
                "year",
                "rows_total",
                "usable_rows",
                "qc_attrition_rows",
                "usable_row_rate",
            ]
        )
    return pd.DataFrame(rows).sort_values(["station_id", "year"]).reset_index(drop=True)


def _build_domain_usability_rows(
    config: CleaningRunConfig,
    status_df: pd.DataFrame,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    completed = status_df[status_df["status"].astype(str) == "completed"].copy()
    station_ids = sorted(set(completed["station_id"].astype(str).tolist()))

    for station_id in station_ids:
        manifest_path = config.output_root.parent / "domains" / station_id / "station_split_manifest.csv"
        if not manifest_path.exists():
            continue
        try:
            domain_manifest = pd.read_csv(manifest_path)
        except Exception:
            continue
        for record in domain_manifest.to_dict(orient="records"):
            domain_name = str(record.get("domain", ""))
            file_path = Path(str(record.get("file", "")))
            if not file_path.exists():
                continue
            output_format = "parquet" if file_path.suffix.lower() == ".parquet" else "csv"
            try:
                domain_df = _read_raw_input(file_path, output_format)
            except Exception:
                continue
            if domain_df.empty:
                continue
            usable_rows = int(_usable_row_series(domain_df).astype(bool).sum())
            rows_total = int(len(domain_df))
            rows.append(
                {
                    "run_id": config.run_id,
                    "station_id": station_id,
                    "domain": domain_name,
                    "rows_total": rows_total,
                    "usable_rows": usable_rows,
                    "usable_row_rate": (float(usable_rows) / float(rows_total) if rows_total > 0 else 0.0),
                    "artifact_mode": "domain_splits",
                    "advisory_only": False,
                }
            )
    rows.sort(key=lambda item: (str(item.get("station_id", "")), str(item.get("domain", ""))))
    return rows


def _fallback_domain_usability_rows(
    config: CleaningRunConfig,
    status_df: pd.DataFrame,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    completed = status_df[status_df["status"].astype(str) == "completed"].copy()
    station_ids = sorted(set(completed["station_id"].astype(str).tolist()))
    cleaned_ext = "csv" if config.input_format == "csv" else "parquet"

    for station_id in station_ids:
        cleaned_path = config.output_root / station_id / f"LocationData_Cleaned.{cleaned_ext}"
        if not cleaned_path.exists():
            continue
        try:
            cleaned = _read_raw_input(cleaned_path, config.input_format)
        except Exception:
            continue
        rows_total = int(len(cleaned))
        usable_rows = int(_usable_row_series(cleaned).astype(bool).sum()) if rows_total > 0 else 0
        rows.append(
            {
                "run_id": config.run_id,
                "station_id": station_id,
                "domain": "__all__",
                "rows_total": rows_total,
                "usable_rows": usable_rows,
                "usable_row_rate": (float(usable_rows) / float(rows_total) if rows_total > 0 else 0.0),
                "artifact_mode": "fallback_no_domain_splits",
                "advisory_only": True,
            }
        )

    return rows


def _build_release_manifest_rows(
    *,
    config: CleaningRunConfig,
    status_df: pd.DataFrame,
    quality_frames: dict[str, pd.DataFrame],
    creation_timestamp: str,
) -> list[dict[str, Any]]:
    raw_source_lineage_by_station = _raw_source_lineage_by_station(config)
    source_rows, source_artifact_ids_by_station = _source_release_manifest_rows(
        config,
        status_df,
        creation_timestamp=creation_timestamp,
        raw_source_lineage_by_station=raw_source_lineage_by_station,
    )

    canonical_rows = _canonical_release_manifest_rows(
        config,
        status_df,
        creation_timestamp=creation_timestamp,
        source_artifact_ids_by_station=source_artifact_ids_by_station,
    )
    canonical_artifact_ids = {str(row["artifact_id"]) for row in canonical_rows}

    domain_rows = _domain_release_manifest_rows(
        config,
        status_df,
        creation_timestamp=creation_timestamp,
        canonical_artifact_ids=canonical_artifact_ids,
        source_artifact_ids_by_station=source_artifact_ids_by_station,
    )
    domain_artifact_ids = {str(row["artifact_id"]) for row in domain_rows}

    quality_rows = _quality_release_manifest_rows(
        config=config,
        quality_frames=quality_frames,
        creation_timestamp=creation_timestamp,
        canonical_artifact_ids=canonical_artifact_ids,
        domain_artifact_ids=domain_artifact_ids,
    )

    rows = source_rows + canonical_rows + domain_rows + quality_rows
    rows.sort(key=lambda row: str(row["artifact_id"]))
    return rows


def _source_release_manifest_rows(
    config: CleaningRunConfig,
    status_df: pd.DataFrame,
    *,
    creation_timestamp: str,
    raw_source_lineage_by_station: dict[str, list[str]],
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    completed = status_df[status_df["status"].astype(str) == "completed"].copy()
    rows: list[dict[str, Any]] = []
    artifact_ids_by_station: dict[str, str] = {}
    created_at = creation_timestamp

    for record in completed.to_dict(orient="records"):
        station_id = str(record.get("station_id", ""))
        input_path = str(record.get("input_path", ""))
        raw_path = Path(input_path) if input_path else None
        if not station_id or raw_path is None or not raw_path.exists():
            continue
        artifact_id = f"raw_source/{config.run_id}/{station_id}"
        artifact_ids_by_station[station_id] = artifact_id
        rows.append(
            {
                "artifact_id": artifact_id,
                "artifact_type": "raw_source",
                "artifact_path": str(raw_path.resolve()),
                "schema_version": RELEASE_MANIFEST_CONTRACT.schema_version,
                "build_id": config.run_id,
                "input_lineage": _json_compact(
                    raw_source_lineage_by_station.get(station_id, [str(raw_path.resolve())])
                ),
                "row_count": int(_coerce_int(record.get("row_count_raw", 0))),
                "checksum": _checksum_for_output_bundle([raw_path]),
                "creation_timestamp": created_at,
            }
        )

    rows.sort(key=lambda row: str(row["artifact_id"]))
    return rows, artifact_ids_by_station


def _raw_source_lineage_by_station(config: CleaningRunConfig) -> dict[str, list[str]]:
    selection_manifest_path = config.input_root.parent / "selected_stations.csv"
    if not selection_manifest_path.exists():
        return {}

    try:
        selection_manifest = pd.read_csv(selection_manifest_path, dtype=str)
    except Exception:
        return {}

    lineage_by_station: dict[str, list[str]] = {}
    for record in selection_manifest.to_dict(orient="records"):
        station_id = str(record.get("station_id", "")).strip()
        if not station_id:
            continue
        lineage: list[str] = []
        source_path = str(record.get("source_path", "")).strip()
        staged_path = str(record.get("staged_path", "")).strip()
        if source_path:
            lineage.append(source_path)
        if staged_path:
            lineage.append(staged_path)
        if lineage:
            lineage_by_station[station_id] = lineage
    return lineage_by_station


def _canonical_release_manifest_rows(
    config: CleaningRunConfig,
    status_df: pd.DataFrame,
    *,
    creation_timestamp: str,
    source_artifact_ids_by_station: dict[str, str],
) -> list[dict[str, Any]]:
    completed = status_df[status_df["status"].astype(str) == "completed"].copy()
    rows: list[dict[str, Any]] = []
    cleaned_ext = "csv" if config.input_format == "csv" else "parquet"
    created_at = creation_timestamp

    for record in completed.to_dict(orient="records"):
        station_id = str(record.get("station_id", ""))
        input_path = str(record.get("input_path", ""))
        cleaned_path = config.output_root / station_id / f"LocationData_Cleaned.{cleaned_ext}"
        if not station_id or not input_path or not cleaned_path.exists():
            continue
        row_count = int(_coerce_int(record.get("row_count_cleaned", 0)))
        source_artifact_id = source_artifact_ids_by_station.get(station_id, "")
        if source_artifact_id:
            lineage = [source_artifact_id]
        else:
            lineage = [str(Path(input_path).resolve())]
        rows.append(
            {
                "artifact_id": f"canonical_dataset/{config.run_id}/{station_id}",
                "artifact_type": "canonical_dataset",
                "artifact_path": str(cleaned_path.resolve()),
                "schema_version": CANONICAL_DATASET_CONTRACT.schema_version,
                "build_id": config.run_id,
                "input_lineage": _json_compact(lineage),
                "row_count": row_count,
                "checksum": _checksum_for_output_bundle([cleaned_path]),
                "creation_timestamp": created_at,
            }
        )
    rows.sort(key=lambda row: str(row["artifact_id"]))
    return rows


def _domain_release_manifest_rows(
    config: CleaningRunConfig,
    status_df: pd.DataFrame,
    *,
    creation_timestamp: str,
    canonical_artifact_ids: set[str],
    source_artifact_ids_by_station: dict[str, str],
) -> list[dict[str, Any]]:
    completed = status_df[status_df["status"].astype(str) == "completed"].copy()
    rows: list[dict[str, Any]] = []
    created_at = creation_timestamp
    input_paths_by_station = {
        str(record.get("station_id", "")): str(record.get("input_path", ""))
        for record in completed.to_dict(orient="records")
    }

    for station_id in sorted(set(completed["station_id"].astype(str).tolist())):
        manifest_path = config.output_root.parent / "domains" / station_id / "station_split_manifest.csv"
        if not manifest_path.exists():
            continue
        try:
            domain_manifest = pd.read_csv(manifest_path)
        except Exception:
            continue

        for record in domain_manifest.to_dict(orient="records"):
            domain_name = str(record.get("domain", ""))
            file_path = Path(str(record.get("file", "")))
            if not domain_name or not file_path.exists():
                continue
            canonical_artifact_id = f"canonical_dataset/{config.run_id}/{station_id}"
            lineage: list[str]
            if canonical_artifact_id in canonical_artifact_ids:
                lineage = [canonical_artifact_id]
            else:
                source_artifact_id = source_artifact_ids_by_station.get(station_id, "")
                if source_artifact_id:
                    lineage = [source_artifact_id]
                else:
                    raw_input_path = input_paths_by_station.get(station_id, "")
                    lineage = [str(Path(raw_input_path).resolve())] if raw_input_path else []
            rows.append(
                {
                    "artifact_id": f"domain_dataset/{config.run_id}/{station_id}/{domain_name}",
                    "artifact_type": "domain_dataset",
                    "artifact_path": str(file_path.resolve()),
                    "schema_version": DOMAIN_DATASET_CONTRACT.schema_version,
                    "build_id": config.run_id,
                    "input_lineage": _json_compact(lineage),
                    "row_count": int(_coerce_int(record.get("rows", 0))),
                    "checksum": _checksum_for_output_bundle([file_path]),
                    "creation_timestamp": created_at,
                }
            )
    rows.sort(key=lambda row: str(row["artifact_id"]))
    return rows


def _quality_release_manifest_rows(
    *,
    config: CleaningRunConfig,
    quality_frames: dict[str, pd.DataFrame],
    creation_timestamp: str,
    canonical_artifact_ids: set[str],
    domain_artifact_ids: set[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    lineage = sorted(canonical_artifact_ids | domain_artifact_ids)
    created_at = creation_timestamp

    for report_type, frame in sorted(quality_frames.items()):
        artifact_path = config.reports_root / f"{report_type}.csv"
        if not artifact_path.exists():
            continue
        rows.append(
            {
                "artifact_id": f"quality_report/{config.run_id}/{report_type}",
                "artifact_type": "quality_report",
                "artifact_path": str(artifact_path.resolve()),
                "schema_version": QUALITY_REPORT_CONTRACT.schema_version,
                "build_id": config.run_id,
                "input_lineage": _json_compact(lineage),
                "row_count": int(len(frame)),
                "checksum": _checksum_for_output_bundle([artifact_path]),
                "creation_timestamp": created_at,
            }
        )
    rows.sort(key=lambda row: str(row["artifact_id"]))
    return rows


def _build_full_file_manifest_rows(
    *,
    config: CleaningRunConfig,
    status_df: pd.DataFrame,
    creation_timestamp: str,
    run_manifest_path: Path,
    run_status_path: Path,
    run_config_path: Path,
    build_metadata_path: Path,
    release_manifest_path: Path,
    quality_assessment_path: Path | None,
    publication_readiness_path: Path | None,
) -> list[dict[str, Any]]:
    paths: set[Path] = set()
    completed = status_df[status_df["status"].astype(str) == "completed"].copy()

    for record in completed.to_dict(orient="records"):
        input_path = str(record.get("input_path", "")).strip()
        if input_path:
            raw_path = Path(input_path)
            if raw_path.exists():
                paths.add(raw_path.resolve())
        expected_outputs = _parse_lineage_values(record.get("expected_outputs", "[]"))
        for path_text in expected_outputs:
            path = Path(path_text)
            if path.exists():
                resolved = path.resolve()
                paths.add(resolved)
                if resolved.name == "station_split_manifest.csv":
                    try:
                        split_manifest = pd.read_csv(resolved)
                    except Exception:
                        split_manifest = pd.DataFrame()
                    for split_record in split_manifest.to_dict(orient="records"):
                        split_path = Path(str(split_record.get("file", "")))
                        if split_path.exists():
                            paths.add(split_path.resolve())
        success_marker_path = str(record.get("success_marker_path", "")).strip()
        if success_marker_path:
            marker = Path(success_marker_path)
            if marker.exists():
                paths.add(marker.resolve())

    global_paths = [
        run_manifest_path,
        run_status_path,
        run_config_path,
        build_metadata_path,
        release_manifest_path,
        config.reports_root / "quality_reports_summary.md",
    ]
    if quality_assessment_path is not None and quality_assessment_path.exists():
        global_paths.append(quality_assessment_path)
    # Intentionally exclude file_manifest.csv itself to avoid a recursive
    # self-checksum fixed point. publication_readiness_gate.json is included.
    if publication_readiness_path is not None and publication_readiness_path.exists():
        global_paths.append(publication_readiness_path)
    global_paths.extend(config.reports_root / f"{name}.csv" for name in MANDATORY_QUALITY_ARTIFACT_NAMES)
    if config.write_flags.write_global_summary:
        global_paths.append(config.reports_root / "global_quality_summary.json")

    for path in global_paths:
        if path.exists():
            paths.add(path.resolve())

    rows: list[dict[str, Any]] = []
    for path in sorted(paths, key=lambda item: str(item)):
        rows.append(
            {
                "artifact_id": _full_file_manifest_artifact_id(config, path),
                "artifact_type": _full_file_manifest_artifact_type(config, path),
                "artifact_path": str(path),
                "schema_version": RELEASE_MANIFEST_CONTRACT.schema_version,
                "build_id": config.run_id,
                "input_lineage": _json_compact([]),
                "row_count": _file_row_count(path),
                "checksum": _checksum_for_output_bundle([path]),
                "creation_timestamp": creation_timestamp,
            }
        )
    return rows


def _full_file_manifest_artifact_id(config: CleaningRunConfig, path: Path) -> str:
    build_root = config.output_root.parent.resolve()
    input_root = config.input_root.resolve()
    resolved = path.resolve()
    if resolved.is_relative_to(build_root):
        rel = resolved.relative_to(build_root).as_posix()
    elif resolved.is_relative_to(input_root):
        rel = f"inputs/{resolved.relative_to(input_root).as_posix()}"
    else:
        rel = f"external/{resolved.as_posix().lstrip('/').replace(':', '')}"
    return f"build_file/{config.run_id}/{rel}"


def _full_file_manifest_artifact_type(config: CleaningRunConfig, path: Path) -> str:
    resolved = path.resolve()
    output_root = config.output_root.resolve()
    reports_root = config.reports_root.resolve()
    quality_profile_root = config.quality_profile_root.resolve()
    domains_root = (config.output_root.parent / "domains").resolve()

    if resolved == (config.manifest_root / "run_manifest.csv").resolve():
        return "run_manifest"
    if resolved == (config.manifest_root / "run_status.csv").resolve():
        return "run_status"
    if resolved == (config.manifest_root / "run_config.json").resolve():
        return "run_config"
    if resolved == (config.manifest_root / "build_metadata.json").resolve():
        return "build_metadata"
    if resolved == (config.manifest_root / "release_manifest.csv").resolve():
        return "release_manifest"
    if resolved == (config.manifest_root / "publication_readiness_gate.json").resolve():
        return "publication_readiness_gate"

    if resolved.name == "_SUCCESS.json":
        return "success_marker"
    if resolved.name == "station_split_manifest.csv":
        return "station_split_manifest"

    if resolved.is_relative_to(quality_profile_root):
        return "station_quality_profile"
    if resolved.is_relative_to(output_root) and resolved.name.startswith("LocationData_Cleaned."):
        return "canonical_dataset"
    if resolved.is_relative_to(domains_root):
        return "domain_dataset"
    if resolved.is_relative_to(reports_root):
        if resolved.name == "quality_reports_summary.md":
            return "quality_summary"
        if resolved.name == "quality_assessment.json":
            return "quality_assessment"
        if resolved.name == "global_quality_summary.json":
            return "global_quality_summary"
        if resolved.parent == reports_root and resolved.suffix.lower() == ".csv":
            return "quality_report"
        return "station_report"

    return "build_file"


def _file_row_count(path: Path) -> int:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        try:
            return int(len(pd.read_csv(path, low_memory=False)))
        except Exception:
            return 0
    if suffix == ".parquet":
        try:
            return int(len(pd.read_parquet(path)))
        except Exception:
            return 0
    if suffix == ".json":
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return 0
        if isinstance(payload, dict):
            if "row_count" in payload:
                return int(_coerce_int(payload.get("row_count", 0)))
            return 1
        if isinstance(payload, list):
            return int(len(payload))
        return 1
    return 1


def _build_publication_readiness_gate(
    *,
    config: CleaningRunConfig,
    status_df: pd.DataFrame,
    quality_frames: dict[str, pd.DataFrame],
    run_manifest_path: Path,
    run_status_path: Path,
    run_config_path: Path,
    build_metadata_path: Path,
    release_manifest_path: Path,
    file_manifest_path: Path,
    quality_assessment_path: Path,
) -> dict[str, Any]:
    completion_check = _publication_completion_check(status_df)
    generated_at = _build_artifact_timestamp(build_metadata_path, fallback=_pst_now_iso())

    release_manifest = pd.read_csv(release_manifest_path, dtype=str) if release_manifest_path.exists() else pd.DataFrame()
    file_manifest = pd.read_csv(file_manifest_path, dtype=str) if file_manifest_path.exists() else pd.DataFrame()

    coverage_check = _publication_manifest_coverage_check(
        config=config,
        status_df=status_df,
        release_manifest=release_manifest,
        file_manifest=file_manifest,
        run_manifest_path=run_manifest_path,
        run_status_path=run_status_path,
        run_config_path=run_config_path,
        build_metadata_path=build_metadata_path,
        release_manifest_path=release_manifest_path,
    )
    timestamp_check = _publication_timestamp_check(
        build_metadata_path=build_metadata_path,
        release_manifest=release_manifest,
        file_manifest=file_manifest,
    )
    checksum_check = _publication_checksum_check(release_manifest, file_manifest)
    structural_check = _publication_structural_sanity_check(quality_frames)
    build_metadata_check = _publication_build_metadata_completeness_check(build_metadata_path)

    checks = {
        "run_completion": completion_check,
        "artifact_manifest_coverage": coverage_check,
        "timestamp_validity": timestamp_check,
        "checksum_policy_conformance": checksum_check,
        "artifact_structural_sanity": structural_check,
        "build_metadata_completeness": build_metadata_check,
    }
    overall_pass = all(bool(section.get("passed", False)) for section in checks.values())
    scores = _build_publication_scores(checks)
    return {
        "run_id": config.run_id,
        "passed": overall_pass,
        "generated_at": generated_at,
        "quality_assessment_generated": quality_assessment_path.exists(),
        "quality_assessment_path": str(quality_assessment_path.resolve()),
        "checks": checks,
        "scores": scores,
    }


def _publication_completion_check(status_df: pd.DataFrame) -> dict[str, Any]:
    total = int(len(status_df))
    completed = int((status_df["status"].astype(str) == "completed").sum()) if total > 0 else 0
    failed = int((status_df["status"].astype(str) == "failed").sum()) if total > 0 else 0
    skipped = total - completed - failed
    return {
        "passed": failed == 0 and completed == total,
        "total": total,
        "completed": completed,
        "failed": failed,
        "skipped": skipped,
    }


def _publication_manifest_coverage_check(
    *,
    config: CleaningRunConfig,
    status_df: pd.DataFrame,
    release_manifest: pd.DataFrame,
    file_manifest: pd.DataFrame,
    run_manifest_path: Path,
    run_status_path: Path,
    run_config_path: Path,
    build_metadata_path: Path,
    release_manifest_path: Path,
) -> dict[str, Any]:
    filtered_file_manifest = _filtered_file_manifest_for_gate(file_manifest)
    expected_paths: set[str] = set()
    completed = status_df[status_df["status"].astype(str) == "completed"].copy()
    for record in completed.to_dict(orient="records"):
        input_path = str(record.get("input_path", "")).strip()
        if input_path:
            raw_path = Path(input_path)
            if raw_path.exists():
                expected_paths.add(str(raw_path.resolve()))

        expected_outputs = _parse_lineage_values(record.get("expected_outputs", "[]"))
        for path_text in expected_outputs:
            output_path = Path(path_text)
            if output_path.exists():
                resolved_output = output_path.resolve()
                expected_paths.add(str(resolved_output))
                if resolved_output.name == "station_split_manifest.csv":
                    try:
                        split_manifest = pd.read_csv(resolved_output)
                    except Exception:
                        split_manifest = pd.DataFrame()
                    for split_record in split_manifest.to_dict(orient="records"):
                        split_path = Path(str(split_record.get("file", "")))
                        if split_path.exists():
                            expected_paths.add(str(split_path.resolve()))

        success_marker = str(record.get("success_marker_path", "")).strip()
        if success_marker:
            success_path = Path(success_marker)
            if success_path.exists():
                expected_paths.add(str(success_path.resolve()))

    global_paths = [
        run_manifest_path,
        run_status_path,
        run_config_path,
        build_metadata_path,
        release_manifest_path,
        config.reports_root / "quality_reports_summary.md",
    ]
    global_paths.extend(config.reports_root / f"{name}.csv" for name in MANDATORY_QUALITY_ARTIFACT_NAMES)
    if config.write_flags.write_global_summary:
        global_paths.append(config.reports_root / "global_quality_summary.json")
    for path in global_paths:
        if path.exists():
            expected_paths.add(str(path.resolve()))

    file_manifest_paths = (
        set(filtered_file_manifest["artifact_path"].astype(str).tolist())
        if not filtered_file_manifest.empty
        else set()
    )
    release_manifest_paths = (
        set(release_manifest["artifact_path"].astype(str).tolist())
        if not release_manifest.empty
        else set()
    )
    coverage_targets = expected_paths | release_manifest_paths
    missing_paths = sorted(coverage_targets - file_manifest_paths)
    return {
        "passed": not missing_paths,
        "expected_count": len(coverage_targets),
        "manifest_count": len(file_manifest_paths),
        "missing_paths": missing_paths,
    }


def _publication_timestamp_check(
    *,
    build_metadata_path: Path,
    release_manifest: pd.DataFrame,
    file_manifest: pd.DataFrame,
) -> dict[str, Any]:
    filtered_file_manifest = _filtered_file_manifest_for_gate(file_manifest)
    build_timestamp_valid = False
    if build_metadata_path.exists():
        try:
            payload = json.loads(build_metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            payload = {}
        build_timestamp_valid = _normalize_iso_timestamp(payload.get("build_timestamp", "")) is not None

    invalid_release_timestamps = []
    for row in release_manifest.to_dict(orient="records"):
        value = str(row.get("creation_timestamp", ""))
        if _normalize_iso_timestamp(value) is None:
            invalid_release_timestamps.append(str(row.get("artifact_id", "")))

    invalid_file_timestamps = []
    for row in filtered_file_manifest.to_dict(orient="records"):
        value = str(row.get("creation_timestamp", ""))
        if _normalize_iso_timestamp(value) is None:
            invalid_file_timestamps.append(str(row.get("artifact_id", "")))

    return {
        "passed": build_timestamp_valid and not invalid_release_timestamps and not invalid_file_timestamps,
        "build_timestamp_valid": build_timestamp_valid,
        "invalid_release_manifest_rows": invalid_release_timestamps,
        "invalid_file_manifest_rows": invalid_file_timestamps,
    }


def _publication_checksum_check(
    release_manifest: pd.DataFrame,
    file_manifest: pd.DataFrame,
) -> dict[str, Any]:
    invalid_rows: list[str] = []
    filtered_file_manifest = _filtered_file_manifest_for_gate(file_manifest)
    combined = pd.concat([release_manifest, filtered_file_manifest], ignore_index=True, sort=False)
    for row in combined.to_dict(orient="records"):
        artifact_id = str(row.get("artifact_id", ""))
        artifact_path = Path(str(row.get("artifact_path", "")))
        expected_checksum = str(row.get("checksum", ""))
        if not artifact_path.exists():
            invalid_rows.append(artifact_id or "<missing-path>")
            continue
        actual_checksum = _checksum_for_output_bundle([artifact_path])
        if actual_checksum != expected_checksum:
            invalid_rows.append(artifact_id)
    return {
        "passed": not invalid_rows,
        "invalid_rows": sorted(set(invalid_rows)),
    }


def _filtered_file_manifest_for_gate(file_manifest: pd.DataFrame) -> pd.DataFrame:
    if file_manifest.empty or "artifact_type" not in file_manifest.columns:
        return file_manifest
    return file_manifest[
        file_manifest["artifact_type"].astype(str) != "publication_readiness_gate"
    ].copy()


def _publication_structural_sanity_check(
    quality_frames: dict[str, pd.DataFrame],
) -> dict[str, Any]:
    field_frame = quality_frames.get("field_completeness", pd.DataFrame())
    domain_frame = quality_frames.get("domain_usability_summary", pd.DataFrame())
    sentinel_frame = quality_frames.get("sentinel_frequency", pd.DataFrame())
    quality_code_frame = quality_frames.get("quality_code_exclusions", pd.DataFrame())
    station_year_frame = quality_frames.get("station_year_quality", pd.DataFrame())

    field_ok = _frame_ratio_bounds_ok(field_frame, "field_completeness_ratio")
    domain_ok = _frame_ratio_bounds_ok(domain_frame, "usable_row_rate")
    sentinel_rate_ok = _frame_ratio_bounds_ok(sentinel_frame, "sentinel_row_rate")
    quality_rate_ok = _frame_ratio_bounds_ok(quality_code_frame, "quality_code_exclusion_rate")
    station_year_ok = _frame_ratio_bounds_ok(station_year_frame, "usable_row_rate")

    required_frames_present = {
        name: name in quality_frames
        for name in MANDATORY_QUALITY_ARTIFACT_NAMES
    }
    required_columns_present = {
        "field_completeness_ratio": "field_completeness_ratio" in field_frame.columns,
        "domain_usable_row_rate": "usable_row_rate" in domain_frame.columns,
        "sentinel_row_rate": "sentinel_row_rate" in sentinel_frame.columns,
        "quality_code_exclusion_rate": "quality_code_exclusion_rate" in quality_code_frame.columns,
        "station_year_usable_row_rate": "usable_row_rate" in station_year_frame.columns,
    }
    passed = (
        all(required_frames_present.values())
        and all(required_columns_present.values())
        and field_ok
        and domain_ok
        and sentinel_rate_ok
        and quality_rate_ok
        and station_year_ok
    )
    return {
        "passed": passed,
        "required_quality_artifacts_present": required_frames_present,
        "required_columns_present": required_columns_present,
        "field_completeness_ratio_bounds_ok": field_ok,
        "domain_usable_row_rate_bounds_ok": domain_ok,
        "sentinel_row_rate_bounds_ok": sentinel_rate_ok,
        "quality_code_exclusion_rate_bounds_ok": quality_rate_ok,
        "station_year_usable_row_rate_bounds_ok": station_year_ok,
    }


def _publication_build_metadata_completeness_check(build_metadata_path: Path) -> dict[str, Any]:
    required_top_level = [
        "build_id",
        "build_timestamp",
        "code_revision",
        "config_identity",
        "source_scope",
    ]
    required_source_scope = [
        "mode",
        "input_root",
        "input_format",
        "manifest_station_count",
        "station_ids",
        "input_paths",
    ]
    if not build_metadata_path.exists():
        return {
            "passed": False,
            "exists": False,
            "missing_top_level_fields": required_top_level,
            "missing_source_scope_fields": required_source_scope,
            "build_timestamp_valid": False,
        }

    try:
        payload = json.loads(build_metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        payload = {}

    source_scope = payload.get("source_scope", {})
    if not isinstance(source_scope, dict):
        source_scope = {}

    missing_top_level = [field for field in required_top_level if field not in payload]
    missing_source_scope = [field for field in required_source_scope if field not in source_scope]
    build_timestamp_valid = _normalize_iso_timestamp(payload.get("build_timestamp", "")) is not None
    return {
        "passed": (
            not missing_top_level
            and not missing_source_scope
            and build_timestamp_valid
        ),
        "exists": True,
        "missing_top_level_fields": missing_top_level,
        "missing_source_scope_fields": missing_source_scope,
        "build_timestamp_valid": build_timestamp_valid,
    }


def _build_quality_assessment(
    config: CleaningRunConfig,
    status_df: pd.DataFrame,
    quality_frames: dict[str, pd.DataFrame],
    *,
    build_metadata_path: Path,
) -> dict[str, Any]:
    field_frame = quality_frames.get("field_completeness", pd.DataFrame())
    domain_frame = quality_frames.get("domain_usability_summary", pd.DataFrame())
    sentinel_frame = quality_frames.get("sentinel_frequency", pd.DataFrame())
    quality_code_frame = quality_frames.get("quality_code_exclusions", pd.DataFrame())
    station_year_frame = quality_frames.get("station_year_quality", pd.DataFrame())

    field_ok = _frame_ratio_bounds_ok(field_frame, "field_completeness_ratio")
    domain_bounds_ok = _frame_ratio_bounds_ok(domain_frame, "usable_row_rate")

    quality_code_threshold_ok = True
    max_quality_code_exclusion_rate = 0.0
    if not quality_code_frame.empty and "quality_code_exclusion_rate" in quality_code_frame.columns:
        quality_rates = pd.to_numeric(quality_code_frame["quality_code_exclusion_rate"], errors="coerce").fillna(0.0)
        if not quality_rates.empty:
            max_quality_code_exclusion_rate = float(quality_rates.max())
            quality_code_threshold_ok = max_quality_code_exclusion_rate <= MAX_QUALITY_CODE_EXCLUSION_RATE

    domain_threshold_violations: list[dict[str, Any]] = []
    if not domain_frame.empty and {"domain", "usable_row_rate"}.issubset(domain_frame.columns):
        for row in domain_frame.to_dict(orient="records"):
            domain_name = str(row.get("domain", ""))
            observed = float(pd.to_numeric(pd.Series([row.get("usable_row_rate", 0.0)]), errors="coerce").fillna(0.0).iloc[0])
            minimum = float(MIN_DOMAIN_USABLE_ROW_RATE_BY_DOMAIN.get(domain_name, 0.0))
            if observed < minimum:
                domain_threshold_violations.append(
                    {
                        "domain": domain_name,
                        "minimum_usable_row_rate": minimum,
                        "observed_usable_row_rate": observed,
                    }
                )
    domain_thresholds_ok = not domain_threshold_violations

    bounds_validity_score = (float(field_ok) + float(domain_bounds_ok)) / 2.0
    quality_code_exclusion_score = _quality_code_exclusion_score(max_quality_code_exclusion_rate)
    domain_usability_score = _domain_usability_score(domain_threshold_violations)
    quality_score = _weighted_score(
        {
            "bounds_validity": bounds_validity_score,
            "quality_code_exclusion": quality_code_exclusion_score,
            "domain_usability": domain_usability_score,
        },
        QUALITY_SCORE_COMPONENT_WEIGHTS,
    )

    sentinel_heavy_stations = _top_records(
        sentinel_frame,
        sort_column="sentinel_row_rate",
        columns=[
            "station_id",
            "sentinel_row_rate",
            "sentinel_events_per_row",
            "sentinel_events",
            "rows_with_sentinel_impacts",
        ],
    )
    exclusion_heavy_stations = _top_records(
        quality_code_frame,
        sort_column="quality_code_exclusion_rate",
        columns=[
            "station_id",
            "quality_code_exclusion_rate",
            "quality_code_exclusion_events_per_row",
            "quality_code_exclusions",
            "rows_with_quality_code_exclusions",
        ],
    )
    completeness_concerns = _top_records(
        field_frame,
        sort_column="field_completeness_ratio",
        columns=[
            "station_id",
            "field_identifier",
            "field_completeness_ratio",
            "present_row_count",
            "row_count",
        ],
        ascending=True,
    )
    structural_impact_summary, substantive_impact_summary = _station_quality_impact_summaries(config)

    completed = status_df[status_df["status"].astype(str) == "completed"].copy()
    total_completed = int(len(completed))
    return {
        "run_id": config.run_id,
        "generated_at": _build_artifact_timestamp(build_metadata_path, fallback=_pst_now_iso()),
        "advisory_only": True,
        "threshold_policy": "advisory",
        "completed_station_count": total_completed,
        "threshold_evaluations": {
            "field_completeness_ratio_bounds_ok": field_ok,
            "domain_usable_row_rate_bounds_ok": domain_bounds_ok,
            "quality_code_exclusion_rate_threshold_ok": quality_code_threshold_ok,
            "max_quality_code_exclusion_rate": max_quality_code_exclusion_rate,
            "max_quality_code_exclusion_rate_allowed": MAX_QUALITY_CODE_EXCLUSION_RATE,
            "domain_usability_thresholds_ok": domain_thresholds_ok,
            "domain_usability_thresholds": MIN_DOMAIN_USABLE_ROW_RATE_BY_DOMAIN,
            "domain_usability_threshold_violations": domain_threshold_violations,
        },
        "summary_scores": {
            "quality_score": quality_score,
            "quality_score_components": {
                "bounds_validity": bounds_validity_score,
                "quality_code_exclusion": quality_code_exclusion_score,
                "domain_usability": domain_usability_score,
            },
            "quality_score_weights": QUALITY_SCORE_COMPONENT_WEIGHTS,
        },
        "exclusion_rate_summaries": {
            "top_quality_code_exclusion_stations": exclusion_heavy_stations,
        },
        "sentinel_heavy_summaries": {
            "top_sentinel_stations": sentinel_heavy_stations,
        },
        "completeness_concerns": {
            "lowest_field_completeness": completeness_concerns,
        },
        "impact_summaries": {
            "structural_vs_substantive": {
                "highest_structural_impact_stations": structural_impact_summary,
                "highest_substantive_impact_stations": substantive_impact_summary,
            }
        },
    }


def _build_publication_scores(checks: dict[str, dict[str, Any]]) -> dict[str, Any]:
    integrity_check_names = (
        "run_completion",
        "artifact_manifest_coverage",
        "timestamp_validity",
        "checksum_policy_conformance",
        "artifact_structural_sanity",
        "build_metadata_completeness",
    )
    integrity_components = {
        name: float(bool(checks.get(name, {}).get("passed", False)))
        for name in integrity_check_names
    }
    integrity_score = _mean_score(integrity_components.values())
    return {
        "overall_score": integrity_score,
        "integrity_score": integrity_score,
        "integrity_components": integrity_components,
        "scale": "0_to_1",
    }


def _quality_code_exclusion_score(max_quality_code_exclusion_rate: float) -> float:
    reference = float(MAX_QUALITY_CODE_EXCLUSION_RATE)
    if reference <= 0.0:
        return 1.0
    ratio = max(0.0, max_quality_code_exclusion_rate) / reference
    return _clamp01(1.0 / (1.0 + ratio))


def _domain_usability_score(domain_threshold_violations: list[dict[str, Any]]) -> float:
    if not domain_threshold_violations:
        return 1.0

    deficit_ratios: list[float] = []
    for violation in domain_threshold_violations:
        minimum = float(violation.get("minimum_usable_row_rate", 0.0))
        observed = float(violation.get("observed_usable_row_rate", 0.0))
        if minimum <= 0.0:
            continue
        deficit = max(0.0, minimum - observed)
        deficit_ratios.append(_clamp01(deficit / minimum))

    if not deficit_ratios:
        return 1.0
    return _clamp01(1.0 - (sum(deficit_ratios) / len(deficit_ratios)))


def _frame_ratio_bounds_ok(frame: pd.DataFrame, column: str) -> bool:
    if column not in frame.columns:
        return False
    if frame.empty:
        return True
    values = pd.to_numeric(frame[column], errors="coerce")
    if values.isna().any():
        return False
    return bool(values.between(0.0, 1.0, inclusive="both").all())


def _top_records(
    frame: pd.DataFrame,
    *,
    sort_column: str,
    columns: list[str],
    ascending: bool = False,
    limit: int = 10,
) -> list[dict[str, Any]]:
    if frame.empty or sort_column not in frame.columns:
        return []
    working = frame.copy()
    working[sort_column] = pd.to_numeric(working[sort_column], errors="coerce")
    working = working.dropna(subset=[sort_column])
    if working.empty:
        return []
    selected_columns = [column for column in columns if column in working.columns]
    if not selected_columns:
        return []
    working = working.sort_values(
        by=[sort_column] + [column for column in selected_columns if column != sort_column],
        ascending=[ascending] + [True] * max(0, len(selected_columns) - 1),
        kind="mergesort",
    ).head(limit)
    return _records_for_json(working[selected_columns])


def _station_year_impact_summary(frame: pd.DataFrame, column: str, limit: int = 10) -> list[dict[str, Any]]:
    if frame.empty or column not in frame.columns:
        return []
    columns = [
        "station_id",
        "year",
        column,
        "rows_total",
        "rows_with_qc_flags",
        "rows_with_structural_impacts",
        "rows_with_sentinel_impacts",
        "rows_with_quality_code_impacts",
        "rows_with_other_substantive_impacts",
    ]
    return _top_records(
        frame,
        sort_column=column,
        columns=columns,
        ascending=False,
        limit=limit,
    )


def _station_quality_impact_summaries(
    config: CleaningRunConfig,
    limit: int = 10,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    if not config.quality_profile_root.exists():
        return ([], [])

    for path in sorted(config.quality_profile_root.glob("station_*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        rows.append(
            {
                "station_id": str(payload.get("station_id", "")),
                "rows_total": _coerce_int(payload.get("rows_total", 0)),
                "rows_with_qc_flags": _coerce_int(payload.get("rows_with_qc_flags", 0)),
                "fraction_rows_impacted": float(payload.get("fraction_rows_impacted", 0.0) or 0.0),
                "rows_with_structural_impacts": _coerce_int(payload.get("rows_with_structural_impacts", 0)),
                "fraction_rows_structural_impacted": float(
                    payload.get("fraction_rows_structural_impacted", 0.0) or 0.0
                ),
                "rows_with_sentinel_impacts": _coerce_int(payload.get("rows_with_sentinel_impacts", 0)),
                "rows_with_quality_code_impacts": _coerce_int(
                    payload.get("rows_with_quality_code_impacts", 0)
                ),
                "rows_with_other_substantive_impacts": _coerce_int(
                    payload.get("rows_with_other_substantive_impacts", 0)
                ),
            }
        )

    if not rows:
        return ([], [])

    frame = pd.DataFrame(rows)
    structural = _top_records(
        frame,
        sort_column="fraction_rows_structural_impacted",
        columns=[
            "station_id",
            "fraction_rows_structural_impacted",
            "rows_with_structural_impacts",
            "rows_total",
        ],
        limit=limit,
    )
    substantive = _top_records(
        frame,
        sort_column="fraction_rows_impacted",
        columns=[
            "station_id",
            "fraction_rows_impacted",
            "rows_with_qc_flags",
            "rows_with_sentinel_impacts",
            "rows_with_quality_code_impacts",
            "rows_with_other_substantive_impacts",
            "rows_total",
        ],
        limit=limit,
    )
    return (structural, substantive)


def _records_for_json(frame: pd.DataFrame) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for record in frame.to_dict(orient="records"):
        normalized: dict[str, Any] = {}
        for key, value in record.items():
            if pd.isna(value):
                normalized[str(key)] = None
            elif isinstance(value, (pd.Timestamp, datetime)):
                normalized[str(key)] = str(value.isoformat())
            elif hasattr(value, "item"):
                normalized[str(key)] = value.item()
            else:
                normalized[str(key)] = value
        records.append(normalized)
    return records


def _weighted_score(values: dict[str, float], weights: dict[str, float]) -> float:
    numerator = 0.0
    denominator = 0.0
    for key, weight in weights.items():
        weight_value = max(0.0, float(weight))
        denominator += weight_value
        numerator += _clamp01(float(values.get(key, 0.0))) * weight_value
    if denominator <= 0.0:
        return 0.0
    return _clamp01(numerator / denominator)


def _mean_score(values: Any) -> float:
    numeric_values = [_clamp01(float(value)) for value in values]
    if not numeric_values:
        return 0.0
    return _clamp01(sum(numeric_values) / len(numeric_values))


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _year_series(cleaned: pd.DataFrame) -> pd.Series:
    if "Year" in cleaned.columns:
        return pd.to_numeric(cleaned["Year"], errors="coerce")
    if "YEAR" in cleaned.columns:
        return pd.to_numeric(cleaned["YEAR"], errors="coerce")
    if "DATE" in cleaned.columns:
        parsed = pd.to_datetime(cleaned["DATE"], errors="coerce")
        return pd.to_numeric(parsed.dt.year, errors="coerce")
    return pd.Series([pd.NA] * len(cleaned), index=cleaned.index, dtype="object")


def _usable_row_series(cleaned: pd.DataFrame) -> pd.Series:
    if "row_has_any_usable_metric" in cleaned.columns:
        return cleaned["row_has_any_usable_metric"].fillna(False).astype(bool)
    metric_candidates = cleaned.select_dtypes(include=["number", "boolean"]).columns.tolist()
    excluded = {"YEAR", "Year", "MonthNum", "Day", "Hour"}
    metric_columns = [column for column in metric_candidates if column not in excluded]
    if not metric_columns:
        text_excluded = {
            "station_id",
            "STATION",
            "station_name",
            "NAME",
            "DATE",
            "date",
            "YEAR",
            "Year",
            "year",
            "MonthNum",
            "month",
            "Day",
            "day",
            "Hour",
            "hour",
        }
        text_columns = [column for column in cleaned.columns if column not in text_excluded]
        if not text_columns:
            return pd.Series(False, index=cleaned.index, dtype="bool")
        text_presence = cleaned[text_columns].apply(_has_non_empty_value)
        return text_presence.any(axis=1)
    return cleaned[metric_columns].notna().any(axis=1)


def _has_non_empty_value(series: pd.Series) -> pd.Series:
    text = series.astype("string").str.strip()
    normalized = text.str.lower()
    return series.notna() & text.ne("") & normalized.ne("nan") & normalized.ne("none")


def _write_quality_reports_summary(
    output_path: Path,
    quality_frames: dict[str, pd.DataFrame],
    run_id: str,
    status_df: pd.DataFrame,
) -> None:
    lines = [
        "# Quality Reports Summary",
        "",
        f"- run_id: `{run_id}`",
    ]
    for artifact_name in MANDATORY_QUALITY_ARTIFACT_NAMES:
        frame = quality_frames.get(artifact_name, pd.DataFrame())
        lines.append(f"- {artifact_name}: {len(frame)} rows")
    completed = status_df[status_df["status"].astype(str) == "completed"].copy()
    if not completed.empty:
        completed["input_size_bytes"] = pd.to_numeric(completed["input_size_bytes"], errors="coerce").fillna(0.0)
        completed["cleaned_columns"] = pd.to_numeric(completed["cleaned_columns"], errors="coerce").fillna(0.0)

    quality_code_frame = quality_frames.get("quality_code_exclusions", pd.DataFrame())
    sentinel_frame = quality_frames.get("sentinel_frequency", pd.DataFrame())
    field_frame = quality_frames.get("field_completeness", pd.DataFrame())

    def _top_rows(frame: pd.DataFrame, sort_column: str, columns: list[str], limit: int = 3) -> list[str]:
        if frame.empty or sort_column not in frame.columns:
            return []
        top = frame.sort_values(sort_column, ascending=False).head(limit)
        rendered: list[str] = []
        for row in top.to_dict(orient="records"):
            values = ", ".join(f"{column}={row.get(column)}" for column in columns)
            rendered.append(f"- {values}")
        return rendered

    lines.extend(
        [
            "",
            "## Highlights",
        ]
    )
    if not completed.empty:
        lines.append("")
        lines.append("### Operational Outliers")
        lines.append("- largest input stations:")
        lines.extend(
            _top_rows(
                completed,
                "input_size_bytes",
                ["station_id", "input_size_bytes", "row_count_raw"],
            )
        )
        lines.append("- widest cleaned schemas:")
        lines.extend(
            _top_rows(
                completed,
                "cleaned_columns",
                ["station_id", "cleaned_columns", "row_count_cleaned"],
            )
        )
    if not quality_code_frame.empty:
        lines.append("")
        lines.append("### Highest Quality-Code Exclusion Rates")
        lines.extend(
            _top_rows(
                quality_code_frame,
                "quality_code_exclusion_rate",
                ["station_id", "quality_code_exclusion_rate", "quality_code_exclusions"],
            )
        )
    if not sentinel_frame.empty:
        lines.append("")
        lines.append("### Highest Sentinel Event Rates")
        lines.extend(
            _top_rows(
                sentinel_frame,
                "sentinel_events_per_row",
                ["station_id", "sentinel_events_per_row", "sentinel_events", "sentinel_row_rate"],
            )
        )
    if not field_frame.empty:
        field_low = field_frame.sort_values("field_completeness_ratio", ascending=True).head(3)
        if not field_low.empty:
            lines.append("")
            lines.append("### Lowest Field Completeness")
            for row in field_low.to_dict(orient="records"):
                lines.append(
                    "- "
                    + ", ".join(
                        [
                            f"station_id={row.get('station_id')}",
                            f"field_identifier={row.get('field_identifier')}",
                            f"field_completeness_ratio={row.get('field_completeness_ratio')}",
                        ]
                    )
                )
    domain_frame = quality_frames.get("domain_usability_summary", pd.DataFrame())
    if not domain_frame.empty and {"artifact_mode", "advisory_only"}.issubset(domain_frame.columns):
        fallback_rows = domain_frame[domain_frame["artifact_mode"].astype(str) == "fallback_no_domain_splits"]
        if not fallback_rows.empty:
            lines.append("")
            lines.append(
                "### Domain Usability Mode\n"
                "- advisory_only=true because domain splits were disabled; `__all__` rows summarize canonical usability only."
            )
    lines.append("")
    _ensure_dir(output_path.parent)
    output_path.write_text("\n".join(lines), encoding="utf-8")


def _write_release_manifest(path: Path, rows: list[dict[str, Any]]) -> None:
    frame = pd.DataFrame(rows)
    for column in RELEASE_MANIFEST_COLUMNS:
        if column not in frame.columns:
            frame[column] = pd.NA
    if frame.empty:
        frame = pd.DataFrame(columns=RELEASE_MANIFEST_COLUMNS)
    else:
        frame = frame[RELEASE_MANIFEST_COLUMNS]
    _validate_release_manifest_frame(frame)
    _validate_release_manifest_lineage(frame)
    write_deterministic_csv(frame, path, sort_by=("artifact_id",))


def _write_full_file_manifest(path: Path, rows: list[dict[str, Any]]) -> None:
    frame = pd.DataFrame(rows)
    for column in RELEASE_MANIFEST_COLUMNS:
        if column not in frame.columns:
            frame[column] = pd.NA
    if frame.empty:
        frame = pd.DataFrame(columns=RELEASE_MANIFEST_COLUMNS)
    else:
        frame = frame[RELEASE_MANIFEST_COLUMNS]
    _validate_release_manifest_frame(frame)
    write_deterministic_csv(frame, path, sort_by=("artifact_id",))


def _validate_release_manifest_frame(frame: pd.DataFrame) -> None:
    missing = [
        column
        for column in RELEASE_MANIFEST_CONTRACT.required_columns
        if column not in frame.columns
    ]
    if missing:
        raise ValueError(f"Release manifest contract violation: missing columns {missing}")

    if frame.empty:
        return

    invalid_rows = frame[
        frame["creation_timestamp"].apply(
            lambda value: _normalize_iso_timestamp(value) is None
        )
    ]
    if not invalid_rows.empty:
        artifact_ids = sorted(str(value) for value in invalid_rows["artifact_id"].astype(str).tolist())
        raise ValueError(
            "Release manifest contract violation: invalid creation_timestamp for "
            f"artifacts {artifact_ids}"
        )

    duplicate_rows = frame[frame["artifact_id"].astype(str).duplicated(keep=False)]
    if not duplicate_rows.empty:
        artifact_ids = sorted(set(duplicate_rows["artifact_id"].astype(str).tolist()))
        raise ValueError(
            "Release manifest contract violation: duplicate artifact_id values "
            f"{artifact_ids}"
        )


def _validate_release_manifest_lineage(frame: pd.DataFrame) -> None:
    if frame.empty:
        return

    artifacts = frame.to_dict(orient="records")
    artifact_ids = {str(record.get("artifact_id", "")) for record in artifacts}
    canonical_ids = {
        str(record.get("artifact_id", ""))
        for record in artifacts
        if str(record.get("artifact_type", "")) == "canonical_dataset"
    }
    source_ids = {
        str(record.get("artifact_id", ""))
        for record in artifacts
        if str(record.get("artifact_type", "")) == "raw_source"
    }
    domain_ids = {
        str(record.get("artifact_id", ""))
        for record in artifacts
        if str(record.get("artifact_type", "")) == "domain_dataset"
    }

    for record in artifacts:
        artifact_id = str(record.get("artifact_id", ""))
        artifact_type = str(record.get("artifact_type", ""))
        lineage = _parse_lineage_values(record.get("input_lineage", "[]"))

        reference_ids = [
            value
            for value in lineage
            if value.startswith("raw_source/")
            or value.startswith("canonical_dataset/")
            or value.startswith("domain_dataset/")
        ]
        unresolved = [value for value in reference_ids if value not in artifact_ids]
        if unresolved:
            raise ValueError(
                f"Release manifest lineage violation for {artifact_id}: unresolved lineage {unresolved}"
            )

        if artifact_type == "canonical_dataset" and source_ids:
            if not any(value in source_ids for value in lineage):
                raise ValueError(
                    f"Release manifest lineage violation for {artifact_id}: "
                    "canonical artifacts must reference raw source artifacts"
                )

        if artifact_type == "domain_dataset" and canonical_ids:
            if not any(value in canonical_ids for value in lineage):
                raise ValueError(
                    f"Release manifest lineage violation for {artifact_id}: "
                    "domain artifacts must reference canonical artifacts"
                )
        if artifact_type == "domain_dataset" and not canonical_ids and source_ids:
            if not any(value in source_ids for value in lineage):
                raise ValueError(
                    f"Release manifest lineage violation for {artifact_id}: "
                    "domain artifacts must reference raw source artifacts when canonical artifacts are absent"
                )

        if artifact_type == "quality_report" and canonical_ids:
            if not any(value in canonical_ids for value in lineage):
                raise ValueError(
                    f"Release manifest lineage violation for {artifact_id}: "
                    "quality artifacts must reference canonical artifacts"
                )
            if domain_ids and not any(value in domain_ids for value in lineage):
                raise ValueError(
                    f"Release manifest lineage violation for {artifact_id}: "
                    "quality artifacts must reference domain artifacts when present"
                )


def _parse_lineage_values(raw_value: Any) -> list[str]:
    if raw_value is None:
        return []
    text = str(raw_value).strip()
    if not text:
        return []
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, list):
        return []
    return [str(value) for value in payload]


def _verify_outputs_exist(paths: list[Path]) -> None:
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing expected output(s): " + ", ".join(missing))


def _all_exist(paths: list[Path]) -> bool:
    return all(path.exists() for path in paths)


def _status_defaults() -> dict[str, Any]:
    return {
        "run_id": "",
        "station_id": "",
        "input_path": "",
        "output_path": "",
        "status": "",
        "started_at": "",
        "completed_at": "",
        "elapsed_seconds": "",
        "elapsed_read_seconds": "",
        "elapsed_clean_seconds": "",
        "elapsed_domain_split_seconds": "",
        "elapsed_quality_profile_seconds": "",
        "elapsed_write_seconds": "",
        "elapsed_total_seconds": "",
        "row_count_raw": "",
        "row_count_cleaned": "",
        "raw_columns": "",
        "cleaned_columns": "",
        "input_size_bytes": "",
        "cleaned_size_bytes": "",
        "station_quality_profile_path": "",
        "success_marker_path": "",
        "expected_outputs": "",
        "error_message": "",
    }


def _upsert_status(status_df: pd.DataFrame, updates: dict[str, Any]) -> pd.DataFrame:
    if status_df.empty:
        base = _status_defaults()
        for key, value in updates.items():
            base[key] = _status_field_value(value)
        return pd.DataFrame([base], columns=RUN_STATUS_COLUMNS)

    station_id = str(updates.get("station_id", ""))
    if not station_id:
        raise ValueError("status update requires station_id")

    work = status_df.copy()
    mask = work["station_id"].astype(str) == station_id

    if not mask.any():
        base = _status_defaults()
        for key, value in updates.items():
            base[key] = _status_field_value(value)
        append_df = pd.DataFrame([base], columns=RUN_STATUS_COLUMNS)
        work = pd.concat([work, append_df], ignore_index=True)
        return work

    index = work[mask].index[0]
    for key, value in updates.items():
        if key not in RUN_STATUS_COLUMNS:
            continue
        work.at[index, key] = _status_field_value(value)
    return work


def _status_field_value(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _coerce_int(value: Any) -> int:
    if value is None:
        return 0
    try:
        if pd.isna(value):
            return 0
    except TypeError:
        pass
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return int(float(str(value)))
        except (TypeError, ValueError):
            return 0


def _safe_file_size(path: Path) -> int:
    try:
        return int(path.stat().st_size)
    except OSError:
        return 0


def _write_manifest(path: Path, rows: list[dict[str, Any]]) -> None:
    frame = pd.DataFrame(rows)
    for column in RUN_MANIFEST_COLUMNS:
        if column not in frame.columns:
            frame[column] = pd.NA
    if frame.empty:
        frame = pd.DataFrame(columns=RUN_MANIFEST_COLUMNS)
    else:
        frame = frame[RUN_MANIFEST_COLUMNS]
    write_deterministic_csv(frame, path, sort_by=("station_id",))


def _read_manifest(path: Path) -> list[dict[str, Any]]:
    frame = pd.read_csv(path, dtype=str)
    for column in RUN_MANIFEST_COLUMNS:
        if column not in frame.columns:
            frame[column] = pd.NA
    frame = frame[RUN_MANIFEST_COLUMNS].sort_values("station_id", kind="stable")
    return frame.to_dict(orient="records")


def _load_status(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=RUN_STATUS_COLUMNS)
    frame = pd.read_csv(path, dtype=str)
    for column in RUN_STATUS_COLUMNS:
        if column not in frame.columns:
            frame[column] = ""
    return frame[RUN_STATUS_COLUMNS].sort_values("station_id", kind="stable")


def _write_status(path: Path, status_df: pd.DataFrame) -> None:
    frame = status_df.copy()
    for column in RUN_STATUS_COLUMNS:
        if column not in frame.columns:
            frame[column] = ""
    if frame.empty:
        frame = pd.DataFrame(columns=RUN_STATUS_COLUMNS)
    else:
        frame = frame[RUN_STATUS_COLUMNS]
    write_deterministic_csv(frame, path, sort_by=("station_id",))


def _run_config_payload(config: CleaningRunConfig) -> dict[str, Any]:
    payload = {
        "run_id": config.run_id,
        "mode": config.mode,
        "input_root": str(config.input_root.resolve()),
        "input_format": config.input_format,
        "station_filters": list(config.station_ids),
        "limit": config.limit,
        "manifest_first": config.manifest_first,
        "write_flags": {
            "write_cleaned_station": config.write_flags.write_cleaned_station,
            "write_domain_splits": config.write_flags.write_domain_splits,
            "write_station_quality_profile": config.write_flags.write_station_quality_profile,
            "write_station_reports": config.write_flags.write_station_reports,
            "write_global_summary": config.write_flags.write_global_summary,
        },
        "roots": {
            "output_root": str(config.output_root.resolve()),
            "reports_root": str(config.reports_root.resolve()),
            "quality_profile_root": str(config.quality_profile_root.resolve()),
            "manifest_root": str(config.manifest_root.resolve()),
        },
    }
    payload["config_fingerprint"] = _json_compact(_canonical_config_payload(payload))
    return payload


def _canonical_config_payload(payload: dict[str, Any]) -> dict[str, Any]:
    canonical = {
        "mode": str(payload.get("mode", "")),
        "input_root": str(payload.get("input_root", "")),
        "input_format": str(payload.get("input_format", "")),
        "station_filters": sorted(str(value) for value in payload.get("station_filters", [])),
        "limit": payload.get("limit"),
        "manifest_first": bool(payload.get("manifest_first", False)),
        "write_flags": {
            key: bool(value)
            for key, value in sorted(dict(payload.get("write_flags", {})).items())
        },
        "roots": {
            key: str(value)
            for key, value in sorted(dict(payload.get("roots", {})).items())
        },
    }
    return canonical


def _canonical_build_metadata_payload(payload: dict[str, Any]) -> dict[str, Any]:
    source_scope = dict(payload.get("source_scope", {}))
    return {
        "build_id": str(payload.get("build_id", "")),
        "build_timestamp": str(payload.get("build_timestamp", "")),
        "code_revision": str(payload.get("code_revision", "")),
        "config_identity": str(payload.get("config_identity", "")),
        "source_scope": {
            "mode": str(source_scope.get("mode", "")),
            "input_root": str(source_scope.get("input_root", "")),
            "input_format": str(source_scope.get("input_format", "")),
            "manifest_station_count": int(_coerce_int(source_scope.get("manifest_station_count", 0))),
            "station_ids": sorted(str(value) for value in source_scope.get("station_ids", [])),
            "input_paths": sorted(str(value) for value in source_scope.get("input_paths", [])),
        },
    }


def _config_diff(existing: dict[str, Any], incoming: dict[str, Any]) -> str:
    diffs: list[str] = []
    for key in sorted(set(existing.keys()) | set(incoming.keys())):
        if existing.get(key) != incoming.get(key):
            diffs.append(f"{key}: existing={existing.get(key)!r} incoming={incoming.get(key)!r}")
    return "; ".join(diffs)


def _build_timestamp_from_run_id(run_id: str) -> str | None:
    try:
        parsed = datetime.strptime(run_id, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    return parsed.isoformat()


def _normalize_iso_timestamp(value: Any) -> str | None:
    text = str(value).strip()
    if not text:
        return None
    normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.isoformat()


def _build_artifact_timestamp(build_metadata_path: Path, *, fallback: str) -> str:
    if build_metadata_path.exists():
        try:
            payload = json.loads(build_metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            payload = {}
        normalized = _normalize_iso_timestamp(payload.get("build_timestamp", ""))
        if normalized is not None:
            return normalized
    return fallback


def _resolve_build_timestamp(
    *,
    run_id: str,
    manifest_rows: list[dict[str, Any]],
    build_metadata_path: Path,
    manifest_refresh: bool,
) -> str:
    run_id_timestamp = _build_timestamp_from_run_id(run_id)
    if run_id_timestamp is not None:
        return run_id_timestamp

    if build_metadata_path.exists() and not manifest_refresh:
        try:
            existing = json.loads(build_metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            existing = {}
        existing_timestamp = _normalize_iso_timestamp(existing.get("build_timestamp", ""))
        if existing_timestamp is not None:
            return existing_timestamp

    for row in manifest_rows:
        discovered_at = _normalize_iso_timestamp(row.get("discovered_at", ""))
        if discovered_at is not None:
            return discovered_at

    return _pst_now_iso()


def _resolve_code_revision() -> str:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            check=True,
            text=True,
        )
    except (subprocess.SubprocessError, FileNotFoundError):
        return "unknown"
    revision = proc.stdout.strip()
    return revision or "unknown"


def _identifier_from_qc_reason_column(internal_col: str) -> str | None:
    if not internal_col.endswith("__qc_reason"):
        return None
    stem = internal_col[: -len("__qc_reason")]
    if "__part" in stem:
        return stem.split("__part", 1)[0]
    if "__" in stem:
        return stem.split("__", 1)[0]
    return stem


def _identifier_from_qc_flag_column(internal_col: str) -> str | None:
    prefixes = (
        "qc_domain_invalid_",
        "qc_pattern_mismatch_",
        "qc_arity_mismatch_",
        "qc_control_invalid_",
    )
    for prefix in prefixes:
        if internal_col.startswith(prefix):
            return internal_col[len(prefix) :]
    return None


def _family_from_qc_flag_column(internal_col: str) -> str | None:
    if internal_col.startswith("qc_domain_invalid_"):
        return "domain_validation"
    if internal_col.startswith("qc_control_invalid_"):
        return "structural_validation"
    if internal_col.startswith("qc_pattern_mismatch_"):
        return "pattern_validation"
    if internal_col.startswith("qc_arity_mismatch_"):
        return "arity_validation"
    return None


def _pst_now_iso() -> str:
    return datetime.now(PST).isoformat()


def _pst_today() -> str:
    return datetime.now(PST).date().isoformat()


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    _ensure_dir(path.parent)
    tmp_path = path.parent / f".{path.name}.tmp-{os.getpid()}-{uuid.uuid4().hex}"
    try:
        tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def _json_compact(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))
