"""Tests for publication domain registry contracts."""

from __future__ import annotations

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
