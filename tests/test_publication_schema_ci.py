"""CI-facing schema validation for release publication artifacts."""

from __future__ import annotations

from datetime import datetime
import json
import hashlib
from pathlib import Path

import pandas as pd
import pytest

import noaa_climate_data.cleaning_runner as cleaning_runner
from noaa_climate_data.cleaning_runner import CleaningRunConfig, RunWriteFlags, run_cleaning_run
from noaa_climate_data.contracts import DOMAIN_DATASET_CONTRACT
from noaa_climate_data.domains.registry import domain_definitions


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = PROJECT_ROOT / "src" / "noaa_climate_data" / "contract_schemas" / "v1"


def _write_raw_csv(station_dir: Path, station_id: str) -> Path:
    station_dir.mkdir(parents=True, exist_ok=True)
    raw_path = station_dir / "LocationData_Raw.csv"
    pd.DataFrame(
        {
            "STATION": [station_id],
            "DATE": ["2020-01-01T00:00:00"],
            "TIME": ["0000"],
            "TMP": ["0010,1"],
        }
    ).to_csv(raw_path, index=False)
    return raw_path


def _schema_payload(name: str) -> dict[str, object]:
    path = SCHEMAS_DIR / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _run_fixture_build(
    tmp_path: Path,
    *,
    run_id: str,
    force: bool = False,
    write_flags: RunWriteFlags | None = None,
) -> tuple[CleaningRunConfig, str]:
    station_id = "01234567890"
    input_root = tmp_path / "inputs"
    _write_raw_csv(input_root / station_id, station_id)

    build_root = tmp_path / "release" / f"build_{run_id}"
    config = CleaningRunConfig(
        mode="test_csv_dir",
        input_root=input_root,
        input_format="csv",
        output_root=build_root / "canonical_cleaned",
        reports_root=build_root / "quality_reports",
        quality_profile_root=build_root / "quality_reports" / "station_quality",
        manifest_root=build_root / "manifests",
        run_id=run_id,
        limit=None,
        station_ids=(),
        force=force,
        manifest_first=False,
        manifest_refresh=False,
        write_flags=write_flags
        or RunWriteFlags(
            write_cleaned_station=True,
            write_domain_splits=True,
            write_station_quality_profile=True,
            write_station_reports=False,
            write_global_summary=False,
        ),
    )
    run_cleaning_run(config)
    return config, station_id


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _expected_file_manifest_paths(config: CleaningRunConfig) -> set[str]:
    run_status = pd.read_csv(config.manifest_root / "run_status.csv", dtype=str)
    completed = run_status[run_status["status"].astype(str) == "completed"].copy()
    expected: set[str] = set()

    for record in completed.to_dict(orient="records"):
        try:
            output_paths = json.loads(str(record.get("expected_outputs", "[]")))
        except json.JSONDecodeError:
            output_paths = []
        for path_text in output_paths:
            path = Path(str(path_text))
            if path.exists():
                expected.add(str(path.resolve()))
        success_marker = str(record.get("success_marker_path", "")).strip()
        if success_marker:
            marker = Path(success_marker)
            if marker.exists():
                expected.add(str(marker.resolve()))

    global_artifacts = [
        config.manifest_root / "run_manifest.csv",
        config.manifest_root / "run_status.csv",
        config.manifest_root / "run_config.json",
        config.manifest_root / "build_metadata.json",
        config.manifest_root / "release_manifest.csv",
        config.reports_root / "field_completeness.csv",
        config.reports_root / "sentinel_frequency.csv",
        config.reports_root / "quality_code_exclusions.csv",
        config.reports_root / "domain_usability_summary.csv",
        config.reports_root / "station_year_quality.csv",
        config.reports_root / "quality_reports_summary.md",
    ]
    if config.write_flags.write_global_summary:
        global_artifacts.append(config.reports_root / "global_quality_summary.json")

    for path in global_artifacts:
        if path.exists():
            expected.add(str(path.resolve()))
    return expected


def test_ci_schema_validation_for_publication_artifact_types(tmp_path: Path) -> None:
    run_id = "20260101T120000Z"
    config, station_id = _run_fixture_build(tmp_path, run_id=run_id)

    canonical_contract = _schema_payload("canonical_dataset")
    domain_contract = _schema_payload("domain_dataset")
    quality_contract = _schema_payload("quality_report")
    release_manifest_contract = _schema_payload("release_manifest")

    canonical_path = config.output_root / station_id / "LocationData_Cleaned.csv"
    canonical_df = pd.read_csv(canonical_path, low_memory=False)
    assert set(canonical_contract["required_columns"]).issubset(canonical_df.columns)

    domain_manifest_path = config.output_root.parent / "domains" / station_id / "station_split_manifest.csv"
    domain_manifest = pd.read_csv(domain_manifest_path)
    assert not domain_manifest.empty
    for artifact_path in domain_manifest["file"].astype(str):
        domain_df = pd.read_csv(artifact_path, low_memory=False)
        assert set(domain_contract["required_columns"]).issubset(domain_df.columns)

    release_manifest_path = config.manifest_root / "release_manifest.csv"
    release_manifest = pd.read_csv(release_manifest_path, dtype=str)
    assert set(release_manifest_contract["required_columns"]).issubset(release_manifest.columns)

    quality_rows = release_manifest[release_manifest["artifact_type"] == "quality_report"].copy()
    assert not quality_rows.empty
    for row in quality_rows.to_dict(orient="records"):
        assert row["schema_version"] == quality_contract["schema_version"]
        for required_field in quality_contract["required_metadata_fields"]:
            assert row.get(str(required_field), "")
        assert Path(str(row["artifact_path"])).exists()


def test_ci_detects_stale_domain_artifacts_against_registry_and_schema(tmp_path: Path) -> None:
    run_id = "20260101T120001Z"
    config, station_id = _run_fixture_build(tmp_path, run_id=run_id)

    domain_contract = _schema_payload("domain_dataset")
    registry_by_name = {definition.domain_name: definition for definition in domain_definitions()}

    domain_manifest_path = config.output_root.parent / "domains" / station_id / "station_split_manifest.csv"
    domain_manifest = pd.read_csv(domain_manifest_path)
    assert not domain_manifest.empty

    release_manifest = pd.read_csv(config.manifest_root / "release_manifest.csv", dtype=str)
    release_domain_rows = release_manifest[release_manifest["artifact_type"] == "domain_dataset"].copy()
    assert len(release_domain_rows) == len(domain_manifest)

    for record in domain_manifest.to_dict(orient="records"):
        domain_name = str(record["domain"])
        assert domain_name in registry_by_name

        definition = registry_by_name[domain_name]
        output_schema_columns = {column for column, _dtype in definition.output_schema}
        join_keys = tuple(str(value) for value in domain_contract["join_keys"])
        assert join_keys == definition.join_keys

        artifact_path = Path(str(record["file"]))
        artifact_df = pd.read_csv(artifact_path, low_memory=False)
        assert set(domain_contract["required_columns"]).issubset(artifact_df.columns)
        assert set(artifact_df.columns).issubset(output_schema_columns)

        artifact_id = f"domain_dataset/{run_id}/{station_id}/{domain_name}"
        release_row = release_domain_rows[release_domain_rows["artifact_id"] == artifact_id]
        assert not release_row.empty
        assert str(release_row.iloc[0]["schema_version"]) == DOMAIN_DATASET_CONTRACT.schema_version


def test_ci_reproducibility_smoke_for_fixture_build_signatures(tmp_path: Path) -> None:
    run_id = "20260101T120002Z"
    config, station_id = _run_fixture_build(tmp_path, run_id=run_id, force=False)

    domain_manifest_path = config.output_root.parent / "domains" / station_id / "station_split_manifest.csv"
    domain_manifest = pd.read_csv(domain_manifest_path)
    domain_artifact_paths = sorted(Path(path) for path in domain_manifest["file"].astype(str))

    first_paths = [
        config.output_root / station_id / "LocationData_Cleaned.csv",
        config.reports_root / "field_completeness.csv",
        config.reports_root / "sentinel_frequency.csv",
        config.reports_root / "quality_code_exclusions.csv",
        config.reports_root / "domain_usability_summary.csv",
        config.reports_root / "station_year_quality.csv",
        config.manifest_root / "release_manifest.csv",
        config.manifest_root / "build_metadata.json",
        *domain_artifact_paths,
    ]
    first_signatures = {str(path): _sha256(path) for path in first_paths}

    forced_config, _ = _run_fixture_build(tmp_path, run_id=run_id, force=True)
    second_paths = [Path(path_text) for path_text in first_signatures.keys()]
    second_signatures = {str(path): _sha256(path) for path in second_paths}

    assert forced_config.run_id == run_id
    assert second_signatures == first_signatures


def test_ci_reproducibility_rerun_gate_for_manifest_checksums(tmp_path: Path) -> None:
    run_id = "20260101T120008Z"
    config, _station_id = _run_fixture_build(tmp_path, run_id=run_id, force=False)

    first_release_manifest = pd.read_csv(config.manifest_root / "release_manifest.csv", dtype=str)
    first_file_manifest = pd.read_csv(config.manifest_root / "file_manifest.csv", dtype=str)

    _run_fixture_build(tmp_path, run_id=run_id, force=True)

    second_release_manifest = pd.read_csv(config.manifest_root / "release_manifest.csv", dtype=str)
    second_file_manifest = pd.read_csv(config.manifest_root / "file_manifest.csv", dtype=str)

    first_release_checksums = {
        str(row["artifact_id"]): str(row["checksum"])
        for row in first_release_manifest.to_dict(orient="records")
    }
    second_release_checksums = {
        str(row["artifact_id"]): str(row["checksum"])
        for row in second_release_manifest.to_dict(orient="records")
    }
    assert second_release_checksums == first_release_checksums

    volatile_types = {"run_status", "success_marker"}
    first_file_checksums = {
        str(row["artifact_id"]): str(row["checksum"])
        for row in first_file_manifest.to_dict(orient="records")
        if str(row["artifact_type"]) not in volatile_types
    }
    second_file_checksums = {
        str(row["artifact_id"]): str(row["checksum"])
        for row in second_file_manifest.to_dict(orient="records")
        if str(row["artifact_type"]) not in volatile_types
    }
    assert second_file_checksums == first_file_checksums


def test_ci_smoke_end_to_end_artifact_graph_generation(tmp_path: Path) -> None:
    run_id = "20260101T120003Z"
    config, _station_id = _run_fixture_build(tmp_path, run_id=run_id, force=False)

    release_manifest = pd.read_csv(config.manifest_root / "release_manifest.csv", dtype=str)
    assert not release_manifest.empty
    assert set(release_manifest["artifact_type"].astype(str)) >= {
        "raw_source",
        "canonical_dataset",
        "domain_dataset",
        "quality_report",
    }

    for artifact_path in release_manifest["artifact_path"].astype(str):
        assert Path(artifact_path).exists()

    artifact_ids = set(release_manifest["artifact_id"].astype(str))
    raw_ids = {
        str(row["artifact_id"])
        for row in release_manifest.to_dict(orient="records")
        if str(row["artifact_type"]) == "raw_source"
    }
    canonical_ids = {
        str(row["artifact_id"])
        for row in release_manifest.to_dict(orient="records")
        if str(row["artifact_type"]) == "canonical_dataset"
    }
    domain_ids = {
        str(row["artifact_id"])
        for row in release_manifest.to_dict(orient="records")
        if str(row["artifact_type"]) == "domain_dataset"
    }

    assert raw_ids
    assert canonical_ids
    assert domain_ids

    for row in release_manifest[release_manifest["artifact_type"] == "canonical_dataset"].to_dict(orient="records"):
        lineage = json.loads(str(row["input_lineage"]))
        assert any(entry in raw_ids for entry in lineage)

    for row in release_manifest[release_manifest["artifact_type"] == "domain_dataset"].to_dict(orient="records"):
        lineage = json.loads(str(row["input_lineage"]))
        assert any(entry in canonical_ids for entry in lineage)

    for row in release_manifest[release_manifest["artifact_type"] == "quality_report"].to_dict(orient="records"):
        lineage = json.loads(str(row["input_lineage"]))
        assert any(entry in canonical_ids for entry in lineage)
        assert any(entry in domain_ids for entry in lineage)
        assert all(entry in artifact_ids for entry in lineage)


@pytest.mark.parametrize(
    ("write_flags", "run_id"),
    [
        (
            RunWriteFlags(
                write_cleaned_station=True,
                write_domain_splits=True,
                write_station_quality_profile=True,
                write_station_reports=False,
                write_global_summary=False,
            ),
            "20260101T120004Z",
        ),
        (
            RunWriteFlags(
                write_cleaned_station=True,
                write_domain_splits=True,
                write_station_quality_profile=True,
                write_station_reports=True,
                write_global_summary=True,
            ),
            "20260101T120005Z",
        ),
    ],
)
def test_ci_file_manifest_completeness_matches_write_flags(
    tmp_path: Path,
    write_flags: RunWriteFlags,
    run_id: str,
) -> None:
    config, _station_id = _run_fixture_build(tmp_path, run_id=run_id, write_flags=write_flags)

    file_manifest = pd.read_csv(config.manifest_root / "file_manifest.csv", dtype=str)
    observed_paths = set(file_manifest["artifact_path"].astype(str))
    expected_paths = _expected_file_manifest_paths(config)

    missing = sorted(expected_paths - observed_paths)
    assert not missing

    release_manifest = pd.read_csv(config.manifest_root / "release_manifest.csv", dtype=str)
    assert set(release_manifest["artifact_path"].astype(str)).issubset(observed_paths)

    observed_types = set(file_manifest["artifact_type"].astype(str))
    if write_flags.write_station_reports:
        assert "station_report" in observed_types
    else:
        assert "station_report" not in observed_types
    if write_flags.write_domain_splits:
        assert "station_split_manifest" in observed_types
    else:
        assert "station_split_manifest" not in observed_types
    if write_flags.write_station_quality_profile:
        assert "station_quality_profile" in observed_types
    else:
        assert "station_quality_profile" not in observed_types


def test_ci_manifest_checksums_follow_path_plus_content_policy(tmp_path: Path) -> None:
    config, _station_id = _run_fixture_build(tmp_path, run_id="20260101T120006Z")

    for manifest_name in ("release_manifest.csv", "file_manifest.csv"):
        manifest = pd.read_csv(config.manifest_root / manifest_name, dtype=str)
        assert not manifest.empty
        for row in manifest.to_dict(orient="records"):
            artifact_path = Path(str(row["artifact_path"]))
            assert artifact_path.exists()
            expected_checksum = cleaning_runner._checksum_for_output_bundle([artifact_path])
            assert str(row["checksum"]) == expected_checksum


def test_ci_end_to_end_contract_check_prefixed_run_id_scenario(tmp_path: Path) -> None:
    run_id = "contract_check_20260308T104353-0700"
    config, station_id = _run_fixture_build(tmp_path, run_id=run_id)

    run_status = pd.read_csv(config.manifest_root / "run_status.csv", dtype=str)
    completed = run_status[run_status["status"].astype(str) == "completed"].copy()
    assert completed["station_id"].astype(str).tolist() == [station_id]

    build_metadata = json.loads((config.manifest_root / "build_metadata.json").read_text(encoding="utf-8"))
    build_timestamp = str(build_metadata["build_timestamp"])
    assert build_timestamp != run_id
    datetime.fromisoformat(build_timestamp)

    release_manifest = pd.read_csv(config.manifest_root / "release_manifest.csv", dtype=str)
    assert not release_manifest.empty
    for value in release_manifest["creation_timestamp"].astype(str):
        assert value != run_id
        datetime.fromisoformat(value)

    file_manifest = pd.read_csv(config.manifest_root / "file_manifest.csv", dtype=str)
    assert not file_manifest.empty


def test_ci_publication_readiness_gate_report(tmp_path: Path) -> None:
    run_id = "20260101T120007Z"
    config, _station_id = _run_fixture_build(tmp_path, run_id=run_id)

    gate_path = config.manifest_root / "publication_readiness_gate.json"
    assert gate_path.exists()

    payload = json.loads(gate_path.read_text(encoding="utf-8"))
    assert payload["run_id"] == run_id
    assert payload["passed"] is True
    datetime.fromisoformat(str(payload["generated_at"]))

    checks = payload["checks"]
    assert set(checks.keys()) == {
        "run_completion",
        "artifact_manifest_coverage",
        "timestamp_validity",
        "checksum_policy_conformance",
        "quality_artifact_sanity",
    }
    for check_payload in checks.values():
        assert check_payload["passed"] is True
