"""Production-safe orchestration for cleaning station batches.

This module intentionally focuses on orchestration, path hygiene, resumability,
and low-I/O execution. Cleaning semantics remain in ``clean_noaa_dataframe``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any

import pandas as pd

from . import __version__
from .cleaning import clean_noaa_dataframe
from .contract_validation import validate_no_sentinel_leakage
from .contracts import REQUIRED_ARTIFACT_METADATA_FIELDS, SUCCESS_MARKER_SCHEMA_VERSION
from .constants import to_internal_column
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
    "row_count_raw",
    "row_count_cleaned",
    "station_quality_profile_path",
    "success_marker_path",
    "expected_outputs",
    "error_message",
]

RULE_FAMILIES = [
    "sentinel_handling",
    "arity_validation",
    "domain_validation",
    "range_validation",
    "pattern_validation",
    "width_validation",
    "structural_parser_guard",
    "quality_code_handling",
]

QC_REASON_TO_FAMILY = {
    "SENTINEL_MISSING": "sentinel_handling",
    "BAD_QUALITY_CODE": "quality_code_handling",
    "OUT_OF_RANGE": "range_validation",
    "MALFORMED_TOKEN": "width_validation",
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
        row_impacted_mask = pd.Series(False, index=cleaned.index)

        qc_flag_counts_by_identifier: dict[str, int] = {}
        null_counts_by_identifier: dict[str, int] = {}
        rule_family_impact_counts = {family: 0 for family in RULE_FAMILIES}

        for column, identifier in schema.qc_reason_columns:
            non_null = cleaned[column].notna()
            row_impacted_mask = row_impacted_mask | non_null
            count = int(non_null.sum())
            if identifier is not None and count > 0:
                qc_flag_counts_by_identifier[identifier] = (
                    qc_flag_counts_by_identifier.get(identifier, 0) + count
                )
            value_counts = cleaned[column].dropna().astype(str).value_counts()
            for reason, reason_count in value_counts.items():
                family = QC_REASON_TO_FAMILY.get(reason)
                if family is not None:
                    rule_family_impact_counts[family] += int(reason_count)

        for column, identifier, family in schema.qc_flag_columns:
            true_mask = cleaned[column].fillna(False).astype(bool)
            row_impacted_mask = row_impacted_mask | true_mask
            count = int(true_mask.sum())
            if identifier is not None and count > 0:
                qc_flag_counts_by_identifier[identifier] = (
                    qc_flag_counts_by_identifier.get(identifier, 0) + count
                )
            if family is not None:
                rule_family_impact_counts[family] += count

        if schema.parse_error_column is not None:
            parse_error_mask = cleaned[schema.parse_error_column].notna()
            row_impacted_mask = row_impacted_mask | parse_error_mask
            rule_family_impact_counts["structural_parser_guard"] += int(parse_error_mask.sum())

        for column, identifier in schema.null_value_columns:
            null_count = int(cleaned[column].isna().sum())
            if null_count > 0:
                null_counts_by_identifier[identifier] = (
                    null_counts_by_identifier.get(identifier, 0) + null_count
                )

        rows_with_qc_flags = int(row_impacted_mask.sum())
        fraction_rows_impacted = (
            float(rows_with_qc_flags) / float(rows_total) if rows_total > 0 else 0.0
        )

        return {
            "station_id": station_id,
            "rows_total": rows_total,
            "rows_with_qc_flags": rows_with_qc_flags,
            "fraction_rows_impacted": fraction_rows_impacted,
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

        status_df = _upsert_status(
            status_df,
            {
                "run_id": config.run_id,
                "station_id": station_id,
                "input_path": str(input_path),
                "status": "running",
                "started_at": started_at,
                "expected_outputs": _json_compact([str(path) for path in expected_outputs]),
                "success_marker_path": str(paths.success_marker_path),
                "error_message": "",
            },
        )
        _write_status(run_status_path, status_df)

        try:
            print(f"[{idx}/{len(manifest_rows)}] {station_id}: begin")
            print(f"[{idx}/{len(manifest_rows)}] {station_id}: read raw input")
            raw_df = _read_raw_input(input_path, config.input_format)
            row_count_raw = int(len(raw_df))

            print(f"[{idx}/{len(manifest_rows)}] {station_id}: clean canonical dataset")
            cleaned_df = _clean_canonical_dataset(raw_df)
            validate_no_sentinel_leakage(cleaned_df)
            row_count_cleaned = int(len(cleaned_df))

            profile_payload: dict[str, Any] | None = None
            if config.write_flags.write_station_quality_profile:
                profile_payload = quality_builder.build(cleaned_df, station_id)

            if config.write_flags.write_cleaned_station:
                print(f"[{idx}/{len(manifest_rows)}] {station_id}: write cleaned output")
                _ensure_dir(paths.station_output_dir)
                _write_cleaned_station(cleaned_df, paths.cleaned_path, config.input_format)

            if config.write_flags.write_domain_splits:
                print(f"[{idx}/{len(manifest_rows)}] {station_id}: write domain splits")
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
                pd.DataFrame(domain_rows).to_csv(paths.domain_manifest_path, index=False)

            if config.write_flags.write_station_quality_profile and profile_payload is not None:
                print(f"[{idx}/{len(manifest_rows)}] {station_id}: write station quality profile")
                _ensure_dir(config.quality_profile_root)
                _write_json(paths.quality_profile_path, profile_payload)

            if config.write_flags.write_station_reports:
                print(f"[{idx}/{len(manifest_rows)}] {station_id}: write station reports")
                _ensure_dir(paths.reports_dir)
                report_paths = _write_station_reports_from_memory(
                    raw=raw_df,
                    cleaned=cleaned_df,
                    station_id=station_id,
                    reports_dir=paths.reports_dir,
                )

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

            elapsed_seconds = (
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
                    "elapsed_seconds": round(float(elapsed_seconds), 6),
                    "row_count_raw": row_count_raw,
                    "row_count_cleaned": row_count_cleaned,
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
                f"(elapsed={elapsed_seconds:.3f}s)"
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
                "row_count_raw": "",
                "row_count_cleaned": "",
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
    return rows


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

    return cleaned


def _write_cleaned_station(cleaned: pd.DataFrame, output_path: Path, input_format: str) -> None:
    _ensure_dir(output_path.parent)
    if input_format == "csv":
        cleaned.to_csv(output_path, index=False)
        return
    if input_format == "parquet":
        _normalize_object_columns_for_parquet(cleaned).to_parquet(output_path, index=False)
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

    total_stations = len(profiles)
    total_rows = int(sum(int(profile.get("rows_total", 0)) for profile in profiles))

    if total_stations > 0:
        average_row_impact_rate = float(
            sum(float(profile.get("fraction_rows_impacted", 0.0)) for profile in profiles)
        ) / float(total_stations)
    else:
        average_row_impact_rate = 0.0

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
        "top_identifiers_by_qc_rate": top_identifiers[:10],
        "rule_family_impact_totals": rule_family_totals,
    }


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
        "row_count_raw": "",
        "row_count_cleaned": "",
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


def _write_manifest(path: Path, rows: list[dict[str, Any]]) -> None:
    _ensure_dir(path.parent)
    frame = pd.DataFrame(rows)
    for column in RUN_MANIFEST_COLUMNS:
        if column not in frame.columns:
            frame[column] = pd.NA
    if frame.empty:
        frame = pd.DataFrame(columns=RUN_MANIFEST_COLUMNS)
    else:
        frame = frame[RUN_MANIFEST_COLUMNS].sort_values("station_id", kind="stable")
    frame.to_csv(path, index=False)


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
    _ensure_dir(path.parent)
    frame = status_df.copy()
    for column in RUN_STATUS_COLUMNS:
        if column not in frame.columns:
            frame[column] = ""
    if frame.empty:
        frame = pd.DataFrame(columns=RUN_STATUS_COLUMNS)
    else:
        frame = frame[RUN_STATUS_COLUMNS].sort_values("station_id", kind="stable")
    frame.to_csv(path, index=False)


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


def _config_diff(existing: dict[str, Any], incoming: dict[str, Any]) -> str:
    diffs: list[str] = []
    for key in sorted(set(existing.keys()) | set(incoming.keys())):
        if existing.get(key) != incoming.get(key):
            diffs.append(f"{key}: existing={existing.get(key)!r} incoming={incoming.get(key)!r}")
    return "; ".join(diffs)


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
        return "domain_validation"
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
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _json_compact(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))
