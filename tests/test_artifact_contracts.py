"""Tests for publication artifact contract declarations."""

from __future__ import annotations

import json
from pathlib import Path

from noaa_climate_data.contracts import (
    CANONICAL_CORE_COLUMN_TYPES,
    REQUIRED_ARTIFACT_METADATA_FIELDS,
    SHARED_JOIN_KEYS,
    QUALITY_REPORT_TYPES,
    publication_artifact_contracts,
)
from noaa_climate_data.domains.registry import domain_definitions


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_CONTRACTS_DIR = PROJECT_ROOT / "src" / "noaa_climate_data" / "contract_schemas" / "v1"


def test_publication_contract_registry_covers_all_artifact_types() -> None:
    contracts = publication_artifact_contracts()
    artifact_types = tuple(contract.artifact_type for contract in contracts)
    assert artifact_types == (
        "canonical_dataset",
        "domain_dataset",
        "quality_report",
        "release_manifest",
    )


def test_all_contracts_require_release_metadata_fields() -> None:
    for contract in publication_artifact_contracts():
        assert contract.required_metadata_fields == REQUIRED_ARTIFACT_METADATA_FIELDS
        assert contract.schema_version
        assert contract.required_columns
        assert contract.join_keys
        assert contract.null_semantics


def test_shared_join_keys_are_standardized_across_canonical_and_domain_contracts() -> None:
    contracts_by_type = {contract.artifact_type: contract for contract in publication_artifact_contracts()}
    assert contracts_by_type["canonical_dataset"].join_keys == SHARED_JOIN_KEYS
    assert contracts_by_type["domain_dataset"].join_keys == SHARED_JOIN_KEYS

    for definition in domain_definitions():
        assert definition.join_keys == SHARED_JOIN_KEYS


def test_quality_contract_declares_required_quality_report_types() -> None:
    assert QUALITY_REPORT_TYPES == (
        "field_completeness",
        "sentinel_frequency",
        "quality_code_exclusions",
        "domain_usability_summary",
        "station_year_quality",
    )


def test_externalized_contract_schemas_exist_and_align_with_runtime_contracts() -> None:
    runtime_contracts = {contract.artifact_type: contract for contract in publication_artifact_contracts()}

    expected_files = (
        "canonical_dataset.json",
        "domain_dataset.json",
        "quality_report.json",
        "release_manifest.json",
    )
    for schema_file_name in expected_files:
        schema_path = SCHEMA_CONTRACTS_DIR / schema_file_name
        assert schema_path.exists()
        payload = json.loads(schema_path.read_text(encoding="utf-8"))

        artifact_type = str(payload["artifact_type"])
        assert artifact_type in runtime_contracts
        runtime_contract = runtime_contracts[artifact_type]
        assert payload["schema_version"] == runtime_contract.schema_version
        assert tuple(payload["required_columns"]) == runtime_contract.required_columns
        assert tuple(payload["join_keys"]) == runtime_contract.join_keys
        assert tuple(payload["required_metadata_fields"]) == runtime_contract.required_metadata_fields
        assert tuple(payload["null_semantics"]) == runtime_contract.null_semantics

        if artifact_type == "canonical_dataset":
            assert payload["column_types"] == dict(CANONICAL_CORE_COLUMN_TYPES)
