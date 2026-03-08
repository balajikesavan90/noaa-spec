from __future__ import annotations

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
    write_flags: RunWriteFlags | None = None,
    output_root: Path | None = None,
    reports_root: Path | None = None,
    quality_root: Path | None = None,
    manifest_root: Path | None = None,
) -> CleaningRunConfig:
    base = tmp_path / "artifacts" / run_id
    return CleaningRunConfig(
        mode=mode,
        input_root=input_root,
        input_format=input_format,
        output_root=output_root or (base / "cleaned"),
        reports_root=reports_root or (base / "reports"),
        quality_profile_root=quality_root or (base / "quality_profiles"),
        manifest_root=manifest_root or (base / "manifests"),
        run_id=run_id,
        limit=limit,
        station_ids=station_ids,
        force=False,
        manifest_first=(mode == "batch_parquet_dir") if manifest_first is None else manifest_first,
        manifest_refresh=manifest_refresh,
        write_flags=write_flags or _flags(),
    )


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


def test_default_roots_for_mode_uses_release_build_layout() -> None:
    run_id = "20260101T120000Z"
    roots = default_roots_for_mode("batch_parquet_dir", run_id)

    assert roots["output_root"] == Path("release") / f"build_{run_id}" / "canonical_cleaned"
    assert roots["reports_root"] == Path("release") / f"build_{run_id}" / "quality_reports"
    assert roots["quality_profile_root"] == (
        Path("release") / f"build_{run_id}" / "quality_reports" / "station_quality"
    )
    assert roots["manifest_root"] == Path("release") / f"build_{run_id}" / "manifests"


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
