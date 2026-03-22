"""Comprehensive QC signal tests for all specified fields (OC1, MA1, GE1, GF1, GG, GH, KA, KB)."""

import pandas as pd
import pytest

from noaa_spec.cleaning import (
    clean_noaa_dataframe,
    clean_value_quality,
    _expand_parsed,
    parse_field,
)


class TestQCSignalsComprehensiveOC1:
    """Comprehensive QC tests for OC1 (wind gust)."""

    def test_oc1_pass(self):
        """OC1 in-range + good quality -> PASS."""
        result = clean_value_quality("0500,1", "OC1")
        assert result["OC1__qc_pass"] is True
        assert result["OC1__qc_status"] == "PASS"
        assert result["OC1__qc_reason"] is None

    def test_oc1_out_of_range_low(self):
        """OC1 below min -> OUT_OF_RANGE."""
        result = clean_value_quality("0049,1", "OC1")
        assert result["OC1__qc_pass"] is False
        assert result["OC1__qc_status"] == "INVALID"
        assert result["OC1__qc_reason"] == "OUT_OF_RANGE"

    def test_oc1_out_of_range_high(self):
        """OC1 above max -> OUT_OF_RANGE."""
        result = clean_value_quality("1101,1", "OC1")
        assert result["OC1__qc_pass"] is False
        assert result["OC1__qc_status"] == "INVALID"
        assert result["OC1__qc_reason"] == "OUT_OF_RANGE"

    def test_oc1_sentinel(self):
        """OC1 sentinel value -> MISSING."""
        result = clean_value_quality("9999,1", "OC1")
        assert result["OC1__qc_pass"] is False
        assert result["OC1__qc_status"] == "MISSING"
        assert result["OC1__qc_reason"] == "SENTINEL_MISSING"

    def test_oc1_bad_quality(self):
        """OC1 invalid quality code -> BAD_QUALITY_CODE."""
        result = clean_value_quality("0500,X", "OC1")
        assert result["OC1__qc_pass"] is False
        assert result["OC1__qc_status"] == "INVALID"
        assert result["OC1__qc_reason"] == "BAD_QUALITY_CODE"


class TestQCSignalsComprehensiveMA1:
    """Comprehensive QC tests for MA1 (pressure: altimeter and station)."""

    def test_ma1_part1_pass(self):
        """MA1 part 1 (altimeter) in-range + good quality -> PASS."""
        result = _expand_parsed(
            parse_field("09000,1,09500,1"),
            "MA1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["MA1__part1__qc_pass"] is True
        assert result["MA1__part1__qc_status"] == "PASS"

    def test_ma1_part1_out_of_range_low(self):
        """MA1 part 1 below min (8635) -> OUT_OF_RANGE."""
        result = _expand_parsed(
            parse_field("08634,1,09500,1"),
            "MA1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["MA1__part1__qc_pass"] is False
        assert result["MA1__part1__qc_status"] == "INVALID"
        assert result["MA1__part1__qc_reason"] == "OUT_OF_RANGE"

    def test_ma1_part1_out_of_range_high(self):
        """MA1 part 1 above max (10904) -> OUT_OF_RANGE."""
        result = _expand_parsed(
            parse_field("10905,1,09500,1"),
            "MA1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["MA1__part1__qc_pass"] is False
        assert result["MA1__part1__qc_status"] == "INVALID"
        assert result["MA1__part1__qc_reason"] == "OUT_OF_RANGE"

    def test_ma1_part1_sentinel(self):
        """MA1 part 1 sentinel (99999) -> MISSING."""
        result = _expand_parsed(
            parse_field("99999,1,09500,1"),
            "MA1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["MA1__part1__qc_pass"] is False
        assert result["MA1__part1__qc_status"] == "MISSING"
        assert result["MA1__part1__qc_reason"] == "SENTINEL_MISSING"

    def test_ma1_part1_bad_quality(self):
        """MA1 part 1 invalid quality -> BAD_QUALITY_CODE."""
        result = _expand_parsed(
            parse_field("09000,X,09500,1"),
            "MA1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["MA1__part1__qc_pass"] is False
        assert result["MA1__part1__qc_status"] == "INVALID"
        assert result["MA1__part1__qc_reason"] == "BAD_QUALITY_CODE"

    def test_ma1_part3_pass(self):
        """MA1 part 3 (station pressure) in-range + good quality -> PASS."""
        result = _expand_parsed(
            parse_field("09000,1,09500,1"),
            "MA1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["MA1__part3__qc_pass"] is True
        assert result["MA1__part3__qc_status"] == "PASS"

    def test_ma1_part3_out_of_range_low(self):
        """MA1 part 3 below min (4500) -> OUT_OF_RANGE."""
        result = _expand_parsed(
            parse_field("09000,1,04499,1"),
            "MA1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["MA1__part3__qc_pass"] is False
        assert result["MA1__part3__qc_status"] == "INVALID"
        assert result["MA1__part3__qc_reason"] == "OUT_OF_RANGE"

    def test_ma1_part3_out_of_range_high(self):
        """MA1 part 3 above max (10900) -> OUT_OF_RANGE."""
        result = _expand_parsed(
            parse_field("09000,1,10901,1"),
            "MA1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["MA1__part3__qc_pass"] is False
        assert result["MA1__part3__qc_status"] == "INVALID"
        assert result["MA1__part3__qc_reason"] == "OUT_OF_RANGE"

    def test_ma1_part3_sentinel(self):
        """MA1 part 3 sentinel (99999) -> MISSING."""
        result = _expand_parsed(
            parse_field("09000,1,99999,1"),
            "MA1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["MA1__part3__qc_pass"] is False
        assert result["MA1__part3__qc_status"] == "MISSING"
        assert result["MA1__part3__qc_reason"] == "SENTINEL_MISSING"

    def test_ma1_part3_bad_quality(self):
        """MA1 part 3 invalid quality -> BAD_QUALITY_CODE."""
        result = _expand_parsed(
            parse_field("09000,1,09500,X"),
            "MA1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["MA1__part3__qc_pass"] is False
        assert result["MA1__part3__qc_status"] == "INVALID"
        assert result["MA1__part3__qc_reason"] == "BAD_QUALITY_CODE"


class TestQCSignalsComprehensiveGE1:
    """Comprehensive QC tests for GE1 (cloud height)."""

    def test_ge1_part3_pass(self):
        """GE1 part 3 (base upper) in-range -> PASS."""
        result = _expand_parsed(
            parse_field("1,MSL,00500,15000"),
            "GE1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["GE1__part3__qc_pass"] is True
        assert result["GE1__part3__qc_status"] == "PASS"

    def test_ge1_part3_out_of_range_low(self):
        """GE1 part 3 below min (-400) -> OUT_OF_RANGE."""
        result = _expand_parsed(
            parse_field("1,MSL,-0401,15000"),
            "GE1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["GE1__part3__qc_pass"] is False
        assert result["GE1__part3__qc_status"] == "INVALID"
        assert result["GE1__part3__qc_reason"] == "OUT_OF_RANGE"

    def test_ge1_part3_out_of_range_high(self):
        """GE1 part 3 above max (15000) -> OUT_OF_RANGE."""
        result = _expand_parsed(
            parse_field("1,MSL,15001,15000"),
            "GE1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["GE1__part3__qc_pass"] is False
        assert result["GE1__part3__qc_status"] == "INVALID"
        assert result["GE1__part3__qc_reason"] == "OUT_OF_RANGE"

    def test_ge1_part3_sentinel(self):
        """GE1 part 3 sentinel (99999) -> MISSING."""
        result = _expand_parsed(
            parse_field("1,MSL,99999,15000"),
            "GE1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["GE1__part3__qc_pass"] is False
        assert result["GE1__part3__qc_status"] == "MISSING"
        assert result["GE1__part3__qc_reason"] == "SENTINEL_MISSING"

    def test_ge1_part4_pass(self):
        """GE1 part 4 (base lower) in-range -> PASS."""
        result = _expand_parsed(
            parse_field("1,MSL,00500,10000"),
            "GE1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["GE1__part4__qc_pass"] is True
        assert result["GE1__part4__qc_status"] == "PASS"

    def test_ge1_part4_sentinel(self):
        """GE1 part 4 sentinel (99999) -> MISSING."""
        result = _expand_parsed(
            parse_field("1,MSL,00500,99999"),
            "GE1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["GE1__part4__qc_pass"] is False
        assert result["GE1__part4__qc_status"] == "MISSING"
        assert result["GE1__part4__qc_reason"] == "SENTINEL_MISSING"


class TestQCSignalsComprehensiveGF1:
    """Comprehensive QC tests for GF1 (cloud coverage and base height)."""

    def test_gf1_part8_pass(self):
        """GF1 part 8 (cloud base height) in-range -> PASS."""
        result = _expand_parsed(
            parse_field("10,05,0,10,0,99,0,01000,0,99,0,99,0"),
            "GF1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["GF1__part8__qc_pass"] is True
        assert result["GF1__part8__qc_status"] == "PASS"

    def test_gf1_part8_out_of_range_low(self):
        """GF1 part 8 below min (-400) -> OUT_OF_RANGE."""
        result = _expand_parsed(
            parse_field("10,05,0,10,0,99,0,-0401,0,99,0,99,0"),
            "GF1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["GF1__part8__qc_pass"] is False
        assert result["GF1__part8__qc_status"] == "INVALID"
        assert result["GF1__part8__qc_reason"] == "OUT_OF_RANGE"

    def test_gf1_part8_out_of_range_high(self):
        """GF1 part 8 above max (15000) -> OUT_OF_RANGE."""
        result = _expand_parsed(
            parse_field("10,05,0,10,0,99,0,15001,0,99,0,99,0"),
            "GF1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["GF1__part8__qc_pass"] is False
        assert result["GF1__part8__qc_status"] == "INVALID"
        assert result["GF1__part8__qc_reason"] == "OUT_OF_RANGE"

    def test_gf1_part8_sentinel(self):
        """GF1 part 8 sentinel (99999) -> MISSING."""
        result = _expand_parsed(
            parse_field("10,05,0,10,0,99,0,99999,0,99,0,99,0"),
            "GF1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["GF1__part8__qc_pass"] is False
        assert result["GF1__part8__qc_status"] == "MISSING"
        assert result["GF1__part8__qc_reason"] == "SENTINEL_MISSING"

    def test_gf1_part8_bad_quality(self):
        """GF1 part 8 invalid quality -> BAD_QUALITY_CODE."""
        result = _expand_parsed(
            parse_field("10,05,0,10,0,99,0,01000,X,99,0,99,0"),
            "GF1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["GF1__part8__qc_pass"] is False
        assert result["GF1__part8__qc_status"] == "INVALID"
        assert result["GF1__part8__qc_reason"] == "BAD_QUALITY_CODE"


class TestQCSignalsComprehensiveGG:
    """Comprehensive QC tests for GG1+ (cloud layer base)."""

    def test_gg1_part3_pass(self):
        """GG1 part 3 (cloud layer base) in-range -> PASS."""
        result = _expand_parsed(
            parse_field("50,1,05000,1,99,1,99,1"),
            "GG1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["GG1__part3__qc_pass"] is True
        assert result["GG1__part3__qc_status"] == "PASS"

    def test_gg1_part3_out_of_range_low(self):
        """GG1 part 3 below min (0) -> OUT_OF_RANGE."""
        result = _expand_parsed(
            parse_field("50,1,-00001,1,99,1,99,1"),
            "GG1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["GG1__part3__qc_pass"] is False
        assert result["GG1__part3__qc_status"] == "INVALID"
        assert result["GG1__part3__qc_reason"] == "OUT_OF_RANGE"

    def test_gg1_part3_out_of_range_high(self):
        """GG1 part 3 above max (35000) -> OUT_OF_RANGE."""
        result = _expand_parsed(
            parse_field("50,1,35001,1,99,1,99,1"),
            "GG1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["GG1__part3__qc_pass"] is False
        assert result["GG1__part3__qc_status"] == "INVALID"
        assert result["GG1__part3__qc_reason"] == "OUT_OF_RANGE"

    def test_gg1_part3_sentinel(self):
        """GG1 part 3 sentinel (99999) -> MISSING."""
        result = _expand_parsed(
            parse_field("50,1,99999,1,99,1,99,1"),
            "GG1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["GG1__part3__qc_pass"] is False
        assert result["GG1__part3__qc_status"] == "MISSING"
        assert result["GG1__part3__qc_reason"] == "SENTINEL_MISSING"

    def test_gg1_part3_bad_quality(self):
        """GG1 part 3 invalid quality -> BAD_QUALITY_CODE."""
        result = _expand_parsed(
            parse_field("50,1,05000,X,99,1,99,1"),
            "GG1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["GG1__part3__qc_pass"] is False
        assert result["GG1__part3__qc_status"] == "INVALID"
        assert result["GG1__part3__qc_reason"] == "BAD_QUALITY_CODE"


class TestQCSignalsComprehensiveGH:
    """Comprehensive QC tests for GH1+ (solar irradiance)."""

    def test_gh1_part1_pass(self):
        """GH1 part 1 (irradiance) in-range -> PASS."""
        result = _expand_parsed(
            parse_field("05000,1,0,10000,1,0,20000,1,0,30000,1,0"),
            "GH1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["GH1__part1__qc_pass"] is True
        assert result["GH1__part1__qc_status"] == "PASS"

    def test_gh1_part1_out_of_range_low(self):
        """GH1 part 1 below min (0) -> OUT_OF_RANGE."""
        result = _expand_parsed(
            parse_field("-0001,1,0,10000,1,0,20000,1,0,30000,1,0"),
            "GH1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["GH1__part1__qc_pass"] is False
        assert result["GH1__part1__qc_status"] == "INVALID"
        assert result["GH1__part1__qc_reason"] == "OUT_OF_RANGE"

    def test_gh1_part1_out_of_range_high(self):
        """GH1 part 1 above max (99998) -> OUT_OF_RANGE."""
        result = _expand_parsed(
            parse_field("99999,1,0,10000,1,0,20000,1,0,30000,1,0"),
            "GH1",
            allow_quality=True,
            strict_mode=False,
        )
        # Note: 99999 is sentinel, so this tests MISSING not OUT_OF_RANGE
        assert result["GH1__part1__qc_pass"] is False
        assert result["GH1__part1__qc_status"] == "MISSING"

    def test_gh1_part1_just_above_max(self):
        """GH1 part 1 just above max (99999 is sentinel, so test 100000) -> OUT_OF_RANGE."""
        # Since we can't directly test 100000 (5 digits), test boundary with scaling
        # Max scaled is 99998 * 0.1 = 9999.8, so raw max is 99998
        result = _expand_parsed(
            parse_field("100000,1,0,10000,1,0,20000,1,0,30000,1,0"),
            "GH1",
            allow_quality=True,
            strict_mode=False,
        )
        # 100000 > 99998 max
        assert result["GH1__part1__qc_pass"] is False
        assert result["GH1__part1__qc_status"] == "INVALID"
        assert result["GH1__part1__qc_reason"] == "OUT_OF_RANGE"

    def test_gh1_part1_sentinel(self):
        """GH1 part 1 sentinel (99999) -> MISSING."""
        result = _expand_parsed(
            parse_field("99999,1,0,10000,1,0,20000,1,0,30000,1,0"),
            "GH1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["GH1__part1__qc_pass"] is False
        assert result["GH1__part1__qc_status"] == "MISSING"
        assert result["GH1__part1__qc_reason"] == "SENTINEL_MISSING"

    def test_gh1_part1_bad_quality(self):
        """GH1 part 1 invalid quality -> BAD_QUALITY_CODE."""
        result = _expand_parsed(
            parse_field("05000,X,0,10000,1,0,20000,1,0,30000,1,0"),
            "GH1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["GH1__part1__qc_pass"] is False
        assert result["GH1__part1__qc_status"] == "INVALID"
        assert result["GH1__part1__qc_reason"] == "BAD_QUALITY_CODE"

    def test_gh1_part4_pass(self):
        """GH1 part 4 (second irradiance) in-range -> PASS."""
        result = _expand_parsed(
            parse_field("05000,1,0,10000,1,0,20000,1,0,30000,1,0"),
            "GH1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["GH1__part4__qc_pass"] is True
        assert result["GH1__part4__qc_status"] == "PASS"

    def test_gh1_part4_sentinel(self):
        """GH1 part 4 sentinel (99999) -> MISSING."""
        result = _expand_parsed(
            parse_field("05000,1,0,99999,1,0,20000,1,0,30000,1,0"),
            "GH1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["GH1__part4__qc_pass"] is False
        assert result["GH1__part4__qc_status"] == "MISSING"
        assert result["GH1__part4__qc_reason"] == "SENTINEL_MISSING"

    def test_gh1_part7_pass(self):
        """GH1 part 7 (third irradiance) in-range -> PASS."""
        result = _expand_parsed(
            parse_field("05000,1,0,10000,1,0,20000,1,0,30000,1,0"),
            "GH1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["GH1__part7__qc_pass"] is True
        assert result["GH1__part7__qc_status"] == "PASS"

    def test_gh1_part10_sentinel(self):
        """GH1 part 10 (fourth irradiance) sentinel -> MISSING."""
        result = _expand_parsed(
            parse_field("05000,1,0,10000,1,0,20000,1,0,99999,1,0"),
            "GH1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["GH1__part10__qc_pass"] is False
        assert result["GH1__part10__qc_status"] == "MISSING"
        assert result["GH1__part10__qc_reason"] == "SENTINEL_MISSING"


class TestQCSignalsComprehensiveKA:
    """Comprehensive QC tests for KA1+ (period and temperature)."""

    def test_ka1_part1_pass(self):
        """KA1 part 1 (period) in-range -> PASS."""
        result = _expand_parsed(
            parse_field("100,M,+2000,1"),
            "KA1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["KA1__part1__qc_pass"] is True
        assert result["KA1__part1__qc_status"] == "PASS"

    def test_ka1_part1_out_of_range_low(self):
        """KA1 part 1 below min (1) -> OUT_OF_RANGE."""
        result = _expand_parsed(
            parse_field("000,M,+2000,1"),
            "KA1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["KA1__part1__qc_pass"] is False
        assert result["KA1__part1__qc_status"] == "INVALID"
        assert result["KA1__part1__qc_reason"] == "OUT_OF_RANGE"

    def test_ka1_part1_out_of_range_high(self):
        """KA1 part 1 above max (480) -> OUT_OF_RANGE."""
        result = _expand_parsed(
            parse_field("481,M,+2000,1"),
            "KA1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["KA1__part1__qc_pass"] is False
        assert result["KA1__part1__qc_status"] == "INVALID"
        assert result["KA1__part1__qc_reason"] == "OUT_OF_RANGE"

    def test_ka1_part1_sentinel(self):
        """KA1 part 1 sentinel (999) -> MISSING."""
        result = _expand_parsed(
            parse_field("999,M,+2000,1"),
            "KA1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["KA1__part1__qc_pass"] is False
        assert result["KA1__part1__qc_status"] == "MISSING"
        assert result["KA1__part1__qc_reason"] == "SENTINEL_MISSING"

    def test_ka1_part3_pass(self):
        """KA1 part 3 (temperature) in-range + good quality -> PASS."""
        result = _expand_parsed(
            parse_field("100,M,+0200,1"),
            "KA1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["KA1__part3__qc_pass"] is True
        assert result["KA1__part3__qc_status"] == "PASS"

    def test_ka1_part3_out_of_range_low(self):
        """KA1 part 3 below min (-1100) -> OUT_OF_RANGE."""
        result = _expand_parsed(
            parse_field("100,M,-1101,1"),
            "KA1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["KA1__part3__qc_pass"] is False
        assert result["KA1__part3__qc_status"] == "INVALID"
        assert result["KA1__part3__qc_reason"] == "OUT_OF_RANGE"

    def test_ka1_part3_out_of_range_high(self):
        """KA1 part 3 above max (6300) -> OUT_OF_RANGE."""
        result = _expand_parsed(
            parse_field("100,M,+6301,1"),
            "KA1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["KA1__part3__qc_pass"] is False
        assert result["KA1__part3__qc_status"] == "INVALID"
        assert result["KA1__part3__qc_reason"] == "OUT_OF_RANGE"

    def test_ka1_part3_sentinel(self):
        """KA1 part 3 sentinel (9999) -> MISSING."""
        result = _expand_parsed(
            parse_field("100,M,+9999,1"),
            "KA1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["KA1__part3__qc_pass"] is False
        assert result["KA1__part3__qc_status"] == "MISSING"
        assert result["KA1__part3__qc_reason"] == "SENTINEL_MISSING"

    def test_ka1_part3_bad_quality(self):
        """KA1 part 3 invalid quality -> BAD_QUALITY_CODE."""
        result = _expand_parsed(
            parse_field("100,M,+2000,X"),
            "KA1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["KA1__part3__qc_pass"] is False
        assert result["KA1__part3__qc_status"] == "INVALID"
        assert result["KA1__part3__qc_reason"] == "BAD_QUALITY_CODE"


class TestQCSignalsComprehensiveKB:
    """Comprehensive QC tests for KB1+ (period and temperature)."""

    def test_kb1_part1_pass(self):
        """KB1 part 1 (period) in-range -> PASS."""
        result = _expand_parsed(
            parse_field("100,A,+0050,1"),
            "KB1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["KB1__part1__qc_pass"] is True
        assert result["KB1__part1__qc_status"] == "PASS"

    def test_kb1_part1_out_of_range_low(self):
        """KB1 part 1 below min (1) -> OUT_OF_RANGE."""
        result = _expand_parsed(
            parse_field("000,A,+0050,1"),
            "KB1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["KB1__part1__qc_pass"] is False
        assert result["KB1__part1__qc_status"] == "INVALID"
        assert result["KB1__part1__qc_reason"] == "OUT_OF_RANGE"

    def test_kb1_part1_out_of_range_high(self):
        """KB1 part 1 above max (744) -> OUT_OF_RANGE."""
        result = _expand_parsed(
            parse_field("745,A,+0050,1"),
            "KB1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["KB1__part1__qc_pass"] is False
        assert result["KB1__part1__qc_status"] == "INVALID"
        assert result["KB1__part1__qc_reason"] == "OUT_OF_RANGE"

    def test_kb1_part1_sentinel(self):
        """KB1 part 1 sentinel (999) -> MISSING."""
        result = _expand_parsed(
            parse_field("999,A,+0050,1"),
            "KB1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["KB1__part1__qc_pass"] is False
        assert result["KB1__part1__qc_status"] == "MISSING"
        assert result["KB1__part1__qc_reason"] == "SENTINEL_MISSING"

    def test_kb1_part3_pass(self):
        """KB1 part 3 (temperature, scale 0.01) in-range + good quality -> PASS."""
        result = _expand_parsed(
            parse_field("100,A,+0050,1"),
            "KB1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["KB1__part3__qc_pass"] is True
        assert result["KB1__part3__qc_status"] == "PASS"

    def test_kb1_part3_out_of_range_low(self):
        """KB1 part 3 below min (-9900) -> OUT_OF_RANGE."""
        result = _expand_parsed(
            parse_field("100,A,-9901,1"),
            "KB1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["KB1__part3__qc_pass"] is False
        assert result["KB1__part3__qc_status"] == "INVALID"
        assert result["KB1__part3__qc_reason"] == "OUT_OF_RANGE"

    def test_kb1_part3_out_of_range_high(self):
        """KB1 part 3 above max (6300) -> OUT_OF_RANGE."""
        result = _expand_parsed(
            parse_field("100,A,+6301,1"),
            "KB1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["KB1__part3__qc_pass"] is False
        assert result["KB1__part3__qc_status"] == "INVALID"
        assert result["KB1__part3__qc_reason"] == "OUT_OF_RANGE"

    def test_kb1_part3_sentinel(self):
        """KB1 part 3 sentinel (9999) -> MISSING."""
        result = _expand_parsed(
            parse_field("100,A,+9999,1"),
            "KB1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["KB1__part3__qc_pass"] is False
        assert result["KB1__part3__qc_status"] == "MISSING"
        assert result["KB1__part3__qc_reason"] == "SENTINEL_MISSING"

    def test_kb1_part3_bad_quality(self):
        """KB1 part 3 invalid quality -> BAD_QUALITY_CODE."""
        result = _expand_parsed(
            parse_field("100,A,+0050,X"),
            "KB1",
            allow_quality=True,
            strict_mode=False,
        )
        assert result["KB1__part3__qc_pass"] is False
        assert result["KB1__part3__qc_status"] == "INVALID"
        assert result["KB1__part3__qc_reason"] == "BAD_QUALITY_CODE"


class TestRowLevelUsabilityMetricsComprehensive:
    """Comprehensive row-level usability metrics with mixed QC signals."""

    def test_all_pass_metrics(self):
        """All metrics pass QC -> usable_metric_fraction = 1.0."""
        df = pd.DataFrame({
            "OC1": ["0500,1"],  # PASS
            "TMP": ["+0250,1"],  # PASS
        })
        result = clean_noaa_dataframe(df, strict_mode=False)
        assert result["row_has_any_usable_metric"].iloc[0] == True
        assert result["usable_metric_fraction"].iloc[0] == 1.0

    def test_all_missing_metrics(self):
        """All metrics are MISSING (sentinels) -> usable_metric_fraction = 0.0."""
        df = pd.DataFrame({
            "OC1": ["9999,1"],  # MISSING
            "TMP": ["+9999,1"],  # MISSING
        })
        result = clean_noaa_dataframe(df, strict_mode=False)
        assert result["row_has_any_usable_metric"].iloc[0] == False
        assert result["usable_metric_fraction"].iloc[0] == 0.0

    def test_all_invalid_metrics(self):
        """All metrics are INVALID (out of range) -> usable_metric_fraction = 0.0."""
        df = pd.DataFrame({
            "OC1": ["0049,1"],  # OUT_OF_RANGE (below min 50)
            "MA1": ["08634,1,04499,1"],  # OUT_OF_RANGE (both parts out of range)
        })
        result = clean_noaa_dataframe(df, strict_mode=False)
        assert result["row_has_any_usable_metric"].iloc[0] == False
        assert result["usable_metric_fraction"].iloc[0] == 0.0

    def test_mixed_pass_and_missing(self):
        """Some PASS, some MISSING -> fraction in (0, 1)."""
        df = pd.DataFrame({
            "OC1": ["0500,1"],  # PASS
            "TMP": ["+9999,1"],  # MISSING
        })
        result = clean_noaa_dataframe(df, strict_mode=False)
        assert result["row_has_any_usable_metric"].iloc[0] == True
        assert 0.0 < result["usable_metric_fraction"].iloc[0] < 1.0

    def test_mixed_pass_and_invalid(self):
        """Some PASS, some INVALID -> fraction in (0, 1)."""
        df = pd.DataFrame({
            "OC1": ["0500,1"],  # PASS
            "MA1": ["08634,1,09500,1"],  # OUT_OF_RANGE (altimeter below min)
        })
        result = clean_noaa_dataframe(df, strict_mode=False)
        assert result["row_has_any_usable_metric"].iloc[0] == True
        assert 0.0 < result["usable_metric_fraction"].iloc[0] < 1.0

    def test_mixed_missing_and_invalid(self):
        """Some MISSING, some INVALID -> fraction = 0.0."""
        df = pd.DataFrame({
            "OC1": ["9999,1"],  # MISSING
            "MA1": ["08634,1,04499,1"],  # OUT_OF_RANGE (both parts out of range)
        })
        result = clean_noaa_dataframe(df, strict_mode=False)
        assert result["row_has_any_usable_metric"].iloc[0] == False
        assert result["usable_metric_fraction"].iloc[0] == 0.0

    def test_usable_metric_count_correct(self):
        """usable_metric_count reflects PASS metrics."""
        df = pd.DataFrame({
            "OC1": ["0500,1"],  # PASS
            "MA1": ["09000,1,09500,1"],  # 2 PASS (part1 and part3)
        })
        result = clean_noaa_dataframe(df, strict_mode=False)
        # OC1 contributes 1, MA1 contributes 2, total 3
        assert result["usable_metric_count"].iloc[0] >= 3

    def test_multiple_rows_metrics(self):
        """Row metrics calculated correctly for multiple rows."""
        df = pd.DataFrame({
            "OC1": ["0500,1", "9999,1", "0049,1"],  # PASS, MISSING, INVALID
        })
        result = clean_noaa_dataframe(df, strict_mode=False)
        # Row 0: PASS, should be usable
        assert result["row_has_any_usable_metric"].iloc[0] == True
        # Row 1: MISSING, not usable
        assert result["row_has_any_usable_metric"].iloc[1] == False
        # Row 2: INVALID, not usable
        assert result["row_has_any_usable_metric"].iloc[2] == False
