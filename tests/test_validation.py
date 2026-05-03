from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import pandas as pd
import pytest

import noaa_spec.cli as cli
from noaa_spec.validation import _scan_station_candidates, _select_candidates, _station_id_from_path


def _write_station_csv(
    directory: Path,
    station_id: str,
    row_count: int,
    extra_fields: dict[str, str] | None = None,
) -> Path:
    path = directory / f"{station_id}.csv"
    extra_fields = extra_fields or {}
    header = ["STATION", "DATE", "TMP", "VIS", "WND", "SLP", *extra_fields.keys()]
    rows = [",".join(header)]
    for index in range(row_count):
        base_values = [
            station_id,
            f"2000-01-{(index % 28) + 1:02d}T00:00:00",
            '"+0010,1"',
            '"010000,1,N,1"',
            '"090,1,N,0010,1"',
            '"10123,1"',
        ]
        rows.append(
            ",".join(
                base_values
                + [f'"{value}"' for value in extra_fields.values()]
            )
        )
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return path


def _make_station_pool(directory: Path, station_count: int = 8) -> None:
    for index in range(station_count):
        station_id = f"{10000000000 + index}"
        _write_station_csv(directory, station_id, row_count=index + 1)


def test_station_id_uses_parent_directory_for_generic_raw_filename(tmp_path: Path) -> None:
    station_dir = tmp_path / "72344154921"
    station_dir.mkdir()
    raw_path = station_dir / "LocationData_Raw.parquet"
    raw_path.write_text("placeholder", encoding="utf-8")

    assert _station_id_from_path(raw_path) == "72344154921"


def test_station_selection_is_deterministic(tmp_path: Path) -> None:
    input_root = tmp_path / "input"
    input_root.mkdir()
    _make_station_pool(input_root, station_count=12)

    scan_records = _scan_station_candidates(source_root=input_root, seed=20260430)
    first_selection, _ = _select_candidates(
        scan_records=scan_records,
        source_root=input_root,
        count=8,
        strategy="size-stratified",
        seed=20260430,
        selected_by="noaa-spec build-validation-bundle",
    )
    second_selection, _ = _select_candidates(
        scan_records=scan_records,
        source_root=input_root,
        count=8,
        strategy="size-stratified",
        seed=20260430,
        selected_by="noaa-spec build-validation-bundle",
    )

    assert [candidate.station_id for candidate in first_selection] == [
        candidate.station_id for candidate in second_selection
    ]


def test_validate_command_writes_expected_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    input_root = tmp_path / "input"
    output_root = tmp_path / "output"
    input_root.mkdir()
    _make_station_pool(input_root, station_count=8)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "prog",
            "build-validation-bundle",
            "--source-root",
            str(input_root),
            "--output-root",
            str(output_root),
            "--count",
            "8",
            "--seed",
            "20260430",
            "--build-id",
            "test-build",
        ],
    )
    cli.main()

    selection_manifest = pd.read_csv(output_root / "station_selection_manifest.csv")
    expected_selection_columns = {
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
        "copied_utc",
    }
    assert expected_selection_columns.issubset(selection_manifest.columns)
    assert selection_manifest["archived_raw_input_path"].astype(str).str.startswith("raw_inputs/").any()

    first_selected = selection_manifest[selection_manifest["selection_status"] == "selected"].iloc[0]
    archived_raw_path = output_root / str(first_selected["archived_raw_input_path"])
    expected_raw_sha = hashlib.sha256(archived_raw_path.read_bytes()).hexdigest()
    assert str(first_selected["raw_sha256"]) == expected_raw_sha

    run_manifest = pd.read_json(output_root / "run_manifest.json", typ="series")
    assert "operational smoke validation for a stratified 100-station sample" in run_manifest[
        "reproducibility_boundary_note"
    ]
    assert "archived with checksums" in run_manifest["reproducibility_boundary_note"]

    station_results = pd.read_csv(output_root / "station_results.csv")
    expected_result_columns = {
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
    }
    assert expected_result_columns.issubset(station_results.columns)
    assert set(station_results["status"]) == {"success"}

    checksums_text = (output_root / "checksums.txt").read_text(encoding="utf-8")
    assert "raw_inputs/" in checksums_text
    assert "station_selection_manifest.csv" in checksums_text
    assert "station_results.csv" in checksums_text
    assert "run_manifest.json" in checksums_text
    assert "summary.md" in checksums_text
    assert "strict_parse_summary_report.json" in checksums_text
    assert "strict_parse_summary_report.md" in checksums_text
    assert "archive_manifest.json" in checksums_text

    archive_manifest = pd.read_json(output_root / "archive_manifest.json", typ="series")
    assert archive_manifest["DOI"] == "TO_BE_ADDED_BEFORE_JOSS_SUBMISSION"

    summary_text = (output_root / "summary.md").read_text(encoding="utf-8")
    assert "does not prove correctness over the full NOAA corpus" in summary_text
    assert "inspectable and rerunnable without relying on live NOAA availability" in summary_text
    assert "not manually selected for favorable outcomes" in summary_text


def test_validation_bundle_reports_strict_token_diagnostics(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    input_root = tmp_path / "input"
    output_root = tmp_path / "output"
    input_root.mkdir()
    for index in range(8):
        station_id = f"{20000000000 + index}"
        extra_fields = {"SA1": "215,1"} if index == 0 else None
        _write_station_csv(input_root, station_id, row_count=index + 1, extra_fields=extra_fields)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "prog",
            "build-validation-bundle",
            "--source-root",
            str(input_root),
            "--output-root",
            str(output_root),
            "--count",
            "8",
            "--seed",
            "20260430",
            "--build-id",
            "strict-token-build",
        ],
    )
    cli.main()

    quality_reports = sorted((output_root / "quality_reports").glob("*_quality_report.json"))
    station_payload = None
    for path in quality_reports:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if int(payload["strict_parse_summary"]["token_rejection_count"]) > 0:
            station_payload = payload
            break

    assert station_payload is not None
    strict_summary = station_payload["strict_parse_summary"]
    assert strict_summary["token_rejection_count"] == 1
    assert strict_summary["token_rejections_by_identifier"] == {"SA1": 1}
    assert strict_summary["token_rejections_by_reason"] == {"token_width_mismatch": 1}
    assert strict_summary["token_rejections_by_identifier_part"] == {"SA1.part_1": 1}
    assert strict_summary["token_rejection_examples"][0]["identifier"] == "SA1"
    assert strict_summary["token_rejection_examples"][0]["part_index"] == 1
    assert strict_summary["token_rejection_examples"][0]["expected_width"] == 4

    strict_report_md = (output_root / "strict_parse_summary_report.md").read_text(encoding="utf-8")
    strict_report_json = json.loads(
        (output_root / "strict_parse_summary_report.json").read_text(encoding="utf-8")
    )
    summary_text = (output_root / "summary.md").read_text(encoding="utf-8")
    canonical_frame = pd.read_csv(output_root / "canonical_cleaned" / f"{station_payload['station_id']}_cleaned.csv")

    assert "## Token validation rejections" in strict_report_md
    assert strict_report_json["token_validation_rejections"]["total_token_rejection_count"] == 1
    assert strict_report_json["token_validation_rejections"]["affected_station_count"] == 1
    assert "Strict token-level validation rejections are diagnostic." in summary_text
    assert "They did not cause station-level failure or row loss in this validation run." in summary_text
    assert int(station_payload["input_rows"]) == int(station_payload["output_rows"]) == len(canonical_frame)
