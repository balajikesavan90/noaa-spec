from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import re

import pandas as pd
import pytest

import noaa_climate_data.cleaning_runner as cleaning_runner
from noaa_climate_data.cleaning_runner import (
    CleaningRunConfig,
    RunWriteFlags,
    _discover_stations,
    default_roots_for_mode,
    run_cleaning_run,
)
from noaa_climate_data.domains.registry import domain_names
from noaa_climate_data.research_reports import domain_quality_report_names


def _sample_raw_df(station_id: str) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "STATION": [station_id],
            "DATE": ["2020-01-01T00:00:00"],
            "TIME": ["0000"],
            "TMP": ["0010,1"],
        }
    )


def _sample_raw_df_with_repeated_wind_fields(station_id: str) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "STATION": [station_id],
            "DATE": ["20200101"],
            "TIME": ["0000"],
            "OD1": ["9,99,999,0000,1"],
            "OD2": ["9,99,999,0000,1"],
            "OE1": ["1,24,00000,999,1200,4"],
            "OE2": ["1,24,00000,999,1200,4"],
        }
    )


def _sample_raw_df_with_remarks(station_id: str) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "STATION": [station_id],
            "DATE": ["20200101"],
            "TIME": ["0000"],
            "TMP": ["0010,1"],
            "REM": ["clear sky"],
        }
    )


def _write_raw_csv(station_dir: Path, station_id: str) -> Path:
    station_dir.mkdir(parents=True, exist_ok=True)
    raw_path = station_dir / "LocationData_Raw.csv"
    _sample_raw_df(station_id).to_csv(raw_path, index=False)
    return raw_path


def _write_raw_csv_with_repeated_wind_fields(station_dir: Path, station_id: str) -> Path:
    station_dir.mkdir(parents=True, exist_ok=True)
    raw_path = station_dir / "LocationData_Raw.csv"
    _sample_raw_df_with_repeated_wind_fields(station_id).to_csv(raw_path, index=False)
    return raw_path


def _write_raw_csv_with_remarks(station_dir: Path, station_id: str) -> Path:
    station_dir.mkdir(parents=True, exist_ok=True)
    raw_path = station_dir / "LocationData_Raw.csv"
    _sample_raw_df_with_remarks(station_id).to_csv(raw_path, index=False)
    return raw_path


def _write_raw_parquet(station_dir: Path, station_id: str) -> Path:
    station_dir.mkdir(parents=True, exist_ok=True)
    raw_path = station_dir / "LocationData_Raw.parquet"
    _sample_raw_df(station_id).to_parquet(raw_path, index=False)
    return raw_path


def _flags(
    *,
    cleaned: bool = True,
    domain: bool = False,
    quality: bool = True,
    reports: bool = False,
    global_summary: bool = False,
) -> RunWriteFlags:
    return RunWriteFlags(
        write_cleaned_station=cleaned,
        write_domain_splits=domain,
        write_station_quality_profile=quality,
        write_station_reports=reports,
        write_global_summary=global_summary,
    )


def _config(
    tmp_path: Path,
    *,
    mode: str,
    input_format: str,
    run_id: str,
    input_root: Path,
    manifest_first: bool | None = None,
    manifest_refresh: bool = False,
    station_ids: tuple[str, ...] = (),
    limit: int | None = None,
    force: bool = False,
    write_flags: RunWriteFlags | None = None,
    output_root: Path | None = None,
    reports_root: Path | None = None,
    quality_root: Path | None = None,
    manifest_root: Path | None = None,
) -> CleaningRunConfig:
    base = tmp_path / "release" / f"build_{run_id}"
    return CleaningRunConfig(
        mode=mode,
        input_root=input_root,
        input_format=input_format,
        output_root=output_root or (base / "canonical_cleaned"),
        reports_root=reports_root or (base / "quality_reports"),
        quality_profile_root=quality_root or (base / "quality_reports" / "station_quality"),
        manifest_root=manifest_root or (base / "manifests"),
        run_id=run_id,
        limit=limit,
        station_ids=station_ids,
        force=force,
        manifest_first=(mode == "batch_parquet_dir") if manifest_first is None else manifest_first,
        manifest_refresh=manifest_refresh,
        write_flags=write_flags or _flags(),
    )


def _sha256(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def test_quality_profile_null_counts_are_per_identifier_rows_not_part_sums() -> None:
    builder = cleaning_runner._QualityProfileBuilder()
    cleaned = pd.DataFrame(
        {
            "OD1__part1": [pd.NA, pd.NA],
            "OD1__part2": [pd.NA, pd.NA],
            "OD1__part3": [pd.NA, pd.NA],
        }
    )

    profile = builder.build(cleaned=cleaned, station_id="01234567890")
    assert profile["rows_total"] == 2
    assert profile["null_counts_by_identifier"]["OD1"] == 2


def test_quality_profile_separates_structural_and_substantive_impacts() -> None:
    builder = cleaning_runner._QualityProfileBuilder()
    cleaned = pd.DataFrame(
        {
            "qc_control_invalid_date": [True, False, False],
            "TMP__qc_reason": ["SENTINEL_MISSING", pd.NA, "BAD_QUALITY_CODE"],
        }
    )

    profile = builder.build(cleaned=cleaned, station_id="01234567890")
    assert profile["rows_with_structural_impacts"] == 1
    assert profile["rows_with_sentinel_impacts"] == 1
    assert profile["rows_with_quality_code_impacts"] == 1
    assert profile["rows_with_qc_flags"] == 2
    assert float(profile["fraction_rows_impacted"]) == pytest.approx(2.0 / 3.0)


def test_usable_row_series_treats_text_only_rows_as_usable() -> None:
    frame = pd.DataFrame(
        {
            "station_id": ["01234567890", "01234567890"],
            "DATE": ["2020-01-01T00:00:00", "2020-01-01T01:00:00"],
            "remarks_text": ["clear sky", pd.NA],
        }
    )

    usable = cleaning_runner._usable_row_series(frame)
    assert usable.astype(bool).tolist() == [True, False]


def test_quality_assessment_keeps_threshold_findings_advisory() -> None:
    quality_frames = {
        "field_completeness": pd.DataFrame(
            {"field_completeness_ratio": [0.75]}
        ),
        "domain_usability_summary": pd.DataFrame(
            {"station_id": ["01234567890"], "domain": ["core_meteorology"], "usable_row_rate": [0.10]}
        ),
        "sentinel_frequency": pd.DataFrame(
            {
                "station_id": ["01234567890"],
                "sentinel_row_rate": [0.60],
                "sentinel_events_per_row": [1.5],
                "sentinel_events": [3],
                "rows_with_sentinel_impacts": [2],
            }
        ),
        "quality_code_exclusions": pd.DataFrame(
            {
                "station_id": ["01234567890"],
                "quality_code_exclusion_rate": [0.80],
                "quality_code_exclusion_events_per_row": [0.80],
                "quality_code_exclusions": [4],
                "rows_with_quality_code_exclusions": [4],
            }
        ),
        "station_year_quality": pd.DataFrame(
            {
                "station_id": ["01234567890"],
                "year": [2020],
                "fraction_rows_impacted": [0.70],
                "fraction_rows_structural_impacted": [0.20],
                "rows_total": [10],
                "rows_with_qc_flags": [7],
                "rows_with_structural_impacts": [2],
                "rows_with_sentinel_impacts": [3],
                "rows_with_quality_code_impacts": [4],
                "rows_with_other_substantive_impacts": [0],
            }
        ),
    }
    status_df = pd.DataFrame({"status": ["completed"]})

    summary = cleaning_runner._build_quality_assessment(
        config=_config(
            Path("/tmp"),
            mode="test_csv_dir",
            input_format="csv",
            run_id="run_advisory_quality",
            input_root=Path("/tmp/inputs"),
        ),
        status_df=status_df,
        quality_frames=quality_frames,
        build_metadata_path=Path("/tmp/build_metadata.json"),
    )
    assert summary["advisory_only"] is True
    assert summary["threshold_policy"] == "advisory"
    assert summary["threshold_evaluations"]["quality_code_exclusion_rate_threshold_ok"] is False
    assert summary["threshold_evaluations"]["domain_usability_thresholds_ok"] is False
    assert 0.0 <= float(summary["summary_scores"]["quality_score"]) <= 1.0
    assert (
        float(summary["summary_scores"]["quality_score_components"]["quality_code_exclusion"]) < 1.0
    )
    assert float(summary["summary_scores"]["quality_score_components"]["domain_usability"]) < 1.0
    assert summary["sentinel_heavy_summaries"]["top_sentinel_stations"][0]["station_id"] == "01234567890"


def test_publication_structural_sanity_check_uses_bounds_not_quality_thresholds() -> None:
    quality_frames = {
        "field_completeness": pd.DataFrame({"field_completeness_ratio": [0.75]}),
        "domain_usability_summary": pd.DataFrame({"usable_row_rate": [0.10]}),
        "sentinel_frequency": pd.DataFrame({"sentinel_row_rate": [0.90]}),
        "quality_code_exclusions": pd.DataFrame({"quality_code_exclusion_rate": [0.80]}),
        "station_year_quality": pd.DataFrame({"usable_row_rate": [0.95]}),
    }

    summary = cleaning_runner._publication_structural_sanity_check(quality_frames)
    assert summary["passed"] is True
    assert summary["quality_code_exclusion_rate_bounds_ok"] is True
    assert summary["domain_usable_row_rate_bounds_ok"] is True


def test_station_discovery_excludes_non_station_directories(tmp_path: Path) -> None:
    input_root = tmp_path / "inputs"
    _write_raw_csv(input_root / "01234567890", "01234567890")
    _write_raw_csv(input_root / "NOAA Demo Data", "00000000000")
    (input_root / "not_a_station").mkdir(parents=True)
    (input_root / "12345678901").mkdir(parents=True)

    config = _config(
        tmp_path,
        mode="test_csv_dir",
        input_format="csv",
        run_id="run_discovery",
        input_root=input_root,
        write_flags=_flags(cleaned=False, quality=False),
    )
    result = run_cleaning_run(config)

    assert result["total"] == 1
    manifest = pd.read_csv(config.manifest_root / "run_manifest.csv", dtype=str)
    assert manifest["station_id"].astype(str).tolist() == ["01234567890"]


def test_mode_specific_file_discovery(tmp_path: Path) -> None:
    input_root = tmp_path / "inputs"
    _write_raw_csv(input_root / "01234567890", "01234567890")
    _write_raw_parquet(input_root / "09876543210", "09876543210")

    csv_config = _config(
        tmp_path,
        mode="test_csv_dir",
        input_format="csv",
        run_id="run_csv_mode",
        input_root=input_root,
        write_flags=_flags(cleaned=False, quality=False),
    )
    parquet_config = _config(
        tmp_path,
        mode="batch_parquet_dir",
        input_format="parquet",
        run_id="run_parquet_mode",
        input_root=input_root,
        write_flags=_flags(cleaned=False, quality=False),
    )
    test_parquet_config = _config(
        tmp_path,
        mode="test_parquet_dir",
        input_format="parquet",
        run_id="run_test_parquet_mode",
        input_root=input_root,
        write_flags=_flags(cleaned=False, quality=False),
    )

    csv_discovered = _discover_stations(csv_config)
    parquet_discovered = _discover_stations(parquet_config)
    test_parquet_discovered = _discover_stations(test_parquet_config)

    assert [row["station_id"] for row in csv_discovered] == ["01234567890"]
    assert [row["station_id"] for row in parquet_discovered] == ["09876543210"]
    assert [row["station_id"] for row in test_parquet_discovered] == ["09876543210"]


def test_test_mode_discovers_stations_by_hardcoded_speed_order(tmp_path: Path) -> None:
    input_root = tmp_path / "inputs"
    station_ids = ("01116099999", "03041099999", "16754399999", "27679099999", "01234567890")
    for station_id in station_ids:
        _write_raw_parquet(input_root / station_id, station_id)

    config = _config(
        tmp_path,
        mode="test_parquet_dir",
        input_format="parquet",
        run_id="run_current",
        input_root=input_root,
        write_flags=_flags(cleaned=False, quality=False),
    )

    discovered = _discover_stations(config)
    assert [row["station_id"] for row in discovered] == [
        "27679099999",
        "03041099999",
        "16754399999",
        "01116099999",
        "01234567890",
    ]


def test_batch_mode_station_discovery_keeps_station_id_order(tmp_path: Path) -> None:
    input_root = tmp_path / "inputs"
    station_ids = ("01116099999", "03041099999", "16754399999")
    for station_id in station_ids:
        _write_raw_parquet(input_root / station_id, station_id)

    config = _config(
        tmp_path,
        mode="batch_parquet_dir",
        input_format="parquet",
        run_id="run_batch",
        input_root=input_root,
        write_flags=_flags(cleaned=False, quality=False),
    )

    discovered = _discover_stations(config)
    assert [row["station_id"] for row in discovered] == sorted(station_ids)


def test_default_roots_for_mode_uses_release_build_layout() -> None:
    run_id = "20260101T120000Z"
    roots = default_roots_for_mode("batch_parquet_dir", run_id)

    assert roots["output_root"] == Path("release") / f"build_{run_id}" / "canonical_cleaned"
    assert roots["reports_root"] == Path("release") / f"build_{run_id}" / "quality_reports"
    assert roots["quality_profile_root"] == (
        Path("release") / f"build_{run_id}" / "quality_reports" / "station_quality"
    )
    assert roots["manifest_root"] == Path("release") / f"build_{run_id}" / "manifests"


def test_release_layout_contract_requires_sibling_roots(tmp_path: Path) -> None:
    input_root = tmp_path / "inputs"
    _write_raw_csv(input_root / "01234567890", "01234567890")

    config = _config(
        tmp_path,
        mode="test_csv_dir",
        input_format="csv",
        run_id="run_bad_layout",
        input_root=input_root,
        reports_root=tmp_path / "non_release" / "quality_reports",
        write_flags=_flags(cleaned=False, quality=False),
    )

    with pytest.raises(ValueError, match="Release layout contract violation"):
        run_cleaning_run(config)


def test_manifest_snapshot_is_deterministic(tmp_path: Path) -> None:
    input_root = tmp_path / "inputs"
    for station_id in ("94368099999", "01116099999", "40435099999"):
        _write_raw_csv(input_root / station_id, station_id)

    config = _config(
        tmp_path,
        mode="test_csv_dir",
        input_format="csv",
        run_id="run_manifest",
        input_root=input_root,
        write_flags=_flags(cleaned=False, quality=False),
    )
    run_cleaning_run(config)

    manifest = pd.read_csv(config.manifest_root / "run_manifest.csv", dtype=str)
    assert manifest["station_id"].astype(str).tolist() == [
        "01116099999",
        "40435099999",
        "94368099999",
    ]
    assert "input_size_bytes" in manifest.columns


def test_run_config_fingerprint_enforced_and_refreshable(tmp_path: Path) -> None:
    input_root = tmp_path / "inputs"
    _write_raw_csv(input_root / "01234567890", "01234567890")

    run_id = "run_config_guard"
    first = _config(
        tmp_path,
        mode="test_csv_dir",
        input_format="csv",
        run_id=run_id,
        input_root=input_root,
        write_flags=_flags(cleaned=False, domain=False, quality=False),
    )
    run_cleaning_run(first)

    changed = _config(
        tmp_path,
        mode="test_csv_dir",
        input_format="csv",
        run_id=run_id,
        input_root=input_root,
        write_flags=_flags(cleaned=False, domain=True, quality=False),
    )
    with pytest.raises(ValueError, match="different configuration"):
        run_cleaning_run(changed)

    refreshed = _config(
        tmp_path,
        mode="test_csv_dir",
        input_format="csv",
        run_id=run_id,
        input_root=input_root,
        manifest_refresh=True,
        write_flags=_flags(cleaned=False, domain=True, quality=False),
    )
    run_cleaning_run(refreshed)

    run_config = json.loads((refreshed.manifest_root / "run_config.json").read_text(encoding="utf-8"))
    assert run_config["write_flags"]["write_domain_splits"] is True


def test_build_metadata_captures_reproducibility_fields(tmp_path: Path) -> None:
    input_root = tmp_path / "inputs"
    station_id = "01234567890"
    raw_path = _write_raw_csv(input_root / station_id, station_id)

    config = _config(
        tmp_path,
        mode="test_csv_dir",
        input_format="csv",
        run_id="20260101T120000Z",
        input_root=input_root,
        write_flags=_flags(cleaned=False, domain=False, quality=False),
    )
    result = run_cleaning_run(config)

    build_metadata_path = config.manifest_root / "build_metadata.json"
    assert result["build_metadata"] == build_metadata_path
    assert build_metadata_path.exists()

    payload = json.loads(build_metadata_path.read_text(encoding="utf-8"))
    run_config = json.loads((config.manifest_root / "run_config.json").read_text(encoding="utf-8"))

    assert payload["build_id"] == "20260101T120000Z"
    assert payload["build_timestamp"] == "2026-01-01T12:00:00+00:00"
    assert payload["config_identity"] == run_config["config_fingerprint"]
    assert isinstance(payload["code_revision"], str)
    assert payload["code_revision"]

    source_scope = payload["source_scope"]
    assert source_scope["mode"] == "test_csv_dir"
    assert source_scope["input_format"] == "csv"
    assert source_scope["manifest_station_count"] == 1
    assert source_scope["station_ids"] == [station_id]
    assert source_scope["input_paths"] == [str(raw_path.resolve())]


def test_nonstandard_run_id_uses_real_build_and_creation_timestamps(tmp_path: Path) -> None:
    input_root = tmp_path / "inputs"
    station_id = "01234567890"
    _write_raw_csv(input_root / station_id, station_id)

    run_id = "contract_check_20260308T104353-0700"
    config = _config(
        tmp_path,
        mode="test_csv_dir",
        input_format="csv",
        run_id=run_id,
        input_root=input_root,
        write_flags=_flags(cleaned=True, domain=True, quality=True, reports=False, global_summary=False),
    )
    run_cleaning_run(config)

    payload = json.loads((config.manifest_root / "build_metadata.json").read_text(encoding="utf-8"))
    build_timestamp = str(payload["build_timestamp"])
    assert build_timestamp != run_id
    datetime.fromisoformat(build_timestamp)

    release_manifest = pd.read_csv(config.manifest_root / "release_manifest.csv", dtype=str)
    assert not release_manifest.empty
    creation_timestamps = set(release_manifest["creation_timestamp"].astype(str))
    assert creation_timestamps == {build_timestamp}
    assert run_id not in creation_timestamps
    for value in creation_timestamps:
        datetime.fromisoformat(value)


def test_build_metadata_validation_rejects_invalid_timestamp(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="build_metadata build_timestamp"):
        cleaning_runner._validate_or_write_build_metadata(
            build_metadata_path=tmp_path / "build_metadata.json",
            payload={
                "build_id": "run_invalid_timestamp",
                "build_timestamp": "not-a-timestamp",
                "code_revision": "deadbeef",
                "config_identity": "config-fingerprint",
                "source_scope": {
                    "mode": "test_csv_dir",
                    "input_root": str(tmp_path / "inputs"),
                    "input_format": "csv",
                    "manifest_station_count": 0,
                    "station_ids": [],
                    "input_paths": [],
                },
            },
            manifest_refresh=False,
        )


def test_release_manifest_validation_rejects_invalid_creation_timestamp(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="invalid creation_timestamp"):
        cleaning_runner._write_release_manifest(
            tmp_path / "release_manifest.csv",
            [
                {
                    "artifact_id": "raw_source/run_invalid_timestamp/01234567890",
                    "artifact_type": "raw_source",
                    "artifact_path": str(tmp_path / "raw.csv"),
                    "schema_version": "v1",
                    "build_id": "run_invalid_timestamp",
                    "input_lineage": "[]",
                    "row_count": 0,
                    "checksum": "0" * 64,
                    "creation_timestamp": "invalid",
                }
            ],
        )


def test_file_manifest_validation_rejects_duplicate_artifact_ids(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="duplicate artifact_id"):
        cleaning_runner._write_full_file_manifest(
            tmp_path / "file_manifest.csv",
            [
                {
                    "artifact_id": "build_file/run_duplicate_id/inputs/01234567890/LocationData_Raw.csv",
                    "artifact_type": "build_file",
                    "artifact_path": str(tmp_path / "inputs" / "01234567890" / "LocationData_Raw.csv"),
                    "schema_version": "v1",
                    "build_id": "run_duplicate_id",
                    "input_lineage": "[]",
                    "row_count": 1,
                    "checksum": "1" * 64,
                    "creation_timestamp": "2026-01-01T00:00:00-08:00",
                },
                {
                    "artifact_id": "build_file/run_duplicate_id/inputs/01234567890/LocationData_Raw.csv",
                    "artifact_type": "build_file",
                    "artifact_path": str(tmp_path / "inputs" / "01234567891" / "LocationData_Raw.csv"),
                    "schema_version": "v1",
                    "build_id": "run_duplicate_id",
                    "input_lineage": "[]",
                    "row_count": 1,
                    "checksum": "2" * 64,
                    "creation_timestamp": "2026-01-01T00:00:00-08:00",
                },
            ],
        )


def test_manifest_refresh_rebuilds_station_snapshot(tmp_path: Path) -> None:
    input_root = tmp_path / "inputs"
    _write_raw_parquet(input_root / "01234567890", "01234567890")

    run_id = "run_refresh"
    base = _config(
        tmp_path,
        mode="batch_parquet_dir",
        input_format="parquet",
        run_id=run_id,
        input_root=input_root,
        write_flags=_flags(cleaned=False, quality=False, global_summary=False),
    )
    run_cleaning_run(base)
    manifest_before = pd.read_csv(base.manifest_root / "run_manifest.csv", dtype=str)
    assert manifest_before["station_id"].astype(str).tolist() == ["01234567890"]

    _write_raw_parquet(input_root / "09876543210", "09876543210")

    run_cleaning_run(base)
    manifest_still = pd.read_csv(base.manifest_root / "run_manifest.csv", dtype=str)
    assert manifest_still["station_id"].astype(str).tolist() == ["01234567890"]

    refreshed = _config(
        tmp_path,
        mode="batch_parquet_dir",
        input_format="parquet",
        run_id=run_id,
        input_root=input_root,
        manifest_refresh=True,
        write_flags=_flags(cleaned=False, quality=False, global_summary=False),
    )
    run_cleaning_run(refreshed)
    manifest_after = pd.read_csv(refreshed.manifest_root / "run_manifest.csv", dtype=str)
    assert manifest_after["station_id"].astype(str).tolist() == [
        "01234567890",
        "09876543210",
    ]


def test_resumable_skip_requires_status_outputs_and_success_marker(tmp_path: Path) -> None:
    input_root = tmp_path / "inputs"
    station_id = "01234567890"
    _write_raw_csv(input_root / station_id, station_id)

    config = _config(
        tmp_path,
        mode="test_csv_dir",
        input_format="csv",
        run_id="run_resume",
        input_root=input_root,
        write_flags=_flags(cleaned=True, quality=True),
    )

    first = run_cleaning_run(config)
    second = run_cleaning_run(config)

    assert first["processed"] == 1
    assert second["processed"] == 0
    assert second["skipped"] >= 1

    success_path = config.output_root / station_id / "_SUCCESS.json"
    success_path.unlink()

    third = run_cleaning_run(config)
    assert third["processed"] == 1


def test_success_marker_includes_required_release_metadata_fields(tmp_path: Path) -> None:
    input_root = tmp_path / "inputs"
    station_id = "01234567890"
    _write_raw_csv(input_root / station_id, station_id)

    config = _config(
        tmp_path,
        mode="test_csv_dir",
        input_format="csv",
        run_id="run_success_marker_metadata",
        input_root=input_root,
        write_flags=_flags(cleaned=True, quality=True),
    )
    run_cleaning_run(config)

    success_payload = json.loads(
        (config.output_root / station_id / "_SUCCESS.json").read_text(encoding="utf-8")
    )

    expected_fields = {
        "artifact_id",
        "schema_version",
        "build_id",
        "input_lineage",
        "row_count",
        "checksum",
        "creation_timestamp",
    }
    assert expected_fields.issubset(success_payload.keys())
    assert success_payload["build_id"] == config.run_id
    assert success_payload["row_count"] == success_payload["row_count_cleaned"]
    assert success_payload["input_lineage"] == [
        str((input_root / station_id / "LocationData_Raw.csv").resolve())
    ]
    assert re.fullmatch(r"[0-9a-f]{64}", str(success_payload["checksum"]))


def test_quality_profile_generated_without_rereading_cleaned_outputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    input_root = tmp_path / "inputs"
    station_id = "01234567890"
    _write_raw_csv(input_root / station_id, station_id)

    original_read_csv = cleaning_runner.pd.read_csv

    def guarded_read_csv(path: object, *args: object, **kwargs: object) -> pd.DataFrame:
        if isinstance(path, (str, Path)) and "LocationData_Cleaned" in str(path):
            raise AssertionError("cleaned station output was re-read")
        return original_read_csv(path, *args, **kwargs)

    monkeypatch.setattr(cleaning_runner.pd, "read_csv", guarded_read_csv)

    config = _config(
        tmp_path,
        mode="test_csv_dir",
        input_format="csv",
        run_id="run_profile_io",
        input_root=input_root,
        write_flags=_flags(cleaned=True, quality=True),
    )
    run_cleaning_run(config)

    profile_path = config.quality_profile_root / f"station_{station_id}.json"
    assert profile_path.exists()


def test_mandatory_quality_artifacts_are_written_with_station_quality_profiles(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "inputs"
    station_id = "01234567890"
    _write_raw_csv(input_root / station_id, station_id)

    config = _config(
        tmp_path,
        mode="test_csv_dir",
        input_format="csv",
        run_id="run_quality_artifacts",
        input_root=input_root,
        write_flags=_flags(cleaned=True, quality=True, reports=False, global_summary=False),
    )
    run_cleaning_run(config)

    expected_artifacts = (
        "field_completeness",
        "sentinel_frequency",
        "quality_code_exclusions",
        "domain_usability_summary",
        "station_year_quality",
    )
    for artifact_name in expected_artifacts:
        artifact_path = config.reports_root / f"{artifact_name}.csv"
        assert artifact_path.exists()
        frame = pd.read_csv(artifact_path)
        assert not frame.empty

    field_completeness = pd.read_csv(config.reports_root / "field_completeness.csv")
    assert {"field_identifier", "null_count", "field_completeness_ratio"}.issubset(field_completeness.columns)

    sentinel_frequency = pd.read_csv(config.reports_root / "sentinel_frequency.csv")
    assert {
        "sentinel_events",
        "rows_with_sentinel_impacts",
        "sentinel_row_rate",
        "sentinel_events_per_row",
    }.issubset(sentinel_frequency.columns)

    domain_usability = pd.read_csv(config.reports_root / "domain_usability_summary.csv")
    assert {
        "domain",
        "usable_rows",
        "usable_row_rate",
        "artifact_mode",
        "advisory_only",
    }.issubset(domain_usability.columns)
    assert set(domain_usability["artifact_mode"].astype(str)) == {"fallback_no_domain_splits"}
    assert set(domain_usability["advisory_only"].astype(str).str.lower()) == {"true"}

    station_year_quality = pd.read_csv(config.reports_root / "station_year_quality.csv")
    assert {"qc_attrition_rows", "usable_row_rate"}.issubset(station_year_quality.columns)

    summary_md = config.reports_root / "quality_reports_summary.md"
    assert summary_md.exists()
    summary_text = summary_md.read_text(encoding="utf-8")
    assert "Quality Reports Summary" in summary_text
    assert "Highest Quality-Code Exclusion Rates" in summary_text
    assert "Highest Sentinel Event Rates" in summary_text


def test_run_status_records_phase_timings_and_station_metrics(tmp_path: Path) -> None:
    input_root = tmp_path / "inputs"
    station_id = "01234567890"
    _write_raw_csv_with_repeated_wind_fields(input_root / station_id, station_id)

    config = _config(
        tmp_path,
        mode="test_csv_dir",
        input_format="csv",
        run_id="run_status_metrics",
        input_root=input_root,
        write_flags=_flags(cleaned=True, domain=True, quality=True, reports=False, global_summary=False),
    )
    run_cleaning_run(config)

    run_status = pd.read_csv(config.manifest_root / "run_status.csv", dtype=str)
    row = run_status.iloc[0].to_dict()
    expected_columns = {
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
    }
    assert expected_columns.issubset(run_status.columns)
    assert float(row["elapsed_total_seconds"]) >= 0.0
    assert float(row["elapsed_seconds"]) == pytest.approx(float(row["elapsed_total_seconds"]))
    assert int(row["row_count_raw"]) == 1
    assert int(row["row_count_cleaned"]) == 1
    assert int(row["raw_columns"]) >= 4
    assert int(row["cleaned_columns"]) >= int(row["raw_columns"])
    assert int(row["input_size_bytes"]) > 0
    assert int(row["cleaned_size_bytes"]) > 0


def test_field_completeness_ratios_are_bounded_between_zero_and_one(tmp_path: Path) -> None:
    input_root = tmp_path / "inputs"
    station_id = "01234567890"
    _write_raw_csv(input_root / station_id, station_id)

    config = _config(
        tmp_path,
        mode="test_csv_dir",
        input_format="csv",
        run_id="run_quality_ratio_bounds",
        input_root=input_root,
        write_flags=_flags(cleaned=True, quality=True, reports=False, global_summary=False),
    )
    run_cleaning_run(config)

    field_completeness = pd.read_csv(config.reports_root / "field_completeness.csv")
    assert not field_completeness.empty

    ratios = pd.to_numeric(field_completeness["field_completeness_ratio"], errors="raise")
    assert ratios.between(0.0, 1.0, inclusive="both").all()


def test_release_manifest_contains_canonical_domain_and_quality_artifact_rows(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "inputs"
    station_id = "01234567890"
    raw_path = _write_raw_csv(input_root / station_id, station_id)

    config = _config(
        tmp_path,
        mode="test_csv_dir",
        input_format="csv",
        run_id="run_release_manifest",
        input_root=input_root,
        write_flags=_flags(cleaned=True, domain=True, quality=True, reports=False, global_summary=False),
    )
    result = run_cleaning_run(config)

    release_manifest_path = config.manifest_root / "release_manifest.csv"
    assert result["release_manifest"] == release_manifest_path
    assert release_manifest_path.exists()

    manifest = pd.read_csv(release_manifest_path, dtype=str)
    assert set(manifest.columns) == {
        "artifact_id",
        "artifact_type",
        "artifact_path",
        "schema_version",
        "build_id",
        "input_lineage",
        "row_count",
        "checksum",
        "creation_timestamp",
    }
    assert set(manifest["artifact_type"].astype(str)) >= {
        "raw_source",
        "canonical_dataset",
        "domain_dataset",
        "quality_report",
    }

    raw_source_row = manifest[manifest["artifact_type"] == "raw_source"].iloc[0].to_dict()
    assert raw_source_row["build_id"] == config.run_id
    assert json.loads(str(raw_source_row["input_lineage"])) == [str(raw_path.resolve())]

    canonical_row = manifest[manifest["artifact_type"] == "canonical_dataset"].iloc[0].to_dict()
    assert canonical_row["build_id"] == config.run_id
    assert json.loads(str(canonical_row["input_lineage"])) == [
        f"raw_source/{config.run_id}/{station_id}"
    ]

    domain_rows = manifest[manifest["artifact_type"] == "domain_dataset"]
    assert not domain_rows.empty
    domain_lineage = json.loads(str(domain_rows.iloc[0]["input_lineage"]))
    assert domain_lineage == [f"canonical_dataset/{config.run_id}/{station_id}"]

    quality_rows = manifest[manifest["artifact_type"] == "quality_report"]
    expected_quality_ids = {
        f"quality_report/{config.run_id}/field_completeness",
        f"quality_report/{config.run_id}/sentinel_frequency",
        f"quality_report/{config.run_id}/quality_code_exclusions",
        f"quality_report/{config.run_id}/domain_usability_summary",
        f"quality_report/{config.run_id}/station_year_quality",
    }
    assert expected_quality_ids.issubset(set(quality_rows["artifact_id"].astype(str)))

    artifact_ids = set(manifest["artifact_id"].astype(str))
    first_quality_lineage = json.loads(str(quality_rows.iloc[0]["input_lineage"]))
    assert any(value.startswith("canonical_dataset/") for value in first_quality_lineage)
    assert any(value.startswith("domain_dataset/") for value in first_quality_lineage)
    assert all(value in artifact_ids for value in first_quality_lineage)


def test_file_manifest_captures_station_outputs_with_dual_manifest_model(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "inputs"
    station_id = "01234567890"
    _write_raw_csv(input_root / station_id, station_id)

    config = _config(
        tmp_path,
        mode="test_csv_dir",
        input_format="csv",
        run_id="run_file_manifest_scope",
        input_root=input_root,
        write_flags=_flags(cleaned=True, domain=True, quality=True, reports=True, global_summary=False),
    )
    result = run_cleaning_run(config)

    file_manifest_path = config.manifest_root / "file_manifest.csv"
    assert result["file_manifest"] == file_manifest_path
    assert file_manifest_path.exists()

    file_manifest = pd.read_csv(file_manifest_path, dtype=str)
    assert not file_manifest.empty
    assert {
        "station_split_manifest",
        "station_report",
        "station_quality_profile",
        "success_marker",
        "release_manifest",
        "quality_assessment",
        "publication_readiness_gate",
    }.issubset(set(file_manifest["artifact_type"].astype(str)))

    release_manifest = pd.read_csv(config.manifest_root / "release_manifest.csv", dtype=str)
    assert "success_marker" not in set(release_manifest["artifact_type"].astype(str))


def test_file_manifest_uses_unique_artifact_ids_for_multi_station_raw_inputs(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "inputs"
    station_ids = ("01234567890", "01234567891")
    for station_id in station_ids:
        _write_raw_csv(input_root / station_id, station_id)

    config = _config(
        tmp_path,
        mode="test_csv_dir",
        input_format="csv",
        run_id="run_file_manifest_unique_raw_ids",
        input_root=input_root,
        write_flags=_flags(cleaned=True, domain=False, quality=True, reports=False, global_summary=False),
    )
    run_cleaning_run(config)

    file_manifest = pd.read_csv(config.manifest_root / "file_manifest.csv", dtype=str)
    assert file_manifest["artifact_id"].astype(str).is_unique

    raw_rows = file_manifest[
        file_manifest["artifact_path"].astype(str).str.endswith("LocationData_Raw.csv")
    ].copy()
    expected_ids = {
        f"build_file/{config.run_id}/inputs/{station_id}/LocationData_Raw.csv"
        for station_id in station_ids
    }
    assert set(raw_rows["artifact_id"].astype(str)) == expected_ids


def test_domain_usability_marks_text_first_remarks_domain_rows_as_usable(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "inputs"
    station_id = "01234567890"
    _write_raw_csv_with_remarks(input_root / station_id, station_id)

    config = _config(
        tmp_path,
        mode="test_csv_dir",
        input_format="csv",
        run_id="run_remarks_domain_usability",
        input_root=input_root,
        write_flags=_flags(cleaned=True, domain=True, quality=True, reports=False, global_summary=False),
    )
    run_cleaning_run(config)

    domain_usability = pd.read_csv(config.reports_root / "domain_usability_summary.csv")
    remarks_rows = domain_usability[domain_usability["domain"].astype(str) == "remarks"].copy()
    assert not remarks_rows.empty
    assert int(remarks_rows["usable_rows"].max()) > 0
    assert float(remarks_rows["usable_row_rate"].max()) > 0.0
    if "artifact_mode" in remarks_rows.columns:
        assert set(remarks_rows["artifact_mode"].astype(str)) == {"domain_splits"}


def test_mandatory_quality_artifacts_written_even_when_quality_profiles_disabled(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "inputs"
    station_id = "01234567890"
    _write_raw_csv(input_root / station_id, station_id)

    config = _config(
        tmp_path,
        mode="test_csv_dir",
        input_format="csv",
        run_id="run_quality_artifacts_without_profiles",
        input_root=input_root,
        write_flags=_flags(cleaned=True, quality=False, reports=False, global_summary=False),
    )
    run_cleaning_run(config)

    expected_artifacts = (
        "field_completeness",
        "sentinel_frequency",
        "quality_code_exclusions",
        "domain_usability_summary",
        "station_year_quality",
    )
    for artifact_name in expected_artifacts:
        artifact_path = config.reports_root / f"{artifact_name}.csv"
        assert artifact_path.exists()
        frame = pd.read_csv(artifact_path)
        assert list(frame.columns)


def test_runner_processes_repeated_wind_groups_without_duplicate_cleaned_columns(tmp_path: Path) -> None:
    input_root = tmp_path / "inputs"
    station_id = "01234567890"
    _write_raw_csv_with_repeated_wind_fields(input_root / station_id, station_id)

    config = _config(
        tmp_path,
        mode="test_csv_dir",
        input_format="csv",
        run_id="run_od_flags",
        input_root=input_root,
        write_flags=_flags(cleaned=True, quality=True),
    )
    result = run_cleaning_run(config)

    assert result["failed"] == 0
    assert result["processed"] == 1

    success_path = config.output_root / station_id / "_SUCCESS.json"
    cleaned_path = config.output_root / station_id / "LocationData_Cleaned.csv"
    profile_path = config.quality_profile_root / f"station_{station_id}.json"

    assert success_path.exists()
    assert cleaned_path.exists()
    assert profile_path.exists()

    cleaned = pd.read_csv(cleaned_path, low_memory=False)
    assert cleaned.columns.is_unique
    assert "qc_calm_direction_detected_OD1" in cleaned.columns
    assert "qc_calm_direction_detected_OD2" in cleaned.columns
    assert "qc_calm_speed_detected_OE1" in cleaned.columns
    assert "qc_calm_speed_detected_OE2" in cleaned.columns
    assert str(cleaned.loc[0, "qc_calm_direction_detected_OD1"]).lower() == "true"
    assert str(cleaned.loc[0, "qc_calm_direction_detected_OD2"]).lower() == "true"
    assert str(cleaned.loc[0, "qc_calm_speed_detected_OE1"]).lower() == "true"
    assert str(cleaned.loc[0, "qc_calm_speed_detected_OE2"]).lower() == "true"


def test_output_root_cannot_be_inside_input_root(tmp_path: Path) -> None:
    input_root = tmp_path / "inputs"
    station_id = "01234567890"
    _write_raw_csv(input_root / station_id, station_id)

    config = _config(
        tmp_path,
        mode="test_csv_dir",
        input_format="csv",
        run_id="run_bad_paths",
        input_root=input_root,
        output_root=input_root / "cleaned",
        reports_root=tmp_path / "reports",
        quality_root=tmp_path / "quality",
        manifest_root=tmp_path / "manifests",
        write_flags=_flags(cleaned=True, quality=True),
    )

    with pytest.raises(ValueError, match="path hygiene"):
        run_cleaning_run(config)


def test_batch_mode_does_not_write_into_input_tree(tmp_path: Path) -> None:
    input_root = tmp_path / "parquet_inputs"
    station_id = "01234567890"
    _write_raw_parquet(input_root / station_id, station_id)

    config = _config(
        tmp_path,
        mode="batch_parquet_dir",
        input_format="parquet",
        run_id="run_batch_io",
        input_root=input_root,
        write_flags=_flags(cleaned=True, quality=True, global_summary=True),
    )
    run_cleaning_run(config)

    station_files = sorted(path.name for path in (input_root / station_id).iterdir())
    assert station_files == ["LocationData_Raw.parquet"]


def test_parquet_write_handles_mixed_object_columns(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    input_root = tmp_path / "parquet_inputs"
    station_id = "01234567890"
    _write_raw_parquet(input_root / station_id, station_id)

    def fake_clean_canonical_dataset(raw: pd.DataFrame) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "station_id": [station_id, station_id],
                "wind_type_code": ["N", 1.0],
                "qc_note": [None, "ok"],
            }
        )

    monkeypatch.setattr(cleaning_runner, "_clean_canonical_dataset", fake_clean_canonical_dataset)

    config = _config(
        tmp_path,
        mode="batch_parquet_dir",
        input_format="parquet",
        run_id="run_parquet_mixed_object",
        input_root=input_root,
        write_flags=_flags(cleaned=True, quality=False, domain=False, reports=False, global_summary=False),
    )
    result = run_cleaning_run(config)

    assert result["failed"] == 0
    cleaned_path = config.output_root / station_id / "LocationData_Cleaned.parquet"
    assert cleaned_path.exists()

    cleaned = pd.read_parquet(cleaned_path)
    assert cleaned["wind_type_code"].tolist() == ["N", "1.0"]


def test_parquet_mode_writes_domain_split_parquet_files(tmp_path: Path) -> None:
    input_root = tmp_path / "parquet_inputs"
    station_id = "01234567890"
    _write_raw_parquet(input_root / station_id, station_id)

    config = _config(
        tmp_path,
        mode="test_parquet_dir",
        input_format="parquet",
        run_id="run_parquet_domain_splits",
        input_root=input_root,
        write_flags=_flags(cleaned=True, quality=True, domain=True, reports=False, global_summary=False),
    )
    result = run_cleaning_run(config)

    assert result["failed"] == 0
    domain_manifest_path = config.output_root.parent / "domains" / station_id / "station_split_manifest.csv"
    assert domain_manifest_path.exists()

    domain_manifest = pd.read_csv(domain_manifest_path)
    assert not domain_manifest.empty
    assert set(domain_manifest["domain"].astype(str)).issubset(set(domain_names()))
    files = domain_manifest["file"].astype(str).tolist()
    assert all(path.endswith(".parquet") for path in files)
    for path in files:
        assert Path(path).exists()


def test_input_size_bytes_is_optional_best_effort(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    input_root = tmp_path / "inputs"
    station_id = "01234567890"
    raw_path = _write_raw_csv(input_root / station_id, station_id)

    original_stat = Path.stat

    def patched_stat(self: Path, *args: object, **kwargs: object) -> object:
        if self == raw_path and not args and not kwargs:
            raise OSError("simulated stat failure")
        return original_stat(self, *args, **kwargs)

    monkeypatch.setattr(cleaning_runner.Path, "stat", patched_stat)

    config = _config(
        tmp_path,
        mode="test_csv_dir",
        input_format="csv",
        run_id="run_optional_size",
        input_root=input_root,
        write_flags=_flags(cleaned=False, quality=False),
    )
    run_cleaning_run(config)

    manifest = pd.read_csv(config.manifest_root / "run_manifest.csv", dtype=str)
    assert manifest["station_id"].astype(str).tolist() == [station_id]
    assert pd.isna(manifest.loc[0, "input_size_bytes"]) or manifest.loc[0, "input_size_bytes"] == ""


def test_station_reports_write_domain_quality_reports_without_aggregation(tmp_path: Path) -> None:
    input_root = tmp_path / "inputs"
    station_id = "01234567890"
    _write_raw_csv(input_root / station_id, station_id)

    config = _config(
        tmp_path,
        mode="test_csv_dir",
        input_format="csv",
        run_id="run_station_reports_domain_quality",
        input_root=input_root,
        write_flags=_flags(
            cleaned=False,
            domain=False,
            quality=False,
            reports=True,
            global_summary=False,
        ),
    )
    result = run_cleaning_run(config)

    assert result["failed"] == 0
    reports_dir = config.reports_root / station_id
    assert (reports_dir / "LocationData_QualityReport.json").exists()
    assert (reports_dir / "LocationData_QualityReport.md").exists()
    assert (reports_dir / "LocationData_QualitySummary.csv").exists()

    assert not (reports_dir / "LocationData_AggregationReport.json").exists()
    assert not (reports_dir / "LocationData_AggregationReport.md").exists()

    domain_quality_dir = reports_dir / "domain_quality"
    for domain_name in domain_quality_report_names():
        assert (domain_quality_dir / f"LocationData_DomainQuality_{domain_name}.json").exists()
        assert (domain_quality_dir / f"LocationData_DomainQuality_{domain_name}.md").exists()

    success_payload = json.loads(
        (config.output_root / station_id / "_SUCCESS.json").read_text(encoding="utf-8")
    )
    expected_outputs = success_payload.get("expected_outputs", [])
    assert all("LocationData_AggregationReport" not in path for path in expected_outputs)
    assert any("LocationData_DomainQuality_temperature.json" in path for path in expected_outputs)


def test_repeated_force_runs_keep_canonical_domain_and_quality_artifact_checksums_stable(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "inputs"
    station_id = "01234567890"
    _write_raw_csv(input_root / station_id, station_id)

    config = _config(
        tmp_path,
        mode="test_csv_dir",
        input_format="csv",
        run_id="run_deterministic_artifacts",
        input_root=input_root,
        write_flags=_flags(cleaned=True, domain=True, quality=True, reports=False, global_summary=False),
    )
    run_cleaning_run(config)

    canonical_path = config.output_root / station_id / "LocationData_Cleaned.csv"
    quality_path = config.reports_root / "field_completeness.csv"
    domain_manifest_path = config.output_root.parent / "domains" / station_id / "station_split_manifest.csv"
    domain_manifest = pd.read_csv(domain_manifest_path)
    domain_path = Path(str(domain_manifest.loc[0, "file"]))

    first_hashes = {
        "canonical": _sha256(canonical_path),
        "domain": _sha256(domain_path),
        "quality": _sha256(quality_path),
    }

    forced = _config(
        tmp_path,
        mode="test_csv_dir",
        input_format="csv",
        run_id="run_deterministic_artifacts",
        input_root=input_root,
        force=True,
        write_flags=_flags(cleaned=True, domain=True, quality=True, reports=False, global_summary=False),
    )
    run_cleaning_run(forced)

    second_hashes = {
        "canonical": _sha256(canonical_path),
        "domain": _sha256(domain_path),
        "quality": _sha256(quality_path),
    }
    assert second_hashes == first_hashes


def test_run_recovery_with_same_run_id_is_idempotent_after_interruption(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    input_root = tmp_path / "inputs"
    station_id = "01234567890"
    _write_raw_csv(input_root / station_id, station_id)

    config = _config(
        tmp_path,
        mode="test_csv_dir",
        input_format="csv",
        run_id="run_recovery_idempotent",
        input_root=input_root,
        write_flags=_flags(cleaned=True, domain=True, quality=True, reports=False, global_summary=False),
    )

    original_clean = cleaning_runner._clean_canonical_dataset
    state = {"failed_once": False}

    def flaky_clean(raw: pd.DataFrame) -> pd.DataFrame:
        if not state["failed_once"]:
            state["failed_once"] = True
            raise RuntimeError("simulated interruption")
        return original_clean(raw)

    monkeypatch.setattr(cleaning_runner, "_clean_canonical_dataset", flaky_clean)
    first = run_cleaning_run(config)
    assert first["failed"] == 1

    status_after_failure = pd.read_csv(config.manifest_root / "run_status.csv", dtype=str)
    assert status_after_failure["status"].astype(str).tolist() == ["failed"]
    assert not (config.output_root / station_id / "_SUCCESS.json").exists()

    monkeypatch.setattr(cleaning_runner, "_clean_canonical_dataset", original_clean)
    second = run_cleaning_run(config)
    assert second["failed"] == 0
    assert second["processed"] == 1

    status_after_recovery = pd.read_csv(config.manifest_root / "run_status.csv", dtype=str)
    assert status_after_recovery["status"].astype(str).tolist() == ["completed"]

    run_manifest = pd.read_csv(config.manifest_root / "run_manifest.csv", dtype=str)
    assert len(run_manifest) == 1

    release_manifest = pd.read_csv(config.manifest_root / "release_manifest.csv", dtype=str)
    assert release_manifest["artifact_id"].is_unique
    file_manifest = pd.read_csv(config.manifest_root / "file_manifest.csv", dtype=str)
    assert file_manifest["artifact_id"].is_unique
