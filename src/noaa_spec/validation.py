"""Operational validation bundle workflow built on the existing deterministic cleaner."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import shlex
import shutil
import subprocess
import time
from typing import Any

import pandas as pd

from . import __version__
from .cleaning import clean_noaa_dataframe
from .deterministic_io import write_deterministic_csv

DEFAULT_VALIDATION_COUNT = 100
DEFAULT_VALIDATION_SEED = 20260430
DOI_PLACEHOLDER = "TO_BE_ADDED_BEFORE_JOSS_SUBMISSION"
REPRODUCIBILITY_BOUNDARY_NOTE = (
    "This artifact provides operational smoke validation for a stratified "
    "100-station sample. It does not claim exhaustive validation of the full "
    "NOAA corpus. Semantic correctness is verified by tracked upstream-traceable "
    "fixtures and tests. The selected raw inputs are archived with checksums so "
    "reviewers can inspect or rerun the workflow without depending on live NOAA "
    "availability."
)
SUMMARY_OPERATIONAL_LANGUAGE = (
    "Small upstream-traceable fixtures verify semantic correctness. The "
    "100-station validation artifact demonstrates that the same "
    "repository-controlled workflow runs successfully across a broader "
    "stratified operational sample."
)
SUMMARY_ARCHIVAL_LANGUAGE = (
    "The archived raw inputs are included to make the validation evidence "
    "inspectable and rerunnable without relying on live NOAA availability."
)
SUMMARY_NON_EXHAUSTIVE_LANGUAGE = (
    "This artifact does not prove correctness over the full NOAA corpus."
)
SUMMARY_SELECTION_LANGUAGE = (
    "The sample is deterministic and size-stratified, not manually selected for "
    "favorable outcomes."
)


@dataclass(frozen=True)
class StationCandidate:
    station_id: str
    source_path: Path
    source_format: str
    file_size_bytes: int
    size_stratum: str | None
    selection_score: int


def default_build_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def run_validation_workflow(
    *,
    source_root: Path,
    output_root: Path,
    count: int = DEFAULT_VALIDATION_COUNT,
    strategy: str = "size-stratified",
    seed: int = DEFAULT_VALIDATION_SEED,
    continue_on_error: bool = False,
    build_id: str | None = None,
    command: str | None = None,
    selected_by: str = "noaa-spec build-validation-bundle",
) -> dict[str, Any]:
    if count <= 0:
        raise ValueError("count must be greater than zero")
    if strategy != "size-stratified":
        raise ValueError(f"Unsupported sampling strategy: {strategy}")

    source_root = source_root.resolve()
    if not source_root.exists():
        raise FileNotFoundError(f"Source root does not exist: {source_root}")

    resolved_build_id = build_id or default_build_id()
    output_root = output_root.resolve()
    raw_inputs_dir = output_root / "raw_inputs"
    canonical_dir = output_root / "canonical_cleaned"
    quality_dir = output_root / "quality_reports"
    for path in (output_root, raw_inputs_dir, canonical_dir, quality_dir):
        path.mkdir(parents=True, exist_ok=True)

    command_text = command or _default_command(
        source_root=source_root,
        output_root=output_root,
        count=count,
        strategy=strategy,
        seed=seed,
        continue_on_error=continue_on_error,
        build_id=resolved_build_id,
        command_name=selected_by.split()[1] if " " in selected_by else selected_by,
    )

    scan_records = _scan_station_candidates(source_root=source_root, seed=seed)
    selected_candidates, selection_rows = _select_candidates(
        scan_records=scan_records,
        source_root=source_root,
        count=count,
        strategy=strategy,
        seed=seed,
        selected_by=selected_by,
    )
    copied_entries = _copy_selected_raw_inputs(
        selected_candidates=selected_candidates,
        raw_inputs_dir=raw_inputs_dir,
        source_root=source_root,
    )
    selection_rows = _merge_copied_metadata_into_selection_rows(
        selection_rows=selection_rows,
        copied_entries=copied_entries,
    )

    git_metadata = _git_metadata()
    run_manifest = {
        "build_id": resolved_build_id,
        "repo_commit_sha": git_metadata["repo_commit_sha"],
        "git_dirty_status": git_metadata["git_dirty_status"],
        "timestamp_utc": _now_utc_isoformat(),
        "command": command_text,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "package_version": __version__,
        "dependency_lock_hash": _dependency_lock_hash(),
        "source_root": str(source_root),
        "output_root": str(output_root),
        "station_count_requested": count,
        "station_count_selected": len(selected_candidates),
        "sampling_strategy": strategy,
        "seed": seed,
        "reproducibility_boundary_note": REPRODUCIBILITY_BOUNDARY_NOTE,
    }

    results_rows: list[dict[str, Any]] = []
    total_runtime = 0.0
    total_input_rows = 0
    total_output_rows = 0
    failure_seen = False
    failed_station_id: str | None = None

    remaining_candidates: list[StationCandidate] = []
    for index, candidate in enumerate(selected_candidates):
        copied_entry = copied_entries[(candidate.station_id, str(candidate.source_path))]
        result = _process_station_candidate(
            candidate=candidate,
            copied_entry=copied_entry,
            canonical_dir=canonical_dir,
            quality_dir=quality_dir,
            output_root=output_root,
        )
        results_rows.append(result)
        total_runtime += float(result["runtime_seconds"] or 0.0)
        total_input_rows += int(result["input_rows"] or 0)
        total_output_rows += int(result["output_rows"] or 0)
        _update_selection_row_with_result(selection_rows, result)

        if result["status"] != "success":
            failure_seen = True
            failed_station_id = candidate.station_id
            remaining_candidates = selected_candidates[index + 1 :]
            break

    if failure_seen and continue_on_error:
        for candidate in remaining_candidates:
            copied_entry = copied_entries[(candidate.station_id, str(candidate.source_path))]
            result = _process_station_candidate(
                candidate=candidate,
                copied_entry=copied_entry,
                canonical_dir=canonical_dir,
                quality_dir=quality_dir,
                output_root=output_root,
            )
            results_rows.append(result)
            total_runtime += float(result["runtime_seconds"] or 0.0)
            total_input_rows += int(result["input_rows"] or 0)
            total_output_rows += int(result["output_rows"] or 0)
            _update_selection_row_with_result(selection_rows, result)
    elif failure_seen:
        for candidate in remaining_candidates:
            copied_entry = copied_entries[(candidate.station_id, str(candidate.source_path))]
            result = _not_run_result(
                candidate=candidate,
                copied_entry=copied_entry,
                output_root=output_root,
                prior_station_id=failed_station_id or "",
            )
            results_rows.append(result)
            _update_selection_row_with_result(selection_rows, result)

    selection_manifest_path = output_root / "station_selection_manifest.csv"
    selection_frame = pd.DataFrame(selection_rows, columns=_station_selection_columns())
    write_deterministic_csv(
        selection_frame,
        selection_manifest_path,
        sort_by=("selection_status", "selection_rank", "station_id", "source_path"),
    )

    station_results_path = output_root / "station_results.csv"
    station_results_frame = pd.DataFrame(results_rows, columns=_station_results_columns())
    write_deterministic_csv(
        station_results_frame,
        station_results_path,
        sort_by=("status", "station_id"),
        float_format="%.6f",
    )

    run_manifest_path = output_root / "run_manifest.json"
    _write_json(run_manifest_path, run_manifest)

    summary_path = output_root / "summary.md"
    _write_summary(
        summary_path=summary_path,
        run_manifest=run_manifest,
        selection_rows=selection_rows,
        results_rows=results_rows,
        total_input_rows=total_input_rows,
        total_output_rows=total_output_rows,
        total_runtime=total_runtime,
    )

    archive_manifest_path = output_root / "archive_manifest.json"
    _write_json(
        archive_manifest_path,
        _build_archive_manifest_payload(output_root=output_root, run_manifest=run_manifest),
    )

    checksums_path = output_root / "checksums.txt"
    _write_checksums(checksums_path=checksums_path, output_root=output_root)
    _write_json(
        archive_manifest_path,
        _build_archive_manifest_payload(output_root=output_root, run_manifest=run_manifest),
    )
    _write_checksums(checksums_path=checksums_path, output_root=output_root)

    return {
        "build_id": resolved_build_id,
        "output_root": output_root,
        "station_selection_manifest": selection_manifest_path,
        "run_manifest": run_manifest_path,
        "station_results": station_results_path,
        "summary": summary_path,
        "checksums": checksums_path,
        "archive_manifest": archive_manifest_path,
        "selected_station_count": len(selected_candidates),
        "failure_count": sum(1 for row in results_rows if row["status"] != "success"),
        "failed": failure_seen,
    }


def _default_command(
    *,
    source_root: Path,
    output_root: Path,
    count: int,
    strategy: str,
    seed: int,
    continue_on_error: bool,
    build_id: str,
    command_name: str,
) -> str:
    parts = [
        "noaa-spec",
        command_name,
        "--source-root",
        str(source_root),
        "--output-root",
        str(output_root),
        "--count",
        str(count),
        "--strategy",
        strategy,
        "--seed",
        str(seed),
        "--build-id",
        build_id,
    ]
    if continue_on_error:
        parts.append("--continue-on-error")
    return shlex.join(parts)


def _scan_station_candidates(source_root: Path, seed: int) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    duplicate_winners: dict[str, str] = {}
    supported_candidates: list[StationCandidate] = []

    for path in sorted(item for item in source_root.rglob("*") if item.is_file()):
        source_format = _detect_source_format(path)
        station_id = _station_id_from_path(path)
        file_size_bytes = path.stat().st_size
        record: dict[str, Any] = {
            "station_id": station_id,
            "source_path": str(path.resolve()),
            "source_format": source_format or "unsupported",
            "file_size_bytes": file_size_bytes,
            "size_stratum": "",
            "selection_score": "",
            "selection_status": "scanned",
            "skip_reason": "",
            "source_url": _infer_source_url(station_id=station_id, source_path=path),
        }
        if source_format is None:
            record["selection_status"] = "skipped_invalid"
            record["skip_reason"] = "unsupported_source_format"
            records.append(record)
            continue

        score = _selection_score(seed=seed, station_id=station_id, source_path=path)
        record["selection_score"] = score
        records.append(record)
        supported_candidates.append(
            StationCandidate(
                station_id=station_id,
                source_path=path.resolve(),
                source_format=source_format,
                file_size_bytes=file_size_bytes,
                size_stratum=None,
                selection_score=score,
            )
        )

    supported_candidates = sorted(
        supported_candidates,
        key=lambda candidate: (
            candidate.station_id,
            candidate.source_path.as_posix(),
            candidate.selection_score,
        ),
    )

    deduped_candidates: list[StationCandidate] = []
    for candidate in supported_candidates:
        existing_path = duplicate_winners.get(candidate.station_id)
        if existing_path is None:
            duplicate_winners[candidate.station_id] = str(candidate.source_path)
            deduped_candidates.append(candidate)
            continue
        for record in records:
            if (
                record["station_id"] == candidate.station_id
                and record["source_path"] == str(candidate.source_path)
            ):
                record["selection_status"] = "skipped_invalid"
                record["skip_reason"] = "duplicate_station_id"
                break

    if deduped_candidates:
        strata = _assign_size_strata(deduped_candidates)
        by_key = {
            (candidate.station_id, str(candidate.source_path)): candidate.size_stratum
            for candidate in strata
        }
        for record in records:
            key = (record["station_id"], record["source_path"])
            if key in by_key and record["selection_status"] == "scanned":
                record["size_stratum"] = by_key[key] or ""

    return records


def _select_candidates(
    *,
    scan_records: list[dict[str, Any]],
    source_root: Path,
    count: int,
    strategy: str,
    seed: int,
    selected_by: str,
) -> tuple[list[StationCandidate], list[dict[str, Any]]]:
    viable_records = [
        record
        for record in scan_records
        if record["selection_status"] == "scanned" and record["size_stratum"]
    ]
    if len(viable_records) < count:
        raise ValueError(
            f"Found only {len(viable_records)} viable station files under {source_root}; "
            f"{count} are required."
        )

    viable_candidates = [
        StationCandidate(
            station_id=str(record["station_id"]),
            source_path=Path(str(record["source_path"])),
            source_format=str(record["source_format"]),
            file_size_bytes=int(record["file_size_bytes"]),
            size_stratum=str(record["size_stratum"]),
            selection_score=int(record["selection_score"]),
        )
        for record in viable_records
    ]
    selected_candidates = _select_size_stratified_candidates(
        viable_candidates=viable_candidates,
        count=count,
    )
    selected_keys = {
        (candidate.station_id, str(candidate.source_path)): rank
        for rank, candidate in enumerate(selected_candidates, start=1)
    }

    selection_rows: list[dict[str, Any]] = []
    for record in scan_records:
        station_id = str(record["station_id"])
        source_path = str(record["source_path"])
        key = (station_id, source_path)
        is_selected = key in selected_keys
        selection_status = (
            "selected"
            if is_selected
            else str(record["selection_status"]).replace("scanned", "skipped_unselected")
        )
        selection_reason = ""
        if is_selected and record["size_stratum"]:
            selection_reason = f"size_stratified_quartile_{record['size_stratum']}"
        elif selection_status == "skipped_unselected":
            selection_reason = "not_selected_after_size_stratified_sampling"
        elif selection_status == "skipped_invalid":
            selection_reason = str(record["skip_reason"] or "invalid_candidate")

        selection_rows.append(
            {
                "station_id": station_id,
                "source_path": source_path,
                "archived_raw_input_path": "",
                "source_format": str(record["source_format"]),
                "file_size_bytes": int(record["file_size_bytes"]),
                "row_count": "",
                "size_stratum": str(record["size_stratum"] or ""),
                "selection_rank": selected_keys.get(key, ""),
                "selection_reason": selection_reason,
                "selected_by": selected_by,
                "seed": seed,
                "raw_sha256": "",
                "input_root": str(source_root),
                "source_root": str(source_root),
                "copied_utc": "",
                "source_url": str(record["source_url"] or ""),
                "original_source_filename": Path(source_path).name,
                "selection_status": selection_status,
                "skip_reason": "" if is_selected else str(record["skip_reason"]),
                "processing_status": "pending" if is_selected else "",
            }
        )

    return selected_candidates, selection_rows


def _assign_size_strata(candidates: list[StationCandidate]) -> list[StationCandidate]:
    ordered = sorted(
        candidates,
        key=lambda candidate: (
            candidate.file_size_bytes,
            candidate.station_id,
            candidate.source_path.as_posix(),
        ),
    )
    labels = _quartile_labels(len(ordered))
    assigned: list[StationCandidate] = []
    for candidate, quartile in zip(ordered, labels, strict=True):
        assigned.append(
            StationCandidate(
                station_id=candidate.station_id,
                source_path=candidate.source_path,
                source_format=candidate.source_format,
                file_size_bytes=candidate.file_size_bytes,
                size_stratum=f"q{quartile}",
                selection_score=candidate.selection_score,
            )
        )
    return assigned


def _quartile_labels(size: int) -> list[int]:
    return [((index * 4) // size) + 1 for index in range(size)]


def _select_size_stratified_candidates(
    *,
    viable_candidates: list[StationCandidate],
    count: int,
) -> list[StationCandidate]:
    by_stratum: dict[str, list[StationCandidate]] = {label: [] for label in ("q1", "q2", "q3", "q4")}
    for candidate in viable_candidates:
        if candidate.size_stratum is not None:
            by_stratum[candidate.size_stratum].append(candidate)

    for label in by_stratum:
        by_stratum[label] = sorted(
            by_stratum[label],
            key=lambda candidate: (
                candidate.selection_score,
                candidate.file_size_bytes,
                candidate.station_id,
                candidate.source_path.as_posix(),
            ),
        )

    base = count // 4
    remainder = count % 4
    targets = {
        label: base + (1 if index < remainder else 0)
        for index, label in enumerate(("q1", "q2", "q3", "q4"))
    }

    selected: list[StationCandidate] = []
    leftovers: list[StationCandidate] = []
    for label in ("q1", "q2", "q3", "q4"):
        candidates = by_stratum[label]
        take = min(len(candidates), targets[label])
        selected.extend(candidates[:take])
        leftovers.extend(candidates[take:])

    if len(selected) < count:
        leftovers = sorted(
            leftovers,
            key=lambda candidate: (
                candidate.selection_score,
                candidate.size_stratum,
                candidate.file_size_bytes,
                candidate.station_id,
                candidate.source_path.as_posix(),
            ),
        )
        selected.extend(leftovers[: count - len(selected)])

    return sorted(
        selected,
        key=lambda candidate: (
            candidate.size_stratum,
            candidate.selection_score,
            candidate.station_id,
            candidate.source_path.as_posix(),
        ),
    )


def _copy_selected_raw_inputs(
    *,
    selected_candidates: list[StationCandidate],
    raw_inputs_dir: Path,
    source_root: Path,
) -> dict[tuple[str, str], dict[str, Any]]:
    copied_entries: dict[tuple[str, str], dict[str, Any]] = {}
    for candidate in selected_candidates:
        copied_utc = _now_utc_isoformat()
        archived_name = f"{candidate.station_id}{''.join(candidate.source_path.suffixes)}"
        archived_path = raw_inputs_dir / archived_name
        shutil.copy2(candidate.source_path, archived_path)
        raw_sha256 = _sha256_file(archived_path)
        copied_entries[(candidate.station_id, str(candidate.source_path))] = {
            "station_id": candidate.station_id,
            "source_path": str(candidate.source_path),
            "source_format": candidate.source_format,
            "source_file_name": candidate.source_path.name,
            "archived_raw_input_path": archived_path.relative_to(raw_inputs_dir.parent).as_posix(),
            "archived_raw_path_abs": archived_path,
            "raw_sha256": raw_sha256,
            "copied_utc": copied_utc,
            "source_root": str(source_root),
            "file_size_bytes": archived_path.stat().st_size,
            "selection_strategy": "size-stratified",
            "source_url": _infer_source_url(
                station_id=candidate.station_id,
                source_path=candidate.source_path,
            )
            or "",
        }
    return copied_entries


def _merge_copied_metadata_into_selection_rows(
    *,
    selection_rows: list[dict[str, Any]],
    copied_entries: dict[tuple[str, str], dict[str, Any]],
) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    for row in selection_rows:
        updated = dict(row)
        key = (str(row["station_id"]), str(row["source_path"]))
        copied = copied_entries.get(key)
        if copied is not None:
            updated["archived_raw_input_path"] = copied["archived_raw_input_path"]
            updated["raw_sha256"] = copied["raw_sha256"]
            updated["copied_utc"] = copied["copied_utc"]
            if copied["source_url"]:
                updated["source_url"] = copied["source_url"]
        merged.append(updated)
    return merged


def _process_station_candidate(
    *,
    candidate: StationCandidate,
    copied_entry: dict[str, Any],
    canonical_dir: Path,
    quality_dir: Path,
    output_root: Path,
) -> dict[str, Any]:
    start = time.perf_counter()
    archived_raw_path = Path(copied_entry["archived_raw_path_abs"])
    canonical_path = canonical_dir / f"{candidate.station_id}_cleaned.csv"
    quality_report_path = quality_dir / f"{candidate.station_id}_quality_report.json"

    try:
        raw = _read_station_data(archived_raw_path, candidate.source_format)
        input_rows = int(len(raw))
        cleaned = clean_noaa_dataframe(raw, keep_raw=False, strict_mode=True)
        output_rows = int(len(cleaned))
        write_deterministic_csv(
            cleaned,
            canonical_path,
            sort_by=("STATION", "DATE"),
            float_format="%.1f",
        )
        strict_summary = cleaned.attrs.get("strict_parse_summary", {})
        parse_error_rows = (
            int(cleaned["__parse_error"].notna().sum())
            if "__parse_error" in cleaned.columns
            else 0
        )
        warnings_count = parse_error_rows + int(
            strict_summary.get("skipped_encoded_column_count", 0)
        )
        _write_json(
            quality_report_path,
            {
                "station_id": candidate.station_id,
                "original_source_path": copied_entry["source_path"],
                "archived_raw_input_path": copied_entry["archived_raw_input_path"],
                "raw_sha256": copied_entry["raw_sha256"],
                "input_rows": input_rows,
                "output_rows": output_rows,
                "parse_error_rows": parse_error_rows,
                "strict_parse_summary": strict_summary,
                "rows_with_any_usable_metric": (
                    int(cleaned["row_has_any_usable_metric"].sum())
                    if "row_has_any_usable_metric" in cleaned.columns
                    else None
                ),
                "warnings_count": warnings_count,
            },
        )
        return {
            "station_id": candidate.station_id,
            "status": "success",
            "input_rows": input_rows,
            "output_rows": output_rows,
            "runtime_seconds": time.perf_counter() - start,
            "archived_raw_input_path": copied_entry["archived_raw_input_path"],
            "raw_sha256": copied_entry["raw_sha256"],
            "canonical_output_path": _relative_to_root(canonical_path, output_root),
            "canonical_output_sha256": _sha256_file(canonical_path),
            "quality_report_path": _relative_to_root(quality_report_path, output_root),
            "domain_outputs_generated": False,
            "warnings_count": warnings_count,
            "error_type": "",
            "error_message": "",
        }
    except Exception as exc:
        return {
            "station_id": candidate.station_id,
            "status": "failed",
            "input_rows": 0,
            "output_rows": 0,
            "runtime_seconds": time.perf_counter() - start,
            "archived_raw_input_path": copied_entry["archived_raw_input_path"],
            "raw_sha256": copied_entry["raw_sha256"],
            "canonical_output_path": "",
            "canonical_output_sha256": "",
            "quality_report_path": "",
            "domain_outputs_generated": False,
            "warnings_count": 0,
            "error_type": exc.__class__.__name__,
            "error_message": str(exc),
        }


def _not_run_result(
    *,
    candidate: StationCandidate,
    copied_entry: dict[str, Any],
    output_root: Path,
    prior_station_id: str,
) -> dict[str, Any]:
    return {
        "station_id": candidate.station_id,
        "status": "not_run",
        "input_rows": 0,
        "output_rows": 0,
        "runtime_seconds": 0.0,
        "archived_raw_input_path": copied_entry["archived_raw_input_path"],
        "raw_sha256": copied_entry["raw_sha256"],
        "canonical_output_path": "",
        "canonical_output_sha256": "",
        "quality_report_path": "",
        "domain_outputs_generated": False,
        "warnings_count": 0,
        "error_type": "prior_station_failure",
        "error_message": (
            "Workflow stopped after an earlier selected station failed and "
            f"--continue-on-error was not set (first failure station_id={prior_station_id})."
        ),
    }


def _update_selection_row_with_result(
    selection_rows: list[dict[str, Any]],
    result: dict[str, Any],
) -> None:
    station_id = str(result["station_id"])
    archived_raw_input_path = str(result["archived_raw_input_path"])
    for row in selection_rows:
        if (
            row["station_id"] == station_id
            and row["archived_raw_input_path"] == archived_raw_input_path
        ):
            if int(result["input_rows"] or 0) > 0:
                row["row_count"] = int(result["input_rows"])
            row["processing_status"] = str(result["status"])
            return


def _read_station_data(source_path: Path, source_format: str) -> pd.DataFrame:
    if source_format == "csv":
        return pd.read_csv(source_path, dtype=str)
    if source_format == "csv.gz":
        return pd.read_csv(source_path, dtype=str, compression="infer")
    if source_format == "parquet":
        return pd.read_parquet(source_path).astype("string")
    raise ValueError(f"Unsupported source format: {source_format}")


def _write_summary(
    *,
    summary_path: Path,
    run_manifest: dict[str, Any],
    selection_rows: list[dict[str, Any]],
    results_rows: list[dict[str, Any]],
    total_input_rows: int,
    total_output_rows: int,
    total_runtime: float,
) -> None:
    selected_rows = [row for row in selection_rows if row["selection_status"] == "selected"]
    succeeded = [row for row in results_rows if row["status"] == "success"]
    failed = [row for row in results_rows if row["status"] == "failed"]
    not_run = [row for row in results_rows if row["status"] == "not_run"]
    selected_sizes = [int(row["file_size_bytes"]) for row in selected_rows]
    size_summary = _selected_size_summary(selected_sizes)
    counts_by_stratum = {
        label: sum(1 for row in selected_rows if row["size_stratum"] == label)
        for label in ("q1", "q2", "q3", "q4")
    }

    lines = [
        "# 100-Station Validation Summary",
        "",
        "## Purpose",
        SUMMARY_OPERATIONAL_LANGUAGE,
        SUMMARY_ARCHIVAL_LANGUAGE,
        "",
        "## What this artifact demonstrates",
        "- The repository-controlled cleaning workflow completed across a deterministic stratified station sample.",
        "- The bundle freezes selected raw inputs, cleaned outputs, per-station results, manifests, and checksums for reviewer inspection.",
        "",
        "## What this artifact does not demonstrate",
        f"- {SUMMARY_NON_EXHAUSTIVE_LANGUAGE}",
        "- It does not claim exhaustive validation of the full NOAA corpus or universal correctness for all NOAA station files.",
        "",
        "## Sampling method",
        f"- Strategy: {run_manifest['sampling_strategy']}",
        f"- Seed: {run_manifest['seed']}",
        f"- Stations requested: {run_manifest['station_count_requested']}",
        f"- Stations selected: {run_manifest['station_count_selected']}",
        f"- Min file size (bytes): {size_summary['min']}",
        f"- Median file size (bytes): {size_summary['median']}",
        f"- Max file size (bytes): {size_summary['max']}",
        f"- Counts by size stratum: q1={counts_by_stratum['q1']}, q2={counts_by_stratum['q2']}, q3={counts_by_stratum['q3']}, q4={counts_by_stratum['q4']}",
        f"- {SUMMARY_SELECTION_LANGUAGE}",
        "",
        "## Provenance and raw inputs",
        "- Selected raw station files are copied into `raw_inputs/` and checksum-recorded before cleaning.",
        "- Reviewers can inspect the archived bundle without needing the original local station corpus or live NOAA access.",
        "- Local rerun requires either the archived raw input bundle or a local NOAA station corpus.",
        "",
        "## Run environment",
        f"- Build ID: {run_manifest['build_id']}",
        f"- Timestamp (UTC): {run_manifest['timestamp_utc']}",
        f"- Python: {run_manifest['python_version']}",
        f"- Platform: {run_manifest['platform']}",
        f"- Package version: {run_manifest['package_version']}",
        f"- Repo commit SHA: {run_manifest['repo_commit_sha'] or 'unavailable'}",
        f"- Git dirty status: {run_manifest['git_dirty_status'] or 'unavailable'}",
        "",
        "## Results summary",
        f"- Stations succeeded: {len(succeeded)}",
        f"- Stations failed: {len(failed)}",
        f"- Stations not run after first failure: {len(not_run)}",
        f"- Total input rows: {total_input_rows}",
        f"- Total output rows: {total_output_rows}",
        f"- Total runtime (seconds): {total_runtime:.6f}",
        f"- Checksum file: {summary_path.parent / 'checksums.txt'}",
        "",
        "## Failure summary",
    ]

    if failed or not_run:
        for row in failed + not_run:
            lines.append(f"- {row['station_id']}: {row['error_type']} - {row['error_message']}")
    else:
        lines.append("- No station failures were recorded.")

    lines.extend(
        [
            "",
            "## Output artifact inventory",
            "- `raw_inputs/`",
            "- `canonical_cleaned/`",
            "- `quality_reports/`",
            "- `station_selection_manifest.csv`",
            "- `run_manifest.json`",
            "- `station_results.csv`",
            "- `checksums.txt`",
            "- `summary.md`",
            "- `archive_manifest.json`",
            "",
            "## Reproducibility boundary",
            run_manifest["reproducibility_boundary_note"],
            "",
            "## DOI archival status",
            f"- DOI: {DOI_PLACEHOLDER}",
            "- This bundle is intended for external archival so reviewers can inspect it without rerunning the workflow.",
            "",
        ]
    )
    summary_path.write_text("\n".join(lines), encoding="utf-8")


def _build_archive_manifest_payload(
    *,
    output_root: Path,
    run_manifest: dict[str, Any],
) -> dict[str, Any]:
    files = sorted(path for path in output_root.rglob("*") if path.is_file())
    top_level_files = sorted(path.name for path in output_root.iterdir() if path.is_file())
    directory_inventory = []
    for directory in sorted(path for path in output_root.iterdir() if path.is_dir()):
        dir_files = sorted(path for path in directory.rglob("*") if path.is_file())
        directory_inventory.append(
            {
                "path": directory.name,
                "file_count": len(dir_files),
                "total_bytes": sum(path.stat().st_size for path in dir_files),
            }
        )
    return {
        "artifact_name": "validation_100_station_bundle",
        "artifact_version": str(run_manifest["build_id"]),
        "build_id": str(run_manifest["build_id"]),
        "repo_commit_sha": run_manifest["repo_commit_sha"],
        "created_utc": _now_utc_isoformat(),
        "intended_archive": "external DOI archive",
        "total_files": len(files),
        "total_bytes": sum(path.stat().st_size for path in files),
        "checksum_algorithm": "SHA256",
        "top_level_files": top_level_files,
        "directory_inventory": directory_inventory,
        "DOI": DOI_PLACEHOLDER,
    }


def _write_checksums(*, checksums_path: Path, output_root: Path) -> None:
    paths = sorted(
        path
        for path in output_root.rglob("*")
        if path.is_file() and path.resolve() != checksums_path.resolve()
    )
    lines = [f"{_sha256_file(path)}  {path.relative_to(output_root).as_posix()}" for path in paths]
    checksums_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _selected_size_summary(selected_sizes: list[int]) -> dict[str, int]:
    if not selected_sizes:
        return {"min": 0, "median": 0, "max": 0}
    ordered = sorted(selected_sizes)
    median = int(pd.Series(ordered, dtype="int64").median())
    return {"min": ordered[0], "median": median, "max": ordered[-1]}


def _station_selection_columns() -> list[str]:
    return [
        "station_id",
        "source_path",
        "archived_raw_input_path",
        "source_format",
        "file_size_bytes",
        "row_count",
        "size_stratum",
        "selection_rank",
        "selection_reason",
        "selected_by",
        "seed",
        "raw_sha256",
        "input_root",
        "source_root",
        "copied_utc",
        "source_url",
        "original_source_filename",
        "selection_status",
        "skip_reason",
        "processing_status",
    ]


def _station_results_columns() -> list[str]:
    return [
        "station_id",
        "status",
        "input_rows",
        "output_rows",
        "runtime_seconds",
        "archived_raw_input_path",
        "raw_sha256",
        "canonical_output_path",
        "canonical_output_sha256",
        "quality_report_path",
        "domain_outputs_generated",
        "warnings_count",
        "error_type",
        "error_message",
    ]


def _detect_source_format(path: Path) -> str | None:
    name = path.name.lower()
    if name.endswith(".csv.gz"):
        return "csv.gz"
    if path.suffix.lower() == ".csv":
        return "csv"
    if path.suffix.lower() == ".parquet":
        return "parquet"
    return None


def _station_id_from_path(path: Path) -> str:
    name = path.name
    if name.lower().endswith(".csv.gz"):
        stem = name[:-7]
    else:
        stem = path.stem
    digits = "".join(character for character in stem if character.isdigit())
    if len(digits) >= 11:
        return digits[:11]
    parent_digits = "".join(character for character in path.parent.name if character.isdigit())
    if len(parent_digits) >= 11:
        return parent_digits[:11]
    return stem


def _infer_source_url(*, station_id: str, source_path: Path) -> str | None:
    if len(station_id) != 11 or not station_id.isdigit():
        return None
    year = next(
        (
            part
            for part in source_path.parts
            if len(part) == 4 and part.isdigit() and 1900 <= int(part) <= 2100
        ),
        None,
    )
    if year is None:
        return None
    return f"https://www.ncei.noaa.gov/data/global-hourly/access/{year}/{station_id}.csv"


def _selection_score(*, seed: int, station_id: str, source_path: Path) -> int:
    text = f"{seed}|{station_id}|{source_path.as_posix()}"
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _relative_to_root(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _now_utc_isoformat() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _git_metadata() -> dict[str, str | None]:
    repo_root = Path(__file__).resolve().parents[2]
    commit = _run_git_command(["git", "rev-parse", "HEAD"], repo_root)
    dirty_output = _run_git_command(["git", "status", "--porcelain"], repo_root)
    dirty_status = None if dirty_output is None else ("dirty" if dirty_output else "clean")
    return {"repo_commit_sha": commit, "git_dirty_status": dirty_status}


def _run_git_command(command: list[str], cwd: Path) -> str | None:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return completed.stdout.strip()


def _dependency_lock_hash() -> str | None:
    repo_root = Path(__file__).resolve().parents[2]
    poetry_lock = repo_root / "poetry.lock"
    if not poetry_lock.exists():
        return None
    return _sha256_file(poetry_lock)
