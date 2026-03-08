"""CI-facing schema validation for release publication artifacts."""

from __future__ import annotations

import json
import hashlib
from pathlib import Path

import pandas as pd

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
        write_flags=RunWriteFlags(
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
