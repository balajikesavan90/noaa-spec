"""Tests for publication domain registry contracts."""

from __future__ import annotations

from pathlib import Path

from noaa_climate_data.domains.registry import domain_definitions, domain_names


def test_domain_registry_includes_six_initial_publication_domains() -> None:
    assert domain_names() == (
        "clouds_visibility",
        "core_meteorology",
        "precipitation",
        "pressure_temperature",
        "remarks",
        "wind",
    )


def test_domain_registry_definitions_expose_required_contract_fields() -> None:
    definitions = domain_definitions()
    assert len(definitions) == 6

    for definition in definitions:
        assert definition.domain_name
        assert definition.input_fields
        assert definition.output_schema
        assert definition.join_keys
        assert definition.quality_rules

        schema_columns = {column for column, _dtype in definition.output_schema}
        assert set(definition.join_keys).issubset(schema_columns)


def test_domain_registry_contracts_remain_observation_level_and_non_aggregate() -> None:
    forbidden_aggregate_columns = {"Year", "MonthNum", "MonthName", "Day", "Hour"}

    for definition in domain_definitions():
        assert definition.join_keys == ("station_id", "DATE")
        schema_columns = {column for column, _dtype in definition.output_schema}
        assert "DATE" in schema_columns
        assert not (schema_columns & forbidden_aggregate_columns)


def test_domain_registry_doc_lists_all_domains_and_shared_join_keys() -> None:
    project_root = Path(__file__).resolve().parent.parent
    registry_doc = project_root / "docs" / "DOMAIN_DATASET_REGISTRY.md"
    text = registry_doc.read_text(encoding="utf-8")

    for domain_name in domain_names():
        assert domain_name in text
    assert "`station_id`" in text
    assert "`DATE`" in text
