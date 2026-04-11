from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import re
import sys

import pandas as pd
import pytest

import noaa_spec.internal.cleaning_runner as cleaning_runner
from noaa_spec.internal.cleaning_runner import (
    CleaningRunConfig,
    RunWriteFlags,
    _discover_stations,
    default_roots_for_mode,
    run_cleaning_run,
)
from noaa_spec.domains.registry import domain_names
from noaa_spec.internal.research_reports import domain_quality_report_names


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


def _sample_chunking_raw_df(station_id: str, rows: int = 7) -> pd.DataFrame:
    data = {
        "STATION": [station_id] * rows,
        "DATE": [f"2020-01-01T{hour:02d}:00:00" for hour in range(rows)],
        "TIME": [f"{hour:02d}00" for hour in range(rows)],
        "TMP": [f"{10 + hour:04d},1" for hour in range(rows)],
        "REM": [f"remark-{hour % 3}" for hour in range(rows)],
    }
    return pd.DataFrame(data)


def _write_chunking_raw_parquet(station_dir: Path, station_id: str, rows: int = 7) -> Path:
    station_dir.mkdir(parents=True, exist_ok=True)
    raw_path = station_dir / "LocationData_Raw.parquet"
    _sample_chunking_raw_df(station_id, rows=rows).to_parquet(raw_path, index=False)
    return raw_path


def _sample_chunking_schema_drift_raw_df(station_id: str) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "STATION": [station_id] * 4,
            "DATE": [
                "2020-01-01T00:00:00",
                "2020-01-01T01:00:00",
                "2020-01-01T02:00:00",
                "2020-01-01T03:00:00",
            ],
            "TIME": ["0000", "0100", "0200", "0300"],
            "TMP": ["", "", "0010,1", "0011,1"],
            "AA1": ["", "", "01,0000,1,1", "01,0001,1,1"],
            "REM": ["plain remark", "plain remark", "MET1234 late", "MET5678 late"],
        }
    )


def _write_chunking_schema_drift_raw_parquet(station_dir: Path, station_id: str) -> Path:
    station_dir.mkdir(parents=True, exist_ok=True)
    raw_path = station_dir / "LocationData_Raw.parquet"
    _sample_chunking_schema_drift_raw_df(station_id).to_parquet(raw_path, index=False)
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
    max_station_retries: int = 1,
    station_timeout_seconds: int | None = None,
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
        max_station_retries=max_station_retries,
        station_timeout_seconds=station_timeout_seconds,
        write_flags=write_flags or _flags(),
    )


def _sha256(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _bundle_checksum(path: Path) -> str:
    return cleaning_runner._checksum_for_output_bundle([path])


def _manifest_artifact_path(config: CleaningRunConfig, artifact_path: str) -> Path:
    return cleaning_runner._resolve_manifest_artifact_path(
        artifact_path,
        build_root=config.manifest_root.parent,
    )


def _portable_artifact_path(config: CleaningRunConfig, path: Path) -> str:
    return cleaning_runner._portable_artifact_path(config, path)


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
                "usable_row_rate": [0.30],
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
    assert "descriptive_notes" in summary
    assert "observed_metric_distributions" in summary
    assert summary["exclusion_rate_summaries"]["max_observed_exclusion_rate"] == pytest.approx(0.80)
    assert summary["domain_usability_summaries"]["lowest_domain_usable_row_rates"][0]["domain"] == "core_meteorology"
    assert summary["sentinel_impact_summaries"]["top_sentinel_stations"][0]["station_id"] == "01234567890"
    assert summary["impact_summaries"]["station_year_low_usable_rows"][0]["year"] == 2020

    forbidden_keys = {
        "advisory_only",
        "threshold_policy",
        "threshold_evaluations",
        "summary_scores",
        "quality_score",
        "quality_score_components",
        "quality_score_weights",
        "quality_code_exclusion_rate_threshold_ok",
        "domain_usability_thresholds_ok",
        "domain_usability_thresholds",
        "domain_usability_threshold_violations",
        "max_quality_code_exclusion_rate_allowed",
    }

    def _assert_forbidden_keys_absent(value: object) -> None:
        if isinstance(value, dict):
            assert forbidden_keys.isdisjoint(set(value.keys()))
            for nested in value.values():
                _assert_forbidden_keys_absent(nested)
        elif isinstance(value, list):
            for nested in value:
                _assert_forbidden_keys_absent(nested)

    _assert_forbidden_keys_absent(summary)


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


def test_station_discovery_accepts_alphanumeric_11_character_station_ids(tmp_path: Path) -> None:
    input_root = tmp_path / "inputs"
    _write_raw_csv(input_root / "A0000453929", "A0000453929")

    config = _config(
        tmp_path,
        mode="test_csv_dir",
        input_format="csv",
        run_id="run_alphanumeric_discovery",
        input_root=input_root,
        write_flags=_flags(cleaned=False, quality=False),
    )
    result = run_cleaning_run(config)

    assert result["total"] == 1
    manifest = pd.read_csv(config.manifest_root / "run_manifest.csv", dtype=str)
    assert manifest["station_id"].astype(str).tolist() == ["A0000453929"]


def test_parse_station_filters_accepts_alphanumeric_station_ids() -> None:
    assert cleaning_runner.parse_station_filters(["A0000453929,01234567890"]) == (
        "01234567890",
        "A0000453929",
    )


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
    }.issubset(domain_usability.columns)
    assert set(domain_usability["artifact_mode"].astype(str)) == {"fallback_no_domain_splits"}

    station_year_quality = pd.read_csv(config.reports_root / "station_year_quality.csv")
    assert {"qc_attrition_rows", "usable_row_rate"}.issubset(station_year_quality.columns)

    summary_md = config.reports_root / "quality_reports_summary.md"
    assert summary_md.exists()
    summary_text = summary_md.read_text(encoding="utf-8")
    assert "Quality Reports Summary" in summary_text
    assert "Highest Quality-Code Exclusion Rates" in summary_text
    assert "Highest Sentinel Event Rates" in summary_text
    assert "advisory_only" not in summary_text


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
        "build_readme",
        "data_dictionary",
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


def test_checksum_registered_artifact_paths_cannot_be_rewritten(tmp_path: Path) -> None:
    cleaning_runner._reset_artifact_checksum_registry()
    path = tmp_path / "artifact.json"
    path.write_text('{"a":1}\n', encoding="utf-8")
    cleaning_runner._ARTIFACT_CHECKSUM_REGISTRY.register_existing_file(
        path,
        source="test_registration",
    )

    with pytest.raises(RuntimeError, match="Attempted to rewrite finalized artifact"):
        cleaning_runner._write_json(path, {"a": 2})

    cleaning_runner._reset_artifact_checksum_registry()


def test_release_and_file_manifest_agree_on_shared_artifact_checksums(tmp_path: Path) -> None:
    input_root = tmp_path / "inputs"
    station_id = "01234567890"
    _write_raw_csv(input_root / station_id, station_id)

    config = _config(
        tmp_path,
        mode="test_csv_dir",
        input_format="csv",
        run_id="run_manifest_checksum_alignment",
        input_root=input_root,
        write_flags=_flags(cleaned=True, domain=True, quality=True, reports=False, global_summary=False),
    )
    run_cleaning_run(config)

    release_manifest = pd.read_csv(config.manifest_root / "release_manifest.csv", dtype=str)
    file_manifest = pd.read_csv(config.manifest_root / "file_manifest.csv", dtype=str)

    file_lookup = {
        str(row["artifact_path"]): str(row["checksum"])
        for row in file_manifest.to_dict(orient="records")
    }
    for row in release_manifest.to_dict(orient="records"):
        artifact_path = str(row["artifact_path"])
        assert artifact_path in file_lookup
        assert str(row["checksum"]) == file_lookup[artifact_path]


def test_publication_gate_matches_final_manifest_snapshot(tmp_path: Path) -> None:
    input_root = tmp_path / "inputs"
    station_id = "01234567890"
    _write_raw_csv(input_root / station_id, station_id)

    config = _config(
        tmp_path,
        mode="test_csv_dir",
        input_format="csv",
        run_id="run_gate_final_snapshot",
        input_root=input_root,
        write_flags=_flags(cleaned=True, domain=True, quality=True, reports=False, global_summary=False),
    )
    run_cleaning_run(config)

    run_status = pd.read_csv(config.manifest_root / "run_status.csv", dtype=str)
    release_manifest = pd.read_csv(config.manifest_root / "release_manifest.csv", dtype=str)
    file_manifest = pd.read_csv(config.manifest_root / "file_manifest.csv", dtype=str)
    build_metadata_path = config.manifest_root / "build_metadata.json"
    gate_path = config.manifest_root / "publication_readiness_gate.json"
    stored_gate = json.loads(gate_path.read_text(encoding="utf-8"))

    quality_frames = cleaning_runner._build_mandatory_quality_artifact_frames(config, run_status)
    rebuilt_gate = cleaning_runner._build_publication_readiness_gate(
        config=config,
        status_df=run_status,
        quality_frames=quality_frames,
        run_manifest_path=config.manifest_root / "run_manifest.csv",
        run_status_path=config.manifest_root / "run_status.csv",
        run_config_path=config.manifest_root / "run_config.json",
        build_metadata_path=build_metadata_path,
        release_manifest=release_manifest,
        file_manifest=file_manifest,
        quality_assessment_path=config.reports_root / "quality_assessment.json",
    )

    assert stored_gate == rebuilt_gate


def test_publication_gate_is_fixed_point_across_provisional_and_final_file_manifest(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "inputs"
    station_id = "01234567890"
    _write_raw_csv(input_root / station_id, station_id)

    config = _config(
        tmp_path,
        mode="test_csv_dir",
        input_format="csv",
        run_id="run_gate_fixed_point",
        input_root=input_root,
        write_flags=_flags(cleaned=True, domain=True, quality=True, reports=False, global_summary=True),
    )
    run_cleaning_run(config)

    run_status = pd.read_csv(config.manifest_root / "run_status.csv", dtype=str)
    release_manifest = pd.read_csv(config.manifest_root / "release_manifest.csv", dtype=str)
    file_manifest = pd.read_csv(config.manifest_root / "file_manifest.csv", dtype=str)
    build_metadata_path = config.manifest_root / "build_metadata.json"
    gate_path = config.manifest_root / "publication_readiness_gate.json"
    stored_gate = json.loads(gate_path.read_text(encoding="utf-8"))
    gate_row = file_manifest[file_manifest["artifact_type"].astype(str) == "publication_readiness_gate"]

    assert len(gate_row) == 1

    quality_frames = cleaning_runner._build_mandatory_quality_artifact_frames(config, run_status)
    provisional_gate = cleaning_runner._build_publication_readiness_gate(
        config=config,
        status_df=run_status,
        quality_frames=quality_frames,
        run_manifest_path=config.manifest_root / "run_manifest.csv",
        run_status_path=config.manifest_root / "run_status.csv",
        run_config_path=config.manifest_root / "run_config.json",
        build_metadata_path=build_metadata_path,
        release_manifest=release_manifest,
        file_manifest=file_manifest[file_manifest["artifact_type"].astype(str) != "publication_readiness_gate"].copy(),
        quality_assessment_path=config.reports_root / "quality_assessment.json",
    )
    final_gate = cleaning_runner._build_publication_readiness_gate(
        config=config,
        status_df=run_status,
        quality_frames=quality_frames,
        run_manifest_path=config.manifest_root / "run_manifest.csv",
        run_status_path=config.manifest_root / "run_status.csv",
        run_config_path=config.manifest_root / "run_config.json",
        build_metadata_path=build_metadata_path,
        release_manifest=release_manifest,
        file_manifest=file_manifest,
        quality_assessment_path=config.reports_root / "quality_assessment.json",
    )

    assert provisional_gate == final_gate
    assert stored_gate == final_gate
    assert cleaning_runner._checksum_for_serialized_artifact(
        gate_path,
        cleaning_runner._json_bytes(final_gate),
    ) == str(gate_row.iloc[0]["checksum"])


def test_single_station_finalization_produces_passing_checksum_gate(tmp_path: Path) -> None:
    input_root = tmp_path / "inputs"
    station_id = "01234567890"
    _write_raw_csv(input_root / station_id, station_id)

    config = _config(
        tmp_path,
        mode="test_csv_dir",
        input_format="csv",
        run_id="run_single_station_integrity",
        input_root=input_root,
        write_flags=_flags(cleaned=True, domain=True, quality=True, reports=False, global_summary=False),
    )
    run_cleaning_run(config)

    gate = json.loads((config.manifest_root / "publication_readiness_gate.json").read_text(encoding="utf-8"))
    assert gate["passed"] is True
    assert gate["checks"]["checksum_policy_conformance"]["passed"] is True


def test_completed_run_writes_post_run_audit_report(tmp_path: Path) -> None:
    input_root = tmp_path / "inputs"
    station_id = "01234567890"
    _write_raw_csv(input_root / station_id, station_id)

    config = _config(
        tmp_path,
        mode="test_csv_dir",
        input_format="csv",
        run_id="run_post_run_audit",
        input_root=input_root,
        write_flags=_flags(cleaned=True, domain=True, quality=True, reports=False, global_summary=False),
    )
    result = run_cleaning_run(config)

    audit_path = config.manifest_root / "post_run_audit.md"
    assert result["post_run_audit"] == audit_path
    assert audit_path.exists()
    content = audit_path.read_text(encoding="utf-8")
    assert "# Post-Run Audit Report" in content
    assert "| Embedded publication gate checksum check | pass |" in content


def test_recover_completed_build_finalization_recreates_missing_terminal_artifacts(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "inputs"
    station_id = "01234567890"
    _write_raw_csv(input_root / station_id, station_id)

    config = _config(
        tmp_path,
        mode="test_csv_dir",
        input_format="csv",
        run_id="run_recover_finalization",
        input_root=input_root,
        write_flags=_flags(cleaned=True, domain=True, quality=True, reports=False, global_summary=False),
    )
    run_cleaning_run(config)

    gate_path = config.manifest_root / "publication_readiness_gate.json"
    run_state_path = config.manifest_root / "run_state.json"
    audit_path = config.manifest_root / "post_run_audit.md"

    gate_payload = json.loads(gate_path.read_text(encoding="utf-8"))
    run_state_payload = json.loads(run_state_path.read_text(encoding="utf-8"))
    audit_content = audit_path.read_text(encoding="utf-8")

    gate_path.unlink()
    run_state_path.unlink()
    audit_path.unlink()

    result = cleaning_runner.recover_completed_build_finalization(config.output_root.parent)

    assert result["publication_readiness_gate"] == gate_path
    assert result["run_state"] == run_state_path
    assert result["post_run_audit"] == audit_path
    assert json.loads(gate_path.read_text(encoding="utf-8")) == gate_payload
    recovered_run_state = json.loads(run_state_path.read_text(encoding="utf-8"))
    assert recovered_run_state["run_id"] == run_state_payload["run_id"]
    assert recovered_run_state["state"] == "completed"
    assert recovered_run_state["finalized"] is True
    assert recovered_run_state["counts"] == run_state_payload["counts"]
    assert recovered_run_state["elapsed_total_seconds"] >= 0.0
    assert "# Post-Run Audit Report" in audit_path.read_text(encoding="utf-8")
    assert "| Embedded publication gate checksum check | pass |" in audit_path.read_text(
        encoding="utf-8"
    )
    assert audit_content == audit_path.read_text(encoding="utf-8")


def test_parquet_raw_source_and_build_file_checksums_match(tmp_path: Path) -> None:
    input_root = tmp_path / "inputs"
    station_id = "01234567890"
    raw_path = _write_raw_parquet(input_root / station_id, station_id)

    config = _config(
        tmp_path,
        mode="test_parquet_dir",
        input_format="parquet",
        run_id="run_parquet_checksum_regression",
        input_root=input_root,
        write_flags=_flags(cleaned=True, domain=True, quality=True, reports=False, global_summary=False),
    )
    run_cleaning_run(config)

    release_manifest = pd.read_csv(config.manifest_root / "release_manifest.csv", dtype=str)
    file_manifest = pd.read_csv(config.manifest_root / "file_manifest.csv", dtype=str)

    raw_release = release_manifest[release_manifest["artifact_type"] == "raw_source"].iloc[0].to_dict()
    raw_build_file = file_manifest[
        file_manifest["artifact_path"] == _portable_artifact_path(config, raw_path)
    ].iloc[0].to_dict()
    assert raw_release["checksum"] == raw_build_file["checksum"] == _bundle_checksum(raw_path)

    canonical_path = config.output_root / station_id / "LocationData_Cleaned.parquet"
    canonical_release = release_manifest[release_manifest["artifact_type"] == "canonical_dataset"].iloc[0].to_dict()
    canonical_build_file = file_manifest[
        file_manifest["artifact_path"] == _portable_artifact_path(config, canonical_path)
    ].iloc[0].to_dict()
    assert canonical_release["checksum"] == canonical_build_file["checksum"] == _bundle_checksum(canonical_path)


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
) -> None:
    frame = pd.DataFrame(
        {
            "station_id": ["01234567890", "01234567890"],
            "wind_type_code": ["N", 1.0],
            "qc_note": [None, "ok"],
        }
    )

    cleaned_path = tmp_path / "LocationData_Cleaned.parquet"
    cleaning_runner._write_cleaned_station(frame, cleaned_path, "parquet")

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
        max_station_retries=0,
        write_flags=_flags(cleaned=True, domain=True, quality=True, reports=False, global_summary=False),
    )

    original_command = cleaning_runner._station_subprocess_command
    state = {"failed_once": False}

    def flaky_command(
        *,
        run_config_path: Path,
        station_id: str,
        input_path: Path,
        result_path: Path,
    ) -> list[str]:
        if not state["failed_once"]:
            state["failed_once"] = True
            return [
                sys.executable,
                "-c",
                "import sys; sys.stderr.write('simulated interruption\\n'); raise SystemExit(2)",
            ]
        return original_command(
            run_config_path=run_config_path,
            station_id=station_id,
            input_path=input_path,
            result_path=result_path,
        )

    monkeypatch.setattr(cleaning_runner, "_station_subprocess_command", flaky_command)
    first = run_cleaning_run(config)
    assert first["failed"] == 1
    assert first["finalized"] is False
    assert first["state"] == "failed"

    status_after_failure = pd.read_csv(config.manifest_root / "run_status.csv", dtype=str)
    assert status_after_failure["status"].astype(str).tolist() == ["failed"]
    assert not (config.output_root / station_id / "_SUCCESS.json").exists()
    assert not (config.manifest_root / "release_manifest.csv").exists()

    second = run_cleaning_run(config)
    assert second["failed"] == 0
    assert second["processed"] == 1
    assert second["finalized"] is True

    status_after_recovery = pd.read_csv(config.manifest_root / "run_status.csv", dtype=str)
    assert status_after_recovery["status"].astype(str).tolist() == ["completed"]

    run_manifest = pd.read_csv(config.manifest_root / "run_manifest.csv", dtype=str)
    assert len(run_manifest) == 1

    release_manifest = pd.read_csv(config.manifest_root / "release_manifest.csv", dtype=str)
    assert release_manifest["artifact_id"].is_unique
    file_manifest = pd.read_csv(config.manifest_root / "file_manifest.csv", dtype=str)
    assert file_manifest["artifact_id"].is_unique


def test_station_subprocess_crash_marks_failed_without_killing_parent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    input_root = tmp_path / "inputs"
    station_id = "01234567890"
    _write_raw_csv(input_root / station_id, station_id)

    def crashing_command(**_: object) -> list[str]:
        return [
            sys.executable,
            "-c",
            "import os, signal; os.kill(os.getpid(), signal.SIGSEGV)",
        ]

    monkeypatch.setattr(cleaning_runner, "_station_subprocess_command", crashing_command)

    config = _config(
        tmp_path,
        mode="test_csv_dir",
        input_format="csv",
        run_id="run_station_crash",
        input_root=input_root,
        max_station_retries=0,
        write_flags=_flags(cleaned=True, quality=True),
    )
    result = run_cleaning_run(config)

    assert result["failed"] == 1
    assert result["state"] == "failed"
    assert result["finalized"] is False

    run_status = pd.read_csv(config.manifest_root / "run_status.csv", dtype=str)
    row = run_status.iloc[0].to_dict()
    assert row["status"] == "failed"
    assert row["retry_count"] == "1"
    assert row["failure_stage"] == "child_process_crash"
    assert row["last_error_summary"]
    assert row["last_exit_code"] in {"-11", "139"}
    assert not (config.manifest_root / "release_manifest.csv").exists()
    run_state = json.loads((config.manifest_root / "run_state.json").read_text(encoding="utf-8"))
    assert run_state["state"] == "failed"
    assert run_state["finalized"] is False


def test_station_retry_succeeds_after_one_nonzero_exit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    input_root = tmp_path / "inputs"
    station_id = "01234567890"
    _write_raw_csv(input_root / station_id, station_id)

    original_command = cleaning_runner._station_subprocess_command
    state = {"failed_once": False}

    def flaky_command(
        *,
        run_config_path: Path,
        station_id: str,
        input_path: Path,
        result_path: Path,
    ) -> list[str]:
        if not state["failed_once"]:
            state["failed_once"] = True
            return [
                sys.executable,
                "-c",
                "import sys; sys.stderr.write('transient worker failure\\n'); raise SystemExit(3)",
            ]
        return original_command(
            run_config_path=run_config_path,
            station_id=station_id,
            input_path=input_path,
            result_path=result_path,
        )

    monkeypatch.setattr(cleaning_runner, "_station_subprocess_command", flaky_command)

    config = _config(
        tmp_path,
        mode="test_csv_dir",
        input_format="csv",
        run_id="run_station_retry",
        input_root=input_root,
        max_station_retries=1,
        write_flags=_flags(cleaned=True, domain=True, quality=True),
    )
    result = run_cleaning_run(config)

    assert result["failed"] == 0
    assert result["processed"] == 1
    assert result["finalized"] is True

    run_status = pd.read_csv(config.manifest_root / "run_status.csv", dtype=str)
    row = run_status.iloc[0].to_dict()
    assert row["status"] == "completed"
    assert row["retry_count"] == "1"
    assert row["last_exit_code"] == "0"


def test_station_not_marked_completed_without_all_expected_outputs_and_success_marker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    input_root = tmp_path / "inputs"
    station_id = "01234567890"
    _write_raw_csv(input_root / station_id, station_id)

    def incomplete_success_command(
        *,
        run_config_path: Path,
        station_id: str,
        input_path: Path,
        result_path: Path,
    ) -> list[str]:
        code = """
import json
from pathlib import Path
import pandas as pd
from noaa_spec.internal.cleaning_runner import (
    StationProcessingResult,
    _station_paths,
    _write_cleaned_station,
    _write_station_worker_result,
    cleaning_run_config_from_payload,
)

config_payload = json.loads(Path(__import__("sys").argv[1]).read_text(encoding="utf-8"))
config = cleaning_run_config_from_payload(config_payload)
station_id = __import__("sys").argv[2]
input_path = Path(__import__("sys").argv[3])
result_path = Path(__import__("sys").argv[4])
paths = _station_paths(config, station_id)
_write_cleaned_station(pd.DataFrame({"station_id": [station_id], "value": ["ok"]}), paths.cleaned_path, config.input_format)
_write_station_worker_result(
    result_path,
    StationProcessingResult(
        station_id=station_id,
        input_path=str(input_path.resolve()),
        output_path=str(paths.cleaned_path),
        station_quality_profile_path="",
        success_marker_path=str(paths.success_marker_path),
        expected_outputs=[str(paths.cleaned_path.resolve())],
        row_count_raw=1,
        row_count_cleaned=1,
        raw_columns=1,
        cleaned_columns=2,
        input_size_bytes=1,
        cleaned_size_bytes=1,
        elapsed_read_seconds=0.0,
        elapsed_clean_seconds=0.0,
        elapsed_domain_split_seconds=0.0,
        elapsed_quality_profile_seconds=0.0,
        elapsed_write_seconds=0.0,
        elapsed_total_seconds=0.0,
    ),
)
"""
        return [
            sys.executable,
            "-c",
            code,
            str(run_config_path),
            station_id,
            str(input_path),
            str(result_path),
        ]

    monkeypatch.setattr(cleaning_runner, "_station_subprocess_command", incomplete_success_command)

    config = _config(
        tmp_path,
        mode="test_csv_dir",
        input_format="csv",
        run_id="run_missing_success_marker",
        input_root=input_root,
        max_station_retries=0,
        write_flags=_flags(cleaned=True, quality=False, domain=False),
    )
    result = run_cleaning_run(config)

    assert result["failed"] == 1
    run_status = pd.read_csv(config.manifest_root / "run_status.csv", dtype=str)
    row = run_status.iloc[0].to_dict()
    assert row["status"] == "failed"
    assert row["failure_stage"] == "success_marker_validation"
    assert not (config.output_root / station_id / "_SUCCESS.json").exists()


def test_partial_limit_run_is_not_finalized_and_resume_completes_same_run_id(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "inputs"
    for station_id in ("01234567890", "01234567891"):
        _write_raw_csv(input_root / station_id, station_id)

    config = _config(
        tmp_path,
        mode="test_csv_dir",
        input_format="csv",
        run_id="run_limit_resume",
        input_root=input_root,
        limit=1,
        write_flags=_flags(cleaned=True, domain=True, quality=True),
    )

    first = run_cleaning_run(config)
    assert first["processed"] == 1
    assert first["finalized"] is False
    assert first["state"] == "interrupted"
    assert not (config.manifest_root / "release_manifest.csv").exists()

    first_status = pd.read_csv(config.manifest_root / "run_status.csv", dtype=str)
    assert set(first_status["status"].astype(str)) == {"completed", "skipped_limit"}

    second = run_cleaning_run(config)
    assert second["processed"] == 1
    assert second["finalized"] is True
    assert second["state"] == "completed"
    assert (config.manifest_root / "release_manifest.csv").exists()

    second_status = pd.read_csv(config.manifest_root / "run_status.csv", dtype=str)
    assert set(second_status["status"].astype(str)) == {"completed"}


def test_plan_station_chunks_is_deterministic() -> None:
    first = cleaning_runner._plan_station_chunks(250_001, chunk_row_count=100_000)
    second = cleaning_runner._plan_station_chunks(250_001, chunk_row_count=100_000)

    assert first == second
    assert [(plan.start_row, plan.end_row) for plan in first] == [
        (0, 100_000),
        (100_000, 200_000),
        (200_000, 250_001),
    ]


def test_union_cleaned_chunk_columns_uses_deterministic_precedence_order() -> None:
    union = cleaning_runner._union_cleaned_chunk_columns(
        [
            ("STATION", "DATE", "TMP"),
            ("STATION", "DATE", "AA1", "TMP"),
            ("STATION", "DATE", "REM", "AA1"),
        ]
    )

    assert union == ("STATION", "DATE", "REM", "AA1", "TMP")


def test_chunked_station_processing_matches_whole_file_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    input_root = tmp_path / "inputs"
    station_id = "01234567890"
    _write_chunking_raw_parquet(input_root / station_id, station_id, rows=7)

    whole_config = _config(
        tmp_path,
        mode="test_parquet_dir",
        input_format="parquet",
        run_id="run_whole_station",
        input_root=input_root,
        write_flags=_flags(cleaned=True, domain=True, quality=True, reports=False, global_summary=False),
        output_root=tmp_path / "whole" / "canonical_cleaned",
        reports_root=tmp_path / "whole" / "quality_reports",
        quality_root=tmp_path / "whole" / "quality_reports" / "station_quality",
        manifest_root=tmp_path / "whole" / "manifests",
    )
    whole_result = run_cleaning_run(whole_config)
    assert whole_result["failed"] == 0

    monkeypatch.setenv(cleaning_runner.STATION_CHUNKING_THRESHOLD_ENV, "3")
    monkeypatch.setenv(cleaning_runner.STATION_CHUNK_ROW_COUNT_ENV, "2")

    chunked_config = _config(
        tmp_path,
        mode="test_parquet_dir",
        input_format="parquet",
        run_id="run_chunked_station",
        input_root=input_root,
        write_flags=_flags(cleaned=True, domain=True, quality=True, reports=False, global_summary=False),
        output_root=tmp_path / "chunked" / "canonical_cleaned",
        reports_root=tmp_path / "chunked" / "quality_reports",
        quality_root=tmp_path / "chunked" / "quality_reports" / "station_quality",
        manifest_root=tmp_path / "chunked" / "manifests",
    )
    chunked_result = run_cleaning_run(chunked_config)
    assert chunked_result["failed"] == 0

    whole_cleaned = pd.read_parquet(whole_config.output_root / station_id / "LocationData_Cleaned.parquet")
    chunked_cleaned = pd.read_parquet(
        chunked_config.output_root / station_id / "LocationData_Cleaned.parquet"
    )
    pd.testing.assert_frame_equal(chunked_cleaned, whole_cleaned, check_dtype=False)
    assert chunked_cleaned["STATION"].astype(str).tolist() == [station_id] * 7
    assert chunked_cleaned["TMP"].astype(str).tolist() == whole_cleaned["TMP"].astype(str).tolist()

    whole_profile = json.loads(
        (whole_config.quality_profile_root / f"station_{station_id}.json").read_text(encoding="utf-8")
    )
    chunked_profile = json.loads(
        (chunked_config.quality_profile_root / f"station_{station_id}.json").read_text(encoding="utf-8")
    )
    assert chunked_profile == whole_profile


def test_chunked_station_processing_handles_schema_drift_with_whole_file_equivalence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    input_root = tmp_path / "inputs"
    station_id = "01234567890"
    _write_chunking_schema_drift_raw_parquet(input_root / station_id, station_id)

    whole_config = _config(
        tmp_path,
        mode="test_parquet_dir",
        input_format="parquet",
        run_id="run_whole_station_schema_drift",
        input_root=input_root,
        write_flags=_flags(cleaned=True, domain=True, quality=True, reports=False, global_summary=False),
        output_root=tmp_path / "whole_schema_drift" / "canonical_cleaned",
        reports_root=tmp_path / "whole_schema_drift" / "quality_reports",
        quality_root=tmp_path / "whole_schema_drift" / "quality_reports" / "station_quality",
        manifest_root=tmp_path / "whole_schema_drift" / "manifests",
    )
    whole_result = run_cleaning_run(whole_config)
    assert whole_result["failed"] == 0

    monkeypatch.setenv(cleaning_runner.STATION_CHUNKING_THRESHOLD_ENV, "2")
    monkeypatch.setenv(cleaning_runner.STATION_CHUNK_ROW_COUNT_ENV, "2")

    chunked_config = _config(
        tmp_path,
        mode="test_parquet_dir",
        input_format="parquet",
        run_id="run_chunked_station_schema_drift",
        input_root=input_root,
        write_flags=_flags(cleaned=True, domain=True, quality=True, reports=False, global_summary=False),
        output_root=tmp_path / "chunked_schema_drift" / "canonical_cleaned",
        reports_root=tmp_path / "chunked_schema_drift" / "quality_reports",
        quality_root=tmp_path / "chunked_schema_drift" / "quality_reports" / "station_quality",
        manifest_root=tmp_path / "chunked_schema_drift" / "manifests",
    )
    chunked_result = run_cleaning_run(chunked_config)
    assert chunked_result["failed"] == 0

    whole_cleaned = pd.read_parquet(whole_config.output_root / station_id / "LocationData_Cleaned.parquet")
    chunked_cleaned = pd.read_parquet(
        chunked_config.output_root / station_id / "LocationData_Cleaned.parquet"
    )
    pd.testing.assert_frame_equal(chunked_cleaned, whole_cleaned, check_dtype=False)

    assert "AA1" in chunked_cleaned.columns
    assert chunked_cleaned["AA1"].tolist() == whole_cleaned["AA1"].tolist()

    whole_profile = json.loads(
        (whole_config.quality_profile_root / f"station_{station_id}.json").read_text(encoding="utf-8")
    )
    chunked_profile = json.loads(
        (chunked_config.quality_profile_root / f"station_{station_id}.json").read_text(encoding="utf-8")
    )
    assert chunked_profile == whole_profile

    whole_domain_manifest = pd.read_csv(
        whole_config.output_root.parent / "domains" / station_id / "station_split_manifest.csv"
    )
    chunked_domain_manifest = pd.read_csv(
        chunked_config.output_root.parent / "domains" / station_id / "station_split_manifest.csv"
    )
    pd.testing.assert_frame_equal(
        chunked_domain_manifest.drop(columns=["file", "size_mb"]),
        whole_domain_manifest.drop(columns=["file", "size_mb"]),
        check_dtype=False,
    )


def test_stream_collate_parquet_ignores_chunk_specific_pandas_metadata(tmp_path: Path) -> None:
    chunk_dir = tmp_path / "chunks"
    chunk_dir.mkdir(parents=True, exist_ok=True)
    chunk_one = chunk_dir / "chunk_00000.parquet"
    chunk_two = chunk_dir / "chunk_00001.parquet"

    pd.DataFrame(
        {
            "station_id": ["01234567890", "01234567890"],
            "flag": pd.Series([True, pd.NA], dtype="boolean"),
        }
    ).to_parquet(chunk_one, index=False)
    pd.DataFrame(
        {
            "station_id": ["01234567890"],
            "flag": pd.Series([False], dtype="object"),
        }
    ).to_parquet(chunk_two, index=False)

    output_path = tmp_path / "LocationData_Cleaned.parquet"
    cleaning_runner._stream_collate_cleaned_chunks(
        chunk_paths=[chunk_one, chunk_two],
        output_path=output_path,
        input_format="parquet",
        aligned_columns=("station_id", "flag"),
        column_dtypes={"station_id": "object", "flag": "bool"},
    )

    collated = pd.read_parquet(output_path)
    assert collated["station_id"].tolist() == ["01234567890", "01234567890", "01234567890"]
    assert collated["flag"].astype("boolean").tolist() == [True, pd.NA, False]


def test_stream_collate_parquet_handles_mixed_chunk_dtypes_for_qc_reason_columns(
    tmp_path: Path,
) -> None:
    chunk_dir = tmp_path / "chunks"
    chunk_dir.mkdir(parents=True, exist_ok=True)
    chunk_one = chunk_dir / "chunk_00000.parquet"
    chunk_two = chunk_dir / "chunk_00001.parquet"

    pd.DataFrame(
        {
            "station_id": ["01234567890"],
            "MD1__part3__qc_reason": pd.Series([pd.NA], dtype="Float64"),
        }
    ).to_parquet(chunk_one, index=False)
    pd.DataFrame(
        {
            "station_id": ["01234567890"],
            "MD1__part3__qc_reason": pd.Series(["SENTINEL_MISSING"], dtype="string"),
        }
    ).to_parquet(chunk_two, index=False)

    observed_dtypes: dict[str, list[object]] = {}
    chunk_schemas: list[tuple[str, ...]] = []
    for path in (chunk_one, chunk_two):
        chunk = pd.read_parquet(path)
        chunk_schemas.append(tuple(chunk.columns))
        cleaning_runner._record_chunk_column_dtypes(observed_dtypes, chunk)

    output_path = tmp_path / "LocationData_Cleaned.parquet"
    cleaning_runner._stream_collate_cleaned_chunks(
        chunk_paths=[chunk_one, chunk_two],
        output_path=output_path,
        input_format="parquet",
        aligned_columns=("station_id", "MD1__part3__qc_reason"),
        column_dtypes=cleaning_runner._resolve_station_column_dtypes(
            chunk_schemas=chunk_schemas,
            observed_dtypes=observed_dtypes,
            ordered_columns=("station_id", "MD1__part3__qc_reason"),
        ),
    )

    collated = pd.read_parquet(output_path)
    assert collated["station_id"].tolist() == ["01234567890", "01234567890"]
    assert collated["MD1__part3__qc_reason"].astype("string").tolist() == [pd.NA, "SENTINEL_MISSING"]


def test_chunked_station_output_is_deterministic_across_repeated_runs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    input_root = tmp_path / "inputs"
    station_id = "01234567890"
    _write_chunking_raw_parquet(input_root / station_id, station_id, rows=7)

    monkeypatch.setenv(cleaning_runner.STATION_CHUNKING_THRESHOLD_ENV, "3")
    monkeypatch.setenv(cleaning_runner.STATION_CHUNK_ROW_COUNT_ENV, "2")

    checksums: list[str] = []
    for run_id in ("run_chunked_once", "run_chunked_twice"):
        build_root = tmp_path / run_id
        config = _config(
            tmp_path,
            mode="test_parquet_dir",
            input_format="parquet",
            run_id=run_id,
            input_root=input_root,
            write_flags=_flags(cleaned=True, domain=False, quality=True, reports=False, global_summary=False),
            output_root=build_root / "canonical_cleaned",
            reports_root=build_root / "quality_reports",
            quality_root=build_root / "quality_reports" / "station_quality",
            manifest_root=build_root / "manifests",
        )
        result = run_cleaning_run(config)
        assert result["failed"] == 0
        checksums.append(_sha256(config.output_root / station_id / "LocationData_Cleaned.parquet"))

    assert checksums[0] == checksums[1]


def test_runtime_chunk_artifacts_are_excluded_from_publication_manifests(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    input_root = tmp_path / "inputs"
    station_id = "01234567890"
    _write_chunking_raw_parquet(input_root / station_id, station_id, rows=7)

    monkeypatch.setenv(cleaning_runner.STATION_CHUNKING_THRESHOLD_ENV, "3")
    monkeypatch.setenv(cleaning_runner.STATION_CHUNK_ROW_COUNT_ENV, "2")

    config = _config(
        tmp_path,
        mode="test_parquet_dir",
        input_format="parquet",
        run_id="run_chunk_manifest_scope",
        input_root=input_root,
        write_flags=_flags(cleaned=True, domain=True, quality=True, reports=False, global_summary=False),
    )
    result = run_cleaning_run(config)
    assert result["failed"] == 0

    runtime_root = config.output_root.parent / ".runtime" / "station_chunks" / station_id
    assert runtime_root.exists()
    assert list(runtime_root.rglob("*.parquet"))

    release_manifest = pd.read_csv(config.manifest_root / "release_manifest.csv", dtype=str)
    file_manifest = pd.read_csv(config.manifest_root / "file_manifest.csv", dtype=str)
    assert not release_manifest["artifact_path"].astype(str).str.contains("/.runtime/").any()
    assert not file_manifest["artifact_path"].astype(str).str.contains("/.runtime/").any()


def test_oversized_station_chunked_path_completes_with_station_level_outputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    input_root = tmp_path / "inputs"
    station_id = "01234567890"
    _write_chunking_raw_parquet(input_root / station_id, station_id, rows=8)

    monkeypatch.setenv(cleaning_runner.STATION_CHUNKING_THRESHOLD_ENV, "3")
    monkeypatch.setenv(cleaning_runner.STATION_CHUNK_ROW_COUNT_ENV, "2")

    config = _config(
        tmp_path,
        mode="test_parquet_dir",
        input_format="parquet",
        run_id="run_chunked_smoke",
        input_root=input_root,
        write_flags=_flags(cleaned=True, domain=True, quality=True, reports=False, global_summary=False),
    )
    result = run_cleaning_run(config)

    assert result["failed"] == 0
    assert result["processed"] == 1
    assert result["state"] == "completed"
    assert (config.output_root / station_id / "LocationData_Cleaned.parquet").exists()
    assert (config.output_root / station_id / "_SUCCESS.json").exists()
    assert (config.output_root.parent / "domains" / station_id / "station_split_manifest.csv").exists()
    assert (config.quality_profile_root / f"station_{station_id}.json").exists()

    run_status = pd.read_csv(config.manifest_root / "run_status.csv", dtype=str)
    row = run_status.iloc[0].to_dict()
    assert row["status"] == "completed"
    assert row["row_count_raw"] == "8"
    assert row["row_count_cleaned"] == "8"
