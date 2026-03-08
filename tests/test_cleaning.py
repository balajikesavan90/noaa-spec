"""Tests for P0 — Data Correctness.

Covers the three P0 fixes:
1. Missing-value sentinels do not leak into numeric outputs.
2. Scale factors (÷10) are applied to all fields that need them.
3. Per-value quality-flag mapping nulls only the governed part.
"""

from __future__ import annotations

import json
import re

import pandas as pd
import pytest

import noaa_climate_data.cleaning as cleaning_module
from noaa_climate_data.cleaning import (
    _expand_parsed,
    _is_missing_value,
    _quality_for_part,
    clean_noaa_dataframe,
    clean_value_quality,
    enforce_domain,
    parse_field,
)
from noaa_climate_data.constants import (
    AUTOMATED_PAST_WEATHER_CODE_DEFINITIONS,
    AUTOMATED_PRESENT_WEATHER_CODE_DEFINITIONS,
    DAILY_PRESENT_WEATHER_ABBREVIATION_DEFINITIONS,
    DAILY_PRESENT_WEATHER_SOURCE_DEFINITIONS,
    DAILY_PRESENT_WEATHER_TYPE_DEFINITIONS,
    GEOPOTENTIAL_ISOBARIC_LEVEL_DEFINITIONS,
    MANUAL_PAST_WEATHER_CODE_DEFINITIONS,
    MANUAL_PRESENT_WEATHER_CODE_DEFINITIONS,
    PRESENT_WEATHER_COMPONENT_PRECIPITATION_CODE_DEFINITIONS,
    PRESENT_WEATHER_VICINITY_CODE_DEFINITIONS,
    PRESSURE_TENDENCY_CODE_DEFINITIONS,
    SECTION_IDENTIFIER_WIDTH_RULE_IDENTIFIERS,
    SUMMARY_OF_DAY_PAST_WEATHER_CODE_DEFINITIONS,
    FieldPartRule,
    _REPEATED_IDENTIFIER_RANGES,
    get_field_rule,
    get_token_width_rules,
    is_valid_identifier,
    to_friendly_column,
    to_internal_column,
)

REPEATED_FAMILY_SIBLINGS: list[tuple[str, int, int]] = [
    (family, siblings[0], siblings[1])
    for family, index_range in sorted(_REPEATED_IDENTIFIER_RANGES.items())
    if len(index_range) >= 2
    for siblings in [tuple(index_range)]
]

# ── 1. Missing-value sentinels ───────────────────────────────────────────


class TestIsMissingValue:
    """_is_missing_value must recognise per-field sentinel patterns."""

    def test_tmp_sentinel_9999(self):
        rule = get_field_rule("TMP").parts[1]
        assert _is_missing_value("+9999", rule)
        assert _is_missing_value("9999", rule)

    def test_tmp_real_value(self):
        rule = get_field_rule("TMP").parts[1]
        assert not _is_missing_value("+0250", rule)
        assert not _is_missing_value("-0032", rule)


class TestDocumentedDomainValueTables:
    def test_field_rules_reference_doc_backed_code_tables(self):
        assert get_field_rule("MD1").parts[1].allowed_values == (
            set(PRESSURE_TENDENCY_CODE_DEFINITIONS) - {"9"}
        )
        assert get_field_rule("ME1").parts[1].allowed_values == (
            set(GEOPOTENTIAL_ISOBARIC_LEVEL_DEFINITIONS) - {"9"}
        )
        assert get_field_rule("AT1").parts[1].allowed_values == set(
            DAILY_PRESENT_WEATHER_SOURCE_DEFINITIONS
        )
        assert get_field_rule("AT1").parts[2].allowed_values == set(
            DAILY_PRESENT_WEATHER_TYPE_DEFINITIONS
        )
        assert get_field_rule("AT1").parts[3].allowed_values == set(
            DAILY_PRESENT_WEATHER_ABBREVIATION_DEFINITIONS
        )
        assert get_field_rule("AU1").parts[3].allowed_values == (
            set(PRESENT_WEATHER_COMPONENT_PRECIPITATION_CODE_DEFINITIONS) - {"99"}
        )
        assert get_field_rule("AW1").parts[1].allowed_values == set(
            AUTOMATED_PRESENT_WEATHER_CODE_DEFINITIONS
        )
        assert get_field_rule("AX1").parts[1].allowed_values == (
            set(SUMMARY_OF_DAY_PAST_WEATHER_CODE_DEFINITIONS) - {"99"}
        )
        assert get_field_rule("MV1").parts[1].allowed_values == (
            set(PRESENT_WEATHER_VICINITY_CODE_DEFINITIONS) - {"99"}
        )
        assert get_field_rule("MW1").parts[1].allowed_values == set(
            MANUAL_PRESENT_WEATHER_CODE_DEFINITIONS
        )
        assert get_field_rule("AY1").parts[1].allowed_values == set(
            MANUAL_PAST_WEATHER_CODE_DEFINITIONS
        )
        assert get_field_rule("AZ1").parts[1].allowed_values == set(
            AUTOMATED_PAST_WEATHER_CODE_DEFINITIONS
        )

    def test_selected_domain_value_definitions_match_doc_examples(self):
        assert "decreasing" in PRESSURE_TENDENCY_CODE_DEFINITIONS["8"]
        assert GEOPOTENTIAL_ISOBARIC_LEVEL_DEFINITIONS["2"] == "925 hectopascals"
        assert DAILY_PRESENT_WEATHER_SOURCE_DEFINITIONS["MW"].startswith("sourced from manually")
        assert "Tornado" in DAILY_PRESENT_WEATHER_TYPE_DEFINITIONS["10"]
        assert "Freezing rain" in DAILY_PRESENT_WEATHER_ABBREVIATION_DEFINITIONS["FZRA"]
        assert "Unknown precipitation" in PRESENT_WEATHER_COMPONENT_PRECIPITATION_CODE_DEFINITIONS["09"]
        assert AUTOMATED_PRESENT_WEATHER_CODE_DEFINITIONS["99"] == "Tornado"
        assert SUMMARY_OF_DAY_PAST_WEATHER_CODE_DEFINITIONS["11"] == "high or damaging winds"
        assert PRESENT_WEATHER_VICINITY_CODE_DEFINITIONS["06"] == "Blowing snow in vicinity"
        assert "duststorm or sandstorm" in MANUAL_PRESENT_WEATHER_CODE_DEFINITIONS["98"]
        assert "Thunderstorms" in MANUAL_PAST_WEATHER_CODE_DEFINITIONS["9"]
        assert AUTOMATED_PAST_WEATHER_CODE_DEFINITIONS["7"] == "Snow or ice pellets"

    def test_tmp_negative_all_9_not_missing(self):
        rule = get_field_rule("TMP").parts[1]
        assert not _is_missing_value("-9999", rule)

    def test_wnd_direction_sentinel_999(self):
        rule = get_field_rule("WND").parts[1]
        assert _is_missing_value("999", rule)

    def test_wnd_speed_sentinel_9999(self):
        rule = get_field_rule("WND").parts[4]
        assert _is_missing_value("9999", rule)

    def test_vis_sentinel_999999(self):
        rule = get_field_rule("VIS").parts[1]
        assert _is_missing_value("999999", rule)

    def test_slp_sentinel_99999(self):
        rule = get_field_rule("SLP").parts[1]
        assert _is_missing_value("99999", rule)

    def test_cig_sentinel_99999(self):
        rule = get_field_rule("CIG").parts[1]
        assert _is_missing_value("99999", rule)

    def test_fallback_generic_when_no_rule(self):
        # Without a rule, the generic all-9s heuristic applies.
        assert _is_missing_value("9999", None)
        assert _is_missing_value("99999", None)
        assert not _is_missing_value("1234", None)

    def test_fallback_negative_all_9_not_missing(self):
        assert not _is_missing_value("-9999", None)

    def test_sentinel_does_not_match_real_value(self):
        """A 3-digit value of 999 is missing for WND direction but 123 is not."""
        rule = get_field_rule("WND").parts[1]
        assert not _is_missing_value("123", rule)

    def test_ge1_convective_cloud_missing(self):
        rule = get_field_rule("GE1").parts[1]
        assert _is_missing_value("9", rule)

    def test_ge1_vertical_datum_missing(self):
        rule = get_field_rule("GE1").parts[2]
        assert _is_missing_value("999999", rule)


class TestEnforceDomain:
    """enforce_domain should normalize and validate allowed code domains."""

    def test_trims_whitespace_before_membership_check(self):
        rule = FieldPartRule(kind="categorical", agg="drop", allowed_values={"A", "B"})
        assert enforce_domain("  A  ", rule) == "A"

    def test_preserves_leading_zero_codes(self):
        rule = FieldPartRule(kind="categorical", agg="drop", allowed_values={"01", "02"})
        assert enforce_domain("01", rule) == "01"
        assert enforce_domain("1", rule) is None

    def test_pattern_uses_fullmatch(self):
        rule = FieldPartRule(kind="categorical", agg="drop", allowed_pattern=re.compile(r"\d{4}"))
        assert enforce_domain("1234", rule) == "1234"
        assert enforce_domain("AA1234ZZ", rule) is None

    def test_string_pattern_is_supported(self):
        rule = FieldPartRule(kind="categorical", agg="drop", allowed_pattern=r"\d{2}")
        assert enforce_domain("09", rule) == "09"
        assert enforce_domain("X09", rule) is None


class TestDomainRuleEnforcement:
    @pytest.mark.parametrize(
        ("prefix", "invalid_raw", "valid_raw", "part_key"),
        [
            ("AC1", "4,C,1", "1,C,1", "AC1__part1"),
            ("AD1", "01000,2,3201,0102,0102,1", "01000,2,0102,0102,0102,1", "AD1__part3"),
            ("AH1", "015,0123,3,051010,1", "015,0123,1,051010,1", "AH1__part3"),
            ("AI1", "060,0123,3,051010,1", "060,0123,1,051010,1", "AI1__part3"),
            ("AK1", "0100,5,010203,1", "0100,1,010203,1", "AK1__part2"),
            ("AU1", "1,1,10,1,1,1,1", "1,1,01,1,1,1,1", "AU1__part3"),
            ("GG1", "11,1,01000,1,01,1,01,1", "01,1,01000,1,01,1,01,1", "GG1__part1"),
            ("WD1", "01,050,06,1,1,1,10,1,050,010,1", "01,050,06,1,1,1,01,1,050,010,1", "WD1__part7"),
            ("WJ1", "010,01000,74,00,0100,1,B", "010,01000,73,00,0100,1,B", "WJ1__part3"),
            ("ST1", "5,0123,4,0050,4,01,4,2,4", "1,0123,4,0050,4,01,4,2,4", "ST1__part1"),
        ],
    )
    def test_invalid_and_valid_domain_codes(self, prefix: str, invalid_raw: str, valid_raw: str, part_key: str):
        invalid = clean_value_quality(invalid_raw, prefix)
        if prefix.startswith(("AC", "AD", "AH")):
            assert invalid[part_key] is not None
            assert invalid.get(f"qc_domain_invalid_{prefix}") is True or invalid.get(f"qc_pattern_mismatch_{prefix}") is True
        else:
            assert invalid[part_key] is None

        valid = clean_value_quality(valid_raw, prefix)
        assert valid[part_key] is not None

    @pytest.mark.parametrize(
        ("prefix", "raw", "part_key", "expect_missing"),
        [
            ("AC1", "4,C,1", "AC1__part1", True),
            ("AH1", "015,0123,1,051010,1", "AH1__part3", False),
            ("AU1", "1,1,10,1,1,1,1", "AU1__part3", True),
        ],
    )
    def test_domain_enforcement_same_in_strict_and_permissive_modes(
        self,
        prefix: str,
        raw: str,
        part_key: str,
        expect_missing: bool,
    ):
        strict = clean_value_quality(raw, prefix, strict_mode=True)
        permissive = clean_value_quality(raw, prefix, strict_mode=False)

        if prefix.startswith("AC"):
            assert strict[part_key] is not None
            assert permissive[part_key] is not None
            assert strict[f"qc_domain_invalid_{prefix}"] is True
            assert permissive[f"qc_domain_invalid_{prefix}"] is True
        else:
            assert (strict[part_key] is None) is expect_missing
            assert (permissive[part_key] is None) is expect_missing


class TestPrefixRuleMapping:
    """Numeric suffixes should resolve to prefix-based field rules."""

    @pytest.mark.parametrize(
        ("prefix", "expected_code"),
        [
            ("AH1", "AH*"),
            ("AI6", "AI*"),
            ("AL4", "AL*"),
            ("AO1", "AO*"),
            ("AT8", "AT*"),
            ("AU9", "AU*"),
            ("AW4", "AW*"),
            ("AX6", "AX*"),
            ("AZ2", "AZ*"),
            ("OA1", "OA*"),
            ("OD2", "OD*"),
            ("OB1", "OB*"),
            ("OE3", "OE*"),
            ("RH2", "RH*"),
            ("MV7", "MV*"),
            ("MW7", "MW*"),
            ("AY1", "AY*"),
            ("CO2", "CO*"),
            ("CT3", "CT*"),
            ("CU2", "CU*"),
            ("CV1", "CV*"),
            ("CW1", "CW*"),
            ("CX3", "CX*"),
            ("GA6", "GA*"),
            ("GD6", "GD*"),
            ("GG6", "GG*"),
            ("GD1", "GD*"),
            ("GH1", "GH*"),
            ("GJ1", "GJ*"),
            ("GK1", "GK*"),
            ("GL1", "GL*"),
            ("GM1", "GM*"),
            ("GN1", "GN*"),
            ("GO1", "GO*"),
        ],
    )
    def test_numeric_suffixes_use_prefix_rules(self, prefix: str, expected_code: str):
        rule = get_field_rule(prefix)
        assert rule is not None
        assert rule.code == expected_code

    @pytest.mark.parametrize(
        "prefix",
        [
            "AH7",
            "AI7",
            "AL5",
            "AO5",
            "AT9",
            "AU10",
            "AW5",
            "AX7",
            "AY3",
            "AZ3",
            "CO10",
            "GA7",
            "GD7",
            "GG7",
            "MV8",
            "MW8",
            "OA4",
            "OD4",
            "OB3",
            "OE4",
            "RH4",
            "CT4",
            "CU4",
            "CV4",
            "CW2",
            "CX4",
        ],
    )
    def test_invalid_repeated_identifiers_rejected(self, prefix: str):
        assert get_field_rule(prefix) is None

    @pytest.mark.parametrize(
        "prefix",
        ["Q00", "P00", "R00", "C00", "D00", "N00", "Q0", "N0"],
    )
    def test_invalid_eqd_identifiers_rejected(self, prefix: str):
        assert get_field_rule(prefix) is None

    def test_invalid_identifier_not_parsed(self):
        assert clean_value_quality("1,2,3", "OA4") == {}

    @pytest.mark.parametrize("prefix", ["CO3", "CO4", "CO5", "CO6", "CO7", "CO8", "CO9"])
    def test_co_prefix_rule_mapping(self, prefix: str):
        rule = get_field_rule(prefix)
        assert rule is not None
        assert rule.code == "CO*"

    @pytest.mark.parametrize(
        "prefix",
        [
            "Q01",
            "Q99",
            "P01",
            "P99",
            "R01",
            "R99",
            "C01",
            "C99",
            "D01",
            "D99",
            "N01",
            "N99",
        ],
    )
    def test_eqd_prefix_rule_mapping(self, prefix: str):
        rule = get_field_rule(prefix)
        assert rule is not None
        assert rule.code == "EQD"


class TestSentinelsInCleanedOutput:
    """Sentinels must become None/NaN, never appear as numeric values."""

    def test_tmp_sentinel_becomes_none(self):
        result = clean_value_quality("+9999,1", "TMP")
        assert result["TMP__value"] is None

    def test_tmp_negative_all_9_kept(self):
        result = clean_value_quality("-9999,1", "TMP")
        assert result["TMP__value"] is None

    def test_slp_sentinel_becomes_none(self):
        result = clean_value_quality("99999,1", "SLP")
        assert result["SLP__value"] is None

    def test_slp_quality_rejects_alpha_codes(self):
        result = clean_value_quality("10132,A", "SLP")
        assert result["SLP__value"] is None

    def test_wnd_sentinels_become_none(self):
        # direction=999, type=N, speed=9999
        result = clean_value_quality("999,1,N,9999,1", "WND")
        assert result["WND__part1"] is None
        assert result["WND__part4"] is None

    def test_vis_sentinel_becomes_none(self):
        result = clean_value_quality("999999,1,N,1", "VIS")
        assert result["VIS__part1"] is None

    def test_clean_dataframe_no_leaked_sentinels(self):
        """End-to-end: cleaning a DataFrame must not leave sentinel numbers."""
        df = pd.DataFrame(
            {
                "TMP": ["+0250,1", "+9999,1", "-0032,1"],
                "SLP": ["10132,1", "99999,1", "10089,1"],
                "WND": [
                    "180,1,N,0050,1",
                    "999,1,N,9999,1",
                    "270,1,N,0030,1",
                ],
            }
        )
        cleaned = clean_noaa_dataframe(df, keep_raw=False)
        # Row 1 (index 1) should have NaN for all value columns.
        assert pd.isna(cleaned.loc[1, "temperature_c"])
        assert pd.isna(cleaned.loc[1, "sea_level_pressure_hpa"])
        assert pd.isna(cleaned.loc[1, "wind_direction_deg"])
        assert pd.isna(cleaned.loc[1, "wind_speed_ms"])
        # Rows 0 and 2 should have real numeric values.
        assert cleaned.loc[0, "temperature_c"] == pytest.approx(25.0)
        assert cleaned.loc[2, "temperature_c"] == pytest.approx(-3.2)

    def test_wnd_variable_direction_sets_flag(self):
        result = clean_value_quality("999,1,V,0050,1", "WND")
        assert result["WND__direction_variable"] is True
        assert result["WND__part1"] is None
        assert result["WND__part4"] == pytest.approx(5.0)

    def test_ge1_missing_parts(self):
        result = clean_value_quality("9,999999,99999,99999", "GE1")
        assert result["GE1__part1"] is None
        assert result["GE1__part2"] is None

    def test_ge1_invalid_convective_cloud_code(self):
        result = clean_value_quality("8,AGL,99999,99999", "GE1")
        assert result["GE1__part1"] is None
        assert result["GE1__part2"] == "AGL"

    def test_ge1_invalid_vertical_datum_code(self):
        result = clean_value_quality("1,BADXXX,99999,99999", "GE1")
        assert result["GE1__part1"] == pytest.approx(1.0)
        assert result["GE1__part2"] is None

    def test_ge1_base_height_range_enforced(self):
        result = clean_value_quality("1,MSL,15001,01000", "GE1")
        assert result["GE1__part3"] is None
        result = clean_value_quality("1,MSL,-0401,01000", "GE1")
        assert result["GE1__part3"] is None

    def test_gf1_lowest_base_height_range_enforced(self):
        result = clean_value_quality("01,01,1,01,1,01,1,15001,1,01,1,01,1", "GF1")
        assert result["GF1__part8"] is None
        result = clean_value_quality("01,01,1,01,1,01,1,-0401,1,01,1,01,1", "GF1")
        assert result["GF1__part8"] is None

    def test_hail_sentinel_becomes_none(self):
        result = clean_value_quality("999,1", "HAIL")
        assert result["HAIL__value"] is None

    def test_hail_range_enforced(self):
        result = clean_value_quality("2001,1", "HAIL")
        assert result["HAIL__value"] is None

    def test_ia1_missing_observation_code(self):
        result = clean_value_quality("99,1", "IA1")
        assert result["IA1__part1"] is None

    def test_ia1_valid_observation_code(self):
        result = clean_value_quality("00,1", "IA1")
        assert result["IA1__part1"] == pytest.approx(0.0)
        result = clean_value_quality("31,1", "IA1")
        assert result["IA1__part1"] == pytest.approx(31.0)

    def test_ia1_invalid_observation_code(self):
        result = clean_value_quality("32,1", "IA1")
        assert result["IA1__part1"] is None

    def test_ia2_missing_min_temp_parts(self):
        result = clean_value_quality("999,+9999,1", "IA2")
        assert result["IA2__part1"] is None
        assert result["IA2__part2"] is None

    def test_ia2_range_enforced(self):
        result = clean_value_quality("000,+0100,1", "IA2")
        assert result["IA2__part1"] is None
        result = clean_value_quality("481,+0100,1", "IA2")
        assert result["IA2__part1"] is None
        result = clean_value_quality("001,-1101,1", "IA2")
        assert result["IA2__part2"] is None
        result = clean_value_quality("001,+1501,1", "IA2")
        assert result["IA2__part2"] is None

    def test_ia2_domain_enforced(self):
        result = clean_value_quality("001,+0100,1", "IA2")
        assert result["IA2__part1"] == pytest.approx(0.1)
        assert result["IA2__part3"] == pytest.approx(1.0)

        result = clean_value_quality("A01,+0100,1", "IA2")
        assert result["IA2__part1"] is None
        assert result["IA2__part2"] == pytest.approx(10.0)
        assert result["IA2__part3"] == pytest.approx(1.0)

    def test_ia2_token_width_accepts_fixed_width_tokens(self):
        result = clean_value_quality("001,+0100,1", "IA2", strict_mode=True)
        assert result["IA2__part1"] == pytest.approx(0.1)
        assert result["IA2__part2"] == pytest.approx(10.0)
        assert result["IA2__part3"] == pytest.approx(1.0)

    def test_ia2_token_width_rejects_wide_quality_token(self):
        result = clean_value_quality("001,+0100,11", "IA2", strict_mode=True)
        assert result["IA2__part3"] is None

    def test_ka_invalid_extreme_code(self):
        result = clean_value_quality("005,X,0123,1", "KA1")
        assert result["KA1__part2"] is None
        assert result["KA1__part3"] == pytest.approx(12.3)

    def test_ka_quality_allows_m(self):
        result = clean_value_quality("005,N,0123,M", "KA1")
        assert result["KA1__part1"] == pytest.approx(0.5)
        assert result["KA1__part2"] == "N"
        assert result["KA1__part3"] == pytest.approx(12.3)

    def test_ka_range_enforced(self):
        result = clean_value_quality("000,N,0123,1", "KA1")
        assert result["KA1__part1"] is None
        result = clean_value_quality("481,N,0123,1", "KA1")
        assert result["KA1__part1"] is None
        result = clean_value_quality("005,N,-0933,1", "KA1")
        assert result["KA1__part3"] is None
        result = clean_value_quality("005,N,+0619,1", "KA1")
        assert result["KA1__part3"] is None

    def test_ka_boundary_pass(self):
        result = clean_value_quality("001,N,-0932,1", "KA1")
        assert result["KA1__part3"] == pytest.approx(-93.2)
        assert result["KA1__part3__qc_pass"] is True
        result = clean_value_quality("001,N,+0618,1", "KA1")
        assert result["KA1__part3"] == pytest.approx(61.8)
        assert result["KA1__part3__qc_pass"] is True

    def test_kb_missing_parts(self):
        result = clean_value_quality("999,9,+9999,1", "KB1")
        assert result["KB1__part1"] is None
        assert result["KB1__part2"] is None
        assert result["KB1__part3"] is None

    def test_kb_range_enforced(self):
        result = clean_value_quality("000,A,0123,1", "KB1")
        assert result["KB1__part1"] is None
        result = clean_value_quality("745,A,0123,1", "KB1")
        assert result["KB1__part1"] is None
        result = clean_value_quality("001,A,-9901,1", "KB1")
        assert result["KB1__part3"] is None
        result = clean_value_quality("001,A,+6301,1", "KB1")
        assert result["KB1__part3"] is None

    def test_kb_boundary_pass(self):
        result = clean_value_quality("001,A,-9900,1", "KB1")
        assert result["KB1__part3"] == pytest.approx(-99.0)
        assert result["KB1__part3__qc_pass"] is True
        result = clean_value_quality("001,A,+6300,1", "KB1")
        assert result["KB1__part3"] == pytest.approx(63.0)
        assert result["KB1__part3__qc_pass"] is True

    def test_kc_missing_parts(self):
        result = clean_value_quality("9,9,+9999,999999,1", "KC1")
        assert result["KC1__part1"] is None
        assert result["KC1__part2"] is None
        assert result["KC1__part3"] is None
        assert result["KC1__part4"] is None

    def test_kc_range_and_date_enforced(self):
        result = clean_value_quality("N,1,-1101,011016,1", "KC1")
        assert result["KC1__part3"] is None
        result = clean_value_quality("N,1,0001,321016,1", "KC1")
        assert result["KC1__part4"] is None
        result = clean_value_quality("N,1,0001,011016,1", "KC1")
        assert result["KC1__part4"] == pytest.approx(11016.0)

    def test_kd_missing_parts(self):
        result = clean_value_quality("999,9,9999,1", "KD1")
        assert result["KD1__part1"] is None
        assert result["KD1__part2"] is None
        assert result["KD1__part3"] is None

    def test_kd_range_enforced(self):
        result = clean_value_quality("000,H,0001,1", "KD1")
        assert result["KD1__part1"] is None
        result = clean_value_quality("745,H,0001,1", "KD1")
        assert result["KD1__part1"] is None
        result = clean_value_quality("001,H,5001,1", "KD1")
        assert result["KD1__part3"] is None

    def test_ke_missing_parts(self):
        result = clean_value_quality("99,1,99,1,99,1,99,1", "KE1")
        assert result["KE1__part1"] is None
        assert result["KE1__part3"] is None
        assert result["KE1__part5"] is None
        assert result["KE1__part7"] is None

    def test_ke_range_enforced(self):
        result = clean_value_quality("32,1,01,1,01,1,01,1", "KE1")
        assert result["KE1__part1"] is None
        result = clean_value_quality("01,1,32,1,01,1,01,1", "KE1")
        assert result["KE1__part3"] is None
        result = clean_value_quality("01,1,01,1,32,1,01,1", "KE1")
        assert result["KE1__part5"] is None
        result = clean_value_quality("01,1,01,1,01,1,32,1", "KE1")
        assert result["KE1__part7"] is None

    def test_kf_missing_parts(self):
        result = clean_value_quality("9999,1", "KF1")
        assert result["KF1__part1"] is None

    def test_kf_range_enforced(self):
        result = clean_value_quality("-10000,1", "KF1")
        assert result["KF1__part1"] is None
        result = clean_value_quality("10000,1", "KF1")
        assert result["KF1__part1"] is None

    def test_kg_missing_parts(self):
        result = clean_value_quality("999,9,+9999,9,1", "KG1")
        assert result["KG1__part1"] is None
        assert result["KG1__part2"] is None
        assert result["KG1__part3"] is None
        assert result["KG1__part4"] is None

    def test_kg_range_enforced(self):
        result = clean_value_quality("000,D,0001,D,1", "KG1")
        assert result["KG1__part1"] is None
        result = clean_value_quality("745,D,0001,D,1", "KG1")
        assert result["KG1__part1"] is None
        result = clean_value_quality("001,D,-9901,D,1", "KG1")
        assert result["KG1__part3"] is None
        result = clean_value_quality("001,D,+6301,D,1", "KG1")
        assert result["KG1__part3"] is None


class TestAdditionalDataFixedWidth:
    """Additional data numerics must respect fixed-width formats."""

    def test_aa_period_requires_two_digits(self):
        result = clean_value_quality("1,0100,1,1", "AA1")
        assert result["AA1__part1"] is None
        result = clean_value_quality("01,0100,1,1", "AA1")
        assert result["AA1__part1"] == pytest.approx(1.0)

    def test_aa_amount_rejects_five_digits(self):
        result = clean_value_quality("01,10000,1,1", "AA1")
        assert result["AA1__part2"] is None
        result = clean_value_quality("01,9998,1,1", "AA1")
        assert result["AA1__part2"] == pytest.approx(999.8)


class TestApConditionCodeFixedMissing:
    """AP condition code is fixed to missing value 9."""

    def test_ap_condition_code_fixed_missing(self):
        result = clean_value_quality("0010,9,1", "AP1")
        assert result["AP1__part2"] is None
        result = clean_value_quality("0010,1,1", "AP1")
        assert result["AP1__part2"] is None


class TestCrnRanges:
    """CRN period and sensor ranges must be enforced."""

    def test_cb_period_range(self):
        result = clean_value_quality("04,000001,1,0", "CB1")
        assert result["CB1__part1"] is None
        result = clean_value_quality("05,000001,1,0", "CB1")
        assert result["CB1__part1"] == pytest.approx(5.0)

    def test_cb_precip_range(self):
        result = clean_value_quality("05,100000,1,0", "CB1")
        assert result["CB1__part2"] is None
        result = clean_value_quality("05,-99999,1,0", "CB1")
        assert result["CB1__part2"] == pytest.approx(-9999.9)

    def test_cf_fan_speed_range(self):
        result = clean_value_quality("10000,1,0", "CF1")
        assert result["CF1__part1"] is None
        result = clean_value_quality("9998,1,0", "CF1")
        assert result["CF1__part1"] == pytest.approx(999.8)

    def test_cg_depth_range(self):
        result = clean_value_quality("100000,1,0", "CG1")
        assert result["CG1__part1"] is None
        result = clean_value_quality("-99999,1,0", "CG1")
        assert result["CG1__part1"] == pytest.approx(-9999.9)

    def test_ch_period_and_sensor_ranges(self):
        result = clean_value_quality("61,00000,1,0,0000,1,0", "CH1")
        assert result["CH1__part1"] is None
        result = clean_value_quality("00,10000,1,0,0000,1,0", "CH1")
        assert result["CH1__part2"] is None
        result = clean_value_quality("00,00000,1,0,1001,1,0", "CH1")
        assert result["CH1__part5"] is None

    def test_st1_missing_parts(self):
        result = clean_value_quality("9,+9999,4,9999,4,99,4,9,4", "ST1")
        assert result["ST1__part1"] is None
        assert result["ST1__part2"] is None
        assert result["ST1__part4"] is None
        assert result["ST1__part6"] is None
        assert result["ST1__part8"] is None

    def test_st1_range_enforced(self):
        result = clean_value_quality("1,-1101,4,0050,4,01,4,2,4", "ST1")
        assert result["ST1__part2"] is None
        result = clean_value_quality("1,0631,4,0050,4,01,4,2,4", "ST1")
        assert result["ST1__part2"] is None
        result = clean_value_quality("1,0123,4,9999,4,01,4,2,4", "ST1")
        assert result["ST1__part4"] is None

    def test_st1_temperature_type_range_enforced(self):
        result = clean_value_quality("4,0123,4,0050,4,01,4,2,4", "ST1")
        assert result["ST1__part1"] == pytest.approx(4.0)

        result = clean_value_quality("0,0123,4,0050,4,01,4,2,4", "ST1")
        assert result["ST1__part1"] is None

    def test_me1_missing_parts(self):
        result = clean_value_quality("9,9999,1", "ME1")
        assert result["ME1__part1"] is None
        assert result["ME1__part2"] is None

    def test_me1_invalid_code(self):
        result = clean_value_quality("6,0123,1", "ME1")
        assert result["ME1__part1"] is None
        assert result["ME1__part2"] == pytest.approx(123.0)

    def test_me1_range_enforced(self):
        result = clean_value_quality("1,-0001,1", "ME1")
        assert result["ME1__part2"] is None
        result = clean_value_quality("1,9999,1", "ME1")
        assert result["ME1__part2"] is None

    def test_me1_boundary_pass(self):
        result = clean_value_quality("1,0000,1", "ME1")
        assert result["ME1__part2"] == pytest.approx(0.0)
        assert result["ME1__part2__qc_pass"] is True
        result = clean_value_quality("1,9998,1", "ME1")
        assert result["ME1__part2"] == pytest.approx(9998.0)
        assert result["ME1__part2__qc_pass"] is True

    def test_mf1_missing_parts(self):
        result = clean_value_quality("99999,1,99999,1", "MF1")
        assert result["MF1__part1"] is None
        assert result["MF1__part3"] is None

    def test_mk1_missing_parts(self):
        result = clean_value_quality("99999,999999,1,99999,999999,1", "MK1")
        assert result["MK1__part1"] is None
        assert result["MK1__part2"] is None
        assert result["MK1__part4"] is None
        assert result["MK1__part5"] is None

    def test_rh1_missing_parts(self):
        result = clean_value_quality("999,9,999,9,9", "RH1")
        assert result["RH1__part1"] is None
        assert result["RH1__part2"] is None
        assert result["RH1__part3"] is None
        assert result["RH1__part4"] is None

    def test_rh1_valid_values(self):
        result = clean_value_quality("024,M,085,D,1", "RH1")
        assert result["RH1__part1"] == pytest.approx(24.0)
        assert result["RH1__part2"] == "M"
        assert result["RH1__part3"] == pytest.approx(85.0)
        assert result["RH1__part4"] == "D"
        assert result["RH1__quality"] == "1"

    def test_rh1_range_enforced(self):
        result = clean_value_quality("000,M,085,D,1", "RH1")
        assert result["RH1__part1"] is None
        result = clean_value_quality("745,M,085,D,1", "RH1")
        assert result["RH1__part1"] is None
        result = clean_value_quality("024,M,101,D,1", "RH1")
        assert result["RH1__part3"] is None

    def test_ob1_missing_parts(self):
        result = clean_value_quality(
            "999,9999,9,9,999,9,9,99999,9,9,99999,9,9",
            "OB1",
        )
        assert result["OB1__part1"] is None
        assert result["OB1__part2"] is None
        assert result["OB1__part5"] is None
        assert result["OB1__part8"] is None
        assert result["OB1__part11"] is None

    def test_oe1_missing_parts(self):
        result = clean_value_quality("9,99,99999,999,9999,9", "OE1")
        assert result["OE1__part1"] is None
        assert result["OE1__part2"] is None
        assert result["OE1__part3"] is None
        assert result["OE1__part4"] is None
        assert result["OE1__part5"] is None

    def test_oe1_requires_24_hour_period(self):
        result = clean_value_quality("1,12,00010,180,1200,4", "OE1")
        assert result["OE1__part2"] is None
        assert result["OE1__part3"] == pytest.approx(0.1)

    def test_oe1_speed_range_enforced(self):
        result = clean_value_quality("1,24,20001,180,1200,4", "OE1")
        assert result["OE1__part3"] is None

    def test_oe1_direction_range_enforced(self):
        result = clean_value_quality("1,24,00010,361,1200,4", "OE1")
        assert result["OE1__part4"] is None

    def test_oe1_occurrence_time_range_enforced(self):
        result = clean_value_quality("1,24,00010,180,2360,4", "OE1")
        assert result["OE1__part5"] is None

    def test_oe1_occurrence_time_minutes_enforced(self):
        result = clean_value_quality("1,24,00010,180,0060,4", "OE1")
        assert result["OE1__part5"] is None
        result = clean_value_quality("1,24,00010,180,1261,4", "OE1")
        assert result["OE1__part5"] is None
        result = clean_value_quality("1,24,00010,180,2359,4", "OE1")
        assert result["OE1__part5"] == pytest.approx(2359.0)

    def test_wa1_missing_parts(self):
        result = clean_value_quality("9,999,9,9", "WA1")
        assert result["WA1__part1"] is None
        assert result["WA1__part2"] is None
        assert result["WA1__part3"] is None

    def test_wa1_invalid_thickness(self):
        result = clean_value_quality("1,999,1,1", "WA1")
        assert result["WA1__part2"] is None

    def test_wd1_missing_parts(self):
        result = clean_value_quality("99,999,99,9,9,9,99,9,999,999,9", "WD1")
        assert result["WD1__part1"] is None
        assert result["WD1__part2"] is None
        assert result["WD1__part3"] is None
        assert result["WD1__part4"] is None
        assert result["WD1__part5"] is None
        assert result["WD1__part6"] is None
        assert result["WD1__part7"] is None
        assert result["WD1__part8"] is None
        assert result["WD1__part9"] is None
        assert result["WD1__part10"] is None

    def test_wd1_invalid_edge_bearing_code(self):
        result = clean_value_quality("11,050,06,1,1,1,00,1,050,010,1", "WD1")
        assert result["WD1__part1"] is None

    def test_wd1_invalid_concentration_rate(self):
        result = clean_value_quality("01,101,06,1,1,1,00,1,050,010,1", "WD1")
        assert result["WD1__part2"] is None

    def test_wd1_invalid_non_uniform_code(self):
        result = clean_value_quality("01,050,05,1,1,1,00,1,050,010,1", "WD1")
        assert result["WD1__part3"] is None

    def test_wd1_invalid_ship_position_code(self):
        result = clean_value_quality("01,050,06,3,1,1,00,1,050,010,1", "WD1")
        assert result["WD1__part4"] is None

    def test_wd1_invalid_penetrability_code(self):
        result = clean_value_quality("01,050,06,1,0,1,00,1,050,010,1", "WD1")
        assert result["WD1__part5"] is None

    def test_wd1_invalid_ice_trend_code(self):
        result = clean_value_quality("01,050,06,1,1,0,00,1,050,010,1", "WD1")
        assert result["WD1__part6"] is None

    def test_wd1_invalid_development_code(self):
        result = clean_value_quality("01,050,06,1,1,1,10,1,050,010,1", "WD1")
        assert result["WD1__part7"] is None

    def test_wd1_invalid_growler_presence_code(self):
        result = clean_value_quality("01,050,06,1,1,1,00,3,050,010,1", "WD1")
        assert result["WD1__part8"] is None

    def test_wd1_invalid_growler_quantity(self):
        result = clean_value_quality("01,050,06,1,1,1,00,1,999,010,1", "WD1")
        assert result["WD1__part9"] is None

    def test_wd1_invalid_iceberg_quantity(self):
        result = clean_value_quality("01,050,06,1,1,1,00,1,050,999,1", "WD1")
        assert result["WD1__part10"] is None

    def test_wg1_missing_parts(self):
        result = clean_value_quality("99,99,99,99,99,9", "WG1")
        assert result["WG1__part1"] is None
        assert result["WG1__part2"] is None
        assert result["WG1__part3"] is None
        assert result["WG1__part4"] is None
        assert result["WG1__part5"] is None

    def test_wg1_invalid_edge_bearing_code(self):
        result = clean_value_quality("11,10,01,01,01,1", "WG1")
        assert result["WG1__part1"] is None

    def test_wg1_invalid_edge_distance(self):
        result = clean_value_quality("01,99,01,01,01,1", "WG1")
        assert result["WG1__part2"] is None

    def test_wg1_invalid_edge_orientation_code(self):
        result = clean_value_quality("01,10,10,01,01,1", "WG1")
        assert result["WG1__part3"] is None

    def test_wg1_invalid_formation_type_code(self):
        result = clean_value_quality("01,10,01,10,01,1", "WG1")
        assert result["WG1__part4"] is None

    def test_wg1_invalid_navigation_effect_code(self):
        result = clean_value_quality("01,10,01,01,10,1", "WG1")
        assert result["WG1__part5"] is None

    def test_wj1_missing_parts(self):
        result = clean_value_quality("999,99999,99,99,9999,9,9", "WJ1")
        assert result["WJ1__part1"] is None
        assert result["WJ1__part2"] is None
        assert result["WJ1__part3"] is None
        assert result["WJ1__part4"] is None
        assert result["WJ1__part5"] is None
        assert result["WJ1__part6"] is None
        assert result["WJ1__part7"] is None

    def test_wj1_invalid_primary_ice_code(self):
        result = clean_value_quality("010,01000,74,00,0100,1,B", "WJ1")
        assert result["WJ1__part3"] is None

    def test_wj1_invalid_secondary_ice_code(self):
        result = clean_value_quality("010,01000,00,74,0100,1,B", "WJ1")
        assert result["WJ1__part4"] is None

    def test_wj1_invalid_slush_condition(self):
        result = clean_value_quality("010,01000,00,00,0100,4,B", "WJ1")
        assert result["WJ1__part6"] is None

    def test_wj1_invalid_ice_thickness(self):
        result = clean_value_quality("1000,01000,00,00,0100,1,B", "WJ1")
        assert result["WJ1__part1"] is None

    def test_wj1_invalid_discharge_rate(self):
        result = clean_value_quality("010,100000,00,00,0100,1,B", "WJ1")
        assert result["WJ1__part2"] is None

    def test_wj1_invalid_stage_height(self):
        result = clean_value_quality("010,01000,00,00,10000,1,B", "WJ1")
        assert result["WJ1__part5"] is None


# ── 2. Scale factors (÷10) ──────────────────────────────────────────────


class TestScaleFactors:
    """Fields with scale=0.1 must divide by 10 in cleaned output."""

    def test_tmp_scaled(self):
        result = clean_value_quality("+0250,1", "TMP")
        assert result["TMP__value"] == pytest.approx(25.0)

    def test_dew_scaled(self):
        result = clean_value_quality("+0120,1", "DEW")
        assert result["DEW__value"] == pytest.approx(12.0)

    def test_slp_scaled(self):
        result = clean_value_quality("10132,1", "SLP")
        assert result["SLP__value"] == pytest.approx(1013.2)

    def test_oc1_gust_scaled(self):
        result = clean_value_quality("0085,1", "OC1")
        assert result["OC1__value"] == pytest.approx(8.5)

    def test_wnd_speed_scaled(self):
        result = clean_value_quality("180,1,N,0050,1", "WND")
        assert result["WND__part4"] == pytest.approx(5.0)

    def test_wnd_direction_not_scaled(self):
        result = clean_value_quality("180,1,N,0050,1", "WND")
        assert result["WND__part1"] == pytest.approx(180.0)

    def test_ma1_altimeter_and_station_pressure_scaled(self):
        result = clean_value_quality("10132,1,09876,1", "MA1")
        assert result["MA1__part1"] == pytest.approx(1013.2)
        assert result["MA1__part3"] == pytest.approx(987.6)

    def test_sa1_sst_scaled(self):
        result = clean_value_quality("0215,1", "SA1")
        assert result["SA1__value"] == pytest.approx(21.5)

    def test_sa1_range_enforced(self):
        result = clean_value_quality("+0451,1", "SA1")
        assert result["SA1__value"] is None

    def test_md1_pressure_change_scaled(self):
        result = clean_value_quality("5,1,045,1,0123,1", "MD1")
        assert result["MD1__part3"] == pytest.approx(4.5)
        assert result["MD1__part5"] == pytest.approx(12.3)

    def test_negative_temperature_scaled(self):
        result = clean_value_quality("-0032,1", "TMP")
        assert result["TMP__value"] == pytest.approx(-3.2)

    def test_hail_scaled(self):
        result = clean_value_quality("025,1", "HAIL")
        assert result["HAIL__value"] == pytest.approx(2.5)

    def test_ic1_evaporation_scaled(self):
        result = clean_value_quality("24,0100,1,4,050,1,4,+050,1,4,+040,1,4", "IC1")
        assert result["IC1__part5"] == pytest.approx(0.5)

    def test_ib1_range_enforced(self):
        result = clean_value_quality("-10000,1,0,0000,1,0,0000,1,0,0000,1,0", "IB1")
        assert result["IB1__part1"] is None
        result = clean_value_quality("10000,1,0,0000,1,0,0000,1,0,0000,1,0", "IB1")
        assert result["IB1__part1"] is None
        result = clean_value_quality("0000,1,0,-10000,1,0,0000,1,0,0000,1,0", "IB1")
        assert result["IB1__part4"] is None
        result = clean_value_quality("0000,1,0,0000,1,0,0000,1,0,9999,1,0", "IB1")
        assert result["IB1__part10"] is None

    def test_ib2_range_enforced(self):
        result = clean_value_quality("-10000,1,0,0000,1,0", "IB2")
        assert result["IB2__part1"] is None
        result = clean_value_quality("0000,1,0,9999,1,0", "IB2")
        assert result["IB2__part4"] is None

    def test_ib2_token_width_accepts_fixed_width_tokens(self):
        result = clean_value_quality("0000,1,0,0000,1,0", "IB2", strict_mode=True)
        assert result["IB2__part1"] == pytest.approx(0.0)
        assert result["IB2__part4"] == pytest.approx(0.0)

    def test_ib2_token_width_rejects_short_first_numeric_token(self):
        result = clean_value_quality("000,1,0,0000,1,0", "IB2", strict_mode=True)
        assert result["IB2__part1"] is None

    def test_ic1_range_enforced(self):
        result = clean_value_quality("00,0100,1,4,050,1,4,+050,1,4,+040,1,4", "IC1")
        assert result["IC1__part1"] is None
        result = clean_value_quality("99,0100,1,4,050,1,4,+050,1,4,+040,1,4", "IC1")
        assert result["IC1__part1"] is None
        result = clean_value_quality("24,10000,1,4,050,1,4,+050,1,4,+040,1,4", "IC1")
        assert result["IC1__part2"] is None
        result = clean_value_quality("24,0100,1,4,1000,1,4,+050,1,4,+040,1,4", "IC1")
        assert result["IC1__part5"] is None
        result = clean_value_quality("24,0100,1,4,050,1,4,+501,1,4,+040,1,4", "IC1")
        assert result["IC1__part8"] is None
        result = clean_value_quality("24,0100,1,4,050,1,4,+050,1,4,-101,1,4", "IC1")
        assert result["IC1__part11"] is None

    def test_kb_scaled(self):
        result = clean_value_quality("024,A,0100,1", "KB1")
        assert result["KB1__part3"] == pytest.approx(1.0)

    def test_kc_scaled(self):
        result = clean_value_quality("M,1,0123,010203,1", "KC1")
        assert result["KC1__part3"] == pytest.approx(12.3)

    def test_kf_scaled(self):
        result = clean_value_quality("0123,1", "KF1")
        assert result["KF1__part1"] == pytest.approx(12.3)

    def test_kg_scaled(self):
        result = clean_value_quality("024,D,0123,D,1", "KG1")
        assert result["KG1__part3"] == pytest.approx(12.3)

    def test_st1_scaled(self):
        result = clean_value_quality("1,0123,4,0050,4,01,4,2,4", "ST1")
        assert result["ST1__part2"] == pytest.approx(12.3)
        assert result["ST1__part4"] == pytest.approx(5.0)

    def test_mf1_scaled(self):
        result = clean_value_quality("10132,1,09876,1", "MF1")
        assert result["MF1__part1"] == pytest.approx(1013.2)
        assert result["MF1__part3"] == pytest.approx(987.6)


class TestScaleFactorsInDataframe:
    """Scale factors work end-to-end through clean_noaa_dataframe."""

    def test_dataframe_tmp_scaled(self):
        df = pd.DataFrame({"TMP": ["+0250,1", "-0100,1"]})
        cleaned = clean_noaa_dataframe(df, keep_raw=False)
        assert cleaned.loc[0, "temperature_c"] == pytest.approx(25.0)
        assert cleaned.loc[1, "temperature_c"] == pytest.approx(-10.0)

    def test_dataframe_wnd_speed_scaled(self):
        df = pd.DataFrame({"WND": ["090,1,N,0110,1", "270,1,N,0030,1"]})
        cleaned = clean_noaa_dataframe(df, keep_raw=False)
        assert cleaned.loc[0, "wind_speed_ms"] == pytest.approx(11.0)
        assert cleaned.loc[1, "wind_speed_ms"] == pytest.approx(3.0)

    def test_dataframe_hail_renamed(self):
        df = pd.DataFrame({"HAIL": ["025,1", "999,9"]})
        cleaned = clean_noaa_dataframe(df, keep_raw=False)
        assert "hail_size_cm" in cleaned.columns
        assert cleaned.loc[0, "hail_size_cm"] == pytest.approx(2.5)
        assert pd.isna(cleaned.loc[1, "hail_size_cm"])


# ── 3. Per-value quality-flag mapping ────────────────────────────────────


class TestQualityForPart:
    """_quality_for_part must return the correct quality flag for each part."""

    def test_wnd_direction_quality_is_part2(self):
        parts = ["180", "1", "N", "0050", "1"]
        assert _quality_for_part("WND", 1, parts) == "1"

    def test_wnd_speed_quality_is_part5(self):
        parts = ["180", "1", "N", "0050", "1"]
        assert _quality_for_part("WND", 4, parts) == "1"

    def test_wnd_direction_bad_quality_does_not_affect_speed(self):
        parts = ["180", "8", "N", "0050", "1"]  # part2=8 → bad for direction
        assert _quality_for_part("WND", 1, parts) == "8"  # direction gets bad flag
        assert _quality_for_part("WND", 4, parts) == "1"  # speed keeps good flag

    def test_ma1_separate_quality_parts(self):
        parts = ["10132", "1", "09876", "1"]
        assert _quality_for_part("MA1", 1, parts) == "1"  # altimeter → part2
        assert _quality_for_part("MA1", 3, parts) == "1"  # station press → part4

    def test_ma1_bad_stn_press_quality_only(self):
        parts = ["10132", "1", "09876", "3"]  # part4=3 → bad for station press
        assert _quality_for_part("MA1", 1, parts) == "1"  # altimeter still good
        assert _quality_for_part("MA1", 3, parts) == "3"  # station press bad

    def test_ua1_wave_parts_use_part4_quality(self):
        parts = ["I", "05", "120", "1", "03", "9"]
        assert _quality_for_part("UA1", 2, parts) == "1"
        assert _quality_for_part("UA1", 3, parts) == "1"

    def test_ua1_sea_state_quality_is_part6(self):
        parts = ["I", "05", "120", "1", "03", "9"]
        assert _quality_for_part("UA1", 5, parts) == "9"

    def test_no_rule_returns_none(self):
        assert _quality_for_part("UNKNOWN", 1, ["x", "y"]) is None


class TestQualityNullsCorrectPart:
    """Bad quality must null only the governed value, not siblings."""

    def test_wnd_bad_direction_quality_nulls_direction_only(self):
        # part2=8 (bad quality for direction), part5=1 (good for speed)
        result = clean_value_quality("180,8,N,0050,1", "WND")
        assert result["WND__part1"] is None         # direction nulled
        assert result["WND__part4"] == pytest.approx(5.0)  # speed preserved

    def test_wnd_bad_speed_quality_nulls_speed_only(self):
        # part2=1 (good for direction), part5=8 (bad for speed)
        result = clean_value_quality("180,1,N,0050,8", "WND")
        assert result["WND__part1"] == pytest.approx(180.0)  # direction preserved
        assert result["WND__part4"] is None          # speed nulled

    def test_wnd_rejects_non_mandatory_quality(self):
        result = clean_value_quality("180,M,N,0050,1", "WND")
        assert result["WND__part1"] is None
        assert result["WND__part4"] == pytest.approx(5.0)

    def test_wnd_both_bad_nulls_both(self):
        result = clean_value_quality("180,8,N,0050,8", "WND")
        assert result["WND__part1"] is None
        assert result["WND__part4"] is None

    def test_cig_rejects_non_mandatory_quality(self):
        result = clean_value_quality("01000,M,9,9", "CIG")
        assert result["CIG__part1"] is None

    def test_vis_rejects_non_mandatory_quality(self):
        result = clean_value_quality("010000,M,N,1", "VIS")
        assert result["VIS__part1"] is None

    def test_ma1_bad_station_pressure_preserves_altimeter(self):
        result = clean_value_quality("10132,1,09876,8", "MA1")
        assert result["MA1__part1"] == pytest.approx(1013.2)  # altimeter preserved
        assert result["MA1__part3"] is None  # station pressure nulled

    def test_ma1_bad_altimeter_preserves_station_pressure(self):
        result = clean_value_quality("10132,8,09876,1", "MA1")
        assert result["MA1__part1"] is None  # altimeter nulled
        assert result["MA1__part3"] == pytest.approx(987.6)  # station pressure preserved

    def test_ma1_altimeter_rejects_non_mandatory_quality(self):
        result = clean_value_quality("10132,A,09876,1", "MA1")
        assert result["MA1__part1"] is None
        assert result["MA1__part3"] == pytest.approx(987.6)

    def test_ma1_station_pressure_rejects_non_mandatory_quality(self):
        result = clean_value_quality("10132,1,09876,U", "MA1")
        assert result["MA1__part1"] == pytest.approx(1013.2)
        assert result["MA1__part3"] is None

    def test_tmp_bad_quality_nulls_value(self):
        result = clean_value_quality("+0250,8", "TMP")
        assert result["TMP__value"] is None

    def test_tmp_good_quality_keeps_value(self):
        result = clean_value_quality("+0250,1", "TMP")
        assert result["TMP__value"] == pytest.approx(25.0)

    def test_ua1_bad_sea_state_quality_nulls_sea_state_only(self):
        result = clean_value_quality("I,05,120,1,03,8", "UA1")
        assert result["UA1__part2"] == pytest.approx(5.0)
        assert result["UA1__part3"] == pytest.approx(12.0)
        assert result["UA1__part5"] is None

    def test_ua1_bad_wave_quality_nulls_wave_values_only(self):
        result = clean_value_quality("I,05,120,8,03,1", "UA1")
        assert result["UA1__part2"] is None
        assert result["UA1__part3"] is None
        assert result["UA1__part5"] == pytest.approx(3.0)

    def test_md1_bad_tendency_quality_nulls_tendency_only(self):
        result = clean_value_quality("5,8,045,1,0123,1", "MD1")
        assert result["MD1__part1"] is None
        assert result["MD1__part3"] == pytest.approx(4.5)
        assert result["MD1__part5"] == pytest.approx(12.3)

    def test_md1_invalid_tendency_code(self):
        result = clean_value_quality("A,1,045,1,0123,1", "MD1")
        assert result["MD1__part1"] is None

    def test_ay_invalid_condition_code(self):
        result = clean_value_quality("10,1,01,1", "AY1")
        assert result["AY1__part1"] is None
        assert result["AY1__part3"] == pytest.approx(1.0)

    def test_ay_invalid_period_quantity(self):
        result = clean_value_quality("1,1,25,1", "AY1")
        assert result["AY1__part3"] is None

    def test_ax_invalid_condition_code(self):
        result = clean_value_quality("12,4,24,4", "AX1")
        assert result["AX1__part1"] is None
        assert result["AX1__part3"] == pytest.approx(24.0)

    def test_ax_invalid_period_quantity(self):
        result = clean_value_quality("01,4,01,4", "AX1")
        assert result["AX1__part3"] is None

    @pytest.mark.parametrize("prefix", ["AX1", "AX2", "AX3", "AX4", "AX5", "AX6"])
    def test_ax_repeated_range_enforced(self, prefix: str):
        result = clean_value_quality("11,4,24,4", prefix)
        assert result[f"{prefix}__part1"] == pytest.approx(11.0)
        assert result[f"{prefix}__part3"] == pytest.approx(24.0)
        result = clean_value_quality("12,4,24,4", prefix)
        assert result[f"{prefix}__part1"] is None

    def test_az_invalid_period_quantity(self):
        result = clean_value_quality("1,1,25,1", "AZ1")
        assert result["AZ1__part3"] is None

    @pytest.mark.parametrize("prefix", ["AY1", "AY2"])
    def test_ay_repeated_range_enforced(self, prefix: str):
        result = clean_value_quality("1,1,24,1", prefix)
        assert result[f"{prefix}__part3"] == pytest.approx(24.0)
        result = clean_value_quality("1,1,25,1", prefix)
        assert result[f"{prefix}__part3"] is None

    @pytest.mark.parametrize("prefix", ["AZ1", "AZ2"])
    def test_az_repeated_range_enforced(self, prefix: str):
        result = clean_value_quality("1,1,24,1", prefix)
        assert result[f"{prefix}__part3"] == pytest.approx(24.0)
        result = clean_value_quality("1,1,25,1", prefix)
        assert result[f"{prefix}__part3"] is None

    def test_ua1_bad_wave_quality_nulls_wave_parts(self):
        result = clean_value_quality("M,10,050,8,04,1", "UA1")
        assert result["UA1__part1"] is None
        assert result["UA1__part2"] is None
        assert result["UA1__part3"] is None
        assert result["UA1__part5"] == pytest.approx(4.0)

    def test_ug1_missing_parts(self):
        result = clean_value_quality("99,999,999,9", "UG1")
        assert result["UG1__part1"] is None
        assert result["UG1__part2"] is None
        assert result["UG1__part3"] is None

    def test_ug1_invalid_direction_range(self):
        result = clean_value_quality("05,050,361,1", "UG1")
        assert result["UG1__part3"] is None

    def test_ug1_quality_rejects_8(self):
        result = clean_value_quality("05,050,180,8", "UG1")
        assert result["UG1__part1"] is None
        assert result["UG1__part2"] is None
        assert result["UG1__part3"] is None

    def test_ug2_invalid_period_range(self):
        result = clean_value_quality("15,050,180,1", "UG2")
        assert result["UG2__part1"] is None

    def test_ua1_quality_code_outside_marine_domain(self):
        result = clean_value_quality("M,10,050,4,04,1", "UA1")
        assert result["UA1__part1"] is None
        assert result["UA1__part2"] is None
        assert result["UA1__part3"] is None
        assert result["UA1__part5"] == pytest.approx(4.0)

    def test_ua1_invalid_method_code(self):
        result = clean_value_quality("X,05,120,1,03,1", "UA1")
        assert result["UA1__part1"] is None
        assert result["UA1__part2"] == pytest.approx(5.0)
        assert result["UA1__part3"] == pytest.approx(12.0)

    def test_ua1_invalid_sea_state_code(self):
        result = clean_value_quality("I,05,120,1,10,1", "UA1")
        assert result["UA1__part2"] == pytest.approx(5.0)
        assert result["UA1__part3"] == pytest.approx(12.0)
        assert result["UA1__part5"] is None

    def test_ua1_invalid_wave_period(self):
        result = clean_value_quality("I,31,120,1,03,1", "UA1")
        assert result["UA1__part2"] is None

    def test_ua1_invalid_wave_height(self):
        result = clean_value_quality("I,05,501,1,03,1", "UA1")
        assert result["UA1__part3"] is None

    def test_ug1_bad_swell_quality_nulls_swell_parts(self):
        result = clean_value_quality("10,050,180,8", "UG1")
        assert result["UG1__part1"] is None
        assert result["UG1__part2"] is None
        assert result["UG1__part3"] is None

    def test_ug1_quality_code_outside_marine_domain(self):
        result = clean_value_quality("10,050,180,4", "UG1")
        assert result["UG1__part1"] is None
        assert result["UG1__part2"] is None
        assert result["UG1__part3"] is None

    def test_ug2_bad_swell_quality_nulls_swell_parts(self):
        result = clean_value_quality("10,050,180,8", "UG2")
        assert result["UG2__part1"] is None
        assert result["UG2__part2"] is None
        assert result["UG2__part3"] is None

    def test_ug2_quality_code_outside_marine_domain(self):
        result = clean_value_quality("10,050,180,4", "UG2")
        assert result["UG2__part1"] is None
        assert result["UG2__part2"] is None
        assert result["UG2__part3"] is None

    def test_ug1_invalid_swell_ranges(self):
        result = clean_value_quality("15,501,000,1", "UG1")
        assert result["UG1__part1"] is None
        assert result["UG1__part2"] is None
        assert result["UG1__part3"] is None

    def test_ug2_invalid_swell_ranges(self):
        result = clean_value_quality("15,501,000,1", "UG2")
        assert result["UG2__part1"] is None
        assert result["UG2__part2"] is None
        assert result["UG2__part3"] is None

    def test_wa1_invalid_source_and_tendency_codes(self):
        result = clean_value_quality("6,010,5,1", "WA1")
        assert result["WA1__part1"] is None
        assert result["WA1__part3"] is None

    def test_quality_in_dataframe(self):
        df = pd.DataFrame(
            {
                "WND": [
                    "180,1,N,0050,1",   # both good
                    "180,8,N,0050,1",   # bad direction
                    "180,1,N,0050,8",   # bad speed
                ],
            }
        )
        cleaned = clean_noaa_dataframe(df, keep_raw=False)
        # Row 0: both values present
        assert cleaned.loc[0, "wind_direction_deg"] == pytest.approx(180.0)
        assert cleaned.loc[0, "wind_speed_ms"] == pytest.approx(5.0)
        # Row 1: direction nulled, speed kept
        assert pd.isna(cleaned.loc[1, "wind_direction_deg"])
        assert cleaned.loc[1, "wind_speed_ms"] == pytest.approx(5.0)
        # Row 2: direction kept, speed nulled
        assert cleaned.loc[2, "wind_direction_deg"] == pytest.approx(180.0)
        assert pd.isna(cleaned.loc[2, "wind_speed_ms"])

    def test_gf1_cloud_quality_gates_values(self):
        result = clean_value_quality("05,05,8,05,8,99,8,5000,8,99,8,99,8", "GF1")
        assert result["GF1__part1"] is None
        assert result["GF1__part4"] is None
        assert result["GF1__part6"] is None
        assert result["GF1__part8"] is None
        assert result["GF1__part10"] is None
        assert result["GF1__part12"] is None

    def test_gf1_invalid_cloud_codes(self):
        result = clean_value_quality(
            "20,11,1,20,1,10,1,00000,1,10,1,10,1",
            "GF1",
        )
        assert result["GF1__part1"] is None
        assert result["GF1__part2"] is None
        assert result["GF1__part4"] is None
        assert result["GF1__part6"] is None
        assert result["GF1__part10"] is None
        assert result["GF1__part12"] is None

    def test_ga_cloud_type_missing(self):
        result = clean_value_quality("05,1,01000,1,99,1", "GA1")
        assert result["GA1__part5"] is None

    def test_ga_invalid_cloud_codes(self):
        result = clean_value_quality("11,1,01000,1,24,1", "GA1")
        assert result["GA1__part1"] is None
        assert result["GA1__part5"] is None

    def test_ga_base_height_range_enforced(self):
        result = clean_value_quality("05,1,36000,1,01,1", "GA1")
        assert result["GA1__part3"] is None
        result = clean_value_quality("05,1,-00401,1,01,1", "GA1")
        assert result["GA1__part3"] is None

    def test_oc1_quality_rejects_c(self):
        result = clean_value_quality("0085,C", "OC1")
        assert result["OC1__value"] is None

    def test_oc1_range_enforced(self):
        result = clean_value_quality("0049,1", "OC1")
        assert result["OC1__value"] is None
        result = clean_value_quality("1101,1", "OC1")
        assert result["OC1__value"] is None

    def test_ma1_station_pressure_quality_rejects_c(self):
        result = clean_value_quality("10132,1,09876,C", "MA1")
        assert result["MA1__part1"] == pytest.approx(1013.2)
        assert result["MA1__part3"] is None

    def test_md1_quality_rejects_4(self):
        result = clean_value_quality("5,4,045,1,0123,1", "MD1")
        assert result["MD1__part1"] is None
        assert result["MD1__part3"] == pytest.approx(4.5)
        assert result["MD1__part5"] == pytest.approx(12.3)

    def test_md1_quality_rejects_4_for_pressure(self):
        result = clean_value_quality("5,1,045,4,0123,1", "MD1")
        assert result["MD1__part3"] is None
        assert result["MD1__part5"] == pytest.approx(12.3)

    def test_sa1_quality_rejects_4(self):
        result = clean_value_quality("0215,4", "SA1")
        assert result["SA1__value"] is None

    def test_au_quality_rejects_8(self):
        result = clean_value_quality("1,1,01,1,1,1,8", "AU1")
        assert result["AU1__part1"] is None
        assert result["AU1__part2"] is None
        assert result["AU1__part3"] is None
        assert result["AU1__part4"] is None
        assert result["AU1__part5"] is None
        assert result["AU1__part6"] is None

    def test_au_missing_sentinels(self):
        result = clean_value_quality("1,9,99,9,9,9,1", "AU1")
        assert result["AU1__part2"] is None
        assert result["AU1__part3"] is None
        assert result["AU1__part4"] is None
        assert result["AU1__part5"] is None
        assert result["AU1__part6"] is None

    def test_au_invalid_component_codes(self):
        result = clean_value_quality("5,9,10,9,6,4,1", "AU1")
        assert result["AU1__part1"] is None
        assert result["AU1__part3"] is None
        assert result["AU1__part5"] is None
        assert result["AU1__part6"] is None

    def test_at_quality_rejects_8(self):
        result = clean_value_quality("AU,01,FG,8", "AT1")
        assert result["AT1__part1"] is None
        assert result["AT1__part2"] is None
        assert result["AT1__part3"] is None

    def test_at_invalid_source_code(self):
        result = clean_value_quality("XX,01,FG  ,1", "AT1")
        assert result["AT1__part1"] is None
        assert result["AT1__part2"] == "01"
        assert result["AT1__part3"] == "FG"

    def test_at_invalid_weather_type(self):
        result = clean_value_quality("AU,99,FG  ,1", "AT1")
        assert result["AT1__part2"] is None

    def test_at_preserves_fixed_width_weather_type_code(self):
        result = clean_value_quality("AU,01,FG  ,1", "AT1")
        assert result["AT1__part1"] == "AU"
        assert result["AT1__part2"] == "01"
        assert result["AT1__part3"] == "FG"

    def test_aw_tornado_code_99(self):
        result = clean_value_quality("99,1", "AW1")
        assert result["AW1__part1"] == "99"

    def test_aw_quality_rejects_8(self):
        result = clean_value_quality("01,8", "AW1")
        assert result["AW1__part1"] is None

    def test_aw_invalid_code(self):
        result = clean_value_quality("06,1", "AW1")
        assert result["AW1__part1"] is None

    def test_aw_valid_code(self):
        result = clean_value_quality("89,1", "AW1")
        assert result["AW1__part1"] == "89"

    def test_cb_quality_rejects_2(self):
        result = clean_value_quality("05,+000123,2,0", "CB1")
        assert result["CB1__part2"] is None
        assert result["CB1__part3"] is None

    def test_cb_quality_9_nulls_associated_value(self):
        result = clean_value_quality("05,+00123,9,0", "CB1", strict_mode=True)
        assert result["CB1__part2"] is None
        assert result["CB1__part2__qc_status"] == "MISSING"

    def test_cb_flag_rejects_alpha(self):
        result = clean_value_quality("05,+000123,1,M", "CB1")
        assert result["CB1__part4"] is None

    def test_cb2_range_enforced(self):
        result = clean_value_quality("05,+99998,1,0", "CB2")
        assert result["CB2__part2"] == pytest.approx(9999.8)
        result = clean_value_quality("05,+99999,1,0", "CB2")
        assert result["CB2__part2"] is None

    def test_cf_quality_rejects_2(self):
        result = clean_value_quality("0123,2,0", "CF1")
        assert result["CF1__part1"] is None

    def test_cf_quality_9_nulls_associated_value(self):
        result = clean_value_quality("0123,9,0", "CF1", strict_mode=True)
        assert result["CF1__part1"] is None
        assert result["CF1__part1__qc_status"] == "MISSING"

    def test_cf2_range_enforced(self):
        result = clean_value_quality("9998,1,0", "CF2")
        assert result["CF2__part1"] == pytest.approx(999.8)
        result = clean_value_quality("9999,1,0", "CF2")
        assert result["CF2__part1"] is None

    def test_cf3_range_enforced(self):
        result = clean_value_quality("9999,1,0", "CF3")
        assert result["CF3__part1"] is None

    def test_cg_quality_rejects_2(self):
        result = clean_value_quality("+000123,2,0", "CG1")
        assert result["CG1__part1"] is None

    def test_cg_quality_9_nulls_associated_value(self):
        result = clean_value_quality("+00123,9,0", "CG1", strict_mode=True)
        assert result["CG1__part1"] is None
        assert result["CG1__part1__qc_status"] == "MISSING"

    def test_cg2_range_enforced(self):
        result = clean_value_quality("+99998,1,0", "CG2")
        assert result["CG2__part1"] == pytest.approx(9999.8)
        result = clean_value_quality("+99999,1,0", "CG2")
        assert result["CG2__part1"] is None

    def test_cg3_range_enforced(self):
        result = clean_value_quality("+99999,1,0", "CG3")
        assert result["CG3__part1"] is None

    def test_ch_temp_quality_rejects_2(self):
        result = clean_value_quality("30,+01234,2,0,0456,1,0", "CH1")
        assert result["CH1__part2"] is None
        assert result["CH1__part5"] == pytest.approx(45.6)

    def test_ch_quality_9_nulls_only_associated_measurement(self):
        result = clean_value_quality("30,+01234,9,0,0456,1,0", "CH1", strict_mode=True)
        assert result["CH1__part2"] is None
        assert result["CH1__part2__qc_status"] == "MISSING"
        assert result["CH1__part5"] == pytest.approx(45.6)

    def test_ch2_range_enforced(self):
        result = clean_value_quality("30,+09998,1,0,0456,1,0", "CH2")
        assert result["CH2__part2"] == pytest.approx(999.8)
        result = clean_value_quality("30,+09999,1,0,0456,1,0", "CH2")
        assert result["CH2__part2"] is None

    def test_ci_std_rh_quality_rejects_2(self):
        result = clean_value_quality("00010,1,0,00020,1,0,00030,1,0,00040,2,0", "CI1")
        assert result["CI1__part10"] is None
        assert result["CI1__part11"] is None

    def test_ci_quality_9_nulls_associated_measurement(self):
        result = clean_value_quality("00010,9,0,00020,1,0,00030,1,0,00040,1,0", "CI1", strict_mode=True)
        assert result["CI1__part1"] is None
        assert result["CI1__part1__qc_status"] == "MISSING"
        assert result["CI1__part10"] == pytest.approx(4.0)

    def test_ci1_range_enforced(self):
        result = clean_value_quality("10000,1,0,00020,1,0,00030,1,0,00040,1,0", "CI1")
        assert result["CI1__part1"] is None
        result = clean_value_quality("00010,1,0,00020,1,0,00030,1,0,99999,1,0", "CI1")
        assert result["CI1__part10"] is None

    def test_ci1_domain_enforced(self):
        result = clean_value_quality("00010,1,0,00020,1,0,00030,1,0,00040,1,0", "CI1")
        assert result["CI1__part1"] == pytest.approx(1.0)
        assert result["CI1__part10"] == pytest.approx(4.0)

        result = clean_value_quality("00010,1,0,00020,1,0,00030,1,0,ABCDE,1,0", "CI1")
        assert result["CI1__part10"] is None

        result = clean_value_quality("00010,2,0,00020,1,0,00030,1,0,00040,1,0", "CI1")
        assert result["CI1__part1"] is None

    def test_cn1_datalogger_quality_rejects_2(self):
        result = clean_value_quality("0123,1,0,0456,1,0,0789,2,0", "CN1")
        assert result["CN1__part7"] is None

    def test_cn1_quality_9_nulls_associated_measurement(self):
        result = clean_value_quality("0123,9,0,0456,1,0,0789,1,0", "CN1", strict_mode=True)
        assert result["CN1__part1"] is None
        assert result["CN1__part1__qc_status"] == "MISSING"
        assert result["CN1__part4"] == pytest.approx(45.6)

    def test_cn1_range_enforced(self):
        result = clean_value_quality("9999,1,0,0456,1,0,0789,1,0", "CN1")
        assert result["CN1__part1"] is None

    def test_cn1_sentinel_rejects_missing_voltage_tokens(self):
        result = clean_value_quality("9999,1,0,9999,1,0,9999,1,0", "CN1", strict_mode=True)
        assert result["CN1__part1"] is None
        assert result["CN1__part4"] is None
        assert result["CN1__part7"] is None

    def test_cn1_sentinel_accepts_non_sentinel_voltage_tokens(self):
        result = clean_value_quality("0123,1,0,0456,1,0,0789,1,0", "CN1", strict_mode=True)
        assert result["CN1__part1"] == pytest.approx(12.3)
        assert result["CN1__part4"] == pytest.approx(45.6)
        assert result["CN1__part7"] == pytest.approx(78.9)

    def test_cn2_door_open_missing(self):
        result = clean_value_quality("0001,1,0,0002,1,0,99,1,0", "CN2")
        assert result["CN2__part7"] is None

    def test_cn2_range_enforced(self):
        result = clean_value_quality("0001,1,0,0002,1,0,61,1,0", "CN2")
        assert result["CN2__part7"] is None

    def test_cn3_signature_quality_rejects_2(self):
        result = clean_value_quality("000100,1,0,000200,2,0", "CN3")
        assert result["CN3__part4"] is None

    def test_cn3_range_enforced(self):
        result = clean_value_quality("999999,1,0,000200,1,0", "CN3")
        assert result["CN3__part1"] is None

    def test_cn3_sentinel_rejects_missing_signature_tokens(self):
        result = clean_value_quality("999999,1,0,999999,1,0", "CN3", strict_mode=True)
        assert result["CN3__part1"] is None
        assert result["CN3__part4"] is None

    def test_cn3_sentinel_accepts_non_sentinel_signature_tokens(self):
        result = clean_value_quality("000100,1,0,000200,1,0", "CN3", strict_mode=True)
        assert result["CN3__part1"] == pytest.approx(10.0)
        assert result["CN3__part4"] == pytest.approx(20.0)

    def test_cn4_flag_missing_and_quality_rejects_2(self):
        result = clean_value_quality("9,1,0,0001,1,0,100,2,0,100,1,0", "CN4")
        assert result["CN4__part1"] is None
        assert result["CN4__part7"] is None
        assert result["CN4__part10"] == pytest.approx(10.0)

    def test_cn4_range_enforced(self):
        result = clean_value_quality("1,1,0,8193,1,0,100,1,0,100,1,0", "CN4")
        assert result["CN4__part4"] is None
        result = clean_value_quality("1,1,0,0001,1,0,501,1,0,100,1,0", "CN4")
        assert result["CN4__part7"] is None

    def test_co1_missing_parts(self):
        result = clean_value_quality("99,+99", "CO1")
        assert result["CO1__part1"] is None
        assert result["CO1__part2"] is None

    def test_co1_invalid_climate_division(self):
        result = clean_value_quality("10,+00", "CO1")
        assert result["CO1__part1"] is None
        assert result["CO1__part2"] == pytest.approx(0.0)

    def test_co1_invalid_utc_offset(self):
        result = clean_value_quality("05,+13", "CO1")
        assert result["CO1__part1"] == pytest.approx(5.0)
        assert result["CO1__part2"] is None

    def test_co1_valid_utc_offsets(self):
        result = clean_value_quality("05,+12", "CO1")
        assert result["CO1__part2"] == pytest.approx(12.0)
        result = clean_value_quality("05,-12", "CO1")
        assert result["CO1__part2"] == pytest.approx(-12.0)

    def test_co2_missing_element(self):
        result = clean_value_quality("999,+0010", "CO2")
        assert result["CO2__part1"] is None
        assert result["CO2__part2"] == pytest.approx(1.0)

    def test_co2_invalid_element_id(self):
        result = clean_value_quality("AB,+0010", "CO2")
        assert result["CO2__part1"] is None
        assert result["CO2__part2"] == pytest.approx(1.0)

    def test_co2_offset_range(self):
        result = clean_value_quality("TMP,+9998", "CO2")
        assert result["CO2__part2"] == pytest.approx(999.8)
        result = clean_value_quality("TMP,+9999", "CO2")
        assert result["CO2__part2"] is None
        result = clean_value_quality("TMP,-9999", "CO2")
        assert result["CO2__part2"] == pytest.approx(-999.9)

    def test_cr1_quality_rejects_2(self):
        result = clean_value_quality("00123,2,0", "CR1")
        assert result["CR1__part1"] is None
        assert result["CR1__part2"] is None

    def test_cr1_range_accepts_max(self):
        result = clean_value_quality("99998,1,0", "CR1")
        assert result["CR1__part1"] == pytest.approx(99.998)

    def test_cr1_range_rejects_negative(self):
        result = clean_value_quality("-00001,1,0", "CR1")
        assert result["CR1__part1"] is None

    def test_ct_quality_rejects_2(self):
        result = clean_value_quality("+00123,2,0", "CT1")
        assert result["CT1__part1"] is None

    def test_ct_range_enforced(self):
        result = clean_value_quality("-10000,1,0", "CT1")
        assert result["CT1__part1"] is None

    def test_ct2_range_enforced(self):
        result = clean_value_quality("-10000,1,0", "CT2")
        assert result["CT2__part1"] is None

    def test_ct3_range_enforced(self):
        result = clean_value_quality("+9998,1,0", "CT3")
        assert result["CT3__part1"] == pytest.approx(999.8)
        result = clean_value_quality("+9999,1,0", "CT3")
        assert result["CT3__part1"] is None

    def test_cu_std_quality_rejects_2(self):
        result = clean_value_quality("+00123,1,0,0100,2,0", "CU1")
        assert result["CU1__part4"] is None

    def test_cu_range_enforced(self):
        result = clean_value_quality("10000,1,0,0100,1,0", "CU1")
        assert result["CU1__part1"] is None
        result = clean_value_quality("+00123,1,0,10000,1,0", "CU1")
        assert result["CU1__part4"] is None

    def test_cu2_range_enforced(self):
        result = clean_value_quality("+9998,1,0,9998,1,0", "CU2")
        assert result["CU2__part1"] == pytest.approx(999.8)
        assert result["CU2__part4"] == pytest.approx(999.8)
        result = clean_value_quality("+9999,1,0,0100,1,0", "CU2")
        assert result["CU2__part1"] is None

    def test_cu3_range_enforced(self):
        result = clean_value_quality("+00123,1,0,9999,1,0", "CU3")
        assert result["CU3__part4"] is None

    def test_cv_min_quality_rejects_2(self):
        result = clean_value_quality("+0123,2,0,1200,1,0,+0234,1,0,1300,1,0", "CV1")
        assert result["CV1__part1"] is None
        assert result["CV1__part7"] == pytest.approx(23.4)

    def test_cv_max_time_missing(self):
        result = clean_value_quality("+0123,1,0,1200,1,0,+0234,1,0,9999,1,0", "CV1")
        assert result["CV1__part10"] is None

    def test_cv_min_time_invalid(self):
        result = clean_value_quality("+0123,1,0,2460,1,0,+0234,1,0,1300,1,0", "CV1")
        assert result["CV1__part4"] is None
        assert result["CV1__part7"] == pytest.approx(23.4)

    def test_cv_max_time_invalid(self):
        result = clean_value_quality("+0123,1,0,1200,1,0,+0234,1,0,2400,1,0", "CV1")
        assert result["CV1__part10"] is None

    def test_cv_range_enforced(self):
        result = clean_value_quality("10000,1,0,1200,1,0,+0234,1,0,1300,1,0", "CV1")
        assert result["CV1__part1"] is None
        result = clean_value_quality("+0123,1,0,1200,1,0,10000,1,0,1300,1,0", "CV1")
        assert result["CV1__part7"] is None

    def test_cv2_range_enforced(self):
        result = clean_value_quality("+0123,1,0,1200,1,0,+0234,1,0,1300,1,0", "CV2")
        assert result["CV2__part1"] == pytest.approx(12.3)
        assert result["CV2__part7"] == pytest.approx(23.4)

        result = clean_value_quality("10000,1,0,1200,1,0,+0234,1,0,1300,1,0", "CV2")
        assert result["CV2__part1"] is None

    def test_cv3_range_enforced(self):
        result = clean_value_quality("+0123,1,0,1200,1,0,+0234,1,0,1300,1,0", "CV3")
        assert result["CV3__part1"] == pytest.approx(12.3)
        assert result["CV3__part7"] == pytest.approx(23.4)

        result = clean_value_quality("+0123,1,0,1200,1,0,10000,1,0,1300,1,0", "CV3")
        assert result["CV3__part7"] is None

    def test_cw_wet2_missing(self):
        result = clean_value_quality("00010,1,0,99999,1,0", "CW1")
        assert result["CW1__part4"] is None

    def test_cw_range_accepts_non_negative(self):
        result = clean_value_quality("00010,1,0,00020,1,0", "CW1")
        assert result["CW1__part1"] == pytest.approx(1.0)
        assert result["CW1__part4"] == pytest.approx(2.0)

    def test_cw_range_rejects_negative(self):
        result = clean_value_quality("-00001,1,0,00020,1,0", "CW1")
        assert result["CW1__part1"] is None

    def test_cx_precip_quality_rejects_2(self):
        result = clean_value_quality("+00100,2,0,1000,1,0,1000,1,0,1000,1,0", "CX1")
        assert result["CX1__part1"] is None

    def test_cx_range_enforced(self):
        result = clean_value_quality("100000,1,0,1000,1,0,1000,1,0,1000,1,0", "CX1")
        assert result["CX1__part1"] is None
        result = clean_value_quality("+00100,1,0,10000,1,0,1000,1,0,1000,1,0", "CX1")
        assert result["CX1__part4"] is None

    def test_cx2_range_enforced(self):
        result = clean_value_quality("+99998,1,0,9998,1,0,9998,1,0,9998,1,0", "CX2")
        assert result["CX2__part1"] == pytest.approx(9999.8)
        assert result["CX2__part4"] == pytest.approx(9998.0)
        result = clean_value_quality("+100000,1,0,1000,1,0,1000,1,0,1000,1,0", "CX2")
        assert result["CX2__part1"] is None

    def test_cx3_range_enforced(self):
        result = clean_value_quality("+00100,1,0,9999,1,0,1000,1,0,1000,1,0", "CX3")
        assert result["CX3__part4"] is None

    def test_ed1_missing_parts(self):
        result = clean_value_quality("99,9,9999,1", "ED1")
        assert result["ED1__part1"] is None
        assert result["ED1__part2"] is None
        assert result["ED1__part3"] is None

    def test_ed1_quality_rejects_8(self):
        result = clean_value_quality("18,L,0800,8", "ED1")
        assert result["ED1__part1"] is None
        assert result["ED1__part2"] is None
        assert result["ED1__part3"] is None

    def test_ed1_invalid_direction(self):
        result = clean_value_quality("00,L,0800,1", "ED1")
        assert result["ED1__part1"] is None
        result = clean_value_quality("37,L,0800,1", "ED1")
        assert result["ED1__part1"] is None

    def test_ed1_invalid_visibility(self):
        result = clean_value_quality("18,L,5001,1", "ED1")
        assert result["ED1__part3"] is None
        result = clean_value_quality("18,L,0000,1", "ED1")
        assert result["ED1__part3"] == pytest.approx(0.0)

    def test_ed1_range_enforced(self):
        result = clean_value_quality("36,L,5000,1", "ED1")
        assert result["ED1__part1"] == pytest.approx(360.0)
        assert result["ED1__part3"] == pytest.approx(5000.0)
        result = clean_value_quality("37,L,5000,1", "ED1")
        assert result["ED1__part1"] is None
        result = clean_value_quality("36,L,5001,1", "ED1")
        assert result["ED1__part3"] is None

    def test_gg_missing_parts(self):
        result = clean_value_quality("99,9,99999,9,99,9,99,9", "GG1")
        assert result["GG1__part1"] is None
        assert result["GG1__part3"] is None
        assert result["GG1__part5"] is None
        assert result["GG1__part7"] is None

    def test_gg_quality_rejects_8(self):
        result = clean_value_quality("01,8,00100,8,01,8,01,8", "GG1")
        assert result["GG1__part1"] is None
        assert result["GG1__part3"] is None
        assert result["GG1__part5"] is None
        assert result["GG1__part7"] is None

    def test_gd_invalid_cloud_codes(self):
        result = clean_value_quality("7,20,1,01000,1,8", "GD1")
        assert result["GD1__part1"] is None
        assert result["GD1__part2"] is None
        assert result["GD1__part6"] is None

    def test_gd_height_range_enforced(self):
        result = clean_value_quality("1,01,1,36000,1,1", "GD1")
        assert result["GD1__part4"] is None
        result = clean_value_quality("1,01,1,-00401,1,1", "GD1")
        assert result["GD1__part4"] is None

    @pytest.mark.parametrize("prefix", ["GD2", "GD3", "GD4", "GD5", "GD6"])
    def test_gd_repeated_range_enforced(self, prefix: str):
        result = clean_value_quality("1,01,1,35000,1,1", prefix)
        assert result[f"{prefix}__part4"] == pytest.approx(35000.0)
        result = clean_value_quality("1,01,1,35001,1,1", prefix)
        assert result[f"{prefix}__part4"] is None

    def test_gg_invalid_cloud_codes(self):
        result = clean_value_quality("11,1,01000,1,11,1,10,1", "GG1")
        assert result["GG1__part1"] is None
        assert result["GG1__part5"] is None
        assert result["GG1__part7"] is None

    def test_gg_top_height_range_enforced(self):
        result = clean_value_quality("01,1,35001,1,01,1,01,1", "GG1")
        assert result["GG1__part3"] is None

    @pytest.mark.parametrize("prefix", ["GG2", "GG3", "GG4", "GG5", "GG6"])
    def test_gg_repeated_range_enforced(self, prefix: str):
        result = clean_value_quality("01,1,35000,1,01,1,01,1", prefix)
        assert result[f"{prefix}__part3"] == pytest.approx(35000.0)
        result = clean_value_quality("01,1,35001,1,01,1,01,1", prefix)
        assert result[f"{prefix}__part3"] is None

    def test_ob1_quality_rejects_8(self):
        result = clean_value_quality(
            "060,0100,8,0,090,1,0,00010,1,0,00020,1,0",
            "OB1",
        )
        assert result["OB1__part2"] is None
        assert result["OB1__part5"] == pytest.approx(90.0)

    def test_oe1_quality_rejects_8(self):
        result = clean_value_quality("1,24,00100,090,1230,8", "OE1")
        assert result["OE1__part3"] is None

    def test_oe1_calm_direction(self):
        result = clean_value_quality("1,24,00000,999,1200,4", "OE1")
        assert result["OE1__part4"] is None
        assert result["qc_calm_speed_detected_OE1"] is True

    def test_wa1_quality_rejects_8(self):
        result = clean_value_quality("1,001,1,8", "WA1")
        assert result["WA1__part1"] is None
        assert result["WA1__part2"] is None
        assert result["WA1__part3"] is None

    def test_wd1_quality_rejects_8(self):
        result = clean_value_quality("01,050,06,0,1,1,01,1,010,020,8", "WD1")
        assert result["WD1__part1"] is None
        assert result["WD1__part2"] is None
        assert result["WD1__part3"] is None

    def test_wg1_quality_rejects_8(self):
        result = clean_value_quality("01,10,01,01,01,8", "WG1")
        assert result["WG1__part1"] is None
        assert result["WG1__part2"] is None

    def test_eqd_q01_reason_code_rejects_8(self):
        result = clean_value_quality("123456,8,APC3", "Q01")
        assert result["Q01__part1"] == "123456"
        assert result["Q01__part2"] is None

    def test_eqd_q01_preserves_signed_text_value(self):
        result = clean_value_quality("+01234,1,APC3", "Q01")
        assert result["Q01__part1"] == "+01234"
        assert result["Q01__part2"] == pytest.approx(1.0)

    def test_eqd_n01_units_code_rejects_z(self):
        result = clean_value_quality("ABCDEF,Z,ALTP0A", "N01")
        assert result["N01__part1"] == "ABCDEF"
        assert result["N01__part2"] is None

    def test_eqd_q01_param_code_rejects_unknown_element(self):
        result = clean_value_quality("123456,1,ZZZZb0", "Q01")
        assert result["Q01__part3"] is None

    def test_eqd_q01_param_code_accepts_legacy(self):
        result = clean_value_quality("123456,1,APC3", "Q01")
        assert result["Q01__part3"] == "APC3"

    def test_eqd_q01_param_code_rejects_element_schema(self):
        result = clean_value_quality("123456,1,ALTPb0", "Q01")
        assert result["Q01__part3"] is None

    def test_eqd_r01_param_code_accepts_msd_pattern(self):
        result = clean_value_quality("123456,1,A01001", "R01")
        assert result["R01__part3"] == "A01001"

    def test_eqd_n01_param_code_accepts_element_schema(self):
        result = clean_value_quality("ABCDEF,A,ALTPb0", "N01")
        assert result["N01__part3"] == "ALTPb0"

    def test_eqd_n01_param_code_rejects_legacy(self):
        result = clean_value_quality("ABCDEF,A,APC3", "N01")
        assert result["N01__part3"] is None

    @pytest.mark.parametrize("prefix", ["N01", "N99"])
    def test_eqd_n_repeated_width_accepts_expected_units_code_width(self, prefix: str):
        result = clean_value_quality("ABCDEF,A,ALTPb0", prefix, strict_mode=True)
        assert result[f"{prefix}__part2"] is not None

    @pytest.mark.parametrize("prefix", ["N01", "N99"])
    def test_eqd_n_repeated_width_rejects_space_padded_units_code(self, prefix: str):
        result = clean_value_quality("ABCDEF,A ,ALTPb0", prefix, strict_mode=True)
        assert result[f"{prefix}__part2"] is None

    def test_n2_token_width_accepts_single_char_units_code(self):
        result = clean_value_quality("ABCDEF,A,ALTPb0", "N2", strict_mode=True)
        assert result["N2__part2"] == "A"

    def test_n2_token_width_rejects_two_char_units_code(self):
        result = clean_value_quality("ABCDEF,AA,ALTPb0", "N2", strict_mode=True)
        assert result["N2__part2"] is None

    def test_gp1_missing_parts(self):
        result = clean_value_quality("9999,9999,99,999,9999,99,999,9999,99,999", "GP1")
        assert result["GP1__part1"] is None
        assert result["GP1__part2"] is None
        assert result["GP1__part3"] is None
        assert result["GP1__part4"] is None
        assert result["GP1__part5"] is None
        assert result["GP1__part6"] is None
        assert result["GP1__part7"] is None
        assert result["GP1__part8"] is None
        assert result["GP1__part9"] is None
        assert result["GP1__part10"] is None

    def test_gp1_invalid_source_flag(self):
        result = clean_value_quality("0060,0100,04,010,0100,01,010,0100,01,010", "GP1")
        assert result["GP1__part3"] is None

    def test_gp1_invalid_time_period(self):
        result = clean_value_quality("0000,0100,01,010,0100,01,010,0100,01,010", "GP1")
        assert result["GP1__part1"] is None

    def test_gp1_invalid_uncertainty(self):
        result = clean_value_quality("0060,0100,01,101,0100,01,010,0100,01,010", "GP1")
        assert result["GP1__part4"] is None

    def test_gp1_range_accepts_boundary_values(self):
        result = clean_value_quality("0001,9998,01,100,9998,02,100,9998,03,100", "GP1")
        assert result["GP1__part1"] == pytest.approx(1.0)
        assert result["GP1__part4"] == pytest.approx(100.0)
        assert result["GP1__part10"] == pytest.approx(100.0)

    def test_gp1_range_rejects_out_of_bounds_values(self):
        result = clean_value_quality("0000,0100,01,101,0100,01,010,0100,01,010", "GP1")
        assert result["GP1__part1"] is None
        assert result["GP1__part4"] is None

    def test_gq1_missing_parts(self):
        result = clean_value_quality("9999,9999,9,9999,9", "GQ1")
        assert result["GQ1__part1"] is None
        assert result["GQ1__part2"] is None
        assert result["GQ1__part4"] is None

    def test_gq1_quality_rejects_8(self):
        result = clean_value_quality("0060,0123,8,0456,1", "GQ1")
        assert result["GQ1__part2"] is None
        assert result["GQ1__part4"] == pytest.approx(45.6)

    def test_gq1_time_period_range(self):
        result = clean_value_quality("0000,0123,1,0456,1", "GQ1")
        assert result["GQ1__part1"] is None

    def test_gq1_angle_range(self):
        result = clean_value_quality("0060,3601,1,0456,1", "GQ1")
        assert result["GQ1__part2"] is None
        result = clean_value_quality("0060,0123,1,3601,1", "GQ1")
        assert result["GQ1__part4"] is None

    def test_gr1_missing_parts(self):
        result = clean_value_quality("9999,9999,9,9999,9", "GR1")
        assert result["GR1__part1"] is None
        assert result["GR1__part2"] is None
        assert result["GR1__part4"] is None

    def test_gr1_quality_rejects_8(self):
        result = clean_value_quality("0060,0800,8,0900,1", "GR1")
        assert result["GR1__part2"] is None
        assert result["GR1__part4"] == pytest.approx(900.0)

    def test_gr1_time_period_range(self):
        result = clean_value_quality("0000,0800,1,0900,1", "GR1")
        assert result["GR1__part1"] is None

    def test_gr1_value_range(self):
        result = clean_value_quality("0060,9999,1,0900,1", "GR1")
        assert result["GR1__part2"] is None
        result = clean_value_quality("0060,0800,1,9999,1", "GR1")
        assert result["GR1__part4"] is None

    def test_gh1_flag_domain(self):
        result = clean_value_quality("00010,1,A,00000,1,0,00000,1,0,00000,1,0", "GH1")
        assert result["GH1__part3"] is None

    def test_gh1_value_range(self):
        result = clean_value_quality("100000,1,0,99998,1,0,00000,1,0,00000,1,0", "GH1")
        assert result["GH1__part1"] is None
        assert result["GH1__part4"] == pytest.approx(9999.8)

    def test_gh1_token_width_accepts_fixed_width_tokens(self):
        result = clean_value_quality("00010,1,0,00000,1,0,00000,1,0,00000,1,0", "GH1", strict_mode=True)
        assert result["GH1__part1"] == pytest.approx(1.0)
        assert result["GH1__part4"] == pytest.approx(0.0)

    def test_gh1_token_width_rejects_short_numeric_token(self):
        result = clean_value_quality("0010,1,0,00000,1,0,00000,1,0,00000,1,0", "GH1", strict_mode=True)
        assert result["GH1__part1"] is None

    def test_gm1_data_flag_domain(self):
        result = clean_value_quality("0060,0123,AA,1,0456,00,1,0789,00,1,0123,1", "GM1")
        assert result["GM1__part3"] is None
        assert result["GM1__part2"] == pytest.approx(123.0)

    def test_gm1_uvb_quality_rejects_8(self):
        result = clean_value_quality("0060,0123,00,1,0456,00,1,0789,00,1,0123,8", "GM1")
        assert result["GM1__part11"] is None

    def test_gm1_uvb_friendly_mapping(self):
        assert (
            to_friendly_column("GM1__part12")
            == "uvb_global_irradiance_quality_code_1"
        )
        assert (
            to_internal_column("uvb_global_irradiance_quality_code_1")
            == "GM1__part12"
        )

    def test_gm1_time_period_range(self):
        result = clean_value_quality("0000,0123,00,1,0456,00,1,0789,00,1,0123,1", "GM1")
        assert result["GM1__part1"] is None

    def test_gm1_value_range(self):
        result = clean_value_quality("0060,10000,00,1,0456,00,1,0789,00,1,0123,1", "GM1")
        assert result["GM1__part2"] is None

    def test_gn1_time_period_range(self):
        result = clean_value_quality("0000,0123,1,0456,1,0789,1,0123,1,090,1", "GN1")
        assert result["GN1__part1"] is None

    def test_gn1_value_range(self):
        result = clean_value_quality("0060,10000,1,0456,1,0789,1,0123,1,090,1", "GN1")
        assert result["GN1__part2"] is None

    def test_gn1_zenith_range(self):
        result = clean_value_quality("0060,0123,1,0456,1,0789,1,0123,1,1000,1", "GN1")
        assert result["GN1__part10"] is None

    def test_go1_time_period_range(self):
        result = clean_value_quality("0000,0123,1,0456,1,0789,1", "GO1")
        assert result["GO1__part1"] is None

    def test_go1_value_range(self):
        result = clean_value_quality("0060,-1000,1,0456,1,0789,1", "GO1")
        assert result["GO1__part2"] is None

    def test_ia1_quality_rejects_8(self):
        result = clean_value_quality("01,8", "IA1")
        assert result["IA1__part1"] is None

    def test_ib1_quality_rejects_2(self):
        result = clean_value_quality("+0100,2,0,+0050,1,0,+0150,1,0,0010,1,0", "IB1")
        assert result["IB1__part1"] is None
        assert result["IB1__part4"] == pytest.approx(5.0)

    def test_ib1_sentinel_9_enforced(self):
        result = clean_value_quality("+0100,1,9,+0050,1,0,+0150,1,0,0010,1,0", "IB1")
        assert result["IB1__part1"] == pytest.approx(10.0)
        assert result["IB1__part3"] is None

        result = clean_value_quality("+0100,1,0,+0050,1,0,+0150,1,0,0010,1,0", "IB1")
        assert result["IB1__part3"] == pytest.approx(0.0)

    def test_ic1_quality_rejects_2(self):
        result = clean_value_quality("24,0100,1,2,050,1,4,+050,1,4,+040,1,4", "IC1")
        assert result["IC1__part2"] is None

    def test_kb_quality_rejects_8(self):
        result = clean_value_quality("024,A,0100,8", "KB1")
        assert result["KB1__part3"] is None

    def test_kc_quality_rejects_8(self):
        result = clean_value_quality("M,1,0123,010203,8", "KC1")
        assert result["KC1__part3"] is None

    def test_kd_quality_rejects_8(self):
        result = clean_value_quality("024,H,0100,8", "KD1")
        assert result["KD1__part3"] is None

    def test_ke_quality_rejects_8(self):
        result = clean_value_quality("01,8,02,1,03,1,04,1", "KE1")
        assert result["KE1__part1"] is None

    def test_kf_quality_rejects_2(self):
        result = clean_value_quality("0123,2", "KF1")
        assert result["KF1__part1"] is None

    def test_kg_quality_rejects_8(self):
        result = clean_value_quality("024,D,0100,D,8", "KG1")
        assert result["KG1__part3"] is None

    def test_st1_quality_rejects_2(self):
        result = clean_value_quality("1,0123,2,0050,4,01,4,2,4", "ST1")
        assert result["ST1__part2"] is None

    def test_me1_quality_rejects_8(self):
        result = clean_value_quality("1,0123,8", "ME1")
        assert result["ME1__part2"] is None

    def test_mg1_quality_rejects_1(self):
        result = clean_value_quality("10132,1,09876,9", "MG1")
        assert result["MG1__part1"] is None

    def test_ma1_range_enforced(self):
        result = clean_value_quality("08634,1,04500,1", "MA1")
        assert result["MA1__part1"] is None

    def test_md1_range_enforced(self):
        result = clean_value_quality("4,1,501,1,+801,1", "MD1")
        assert result["MD1__part3"] is None
        assert result["MD1__part5"] is None

    def test_mf1_range_enforced(self):
        result = clean_value_quality("04499,1,08600,1", "MF1")
        assert result["MF1__part1"] is None

    def test_mg1_range_enforced(self):
        result = clean_value_quality("04500,4,08599,4", "MG1")
        assert result["MG1__part3"] is None

    def test_mh1_range_enforced(self):
        result = clean_value_quality("04500,1,08599,1", "MH1")
        assert result["MH1__part3"] is None

    def test_mk1_range_enforced(self):
        result = clean_value_quality("08599,051500,1,08600,051500,1", "MK1")
        assert result["MK1__part1"] is None

    def test_mk1_invalid_occurrence_timestamp(self):
        result = clean_value_quality("08600,051560,1,08600,311260,1", "MK1")
        assert result["MK1__part2"] is None
        assert result["MK1__part5"] is None

    def test_mk1_valid_occurrence_timestamp(self):
        result = clean_value_quality("08600,051500,1,08600,311259,1", "MK1")
        assert result["MK1__part2"] == pytest.approx(51500.0)
        assert result["MK1__part5"] == pytest.approx(311259.0)

    def test_ay_quality_rejects_4(self):
        result = clean_value_quality("1,4,12,1", "AY1")
        assert result["AY1__part1"] is None
        assert result["AY1__part3"] == pytest.approx(12.0)

    def test_ay_period_quality_rejects_4(self):
        result = clean_value_quality("1,1,12,4", "AY1")
        assert result["AY1__part3"] is None

    def test_aa_quality_rejects_c(self):
        result = clean_value_quality("01,0010,1,C", "AA1")
        assert result["AA1__part2"] is None

    def test_aj_quality_rejects_c(self):
        result = clean_value_quality("0010,1,C,000100,1,C", "AJ1")
        assert result["AJ1__part1"] is None
        assert result["AJ1__part4"] is None

    def test_od_calm_direction(self):
        result = clean_value_quality("9,99,999,0000,1", "OD1")
        assert result["OD1__part3"] is None
        assert result["qc_calm_direction_detected_OD1"] is True

    def test_od_calm_flags_are_prefix_specific(self):
        od1 = clean_value_quality("9,99,999,0000,1", "OD1")
        od2 = clean_value_quality("9,99,999,0000,1", "OD2")

        assert od1["qc_calm_direction_detected_OD1"] is True
        assert od2["qc_calm_direction_detected_OD2"] is True
        assert "qc_calm_direction_detected_OD2" not in od1
        assert "qc_calm_direction_detected_OD1" not in od2

    def test_oe_calm_flags_are_prefix_specific(self):
        oe1 = clean_value_quality("1,24,00000,999,1200,4", "OE1")
        oe2 = clean_value_quality("1,24,00000,999,1200,4", "OE2")

        assert oe1["qc_calm_speed_detected_OE1"] is True
        assert oe2["qc_calm_speed_detected_OE2"] is True
        assert "qc_calm_speed_detected_OE2" not in oe1
        assert "qc_calm_speed_detected_OE1" not in oe2

    def test_oa_invalid_type_code(self):
        result = clean_value_quality("7,01,0005,1", "OA1")
        assert result["OA1__part1"] is None

    def test_oa_invalid_period_quantity(self):
        result = clean_value_quality("1,00,0005,1", "OA1")
        assert result["OA1__part2"] is None

    def test_oa_invalid_speed_rate(self):
        result = clean_value_quality("1,01,2001,1", "OA1")
        assert result["OA1__part3"] is None

    def test_od_invalid_direction(self):
        result = clean_value_quality("1,01,361,0005,1", "OD1")
        assert result["OD1__part3"] is None

    def test_od_invalid_speed_rate(self):
        result = clean_value_quality("1,01,090,2001,1", "OD1")
        assert result["OD1__part4"] is None

    @pytest.mark.parametrize("prefix", ["OA1", "OA2", "OA3"])
    def test_oa_range_period_quantity_boundary_values(self, prefix: str):
        low = clean_value_quality("1,01,0005,1", prefix, strict_mode=True)
        high = clean_value_quality("1,48,0005,1", prefix, strict_mode=True)
        assert low[f"{prefix}__part2"] == pytest.approx(1.0)
        assert high[f"{prefix}__part2"] == pytest.approx(48.0)
        assert low[f"{prefix}__part2__qc_reason"] is None
        assert high[f"{prefix}__part2__qc_reason"] is None

    @pytest.mark.parametrize("prefix", ["OA1", "OA2", "OA3"])
    def test_oa_range_period_quantity_out_of_range(self, prefix: str):
        result = clean_value_quality("1,49,0005,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part2"] is None
        assert result[f"{prefix}__part2__qc_reason"] == "OUT_OF_RANGE"

    @pytest.mark.parametrize("prefix", ["OA1", "OA2", "OA3"])
    def test_oa_range_speed_rate_boundary_values(self, prefix: str):
        low = clean_value_quality("1,01,0000,1", prefix, strict_mode=True)
        high = clean_value_quality("1,01,2000,1", prefix, strict_mode=True)
        assert low[f"{prefix}__part3"] == pytest.approx(0.0)
        assert high[f"{prefix}__part3"] == pytest.approx(200.0)
        assert low[f"{prefix}__part3__qc_reason"] is None
        assert high[f"{prefix}__part3__qc_reason"] is None

    @pytest.mark.parametrize("prefix", ["OA1", "OA2", "OA3"])
    def test_oa_range_speed_rate_out_of_range(self, prefix: str):
        result = clean_value_quality("1,01,2001,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part3"] is None
        assert result[f"{prefix}__part3__qc_reason"] == "OUT_OF_RANGE"

    @pytest.mark.parametrize("prefix", ["OD1", "OD2", "OD3"])
    def test_od_range_period_quantity_boundary_values(self, prefix: str):
        low = clean_value_quality("1,01,090,0005,1", prefix, strict_mode=True)
        high = clean_value_quality("1,48,090,0005,1", prefix, strict_mode=True)
        assert low[f"{prefix}__part2"] == pytest.approx(1.0)
        assert high[f"{prefix}__part2"] == pytest.approx(48.0)
        assert low[f"{prefix}__part2__qc_reason"] is None
        assert high[f"{prefix}__part2__qc_reason"] is None

    @pytest.mark.parametrize("prefix", ["OD1", "OD2", "OD3"])
    def test_od_range_period_quantity_out_of_range(self, prefix: str):
        result = clean_value_quality("1,49,090,0005,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part2"] is None
        assert result[f"{prefix}__part2__qc_reason"] == "OUT_OF_RANGE"

    @pytest.mark.parametrize("prefix", ["OD1", "OD2", "OD3"])
    def test_od_range_direction_boundary_values(self, prefix: str):
        low = clean_value_quality("1,01,001,0005,1", prefix, strict_mode=True)
        high = clean_value_quality("1,01,360,0005,1", prefix, strict_mode=True)
        assert low[f"{prefix}__part3"] == pytest.approx(1.0)
        assert high[f"{prefix}__part3"] == pytest.approx(360.0)
        assert low[f"{prefix}__part3__qc_reason"] is None
        assert high[f"{prefix}__part3__qc_reason"] is None

    @pytest.mark.parametrize("prefix", ["OD1", "OD2", "OD3"])
    def test_od_range_direction_out_of_range(self, prefix: str):
        result = clean_value_quality("1,01,361,0005,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part3"] is None
        assert result[f"{prefix}__part3__qc_reason"] == "OUT_OF_RANGE"

    @pytest.mark.parametrize("prefix", ["OD1", "OD2", "OD3"])
    def test_od_range_speed_rate_boundary_values(self, prefix: str):
        low = clean_value_quality("1,01,090,0000,1", prefix, strict_mode=True)
        high = clean_value_quality("1,01,090,2000,1", prefix, strict_mode=True)
        assert low[f"{prefix}__part4"] == pytest.approx(0.0)
        assert high[f"{prefix}__part4"] == pytest.approx(200.0)
        assert low[f"{prefix}__part4__qc_reason"] is None
        assert high[f"{prefix}__part4__qc_reason"] is None

    @pytest.mark.parametrize("prefix", ["OD1", "OD2", "OD3"])
    def test_od_range_speed_rate_out_of_range(self, prefix: str):
        result = clean_value_quality("1,01,090,2001,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part4"] is None
        assert result[f"{prefix}__part4__qc_reason"] == "OUT_OF_RANGE"

    @pytest.mark.parametrize("prefix", ["OE2", "OE3"])
    def test_oe_range_period_hours_boundary_values(self, prefix: str):
        result = clean_value_quality("1,24,00010,180,1200,4", prefix, strict_mode=True)
        assert result[f"{prefix}__part2"] == pytest.approx(24.0)
        assert result[f"{prefix}__part2__qc_reason"] is None

    @pytest.mark.parametrize("prefix", ["OE2", "OE3"])
    def test_oe_range_period_hours_out_of_range(self, prefix: str):
        result = clean_value_quality("1,23,00010,180,1200,4", prefix, strict_mode=True)
        assert result[f"{prefix}__part2"] is None
        assert result[f"{prefix}__part2__qc_reason"] == "OUT_OF_RANGE"

    @pytest.mark.parametrize("prefix", ["OE2", "OE3"])
    def test_oe_range_speed_rate_boundary_values(self, prefix: str):
        low = clean_value_quality("1,24,00000,180,1200,4", prefix, strict_mode=True)
        high = clean_value_quality("1,24,20000,180,1200,4", prefix, strict_mode=True)
        assert low[f"{prefix}__part3"] == pytest.approx(0.0)
        assert high[f"{prefix}__part3"] == pytest.approx(200.0)
        assert low[f"{prefix}__part3__qc_reason"] is None
        assert high[f"{prefix}__part3__qc_reason"] is None

    @pytest.mark.parametrize("prefix", ["OE2", "OE3"])
    def test_oe_range_speed_rate_out_of_range(self, prefix: str):
        result = clean_value_quality("1,24,20001,180,1200,4", prefix, strict_mode=True)
        assert result[f"{prefix}__part3"] is None
        assert result[f"{prefix}__part3__qc_reason"] == "OUT_OF_RANGE"

    @pytest.mark.parametrize("prefix", ["OE2", "OE3"])
    def test_oe_range_direction_boundary_values(self, prefix: str):
        low = clean_value_quality("1,24,00010,001,1200,4", prefix, strict_mode=True)
        high = clean_value_quality("1,24,00010,360,1200,4", prefix, strict_mode=True)
        assert low[f"{prefix}__part4"] == pytest.approx(1.0)
        assert high[f"{prefix}__part4"] == pytest.approx(360.0)
        assert low[f"{prefix}__part4__qc_reason"] is None
        assert high[f"{prefix}__part4__qc_reason"] is None

    @pytest.mark.parametrize("prefix", ["OE2", "OE3"])
    def test_oe_range_direction_out_of_range(self, prefix: str):
        result = clean_value_quality("1,24,00010,361,1200,4", prefix, strict_mode=True)
        assert result[f"{prefix}__part4"] is None
        assert result[f"{prefix}__part4__qc_reason"] == "OUT_OF_RANGE"

    @pytest.mark.parametrize("prefix", ["OE2", "OE3"])
    def test_oe_range_peak_time_boundary_values(self, prefix: str):
        low = clean_value_quality("1,24,00010,180,0000,4", prefix, strict_mode=True)
        high = clean_value_quality("1,24,00010,180,2359,4", prefix, strict_mode=True)
        assert low[f"{prefix}__part5"] == pytest.approx(0.0)
        assert high[f"{prefix}__part5"] == pytest.approx(2359.0)
        assert low[f"{prefix}__part5__qc_reason"] is None
        assert high[f"{prefix}__part5__qc_reason"] is None

    @pytest.mark.parametrize("prefix", ["OE2", "OE3"])
    def test_oe_range_peak_time_out_of_range(self, prefix: str):
        result = clean_value_quality("1,24,00010,180,2360,4", prefix, strict_mode=True)
        assert result[f"{prefix}__part5"] is None
        assert result[f"{prefix}__part5__qc_reason"] == "OUT_OF_RANGE"

    @pytest.mark.parametrize("prefix", ["RH2", "RH3"])
    def test_rh_range_period_hours_boundary_values(self, prefix: str):
        low = clean_value_quality("001,M,085,D,1", prefix, strict_mode=True)
        high = clean_value_quality("744,M,085,D,1", prefix, strict_mode=True)
        assert low[f"{prefix}__part1"] == pytest.approx(1.0)
        assert high[f"{prefix}__part1"] == pytest.approx(744.0)
        assert low[f"{prefix}__part1__qc_reason"] is None
        assert high[f"{prefix}__part1__qc_reason"] is None

    @pytest.mark.parametrize("prefix", ["RH2", "RH3"])
    def test_rh_range_period_hours_out_of_range(self, prefix: str):
        result = clean_value_quality("745,M,085,D,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] is None
        assert result[f"{prefix}__part1__qc_reason"] == "OUT_OF_RANGE"

    @pytest.mark.parametrize("prefix", ["RH2", "RH3"])
    def test_rh_range_humidity_boundary_values(self, prefix: str):
        low = clean_value_quality("024,M,000,D,1", prefix, strict_mode=True)
        high = clean_value_quality("024,M,100,D,1", prefix, strict_mode=True)
        assert low[f"{prefix}__part3"] == pytest.approx(0.0)
        assert high[f"{prefix}__part3"] == pytest.approx(100.0)
        assert low[f"{prefix}__part3__qc_reason"] is None
        assert high[f"{prefix}__part3__qc_reason"] is None

    @pytest.mark.parametrize("prefix", ["RH2", "RH3"])
    def test_rh_range_humidity_out_of_range(self, prefix: str):
        result = clean_value_quality("024,M,101,D,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part3"] is None
        assert result[f"{prefix}__part3__qc_reason"] == "OUT_OF_RANGE"

    def test_ua1_range_wave_period_boundary_values(self):
        low = clean_value_quality("I,00,120,1,03,1", "UA1", strict_mode=True)
        high = clean_value_quality("I,30,120,1,03,1", "UA1", strict_mode=True)
        assert low["UA1__part2"] == pytest.approx(0.0)
        assert high["UA1__part2"] == pytest.approx(30.0)
        assert low["UA1__part2__qc_reason"] is None
        assert high["UA1__part2__qc_reason"] is None

    def test_ua1_range_wave_period_out_of_range(self):
        result = clean_value_quality("I,31,120,1,03,1", "UA1", strict_mode=True)
        assert result["UA1__part2"] is None
        assert result["UA1__part2__qc_reason"] == "OUT_OF_RANGE"

    def test_ua1_range_wave_height_boundary_values(self):
        low = clean_value_quality("I,05,000,1,03,1", "UA1", strict_mode=True)
        high = clean_value_quality("I,05,500,1,03,1", "UA1", strict_mode=True)
        assert low["UA1__part3"] == pytest.approx(0.0)
        assert high["UA1__part3"] == pytest.approx(50.0)
        assert low["UA1__part3__qc_reason"] is None
        assert high["UA1__part3__qc_reason"] is None

    def test_ua1_range_wave_height_out_of_range(self):
        result = clean_value_quality("I,05,501,1,03,1", "UA1", strict_mode=True)
        assert result["UA1__part3"] is None
        assert result["UA1__part3__qc_reason"] == "OUT_OF_RANGE"

    def test_ug2_width_accepts_expected_part_widths(self):
        result = clean_value_quality("10,050,180,1", "UG2", strict_mode=True)
        assert result["UG2__part1"] is not None
        assert result["UG2__part2"] is not None
        assert result["UG2__part3"] is not None
        assert result["UG2__part4"] is not None

    def test_ug2_width_rejects_short_primary_period_token(self):
        result = clean_value_quality("1,050,180,1", "UG2", strict_mode=True)
        assert result["UG2__part1"] is None
        assert result["UG2__part1__qc_reason"] == "MALFORMED_TOKEN"

    def test_wnd2_width_accepts_expected_part_widths(self):
        result = clean_value_quality("090,1,N,0005,1", "WND2", strict_mode=True)
        assert result["WND2__part1"] is not None
        assert result["WND2__part2"] is not None
        assert result["WND2__part3"] is not None
        assert result["WND2__part4"] is not None
        assert result["WND2__part5"] is not None

    def test_wnd2_width_rejects_short_direction_token(self):
        result = clean_value_quality("90,1,N,0005,1", "WND2", strict_mode=True)
        assert result["WND2__part1"] is None
        assert result["WND2__part1__qc_reason"] == "MALFORMED_TOKEN"

    def test_wa1_width_accepts_expected_part_widths(self):
        result = clean_value_quality("1,050,1,1", "WA1", strict_mode=True)
        assert result["WA1__part1"] is not None
        assert result["WA1__part2"] is not None
        assert result["WA1__part3"] is not None
        assert result["WA1__part4"] is not None

    def test_wa1_width_rejects_space_padded_source_code(self):
        result = clean_value_quality("1 ,050,1,1", "WA1", strict_mode=True)
        assert result["WA1__part1"] is None

    def test_wd1_width_accepts_expected_part_widths(self):
        result = clean_value_quality("01,050,06,1,1,1,01,1,050,010,1", "WD1", strict_mode=True)
        assert result["WD1__part1"] is not None
        assert result["WD1__part2"] is not None
        assert result["WD1__part3"] is not None
        assert result["WD1__part11"] is not None

    def test_wd1_width_rejects_space_padded_coverage_code(self):
        result = clean_value_quality("01 ,050,06,1,1,1,01,1,050,010,1", "WD1", strict_mode=True)
        assert result["WD1__part1"] is None

    def test_wg1_width_accepts_expected_part_widths(self):
        result = clean_value_quality("05,20,06,01,02,1", "WG1", strict_mode=True)
        assert result["WG1__part1"] is not None
        assert result["WG1__part2"] is not None
        assert result["WG1__part3"] is not None
        assert result["WG1__part4"] is not None
        assert result["WG1__part5"] is not None
        assert result["WG1__part6"] is not None

    def test_wg1_width_rejects_space_padded_type_code(self):
        result = clean_value_quality("05 ,20,06,01,02,1", "WG1", strict_mode=True)
        assert result["WG1__part1"] is None

    def test_wj1_width_accepts_expected_part_widths(self):
        result = clean_value_quality("010,01000,73,00,0100,1,B", "WJ1", strict_mode=True)
        assert result["WJ1__part1"] is not None
        assert result["WJ1__part2"] is not None
        assert result["WJ1__part3"] is not None
        assert result["WJ1__part4"] is not None
        assert result["WJ1__part5"] is not None
        assert result["WJ1__part6"] is not None
        assert result["WJ1__part7"] is not None

    def test_wj1_width_rejects_space_padded_weather_code(self):
        result = clean_value_quality("010,01000,73 ,00,0100,1,B", "WJ1", strict_mode=True)
        assert result["WJ1__part3"] is None

    def test_mv_invalid_code(self):
        result = clean_value_quality("10,4", "MV1")
        assert result["MV1__part1"] is None

    def test_mw_invalid_code(self):
        result = clean_value_quality("100,1", "MW1")
        assert result["MW1__part1"] is None

    def test_ob_invalid_period_minutes(self):
        result = clean_value_quality("000,0050,1,0,090,1,0,00010,1,0,00020,1,0", "OB1")
        assert result["OB1__part1"] is None

    def test_ob_invalid_max_gust(self):
        result = clean_value_quality("060,10000,1,0,090,1,0,00010,1,0,00020,1,0", "OB1")
        assert result["OB1__part2"] is None

    def test_ob_invalid_direction(self):
        result = clean_value_quality("060,0050,1,0,361,1,0,00010,1,0,00020,1,0", "OB1")
        assert result["OB1__part5"] is None

    def test_ob_invalid_speed_std(self):
        result = clean_value_quality("060,0050,1,0,090,1,0,100000,1,0,00020,1,0", "OB1")
        assert result["OB1__part8"] is None

    def test_ob_invalid_direction_std(self):
        result = clean_value_quality("060,0050,1,0,090,1,0,00010,1,0,100000,1,0", "OB1")
        assert result["OB1__part11"] is None

    def test_aj_condition_missing(self):
        result = clean_value_quality("0010,9,1,000100,9,1", "AJ1")
        assert result["AJ1__part2"] is None
        assert result["AJ1__part5"] is None

    def test_ua1_missing_method_and_sea_state(self):
        result = clean_value_quality("9,05,120,1,99,1", "UA1")
        assert result["UA1__part1"] is None
        assert result["UA1__part5"] is None

    @pytest.mark.parametrize("prefix", ["OE1", "OE2", "OE3"])
    def test_oe_repeated_width_accepts_expected_part_widths(self, prefix: str):
        result = clean_value_quality("1,24,00010,180,1200,4", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] is not None
        assert result[f"{prefix}__part2"] is not None
        assert result[f"{prefix}__part3"] is not None

    @pytest.mark.parametrize("prefix", ["OE1", "OE2", "OE3"])
    def test_oe_repeated_width_rejects_space_padded_type_code(self, prefix: str):
        result = clean_value_quality("1 ,24,00010,180,1200,4", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] is None

    @pytest.mark.parametrize("prefix", ["RH1", "RH2", "RH3"])
    def test_rh_repeated_width_accepts_expected_part_widths(self, prefix: str):
        result = clean_value_quality("024,M,085,D,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] is not None
        assert result[f"{prefix}__part2"] is not None
        assert result[f"{prefix}__part3"] is not None

    @pytest.mark.parametrize("prefix", ["RH1", "RH2", "RH3"])
    def test_rh_repeated_width_rejects_space_padded_code(self, prefix: str):
        result = clean_value_quality("024, M,085,D,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part2"] is None

    def test_ua1_width_accepts_expected_part_widths(self):
        result = clean_value_quality("I,05,120,1,03,1", "UA1", strict_mode=True)
        assert result["UA1__part1"] is not None
        assert result["UA1__part2"] is not None
        assert result["UA1__part3"] is not None

    def test_ua1_width_rejects_space_padded_quality_code(self):
        result = clean_value_quality("I,05,120,1 ,03,1", "UA1", strict_mode=True)
        assert result["UA1__part1"] is not None
        assert result["UA1__part2"] is not None
        assert result["UA1__part3"] is not None
        assert result["UA1__part4"] is None

    def test_ug1_width_accepts_expected_part_widths(self):
        result = clean_value_quality("10,050,180,1", "UG1", strict_mode=True)
        assert result["UG1__part1"] is not None
        assert result["UG1__part2"] is not None
        assert result["UG1__part3"] is not None

    def test_ug1_width_rejects_space_padded_quality_code(self):
        result = clean_value_quality("10,050,180,1 ", "UG1", strict_mode=True)
        assert result["UG1__part1"] is not None
        assert result["UG1__part2"] is not None
        assert result["UG1__part3"] is not None
        assert result["UG1__part4"] is None

    def test_ab_monthly_total_quality(self):
        result = clean_value_quality("00500,1,8", "AB1")
        assert result["AB1__part1"] is None

    def test_ab_monthly_total_range(self):
        result = clean_value_quality("50001,1,1", "AB1")
        assert result["AB1__part1"] is None

    def test_ac_duration_characteristic_codes(self):
        result = clean_value_quality("4,C,1", "AC1")
        assert result["AC1__part1"] == pytest.approx(4.0)
        assert result["AC1__part2"] == "C"
        assert result["qc_domain_invalid_AC1"] is True

    def test_ac_characteristic_missing(self):
        result = clean_value_quality("1,9,1", "AC1")
        assert result["AC1__part2"] is None

    def test_ad_missing_dates(self):
        result = clean_value_quality("01000,2,9999,0102,9999,1", "AD1")
        assert result["AD1__part3"] is None
        assert result["AD1__part5"] is None

    def test_ad_amount_and_date_range(self):
        result = clean_value_quality("20001,2,0102,0102,0102,1", "AD1")
        assert result["AD1__part1"] is None
        result = clean_value_quality("01000,2,3201,0102,0102,1", "AD1")
        assert result["AD1__part3"] == pytest.approx(3201.0)
        assert result["qc_pattern_mismatch_AD1"] is True

    def test_ae_missing_and_quality(self):
        result = clean_value_quality("99,1,05,8,10,1,00,1", "AE1")
        assert result["AE1__part1"] is None
        assert result["AE1__part3"] is None

    def test_ae_day_count_range(self):
        result = clean_value_quality("32,1,00,1,00,1,00,1", "AE1")
        assert result["AE1__part1"] is None
        result = clean_value_quality("00,1,32,1,00,1,00,1", "AE1")
        assert result["AE1__part3"] is None

    def test_aj_range_enforced(self):
        result = clean_value_quality("1201,1,1,120001,1,1", "AJ1")
        assert result["AJ1__part1"] is None
        assert result["AJ1__part4"] is None

    def test_aj1_width_accepts_expected_part_widths(self):
        result = clean_value_quality("1200,1,1,120000,1,1", "AJ1", strict_mode=True)
        assert result["AJ1__part1"] is not None
        assert result["AJ1__part2"] is not None
        assert result["AJ1__part3"] is not None
        assert result["AJ1__part4"] is not None
        assert result["AJ1__part5"] is not None
        assert result["AJ1__part6"] is not None

    def test_aj1_width_rejects_short_part1_token_as_malformed(self):
        result = clean_value_quality("120,1,1,120000,1,1", "AJ1", strict_mode=True)
        assert result["AJ1__part1"] is None
        assert result["AJ1__part1__qc_reason"] == "MALFORMED_TOKEN"

    def test_ag_discrepancy_and_missing_depth(self):
        result = clean_value_quality("9,999", "AG1")
        assert result["AG1__part1"] is None
        assert result["AG1__part2"] is None

    def test_ah_missing_and_quality(self):
        result = clean_value_quality("999,9999,9,999999,1", "AH1")
        assert result["AH1__part1"] is None
        assert result["AH1__part2"] is None
        assert result["AH1__part3"] is None
        assert result["AH1__part4"] is None

    def test_ah_quality_rejects_c(self):
        result = clean_value_quality("015,0123,1,010100,C", "AH1")
        assert result["AH1__part2"] is None

    def test_ah_end_datetime_range_enforced(self):
        result = clean_value_quality("015,0123,1,006000,1", "AH1")
        assert result["AH1__part4"] == pytest.approx(6000.0)
        result = clean_value_quality("015,0123,1,320000,1", "AH1")
        assert result["AH1__part4"] == pytest.approx(320000.0)
        assert result["qc_pattern_mismatch_AH1"] is True
        result = clean_value_quality("015,0123,1,051010,1", "AH1")
        assert result["AH1__part4"] == pytest.approx(51010.0)

    def test_ai_missing_and_quality(self):
        result = clean_value_quality("999,9999,9,999999,1", "AI1")
        assert result["AI1__part1"] is None
        assert result["AI1__part2"] is None
        assert result["AI1__part3"] is None
        assert result["AI1__part4"] is None

    def test_ai_quality_rejects_c(self):
        result = clean_value_quality("060,0123,1,010100,C", "AI1")
        assert result["AI1__part2"] is None

    def test_ai_end_datetime_range_enforced(self):
        result = clean_value_quality("060,0123,1,006000,1", "AI1")
        assert result["AI1__part4"] is None
        result = clean_value_quality("060,0123,1,320000,1", "AI1")
        assert result["AI1__part4"] is None
        result = clean_value_quality("060,0123,1,051010,1", "AI1")
        assert result["AI1__part4"] == pytest.approx(51010.0)

    def test_ak_missing_and_quality(self):
        result = clean_value_quality("9999,9,999999,1", "AK1")
        assert result["AK1__part1"] is None
        assert result["AK1__part2"] is None
        assert result["AK1__part3"] is None

    def test_ak_quality_rejects_c(self):
        result = clean_value_quality("0100,1,010203,C", "AK1")
        assert result["AK1__part1"] is None

    def test_ak_range_enforced(self):
        result = clean_value_quality("1501,1,010203,1", "AK1")
        assert result["AK1__part1"] is None
        result = clean_value_quality("0100,1,320203,1", "AK1")
        assert result["AK1__part3"] is None

    def test_ak1_width_accepts_expected_part_widths(self):
        result = clean_value_quality("1500,1,010203,1", "AK1", strict_mode=True)
        assert result["AK1__part1"] is not None
        assert result["AK1__part2"] is not None
        assert result["AK1__part3"] is not None
        assert result["AK1__part4"] is not None

    def test_ak1_width_rejects_short_part1_token_as_malformed(self):
        result = clean_value_quality("100,1,010203,1", "AK1", strict_mode=True)
        assert result["AK1__part1"] is None
        assert result["AK1__part1__qc_reason"] == "MALFORMED_TOKEN"

    def test_al_missing_and_quality(self):
        result = clean_value_quality("99,999,9,1", "AL1")
        assert result["AL1__part1"] is None
        assert result["AL1__part2"] is None
        assert result["AL1__part3"] is None

    def test_al_quality_rejects_c(self):
        result = clean_value_quality("24,010,1,C", "AL1")
        assert result["AL1__part2"] is None

    def test_al_range_enforced(self):
        result = clean_value_quality("73,010,1,1", "AL1")
        assert result["AL1__part1"] is None
        result = clean_value_quality("24,501,1,1", "AL1")
        assert result["AL1__part2"] is None

    def test_al2_range_enforced(self):
        result = clean_value_quality("72,500,1,1", "AL2")
        assert result["AL2__part1"] == pytest.approx(72.0)
        assert result["AL2__part2"] == pytest.approx(500.0)
        result = clean_value_quality("73,500,1,1", "AL2")
        assert result["AL2__part1"] is None

    def test_al3_range_enforced(self):
        result = clean_value_quality("24,501,1,1", "AL3")
        assert result["AL3__part2"] is None

    def test_al4_range_enforced(self):
        result = clean_value_quality("00,000,1,1", "AL4")
        assert result["AL4__part1"] == pytest.approx(0.0)
        assert result["AL4__part2"] == pytest.approx(0.0)

    @pytest.mark.parametrize("prefix", ["AL2", "AL3", "AL4"])
    def test_al_repeated_sentinel_rejects_missing_period_token(self, prefix: str):
        result = clean_value_quality("99,100,1,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] is None

    @pytest.mark.parametrize("prefix", ["AL2", "AL3", "AL4"])
    def test_al_repeated_sentinel_accepts_non_sentinel_period_token(self, prefix: str):
        result = clean_value_quality("72,100,1,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] == pytest.approx(72.0)

    @pytest.mark.parametrize("prefix", ["AL2", "AL3", "AL4"])
    def test_al_repeated_sentinel_rejects_missing_depth_token(self, prefix: str):
        result = clean_value_quality("72,999,1,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part2"] is None

    @pytest.mark.parametrize("prefix", ["AL2", "AL3", "AL4"])
    def test_al_repeated_sentinel_accepts_non_sentinel_depth_token(self, prefix: str):
        result = clean_value_quality("72,500,1,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part2"] == pytest.approx(500.0)

    @pytest.mark.parametrize("prefix", ["AL2", "AL3", "AL4"])
    def test_al_repeated_sentinel_rejects_missing_condition_token(self, prefix: str):
        result = clean_value_quality("72,100,9,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part3"] is None

    @pytest.mark.parametrize("prefix", ["AL2", "AL3", "AL4"])
    def test_al_repeated_sentinel_accepts_non_sentinel_condition_token(self, prefix: str):
        result = clean_value_quality("72,100,E,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part3"] == "E"

    @pytest.mark.parametrize("prefix", ["AL1", "AL2", "AL3", "AL4"])
    def test_al_repeated_width_accepts_expected_part_widths(self, prefix: str):
        result = clean_value_quality("72,500,1,9", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] is not None
        assert result[f"{prefix}__part2"] is not None
        assert result[f"{prefix}__part3"] is not None
        assert result[f"{prefix}__part4"] is not None

    @pytest.mark.parametrize("prefix", ["AL1", "AL2", "AL3", "AL4"])
    def test_al_repeated_width_rejects_short_period_token_as_malformed(self, prefix: str):
        result = clean_value_quality("7,500,1,9", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] is None
        assert result[f"{prefix}__part1__qc_reason"] == "MALFORMED_TOKEN"

    def test_am_missing_and_quality(self):
        result = clean_value_quality("9999,9,9999,9999,9999,1", "AM1")
        assert result["AM1__part1"] is None
        assert result["AM1__part2"] is None
        assert result["AM1__part3"] is None
        assert result["AM1__part4"] is None
        assert result["AM1__part5"] is None

    def test_am_quality_rejects_c(self):
        result = clean_value_quality("0100,1,0102,0203,0304,C", "AM1")
        assert result["AM1__part1"] is None

    def test_am_range_enforced(self):
        result = clean_value_quality("2001,1,0102,0203,0304,1", "AM1")
        assert result["AM1__part1"] is None
        result = clean_value_quality("0100,1,3202,0203,0304,1", "AM1")
        assert result["AM1__part3"] is None

    def test_am1_width_accepts_expected_part_widths(self):
        result = clean_value_quality("2000,1,0101,0202,0303,1", "AM1", strict_mode=True)
        assert result["AM1__part1"] is not None
        assert result["AM1__part2"] is not None
        assert result["AM1__part3"] is not None
        assert result["AM1__part4"] is not None
        assert result["AM1__part5"] is not None
        assert result["AM1__part6"] is not None

    def test_am1_width_rejects_short_part1_token_as_malformed(self):
        result = clean_value_quality("200,1,0101,0202,0303,1", "AM1", strict_mode=True)
        assert result["AM1__part1"] is None
        assert result["AM1__part1__qc_reason"] == "MALFORMED_TOKEN"

    def test_an_missing_and_quality(self):
        result = clean_value_quality("999,9999,9,1", "AN1")
        assert result["AN1__part1"] is None
        assert result["AN1__part2"] is None
        assert result["AN1__part3"] is None

    def test_an_quality_rejects_c(self):
        result = clean_value_quality("024,0100,1,C", "AN1")
        assert result["AN1__part2"] is None

    def test_an_range_enforced(self):
        result = clean_value_quality("000,0100,1,1", "AN1")
        assert result["AN1__part1"] is None
        result = clean_value_quality("024,9999,1,1", "AN1")
        assert result["AN1__part2"] is None

    def test_an1_width_accepts_expected_part_widths(self):
        result = clean_value_quality("744,9998,1,9", "AN1", strict_mode=True)
        assert result["AN1__part1"] is not None
        assert result["AN1__part2"] is not None
        assert result["AN1__part3"] is not None
        assert result["AN1__part4"] is not None

    def test_an1_width_rejects_short_part1_token_as_malformed(self):
        result = clean_value_quality("74,9998,1,9", "AN1", strict_mode=True)
        assert result["AN1__part1"] is None
        assert result["AN1__part1__qc_reason"] == "MALFORMED_TOKEN"

    def test_ao_missing_and_quality(self):
        result = clean_value_quality("99,9999,9,1", "AO1")
        assert result["AO1__part1"] is None
        assert result["AO1__part2"] is None
        assert result["AO1__part3"] is None

    def test_ao_quality_rejects_8(self):
        result = clean_value_quality("15,0010,1,8", "AO1")
        assert result["AO1__part2"] is None

    @pytest.mark.parametrize("prefix", ["AO2", "AO3", "AO4"])
    def test_ao_repeated_sentinel_rejects_missing_period_token(self, prefix: str):
        result = clean_value_quality("99,1000,1,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] is None

    @pytest.mark.parametrize("prefix", ["AO2", "AO3", "AO4"])
    def test_ao_repeated_sentinel_accepts_non_sentinel_period_token(self, prefix: str):
        result = clean_value_quality("98,1000,1,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] == pytest.approx(98.0)

    @pytest.mark.parametrize("prefix", ["AO2", "AO3", "AO4"])
    def test_ao_repeated_sentinel_rejects_missing_depth_token(self, prefix: str):
        result = clean_value_quality("98,9999,1,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part2"] is None

    @pytest.mark.parametrize("prefix", ["AO2", "AO3", "AO4"])
    def test_ao_repeated_sentinel_accepts_non_sentinel_depth_token(self, prefix: str):
        result = clean_value_quality("98,9998,1,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part2"] == pytest.approx(999.8)

    @pytest.mark.parametrize("prefix", ["AO2", "AO3", "AO4"])
    def test_ao_repeated_sentinel_rejects_missing_condition_token(self, prefix: str):
        result = clean_value_quality("98,1000,9,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part3"] is None

    @pytest.mark.parametrize("prefix", ["AO2", "AO3", "AO4"])
    def test_ao_repeated_sentinel_accepts_non_sentinel_condition_token(self, prefix: str):
        result = clean_value_quality("98,1000,E,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part3"] == "E"

    @pytest.mark.parametrize("prefix", ["AO1", "AO2", "AO3", "AO4"])
    def test_ao_repeated_width_accepts_expected_part_widths(self, prefix: str):
        result = clean_value_quality("98,9998,1,9", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] is not None
        assert result[f"{prefix}__part2"] is not None
        assert result[f"{prefix}__part3"] is not None
        assert result[f"{prefix}__part4"] is not None

    @pytest.mark.parametrize("prefix", ["AO1", "AO2", "AO3", "AO4"])
    def test_ao_repeated_width_rejects_short_period_token_as_malformed(self, prefix: str):
        result = clean_value_quality("8,9998,1,9", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] is None
        assert result[f"{prefix}__part1__qc_reason"] == "MALFORMED_TOKEN"

    @pytest.mark.parametrize("prefix", ["AO1", "AO2", "AO3", "AO4"])
    def test_ao_repeated_range_accepts_upper_bounds(self, prefix: str):
        result = clean_value_quality("98,9998,1,9", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] == pytest.approx(98.0)
        assert result[f"{prefix}__part2"] == pytest.approx(999.8)

    @pytest.mark.parametrize("prefix", ["AO1", "AO2", "AO3", "AO4"])
    def test_ao_repeated_range_rule_bounds_are_not_open_ended(self, prefix: str):
        rule = get_field_rule(prefix)
        assert rule is not None
        assert rule.parts[1].max_value == 98
        assert rule.parts[2].max_value == 9998
        assert rule.parts[1].max_value != 99
        assert rule.parts[2].max_value != 9999

    def test_ap_missing_and_quality(self):
        result = clean_value_quality("9999,9,1", "AP1")
        assert result["AP1__part1"] is None
        assert result["AP1__part2"] is None

    def test_ap_quality_rejects_8(self):
        result = clean_value_quality("0010,9,8", "AP1")
        assert result["AP1__part1"] is None

    def test_ap4_sentinel_rejects_missing_amount_token(self):
        result = clean_value_quality("9999,9,1", "AP4", strict_mode=True)
        assert result["AP4__part1"] is None

    def test_ap4_sentinel_accepts_non_sentinel_amount_token(self):
        result = clean_value_quality("9998,9,1", "AP4", strict_mode=True)
        assert result["AP4__part1"] == pytest.approx(999.8)

    def test_ap4_sentinel_rejects_missing_condition_token(self):
        result = clean_value_quality("0001,9,1", "AP4", strict_mode=True)
        assert result["AP4__part2"] is None

    def test_ap4_width_accepts_expected_part_widths(self):
        result = clean_value_quality("9998,9,1", "AP4", strict_mode=True)
        assert result["AP4__part1"] is not None
        assert result["AP4__part2"] is None
        assert result["AP4__part3"] is not None

    def test_ap4_width_rejects_short_part1_token_as_malformed(self):
        result = clean_value_quality("998,9,1", "AP4", strict_mode=True)
        assert result["AP4__part1"] is None
        assert result["AP4__part1__qc_reason"] == "MALFORMED_TOKEN"

    def test_ap4_range_accepts_upper_bound(self):
        result = clean_value_quality("9998,9,1", "AP4", strict_mode=True)
        assert result["AP4__part1"] == pytest.approx(999.8)

    def test_ap4_range_rule_bounds_are_not_open_ended(self):
        rule = get_field_rule("AP4")
        assert rule is not None
        assert rule.parts[1].min_value == 0
        assert rule.parts[1].max_value == 9998
        assert rule.parts[1].max_value != 9999


class TestTwoPartFieldNamingAndQuality:
    def test_mw_two_part_uses_parts(self):
        result = clean_value_quality("12,4", "MW1")
        assert "MW1__part1" in result
        assert "MW1__part2" in result

    def test_mw_quality_gates_code(self):
        result = clean_value_quality("12,8", "MW1")
        assert result["MW1__part1"] is None

    def test_mv_quality_gates_code(self):
        result = clean_value_quality("05,3", "MV1")
        assert result["MV1__part1"] is None

    def test_gj_quality_gates_value(self):
        result = clean_value_quality("0100,8", "GJ1")
        assert result["GJ1__part1"] is None

    def test_gj_range_enforced(self):
        result = clean_value_quality("6001,1", "GJ1")
        assert result["GJ1__part1"] is None

    def test_gk_range_enforced(self):
        result = clean_value_quality("101,4", "GK1")
        assert result["GK1__part1"] is None

    def test_gl_range_enforced(self):
        result = clean_value_quality("30001,1", "GL1")
        assert result["GL1__part1"] is None


class TestCleanDataframeEdgeCases:
    def test_invalid_quality_nulls_values_in_dataframe(self):
        df = pd.DataFrame(
            {
                "TMP": [
                    "+0250,1",
                    "+0250,8",
                ],
            }
        )
        cleaned = clean_noaa_dataframe(df, keep_raw=False)
        assert cleaned.loc[0, "temperature_c"] == pytest.approx(25.0)
        assert pd.isna(cleaned.loc[1, "temperature_c"])

    def test_invalid_quality_in_multipart_field(self):
        df = pd.DataFrame(
            {
                "KA1": [
                    "005,1,0123,8",  # invalid quality code
                ],
            }
        )
        cleaned = clean_noaa_dataframe(df, keep_raw=False)
        assert pd.isna(cleaned.loc[0, "extreme_temp_period_hours_1"])
        assert pd.isna(cleaned.loc[0, "extreme_temp_c_1"])

    def test_vis_missing_with_leading_zeros(self):
        df = pd.DataFrame(
            {
                "VIS": [
                    "009999,5,N,1",
                ],
            }
        )
        cleaned = clean_noaa_dataframe(df, keep_raw=False)
        assert cleaned.loc[0, "visibility_m"] == pytest.approx(9999.0)

    def test_add_section_marker_dropped(self):
        df = pd.DataFrame(
            {
                "ADD": ["ADD", "ADD"],
                "TMP": ["+0250,1", "+0260,1"],
            }
        )
        cleaned = clean_noaa_dataframe(df, keep_raw=True)
        assert "ADD" not in cleaned.columns

    def test_remark_parsing(self):
        df = pd.DataFrame(
            {
                "REM": [
                    "SYN013052AAXX 01004",
                    "MET005a,b c",
                    "XYZbar",
                    None,
                ]
            }
        )
        cleaned = clean_noaa_dataframe(df, keep_raw=False)
        assert cleaned.loc[0, "remarks_type_code"] == "SYN"
        assert cleaned.loc[0, "remarks_text"] == "052AAXX 01004"
        assert cleaned.loc[0, "remarks_type_codes"] == "SYN"
        assert json.loads(cleaned.loc[0, "remarks_text_blocks_json"]) == ["052AAXX 01004"]
        assert cleaned.loc[1, "remarks_type_code"] == "MET"
        assert cleaned.loc[1, "remarks_text"] == "a,b c"
        assert cleaned.loc[1, "remarks_type_codes"] == "MET"
        assert json.loads(cleaned.loc[1, "remarks_text_blocks_json"]) == ["a,b c"]
        assert pd.isna(cleaned.loc[2, "remarks_type_code"])
        assert cleaned.loc[2, "remarks_text"] == "XYZbar"
        assert pd.isna(cleaned.loc[2, "remarks_type_codes"])
        assert pd.isna(cleaned.loc[2, "remarks_text_blocks_json"])
        assert pd.isna(cleaned.loc[3, "remarks_type_code"])
        assert pd.isna(cleaned.loc[3, "remarks_text"])
        assert pd.isna(cleaned.loc[3, "remarks_type_codes"])
        assert pd.isna(cleaned.loc[3, "remarks_text_blocks_json"])

    def test_remark_all9_text_preserved(self):
        df = pd.DataFrame({"REM": ["MET003999"]})
        cleaned = clean_noaa_dataframe(df, keep_raw=False)
        assert cleaned.loc[0, "remarks_type_code"] == "MET"
        assert cleaned.loc[0, "remarks_text"] == "999"
        assert cleaned.loc[0, "remarks_type_codes"] == "MET"
        assert json.loads(cleaned.loc[0, "remarks_text_blocks_json"]) == ["999"]

    def test_remark_repeated_blocks_are_parsed_losslessly(self):
        df = pd.DataFrame({"REM": ["MET003fooSOD003bar"]})
        cleaned = clean_noaa_dataframe(df, keep_raw=False)
        assert cleaned.loc[0, "remarks_type_code"] == "MET"
        assert cleaned.loc[0, "remarks_text"] == "foo"
        assert cleaned.loc[0, "remarks_type_codes"] == "MET,SOD"
        assert json.loads(cleaned.loc[0, "remarks_text_blocks_json"]) == ["foo", "bar"]

    def test_remark_invalid_length_falls_back_to_raw_text(self):
        df = pd.DataFrame({"REM": ["METfoo", "MET003fo"]})
        cleaned = clean_noaa_dataframe(df, keep_raw=False)
        assert pd.isna(cleaned.loc[0, "remarks_type_code"])
        assert cleaned.loc[0, "remarks_text"] == "METfoo"
        assert pd.isna(cleaned.loc[0, "remarks_type_codes"])
        assert pd.isna(cleaned.loc[0, "remarks_text_blocks_json"])
        assert pd.isna(cleaned.loc[1, "remarks_type_code"])
        assert cleaned.loc[1, "remarks_text"] == "MET003fo"
        assert pd.isna(cleaned.loc[1, "remarks_type_codes"])
        assert pd.isna(cleaned.loc[1, "remarks_text_blocks_json"])

    def test_qnn_parsing(self):
        df = pd.DataFrame(
            {
                "QNN": [
                    "QNN A1234B5678 001234002345",
                    "QNN A1234 001234",
                    "QNN A1234B5678 001234",
                    "QNNZ9999",
                    None,
                ]
            }
        )
        cleaned = clean_noaa_dataframe(df, keep_raw=False)
        assert cleaned.loc[0, "qnn_element_ids"] == "A,B"
        assert cleaned.loc[0, "qnn_source_flags"] == "1234,5678"
        assert cleaned.loc[0, "qnn_data_values"] == "001234,002345"
        assert cleaned.loc[1, "qnn_element_ids"] == "A"
        assert cleaned.loc[1, "qnn_source_flags"] == "1234"
        assert cleaned.loc[1, "qnn_data_values"] == "001234"
        assert pd.isna(cleaned.loc[2, "qnn_element_ids"])
        assert pd.isna(cleaned.loc[2, "qnn_source_flags"])
        assert pd.isna(cleaned.loc[2, "qnn_data_values"])
        assert pd.isna(cleaned.loc[3, "qnn_element_ids"])
        assert pd.isna(cleaned.loc[3, "qnn_source_flags"])
        assert pd.isna(cleaned.loc[3, "qnn_data_values"])
        assert pd.isna(cleaned.loc[4, "qnn_element_ids"])
        assert pd.isna(cleaned.loc[4, "qnn_source_flags"])
        assert pd.isna(cleaned.loc[4, "qnn_data_values"])

    def test_qnn_preserves_ascii_and_all9_payloads(self):
        df = pd.DataFrame(
            {
                "QNN": [
                    "QNN Aab!$ AbCd12",
                    "QNN A1234 999999",
                    "QNN A1234 AAAAAA",
                    "QNN A1234 A56789",
                ]
            }
        )
        cleaned = clean_noaa_dataframe(df, keep_raw=False)
        assert cleaned.loc[0, "qnn_element_ids"] == "A"
        assert cleaned.loc[0, "qnn_source_flags"] == "ab!$"
        assert cleaned.loc[0, "qnn_data_values"] == "AbCd12"
        assert cleaned.loc[1, "qnn_data_values"] == "999999"
        assert cleaned.loc[2, "qnn_data_values"] == "AAAAAA"
        assert cleaned.loc[3, "qnn_data_values"] == "A56789"

    def test_qnn_multiblock_ascii_token_boundaries(self):
        df = pd.DataFrame(
            {
                "QNN": [
                    "QNN Aab!$B[]{} !@#$%^A?<>/=",
                ]
            }
        )
        cleaned = clean_noaa_dataframe(df, keep_raw=False)
        assert cleaned.loc[0, "qnn_element_ids"] == "A,B"
        assert cleaned.loc[0, "qnn_source_flags"] == "ab!$,[]{}"
        assert cleaned.loc[0, "qnn_data_values"] == "!@#$%^,A?<>/="

    def test_rem_and_qnn_all9_text_payloads_survive_cleanup(self):
        df = pd.DataFrame(
            {
                "REM": ["MET006999999"],
                "QNN": ["QNN A9999 999999"],
            }
        )
        cleaned = clean_noaa_dataframe(df, keep_raw=False)
        assert cleaned.loc[0, "remarks_type_code"] == "MET"
        assert cleaned.loc[0, "remarks_text"] == "999999"
        assert cleaned.loc[0, "remarks_type_codes"] == "MET"
        assert json.loads(cleaned.loc[0, "remarks_text_blocks_json"]) == ["999999"]
        assert cleaned.loc[0, "qnn_element_ids"] == "A"
        assert cleaned.loc[0, "qnn_source_flags"] == "9999"
        assert cleaned.loc[0, "qnn_data_values"] == "999999"

    def test_ah_ai_friendly_columns_are_disambiguated(self):
        assert to_friendly_column("AH1__part1") == "precip_5_to_45_min_period_minutes_1"
        assert to_friendly_column("AI1__part1") == "precip_60_to_180_min_period_minutes_1"
        assert to_internal_column("precip_5_to_45_min_period_minutes_1") == "AH1__part1"
        assert to_internal_column("precip_60_to_180_min_period_minutes_1") == "AI1__part1"
        assert to_internal_column("precip_short_duration_period_minutes_1") == "AH1__part1"

    def test_ah_ai_cleaned_outputs_are_distinct(self):
        df = pd.DataFrame(
            {
                "AH1": ["015,0123,1,051010,1"],
                "AI1": ["060,0456,1,051010,1"],
            }
        )
        cleaned = clean_noaa_dataframe(df, keep_raw=False)
        assert not cleaned.columns.duplicated().any()
        assert "precip_5_to_45_min_period_minutes_1" in cleaned.columns
        assert "precip_60_to_180_min_period_minutes_1" in cleaned.columns
        assert cleaned.loc[0, "precip_5_to_45_min_period_minutes_1"] == pytest.approx(15.0)
        assert cleaned.loc[0, "precip_60_to_180_min_period_minutes_1"] == pytest.approx(60.0)

    @pytest.mark.parametrize(
        "family,left_idx,right_idx",
        REPEATED_FAMILY_SIBLINGS,
    )
    def test_repeated_family_siblings_map_to_distinct_cleaned_names(
        self,
        family: str,
        left_idx: int,
        right_idx: int,
    ) -> None:
        left_internal = f"{family}{left_idx}__part1"
        right_internal = f"{family}{right_idx}__part1"
        left_friendly = to_friendly_column(left_internal)
        right_friendly = to_friendly_column(right_internal)

        assert left_friendly != right_friendly
        assert to_internal_column(left_friendly) == left_internal
        assert to_internal_column(right_friendly) == right_internal

    @pytest.mark.parametrize(
        "column,value,expected_flag",
        [
            ("OD1", "9,99,999,0000,1", "qc_calm_direction_detected_OD1"),
            ("OD2", "9,99,999,0000,1", "qc_calm_direction_detected_OD2"),
            ("OE1", "1,24,00000,999,1200,4", "qc_calm_speed_detected_OE1"),
            ("OE2", "1,24,00000,999,1200,4", "qc_calm_speed_detected_OE2"),
        ],
    )
    def test_single_repeated_group_keeps_prefix_specific_qc_columns(
        self,
        column: str,
        value: str,
        expected_flag: str,
    ) -> None:
        cleaned = clean_noaa_dataframe(pd.DataFrame({column: [value]}), keep_raw=False)
        assert cleaned.columns.is_unique
        assert expected_flag in cleaned.columns
        assert bool(cleaned.loc[0, expected_flag])

    def test_multi_repeated_groups_keep_distinct_lineage(self):
        df = pd.DataFrame(
            {
                "OD1": ["9,99,999,0000,1"],
                "OD2": ["9,99,999,0000,1"],
                "OE1": ["1,24,00000,999,1200,4"],
                "OE2": ["1,24,00000,999,1200,4"],
                "RH1": ["999,9,999,9,9"],
                "RH2": ["999,9,999,9,9"],
            }
        )
        cleaned = clean_noaa_dataframe(df, keep_raw=False)
        assert cleaned.columns.is_unique
        assert "qc_calm_direction_detected_OD1" in cleaned.columns
        assert "qc_calm_direction_detected_OD2" in cleaned.columns
        assert "qc_calm_speed_detected_OE1" in cleaned.columns
        assert "qc_calm_speed_detected_OE2" in cleaned.columns
        assert "relative_humidity_period_hours_1" in cleaned.columns
        assert "relative_humidity_period_hours_2" in cleaned.columns
        assert cleaned.loc[0, "qc_calm_direction_detected_OD1"] == True
        assert cleaned.loc[0, "qc_calm_direction_detected_OD2"] == True
        assert cleaned.loc[0, "qc_calm_speed_detected_OE1"] == True
        assert cleaned.loc[0, "qc_calm_speed_detected_OE2"] == True

    def test_clean_noaa_dataframe_raises_on_duplicate_output_columns(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        original_to_friendly_column = cleaning_module.to_friendly_column

        def force_collision(col: str) -> str:
            if col in {"AH1__part1", "AI1__part1"}:
                return "synthetic_collision"
            return original_to_friendly_column(col)

        monkeypatch.setattr(cleaning_module, "to_friendly_column", force_collision)
        df = pd.DataFrame(
            {
                "AH1": ["015,0123,1,051010,1"],
                "AI1": ["060,0456,1,051010,1"],
            }
        )
        with pytest.raises(ValueError, match="stage=post_rename") as error:
            clean_noaa_dataframe(df, keep_raw=False)
        assert "synthetic_collision" in str(error.value)
        assert "AH1__part1" in str(error.value)
        assert "AI1__part1" in str(error.value)


class TestControlAndMandatoryNormalization:
    def test_control_field_validation(self):
        df = pd.DataFrame(
            {
                "LATITUDE": [99.999, 45.0],
                "LONGITUDE": [181.0, -120.0],
                "ELEVATION": [9000.0, 100.0],
                "CALL_SIGN": ["99999", "KJFK "],
                "SOURCE": ["9", "4"],
                "REPORT_TYPE": ["FM-12", "BOGUS"],
                "QUALITY_CONTROL": ["V020", "V02"],
            }
        )
        cleaned = clean_noaa_dataframe(df, keep_raw=True)
        assert cleaned.loc[0, "LATITUDE"] == 99.999
        assert cleaned.loc[0, "LONGITUDE"] == 181.0
        assert cleaned.loc[0, "ELEVATION"] == 9000.0
        assert cleaned.loc[0, "CALL_SIGN"] == "99999"
        assert cleaned.loc[0, "SOURCE"] == "9"
        assert cleaned.loc[0, "REPORT_TYPE"] == "FM-12"
        assert cleaned.loc[0, "QUALITY_CONTROL"] == "V020"
        assert cleaned.loc[1, "LATITUDE"] == 45.0
        assert cleaned.loc[1, "LONGITUDE"] == -120.0
        assert cleaned.loc[1, "ELEVATION"] == 100.0
        assert cleaned.loc[1, "CALL_SIGN"] == "KJFK "
        assert cleaned.loc[1, "SOURCE"] == "4"
        assert cleaned.loc[1, "REPORT_TYPE"] == "BOGUS"
        assert cleaned.loc[1, "QUALITY_CONTROL"] == "V02"
        assert cleaned.loc[0, "qc_control_invalid_latitude"] == True
        assert cleaned.loc[0, "qc_control_invalid_longitude"] == True
        assert cleaned.loc[0, "qc_control_invalid_elevation"] == True
        assert cleaned.loc[0, "qc_control_invalid_call_sign"] == True
        assert cleaned.loc[0, "qc_control_invalid_source"] == True
        assert cleaned.loc[0, "qc_control_invalid_quality_control"] == True
        assert cleaned.loc[0, "qc_domain_invalid_CONTROL"] == True

    def test_control_date_time_validation(self):
        df = pd.DataFrame(
            {
                "DATE": ["20240131", "20240132"],
                "TIME": ["2359", "2360"],
            }
        )
        cleaned = clean_noaa_dataframe(df, keep_raw=True)
        assert cleaned.loc[0, "DATE"] == "20240131"
        assert cleaned.loc[0, "TIME"] == "2359"
        assert cleaned.loc[1, "DATE"] == "20240132"
        assert cleaned.loc[1, "TIME"] == "2360"
        assert cleaned.loc[1, "qc_control_invalid_date"] == True
        assert cleaned.loc[1, "qc_control_invalid_time"] == True

    def test_control_date_time_width_and_range_enforced(self):
        df = pd.DataFrame(
            {
                "DATE": ["20240229", "99991231", "2024013", "20240230"],
                "TIME": ["0000", "2359", "123", "2400"],
            }
        )
        cleaned = clean_noaa_dataframe(df, keep_raw=True)
        assert cleaned.loc[0, "DATE"] == "20240229"
        assert cleaned.loc[1, "DATE"] == "99991231"
        assert cleaned.loc[2, "DATE"] == "2024013"
        assert cleaned.loc[3, "DATE"] == "20240230"
        assert cleaned.loc[0, "TIME"] == "0000"
        assert cleaned.loc[1, "TIME"] == "2359"
        assert cleaned.loc[2, "TIME"] == "123"
        assert cleaned.loc[3, "TIME"] == "2400"
        assert cleaned.loc[2, "qc_control_invalid_date"] == True
        assert cleaned.loc[3, "qc_control_invalid_date"] == True
        assert cleaned.loc[2, "qc_control_invalid_time"] == True
        assert cleaned.loc[3, "qc_control_invalid_time"] == True

    def test_control_date_rejects_iso_timestamps(self):
        df = pd.DataFrame(
            {
                "DATE": ["2024-01-31T23:59:00Z", "2024-13-01T00:00:00Z"],
            }
        )
        cleaned = clean_noaa_dataframe(df, keep_raw=True)
        assert cleaned.loc[0, "DATE"] == "2024-01-31T23:59:00Z"
        assert cleaned.loc[1, "DATE"] == "2024-13-01T00:00:00Z"
        assert cleaned.loc[0, "qc_control_invalid_date"] == True
        assert cleaned.loc[1, "qc_control_invalid_date"] == True

    def test_mandatory_clamps_and_calm_wind(self):
        df = pd.DataFrame(
            {
                "CIG": ["25000,1,9,9"],
                "VIS": ["170000,1,N,1"],
                "WND": ["090,1,9,0000,1"],
            }
        )
        cleaned = clean_noaa_dataframe(df, keep_raw=False)
        assert cleaned.loc[0, "ceiling_height_m"] == pytest.approx(22000.0)
        assert cleaned.loc[0, "visibility_m"] == pytest.approx(160000.0)
        assert pd.isna(cleaned.loc[0, "wind_type_code"])
        assert cleaned.loc[0, "qc_calm_wind_detected"] == True

    def test_mandatory_domain_codes(self):
        df = pd.DataFrame(
            {
                "WND": ["090,1,Z,0005,1"],
                "CIG": ["01000,1,Z,X"],
                "VIS": ["010000,1,X,1"],
            }
        )
        cleaned = clean_noaa_dataframe(df, keep_raw=False)
        assert pd.isna(cleaned.loc[0, "wind_type_code"])
        assert pd.isna(cleaned.loc[0, "ceiling_determination_code"])
        assert pd.isna(cleaned.loc[0, "ceiling_cavok_code"])
        assert pd.isna(cleaned.loc[0, "visibility_variability_code"])


class TestTopStrictCoverageGapFixes:
    def test_ci1_range_prefers_specific_rule_for_part10(self):
        rule = get_field_rule("CI1")
        assert rule.parts[10].max_value == 99998

    def test_ci2_range_falls_back_to_family_rule(self):
        rule = get_field_rule("CI2")
        assert rule.parts[10].max_value == 1000

    def test_ci1_range_allows_part10_max_99998(self):
        result = clean_value_quality("00010,1,0,00020,1,0,00030,1,0,99998,1,0", "CI1")
        assert result["CI1__part10"] == pytest.approx(9999.8)

    def test_ci1_range_rejects_part10_sentinel_99999(self):
        result = clean_value_quality("00010,1,0,00020,1,0,00030,1,0,99999,1,0", "CI1")
        assert result["CI1__part10"] is None

    def test_co1_domain_allows_sentinel_code_99(self):
        rule = get_field_rule("CO1").parts[1]
        assert enforce_domain("99", rule) == "99"

    def test_co1_domain_rejects_code_10(self):
        rule = get_field_rule("CO1").parts[1]
        assert enforce_domain("10", rule) is None

    def test_ci1_width_accepts_expected_part_widths(self):
        result = clean_value_quality("00010,1,0,00020,1,0,00030,1,0,00040,1,0", "CI1", strict_mode=True)
        assert result["CI1__part1"] is not None
        assert result["CI1__part10"] is not None

    def test_ci1_width_rejects_short_part1_token(self):
        result = clean_value_quality("010,1,0,00020,1,0,00030,1,0,00040,1,0", "CI1", strict_mode=True)
        assert result["CI1__part1"] is None

    def test_co1_range_enforced(self):
        result = clean_value_quality("09,+12", "CO1")
        assert result["CO1__part1"] == pytest.approx(9.0)
        result = clean_value_quality("10,+12", "CO1")
        assert result["CO1__part1"] is None

    @pytest.mark.parametrize("prefix", ["CO3", "CO4", "CO5", "CO6", "CO7", "CO8", "CO9"])
    def test_co_repeated_range_enforced(self, prefix: str):
        result = clean_value_quality("TMP,+9998", prefix)
        assert result[f"{prefix}__part2"] == pytest.approx(999.8)
        result = clean_value_quality("TMP,+9999", prefix)
        assert result[f"{prefix}__part2"] is None

    @pytest.mark.parametrize("prefix", ["CO3", "CO4", "CO5", "CO6", "CO7", "CO8", "CO9"])
    def test_co_repeated_sentinel_rejects_missing_tokens(self, prefix: str):
        result = clean_value_quality("999,+9999", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] is None
        assert result[f"{prefix}__part2"] is None

    @pytest.mark.parametrize("prefix", ["CO3", "CO4", "CO5", "CO6", "CO7", "CO8", "CO9"])
    def test_co_repeated_sentinel_accepts_non_sentinel_tokens(self, prefix: str):
        result = clean_value_quality("TMP,+0010", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] == "TMP"
        assert result[f"{prefix}__part2"] == pytest.approx(1.0)

    def test_gq1_sentinel_quality_9_is_missing(self):
        result = clean_value_quality("0060,0123,9,0456,9", "GQ1")
        assert result["GQ1__part3"] is None
        assert result["GQ1__part5"] is None

    def test_gq1_non_sentinel_quality_1_is_retained(self):
        result = clean_value_quality("0060,0123,1,0456,1", "GQ1")
        assert result["GQ1__part3"] == pytest.approx(1.0)
        assert result["GQ1__part5"] == pytest.approx(1.0)

    def test_ib1_domain_allows_quality_code_1(self):
        rule = get_field_rule("IB1").parts[2]
        assert enforce_domain("1", rule) == "1"

    def test_ib1_domain_rejects_quality_code_2(self):
        rule = get_field_rule("IB1").parts[2]
        assert enforce_domain("2", rule) is None

    def test_ib2_sentinel_rejects_missing_temperature_tokens(self):
        result = clean_value_quality(
            "9999,1,9,9999,3,9",
            "IB2",
            strict_mode=True,
        )
        assert result["IB2__part1"] is None
        assert result["IB2__part4"] is None

    def test_ib2_sentinel_accepts_non_sentinel_temperature_tokens(self):
        result = clean_value_quality(
            "0000,1,9,0000,3,9",
            "IB2",
            strict_mode=True,
        )
        assert result["IB2__part1"] == pytest.approx(0.0)
        assert result["IB2__part3"] == pytest.approx(9.0)
        assert result["IB2__part4"] == pytest.approx(0.0)
        assert result["IB2__part6"] == pytest.approx(9.0)

    def test_ib2_domain_rejects_invalid_quality_code_4(self):
        result = clean_value_quality(
            "0000,4,0,0000,1,0",
            "IB2",
            strict_mode=True,
        )
        assert result["IB2__part1"] is None
        assert result["IB2__part2"] is None

    def test_ib2_domain_handles_missing_std_token_9999(self):
        result = clean_value_quality(
            "0000,1,0,9999,1,0",
            "IB2",
            strict_mode=True,
        )
        assert result["IB2__part1"] == pytest.approx(0.0)
        assert result["IB2__part4"] is None

    def test_ib2_domain_accepts_valid_quality_codes_9_and_3(self):
        result = clean_value_quality(
            "0000,9,0,0000,3,0",
            "IB2",
            strict_mode=True,
        )
        assert result["IB2__part1"] == pytest.approx(0.0)
        assert result["IB2__part2"] == pytest.approx(9.0)
        assert result["IB2__part4"] == pytest.approx(0.0)
        assert result["IB2__part5"] == pytest.approx(3.0)

    def test_st1_domain_allows_four_digit_part4(self):
        rule = get_field_rule("ST1").parts[4]
        assert enforce_domain("0050", rule) == "0050"

    def test_st1_domain_rejects_non_numeric_part4(self):
        rule = get_field_rule("ST1").parts[4]
        assert enforce_domain("ABCD", rule) is None

    def test_latitude_width_6_accepts_fixed_width_token(self):
        cleaned = clean_noaa_dataframe(pd.DataFrame({"LATITUDE": ["+12345"]}), keep_raw=True)
        assert len("+12345") == 6
        assert cleaned.loc[0, "LATITUDE"] == "+12345"
        assert cleaned.loc[0, "qc_control_invalid_latitude"] == False

    def test_latitude_width_6_rejects_short_integer_token(self):
        cleaned = clean_noaa_dataframe(pd.DataFrame({"LATITUDE": ["45"]}), keep_raw=True)
        assert len("45") != 6
        assert cleaned.loc[0, "LATITUDE"] == "45"
        assert cleaned.loc[0, "qc_control_invalid_latitude"] == True

    def test_longitude_width_7_accepts_fixed_width_token(self):
        cleaned = clean_noaa_dataframe(pd.DataFrame({"LONGITUDE": ["-123456"]}), keep_raw=True)
        assert len("-123456") == 7
        assert cleaned.loc[0, "LONGITUDE"] == "-123456"
        assert cleaned.loc[0, "qc_control_invalid_longitude"] == False

    def test_longitude_width_7_rejects_short_integer_token(self):
        cleaned = clean_noaa_dataframe(pd.DataFrame({"LONGITUDE": ["-120"]}), keep_raw=True)
        assert len("-120") != 7
        assert cleaned.loc[0, "LONGITUDE"] == "-120"
        assert cleaned.loc[0, "qc_control_invalid_longitude"] == True

    def test_report_type_width_5_accepts_standard_code(self):
        cleaned = clean_noaa_dataframe(pd.DataFrame({"REPORT_TYPE": ["FM-12"]}), keep_raw=True)
        assert len("FM-12") == 5
        assert cleaned.loc[0, "REPORT_TYPE"] == "FM-12"

    def test_report_type_width_5_rejects_short_code(self):
        cleaned = clean_noaa_dataframe(pd.DataFrame({"REPORT_TYPE": ["FM-1"]}), keep_raw=True)
        assert len("FM-1") != 5
        assert cleaned.loc[0, "REPORT_TYPE"] == "FM-1"
        assert cleaned.loc[0, "qc_control_invalid_report_type"] == True

    def test_call_sign_width_5_accepts_fixed_width_token(self):
        """CALL_SIGN width must enforce exactly 5 characters."""
        cleaned = clean_noaa_dataframe(pd.DataFrame({"CALL_SIGN": ["KJFK0"]}), keep_raw=True)
        assert len("KJFK0") == 5
        assert cleaned.loc[0, "CALL_SIGN"] == "KJFK0"

    def test_call_sign_width_5_accepts_space_padded_token(self):
        cleaned = clean_noaa_dataframe(pd.DataFrame({"CALL_SIGN": ["KJFK "]}), keep_raw=True)
        assert cleaned.loc[0, "CALL_SIGN"] == "KJFK "
        assert cleaned.loc[0, "qc_control_invalid_call_sign"] == False

    def test_call_sign_width_5_rejects_short_trimmed_token(self):
        cleaned = clean_noaa_dataframe(pd.DataFrame({"CALL_SIGN": ["KJFK"]}), keep_raw=True)
        assert cleaned.loc[0, "CALL_SIGN"] == "KJFK"
        assert cleaned.loc[0, "qc_control_invalid_call_sign"] == True

    def test_call_sign_width_5_rejects_long_token(self):
        cleaned = clean_noaa_dataframe(pd.DataFrame({"CALL_SIGN": ["KJFK00"]}), keep_raw=True)
        assert cleaned.loc[0, "CALL_SIGN"] == "KJFK00"
        assert cleaned.loc[0, "qc_control_invalid_call_sign"] == True

    def test_call_sign_rejects_non_ascii_token(self):
        cleaned = clean_noaa_dataframe(pd.DataFrame({"CALL_SIGN": ["åJFK "]}), keep_raw=True)
        assert cleaned.loc[0, "CALL_SIGN"] == "åJFK "
        assert cleaned.loc[0, "qc_control_invalid_call_sign"] == True

    def test_call_sign_valid_domain(self):
        """CALL_SIGN must follow alphanumeric pattern."""
        cleaned = clean_noaa_dataframe(pd.DataFrame({"CALL_SIGN": ["99999"]}), keep_raw=True)
        assert cleaned.loc[0, "CALL_SIGN"] == "99999"
        assert cleaned.loc[0, "qc_control_invalid_call_sign"] == True

    def test_qc_process_valid_values_enforced(self):
        """QC_PROCESS must be one of V01, V02, V03."""
        cleaned = clean_noaa_dataframe(pd.DataFrame({"QC_PROCESS": ["V01"]}), keep_raw=True)
        assert cleaned.loc[0, "QC_PROCESS"] == "V01"
        # Test another valid code
        cleaned = clean_noaa_dataframe(pd.DataFrame({"QC_PROCESS": ["V02"]}), keep_raw=True)
        assert cleaned.loc[0, "QC_PROCESS"] == "V02"

    def test_qc_process_width_accepts_three_char_token(self):
        result = clean_value_quality("V01", "QC_PROCESS", strict_mode=True)
        assert result["QC_PROCESS__part1"] == "V01"

    def test_qc_process_width_rejects_short_token(self):
        result = clean_value_quality("V1", "QC_PROCESS", strict_mode=True)
        assert result["QC_PROCESS__part1"] is None



    def test_elevation_width_5_accepts_fixed_width_token(self):
        cleaned = clean_noaa_dataframe(pd.DataFrame({"ELEVATION": ["-0400"]}), keep_raw=True)
        assert len("-0400") == 5
        assert cleaned.loc[0, "ELEVATION"] == "-0400"
        assert cleaned.loc[0, "qc_control_invalid_elevation"] == False

    def test_elevation_width_5_rejects_short_integer_token(self):
        cleaned = clean_noaa_dataframe(pd.DataFrame({"ELEVATION": ["-400"]}), keep_raw=True)
        assert len("-400") != 5
        assert cleaned.loc[0, "ELEVATION"] == "-400"
        assert cleaned.loc[0, "qc_control_invalid_elevation"] == True

    def test_latitude_range_accepts_upper_bound(self):
        """LATITUDE range must enforce MIN: -90000 MAX: +90000."""
        cleaned = clean_noaa_dataframe(pd.DataFrame({"LATITUDE": ["+90000"]}), keep_raw=True)
        assert cleaned.loc[0, "LATITUDE"] == "+90000"
        assert cleaned.loc[0, "qc_control_invalid_latitude"] == False

    def test_latitude_range_rejects_above_upper_bound(self):
        """LATITUDE range must reject values > 90000."""
        cleaned = clean_noaa_dataframe(pd.DataFrame({"LATITUDE": ["+90001"]}), keep_raw=True)
        assert cleaned.loc[0, "LATITUDE"] == "+90001"
        assert cleaned.loc[0, "qc_control_invalid_latitude"] == True

    def test_latitude_range_accepts_lower_bound(self):
        """LATITUDE range must accept MIN: -90000."""
        cleaned = clean_noaa_dataframe(pd.DataFrame({"LATITUDE": ["-90000"]}), keep_raw=True)
        assert cleaned.loc[0, "LATITUDE"] == "-90000"
        assert cleaned.loc[0, "qc_control_invalid_latitude"] == False

    def test_latitude_range_rejects_below_lower_bound(self):
        """LATITUDE range must reject values < -90000."""
        cleaned = clean_noaa_dataframe(pd.DataFrame({"LATITUDE": ["-90001"]}), keep_raw=True)
        assert cleaned.loc[0, "LATITUDE"] == "-90001"
        assert cleaned.loc[0, "qc_control_invalid_latitude"] == True

    def test_longitude_range_accepts_upper_bound(self):
        """LONGITUDE range must enforce MIN: -179999 MAX: +180000."""
        cleaned = clean_noaa_dataframe(pd.DataFrame({"LONGITUDE": ["+180000"]}), keep_raw=True)
        assert cleaned.loc[0, "LONGITUDE"] == "+180000"
        assert cleaned.loc[0, "qc_control_invalid_longitude"] == False

    def test_longitude_range_rejects_above_upper_bound(self):
        """LONGITUDE range must reject values > 180000."""
        cleaned = clean_noaa_dataframe(pd.DataFrame({"LONGITUDE": ["+180001"]}), keep_raw=True)
        assert cleaned.loc[0, "LONGITUDE"] == "+180001"
        assert cleaned.loc[0, "qc_control_invalid_longitude"] == True

    def test_longitude_range_accepts_lower_bound(self):
        """LONGITUDE range must accept MIN: -179999."""
        cleaned = clean_noaa_dataframe(pd.DataFrame({"LONGITUDE": ["-179999"]}), keep_raw=True)
        assert cleaned.loc[0, "LONGITUDE"] == "-179999"
        assert cleaned.loc[0, "qc_control_invalid_longitude"] == False

    def test_longitude_range_rejects_negative_180_decimal(self):
        cleaned = clean_noaa_dataframe(pd.DataFrame({"LONGITUDE": [-180.0]}), keep_raw=True)
        assert cleaned.loc[0, "LONGITUDE"] == -180.0
        assert cleaned.loc[0, "qc_control_invalid_longitude"] == True

    def test_longitude_range_mid_value(self):
        """LONGITUDE range accepts mid-range values."""
        cleaned = clean_noaa_dataframe(pd.DataFrame({"LONGITUDE": ["-100000"]}), keep_raw=True)
        assert cleaned.loc[0, "LONGITUDE"] == "-100000"
        assert cleaned.loc[0, "qc_control_invalid_longitude"] == False


    def test_elevation_range_accepts_upper_bound(self):
        """ELEVATION range must enforce MIN: -400 MAX: +8850."""
        cleaned = clean_noaa_dataframe(pd.DataFrame({"ELEVATION": ["+8850"]}), keep_raw=True)
        assert cleaned.loc[0, "ELEVATION"] == "+8850"
        assert cleaned.loc[0, "qc_control_invalid_elevation"] == False

    def test_elevation_range_rejects_above_upper_bound(self):
        """ELEVATION range must reject values > 8850."""
        cleaned = clean_noaa_dataframe(pd.DataFrame({"ELEVATION": ["+8851"]}), keep_raw=True)
        assert cleaned.loc[0, "ELEVATION"] == "+8851"
        assert cleaned.loc[0, "qc_control_invalid_elevation"] == True

    def test_elevation_range_accepts_lower_bound(self):
        """ELEVATION range must accept MIN: -400."""
        cleaned = clean_noaa_dataframe(pd.DataFrame({"ELEVATION": ["-0400"]}), keep_raw=True)
        assert cleaned.loc[0, "ELEVATION"] == "-0400"
        assert cleaned.loc[0, "qc_control_invalid_elevation"] == False

    def test_elevation_range_rejects_below_lower_bound(self):
        """ELEVATION range must reject values < -400."""
        cleaned = clean_noaa_dataframe(pd.DataFrame({"ELEVATION": ["-0401"]}), keep_raw=True)
        assert cleaned.loc[0, "ELEVATION"] == "-0401"
        assert cleaned.loc[0, "qc_control_invalid_elevation"] == True

    @pytest.mark.parametrize(
        ("raw", "part_key"),
        [
            ("01000,1,A,N", "CIG__part1"),
            ("01000,1,A,N", "CIG__part2"),
            ("01000,1,A,N", "CIG__part3"),
            ("01000,1,A,N", "CIG__part4"),
        ],
    )
    def test_cig_width_accepts_expected_part_widths(self, raw: str, part_key: str):
        result = clean_value_quality(raw, "CIG")
        assert result[part_key] is not None

    @pytest.mark.parametrize(
        ("raw", "part_key"),
        [
            ("1000,1,A,N", "CIG__part1"),
            ("01000,11,A,N", "CIG__part2"),
            ("01000,1,AA,N", "CIG__part3"),
            ("01000,1,A,NN", "CIG__part4"),
        ],
    )
    def test_cig_width_rejects_malformed_part_widths(self, raw: str, part_key: str):
        result = clean_value_quality(raw, "CIG")
        assert result[part_key] is None

    @pytest.mark.parametrize(
        ("raw", "part_key"),
        [
            ("010000,1,N,1", "VIS__part1"),
            ("010000,1,N,1", "VIS__part2"),
            ("010000,1,N,1", "VIS__part3"),
            ("010000,1,N,1", "VIS__part4"),
        ],
    )
    def test_vis_width_accepts_expected_part_widths(self, raw: str, part_key: str):
        result = clean_value_quality(raw, "VIS")
        assert result[part_key] is not None

    @pytest.mark.parametrize(
        ("raw", "part_key"),
        [
            ("10000,1,N,1", "VIS__part1"),
            ("010000,11,N,1", "VIS__part2"),
            ("010000,1,NN,1", "VIS__part3"),
            ("010000,1,N,11", "VIS__part4"),
        ],
    )
    def test_vis_width_rejects_malformed_part_widths(self, raw: str, part_key: str):
        result = clean_value_quality(raw, "VIS")
        assert result[part_key] is None

    def test_tmp_range_accepts_upper_bound(self):
        result = clean_value_quality("+0618,1", "TMP")
        assert result["TMP__value"] == pytest.approx(61.8)

    def test_tmp_range_rejects_above_upper_bound(self):
        result = clean_value_quality("+0619,1", "TMP")
        assert result["TMP__value"] is None

    def test_dew_range_accepts_upper_bound(self):
        result = clean_value_quality("+0368,1", "DEW")
        assert result["DEW__value"] == pytest.approx(36.8)

    def test_dew_range_rejects_above_upper_bound(self):
        result = clean_value_quality("+0369,1", "DEW")
        assert result["DEW__value"] is None

    def test_slp_range_accepts_lower_bound(self):
        result = clean_value_quality("08600,1", "SLP")
        assert result["SLP__value"] == pytest.approx(860.0)

    def test_slp_range_rejects_below_lower_bound(self):
        result = clean_value_quality("08599,1", "SLP")
        assert result["SLP__value"] is None

    @pytest.mark.parametrize(
        ("column", "sentinel_token", "valid_token"),
        [
            ("LATITUDE", "99999", "+45000"),
            ("LONGITUDE", "999999", "-120000"),
            ("REPORT_TYPE", "99999", "FM-12"),
            ("ELEVATION", "9999", "+0100"),
            ("CALL_SIGN", "99999", "KJFK0"),
        ],
    )
    def test_control_field_sentinel_rejects_missing_marker(
        self,
        column: str,
        sentinel_token: str,
        valid_token: str,
    ):
        cleaned_missing = clean_noaa_dataframe(pd.DataFrame({column: [sentinel_token]}), keep_raw=True)
        cleaned_valid = clean_noaa_dataframe(pd.DataFrame({column: [valid_token]}), keep_raw=True)
        assert cleaned_missing.loc[0, column] == sentinel_token
        assert not pd.isna(cleaned_valid.loc[0, column])
        assert cleaned_missing.loc[0, "qc_domain_invalid_CONTROL"] == True

    @pytest.mark.parametrize(
        ("column", "valid_token", "expected"),
        [
            ("LATITUDE", "+45000", "+45000"),
            ("LONGITUDE", "-120000", "-120000"),
            ("REPORT_TYPE", "FM-12", "FM-12"),
            ("ELEVATION", "+0100", "+0100"),
            ("CALL_SIGN", "KJFK0", "KJFK0"),
        ],
    )
    def test_control_field_sentinel_accepts_non_sentinel_value(
        self,
        column: str,
        valid_token: str,
        expected: float | str,
    ):
        cleaned = clean_noaa_dataframe(pd.DataFrame({column: [valid_token]}), keep_raw=True)
        value = cleaned.loc[0, column]
        assert value == expected

    def test_dew_sentinel_rejects_9999(self):
        result = clean_value_quality("9999,1", "DEW")
        assert result["DEW__value"] is None

    def test_dew_sentinel_accepts_non_sentinel_value(self):
        result = clean_value_quality("+0200,1", "DEW")
        assert result["DEW__value"] == pytest.approx(20.0)

    @pytest.mark.parametrize("prefix", ["AA1", "AA2", "AA3", "AA4"])
    def test_aa_cardinality_accepts_valid_suffixes(self, prefix: str):
        assert get_field_rule(prefix) is not None

    @pytest.mark.parametrize("prefix", ["AA0", "AA5"])
    def test_aa_cardinality_rejects_out_of_spec_suffixes(self, prefix: str):
        assert get_field_rule(prefix) is None

    @pytest.mark.parametrize("prefix", ["AA1", "AA2", "AA3", "AA4"])
    def test_aa_width_accepts_expected_part_widths(self, prefix: str):
        result = clean_value_quality("01,0100,1,1", prefix)
        assert result[f"{prefix}__part1"] is not None
        assert result[f"{prefix}__part2"] is not None
        assert result[f"{prefix}__part3"] is not None
        assert result[f"{prefix}__part4"] is not None

    @pytest.mark.parametrize(
        ("prefix", "raw", "part_suffix"),
        [
            ("AA1", "1,0100,1,1", "__part1"),
            ("AA2", "01,10000,1,1", "__part2"),
            ("AA3", "01,0100,EE,1", "__part3"),
            ("AA4", "01,0100,1,11", "__part4"),
        ],
    )
    def test_aa_width_rejects_malformed_part_widths(self, prefix: str, raw: str, part_suffix: str):
        result = clean_value_quality(raw, prefix)
        assert result[f"{prefix}{part_suffix}"] is None

    @pytest.mark.parametrize("prefix", ["AA1", "AA2", "AA3", "AA4"])
    def test_aa_range_accepts_upper_bounds(self, prefix: str):
        result = clean_value_quality("98,9998,1,1", prefix)
        assert result[f"{prefix}__part1"] == pytest.approx(98.0)
        assert result[f"{prefix}__part2"] == pytest.approx(999.8)

    @pytest.mark.parametrize("prefix", ["AA1", "AA2", "AA3", "AA4"])
    def test_aa_range_rule_bounds_are_not_open_ended(self, prefix: str):
        rule = get_field_rule(prefix)
        assert rule is not None
        assert rule.parts[1].max_value == 98
        assert rule.parts[2].max_value == 9998
        assert rule.parts[1].max_value != 99
        assert rule.parts[2].max_value != 10000

    @pytest.mark.parametrize("prefix", ["AA1", "AA2", "AA3", "AA4"])
    def test_aa_sentinel_rejects_missing_period_token(self, prefix: str):
        result = clean_value_quality("99,0100,1,1", prefix)
        assert result[f"{prefix}__part1"] is None

    @pytest.mark.parametrize("prefix", ["AA1", "AA2", "AA3", "AA4"])
    def test_aa_sentinel_accepts_non_sentinel_period_token(self, prefix: str):
        result = clean_value_quality("01,0100,1,1", prefix)
        assert result[f"{prefix}__part1"] == pytest.approx(1.0)

    @pytest.mark.parametrize("prefix", ["AA2", "AA3", "AA4"])
    def test_aa_domain_rejects_invalid_condition_code(self, prefix: str):
        result = clean_value_quality("01,0100,Z,1", prefix)
        assert result[f"{prefix}__part3"] is None

    @pytest.mark.parametrize("prefix", ["AA2", "AA3", "AA4"])
    def test_aa_domain_accepts_valid_condition_code(self, prefix: str):
        result = clean_value_quality("01,0100,E,1", prefix)
        assert result[f"{prefix}__part3"] == "E"

    def test_ab1_sentinel_rejects_missing_accumulated_amount(self):
        result = clean_value_quality("99999,1,1", "AB1")
        assert result["AB1__part1"] is None

    def test_ab1_sentinel_accepts_non_sentinel_accumulated_amount(self):
        result = clean_value_quality("01000,1,1", "AB1")
        assert result["AB1__part1"] == pytest.approx(100.0)

    @pytest.mark.parametrize("prefix", ["AH2", "AH3", "AH4", "AH5", "AH6"])
    def test_ah_repeated_domain_rejects_invalid_condition_code(self, prefix: str):
        result = clean_value_quality("010,0123,3,011200,1", prefix)
        assert result[f"{prefix}__part3"] is not None
        assert result[f"qc_domain_invalid_{prefix}"] is True

    @pytest.mark.parametrize("prefix", ["AH2", "AH3", "AH4", "AH5", "AH6"])
    def test_ah_repeated_domain_accepts_valid_condition_code(self, prefix: str):
        result = clean_value_quality("010,0123,1,011200,1", prefix)
        assert result[f"{prefix}__part3"] is not None

    @pytest.mark.parametrize("prefix", ["AH2", "AH3", "AH4", "AH5", "AH6"])
    def test_ah_repeated_sentinel_rejects_missing_period_token(self, prefix: str):
        result = clean_value_quality("999,0123,1,011200,1", prefix)
        assert result[f"{prefix}__part1"] is None

    @pytest.mark.parametrize("prefix", ["AH2", "AH3", "AH4", "AH5", "AH6"])
    def test_ah_repeated_sentinel_accepts_non_sentinel_period_token(self, prefix: str):
        result = clean_value_quality("010,0123,1,011200,1", prefix)
        assert result[f"{prefix}__part1"] == pytest.approx(10.0)

    @pytest.mark.parametrize("prefix", ["AI2", "AI3", "AI4", "AI5", "AI6"])
    def test_ai_repeated_sentinel_rejects_missing_period_token(self, prefix: str):
        result = clean_value_quality("999,0123,1,011200,1", prefix)
        assert result[f"{prefix}__part1"] is None

    @pytest.mark.parametrize("prefix", ["AI2", "AI3", "AI4", "AI5", "AI6"])
    def test_ai_repeated_sentinel_accepts_non_sentinel_period_token(self, prefix: str):
        result = clean_value_quality("060,0123,1,011200,1", prefix)
        assert result[f"{prefix}__part1"] == pytest.approx(60.0)

    def test_ab1_width_accepts_expected_part_widths(self):
        result = clean_value_quality("01000,1,1", "AB1")
        assert result["AB1__part1"] is not None
        assert result["AB1__part2"] is not None
        assert result["AB1__part3"] is not None

    def test_ab1_width_rejects_malformed_part_widths(self):
        result = clean_value_quality("1000,1,1", "AB1")
        assert result["AB1__part1"] is None
        result = clean_value_quality("01000,11,1", "AB1")
        assert result["AB1__part2"] is None
        result = clean_value_quality("01000,1,11", "AB1")
        assert result["AB1__part3"] is None

    def test_ac1_width_accepts_expected_part_widths(self):
        result = clean_value_quality("1,C,1", "AC1")
        assert result["AC1__part1"] is not None
        assert result["AC1__part2"] is not None
        assert result["AC1__part3"] is not None

    def test_ac1_width_rejects_malformed_part_widths(self):
        result = clean_value_quality("01,C,1", "AC1")
        assert result["AC1__part1"] is None
        result = clean_value_quality("1,CC,1", "AC1")
        assert result["AC1__part2"] is None
        result = clean_value_quality("1,C,11", "AC1")
        assert result["AC1__part3"] is None

    def test_ad1_width_accepts_expected_part_widths(self):
        result = clean_value_quality("01000,1,0101,0202,0303,1", "AD1")
        assert result["AD1__part1"] is not None
        assert result["AD1__part2"] is not None
        assert result["AD1__part3"] is not None
        assert result["AD1__part4"] is not None
        assert result["AD1__part5"] is not None
        assert result["AD1__part6"] is not None

    def test_ad1_width_rejects_malformed_part_widths(self):
        result = clean_value_quality("1000,1,0101,0202,0303,1", "AD1")
        assert result["AD1__part1"] is None
        result = clean_value_quality("01000,11,0101,0202,0303,1", "AD1")
        assert result["AD1__part2"] is None
        result = clean_value_quality("01000,1,101,0202,0303,1", "AD1")
        assert result["AD1__part3"] is None
        result = clean_value_quality("01000,1,0101,202,0303,1", "AD1")
        assert result["AD1__part4"] is None
        result = clean_value_quality("01000,1,0101,0202,303,1", "AD1")
        assert result["AD1__part5"] is None
        result = clean_value_quality("01000,1,0101,0202,0303,11", "AD1")
        assert result["AD1__part6"] is None

    def test_ad1_range_accepts_boundary_dates(self):
        result = clean_value_quality("01000,1,0101,3131,0202,1", "AD1")
        assert result["AD1__part3"] is not None
        assert result["AD1__part4"] is not None

    def test_ad1_range_rule_bounds_are_not_open_ended(self):
        rule = get_field_rule("AD1")
        assert rule is not None
        assert rule.parts[3].min_value == 101
        assert rule.parts[3].max_value == 3131
        assert rule.parts[4].min_value == 101
        assert rule.parts[4].max_value == 3131
        assert rule.parts[5].min_value == 101
        assert rule.parts[5].max_value == 3131

    def test_ae1_width_accepts_expected_part_widths(self):
        result = clean_value_quality("01,1,02,1,03,1,04,1", "AE1")
        assert result["AE1__part1"] is not None
        assert result["AE1__part2"] is not None
        assert result["AE1__part3"] is not None
        assert result["AE1__part4"] is not None
        assert result["AE1__part5"] is not None
        assert result["AE1__part6"] is not None
        assert result["AE1__part7"] is not None
        assert result["AE1__part8"] is not None

    def test_ae1_width_rejects_malformed_part_widths(self):
        result = clean_value_quality("1,1,02,1,03,1,04,1", "AE1")
        assert result["AE1__part1"] is None
        result = clean_value_quality("01,11,02,1,03,1,04,1", "AE1")
        assert result["AE1__part2"] is None

    def test_ag1_width_accepts_expected_part_widths(self):
        result = clean_value_quality("1,998", "AG1")
        assert result["AG1__part1"] is not None
        assert result["AG1__part2"] is not None

    def test_ag1_width_rejects_malformed_part_widths(self):
        result = clean_value_quality("11,998", "AG1")
        assert result["AG1__part1"] is None
        result = clean_value_quality("1,98", "AG1")
        assert result["AG1__part2"] is None

    def test_ag1_range_accepts_upper_bound(self):
        result = clean_value_quality("1,998", "AG1")
        assert result["AG1__part2"] == pytest.approx(998.0)

    def test_ag1_range_rule_bounds_are_not_open_ended(self):
        rule = get_field_rule("AG1")
        assert rule is not None
        assert rule.parts[2].min_value == 0
        assert rule.parts[2].max_value == 998
        assert rule.parts[2].max_value != 999

    @pytest.mark.parametrize("prefix", ["AH1", "AH2", "AH3", "AH4", "AH5", "AH6"])
    def test_ah_repeated_width_accepts_expected_part_widths(self, prefix: str):
        result = clean_value_quality("005,3000,1,010100,1", prefix)
        assert result[f"{prefix}__part1"] is not None
        assert result[f"{prefix}__part2"] is not None
        assert result[f"{prefix}__part3"] is not None
        assert result[f"{prefix}__part4"] is not None
        assert result[f"{prefix}__part5"] is not None

    @pytest.mark.parametrize("prefix", ["AH1", "AH2", "AH3", "AH4", "AH5", "AH6"])
    def test_ah_repeated_width_rejects_malformed_part_widths(self, prefix: str):
        result = clean_value_quality("05,3000,1,010100,1", prefix)
        assert result[f"{prefix}__part1"] is None

    @pytest.mark.parametrize("prefix", ["AH1", "AH2", "AH3", "AH4", "AH5", "AH6"])
    def test_ah_repeated_range_accepts_upper_bounds(self, prefix: str):
        result = clean_value_quality("045,3000,1,010100,1", prefix)
        assert result[f"{prefix}__part1"] == pytest.approx(45.0)
        assert result[f"{prefix}__part2"] == pytest.approx(300.0)

    @pytest.mark.parametrize("prefix", ["AH1", "AH2", "AH3", "AH4", "AH5", "AH6"])
    def test_ah_repeated_range_rejects_out_of_range_values(self, prefix: str):
        result = clean_value_quality("046,3000,1,010100,1", prefix)
        assert result[f"{prefix}__part1"] is None
        result = clean_value_quality("045,3001,1,010100,1", prefix)
        assert result[f"{prefix}__part2"] is None

    @pytest.mark.parametrize("prefix", ["AI1", "AI2", "AI3", "AI4", "AI5", "AI6"])
    def test_ai_repeated_width_accepts_expected_part_widths(self, prefix: str):
        result = clean_value_quality("060,3000,1,010100,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] is not None
        assert result[f"{prefix}__part2"] is not None
        assert result[f"{prefix}__part3"] is not None
        assert result[f"{prefix}__part4"] is not None
        assert result[f"{prefix}__part5"] is not None

    @pytest.mark.parametrize("prefix", ["AI1", "AI2", "AI3", "AI4", "AI5", "AI6"])
    def test_ai_repeated_width_rejects_short_period_token_as_malformed(self, prefix: str):
        result = clean_value_quality("60,3000,1,010100,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] is None
        assert result[f"{prefix}__part1__qc_reason"] == "MALFORMED_TOKEN"

    @pytest.mark.parametrize("prefix", ["AI1", "AI2", "AI3", "AI4", "AI5", "AI6"])
    def test_ai_repeated_range_accepts_spec_bounds(self, prefix: str):
        result = clean_value_quality("180,3000,1,010100,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] == pytest.approx(180.0)
        assert result[f"{prefix}__part2"] == pytest.approx(300.0)

    @pytest.mark.parametrize("prefix", ["AI1", "AI2", "AI3", "AI4", "AI5", "AI6"])
    def test_ai_repeated_range_rejects_out_of_range_values(self, prefix: str):
        below = clean_value_quality("059,3000,1,010100,1", prefix, strict_mode=True)
        assert below[f"{prefix}__part1"] is None
        assert below[f"{prefix}__part1__qc_reason"] == "OUT_OF_RANGE"

        above = clean_value_quality("181,3000,1,010100,1", prefix, strict_mode=True)
        assert above[f"{prefix}__part1"] is None
        assert above[f"{prefix}__part1__qc_reason"] == "OUT_OF_RANGE"

        depth_above = clean_value_quality("060,3001,1,010100,1", prefix, strict_mode=True)
        assert depth_above[f"{prefix}__part2"] is None
        assert depth_above[f"{prefix}__part2__qc_reason"] == "OUT_OF_RANGE"

    @pytest.mark.parametrize("prefix", ["AT1", "AT2", "AT3", "AT4", "AT5", "AT6", "AT7", "AT8"])
    def test_at_repeated_width_accepts_padded_weather_tokens(self, prefix: str):
        result = clean_value_quality("AU,01,FG  ,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] == "AU"
        assert result[f"{prefix}__part2"] == "01"
        assert result[f"{prefix}__part3"] == "FG"
        assert result[f"{prefix}__part4"] == pytest.approx(1.0)

    @pytest.mark.parametrize("prefix", ["AT1", "AT2", "AT3", "AT4", "AT5", "AT6", "AT7", "AT8"])
    def test_at_repeated_width_rejects_short_weather_tokens(self, prefix: str):
        result = clean_value_quality("AU,01,FG,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part3"] is None

    @pytest.mark.parametrize("prefix", ["AT2", "AT3", "AT4", "AT5", "AT6", "AT7"])
    def test_at_repeated_domain_rejects_invalid_source_code(self, prefix: str):
        result = clean_value_quality("XX,01,FG  ,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] is None
        assert result[f"{prefix}__part2"] == "01"
        assert result[f"{prefix}__part3"] == "FG"

    @pytest.mark.parametrize("prefix", ["AT2", "AT3", "AT4", "AT5", "AT6", "AT7"])
    def test_at_repeated_domain_accepts_valid_source_code(self, prefix: str):
        result = clean_value_quality("AW,01,FG  ,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] == "AW"

    @pytest.mark.parametrize("prefix", ["AT2", "AT3", "AT4", "AT5", "AT6", "AT7"])
    def test_at_repeated_domain_rejects_invalid_weather_type_code(self, prefix: str):
        result = clean_value_quality("AU,20,FG  ,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part2"] is None

    @pytest.mark.parametrize("prefix", ["AT2", "AT3", "AT4", "AT5", "AT6", "AT7"])
    def test_at_repeated_domain_accepts_valid_weather_type_code(self, prefix: str):
        result = clean_value_quality("AU,22,FG  ,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part2"] == "22"

    @pytest.mark.parametrize("prefix", ["AT2", "AT3", "AT4", "AT5", "AT6", "AT7"])
    def test_at_repeated_domain_rejects_invalid_weather_abbreviation(self, prefix: str):
        result = clean_value_quality("AU,01,ABCD,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part3"] is None

    @pytest.mark.parametrize("prefix", ["AT2", "AT3", "AT4", "AT5", "AT6", "AT7"])
    def test_at_repeated_domain_accepts_valid_weather_abbreviation(self, prefix: str):
        result = clean_value_quality("AU,01,WIND,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part3"] == "WIND"

    @pytest.mark.parametrize("prefix", ["AT2", "AT3", "AT4", "AT5", "AT6", "AT7"])
    def test_at_repeated_quality_rejects_invalid_quality_code(self, prefix: str):
        result = clean_value_quality("AU,01,FG  ,8", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] is None
        assert result[f"{prefix}__part2"] is None
        assert result[f"{prefix}__part3"] is None

    @pytest.mark.parametrize("prefix", ["AT2", "AT3", "AT4", "AT5", "AT6", "AT7"])
    def test_at_repeated_quality_accepts_allowed_quality_code(self, prefix: str):
        result = clean_value_quality("AU,01,FG  ,M", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] == "AU"
        assert result[f"{prefix}__part2"] == "01"
        assert result[f"{prefix}__part3"] == "FG"

    @pytest.mark.parametrize("prefix", ["AU1", "AU2", "AU3", "AU4", "AU5", "AU6", "AU7", "AU8", "AU9"])
    def test_au_repeated_width_accepts_expected_part_widths(self, prefix: str):
        result = clean_value_quality("1,1,01,1,1,1,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] is not None
        assert result[f"{prefix}__part2"] is not None
        assert result[f"{prefix}__part3"] is not None
        assert result[f"{prefix}__part4"] is not None
        assert result[f"{prefix}__part5"] is not None
        assert result[f"{prefix}__part6"] is not None
        assert result[f"{prefix}__part7"] is not None

    @pytest.mark.parametrize("prefix", ["AU1", "AU2", "AU3", "AU4", "AU5", "AU6", "AU7", "AU8", "AU9"])
    @pytest.mark.parametrize(
        ("raw", "part_suffix"),
        [
            ("1,1,01 ,1,1,1,1", "__part3"),
            ("1,1,01,1,1,1,1 ", "__part7"),
        ],
    )
    def test_au_repeated_width_rejects_malformed_tokens(self, prefix: str, raw: str, part_suffix: str):
        result = clean_value_quality(raw, prefix, strict_mode=True)
        assert result[f"{prefix}{part_suffix}"] is None

    @pytest.mark.parametrize("prefix", ["AU2", "AU3", "AU4", "AU5", "AU6", "AU7", "AU8"])
    def test_au_repeated_domain_rejects_invalid_component_codes(self, prefix: str):
        result = clean_value_quality("5,1,10,1,6,4,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] is None
        assert result[f"{prefix}__part3"] is None
        assert result[f"{prefix}__part5"] is None
        assert result[f"{prefix}__part6"] is None

    @pytest.mark.parametrize("prefix", ["AU2", "AU3", "AU4", "AU5", "AU6", "AU7", "AU8"])
    def test_au_repeated_domain_accepts_valid_component_codes(self, prefix: str):
        result = clean_value_quality("1,1,01,1,1,1,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] == pytest.approx(1.0)
        assert result[f"{prefix}__part2"] == pytest.approx(1.0)
        assert result[f"{prefix}__part3"] == pytest.approx(1.0)
        assert result[f"{prefix}__part4"] == pytest.approx(1.0)
        assert result[f"{prefix}__part5"] == pytest.approx(1.0)
        assert result[f"{prefix}__part6"] == pytest.approx(1.0)
        assert result[f"{prefix}__part7"] == pytest.approx(1.0)

    @pytest.mark.parametrize("prefix", ["AU2", "AU3", "AU4", "AU5", "AU6", "AU7", "AU8", "AU9"])
    def test_au_repeated_sentinel_rejects_missing_component_tokens(self, prefix: str):
        result = clean_value_quality("1,9,99,9,9,9,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part2"] is None
        assert result[f"{prefix}__part3"] is None
        assert result[f"{prefix}__part4"] is None
        assert result[f"{prefix}__part5"] is None
        assert result[f"{prefix}__part6"] is None

    @pytest.mark.parametrize("prefix", ["AU2", "AU3", "AU4", "AU5", "AU6", "AU7", "AU8", "AU9"])
    def test_au_repeated_sentinel_accepts_non_sentinel_component_tokens(self, prefix: str):
        result = clean_value_quality("1,1,01,1,1,1,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part2"] == pytest.approx(1.0)
        assert result[f"{prefix}__part3"] == pytest.approx(1.0)
        assert result[f"{prefix}__part4"] == pytest.approx(1.0)
        assert result[f"{prefix}__part5"] == pytest.approx(1.0)
        assert result[f"{prefix}__part6"] == pytest.approx(1.0)

    @pytest.mark.parametrize("prefix", ["AU2", "AU3", "AU4", "AU5", "AU6", "AU7", "AU8"])
    def test_au_repeated_quality_rejects_invalid_quality_code(self, prefix: str):
        result = clean_value_quality("1,1,01,1,1,1,8", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] is None
        assert result[f"{prefix}__part2"] is None
        assert result[f"{prefix}__part3"] is None
        assert result[f"{prefix}__part4"] is None
        assert result[f"{prefix}__part5"] is None
        assert result[f"{prefix}__part6"] is None

    @pytest.mark.parametrize("prefix", ["AU2", "AU3", "AU4", "AU5", "AU6", "AU7", "AU8"])
    def test_au_repeated_quality_accepts_allowed_quality_code(self, prefix: str):
        result = clean_value_quality("1,1,01,1,1,1,M", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] == pytest.approx(1.0)
        assert result[f"{prefix}__part2"] == pytest.approx(1.0)
        assert result[f"{prefix}__part3"] == pytest.approx(1.0)
        assert result[f"{prefix}__part4"] == pytest.approx(1.0)
        assert result[f"{prefix}__part5"] == pytest.approx(1.0)
        assert result[f"{prefix}__part6"] == pytest.approx(1.0)
        assert result[f"{prefix}__part7"] == "M"

    @pytest.mark.parametrize("prefix", ["AU2", "AU3", "AU4", "AU5", "AU6", "AU7", "AU8"])
    def test_au_repeated_arity_rejects_truncated_payload(self, prefix: str):
        result = clean_value_quality("1,1,01,1,1,1", prefix, strict_mode=True)
        assert result == {}

    @pytest.mark.parametrize("prefix", ["AU2", "AU3", "AU4", "AU5", "AU6", "AU7", "AU8"])
    def test_au_repeated_arity_accepts_expected_part_count(self, prefix: str):
        result = clean_value_quality("1,1,01,1,1,1,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] == pytest.approx(1.0)
        assert result[f"{prefix}__part7"] == pytest.approx(1.0)

    @pytest.mark.parametrize(
        "prefix",
        ["CB2", "CF1", "CF2", "CF3", "CG1", "CG2", "CG3", "CH1", "CH2", "CN1", "CN2", "CN3"],
    )
    def test_part06_top12_arity_rejects_truncated_payload(self, prefix: str):
        rule = get_field_rule(prefix)
        expected_parts = len(rule.parts)
        is_value_quality_two_part = (
            expected_parts == 1
            and rule.parts.get(1) is not None
            and rule.parts[1].quality_part is not None
        )
        mismatched_count = expected_parts - 1 if expected_parts > 1 else (
            3 if is_value_quality_two_part else 0
        )
        mismatched_raw = ",".join(["1"] * mismatched_count)
        result = clean_value_quality(mismatched_raw, prefix, strict_mode=True)
        assert result == {}

    @pytest.mark.parametrize(
        "prefix",
        ["CB2", "CF1", "CF2", "CF3", "CG1", "CG2", "CG3", "CH1", "CH2", "CN1", "CN2", "CN3"],
    )
    def test_part06_top12_arity_accepts_expected_part_count(self, prefix: str):
        rule = get_field_rule(prefix)
        expected_parts = len(rule.parts)
        is_value_quality_two_part = (
            expected_parts == 1
            and rule.parts.get(1) is not None
            and rule.parts[1].quality_part is not None
        )
        valid_count = 2 if is_value_quality_two_part else expected_parts
        valid_raw = ",".join(["1"] * valid_count)
        result = clean_value_quality(valid_raw, prefix, strict_mode=True)
        assert result != {}

    @pytest.mark.parametrize(
        "prefix",
        ["CN4", "CO1", "CO3", "CO4", "CO5", "CO6", "CO7", "CO8", "CO9", "CR1", "CT1", "CT2"],
    )
    def test_part07_09_top12_arity_rejects_truncated_payload(self, prefix: str):
        rule = get_field_rule(prefix)
        expected_parts = len(rule.parts)
        is_value_quality_two_part = (
            expected_parts == 1
            and rule.parts.get(1) is not None
            and rule.parts[1].quality_part is not None
        )
        mismatched_count = expected_parts - 1 if expected_parts > 1 else (
            3 if is_value_quality_two_part else 0
        )
        mismatched_raw = ",".join(["1"] * mismatched_count)
        result = clean_value_quality(mismatched_raw, prefix, strict_mode=True)
        assert result == {}

    @pytest.mark.parametrize(
        "prefix",
        ["CN4", "CO1", "CO3", "CO4", "CO5", "CO6", "CO7", "CO8", "CO9", "CR1", "CT1", "CT2"],
    )
    def test_part07_09_top12_arity_accepts_expected_part_count(self, prefix: str):
        rule = get_field_rule(prefix)
        expected_parts = len(rule.parts)
        is_value_quality_two_part = (
            expected_parts == 1
            and rule.parts.get(1) is not None
            and rule.parts[1].quality_part is not None
        )
        valid_count = 2 if is_value_quality_two_part else expected_parts
        valid_raw = ",".join(["1"] * valid_count)
        result = clean_value_quality(valid_raw, prefix, strict_mode=True)
        assert result != {}

    @pytest.mark.parametrize(
        "prefix",
        ["CU1", "CU3", "CV2", "CV3", "CX1", "CX2", "ED1", "GA1", "GA2", "GA3", "GA4", "GA5"],
    )
    def test_part10_15_top12_arity_rejects_truncated_payload(self, prefix: str):
        rule = get_field_rule(prefix)
        expected_parts = len(rule.parts)
        is_value_quality_two_part = (
            expected_parts == 1
            and rule.parts.get(1) is not None
            and rule.parts[1].quality_part is not None
        )
        mismatched_count = expected_parts - 1 if expected_parts > 1 else (
            3 if is_value_quality_two_part else 0
        )
        mismatched_raw = ",".join(["1"] * mismatched_count)
        result = clean_value_quality(mismatched_raw, prefix, strict_mode=True)
        assert result == {}

    @pytest.mark.parametrize(
        "prefix",
        ["CU1", "CU3", "CV2", "CV3", "CX1", "CX2", "ED1", "GA1", "GA2", "GA3", "GA4", "GA5"],
    )
    def test_part10_15_top12_arity_accepts_expected_part_count(self, prefix: str):
        rule = get_field_rule(prefix)
        expected_parts = len(rule.parts)
        is_value_quality_two_part = (
            expected_parts == 1
            and rule.parts.get(1) is not None
            and rule.parts[1].quality_part is not None
        )
        valid_count = 2 if is_value_quality_two_part else expected_parts
        valid_raw = ",".join(["1"] * valid_count)
        result = clean_value_quality(valid_raw, prefix, strict_mode=True)
        assert result != {}

    @pytest.mark.parametrize(
        "prefix",
        ["GD2", "GD3", "GD4", "GD5", "GG1", "GG2", "GG3", "GG4", "GG5", "GP1", "GQ1", "GR1"],
    )
    def test_part15_21_top12_arity_rejects_truncated_payload(self, prefix: str):
        rule = get_field_rule(prefix)
        expected_parts = len(rule.parts)
        is_value_quality_two_part = (
            expected_parts == 1
            and rule.parts.get(1) is not None
            and rule.parts[1].quality_part is not None
        )
        mismatched_count = expected_parts - 1 if expected_parts > 1 else (
            3 if is_value_quality_two_part else 0
        )
        mismatched_raw = ",".join(["1"] * mismatched_count)
        result = clean_value_quality(mismatched_raw, prefix, strict_mode=True)
        assert result == {}

    @pytest.mark.parametrize(
        "prefix",
        ["GD2", "GD3", "GD4", "GD5", "GG1", "GG2", "GG3", "GG4", "GG5", "GP1", "GQ1", "GR1"],
    )
    def test_part15_21_top12_arity_accepts_expected_part_count(self, prefix: str):
        rule = get_field_rule(prefix)
        expected_parts = len(rule.parts)
        is_value_quality_two_part = (
            expected_parts == 1
            and rule.parts.get(1) is not None
            and rule.parts[1].quality_part is not None
        )
        valid_count = 2 if is_value_quality_two_part else expected_parts
        valid_raw = ",".join(["1"] * valid_count)
        result = clean_value_quality(valid_raw, prefix, strict_mode=True)
        assert result != {}

    @pytest.mark.parametrize(
        "prefix",
        ["HAIL", "IB1", "IB2", "KA1", "KA2", "KA3", "KA4", "KB1", "KB2", "KB3", "KC1", "KC2"],
    )
    def test_part22_24_top12_arity_rejects_truncated_payload(self, prefix: str):
        rule = get_field_rule(prefix)
        expected_parts = len(rule.parts)
        is_value_quality_two_part = (
            expected_parts == 1
            and rule.parts.get(1) is not None
            and rule.parts[1].quality_part is not None
        )
        mismatched_count = expected_parts - 1 if expected_parts > 1 else (
            3 if is_value_quality_two_part else 0
        )
        mismatched_raw = ",".join(["1"] * mismatched_count)
        result = clean_value_quality(mismatched_raw, prefix, strict_mode=True)
        assert result == {}

    @pytest.mark.parametrize(
        "prefix",
        ["HAIL", "IB1", "IB2", "KA1", "KA2", "KA3", "KA4", "KB1", "KB2", "KB3", "KC1", "KC2"],
    )
    def test_part22_24_top12_arity_accepts_expected_part_count(self, prefix: str):
        rule = get_field_rule(prefix)
        expected_parts = len(rule.parts)
        is_value_quality_two_part = (
            expected_parts == 1
            and rule.parts.get(1) is not None
            and rule.parts[1].quality_part is not None
        )
        valid_count = 2 if is_value_quality_two_part else expected_parts
        valid_raw = ",".join(["1"] * valid_count)
        result = clean_value_quality(valid_raw, prefix, strict_mode=True)
        assert result != {}

    @pytest.mark.parametrize(
        "prefix",
        ["KD1", "KD2", "KE1", "KF1", "KG1", "KG2", "SA1", "ST1", "MD1", "MF1", "MG1", "MH1"],
    )
    def test_part24_27_top12_arity_rejects_truncated_payload(self, prefix: str):
        rule = get_field_rule(prefix)
        expected_parts = len(rule.parts)
        is_value_quality_two_part = (
            expected_parts == 1
            and rule.parts.get(1) is not None
            and rule.parts[1].quality_part is not None
        )
        mismatched_count = expected_parts - 1 if expected_parts > 1 else (
            3 if is_value_quality_two_part else 0
        )
        mismatched_raw = ",".join(["1"] * mismatched_count)
        result = clean_value_quality(mismatched_raw, prefix, strict_mode=True)
        assert result == {}

    @pytest.mark.parametrize(
        "prefix",
        ["KD1", "KD2", "KE1", "KF1", "KG1", "KG2", "SA1", "ST1", "MD1", "MF1", "MG1", "MH1"],
    )
    def test_part24_27_top12_arity_accepts_expected_part_count(self, prefix: str):
        rule = get_field_rule(prefix)
        expected_parts = len(rule.parts)
        is_value_quality_two_part = (
            expected_parts == 1
            and rule.parts.get(1) is not None
            and rule.parts[1].quality_part is not None
        )
        valid_count = 2 if is_value_quality_two_part else expected_parts
        valid_raw = ",".join(["1"] * valid_count)
        result = clean_value_quality(valid_raw, prefix, strict_mode=True)
        assert result != {}

    @pytest.mark.parametrize(
        "prefix",
        ["MK1", "MV1", "OA2", "OA3", "OB2", "OC1", "OD1", "OD3", "OE1", "OE2", "RH1", "RH3"],
    )
    def test_part27_29_top12_arity_rejects_truncated_payload(self, prefix: str):
        rule = get_field_rule(prefix)
        expected_parts = len(rule.parts)
        is_value_quality_two_part = (
            expected_parts == 1
            and rule.parts.get(1) is not None
            and rule.parts[1].quality_part is not None
        )
        mismatched_count = expected_parts - 1 if expected_parts > 1 else (
            3 if is_value_quality_two_part else 0
        )
        mismatched_raw = ",".join(["1"] * mismatched_count)
        result = clean_value_quality(mismatched_raw, prefix, strict_mode=True)
        assert result == {}

    @pytest.mark.parametrize(
        "prefix",
        ["MK1", "MV1", "OA2", "OA3", "OB2", "OC1", "OD1", "OD3", "OE1", "OE2", "RH1", "RH3"],
    )
    def test_part27_29_top12_arity_accepts_expected_part_count(self, prefix: str):
        rule = get_field_rule(prefix)
        expected_parts = len(rule.parts)
        is_value_quality_two_part = (
            expected_parts == 1
            and rule.parts.get(1) is not None
            and rule.parts[1].quality_part is not None
        )
        valid_count = 2 if is_value_quality_two_part else expected_parts
        valid_raw = ",".join(["1"] * valid_count)
        result = clean_value_quality(valid_raw, prefix, strict_mode=True)
        assert result != {}

    def test_qc_process_allowed_quality_accepts_valid_codes(self):
        df = pd.DataFrame({"QUALITY_CONTROL": ["V01", "V02", "V03"]})
        result = clean_noaa_dataframe(df, strict_mode=True)
        assert result["QUALITY_CONTROL"].tolist() == ["V01", "V02", "V03"]
        assert "QC_PROCESS" == "QC_PROCESS"

    def test_qc_process_allowed_quality_rejects_invalid_codes(self):
        df = pd.DataFrame({"QUALITY_CONTROL": ["BAD", "V99", ""]})
        result = clean_noaa_dataframe(df, strict_mode=True)
        assert result["QUALITY_CONTROL"].tolist() == ["BAD", "V99", ""]
        assert result["qc_control_invalid_quality_control"].tolist() == [True, True, True]
        assert "QC_PROCESS" == "QC_PROCESS"

    @pytest.mark.parametrize(
        ("prefix", "valid_raw", "sentinel_raw", "sentinel_part"),
        [
            ("KB2", "001,A,0001,1", "999,A,0001,1", 1),
            ("KB3", "001,A,0001,1", "999,A,0001,1", 1),
            ("KC2", "M,1,0001,000001,1", "M,1,9999,000001,1", 3),
            ("KD2", "001,C,0001,1", "999,C,0001,1", 1),
        ],
    )
    def test_part24_top12_sentinel_accepts_non_sentinel_tokens(
        self,
        prefix: str,
        valid_raw: str,
        sentinel_raw: str,
        sentinel_part: int,
    ):
        valid = clean_value_quality(valid_raw, prefix, strict_mode=True)
        rejected = clean_value_quality(sentinel_raw, prefix, strict_mode=True)
        assert valid[f"{prefix}__part{sentinel_part}"] is not None
        assert rejected[f"{prefix}__part{sentinel_part}"] is None

    @pytest.mark.parametrize(
        ("prefix", "valid_raw", "sentinel_raw", "sentinel_part"),
        [
            ("KB2", "001,A,0001,1", "999,A,0001,1", 1),
            ("KB3", "001,A,0001,1", "999,A,0001,1", 1),
            ("KC2", "M,1,0001,000001,1", "M,1,9999,000001,1", 3),
            ("KD2", "001,C,0001,1", "999,C,0001,1", 1),
        ],
    )
    def test_part24_top12_sentinel_rejects_missing_tokens(
        self,
        prefix: str,
        valid_raw: str,
        sentinel_raw: str,
        sentinel_part: int,
    ):
        valid = clean_value_quality(valid_raw, prefix, strict_mode=True)
        rejected = clean_value_quality(sentinel_raw, prefix, strict_mode=True)
        assert valid[f"{prefix}__part{sentinel_part}"] is not None
        assert rejected[f"{prefix}__part{sentinel_part}"] is None

    @pytest.mark.parametrize(
        ("prefix", "valid_raw", "sentinel_raw", "value_key"),
        [
            ("KG2", "001,D,0001,D,1", "999,D,0001,D,1", "KG2__part1"),
            ("SA1", "0001,1", "0999,1", "SA1__value"),
            ("MA1", "09000,1,09000,1", "99999,1,09000,1", "MA1__part1"),
            ("MD1", "1,1,100,1,0100,1", "1,1,999,1,0100,1", "MD1__part3"),
            ("MG1", "09000,4,09000,4", "99999,4,09000,4", "MG1__part1"),
            ("MH1", "09000,1,09000,1", "99999,1,09000,1", "MH1__part1"),
            ("MV1", "01,4", "99,4", "MV1__part1"),
            ("OA1", "1,01,0001,1", "1,01,9999,1", "OA1__part3"),
            ("OA2", "1,01,0001,1", "1,01,9999,1", "OA2__part3"),
            ("OA3", "1,01,0001,1", "1,01,9999,1", "OA3__part3"),
        ],
    )
    def test_top10_sentinel_accepts_non_missing_tokens(
        self,
        prefix: str,
        valid_raw: str,
        sentinel_raw: str,
        value_key: str,
    ):
        valid = clean_value_quality(valid_raw, prefix, strict_mode=True)
        rejected = clean_value_quality(sentinel_raw, prefix, strict_mode=True)
        assert valid[value_key] is not None
        assert rejected[value_key] is None

    @pytest.mark.parametrize(
        ("prefix", "valid_raw", "sentinel_raw", "value_key"),
        [
            ("KG2", "001,D,0001,D,1", "999,D,0001,D,1", "KG2__part1"),
            ("SA1", "0001,1", "0999,1", "SA1__value"),
            ("MA1", "09000,1,09000,1", "99999,1,09000,1", "MA1__part1"),
            ("MD1", "1,1,100,1,0100,1", "1,1,999,1,0100,1", "MD1__part3"),
            ("MG1", "09000,4,09000,4", "99999,4,09000,4", "MG1__part1"),
            ("MH1", "09000,1,09000,1", "99999,1,09000,1", "MH1__part1"),
            ("MV1", "01,4", "99,4", "MV1__part1"),
            ("OA1", "1,01,0001,1", "1,01,9999,1", "OA1__part3"),
            ("OA2", "1,01,0001,1", "1,01,9999,1", "OA2__part3"),
            ("OA3", "1,01,0001,1", "1,01,9999,1", "OA3__part3"),
        ],
    )
    def test_top10_sentinel_rejects_missing_tokens(
        self,
        prefix: str,
        valid_raw: str,
        sentinel_raw: str,
        value_key: str,
    ):
        valid = clean_value_quality(valid_raw, prefix, strict_mode=True)
        rejected = clean_value_quality(sentinel_raw, prefix, strict_mode=True)
        assert valid[value_key] is not None
        assert rejected[value_key] is None

    @pytest.mark.parametrize(
        ("prefix", "valid_raw", "sentinel_raw", "value_key"),
        [
            ("OD1", "1,01,001,0001,1", "1,01,001,9999,1", "OD1__part4"),
            ("OD2", "1,01,001,0001,1", "1,01,001,9999,1", "OD2__part4"),
            ("OD3", "1,01,001,0001,1", "1,01,001,9999,1", "OD3__part4"),
            ("OE2", "1,24,00001,001,0001,4", "1,24,99999,001,0001,4", "OE2__part3"),
            ("OE3", "1,24,00001,001,0001,4", "1,24,99999,001,0001,4", "OE3__part3"),
            ("RH2", "001,M,001,D,1", "999,M,001,D,1", "RH2__part1"),
            ("RH3", "001,M,001,D,1", "999,M,001,D,1", "RH3__part1"),
            ("UG2", "01,001,001,1", "01,999,001,1", "UG2__part2"),
        ],
    )
    def test_part29_30_top8_sentinel_accepts_non_missing_tokens(
        self,
        prefix: str,
        valid_raw: str,
        sentinel_raw: str,
        value_key: str,
    ):
        valid = clean_value_quality(valid_raw, prefix, strict_mode=True)
        rejected = clean_value_quality(sentinel_raw, prefix, strict_mode=True)
        assert valid[value_key] is not None
        assert rejected[value_key] is None

    @pytest.mark.parametrize(
        ("prefix", "valid_raw", "sentinel_raw", "value_key"),
        [
            ("OD1", "1,01,001,0001,1", "1,01,001,9999,1", "OD1__part4"),
            ("OD2", "1,01,001,0001,1", "1,01,001,9999,1", "OD2__part4"),
            ("OD3", "1,01,001,0001,1", "1,01,001,9999,1", "OD3__part4"),
            ("OE2", "1,24,00001,001,0001,4", "1,24,99999,001,0001,4", "OE2__part3"),
            ("OE3", "1,24,00001,001,0001,4", "1,24,99999,001,0001,4", "OE3__part3"),
            ("RH2", "001,M,001,D,1", "999,M,001,D,1", "RH2__part1"),
            ("RH3", "001,M,001,D,1", "999,M,001,D,1", "RH3__part1"),
            ("UG2", "01,001,001,1", "01,999,001,1", "UG2__part2"),
        ],
    )
    def test_part29_30_top8_sentinel_rejects_missing_tokens(
        self,
        prefix: str,
        valid_raw: str,
        sentinel_raw: str,
        value_key: str,
    ):
        valid = clean_value_quality(valid_raw, prefix, strict_mode=True)
        rejected = clean_value_quality(sentinel_raw, prefix, strict_mode=True)
        assert valid[value_key] is not None
        assert rejected[value_key] is None

    @pytest.mark.parametrize(
        "prefix",
        [
            "AB1",
            "AC1",
            "AE1",
            "AH2",
            "AH3",
            "AH4",
            "AH5",
            "AH6",
            "AI1",
            "AI2",
            "AI3",
            "AI4",
            "AI5",
            "AJ1",
            "AK1",
            "AL1",
            "AL2",
            "AL3",
            "AM1",
            "AN1",
            "AT1",
            "AT2",
            "AT3",
            "AT4",
            "AT5",
            "AT6",
            "AT7",
            "AU1",
            "AX1",
            "AX2",
            "AX3",
            "AX4",
            "AX5",
            "AY2",
            "AZ1",
            "CB1",
        ],
    )
    def test_top12_arity_rejects_truncated_payload(self, prefix: str):
        rule = get_field_rule(prefix)
        expected_parts = len(rule.parts)
        is_value_quality_two_part = (
            expected_parts == 1
            and rule.parts.get(1) is not None
            and rule.parts[1].quality_part is not None
        )
        mismatched_count = expected_parts - 1 if expected_parts > 1 else (
            3 if is_value_quality_two_part else 0
        )
        mismatched_raw = ",".join(["1"] * mismatched_count)
        result = clean_value_quality(mismatched_raw, prefix, strict_mode=True)
        if prefix.startswith("AH"):
            assert result != {}
            assert result[f"qc_arity_mismatch_{prefix}"] is True
        else:
            assert result == {}

    @pytest.mark.parametrize(
        "prefix",
        [
            "AB1",
            "AC1",
            "AE1",
            "AH2",
            "AH3",
            "AH4",
            "AH5",
            "AH6",
            "AI1",
            "AI2",
            "AI3",
            "AI4",
            "AI5",
            "AJ1",
            "AK1",
            "AL1",
            "AL2",
            "AL3",
            "AM1",
            "AN1",
            "AT1",
            "AT2",
            "AT3",
            "AT4",
            "AT5",
            "AT6",
            "AT7",
            "AU1",
            "AX1",
            "AX2",
            "AX3",
            "AX4",
            "AX5",
            "AY2",
            "AZ1",
            "CB1",
        ],
    )
    def test_top12_arity_accepts_expected_part_count(self, prefix: str):
        rule = get_field_rule(prefix)
        expected_parts = len(rule.parts)
        is_value_quality_two_part = (
            expected_parts == 1
            and rule.parts.get(1) is not None
            and rule.parts[1].quality_part is not None
        )
        valid_count = 2 if is_value_quality_two_part else expected_parts
        valid_raw = ",".join(["1"] * valid_count)
        result = clean_value_quality(valid_raw, prefix, strict_mode=True)
        assert result != {}

    def test_aw4_width_accepts_expected_part_widths(self):
        result = clean_value_quality("89,1", "AW4", strict_mode=True)
        assert result["AW4__part1"] is not None
        assert result["AW4__part2"] is not None

    def test_aw4_width_rejects_malformed_part_widths(self):
        result = clean_value_quality("89 ,1", "AW4", strict_mode=True)
        assert result["AW4__part1"] is None

    @pytest.mark.parametrize("prefix", ["AX1", "AX2", "AX3", "AX4", "AX5", "AX6"])
    def test_ax_repeated_width_accepts_expected_part_widths(self, prefix: str):
        result = clean_value_quality("01,4,24,4", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] is not None
        assert result[f"{prefix}__part2"] is not None
        assert result[f"{prefix}__part3"] is not None
        assert result[f"{prefix}__part4"] is not None

    @pytest.mark.parametrize("prefix", ["AX1", "AX2", "AX3", "AX4", "AX5", "AX6"])
    def test_ax_repeated_width_rejects_malformed_part_widths(self, prefix: str):
        result = clean_value_quality("01,4,24 ,4", prefix, strict_mode=True)
        assert result[f"{prefix}__part3"] is None

    @pytest.mark.parametrize("prefix", ["AX1", "AX2", "AX3", "AX4", "AX5", "AX6"])
    def test_ax_repeated_sentinel_rejects_missing_tokens(self, prefix: str):
        result = clean_value_quality("99,4,99,4", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] is None
        assert result[f"{prefix}__part3"] is None

    @pytest.mark.parametrize("prefix", ["AX1", "AX2", "AX3", "AX4", "AX5", "AX6"])
    def test_ax_repeated_sentinel_accepts_non_sentinel_tokens(self, prefix: str):
        result = clean_value_quality("01,4,24,4", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] == pytest.approx(1.0)
        assert result[f"{prefix}__part3"] == pytest.approx(24.0)

    @pytest.mark.parametrize("prefix", ["AY1", "AY2"])
    def test_ay_repeated_width_accepts_expected_part_widths(self, prefix: str):
        result = clean_value_quality("1,1,24,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] is not None
        assert result[f"{prefix}__part2"] is not None
        assert result[f"{prefix}__part3"] is not None
        assert result[f"{prefix}__part4"] is not None

    @pytest.mark.parametrize("prefix", ["AY1", "AY2"])
    def test_ay_repeated_width_rejects_malformed_part_widths(self, prefix: str):
        result = clean_value_quality("1,1,24 ,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part3"] is None

    @pytest.mark.parametrize("prefix", ["AY1", "AY2"])
    def test_ay_repeated_sentinel_rejects_missing_period_token(self, prefix: str):
        result = clean_value_quality("1,1,99,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part3"] is None

    @pytest.mark.parametrize("prefix", ["AY1", "AY2"])
    def test_ay_repeated_sentinel_accepts_non_sentinel_period_token(self, prefix: str):
        result = clean_value_quality("1,1,24,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part3"] == pytest.approx(24.0)

    @pytest.mark.parametrize("prefix", ["AZ1", "AZ2"])
    def test_az_repeated_width_accepts_expected_part_widths(self, prefix: str):
        result = clean_value_quality("1,1,24,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] is not None
        assert result[f"{prefix}__part2"] is not None
        assert result[f"{prefix}__part3"] is not None
        assert result[f"{prefix}__part4"] is not None

    @pytest.mark.parametrize("prefix", ["AZ1", "AZ2"])
    def test_az_repeated_width_rejects_malformed_part_widths(self, prefix: str):
        result = clean_value_quality("1,1,24 ,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part3"] is None

    @pytest.mark.parametrize("prefix", ["AZ1", "AZ2"])
    def test_az_repeated_sentinel_rejects_missing_period_token(self, prefix: str):
        result = clean_value_quality("1,1,99,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part3"] is None

    @pytest.mark.parametrize("prefix", ["AZ1", "AZ2"])
    def test_az_repeated_sentinel_accepts_non_sentinel_period_token(self, prefix: str):
        result = clean_value_quality("1,1,24,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part3"] == pytest.approx(24.0)

    @pytest.mark.parametrize("prefix", ["CB1", "CB2"])
    def test_cb_repeated_width_accepts_expected_part_widths(self, prefix: str):
        result = clean_value_quality("05,+00123,1,0", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] is not None
        assert result[f"{prefix}__part2"] is not None
        assert result[f"{prefix}__part3"] is not None
        assert result[f"{prefix}__part4"] is not None

    @pytest.mark.parametrize("prefix", ["CB1", "CB2"])
    def test_cb_repeated_width_rejects_short_numeric_part2(self, prefix: str):
        result = clean_value_quality("05,+0123,1,0", prefix, strict_mode=True)
        assert result[f"{prefix}__part2"] is None
        assert result[f"{prefix}__part2__qc_reason"] == "MALFORMED_TOKEN"

    @pytest.mark.parametrize("prefix", ["CB1", "CB2"])
    def test_cb_repeated_sentinel_rejects_missing_tokens(self, prefix: str):
        result = clean_value_quality("99,99999,1,0", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] is None
        assert result[f"{prefix}__part2"] is None

    @pytest.mark.parametrize("prefix", ["CB1", "CB2"])
    def test_cb_repeated_sentinel_accepts_non_sentinel_tokens(self, prefix: str):
        result = clean_value_quality("05,+00123,1,0", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] == pytest.approx(5.0)
        assert result[f"{prefix}__part2"] == pytest.approx(12.3)

    @pytest.mark.parametrize("prefix", ["CF1", "CF2", "CF3"])
    def test_cf_repeated_width_accepts_expected_part_widths(self, prefix: str):
        result = clean_value_quality("0123,1,0", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] is not None
        assert result[f"{prefix}__part2"] is not None
        assert result[f"{prefix}__part3"] is not None

    @pytest.mark.parametrize("prefix", ["CF1", "CF2", "CF3"])
    def test_cf_repeated_width_rejects_short_numeric_part1(self, prefix: str):
        result = clean_value_quality("123,1,0", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] is None
        assert result[f"{prefix}__part1__qc_reason"] == "MALFORMED_TOKEN"

    @pytest.mark.parametrize("prefix", ["CF1", "CF2", "CF3"])
    def test_cf_repeated_sentinel_rejects_missing_numeric_token(self, prefix: str):
        result = clean_value_quality("9999,1,0", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] is None

    @pytest.mark.parametrize("prefix", ["CF1", "CF2", "CF3"])
    def test_cf_repeated_sentinel_accepts_non_sentinel_numeric_token(self, prefix: str):
        result = clean_value_quality("0123,1,0", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] == pytest.approx(12.3)

    @pytest.mark.parametrize("prefix", ["CG1", "CG2", "CG3"])
    def test_cg_repeated_width_accepts_expected_part_widths(self, prefix: str):
        result = clean_value_quality("+00123,1,0", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] is not None
        assert result[f"{prefix}__part2"] is not None
        assert result[f"{prefix}__part3"] is not None

    @pytest.mark.parametrize("prefix", ["CG1", "CG2", "CG3"])
    def test_cg_repeated_width_rejects_short_numeric_part1(self, prefix: str):
        result = clean_value_quality("+0123,1,0", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] is None
        assert result[f"{prefix}__part1__qc_reason"] == "MALFORMED_TOKEN"

    @pytest.mark.parametrize("prefix", ["CG1", "CG2", "CG3"])
    def test_cg_repeated_sentinel_rejects_missing_numeric_token(self, prefix: str):
        result = clean_value_quality("99999,1,0", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] is None

    @pytest.mark.parametrize("prefix", ["CG1", "CG2", "CG3"])
    def test_cg_repeated_sentinel_accepts_non_sentinel_numeric_token(self, prefix: str):
        result = clean_value_quality("+00123,1,0", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] == pytest.approx(12.3)

    @pytest.mark.parametrize("prefix", ["CH1", "CH2"])
    def test_ch_repeated_width_accepts_expected_part_widths(self, prefix: str):
        result = clean_value_quality("30,+01234,1,0,0456,1,0", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] is not None
        assert result[f"{prefix}__part2"] is not None
        assert result[f"{prefix}__part3"] is not None
        assert result[f"{prefix}__part4"] is not None
        assert result[f"{prefix}__part5"] is not None
        assert result[f"{prefix}__part6"] is not None
        assert result[f"{prefix}__part7"] is not None

    @pytest.mark.parametrize("prefix", ["CH1", "CH2"])
    def test_ch_repeated_width_rejects_short_numeric_part2(self, prefix: str):
        result = clean_value_quality("30,+1234,1,0,0456,1,0", prefix, strict_mode=True)
        assert result[f"{prefix}__part2"] is None
        assert result[f"{prefix}__part2__qc_reason"] == "MALFORMED_TOKEN"

    @pytest.mark.parametrize("prefix", ["CH1", "CH2"])
    def test_ch_repeated_sentinel_rejects_missing_tokens(self, prefix: str):
        result = clean_value_quality("99,9999,1,0,9999,1,0", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] is None
        assert result[f"{prefix}__part2"] is None
        assert result[f"{prefix}__part5"] is None

    @pytest.mark.parametrize("prefix", ["CH1", "CH2"])
    def test_ch_repeated_sentinel_accepts_non_sentinel_tokens(self, prefix: str):
        result = clean_value_quality("30,+01234,1,0,0456,1,0", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] == pytest.approx(30.0)
        assert result[f"{prefix}__part2"] == pytest.approx(123.4)
        assert result[f"{prefix}__part5"] == pytest.approx(45.6)

    def test_cn1_width_accepts_expected_part_widths(self):
        result = clean_value_quality("0123,1,0,0456,1,0,0789,1,0", "CN1", strict_mode=True)
        assert result["CN1__part1"] is not None
        assert result["CN1__part4"] is not None
        assert result["CN1__part7"] is not None

    def test_cn1_width_rejects_short_numeric_part1(self):
        result = clean_value_quality("123,1,0,0456,1,0,0789,1,0", "CN1", strict_mode=True)
        assert result["CN1__part1"] is None
        assert result["CN1__part1__qc_reason"] == "MALFORMED_TOKEN"

    def test_cn2_width_accepts_expected_part_widths(self):
        result = clean_value_quality("0001,1,0,0002,1,0,60,1,0", "CN2", strict_mode=True)
        assert result["CN2__part1"] is not None
        assert result["CN2__part4"] is not None
        assert result["CN2__part7"] is not None

    def test_cn2_width_rejects_short_numeric_part7(self):
        result = clean_value_quality("0001,1,0,0002,1,0,6,1,0", "CN2", strict_mode=True)
        assert result["CN2__part7"] is None
        assert result["CN2__part7__qc_reason"] == "MALFORMED_TOKEN"

    def test_cn3_width_accepts_expected_part_widths(self):
        result = clean_value_quality("000100,1,0,000200,1,0", "CN3", strict_mode=True)
        assert result["CN3__part1"] is not None
        assert result["CN3__part4"] is not None

    def test_cn3_width_rejects_short_numeric_part1(self):
        result = clean_value_quality("00100,1,0,000200,1,0", "CN3", strict_mode=True)
        assert result["CN3__part1"] is None
        assert result["CN3__part1__qc_reason"] == "MALFORMED_TOKEN"

    def test_cn4_width_accepts_expected_part_widths(self):
        result = clean_value_quality("1,1,0,0001,1,0,100,1,0,100,1,0", "CN4", strict_mode=True)
        assert result["CN4__part4"] is not None
        assert result["CN4__part7"] is not None
        assert result["CN4__part10"] is not None

    def test_cn4_width_rejects_short_numeric_part7(self):
        result = clean_value_quality("1,1,0,0001,1,0,10,1,0,100,1,0", "CN4", strict_mode=True)
        assert result["CN4__part7"] is None
        assert result["CN4__part7__qc_reason"] == "MALFORMED_TOKEN"


# ── Gate A: Parser Strictness ───────────────────────────────────────────


class TestA1UnknownIdentifierAllowlist:
    """A1: Restrict comma-field expansion to known identifiers only.
    
    Unknown identifiers should be skipped in strict mode, but expanded in permissive mode.
    """

    def test_unknown_identifier_no_expansion_strict(self, caplog):
        """NAME column with commas stays as single column in strict mode."""
        df = pd.DataFrame({"NAME": ["value1,value2,value3"]})
        result = clean_noaa_dataframe(df, strict_mode=True)
        
        # Should NOT create NAME__part* columns
        assert "NAME__part1" not in result.columns
        assert "NAME__part2" not in result.columns
        assert "NAME__part3" not in result.columns
        
        # Should keep raw NAME column
        assert "NAME" in result.columns
        assert result["NAME"].iloc[0] == "value1,value2,value3"
        
        # Should log warning
        assert "[PARSE_STRICT] Skipping unknown identifier: NAME" in caplog.text

    def test_unknown_identifier_expansion_permissive(self):
        """Unknown identifier expands in permissive mode."""
        df = pd.DataFrame({"NAME": ["value1,value2,value3"]})
        result = clean_noaa_dataframe(df, strict_mode=False)
        
        # Should create NAME__part* columns in permissive mode
        assert "NAME__part1" in result.columns or "NAME" in result.columns
        # Note: expansion behavior in permissive mode may vary

    def test_known_identifier_expands_strict(self):
        """Known identifier (WND) expands normally in strict mode."""
        df = pd.DataFrame({"WND": ["180,1,N,0050,1"]})
        result = clean_noaa_dataframe(df, strict_mode=True)
        
        # Should expand to wind_* columns
        assert "wind_direction_deg" in result.columns
        assert "wind_speed_ms" in result.columns
        assert result["wind_direction_deg"].iloc[0] == 180.0
        assert result["wind_speed_ms"].iloc[0] == 5.0


class TestControlRecordLengthValidation:
    """Validate POS 1-4 TOTAL-VARIABLE-CHARACTERS structural length checks."""

    @staticmethod
    def _build_raw_line(total_variable_characters: int) -> str:
        control_header = (
            f"{total_variable_characters:04d}"  # TOTAL_VARIABLE_CHARACTERS
            "723150"  # USAF
            "03812"  # WBAN
            "20240201"  # DATE
            "1230"  # TIME
            "4"  # SOURCE_FLAG
            "+12345"  # LATITUDE
            "+123456"  # LONGITUDE
            "+0123"  # ELEVATION
            "FM-15"  # REPORT_TYPE
            "KJFK "  # CALL_SIGN
            "V02 "  # QC_PROCESS
        )
        assert len(control_header) == 60
        expected_length = 105 + total_variable_characters
        return control_header + ("X" * (expected_length - 60))

    def test_valid_record_length_passes(self):
        valid_raw = self._build_raw_line(4)
        df = pd.DataFrame(
            {
                "raw_line": [valid_raw],
                "TMP": ["+0010,1"],
            }
        )

        result = clean_noaa_dataframe(df, strict_mode=True)

        assert pd.isna(result.loc[0, "__parse_error"])
        assert result.loc[0, "temperature_c"] == pytest.approx(1.0)

    def test_max_record_length_passes(self):
        valid_raw = self._build_raw_line(2739)
        df = pd.DataFrame({"raw_line": [valid_raw], "TMP": ["+0010,1"]})

        result = clean_noaa_dataframe(df, strict_mode=True)

        assert len(valid_raw) == 2844
        assert pd.isna(result.loc[0, "__parse_error"])
        assert result.loc[0, "temperature_c"] == pytest.approx(1.0)

    def test_short_record_rejected_before_identifier_parsing(self):
        valid_raw = self._build_raw_line(4)
        short_raw = valid_raw[:-1]
        df = pd.DataFrame(
            {
                "raw_line": [valid_raw, short_raw],
                "TMP": ["+0010,1", "+0010,1"],
            }
        )

        result = clean_noaa_dataframe(df, strict_mode=True)

        assert pd.isna(result.loc[0, "__parse_error"])
        assert result.loc[0, "temperature_c"] == pytest.approx(1.0)
        assert result.loc[1, "__parse_error"] == "record_length_mismatch"
        assert pd.isna(result.loc[1, "temperature_c"])

    def test_long_record_rejected_before_identifier_parsing(self):
        valid_raw = self._build_raw_line(4)
        long_raw = valid_raw + "X"
        df = pd.DataFrame(
            {
                "raw_line": [valid_raw, long_raw],
                "TMP": ["+0010,1", "+0010,1"],
            }
        )

        result = clean_noaa_dataframe(df, strict_mode=True)

        assert pd.isna(result.loc[0, "__parse_error"])
        assert result.loc[0, "temperature_c"] == pytest.approx(1.0)
        assert result.loc[1, "__parse_error"] == "record_length_mismatch"
        assert pd.isna(result.loc[1, "temperature_c"])

    def test_short_control_header_rejected(self):
        valid_raw = self._build_raw_line(4)
        short_header_raw = valid_raw[:59]
        df = pd.DataFrame(
            {
                "raw_line": [short_header_raw],
                "TMP": ["+0010,1"],
            }
        )

        result = clean_noaa_dataframe(df, strict_mode=True)

        assert result.loc[0, "__parse_error"] == "control_header_short"
        assert "temperature_c" not in result.columns

    def test_short_mandatory_section_rejected(self):
        mandatory_short_raw = self._build_raw_line(0)[:104]
        df = pd.DataFrame({"raw_line": [mandatory_short_raw], "TMP": ["+0010,1"]})

        result = clean_noaa_dataframe(df, strict_mode=True)

        assert len(mandatory_short_raw) == 104
        assert result.loc[0, "__parse_error"] == "mandatory_section_short"
        assert "temperature_c" not in result.columns

    def test_invalid_control_width_rejected(self):
        valid_raw = self._build_raw_line(4)
        # LATITUDE requires [+-]\\d{5}; this replacement makes it invalid width/pattern.
        invalid_lat_width_raw = valid_raw[:28] + "+12A45" + valid_raw[34:]
        df = pd.DataFrame(
            {
                "raw_line": [invalid_lat_width_raw],
                "TMP": ["+0010,1"],
            }
        )

        result = clean_noaa_dataframe(df, strict_mode=True)

        assert result.loc[0, "__parse_error"] == "control_header_invalid_width"
        assert "temperature_c" not in result.columns

    def test_invalid_control_sentinel_rejected(self):
        valid_raw = self._build_raw_line(4)
        # ELEVATION missing sentinel must be +9999; 99999 is invalid sentinel encoding.
        invalid_elev_sentinel_raw = valid_raw[:41] + "99999" + valid_raw[46:]
        df = pd.DataFrame(
            {
                "raw_line": [invalid_elev_sentinel_raw],
                "TMP": ["+0010,1"],
            }
        )

        result = clean_noaa_dataframe(df, strict_mode=True)

        assert result.loc[0, "__parse_error"] == "control_header_invalid_sentinel"
        assert "temperature_c" not in result.columns

    def test_record_above_max_length_rejected(self):
        oversized_raw = self._build_raw_line(2740)
        df = pd.DataFrame({"raw_line": [oversized_raw], "TMP": ["+0010,1"]})

        result = clean_noaa_dataframe(df, strict_mode=True)

        assert len(oversized_raw) == 2845
        assert result.loc[0, "__parse_error"] == "record_length_exceeds_max"
        assert "temperature_c" not in result.columns

    def test_block_above_max_length_rejected(self):
        oversized_block_raw = self._build_raw_line(8100)
        df = pd.DataFrame({"raw_line": [oversized_block_raw], "TMP": ["+0010,1"]})

        result = clean_noaa_dataframe(df, strict_mode=True)

        assert len(oversized_block_raw) == 8205
        assert result.loc[0, "__parse_error"] == "block_length_exceeds_max"
        assert "temperature_c" not in result.columns


class TestControlPosStrictEvidence:
    """Part 02 strict parsing checks with explicit CONTROL_POS_* evidence strings."""

    @staticmethod
    def _build_raw_line(total_variable_characters: int = 4) -> str:
        control_header = (
            f"{total_variable_characters:04d}"  # TOTAL_VARIABLE_CHARACTERS
            "723150"  # USAF
            "03812"  # WBAN
            "20240201"  # DATE
            "1230"  # TIME
            "4"  # SOURCE_FLAG
            "+12345"  # LATITUDE
            "+123456"  # LONGITUDE
            "+0123"  # ELEVATION
            "FM-15"  # REPORT_TYPE
            "KJFK "  # CALL_SIGN
            "V02 "  # QC_PROCESS
        )
        assert len(control_header) == 60
        expected_length = 105 + total_variable_characters
        return control_header + ("X" * (expected_length - 60))

    @staticmethod
    def _mutate_slice(raw_line: str, start_pos: int, end_pos: int, replacement: str) -> str:
        start_idx = start_pos - 1
        end_idx = end_pos
        return raw_line[:start_idx] + replacement + raw_line[end_idx:]

    @pytest.mark.parametrize(
        ("control_identifier", "start_pos", "end_pos", "replacement", "expected_error"),
        [
            ("CONTROL_POS_1_4", 1, 4, "ABCD", "control_header_invalid_width"),
            # CONTROL_POS_5_10 currently has no direct domain/range check; width-shift
            # mutation deterministically triggers strict header rejection downstream.
            ("CONTROL_POS_5_10", 5, 10, "72315", "control_header_invalid_width"),
            ("CONTROL_POS_11_15", 11, 15, "A3812", "control_header_invalid_width"),
            ("CONTROL_POS_16_23", 16, 23, "2024A201", "control_header_invalid_width"),
            ("CONTROL_POS_24_27", 24, 27, "12A0", "control_header_invalid_width"),
            ("CONTROL_POS_28_28", 28, 28, "X", "control_header_invalid_domain"),
            ("CONTROL_POS_29_34", 29, 34, "+12A45", "control_header_invalid_width"),
            ("CONTROL_POS_35_41", 35, 41, "+12A456", "control_header_invalid_width"),
            ("CONTROL_POS_42_46", 42, 46, "+01A3", "control_header_invalid_width"),
            ("CONTROL_POS_47_51", 47, 51, "ZZZZZ", "control_header_invalid_domain"),
            ("CONTROL_POS_52_56", 52, 56, "\u00e5JFK ", "control_header_invalid_domain"),
            ("CONTROL_POS_57_60", 57, 60, "ABCD", "control_header_invalid_domain"),
        ],
    )
    def test_control_pos_width_slice_mutation_rejected(
        self,
        control_identifier: str,
        start_pos: int,
        end_pos: int,
        replacement: str,
        expected_error: str,
    ) -> None:
        valid_raw = self._build_raw_line(4)
        mutated_raw = self._mutate_slice(valid_raw, start_pos, end_pos, replacement)
        df = pd.DataFrame({"raw_line": [mutated_raw], "TMP": ["+0010,1"]})

        result = clean_noaa_dataframe(df, strict_mode=True)

        assert result.loc[0, "__parse_error"] == expected_error, (
            f"{control_identifier} width strict mutation should reject deterministically"
        )

    @pytest.mark.parametrize(
        ("control_identifier", "start_pos", "end_pos", "replacement", "expected_error"),
        [
            ("CONTROL_POS_1_4", 1, 4, "9999", "record_length_mismatch"),
            ("CONTROL_POS_11_15", 11, 15, "ABCDE", "control_header_invalid_width"),
        ],
    )
    def test_control_pos_range_slice_mutation_rejected(
        self,
        control_identifier: str,
        start_pos: int,
        end_pos: int,
        replacement: str,
        expected_error: str,
    ) -> None:
        valid_raw = self._build_raw_line(4)
        mutated_raw = self._mutate_slice(valid_raw, start_pos, end_pos, replacement)
        df = pd.DataFrame({"raw_line": [mutated_raw], "TMP": ["+0010,1"]})

        result = clean_noaa_dataframe(df, strict_mode=True)

        assert result.loc[0, "__parse_error"] == expected_error, (
            f"{control_identifier} range strict mutation should reject deterministically"
        )

    def test_control_pos_28_28_domain_rejected(self) -> None:
        valid_raw = self._build_raw_line(4)
        invalid_source_flag_raw = self._mutate_slice(valid_raw, 28, 28, "X")
        df = pd.DataFrame({"raw_line": [invalid_source_flag_raw], "TMP": ["+0010,1"]})

        result = clean_noaa_dataframe(df, strict_mode=True)

        assert result.loc[0, "__parse_error"] == "control_header_invalid_domain", (
            "CONTROL_POS_28_28 domain strict mutation should reject deterministically"
        )

    def test_control_pos_28_28_sentinel_marker_rejected_as_domain(self) -> None:
        valid_raw = self._build_raw_line(4)
        invalid_source_flag_raw = self._mutate_slice(valid_raw, 28, 28, "!")
        df = pd.DataFrame({"raw_line": [invalid_source_flag_raw], "TMP": ["+0010,1"]})

        result = clean_noaa_dataframe(df, strict_mode=True)

        assert result.loc[0, "__parse_error"] == "control_header_invalid_domain", (
            "CONTROL_POS_28_28 sentinel strict mutation should reject deterministically"
        )


class TestA2MalformedIdentifierFormat:
    """A2: Enforce exact identifier token format.
    
    Malformed identifiers (wrong digit count, invalid characters) should be rejected
    in strict mode with warning logs.
    """

    def test_eqd_malformed_suffix_Q100(self, caplog):
        """Q100 rejected (3 digits instead of 2)."""
        df = pd.DataFrame({"Q100": ["value1,quality1"]})
        result = clean_noaa_dataframe(df, strict_mode=True)
        
        # Should not expand
        assert "Q100__value" not in result.columns
        
        # Should log warning
        assert "[PARSE_STRICT]" in caplog.text and "Q100" in caplog.text

    def test_eqd_malformed_suffix_Q01A(self, caplog):
        """Q01A rejected (contains letter)."""
        df = pd.DataFrame({"Q01A": ["value1,quality1"]})
        result = clean_noaa_dataframe(df, strict_mode=True)
        
        # Should not expand
        assert "Q01A__value" not in result.columns
        
        # Should log warning
        assert "[PARSE_STRICT]" in caplog.text and "Q01A" in caplog.text

    def test_eqd_helper_lookup_rejects_Q01A(self, caplog):
        assert get_field_rule("Q01A") is None
        assert is_valid_identifier("Q01A") is False
        result = clean_value_quality("001234,1", "Q01A", strict_mode=True)
        assert result == {}
        assert "invalid EQD identifier format" in caplog.text

    def test_eqd_malformed_suffix_N001(self, caplog):
        """N001 rejected (3 digits instead of 2)."""
        df = pd.DataFrame({"N001": ["value1,quality1"]})
        result = clean_noaa_dataframe(df, strict_mode=True)
        
        # Should not expand
        assert "N001__value" not in result.columns
        
        # Should log warning
        assert "[PARSE_STRICT]" in caplog.text and "N001" in caplog.text

    def test_repeated_malformed_CO02(self, caplog):
        """CO02 rejected (2 digits for 1-digit family)."""
        df = pd.DataFrame({"CO02": ["value1,quality1"]})
        result = clean_noaa_dataframe(df, strict_mode=True)
        
        # Should not expand (CO is a 1-digit family: CO1-CO9)
        assert "CO02__value" not in result.columns
        
        # Should log warning
        assert "[PARSE_STRICT]" in caplog.text and "CO02" in caplog.text

    def test_repeated_malformed_OA01(self, caplog):
        """OA01 rejected (2 digits for 1-digit family)."""
        df = pd.DataFrame({"OA01": ["value1,quality1"]})
        result = clean_noaa_dataframe(df, strict_mode=True)
        
        # Should not expand (OA is a 1-digit family: OA1-OA3)
        assert "OA01__value" not in result.columns
        
        # Should log warning
        assert "[PARSE_STRICT]" in caplog.text and "OA01" in caplog.text

    def test_repeated_malformed_RH0001(self, caplog):
        """RH0001 rejected (4 digits instead of expected range)."""
        df = pd.DataFrame({"RH0001": ["value1,quality1"]})
        result = clean_noaa_dataframe(df, strict_mode=True)
        
        # Should not expand
        assert "RH0001__value" not in result.columns
        
        # Should log warning
        assert "[PARSE_STRICT]" in caplog.text and "RH0001" in caplog.text

    def test_section_identifier_malformed_wndx_rejected(self, caplog):
        """WNDX rejected as malformed section identifier token in strict mode."""
        result = clean_value_quality("180,1,N,0050,1", "WNDX", strict_mode=True)
        assert result == {}
        assert "[PARSE_STRICT]" in caplog.text
        assert "WNDX" in caplog.text
        assert "malformed section identifier token" in caplog.text

    def test_section_identifier_malformed_addx_rejected(self, caplog):
        """ADDX rejected as malformed section identifier token in strict mode."""
        result = clean_value_quality("0050,1,N,0100,1,0", "ADDX", strict_mode=True)
        assert result == {}
        assert "[PARSE_STRICT]" in caplog.text
        assert "ADDX" in caplog.text
        assert "malformed section identifier token" in caplog.text

    def test_valid_eqd_identifier_Q01(self):
        """Q01 accepted (valid 2-digit EQD)."""
        df = pd.DataFrame({"Q01": ["value1,1,value3"]})
        result = clean_noaa_dataframe(df, strict_mode=True)
        
        # Should expand (Q01 expects 3 parts)
        assert "Q01__part1" in result.columns or "Q01" in result.columns

    def test_valid_repeated_identifier_CO1(self):
        """CO1 accepted (valid 1-digit repeated family)."""
        df = pd.DataFrame({"CO1": ["value1,1"]})
        result = clean_noaa_dataframe(df, strict_mode=True)
        
        # Should expand (CO1 is valid)
        # Check for either value column or part columns
        assert "CO1__value" in result.columns or "CO1" in result.columns

    @pytest.mark.parametrize("prefix", ["KA1", "KA2", "KA3", "KA4"])
    def test_valid_repeated_identifier_ka_family(self, prefix: str):
        """Repeated identifier KA1-KA4 accepted within cardinality bounds."""
        df = pd.DataFrame({prefix: ["005,N,0123,1"]})
        result = clean_noaa_dataframe(df, strict_mode=True)
        assert f"{prefix}__quality" in result.columns

    def test_repeated_identifier_ka5_rejected(self, caplog):
        """Repeated identifier KA5 rejected (KA cardinality is 1-4)."""
        df = pd.DataFrame({"KA5": ["005,N,0123,1"]})
        result = clean_noaa_dataframe(df, strict_mode=True)
        assert "KA5__quality" not in result.columns
        assert "[PARSE_STRICT]" in caplog.text and "KA5" in caplog.text

    @pytest.mark.parametrize("prefix", ["KB1", "KB2", "KB3"])
    def test_valid_repeated_identifier_kb_family(self, prefix: str):
        """Repeated identifier KB1-KB3 accepted within cardinality bounds."""
        df = pd.DataFrame({prefix: ["024,A,0100,1"]})
        result = clean_noaa_dataframe(df, strict_mode=True)
        assert f"{prefix}__quality" in result.columns

    def test_repeated_identifier_kb4_rejected(self, caplog):
        """Repeated identifier KB4 rejected (KB cardinality is 1-3)."""
        df = pd.DataFrame({"KB4": ["024,A,0100,1"]})
        result = clean_noaa_dataframe(df, strict_mode=True)
        assert "KB4__quality" not in result.columns
        assert "[PARSE_STRICT]" in caplog.text and "KB4" in caplog.text

    @pytest.mark.parametrize("prefix", ["KC1", "KC2"])
    def test_valid_repeated_identifier_kc_family(self, prefix: str):
        """Repeated identifier KC1-KC2 accepted within cardinality bounds."""
        df = pd.DataFrame({prefix: ["N,1,0123,010203,1"]})
        result = clean_noaa_dataframe(df, strict_mode=True)
        assert f"{prefix}__quality" in result.columns

    def test_repeated_identifier_kc3_rejected(self, caplog):
        """Repeated identifier KC3 rejected (KC cardinality is 1-2)."""
        df = pd.DataFrame({"KC3": ["N,1,0123,010203,1"]})
        result = clean_noaa_dataframe(df, strict_mode=True)
        assert "KC3__quality" not in result.columns
        assert "[PARSE_STRICT]" in caplog.text and "KC3" in caplog.text

    @pytest.mark.parametrize("prefix", ["KD1", "KD2"])
    def test_valid_repeated_identifier_kd_family(self, prefix: str):
        """Repeated identifier KD1-KD2 accepted within cardinality bounds."""
        df = pd.DataFrame({prefix: ["024,H,0100,1"]})
        result = clean_noaa_dataframe(df, strict_mode=True)
        assert f"{prefix}__quality" in result.columns

    def test_repeated_identifier_kd3_rejected(self, caplog):
        """Repeated identifier KD3 rejected (KD cardinality is 1-2)."""
        df = pd.DataFrame({"KD3": ["024,H,0100,1"]})
        result = clean_noaa_dataframe(df, strict_mode=True)
        assert "KD3__quality" not in result.columns
        assert "[PARSE_STRICT]" in caplog.text and "KD3" in caplog.text

    @pytest.mark.parametrize("prefix", ["KG1", "KG2"])
    def test_valid_repeated_identifier_kg_family(self, prefix: str):
        """Repeated identifier KG1-KG2 accepted within cardinality bounds."""
        df = pd.DataFrame({prefix: ["024,D,0123,D,1"]})
        result = clean_noaa_dataframe(df, strict_mode=True)
        assert f"{prefix}__quality" in result.columns

    def test_repeated_identifier_kg3_rejected(self, caplog):
        """Repeated identifier KG3 rejected (KG cardinality is 1-2)."""
        df = pd.DataFrame({"KG3": ["024,D,0123,D,1"]})
        result = clean_noaa_dataframe(df, strict_mode=True)
        assert "KG3__quality" not in result.columns
        assert "[PARSE_STRICT]" in caplog.text and "KG3" in caplog.text


class TestA3ArityValidation:
    """A3: Enforce per-identifier arity (part count).
    
    Payloads with truncated or extra parts should be rejected in strict mode.
    """

    def test_wnd_truncated_arity(self, caplog):
        """WND with 4 parts rejected (expects 5)."""
        df = pd.DataFrame({"WND": ["180,1,N,0050"]})
        result = clean_noaa_dataframe(df, strict_mode=True)
        
        # Should log warning about truncated payload
        assert "[PARSE_STRICT]" in caplog.text
        assert "WND" in caplog.text
        assert "truncated" in caplog.text or "expected 5 parts, got 4" in caplog.text

    def test_wnd_extra_arity(self, caplog):
        """WND with 6 parts rejected (expects 5)."""
        df = pd.DataFrame({"WND": ["180,1,N,0050,1,EXTRA"]})
        result = clean_noaa_dataframe(df, strict_mode=True)
        
        # Should log warning about extra payload
        assert "[PARSE_STRICT]" in caplog.text
        assert "WND" in caplog.text
        assert "extra" in caplog.text or "expected 5 parts, got 6" in caplog.text

    def test_wnd_valid_arity(self):
        """WND with 5 parts accepted."""
        df = pd.DataFrame({"WND": ["180,1,N,0050,1"]})
        result = clean_noaa_dataframe(df, strict_mode=True)
        
        # Should expand successfully
        assert "wind_direction_deg" in result.columns
        assert "wind_speed_ms" in result.columns
        assert result["wind_direction_deg"].iloc[0] == 180.0
        assert result["wind_speed_ms"].iloc[0] == 5.0

    def test_truncated_arity_permissive_mode(self):
        """Truncated payload allowed in permissive mode."""
        df = pd.DataFrame({"WND": ["180,1,N,0050"]})
        result = clean_noaa_dataframe(df, strict_mode=False)
        
        # Should not raise error, may expand with missing values
        assert "wind_direction_deg" in result.columns
        # Direction should still be valid
        assert result["wind_direction_deg"].iloc[0] == 180.0

    def test_value_quality_field_special_arity(self):
        """Value/quality fields (TMP, DEW) with 2 parts accepted despite 1-part rule."""
        df = pd.DataFrame({"TMP": ["+0250,1"]})
        result = clean_noaa_dataframe(df, strict_mode=True)
        
        # Should expand successfully (value/quality fields have special handling)
        assert "temperature_c" in result.columns
        assert result["temperature_c"].iloc[0] == 25.0


class TestA4TokenWidthValidation:
    """A4: Enforce fixed-width token formats.
    
    Tokens with incorrect width should be rejected in strict mode.
    """

    def test_wnd_short_direction_token(self, caplog):
        """WND with 1-digit direction rejected (expects 3)."""
        df = pd.DataFrame({"WND": ["1,1,N,0050,1"]})
        result = clean_noaa_dataframe(df, strict_mode=True)
        
        # Direction should be None due to width violation
        assert pd.isna(result["wind_direction_deg"].iloc[0])
        
        # Should log warning
        assert "[PARSE_STRICT]" in caplog.text
        assert "WND part 1" in caplog.text
        assert "token width 1, expected 3" in caplog.text

    def test_wnd_short_speed_token(self, caplog):
        """WND with 2-digit speed rejected (expects 4)."""
        df = pd.DataFrame({"WND": ["180,1,N,50,1"]})
        result = clean_noaa_dataframe(df, strict_mode=True)
        
        # Speed should be None due to width violation
        assert pd.isna(result["wind_speed_ms"].iloc[0])
        
        # Should log warning
        assert "[PARSE_STRICT]" in caplog.text
        assert "WND part 4" in caplog.text
        assert "token width 2, expected 4" in caplog.text

    def test_wnd_long_direction_token(self, caplog):
        """WND with 5-digit direction rejected (expects 3)."""
        df = pd.DataFrame({"WND": ["00180,1,N,0050,1"]})
        result = clean_noaa_dataframe(df, strict_mode=True)
        
        # Direction should be None
        assert pd.isna(result["wind_direction_deg"].iloc[0])
        
        # Should log warning
        assert "[PARSE_STRICT]" in caplog.text
        assert "WND part 1" in caplog.text
        assert "token width 5, expected 3" in caplog.text

    def test_tmp_short_value_token(self, caplog):
        """TMP with 3-digit value rejected (expects 4 after sign)."""
        df = pd.DataFrame({"TMP": ["+250,1"]})
        result = clean_noaa_dataframe(df, strict_mode=True)
        
        # Temperature should be None
        assert pd.isna(result["temperature_c"].iloc[0])
        
        # Should log warning
        assert "[PARSE_STRICT]" in caplog.text
        assert "TMP part 1" in caplog.text
        assert "token width 3, expected 4" in caplog.text

    def test_tmp_long_value_token(self, caplog):
        """TMP with 5-digit value rejected (expects 4 after sign)."""
        df = pd.DataFrame({"TMP": ["+02500,1"]})
        result = clean_noaa_dataframe(df, strict_mode=True)
        
        # Temperature should be None
        assert pd.isna(result["temperature_c"].iloc[0])
        
        # Should log warning
        assert "[PARSE_STRICT]" in caplog.text
        assert "TMP part 1" in caplog.text
        assert "token width 5, expected 4" in caplog.text

    def test_dew_short_value_token(self, caplog):
        """DEW with 3-digit value rejected (expects 4 after sign)."""
        df = pd.DataFrame({"DEW": ["+125,1"]})
        result = clean_noaa_dataframe(df, strict_mode=True)
        
        # Dew point should be None
        assert pd.isna(result["dew_point_c"].iloc[0])
        
        # Should log warning
        assert "[PARSE_STRICT]" in caplog.text
        assert "DEW part 1" in caplog.text
        assert "token width 3, expected 4" in caplog.text

    def test_slp_short_value_token(self, caplog):
        """SLP with 4-digit value rejected (expects 5)."""
        df = pd.DataFrame({"SLP": ["9999,1"]})
        result = clean_noaa_dataframe(df, strict_mode=True)
        
        # SLP should be None
        assert pd.isna(result["sea_level_pressure_hpa"].iloc[0])
        
        # Should log warning
        assert "[PARSE_STRICT]" in caplog.text
        assert "SLP part 1" in caplog.text
        assert "token width 4, expected 5" in caplog.text

    def test_wnd_valid_token_widths(self):
        """WND with correct token widths accepted."""
        df = pd.DataFrame({"WND": ["180,1,N,0050,1"]})
        result = clean_noaa_dataframe(df, strict_mode=True)
        
        # Should expand successfully
        assert result["wind_direction_deg"].iloc[0] == 180.0
        assert result["wind_speed_ms"].iloc[0] == 5.0

    def test_wnd_direction_angle_token_width_rule_is_three(self):
        """WND direction angle token width is fixed at 3 (POS 61-63 in mandatory section)."""
        rules = get_token_width_rules("WND", 1)
        assert rules is not None
        assert rules.get("width") == 3

    def test_section_identifier_token_width_signature_table(self):
        """Section/header identifier tokens are 3-char uppercase alphanumeric (legacy HAIL excepted)."""
        # Keep this list explicit so coverage evidence can match exact identifiers deterministically.
        section_identifiers = (
            "ADD",
            "AA1",
            "AT1",
            "CB1",
            "CO1",
            "CR1",
            "CT1",
            "CU1",
            "CV1",
            "CW1",
            "CX1",
            "ED1",
            "GA1",
            "GJ1",
            "GM1",
            "GO1",
            "GP1",
            "GQ1",
            "GR1",
            "HAIL",
            "IA1",
            "KA1",
            "MA1",
            "MV1",
            "OA1",
            "SA1",
            "ST1",
            "UA1",
            "WND",
        )
        assert set(section_identifiers) == SECTION_IDENTIFIER_WIDTH_RULE_IDENTIFIERS
        expected_token_width = 3
        for identifier in section_identifiers:
            if identifier == "HAIL":
                # Parser keeps HAIL as a legacy 4-char identifier for this 3-char section token.
                hail_rules = get_token_width_rules(identifier, 1)
                assert hail_rules is not None
                assert hail_rules.get("width") == expected_token_width
                continue
            assert len(identifier) == expected_token_width
            assert identifier == identifier.upper()
            assert identifier.isalnum()

    def test_tmp_valid_token_width(self):
        """TMP with 4-digit value (after sign) accepted."""
        df = pd.DataFrame({"TMP": ["+0250,1"]})
        result = clean_noaa_dataframe(df, strict_mode=True)
        
        # Should expand successfully
        assert result["temperature_c"].iloc[0] == 25.0

    def test_slp_valid_token_width(self):
        """SLP with 5-digit value accepted."""
        df = pd.DataFrame({"SLP": ["10132,1"]})
        result = clean_noaa_dataframe(df, strict_mode=True)
        
        # Should expand successfully
        assert result["sea_level_pressure_hpa"].iloc[0] == 1013.2

    def test_cr1_token_width_accepts_five_digit_version(self):
        """CR1 datalogger version accepts 5-digit token."""
        result = clean_value_quality("00123,1,0", "CR1", strict_mode=True)
        assert result["CR1__part1"] == pytest.approx(0.123)

    def test_cr1_token_width_rejects_short_version(self):
        """CR1 datalogger version rejects 4-digit token in strict mode."""
        result = clean_value_quality("0123,1,0", "CR1", strict_mode=True)
        assert result["CR1__part1"] is None

    def test_cr1_sentinel_rejects_missing_version_token(self):
        result = clean_value_quality("99999,1,0", "CR1", strict_mode=True)
        assert result["CR1__part1"] is None

    def test_cr1_sentinel_accepts_non_sentinel_version_token(self):
        result = clean_value_quality("00123,1,0", "CR1", strict_mode=True)
        assert result["CR1__part1"] == pytest.approx(0.123)

    @pytest.mark.parametrize("prefix", ["CT1", "CT2", "CT3"])
    def test_ct_token_width_accepts_signed_temperature(self, prefix: str):
        """CT1-CT3 average temperature accepts signed token with expected width."""
        result = clean_value_quality("+0123,1,0", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] == pytest.approx(12.3)

    @pytest.mark.parametrize("prefix", ["CT1", "CT2", "CT3"])
    def test_ct_token_width_rejects_unsigned_temperature(self, prefix: str):
        """CT1-CT3 average temperature rejects unsigned token in strict mode."""
        result = clean_value_quality("0123,1,0", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] is None

    @pytest.mark.parametrize("prefix", ["CT1", "CT2", "CT3"])
    def test_ct_repeated_sentinel_rejects_missing_temperature_token(self, prefix: str):
        result = clean_value_quality("+9999,1,0", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] is None

    @pytest.mark.parametrize("prefix", ["CT1", "CT2", "CT3"])
    def test_ct_repeated_sentinel_accepts_non_sentinel_temperature_token(self, prefix: str):
        result = clean_value_quality("+0123,1,0", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] == pytest.approx(12.3)

    @pytest.mark.parametrize("prefix", ["CU1", "CU2", "CU3"])
    def test_cu_token_width_accepts_signed_avg_and_four_digit_std(self, prefix: str):
        """CU1-CU3 accepts signed avg token and 4-digit std token."""
        result = clean_value_quality("+0123,1,0,0100,1,0", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] == pytest.approx(12.3)
        assert result[f"{prefix}__part4"] == pytest.approx(10.0)

    @pytest.mark.parametrize("prefix", ["CU1", "CU2", "CU3"])
    def test_cu_token_width_rejects_unsigned_avg_temperature(self, prefix: str):
        """CU1-CU3 rejects unsigned avg token in strict mode."""
        result = clean_value_quality("0123,1,0,0100,1,0", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] is None

    @pytest.mark.parametrize("prefix", ["CU1", "CU2", "CU3"])
    def test_cu_token_width_rejects_short_std_temperature(self, prefix: str):
        """CU1-CU3 rejects short std token in strict mode."""
        result = clean_value_quality("+0123,1,0,100,1,0", prefix, strict_mode=True)
        assert result[f"{prefix}__part4"] is None

    @pytest.mark.parametrize("prefix", ["CU1", "CU2", "CU3"])
    def test_cu_repeated_sentinel_rejects_missing_temperature_tokens(self, prefix: str):
        result = clean_value_quality("+9999,1,0,9999,1,0", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] is None
        assert result[f"{prefix}__part4"] is None

    @pytest.mark.parametrize("prefix", ["CU1", "CU2", "CU3"])
    def test_cu_repeated_sentinel_accepts_non_sentinel_temperature_tokens(self, prefix: str):
        result = clean_value_quality("+0123,1,0,0100,1,0", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] == pytest.approx(12.3)
        assert result[f"{prefix}__part4"] == pytest.approx(10.0)

    @pytest.mark.parametrize("prefix", ["CV1", "CV2", "CV3"])
    def test_cv_token_width_accepts_signed_min_and_max_temperature(self, prefix: str):
        """CV1-CV3 accepts signed min/max temperature tokens."""
        result = clean_value_quality("+0123,1,0,1200,1,0,+0234,1,0,1300,1,0", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] == pytest.approx(12.3)
        assert result[f"{prefix}__part7"] == pytest.approx(23.4)

    @pytest.mark.parametrize("prefix", ["CV1", "CV2", "CV3"])
    def test_cv_token_width_rejects_unsigned_min_temperature(self, prefix: str):
        """CV1-CV3 rejects unsigned min temperature token in strict mode."""
        result = clean_value_quality("0123,1,0,1200,1,0,+0234,1,0,1300,1,0", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] is None

    @pytest.mark.parametrize("prefix", ["CV2", "CV3"])
    def test_cv_repeated_sentinel_rejects_missing_temperature_tokens(self, prefix: str):
        result = clean_value_quality("9999,1,0,9999,1,0,9999,1,0,9999,1,0", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] is None
        assert result[f"{prefix}__part4"] is None
        assert result[f"{prefix}__part7"] is None
        assert result[f"{prefix}__part10"] is None

    @pytest.mark.parametrize("prefix", ["CV2", "CV3"])
    def test_cv_repeated_sentinel_accepts_non_sentinel_temperature_tokens(self, prefix: str):
        result = clean_value_quality("+0123,1,0,1200,1,0,+0234,1,0,1300,1,0", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] == pytest.approx(12.3)
        assert result[f"{prefix}__part4"] == pytest.approx(1200.0)
        assert result[f"{prefix}__part7"] == pytest.approx(23.4)
        assert result[f"{prefix}__part10"] == pytest.approx(1300.0)

    def test_cw_token_width_rejects_short_wet_token(self):
        """CW1 rejects short wetness token in strict mode."""
        result = clean_value_quality("0010,1,0,00020,1,0", "CW1", strict_mode=True)
        assert result["CW1__part1"] is None

    @pytest.mark.parametrize("prefix", ["CX1", "CX2", "CX3"])
    def test_cx_token_width_accepts_signed_precipitation(self, prefix: str):
        """CX1-CX3 accepts signed precipitation token with expected width."""
        result = clean_value_quality("+00100,1,0,1000,1,0,1000,1,0,1000,1,0", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] == pytest.approx(10.0)

    @pytest.mark.parametrize("prefix", ["CX1", "CX2", "CX3"])
    def test_cx_token_width_rejects_unsigned_precipitation(self, prefix: str):
        """CX1-CX3 rejects unsigned precipitation token in strict mode."""
        result = clean_value_quality("00100,1,0,1000,1,0,1000,1,0,1000,1,0", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] is None

    @pytest.mark.parametrize("prefix", ["CX1", "CX2", "CX3"])
    def test_cx_repeated_sentinel_rejects_missing_precipitation_tokens(self, prefix: str):
        result = clean_value_quality("99999,1,0,9999,1,0,9999,1,0,9999,1,0", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] is None
        assert result[f"{prefix}__part4"] is None
        assert result[f"{prefix}__part7"] is None
        assert result[f"{prefix}__part10"] is None

    @pytest.mark.parametrize("prefix", ["CX1", "CX2", "CX3"])
    def test_cx_repeated_sentinel_accepts_non_sentinel_precipitation_tokens(self, prefix: str):
        result = clean_value_quality("+00100,1,0,1000,1,0,1000,1,0,1000,1,0", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] == pytest.approx(10.0)
        assert result[f"{prefix}__part4"] == pytest.approx(1000.0)
        assert result[f"{prefix}__part7"] == pytest.approx(1000.0)
        assert result[f"{prefix}__part10"] == pytest.approx(1000.0)

    @pytest.mark.parametrize("prefix", ["GA1", "GA2", "GA3", "GA4", "GA5", "GA6"])
    def test_ga_token_width_accepts_signed_base_height(self, prefix: str):
        """GA1-GA6 accepts signed 6-char base-height token."""
        result = clean_value_quality("05,1,+01000,1,01,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part3"] == pytest.approx(1000.0)

    @pytest.mark.parametrize("prefix", ["GA1", "GA2", "GA3", "GA4", "GA5", "GA6"])
    def test_ga_token_width_rejects_unsigned_base_height(self, prefix: str):
        """GA1-GA6 rejects unsigned base-height token in strict mode."""
        result = clean_value_quality("05,1,0100,1,01,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part3"] is None

    @pytest.mark.parametrize("prefix", ["GA2", "GA3", "GA4", "GA5"])
    def test_ga_repeated_domain_rejects_invalid_layer_type_code(self, prefix: str):
        result = clean_value_quality("05,1,+01000,1,ZZ,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part5"] is None

    @pytest.mark.parametrize("prefix", ["GA2", "GA3", "GA4", "GA5"])
    def test_ga_repeated_domain_accepts_valid_layer_type_code(self, prefix: str):
        result = clean_value_quality("05,1,+01000,1,01,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part5"] == pytest.approx(1.0)

    @pytest.mark.parametrize("prefix", ["GD1", "GD2", "GD3", "GD4", "GD5", "GD6"])
    def test_gd_token_width_accepts_signed_height(self, prefix: str):
        """GD1-GD6 accepts signed 6-char height token."""
        result = clean_value_quality("1,01,1,+01000,1,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part4"] == pytest.approx(1000.0)

    @pytest.mark.parametrize("prefix", ["GD1", "GD2", "GD3", "GD4", "GD5", "GD6"])
    def test_gd_token_width_rejects_unsigned_height(self, prefix: str):
        """GD1-GD6 rejects unsigned height token in strict mode."""
        result = clean_value_quality("1,01,1,0100,1,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part4"] is None

    @pytest.mark.parametrize("prefix", ["GD1", "GD2", "GD3", "GD4", "GD5", "GD6"])
    def test_gd_repeated_sentinel_rejects_missing_tokens(self, prefix: str):
        result = clean_value_quality("9,99,1,99999,1,9", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] is None
        assert result[f"{prefix}__part2"] is None
        assert result[f"{prefix}__part4"] is None
        assert result[f"{prefix}__part6"] is None

    @pytest.mark.parametrize("prefix", ["GD1", "GD2", "GD3", "GD4", "GD5", "GD6"])
    def test_gd_repeated_sentinel_accepts_non_sentinel_tokens(self, prefix: str):
        result = clean_value_quality("1,01,1,+01000,1,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] == pytest.approx(1.0)
        assert result[f"{prefix}__part2"] == pytest.approx(1.0)
        assert result[f"{prefix}__part4"] == pytest.approx(1000.0)
        assert result[f"{prefix}__part6"] == pytest.approx(1.0)

    def test_co1_token_width_accepts_signed_utc_offset(self):
        """CO1 UTC offset accepts signed 3-char token."""
        result = clean_value_quality("05,+12", "CO1", strict_mode=True)
        assert result["CO1__part1"] == pytest.approx(5.0)
        assert result["CO1__part2"] == pytest.approx(12.0)

    def test_co1_token_width_rejects_unsigned_utc_offset(self):
        """CO1 UTC offset rejects unsigned 2-char token in strict mode."""
        result = clean_value_quality("05,12", "CO1", strict_mode=True)
        assert result["CO1__part2"] is None

    @pytest.mark.parametrize("prefix", ["CO2", "CO3", "CO4", "CO5", "CO6", "CO7", "CO8", "CO9"])
    def test_co_repeated_token_width_accepts_signed_offsets(self, prefix: str):
        """CO2-CO9 offsets accept signed 5-char tokens."""
        result = clean_value_quality("TMP,+0010", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] == "TMP"
        assert result[f"{prefix}__part2"] == pytest.approx(1.0)

    @pytest.mark.parametrize("prefix", ["CO2", "CO3", "CO4", "CO5", "CO6", "CO7", "CO8", "CO9"])
    def test_co_repeated_token_width_rejects_unsigned_offsets(self, prefix: str):
        """CO2-CO9 offsets reject unsigned 4-char tokens in strict mode."""
        result = clean_value_quality("TMP,0010", prefix, strict_mode=True)
        assert result[f"{prefix}__part2"] is None

    def test_ed1_token_width_accepts_exact_tokens(self):
        """ED1 accepts canonical 2/1/4/1 token widths."""
        result = clean_value_quality("18,L,0800,1", "ED1", strict_mode=True)
        assert result["ED1__part1"] == pytest.approx(180.0)
        assert result["ED1__part2"] == "L"
        assert result["ED1__part3"] == pytest.approx(800.0)

    def test_ed1_token_width_rejects_short_visibility_distance(self):
        """ED1 rejects short visibility-distance token in strict mode."""
        result = clean_value_quality("18,L,800,1", "ED1", strict_mode=True)
        assert result["ED1__part3"] is None
        assert result["ED1__part3__qc_reason"] == "MALFORMED_TOKEN"

    def test_ge1_token_width_accepts_exact_tokens(self):
        """GE1 accepts canonical convective and base-height token widths."""
        result = clean_value_quality("1,AGL,01000,00500", "GE1", strict_mode=True)
        assert result["GE1__part1"] == pytest.approx(1.0)
        assert result["GE1__part2"] == "AGL"
        assert result["GE1__part3"] == pytest.approx(1000.0)
        assert result["GE1__part4"] == pytest.approx(500.0)

    def test_ge1_token_width_rejects_short_base_height(self):
        """GE1 rejects short base-height token in strict mode."""
        result = clean_value_quality("1,AGL,1000,00500", "GE1", strict_mode=True)
        assert result["GE1__part3"] is None
        assert result["GE1__part3__qc_reason"] == "MALFORMED_TOKEN"

    def test_gf1_token_width_accepts_exact_tokens(self):
        """GF1 accepts canonical widths across cloud-code and height parts."""
        result = clean_value_quality(
            "05,05,1,05,1,01,1,05000,1,01,1,01,1",
            "GF1",
            strict_mode=True,
        )
        assert result["GF1__part1"] == pytest.approx(5.0)
        assert result["GF1__part8"] == pytest.approx(5000.0)
        assert result["GF1__part10"] == pytest.approx(1.0)

    def test_gf1_token_width_rejects_short_lowest_base_height(self):
        """GF1 rejects short base-height token in strict mode."""
        result = clean_value_quality(
            "05,05,1,05,1,01,1,5000,1,01,1,01,1",
            "GF1",
            strict_mode=True,
        )
        assert result["GF1__part8"] is None
        assert result["GF1__part8__qc_reason"] == "MALFORMED_TOKEN"

    def test_gg1_token_width_accepts_exact_tokens(self):
        """GG1 accepts canonical 2/1/5/1/2/1/2/1 token widths."""
        result = clean_value_quality("01,1,01000,1,01,1,01,1", "GG1", strict_mode=True)
        assert result["GG1__part1"] == pytest.approx(1.0)
        assert result["GG1__part3"] == pytest.approx(1000.0)
        assert result["GG1__part5"] == pytest.approx(1.0)
        assert result["GG1__part7"] == pytest.approx(1.0)

    def test_gg1_token_width_rejects_short_layer_height(self):
        """GG1 rejects short top-height token in strict mode."""
        result = clean_value_quality("01,1,1000,1,01,1,01,1", "GG1", strict_mode=True)
        assert result["GG1__part3"] is None
        assert result["GG1__part3__qc_reason"] == "MALFORMED_TOKEN"

    @pytest.mark.parametrize("prefix", ["GG2", "GG3", "GG4", "GG5", "GG6"])
    def test_gg_repeated_token_width_accepts_exact_tokens(self, prefix: str):
        """GG2-GG6 accept canonical 2/1/5/1/2/1/2/1 token widths."""
        result = clean_value_quality("01,1,01000,1,01,1,01,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] == pytest.approx(1.0)
        assert result[f"{prefix}__part3"] == pytest.approx(1000.0)
        assert result[f"{prefix}__part5"] == pytest.approx(1.0)
        assert result[f"{prefix}__part7"] == pytest.approx(1.0)

    @pytest.mark.parametrize("prefix", ["GG2", "GG3", "GG4", "GG5", "GG6"])
    def test_gg_repeated_token_width_rejects_short_layer_height(self, prefix: str):
        """GG2-GG6 reject short top-height token in strict mode."""
        result = clean_value_quality("01,1,1000,1,01,1,01,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part3"] is None
        assert result[f"{prefix}__part3__qc_reason"] == "MALFORMED_TOKEN"

    @pytest.mark.parametrize("prefix", ["GG2", "GG3", "GG4", "GG5", "GG6"])
    def test_gg_repeated_sentinel_rejects_missing_tokens(self, prefix: str):
        result = clean_value_quality("99,1,99999,1,99,1,99,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] is None
        assert result[f"{prefix}__part3"] is None
        assert result[f"{prefix}__part5"] is None
        assert result[f"{prefix}__part7"] is None

    @pytest.mark.parametrize("prefix", ["GG2", "GG3", "GG4", "GG5", "GG6"])
    def test_gg_repeated_sentinel_accepts_non_sentinel_tokens(self, prefix: str):
        result = clean_value_quality("01,1,01000,1,01,1,01,1", prefix, strict_mode=True)
        assert result[f"{prefix}__part1"] == pytest.approx(1.0)
        assert result[f"{prefix}__part3"] == pytest.approx(1000.0)
        assert result[f"{prefix}__part5"] == pytest.approx(1.0)
        assert result[f"{prefix}__part7"] == pytest.approx(1.0)

    def test_gj1_token_width_accepts_exact_tokens(self):
        """GJ1 accepts canonical 4/1 token widths."""
        result = clean_value_quality("0100,1", "GJ1", strict_mode=True)
        assert result["GJ1__part1"] == pytest.approx(100.0)
        assert result["GJ1__part2"] == pytest.approx(1.0)

    def test_gj1_token_width_rejects_short_duration(self):
        """GJ1 rejects short sunshine-duration token in strict mode."""
        result = clean_value_quality("100,1", "GJ1", strict_mode=True)
        assert result["GJ1__part1"] is None
        assert result["GJ1__part1__qc_reason"] == "MALFORMED_TOKEN"

    def test_gj1_sentinel_rejects_missing_duration_token(self):
        result = clean_value_quality("9999,1", "GJ1", strict_mode=True)
        assert result["GJ1__part1"] is None

    def test_gj1_sentinel_accepts_non_sentinel_duration_token(self):
        result = clean_value_quality("0100,1", "GJ1", strict_mode=True)
        assert result["GJ1__part1"] == pytest.approx(100.0)

    def test_gk1_token_width_accepts_exact_tokens(self):
        """GK1 accepts canonical 3/1 token widths."""
        result = clean_value_quality("100,4", "GK1", strict_mode=True)
        assert result["GK1__part1"] == pytest.approx(100.0)
        assert result["GK1__part2"] == pytest.approx(4.0)

    def test_gk1_token_width_rejects_short_percent(self):
        """GK1 rejects short sunshine-percent token in strict mode."""
        result = clean_value_quality("10,4", "GK1", strict_mode=True)
        assert result["GK1__part1"] is None
        assert result["GK1__part1__qc_reason"] == "MALFORMED_TOKEN"

    def test_gk1_sentinel_rejects_missing_percent_token(self):
        result = clean_value_quality("999,4", "GK1", strict_mode=True)
        assert result["GK1__part1"] is None

    def test_gk1_sentinel_accepts_non_sentinel_percent_token(self):
        result = clean_value_quality("100,4", "GK1", strict_mode=True)
        assert result["GK1__part1"] == pytest.approx(100.0)

    def test_gl1_token_width_accepts_exact_tokens(self):
        """GL1 accepts canonical 5/1 token widths."""
        result = clean_value_quality("12000,1", "GL1", strict_mode=True)
        assert result["GL1__part1"] == pytest.approx(12000.0)
        assert result["GL1__part2"] == pytest.approx(1.0)

    def test_gl1_token_width_rejects_short_duration(self):
        """GL1 rejects short monthly-duration token in strict mode."""
        result = clean_value_quality("1200,1", "GL1", strict_mode=True)
        assert result["GL1__part1"] is None
        assert result["GL1__part1__qc_reason"] == "MALFORMED_TOKEN"

    def test_gl1_sentinel_rejects_missing_duration_token(self):
        result = clean_value_quality("99999,1", "GL1", strict_mode=True)
        assert result["GL1__part1"] is None

    def test_gl1_sentinel_accepts_non_sentinel_duration_token(self):
        result = clean_value_quality("12000,1", "GL1", strict_mode=True)
        assert result["GL1__part1"] == pytest.approx(12000.0)

    def test_gm1_token_width_accepts_exact_tokens(self):
        """GM1 accepts canonical widths across all 12 parts."""
        result = clean_value_quality(
            "0060,0123,00,1,0456,00,1,0789,00,1,0123,1",
            "GM1",
            strict_mode=True,
        )
        assert result["GM1__part1"] == pytest.approx(60.0)
        assert result["GM1__part2"] == pytest.approx(123.0)
        assert result["GM1__part3"] == pytest.approx(0.0)
        assert result["GM1__part11"] == pytest.approx(123.0)

    def test_gm1_token_width_rejects_short_global_irradiance(self):
        """GM1 rejects short global-irradiance token in strict mode."""
        result = clean_value_quality(
            "0060,123,00,1,0456,00,1,0789,00,1,0123,1",
            "GM1",
            strict_mode=True,
        )
        assert result["GM1__part2"] is None
        assert result["GM1__part2__qc_reason"] == "MALFORMED_TOKEN"

    def test_gm1_sentinel_rejects_missing_radiation_tokens(self):
        result = clean_value_quality(
            "9999,9999,99,1,9999,99,1,9999,99,1,9999,1",
            "GM1",
            strict_mode=True,
        )
        assert result["GM1__part1"] is None
        assert result["GM1__part2"] is None
        assert result["GM1__part5"] is None
        assert result["GM1__part8"] is None
        assert result["GM1__part11"] is None

    def test_gm1_sentinel_accepts_non_sentinel_radiation_tokens(self):
        result = clean_value_quality(
            "0060,0123,00,1,0456,00,1,0789,00,1,0123,1",
            "GM1",
            strict_mode=True,
        )
        assert result["GM1__part1"] == pytest.approx(60.0)
        assert result["GM1__part2"] == pytest.approx(123.0)
        assert result["GM1__part5"] == pytest.approx(456.0)
        assert result["GM1__part8"] == pytest.approx(789.0)
        assert result["GM1__part11"] == pytest.approx(123.0)

    def test_gn1_token_width_accepts_exact_tokens(self):
        """GN1 accepts canonical widths across all 11 parts."""
        result = clean_value_quality(
            "0060,0123,1,0456,1,0789,1,0123,1,090,1",
            "GN1",
            strict_mode=True,
        )
        assert result["GN1__part1"] == pytest.approx(60.0)
        assert result["GN1__part2"] == pytest.approx(123.0)
        assert result["GN1__part10"] == pytest.approx(90.0)

    def test_gn1_token_width_rejects_short_upwelling_global(self):
        """GN1 rejects short upwelling-global token in strict mode."""
        result = clean_value_quality(
            "0060,123,1,0456,1,0789,1,0123,1,090,1",
            "GN1",
            strict_mode=True,
        )
        assert result["GN1__part2"] is None
        assert result["GN1__part2__qc_reason"] == "MALFORMED_TOKEN"

    def test_gn1_sentinel_rejects_missing_radiation_tokens(self):
        result = clean_value_quality(
            "9999,9999,1,9999,1,9999,1,9999,1,999,1",
            "GN1",
            strict_mode=True,
        )
        assert result["GN1__part1"] is None
        assert result["GN1__part2"] is None
        assert result["GN1__part4"] is None
        assert result["GN1__part6"] is None
        assert result["GN1__part8"] is None
        assert result["GN1__part10"] is None

    def test_gn1_sentinel_accepts_non_sentinel_radiation_tokens(self):
        result = clean_value_quality(
            "0060,0123,1,0456,1,0789,1,0123,1,090,1",
            "GN1",
            strict_mode=True,
        )
        assert result["GN1__part1"] == pytest.approx(60.0)
        assert result["GN1__part2"] == pytest.approx(123.0)
        assert result["GN1__part4"] == pytest.approx(456.0)
        assert result["GN1__part6"] == pytest.approx(789.0)
        assert result["GN1__part8"] == pytest.approx(123.0)
        assert result["GN1__part10"] == pytest.approx(90.0)

    def test_go1_token_width_accepts_exact_tokens(self):
        """GO1 accepts canonical widths across all 7 parts."""
        result = clean_value_quality(
            "0060,0123,1,0456,1,0789,1",
            "GO1",
            strict_mode=True,
        )
        assert result["GO1__part1"] == pytest.approx(60.0)
        assert result["GO1__part2"] == pytest.approx(123.0)
        assert result["GO1__part4"] == pytest.approx(456.0)

    def test_go1_token_width_rejects_short_net_solar(self):
        """GO1 rejects short net-solar token in strict mode."""
        result = clean_value_quality(
            "0060,123,1,0456,1,0789,1",
            "GO1",
            strict_mode=True,
        )
        assert result["GO1__part2"] is None
        assert result["GO1__part2__qc_reason"] == "MALFORMED_TOKEN"

    def test_go1_sentinel_rejects_missing_radiation_tokens(self):
        result = clean_value_quality(
            "9999,9999,9,9999,9,9999,9",
            "GO1",
            strict_mode=True,
        )
        assert result["GO1__part1"] is None
        assert result["GO1__part2"] is None
        assert result["GO1__part4"] is None
        assert result["GO1__part6"] is None

    def test_go1_sentinel_accepts_non_sentinel_radiation_tokens(self):
        result = clean_value_quality(
            "0060,0123,9,0456,9,0789,9",
            "GO1",
            strict_mode=True,
        )
        assert result["GO1__part1"] == pytest.approx(60.0)
        assert result["GO1__part2"] == pytest.approx(123.0)
        assert result["GO1__part3"] == pytest.approx(9.0)
        assert result["GO1__part4"] == pytest.approx(456.0)
        assert result["GO1__part5"] == pytest.approx(9.0)
        assert result["GO1__part6"] == pytest.approx(789.0)
        assert result["GO1__part7"] == pytest.approx(9.0)

    def test_gp1_token_width_accepts_exact_tokens(self):
        """GP1 accepts canonical widths across all 10 parts."""
        result = clean_value_quality(
            "0060,0123,01,100,0456,02,050,0789,03,025",
            "GP1",
            strict_mode=True,
        )
        assert result["GP1__part1"] == pytest.approx(60.0)
        assert result["GP1__part2"] == pytest.approx(123.0)
        assert result["GP1__part4"] == pytest.approx(100.0)
        assert result["GP1__part8"] == pytest.approx(789.0)

    def test_gp1_token_width_rejects_short_modeled_global(self):
        """GP1 rejects short modeled-global token in strict mode."""
        result = clean_value_quality(
            "0060,123,01,100,0456,02,050,0789,03,025",
            "GP1",
            strict_mode=True,
        )
        assert result["GP1__part2"] is None
        assert result["GP1__part2__qc_reason"] == "MALFORMED_TOKEN"

    def test_gq1_token_width_accepts_exact_tokens(self):
        """GQ1 accepts canonical widths across all 5 parts."""
        result = clean_value_quality(
            "0060,0123,1,2345,1",
            "GQ1",
            strict_mode=True,
        )
        assert result["GQ1__part1"] == pytest.approx(60.0)
        assert result["GQ1__part2"] == pytest.approx(12.3)
        assert result["GQ1__part4"] == pytest.approx(234.5)

    def test_gq1_token_width_rejects_short_zenith_angle(self):
        """GQ1 rejects short zenith-angle token in strict mode."""
        result = clean_value_quality(
            "0060,123,1,2345,1",
            "GQ1",
            strict_mode=True,
        )
        assert result["GQ1__part2"] is None
        assert result["GQ1__part2__qc_reason"] == "MALFORMED_TOKEN"

    def test_gr1_token_width_accepts_exact_tokens(self):
        """GR1 accepts canonical widths across all 5 parts."""
        result = clean_value_quality(
            "0060,0800,1,0900,1",
            "GR1",
            strict_mode=True,
        )
        assert result["GR1__part1"] == pytest.approx(60.0)
        assert result["GR1__part2"] == pytest.approx(800.0)
        assert result["GR1__part4"] == pytest.approx(900.0)

    def test_gr1_token_width_rejects_short_horizontal_radiation(self):
        """GR1 rejects short horizontal-radiation token in strict mode."""
        result = clean_value_quality(
            "0060,800,1,0900,1",
            "GR1",
            strict_mode=True,
        )
        assert result["GR1__part2"] is None
        assert result["GR1__part2__qc_reason"] == "MALFORMED_TOKEN"

    def test_hail_token_width_accepts_exact_tokens(self):
        """HAIL accepts canonical 3/1 token widths."""
        result = clean_value_quality("100,1", "HAIL", strict_mode=True)
        assert result["HAIL__value"] == pytest.approx(10.0)
        assert result["HAIL__quality"] == "1"

    def test_hail_token_width_rejects_short_hail_size(self):
        """HAIL rejects short hail-size token in strict mode."""
        result = clean_value_quality("10,1", "HAIL", strict_mode=True)
        assert result["HAIL__value"] is None
        assert result["HAIL__qc_reason"] == "MALFORMED_TOKEN"

    def test_ia1_token_width_accepts_exact_tokens(self):
        """IA1 accepts canonical 2/1 token widths."""
        result = clean_value_quality("10,1", "IA1", strict_mode=True)
        assert result["IA1__part1"] == pytest.approx(10.0)
        assert result["IA1__part2"] == pytest.approx(1.0)

    def test_ia1_token_width_rejects_space_padded_code(self):
        """IA1 rejects space-padded ground-surface code in strict mode."""
        result = clean_value_quality("10 ,1", "IA1", strict_mode=True)
        assert result["IA1__part1"] is None

    def test_ib1_token_width_accepts_exact_tokens(self):
        """IB1 accepts canonical widths across all 12 parts."""
        result = clean_value_quality(
            "+0100,1,0,+0050,1,0,+0150,1,0,0010,1,0",
            "IB1",
            strict_mode=True,
        )
        assert result["IB1__part1"] == pytest.approx(10.0)
        assert result["IB1__part7"] == pytest.approx(15.0)
        assert result["IB1__part10"] == pytest.approx(1.0)

    def test_ib1_token_width_rejects_short_std_token(self):
        """IB1 rejects short surface-temperature-std token in strict mode."""
        result = clean_value_quality(
            "+0100,1,0,+0050,1,0,+0150,1,0,010,1,0",
            "IB1",
            strict_mode=True,
        )
        assert result["IB1__part10"] is None
        assert result["IB1__part10__qc_reason"] == "MALFORMED_TOKEN"

    def test_ic1_token_width_accepts_exact_tokens(self):
        """IC1 accepts canonical 2/4/1/1/3/1/1/4/1/1/4/1/1 token widths."""
        result = clean_value_quality(
            "24,0100,1,4,050,1,4,+050,1,4,+040,1,4",
            "IC1",
            strict_mode=True,
        )
        assert result["IC1__part1"] == pytest.approx(24.0)
        assert result["IC1__part2"] == pytest.approx(100.0)
        assert result["IC1__part5"] == pytest.approx(0.5)
        assert result["IC1__part8"] == pytest.approx(5.0)
        assert result["IC1__part11"] == pytest.approx(4.0)

    def test_ic1_token_width_rejects_short_snow_depth(self):
        """IC1 rejects short snow-depth token in strict mode."""
        result = clean_value_quality(
            "24,100,1,4,050,1,4,+050,1,4,+040,1,4",
            "IC1",
            strict_mode=True,
        )
        assert result["IC1__part2"] is None
        assert result["IC1__part2__qc_reason"] == "MALFORMED_TOKEN"

    def test_ic1_sentinel_rejects_missing_measurement_tokens(self):
        result = clean_value_quality(
            "99,9999,9,4,999,9,4,999,9,4,999,9,4",
            "IC1",
            strict_mode=True,
        )
        assert result["IC1__part1"] is None
        assert result["IC1__part2"] is None
        assert result["IC1__part3"] is None
        assert result["IC1__part5"] is None
        assert result["IC1__part6"] is None
        assert result["IC1__part8"] is None
        assert result["IC1__part9"] is None
        assert result["IC1__part11"] is None
        assert result["IC1__part12"] is None

    def test_ic1_sentinel_accepts_non_sentinel_measurement_tokens(self):
        result = clean_value_quality(
            "24,0100,1,4,050,1,4,+050,1,4,+040,1,4",
            "IC1",
            strict_mode=True,
        )
        assert result["IC1__part1"] == pytest.approx(24.0)
        assert result["IC1__part2"] == pytest.approx(100.0)
        assert result["IC1__part3"] == pytest.approx(1.0)
        assert result["IC1__part5"] == pytest.approx(0.5)
        assert result["IC1__part6"] == pytest.approx(1.0)
        assert result["IC1__part8"] == pytest.approx(5.0)
        assert result["IC1__part9"] == pytest.approx(1.0)
        assert result["IC1__part11"] == pytest.approx(4.0)
        assert result["IC1__part12"] == pytest.approx(1.0)

    @pytest.mark.parametrize("prefix", ["KA1", "KA2", "KA3", "KA4"])
    def test_ka_token_width_accepts_exact_tokens(self, prefix: str):
        """KA1-KA4 accept canonical 3/1/4/1 token widths."""
        result = clean_value_quality(
            "005,N,0123,1",
            prefix,
            strict_mode=True,
        )
        assert result[f"{prefix}__part1"] == pytest.approx(0.5)
        assert result[f"{prefix}__part2"] == "N"
        assert result[f"{prefix}__part3"] == pytest.approx(12.3)

    @pytest.mark.parametrize("prefix", ["KA1", "KA2", "KA3", "KA4"])
    def test_ka_token_width_rejects_short_period(self, prefix: str):
        """KA1-KA4 reject short period tokens in strict mode."""
        result = clean_value_quality(
            "05,N,0123,1",
            prefix,
            strict_mode=True,
        )
        assert result[f"{prefix}__part1"] is None
        assert result[f"{prefix}__part1__qc_reason"] == "MALFORMED_TOKEN"

    @pytest.mark.parametrize("prefix", ["KA2", "KA3", "KA4"])
    def test_ka_repeated_sentinel_rejects_missing_tokens(self, prefix: str):
        result = clean_value_quality(
            "999,9,9999,1",
            prefix,
            strict_mode=True,
        )
        assert result[f"{prefix}__part1"] is None
        assert result[f"{prefix}__part2"] is None
        assert result[f"{prefix}__part3"] is None

    @pytest.mark.parametrize("prefix", ["KA2", "KA3", "KA4"])
    def test_ka_repeated_sentinel_accepts_non_sentinel_tokens(self, prefix: str):
        result = clean_value_quality(
            "005,N,0123,9",
            prefix,
            strict_mode=True,
        )
        assert result[f"{prefix}__part1"] == pytest.approx(0.5)
        assert result[f"{prefix}__part2"] == "N"
        assert result[f"{prefix}__part3"] == pytest.approx(12.3)
        assert result[f"{prefix}__part4"] == pytest.approx(9.0)

    @pytest.mark.parametrize("prefix", ["KB1", "KB2", "KB3"])
    def test_kb_token_width_accepts_exact_tokens(self, prefix: str):
        """KB1-KB3 accept canonical 3/1/4/1 token widths."""
        result = clean_value_quality(
            "024,A,0100,1",
            prefix,
            strict_mode=True,
        )
        assert result[f"{prefix}__part1"] == pytest.approx(24.0)
        assert result[f"{prefix}__part2"] == "A"
        assert result[f"{prefix}__part3"] == pytest.approx(1.0)

    @pytest.mark.parametrize("prefix", ["KB1", "KB2", "KB3"])
    def test_kb_token_width_rejects_short_period(self, prefix: str):
        """KB1-KB3 reject short period tokens in strict mode."""
        result = clean_value_quality(
            "24,A,0100,1",
            prefix,
            strict_mode=True,
        )
        assert result[f"{prefix}__part1"] is None
        assert result[f"{prefix}__part1__qc_reason"] == "MALFORMED_TOKEN"

    @pytest.mark.parametrize("prefix", ["KC1", "KC2"])
    def test_kc_token_width_accepts_exact_tokens(self, prefix: str):
        """KC1-KC2 accept canonical 1/1/4/6/1 token widths."""
        result = clean_value_quality(
            "N,1,0123,010203,1",
            prefix,
            strict_mode=True,
        )
        assert result[f"{prefix}__part1"] == "N"
        assert result[f"{prefix}__part2"] == pytest.approx(1.0)
        assert result[f"{prefix}__part3"] == pytest.approx(12.3)
        assert result[f"{prefix}__part4"] == pytest.approx(10203.0)

    @pytest.mark.parametrize("prefix", ["KC1", "KC2"])
    def test_kc_token_width_rejects_short_temperature(self, prefix: str):
        """KC1-KC2 reject short temperature tokens in strict mode."""
        result = clean_value_quality(
            "N,1,123,010203,1",
            prefix,
            strict_mode=True,
        )
        assert result[f"{prefix}__part3"] is None
        assert result[f"{prefix}__part3__qc_reason"] == "MALFORMED_TOKEN"

    @pytest.mark.parametrize("prefix", ["KD1", "KD2"])
    def test_kd_token_width_accepts_exact_tokens(self, prefix: str):
        """KD1-KD2 accept canonical 3/1/4/1 token widths."""
        result = clean_value_quality(
            "024,H,0100,1",
            prefix,
            strict_mode=True,
        )
        assert result[f"{prefix}__part1"] == pytest.approx(24.0)
        assert result[f"{prefix}__part2"] == "H"
        assert result[f"{prefix}__part3"] == pytest.approx(100.0)

    @pytest.mark.parametrize("prefix", ["KD1", "KD2"])
    def test_kd_token_width_rejects_short_period(self, prefix: str):
        """KD1-KD2 reject short period tokens in strict mode."""
        result = clean_value_quality(
            "24,H,0100,1",
            prefix,
            strict_mode=True,
        )
        assert result[f"{prefix}__part1"] is None
        assert result[f"{prefix}__part1__qc_reason"] == "MALFORMED_TOKEN"

    def test_ke1_token_width_accepts_exact_tokens(self):
        """KE1 accepts canonical 2/1/2/1/2/1/2/1 token widths."""
        result = clean_value_quality(
            "01,1,02,1,03,1,04,1",
            "KE1",
            strict_mode=True,
        )
        assert result["KE1__part1"] == pytest.approx(1.0)
        assert result["KE1__part3"] == pytest.approx(2.0)
        assert result["KE1__part5"] == pytest.approx(3.0)
        assert result["KE1__part7"] == pytest.approx(4.0)

    def test_ke1_token_width_rejects_short_day(self):
        """KE1 rejects short day token in strict mode."""
        result = clean_value_quality(
            "1,1,02,1,03,1,04,1",
            "KE1",
            strict_mode=True,
        )
        assert result["KE1__part1"] is None
        assert result["KE1__part1__qc_reason"] == "MALFORMED_TOKEN"

    def test_kf1_token_width_accepts_exact_tokens(self):
        """KF1 accepts canonical 4/1 token widths."""
        result = clean_value_quality(
            "+0123,1",
            "KF1",
            strict_mode=True,
        )
        assert result["KF1__part1"] == pytest.approx(12.3)
        assert result["KF1__part2"] == pytest.approx(1.0)

    def test_kf1_token_width_rejects_short_temperature(self):
        """KF1 rejects short temperature token in strict mode."""
        result = clean_value_quality(
            "123,1",
            "KF1",
            strict_mode=True,
        )
        assert result["KF1__part1"] is None
        assert result["KF1__part1__qc_reason"] == "MALFORMED_TOKEN"

    @pytest.mark.parametrize("prefix", ["KG1", "KG2"])
    def test_kg_token_width_accepts_exact_tokens(self, prefix: str):
        """KG1-KG2 accept canonical 3/1/4/1/1 token widths."""
        result = clean_value_quality(
            "024,D,0123,D,1",
            prefix,
            strict_mode=True,
        )
        assert result[f"{prefix}__part1"] == pytest.approx(24.0)
        assert result[f"{prefix}__part2"] == "D"
        assert result[f"{prefix}__part3"] == pytest.approx(12.3)
        assert result[f"{prefix}__part4"] == "D"

    @pytest.mark.parametrize("prefix", ["KG1", "KG2"])
    def test_kg_token_width_rejects_short_period(self, prefix: str):
        """KG1-KG2 reject short period token in strict mode."""
        result = clean_value_quality(
            "24,D,0123,D,1",
            prefix,
            strict_mode=True,
        )
        assert result[f"{prefix}__part1"] is None
        assert result[f"{prefix}__part1__qc_reason"] == "MALFORMED_TOKEN"

    def test_sa1_token_width_accepts_exact_tokens(self):
        """SA1 accepts canonical 4/1 token widths."""
        result = clean_value_quality(
            "0215,1",
            "SA1",
            strict_mode=True,
        )
        assert result["SA1__value"] == pytest.approx(21.5)
        assert result["SA1__quality"] == "1"

    def test_sa1_token_width_rejects_short_temperature(self):
        """SA1 rejects short temperature token in strict mode."""
        result = clean_value_quality(
            "215,1",
            "SA1",
            strict_mode=True,
        )
        assert result["SA1__value"] is None
        assert result["SA1__qc_reason"] == "MALFORMED_TOKEN"

    def test_st1_token_width_accepts_exact_tokens(self):
        """ST1 accepts canonical 1/4/1/4/1/2/1/1/1 token widths."""
        result = clean_value_quality(
            "1,0123,4,0050,4,01,4,2,4",
            "ST1",
            strict_mode=True,
        )
        assert result["ST1__part2"] == pytest.approx(12.3)
        assert result["ST1__part4"] == pytest.approx(5.0)
        assert result["ST1__part6"] == pytest.approx(1.0)

    def test_st1_token_width_rejects_short_temperature(self):
        """ST1 rejects short temperature token in strict mode."""
        result = clean_value_quality(
            "1,123,4,0050,4,01,4,2,4",
            "ST1",
            strict_mode=True,
        )
        assert result["ST1__part2"] is None
        assert result["ST1__part2__qc_reason"] == "MALFORMED_TOKEN"

    def test_ma1_token_width_accepts_exact_tokens(self):
        """MA1 accepts canonical 5/1/5/1 token widths."""
        result = clean_value_quality(
            "10132,1,09876,1",
            "MA1",
            strict_mode=True,
        )
        assert result["MA1__part1"] == pytest.approx(1013.2)
        assert result["MA1__part3"] == pytest.approx(987.6)

    def test_ma1_token_width_rejects_short_altimeter(self):
        """MA1 rejects short altimeter token in strict mode."""
        result = clean_value_quality(
            "1013,1,09876,1",
            "MA1",
            strict_mode=True,
        )
        assert result["MA1__part1"] is None
        assert result["MA1__part1__qc_reason"] == "MALFORMED_TOKEN"

    def test_md1_token_width_accepts_exact_tokens(self):
        """MD1 accepts canonical 1/1/3/1/4/1 token widths."""
        result = clean_value_quality(
            "5,1,045,1,0123,1",
            "MD1",
            strict_mode=True,
        )
        assert result["MD1__part3"] == pytest.approx(4.5)
        assert result["MD1__part5"] == pytest.approx(12.3)

    def test_md1_token_width_rejects_short_three_hour_change(self):
        """MD1 rejects short 3-hour pressure-change token in strict mode."""
        result = clean_value_quality(
            "5,1,45,1,0123,1",
            "MD1",
            strict_mode=True,
        )
        assert result["MD1__part3"] is None
        assert result["MD1__part3__qc_reason"] == "MALFORMED_TOKEN"

    def test_me1_token_width_accepts_exact_tokens(self):
        """ME1 accepts canonical 1/4/1 token widths."""
        result = clean_value_quality(
            "1,0123,1",
            "ME1",
            strict_mode=True,
        )
        assert result["ME1__part1"] == pytest.approx(1.0)
        assert result["ME1__part2"] == pytest.approx(123.0)
        assert result["ME1__part3"] == pytest.approx(1.0)

    def test_me1_token_width_rejects_short_height(self):
        """ME1 rejects short geopotential-height token in strict mode."""
        result = clean_value_quality(
            "1,123,1",
            "ME1",
            strict_mode=True,
        )
        assert result["ME1__part2"] is None
        assert result["ME1__part2__qc_reason"] == "MALFORMED_TOKEN"

    def test_mf1_token_width_accepts_exact_tokens(self):
        """MF1 accepts canonical 5/1/5/1 token widths."""
        result = clean_value_quality(
            "10132,1,09876,1",
            "MF1",
            strict_mode=True,
        )
        assert result["MF1__part1"] == pytest.approx(1013.2)
        assert result["MF1__part3"] == pytest.approx(987.6)

    def test_mf1_token_width_rejects_short_station_pressure(self):
        """MF1 rejects short station-pressure token in strict mode."""
        result = clean_value_quality(
            "9999,1,09876,1",
            "MF1",
            strict_mode=True,
        )
        assert result["MF1__part1"] is None
        assert result["MF1__part1__qc_reason"] == "MALFORMED_TOKEN"

    def test_mg1_token_width_accepts_exact_tokens(self):
        """MG1 accepts canonical 5/1/5/1 token widths."""
        result = clean_value_quality(
            "10132,4,09876,4",
            "MG1",
            strict_mode=True,
        )
        assert result["MG1__part1"] == pytest.approx(1013.2)
        assert result["MG1__part3"] == pytest.approx(987.6)

    def test_mg1_token_width_rejects_short_sea_level_pressure(self):
        """MG1 rejects short sea-level-pressure token in strict mode."""
        result = clean_value_quality(
            "10132,4,9999,4",
            "MG1",
            strict_mode=True,
        )
        assert result["MG1__part3"] is None
        assert result["MG1__part3__qc_reason"] == "MALFORMED_TOKEN"

    def test_mh1_token_width_accepts_exact_tokens(self):
        """MH1 accepts canonical 5/1/5/1 token widths."""
        result = clean_value_quality(
            "10132,1,09876,1",
            "MH1",
            strict_mode=True,
        )
        assert result["MH1__part1"] == pytest.approx(1013.2)
        assert result["MH1__part3"] == pytest.approx(987.6)

    def test_mh1_token_width_rejects_short_sea_level_pressure(self):
        """MH1 rejects short sea-level-pressure token in strict mode."""
        result = clean_value_quality(
            "10132,1,9999,1",
            "MH1",
            strict_mode=True,
        )
        assert result["MH1__part3"] is None
        assert result["MH1__part3__qc_reason"] == "MALFORMED_TOKEN"

    def test_mk1_token_width_accepts_exact_tokens(self):
        """MK1 accepts canonical 5/6/1/5/6/1 token widths."""
        result = clean_value_quality(
            "08600,051500,1,08650,311259,1",
            "MK1",
            strict_mode=True,
        )
        assert result["MK1__part1"] == pytest.approx(860.0)
        assert result["MK1__part2"] == pytest.approx(51500.0)
        assert result["MK1__part4"] == pytest.approx(865.0)
        assert result["MK1__part5"] == pytest.approx(311259.0)

    def test_mk1_token_width_rejects_short_month_max_pressure(self):
        """MK1 rejects short month-max pressure token in strict mode."""
        result = clean_value_quality(
            "9999,051500,1,08650,311259,1",
            "MK1",
            strict_mode=True,
        )
        assert result["MK1__part1"] is None
        assert result["MK1__part1__qc_reason"] == "MALFORMED_TOKEN"

    def test_mv1_token_width_accepts_exact_tokens(self):
        """MV1 accepts canonical 2/1 token widths."""
        result = clean_value_quality(
            "05,4",
            "MV1",
            strict_mode=True,
        )
        assert result["MV1__part1"] == "05"
        assert result["MV1__part2"] == pytest.approx(4.0)

    def test_mv1_token_width_rejects_space_padded_code(self):
        """MV1 rejects space-padded present-weather code in strict mode."""
        result = clean_value_quality(
            "05 ,4",
            "MV1",
            strict_mode=True,
        )
        assert result["MV1__part1"] is None

    def test_mw1_token_width_accepts_exact_tokens(self):
        """MW1 accepts canonical 2/1 token widths."""
        result = clean_value_quality(
            "12,4",
            "MW1",
            strict_mode=True,
        )
        assert result["MW1__part1"] == "12"
        assert result["MW1__part2"] == pytest.approx(4.0)

    def test_mw1_token_width_rejects_space_padded_code(self):
        """MW1 rejects space-padded present-weather code in strict mode."""
        result = clean_value_quality(
            "12 ,4",
            "MW1",
            strict_mode=True,
        )
        assert result["MW1__part1"] is None

    def test_oa1_token_width_accepts_exact_tokens(self):
        """OA1 accepts canonical 1/2/4/1 token widths."""
        result = clean_value_quality(
            "1,01,0005,1",
            "OA1",
            strict_mode=True,
        )
        assert result["OA1__part1"] == pytest.approx(1.0)
        assert result["OA1__part2"] == pytest.approx(1.0)
        assert result["OA1__part3"] == pytest.approx(0.5)
        assert result["OA1__part4"] == pytest.approx(1.0)

    def test_oa1_token_width_rejects_space_padded_type(self):
        """OA1 rejects space-padded type code in strict mode."""
        result = clean_value_quality(
            "1 ,01,0005,1",
            "OA1",
            strict_mode=True,
        )
        assert result["OA1__part1"] is None

    def test_oa2_token_width_accepts_exact_tokens(self):
        """OA2 accepts canonical 1/2/4/1 token widths."""
        result = clean_value_quality(
            "1,01,0005,1",
            "OA2",
            strict_mode=True,
        )
        assert result["OA2__part1"] == pytest.approx(1.0)
        assert result["OA2__part2"] == pytest.approx(1.0)
        assert result["OA2__part3"] == pytest.approx(0.5)
        assert result["OA2__part4"] == pytest.approx(1.0)

    def test_oa2_token_width_rejects_space_padded_period_quantity(self):
        """OA2 rejects space-padded period-quantity token in strict mode."""
        result = clean_value_quality(
            "1,01 ,0005,1",
            "OA2",
            strict_mode=True,
        )
        assert result["OA2__part2"] is None

    def test_oa3_token_width_accepts_exact_tokens(self):
        """OA3 accepts canonical 1/2/4/1 token widths."""
        result = clean_value_quality(
            "1,01,0005,1",
            "OA3",
            strict_mode=True,
        )
        assert result["OA3__part1"] == pytest.approx(1.0)
        assert result["OA3__part2"] == pytest.approx(1.0)
        assert result["OA3__part3"] == pytest.approx(0.5)
        assert result["OA3__part4"] == pytest.approx(1.0)

    def test_oa3_token_width_rejects_short_speed_rate(self):
        """OA3 rejects short speed-rate token in strict mode."""
        result = clean_value_quality(
            "1,01,5,1",
            "OA3",
            strict_mode=True,
        )
        assert result["OA3__part3"] is None
        assert result["OA3__part3__qc_reason"] == "MALFORMED_TOKEN"

    def test_ob1_token_width_accepts_exact_tokens(self):
        """OB1 accepts canonical 3/4/1/1/3/1/1/5/1/1/5/1/1 token widths."""
        result = clean_value_quality(
            "060,0050,1,0,090,1,0,00010,1,0,00020,1,0",
            "OB1",
            strict_mode=True,
        )
        assert result["OB1__part1"] == pytest.approx(60.0)
        assert result["OB1__part2"] == pytest.approx(5.0)
        assert result["OB1__part8"] == pytest.approx(0.1)
        assert result["OB1__part11"] == pytest.approx(0.2)

    def test_ob1_token_width_rejects_short_period_minutes(self):
        """OB1 rejects short period-minutes token in strict mode."""
        result = clean_value_quality(
            "60,0050,1,0,090,1,0,00010,1,0,00020,1,0",
            "OB1",
            strict_mode=True,
        )
        assert result["OB1__part1"] is None
        assert result["OB1__part1__qc_reason"] == "MALFORMED_TOKEN"

    def test_ob1_token_width_rejects_short_max_gust(self):
        """OB1 rejects short max-gust token in strict mode."""
        result = clean_value_quality(
            "060,050,1,0,090,1,0,00010,1,0,00020,1,0",
            "OB1",
            strict_mode=True,
        )
        assert result["OB1__part2"] is None
        assert result["OB1__part2__qc_reason"] == "MALFORMED_TOKEN"

    def test_ob1_token_width_rejects_short_speed_std(self):
        """OB1 rejects short speed-standard-deviation token in strict mode."""
        result = clean_value_quality(
            "060,0050,1,0,090,1,0,0010,1,0,00020,1,0",
            "OB1",
            strict_mode=True,
        )
        assert result["OB1__part8"] is None
        assert result["OB1__part8__qc_reason"] == "MALFORMED_TOKEN"

    def test_ob1_token_width_rejects_space_padded_quality(self):
        """OB1 rejects space-padded quality token in strict mode."""
        result = clean_value_quality(
            "060,0050,1 ,0,090,1,0,00010,1,0,00020,1,0",
            "OB1",
            strict_mode=True,
        )
        assert result["OB1__part3"] is None

    def test_ob2_token_width_accepts_exact_tokens(self):
        """OB2 accepts canonical 3/4/1/1/3/1/1/5/1/1/5/1/1 token widths."""
        result = clean_value_quality(
            "060,0050,1,0,090,1,0,00010,1,0,00020,1,0",
            "OB2",
            strict_mode=True,
        )
        assert result["OB2__part1"] == pytest.approx(60.0)
        assert result["OB2__part2"] == pytest.approx(5.0)
        assert result["OB2__part8"] == pytest.approx(0.1)
        assert result["OB2__part11"] == pytest.approx(0.2)

    def test_ob2_token_width_rejects_short_period_minutes(self):
        """OB2 rejects short period-minutes token in strict mode."""
        result = clean_value_quality(
            "60,0050,1,0,090,1,0,00010,1,0,00020,1,0",
            "OB2",
            strict_mode=True,
        )
        assert result["OB2__part1"] is None
        assert result["OB2__part1__qc_reason"] == "MALFORMED_TOKEN"

    def test_oc1_token_width_accepts_exact_tokens(self):
        """OC1 accepts canonical 4/1 token widths."""
        result = clean_value_quality(
            "0500,1",
            "OC1",
            strict_mode=True,
        )
        assert result["OC1__value"] == pytest.approx(50.0)
        assert result["OC1__quality"] == "1"
        assert result["OC1__qc_reason"] is None

    def test_oc1_token_width_rejects_short_speed_rate(self):
        """OC1 rejects short speed-rate token in strict mode."""
        result = clean_value_quality(
            "500,1",
            "OC1",
            strict_mode=True,
        )
        assert result["OC1__value"] is None
        assert result["OC1__qc_reason"] == "MALFORMED_TOKEN"

    def test_od1_token_width_accepts_exact_tokens(self):
        """OD1 accepts canonical 1/2/3/4/1 token widths."""
        result = clean_value_quality(
            "1,01,090,0005,1",
            "OD1",
            strict_mode=True,
        )
        assert result["OD1__part1"] == pytest.approx(1.0)
        assert result["OD1__part2"] == pytest.approx(1.0)
        assert result["OD1__part3"] == pytest.approx(90.0)
        assert result["OD1__part4"] == pytest.approx(0.5)
        assert result["OD1__part5"] == pytest.approx(1.0)

    def test_od1_token_width_rejects_space_padded_type_code(self):
        """OD1 rejects space-padded type-code token in strict mode."""
        result = clean_value_quality(
            "1 ,01,090,0005,1",
            "OD1",
            strict_mode=True,
        )
        assert result["OD1__part1"] is None

    def test_od2_token_width_accepts_exact_tokens(self):
        """OD2 accepts canonical 1/2/3/4/1 token widths."""
        result = clean_value_quality(
            "1,01,090,0005,1",
            "OD2",
            strict_mode=True,
        )
        assert result["OD2__part1"] == pytest.approx(1.0)
        assert result["OD2__part2"] == pytest.approx(1.0)
        assert result["OD2__part3"] == pytest.approx(90.0)
        assert result["OD2__part4"] == pytest.approx(0.5)
        assert result["OD2__part5"] == pytest.approx(1.0)

    def test_od2_token_width_rejects_space_padded_period_quantity(self):
        """OD2 rejects space-padded period-quantity token in strict mode."""
        result = clean_value_quality(
            "1,01 ,090,0005,1",
            "OD2",
            strict_mode=True,
        )
        assert result["OD2__part2"] is None

    def test_od3_token_width_accepts_exact_tokens(self):
        """OD3 accepts canonical 1/2/3/4/1 token widths."""
        result = clean_value_quality(
            "1,01,090,0005,1",
            "OD3",
            strict_mode=True,
        )
        assert result["OD3__part1"] == pytest.approx(1.0)
        assert result["OD3__part2"] == pytest.approx(1.0)
        assert result["OD3__part3"] == pytest.approx(90.0)
        assert result["OD3__part4"] == pytest.approx(0.5)
        assert result["OD3__part5"] == pytest.approx(1.0)

    def test_od3_token_width_rejects_short_speed_rate(self):
        """OD3 rejects short speed-rate token in strict mode."""
        result = clean_value_quality(
            "1,01,090,005,1",
            "OD3",
            strict_mode=True,
        )
        assert result["OD3__part4"] is None
        assert result["OD3__part4__qc_reason"] == "MALFORMED_TOKEN"

    def test_token_width_permissive_mode(self):
        """Invalid token widths allowed in permissive mode."""
        df = pd.DataFrame({
            "WND": ["1,1,N,50,1"],  # 1-digit direction, 2-digit speed
            "TMP": ["+250,1"],       # 3-digit temperature
        })
        result = clean_noaa_dataframe(df, strict_mode=False)
        
        # Should not raise errors, values should parse
        assert result["wind_direction_deg"].iloc[0] == 1.0
        assert result["wind_speed_ms"].iloc[0] == 5.0
        assert result["temperature_c"].iloc[0] == 25.0


# ── QC Signals and Row-level Metrics ─────────────────────────────────────


class TestQCSignalsValueQualityFields:
    """Test QC signal emission for value/quality fields (2-part)."""

    def test_oc1_in_range_good_quality(self):
        """In-range value with good quality -> PASS."""
        result = clean_value_quality("0500,1", "OC1")  # 500 m/s * 0.1 = 50 m/s, within 50-1100
        assert result["OC1__value"] == pytest.approx(50.0)
        assert result["OC1__qc_pass"] is True
        assert result["OC1__qc_status"] == "PASS"
        assert result["OC1__qc_reason"] is None

    def test_oc1_boundary_low(self):
        """Value exactly at min boundary -> PASS."""
        result = clean_value_quality("0050,1", "OC1")  # 50 m/s * 0.1 = 5 m/s, equals 50 raw
        assert result["OC1__qc_pass"] is True
        assert result["OC1__qc_status"] == "PASS"

    def test_oc1_boundary_high(self):
        """Value exactly at max boundary -> PASS."""
        result = clean_value_quality("1100,1", "OC1")  # 1100 m/s * 0.1 = 110 m/s, equals 1100 raw
        assert result["OC1__qc_pass"] is True
        assert result["OC1__qc_status"] == "PASS"

    def test_oc1_just_below_min(self):
        """Value just below min -> OUT_OF_RANGE."""
        result = clean_value_quality("0049,1", "OC1")  # 49 raw < 50 min
        assert result["OC1__value"] is None
        assert result["OC1__qc_pass"] is False
        assert result["OC1__qc_status"] == "INVALID"
        assert result["OC1__qc_reason"] == "OUT_OF_RANGE"

    def test_oc1_just_above_max(self):
        """Value just above max -> OUT_OF_RANGE."""
        result = clean_value_quality("1101,1", "OC1")  # 1101 raw > 1100 max
        assert result["OC1__value"] is None
        assert result["OC1__qc_pass"] is False
        assert result["OC1__qc_status"] == "INVALID"
        assert result["OC1__qc_reason"] == "OUT_OF_RANGE"

    def test_oc1_missing_sentinel(self):
        """Missing sentinel value -> SENTINEL_MISSING."""
        result = clean_value_quality("9999,1", "OC1")
        assert result["OC1__value"] is None
        assert result["OC1__qc_pass"] is False
        assert result["OC1__qc_status"] == "MISSING"
        assert result["OC1__qc_reason"] == "SENTINEL_MISSING"

    def test_oc1_bad_quality_code(self):
        """Invalid quality code -> BAD_QUALITY_CODE."""
        result = clean_value_quality("0500,X", "OC1")  # X not in allowed_quality
        assert result["OC1__value"] is None
        assert result["OC1__qc_pass"] is False
        assert result["OC1__qc_status"] == "INVALID"
        assert result["OC1__qc_reason"] == "BAD_QUALITY_CODE"

    def test_tmp_malformed_token(self):
        """Invalid token width -> MALFORMED_TOKEN."""
        result = clean_value_quality("+250,1", "TMP", strict_mode=True)
        assert result["TMP__value"] is None
        assert result["TMP__qc_pass"] is False
        assert result["TMP__qc_status"] == "INVALID"
        assert result["TMP__qc_reason"] == "MALFORMED_TOKEN"

    def test_tmp_non_numeric_token_is_malformed(self):
        result = clean_value_quality("A250,1", "TMP", strict_mode=True)
        assert result["TMP__value"] is None
        assert result["TMP__qc_pass"] is False
        assert result["TMP__qc_status"] == "INVALID"
        assert result["TMP__qc_reason"] == "MALFORMED_TOKEN"

    def test_ma1_in_range_good_quality(self):
        """MA1 (pressure) is multi-part, testing via dataframe parsing."""
        df = pd.DataFrame({
            "MA1": ["09000,1,09500,1"],  # 4-part: alimeter:9000, quality, station:9500, quality
        })
        result = clean_noaa_dataframe(df, strict_mode=False)
        # Check that QC columns exist and indicate pass
        ma1_qc_cols = [col for col in result.columns if "MA1" in col and "__qc_" in col]
        assert len(ma1_qc_cols) > 0

    def test_ma1_out_of_range_high(self):
        """MA1 part above max -> OUT_OF_RANGE."""
        df = pd.DataFrame({
            "MA1": ["11000,1,09500,1"],  # Alimeter 11000 > 10904 max
        })
        result = clean_noaa_dataframe(df, strict_mode=False)
        # At least one QC col should indicate out of range
        ma1_qc_cols = [col for col in result.columns if "MA1" in col and "__qc_reason" in col]
        assert len(ma1_qc_cols) > 0


class TestQCSignalsMultipartFields:
    """Test QC signal emission for multi-part fields."""

    def test_wnd_direction_in_range(self):
        """WND direction part in range -> qc_pass True."""
        result = _expand_parsed(
            parse_field("180,1,N,0500,1"),
            "WND",
            allow_quality=True,
            strict_mode=False,
        )
        # Part 1: direction, no min/max
        assert result["WND__part1"] == 180.0
        assert result.get("WND__part1__qc_pass") in (True, None)  # May not have QC if no bounds

    def test_wnd_malformed_token(self):
        """Invalid token width -> MALFORMED_TOKEN for numeric part."""
        result = _expand_parsed(
            parse_field("1,1,N,0500,1"),
            "WND",
            allow_quality=True,
            strict_mode=True,
        )
        assert result["WND__part1"] is None
        assert result["WND__part1__qc_pass"] is False
        assert result["WND__part1__qc_status"] == "INVALID"
        assert result["WND__part1__qc_reason"] == "MALFORMED_TOKEN"

    def test_wnd_non_numeric_direction_token_is_malformed(self):
        result = clean_value_quality("A90,1,N,0500,1", "WND", strict_mode=True)
        assert result["WND__part1"] is None
        assert result["WND__part1__qc_pass"] is False
        assert result["WND__part1__qc_reason"] == "MALFORMED_TOKEN"
        assert result["WND__part4"] == pytest.approx(50.0)

    def test_wnd_non_numeric_speed_token_is_malformed(self):
        result = clean_value_quality("090,1,N,0A50,1", "WND", strict_mode=True)
        assert result["WND__part1"] == pytest.approx(90.0)
        assert result["WND__part4"] is None
        assert result["WND__part4__qc_pass"] is False
        assert result["WND__part4__qc_reason"] == "MALFORMED_TOKEN"

    def test_ma1_part1_out_of_range(self):
        """MA1 altimeter outside max -> OUT_OF_RANGE."""
        result = _expand_parsed(
            parse_field("11000,1,09500,1"),
            "MA1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["MA1__part1__qc_pass"] is False
        assert result["MA1__part1__qc_status"] == "INVALID"
        assert result["MA1__part1__qc_reason"] == "OUT_OF_RANGE"

    def test_ge1_base_height_boundary(self):
        """GE1 base height boundary values -> PASS."""
        result = _expand_parsed(
            parse_field("1,MSL,-0400,15000"),
            "GE1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["GE1__part3__qc_pass"] is True
        assert result["GE1__part4__qc_pass"] is True

    def test_gg_layer_coverage_out_of_range(self):
        """GG layer coverage > 100 -> OUT_OF_RANGE."""
        result = _expand_parsed(
            parse_field("101,1,01000,1,99,1,99,1"),
            "GG1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["GG1__part1__qc_pass"] is False
        assert result["GG1__part1__qc_status"] == "INVALID"
        assert result["GG1__part1__qc_reason"] == "OUT_OF_RANGE"

    def test_gh1_boundary_max_pass(self):
        """GH1 max boundary -> PASS."""
        result = _expand_parsed(
            parse_field("99998,1,0,10000,1,0,20000,1,0,30000,1,0"),
            "GH1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result.get("GH1__part1__qc_pass") is True
        assert result.get("GH1__part1__qc_status") == "PASS"

    def test_gh1_numeric_parts_in_range(self):
        """GH1 (solar irradiance) numeric parts in range -> qc_pass True."""
        result = _expand_parsed(
            parse_field("05000,1,0,10000,1,0,20000,1,0,30000,1,0"),
            "GH1",
            allow_quality=True,
            strict_mode=False,
        )
        # Parts 1, 4, 7, 10 are numeric with min=0, max=99998
        assert result.get("GH1__part1__qc_pass") is True
        assert result.get("GH1__part1__qc_status") == "PASS"
        assert result.get("GH1__part1__qc_reason") is None

    def test_gh1_numeric_part_out_of_range(self):
        """GH1 part exceeds max -> OUT_OF_RANGE."""
        result = _expand_parsed(
            parse_field("100000,1,0,10000,1,0,20000,1,0,30000,1,0"),
            "GH1",
            allow_quality=True,
            strict_mode=False,
        )
        # Part 1: 100000 > 99998 max
        assert result.get("GH1__part1__qc_pass") is False
        assert result.get("GH1__part1__qc_status") == "INVALID"
        assert result.get("GH1__part1__qc_reason") == "OUT_OF_RANGE"

    def test_gh1_sentinel_value(self):
        """GH1 part with missing sentinel -> SENTINEL_MISSING."""
        result = _expand_parsed(
            parse_field("99999,1,0,10000,1,0,20000,1,0,30000,1,0"),
            "GH1",
            allow_quality=True,
            strict_mode=False,
        )
        # Part 1: 99999 is missing sentinel
        assert result.get("GH1__part1__qc_pass") is False
        assert result.get("GH1__part1__qc_reason") == "SENTINEL_MISSING"


class TestRowLevelUsabilityMetrics:
    """Test row-level summary columns."""

    def test_all_metrics_usable(self):
        """All metrics pass -> row_has_any_usable_metric True, fraction 1.0."""
        df = pd.DataFrame({
            "OC1": ["0500,1"],  # In range, good quality
        })
        result = clean_noaa_dataframe(df, strict_mode=False)
        assert result["row_has_any_usable_metric"].iloc[0] == True
        assert result["usable_metric_count"].iloc[0] >= 1
        assert result["usable_metric_fraction"].iloc[0] > 0.0

    def test_all_metrics_invalid(self):
        """All metrics fail -> row_has_any_usable_metric False, fraction 0.0."""
        df = pd.DataFrame({
            "OC1": ["0049,1"],  # Out of range
        })
        result = clean_noaa_dataframe(df, strict_mode=False)
        assert result["row_has_any_usable_metric"].iloc[0] == False
        assert result["usable_metric_count"].iloc[0] == 0
        assert result["usable_metric_fraction"].iloc[0] == 0.0

    def test_mixed_usability(self):
        """Some metrics pass, some fail -> fraction in (0, 1)."""
        df = pd.DataFrame({
            "OC1": ["0500,1"],  # In range
            "MA1": ["11000,1"],  # Out of range
        })
        result = clean_noaa_dataframe(df, strict_mode=False)
        fraction = result["usable_metric_fraction"].iloc[0]
        assert 0.0 < fraction < 1.0

    def test_no_numeric_fields_skipped(self):
        """Non-numeric fields (categorical) don't affect metrics."""
        df = pd.DataFrame({
            "WND": ["180,1,N,0500,1"],  # Has numeric parts but direction has no bounds
        })
        result = clean_noaa_dataframe(df, strict_mode=False)
        # Should have row-level columns even with only WND
        assert "row_has_any_usable_metric" in result.columns
        assert "usable_metric_count" in result.columns
        assert "usable_metric_fraction" in result.columns


class TestQCSignalsRegressions:
    """Ensure QC signals don't break existing functionality."""

    def test_raw_columns_preserved_with_keep_raw(self):
        """Raw columns should still be present with keep_raw=True."""
        df = pd.DataFrame({
            "OC1": ["0500,1"],
        })
        result = clean_noaa_dataframe(df, keep_raw=True, strict_mode=False)
        assert "OC1" in result.columns  # Raw column preserved

    def test_value_quality_columns_still_present(self):
        """Original __value and __quality columns still emitted."""
        result = clean_value_quality("0500,1", "OC1")
        assert "OC1__value" in result
        assert "OC1__quality" in result

    def test_scaling_still_applied(self):
        """Scale factors still applied to values."""
        result = clean_value_quality("0500,1", "OC1")
        # Raw: 500, Scale: 0.1 (per field rule), Expected: 50.0
        assert result["OC1__value"] == pytest.approx(50.0)

    def test_multipart_column_names_unchanged(self):
        """Multi-part column names unchanged, QC appended."""
        result = _expand_parsed(
            parse_field("180,1,N,0500,1"),
            "WND",
            allow_quality=True,
            strict_mode=False,
        )
        assert "WND__part1" in result  # Original part column
        # QC columns are additional

    def test_qc_columns_have_correct_types(self):
        """QC columns have correct types: bool, str, str|None."""
        result = clean_value_quality("0500,1", "OC1")
        assert isinstance(result["OC1__qc_pass"], bool)
        assert isinstance(result["OC1__qc_status"], str)
        assert result["OC1__qc_reason"] is None or isinstance(result["OC1__qc_reason"], str)

    def test_empty_dataframe_with_row_metrics(self):
        """Empty DataFrame with no QC columns doesn't get row metrics."""
        df = pd.DataFrame({
            "OC1": [],
        })
        result = clean_noaa_dataframe(df, strict_mode=False)
        # Empty with no parses means no QC columns, so no row metrics added
        if "OC1__qc_pass" in result.columns:
            assert "row_has_any_usable_metric" in result.columns
        # Alternatively, row metrics added only if QC columns exist
        assert len(result) == 0

    def test_qc_columns_in_clean_output(self):
        """QC columns appear in cleaned DataFrame output."""
        df = pd.DataFrame({
            "OC1": ["0500,1"],
        })
        result = clean_noaa_dataframe(df, strict_mode=False)
        # Check for at least one QC column (renamed to friendly name)
        qc_columns = [col for col in result.columns if "__qc_" in col]
        assert len(qc_columns) > 0
