"""Tests for publication artifact contract declarations."""

from __future__ import annotations

from noaa_climate_data.contracts import (
    REQUIRED_ARTIFACT_METADATA_FIELDS,
    SHARED_JOIN_KEYS,
    QUALITY_REPORT_TYPES,
    publication_artifact_contracts,
)
from noaa_climate_data.domains.registry import domain_definitions


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
