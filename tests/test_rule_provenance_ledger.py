"""Tests for rule provenance ledger generation helpers."""

from __future__ import annotations

from pathlib import Path

from tools.spec_coverage.generate_rule_provenance_ledger import (
    CodeRule,
    SpecRule,
    build_custom_cleaning_rules,
    compare_payload,
)


def test_compare_payload_range_equal():
    code = CodeRule(
        field_identifier="TMP",
        rule_type="range",
        rule_description="tmp bounds",
        enforcement_location="src/noaa_climate_data/cleaning.py",
        enforcement_function="_expand_parsed",
        code_reference="ref",
        behavior_on_violation="null",
        output_effect="null out of range",
        source_reference="test",
        min_value=-932.0,
        max_value=618.0,
    )
    spec = SpecRule(
        rule_id="spec-tmp-range",
        identifier="TMP",
        identifier_family="TMP",
        rule_type="range",
        min_value=-932.0,
        max_value=618.0,
        sentinels=set(),
        allowed_values=set(),
        token_width=None,
        expected_parts=None,
    )
    strictness, score, exact = compare_payload(code, spec, "range")
    assert strictness == "equal"
    assert score == 1.0
    assert exact is True


def test_compare_payload_domain_subset_is_stricter():
    code = CodeRule(
        field_identifier="SOURCE",
        rule_type="domain",
        rule_description="source subset",
        enforcement_location="src/noaa_climate_data/cleaning.py",
        enforcement_function="_validate_control_header",
        code_reference="ref",
        behavior_on_violation="null",
        output_effect="null for unknown codes",
        source_reference="test",
        allowed_values={"1", "2", "3"},
    )
    spec = SpecRule(
        rule_id="spec-source-domain",
        identifier="SOURCE",
        identifier_family="SOURCE",
        rule_type="domain",
        min_value=None,
        max_value=None,
        sentinels=set(),
        allowed_values={"1", "2", "3", "4"},
        token_width=None,
        expected_parts=None,
    )
    strictness, score, exact = compare_payload(code, spec, "domain")
    assert strictness == "stricter"
    assert 0 < score < 1
    assert exact is False


def test_custom_rules_include_expected_implementation_rules():
    cleaning_path = Path("src/noaa_climate_data/cleaning.py")
    rules = build_custom_cleaning_rules(cleaning_path)
    ids = {f"{rule.field_identifier}:{rule.rule_description}" for rule in rules}
    assert any("CIG ceiling height is clipped to 22000.0" in item for item in ids)
    assert any("rows with raw record length above 2844" in item.lower() for item in ids)
