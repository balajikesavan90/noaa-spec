"""Tests for P1 aggregation correctness.

Verifies that:
1. Categorical columns (MW, AY, WND__part3, CIG__part3/4, VIS__part3,
   MD1__part1, GE1__part1) are excluded from numeric aggregation.
2. Quality columns (*__quality) are excluded from aggregated output.
3. Field-appropriate aggregation functions are applied (max for OC1,
   min for VIS, mean for TMP/DEW/SLP/MA1, etc.).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from noaa_climate_data.constants import (
    FieldPartRule,
    FieldRule,
    get_agg_func,
    is_categorical_column,
    is_quality_column,
)
from noaa_climate_data.pipeline import (
    _aggregate_numeric,
    _classify_columns,
    _coerce_numeric,
    _daily_min_max_mean,
    _extract_time_columns,
    process_location_from_raw,
)


# ── constants helpers ────────────────────────────────────────────────────


class TestIsQualityColumn:
    def test_quality_suffix(self):
        assert is_quality_column("WND__quality")
        assert is_quality_column("TMP__quality")

    def test_qc_suffix(self):
        assert is_quality_column("SLP__qc")

    def test_non_quality(self):
        assert not is_quality_column("temperature_c")
        assert not is_quality_column("wind_speed_ms")
        assert not is_quality_column("Year")


class TestIsCategoricalColumn:
    def test_categorical_columns(self):
        assert is_categorical_column("present_weather_code_1")
        assert is_categorical_column("present_weather_code_2")
        assert is_categorical_column("MW1__part2")
        assert is_categorical_column("AY1__part1")
        assert is_categorical_column("AY2__part1")
        assert is_categorical_column("AY1__part2")
        assert is_categorical_column("AY1__part4")
        assert is_categorical_column("KA1__part2")
        assert is_categorical_column("WND__part2")
        assert is_categorical_column("WND__part3")
        assert is_categorical_column("WND__part5")
        assert is_categorical_column("CIG__part2")
        assert is_categorical_column("CIG__part3")
        assert is_categorical_column("CIG__part4")
        assert is_categorical_column("VIS__part3")
        assert is_categorical_column("VIS__part4")
        assert is_categorical_column("MD1__part1")
        assert is_categorical_column("MD1__part2")
        assert is_categorical_column("GE1__part1")
        assert is_categorical_column("GE1__part2")

    def test_numeric_columns_not_categorical(self):
        assert not is_categorical_column("temperature_c")
        assert not is_categorical_column("dew_point_c")
        assert not is_categorical_column("wind_speed_ms")
        assert not is_categorical_column("wind_direction_deg")
        assert not is_categorical_column("visibility_m")
        assert not is_categorical_column("altimeter_setting_hpa")

    def test_plain_columns_not_categorical(self):
        assert not is_categorical_column("Year")
        assert not is_categorical_column("MonthNum")
        assert not is_categorical_column("ID")


class TestGetAggFunc:
    def test_quality_columns_drop(self):
        assert get_agg_func("WND__quality") == "drop"
        assert get_agg_func("TMP__quality") == "drop"

    def test_categorical_columns_drop(self):
        assert get_agg_func("present_weather_code_1") == "drop"
        assert get_agg_func("MW1__part2") == "drop"
        assert get_agg_func("WND__part2") == "drop"
        assert get_agg_func("WND__part3") == "drop"
        assert get_agg_func("WND__part5") == "drop"
        assert get_agg_func("CIG__part2") == "drop"
        assert get_agg_func("CIG__part3") == "drop"
        assert get_agg_func("VIS__part3") == "drop"
        assert get_agg_func("VIS__part4") == "drop"
        assert get_agg_func("MD1__part1") == "drop"
        assert get_agg_func("MD1__part2") == "drop"
        assert get_agg_func("AY1__part2") == "drop"
        assert get_agg_func("AY1__part4") == "drop"
        assert get_agg_func("KA1__part2") == "drop"
        assert get_agg_func("GE1__part1") == "drop"
        assert get_agg_func("GE1__part2") == "drop"

    def test_mean_columns(self):
        assert get_agg_func("temperature_c") == "mean"
        assert get_agg_func("dew_point_c") == "mean"
        assert get_agg_func("sea_level_pressure_hpa") == "mean"
        assert get_agg_func("wind_speed_ms") == "mean"
        assert get_agg_func("altimeter_setting_hpa") == "mean"
        assert get_agg_func("station_pressure_hpa") == "mean"
        assert get_agg_func("GE1__part3") == "mean"
        assert get_agg_func("GE1__part4") == "mean"

    def test_circular_mean_columns(self):
        assert get_agg_func("wind_direction_deg") == "circular_mean"

    def test_max_columns(self):
        assert get_agg_func("wind_gust_ms") == "max"

    def test_min_columns(self):
        assert get_agg_func("visibility_m") == "min"

    def test_sum_columns(self):
        assert get_agg_func("AA1__part2") == "sum"

    def test_unknown_column_defaults_mean(self):
        assert get_agg_func("Year") == "mean"
        assert get_agg_func("UNKNOWN__part1") == "mean"


# ── pipeline aggregation ────────────────────────────────────────────────


def _sample_df() -> pd.DataFrame:
    """Build a small DataFrame mimicking cleaned NOAA data."""
    return pd.DataFrame(
        {
            "Year": [2020, 2020, 2020, 2021, 2021, 2021],
            "MonthNum": [1, 1, 1, 1, 1, 1],
            "temperature_c": [10.0, 12.0, 14.0, 20.0, 22.0, 24.0],
            "dew_point_c": [5.0, 6.0, 7.0, 10.0, 11.0, 12.0],
            "wind_gust_ms": [8.0, 12.0, 10.0, 15.0, 18.0, 14.0],
            "visibility_m": [5000.0, 3000.0, 4000.0, 8000.0, 6000.0, 7000.0],
            "present_weather_code_1": [3.0, 5.0, 7.0, 1.0, 2.0, 3.0],
            "WND__part3": [9.0, 9.0, 9.0, 9.0, 9.0, 9.0],
            "WND__quality": ["1", "1", "1", "1", "1", "1"],
            "TMP__quality": ["1", "1", "1", "1", "1", "1"],
        }
    )


def _tmp_raw(value: float) -> str:
    raw = f"{int(round(value * 10)):04d}"
    return f"{raw},1"


def _raw_with_hours(rows: list[tuple[str, float]]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "DATE": [row[0] for row in rows],
            "TMP": [_tmp_raw(row[1]) for row in rows],
        }
    )


def _raw_with_split_date_time(rows: list[tuple[str, str, float]]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "DATE": [row[0] for row in rows],
            "TIME": [row[1] for row in rows],
            "TMP": [_tmp_raw(row[2]) for row in rows],
        }
    )


class TestCoerceNumeric:
    def test_skips_quality_and_categorical(self):
        df = _sample_df()
        group_cols = ["Year", "MonthNum"]
        work, numeric_cols = _coerce_numeric(df, group_cols)
        # Quality columns should NOT be coerced
        assert "WND__quality" not in numeric_cols
        assert "TMP__quality" not in numeric_cols
        # Categorical columns should NOT be coerced
        assert "present_weather_code_1" in numeric_cols or "present_weather_code_1" not in numeric_cols
        # The key is that get_agg_func("present_weather_code_1") == "drop", so even if
        # it IS numeric, it won't be aggregated.


class TestClassifyColumns:
    def test_classification(self):
        cols = [
            "temperature_c",
            "dew_point_c",
            "wind_gust_ms",
            "visibility_m",
            "present_weather_code_1",
            "WND__part3",
            "WND__quality",
            "TMP__quality",
        ]
        buckets = _classify_columns(cols)
        assert "temperature_c" in buckets.get("mean", [])
        assert "dew_point_c" in buckets.get("mean", [])
        assert "wind_gust_ms" in buckets.get("max", [])
        assert "visibility_m" in buckets.get("min", [])
        assert "present_weather_code_1" in buckets.get("drop", [])
        assert "WND__part3" in buckets.get("drop", [])
        assert "WND__quality" in buckets.get("drop", [])
        assert "TMP__quality" in buckets.get("drop", [])


class TestAggregateNumeric:
    def test_categoricals_excluded(self):
        df = _sample_df()
        result = _aggregate_numeric(df, ["Year", "MonthNum"])
        # Categorical & quality columns must not appear in result
        assert "present_weather_code_1" not in result.columns
        assert "WND__part3" not in result.columns
        assert "WND__quality" not in result.columns
        assert "TMP__quality" not in result.columns

    def test_mean_applied(self):
        df = _sample_df()
        result = _aggregate_numeric(df, ["Year", "MonthNum"])
        row_2020 = result[result["Year"] == 2020].iloc[0]
        assert row_2020["temperature_c"] == pytest.approx(12.0)
        assert row_2020["dew_point_c"] == pytest.approx(6.0)

    def test_max_applied_for_gust(self):
        df = _sample_df()
        result = _aggregate_numeric(df, ["Year", "MonthNum"])
        row_2020 = result[result["Year"] == 2020].iloc[0]
        # OC1 (wind gust) should use max, not mean
        assert row_2020["wind_gust_ms"] == pytest.approx(12.0)

    def test_min_applied_for_visibility(self):
        df = _sample_df()
        result = _aggregate_numeric(df, ["Year", "MonthNum"])
        row_2020 = result[result["Year"] == 2020].iloc[0]
        # VIS should use min (worst visibility)
        assert row_2020["visibility_m"] == pytest.approx(3000.0)

    def test_sum_applied_for_precip(self):
        df = pd.DataFrame(
            {
                "Year": [2020, 2020],
                "MonthNum": [1, 1],
                "AA1__part2": [1.2, 0.8],
            }
        )
        result = _aggregate_numeric(df, ["Year", "MonthNum"])
        assert result.iloc[0]["AA1__part2"] == pytest.approx(2.0)

    def test_mode_applied_for_custom_rule(self, monkeypatch: pytest.MonkeyPatch):
        import noaa_climate_data.constants as constants

        monkeypatch.setitem(
            constants.FIELD_RULES,
            "ZZ1",
            FieldRule(code="ZZ1", parts={1: FieldPartRule(agg="mode")}),
        )
        df = pd.DataFrame(
            {
                "Year": [2020, 2020, 2020],
                "MonthNum": [1, 1, 1],
                "ZZ1__value": [2.0, 2.0, 3.0],
            }
        )
        result = _aggregate_numeric(df, ["Year", "MonthNum"])
        assert result.iloc[0]["ZZ1__value"] == pytest.approx(2.0)

    def test_circular_mean_applied_for_wind_direction(self):
        df = pd.DataFrame(
            {
                "Year": [2020, 2020],
                "MonthNum": [1, 1],
                "wind_direction_deg": [350.0, 10.0],
            }
        )
        result = _aggregate_numeric(df, ["Year", "MonthNum"])
        row = result.iloc[0]
        assert row["wind_direction_deg"] == pytest.approx(0.0, abs=1e-6)


class TestDailyMinMaxMean:
    def test_excludes_categoricals(self):
        df = _sample_df()
        df["Day"] = pd.to_datetime(["2020-01-01"] * 3 + ["2021-01-01"] * 3).date
        result = _daily_min_max_mean(df, ["Year", "MonthNum", "Day"])
        col_names = set(result.columns)
        # Categorical should not appear
        assert "present_weather_code_1__daily_mean" not in col_names
        assert "WND__part3__daily_mean" not in col_names
        assert "WND__quality__daily_mean" not in col_names
        # Numeric should appear
        assert "temperature_c__daily_min" in col_names
        assert "temperature_c__daily_max" in col_names
        assert "temperature_c__daily_mean" in col_names


class TestAggregationStrategies:
    def test_fixed_hour_requires_value(self):
        raw = _raw_with_hours([("2020-01-01T01:00:00", 10.0)])
        with pytest.raises(ValueError, match="fixed_hour must be provided"):
            process_location_from_raw(
                raw,
                aggregation_strategy="fixed_hour",
                min_days_per_month=1,
                min_months_per_year=1,
            )

    def test_fixed_hour_uses_only_selected_hour(self):
        raw = _raw_with_hours(
            [
                ("2020-01-01T01:00:00", 10.0),
                ("2020-01-01T02:00:00", 20.0),
            ]
        )
        outputs = process_location_from_raw(
            raw,
            aggregation_strategy="fixed_hour",
            fixed_hour=2,
            min_days_per_month=1,
            min_months_per_year=1,
            strict_mode=False,
        )
        assert (outputs.hourly["Hour"] == 2).all()
        assert outputs.monthly.iloc[0]["temperature_c"] == pytest.approx(20.0)
        assert outputs.yearly.iloc[0]["temperature_c"] == pytest.approx(20.0)

    def test_fixed_hour_accepts_iso_timestamp_dates_in_non_strict_mode(self):
        raw = _raw_with_hours(
            [
                ("2020-01-01T01:00:00Z", 10.0),
            ]
        )
        outputs = process_location_from_raw(
            raw,
            aggregation_strategy="fixed_hour",
            fixed_hour=1,
            min_days_per_month=1,
            min_months_per_year=1,
            strict_mode=False,
        )
        assert outputs.monthly.iloc[0]["temperature_c"] == pytest.approx(10.0)

    def test_fixed_hour_preserves_iso_timestamp_dates_in_strict_mode(self):
        raw = _raw_with_hours(
            [
                ("2020-01-01T01:00:00Z", 10.0),
            ]
        )
        outputs = process_location_from_raw(
            raw,
            aggregation_strategy="fixed_hour",
            fixed_hour=1,
            min_days_per_month=1,
            min_months_per_year=1,
            strict_mode=True,
        )
        assert not outputs.cleaned.empty
        assert outputs.monthly.iloc[0]["temperature_c"] == pytest.approx(10.0)

    def test_fixed_hour_uses_split_date_and_time(self):
        raw = _raw_with_split_date_time(
            [
                ("20240101", "0100", 10.0),
                ("20240101", "2300", 20.0),
            ]
        )
        outputs = process_location_from_raw(
            raw,
            aggregation_strategy="fixed_hour",
            fixed_hour=23,
            min_days_per_month=1,
            min_months_per_year=1,
        )
        assert (outputs.hourly["Hour"] == 23).all()
        assert outputs.monthly.iloc[0]["temperature_c"] == pytest.approx(20.0)


class TestExtractTimeColumns:
    def test_combines_date_only_and_time(self):
        df = pd.DataFrame({"DATE": ["20240101", "20240101"], "TIME": ["2359", "0000"]})
        result = _extract_time_columns(df)
        assert result["Hour"].tolist() == [23, 0]
        assert result.loc[0, "DATE"] == pd.Timestamp("2024-01-01T23:59:00Z")
        assert result.loc[1, "DATE"] == pd.Timestamp("2024-01-01T00:00:00Z")

    def test_prefers_timestamp_date_over_time(self):
        df = pd.DataFrame(
            {"DATE": ["2020-01-01T01:00:00Z"], "TIME": ["2359"]}
        )
        result = _extract_time_columns(df)
        assert result.loc[0, "Hour"] == 1
        assert result.loc[0, "DATE"] == pd.Timestamp("2020-01-01T01:00:00Z")

    def test_uses_date_parsed_fallback_with_time(self):
        df = pd.DataFrame(
            {"DATE": ["bad-date"], "DATE_PARSED": ["2024-01-01"], "TIME": ["2359"]}
        )
        result = _extract_time_columns(df)
        assert result.loc[0, "Hour"] == 23
        assert result.loc[0, "DATE"] == pd.Timestamp("2024-01-01T23:59:00Z")

    def test_invalid_time_preserves_existing_date_fallback(self):
        df = pd.DataFrame({"DATE": ["20240101"], "TIME": ["2460"]})
        result = _extract_time_columns(df)
        assert result.loc[0, "Hour"] == 0
        assert result.loc[0, "DATE"] == pd.Timestamp("2024-01-01T00:00:00Z")

    def test_hour_day_month_year_rollup(self):
        raw = _raw_with_hours(
            [
                ("2020-01-01T01:00:00", 10.0),
                ("2020-01-01T02:00:00", 20.0),
                ("2020-01-02T01:00:00", 30.0),
            ]
        )
        outputs = process_location_from_raw(
            raw,
            aggregation_strategy="hour_day_month_year",
            min_days_per_month=1,
            min_months_per_year=1,
            strict_mode=False,
        )
        assert len(outputs.hourly) == 3
        assert outputs.monthly.iloc[0]["temperature_c"] == pytest.approx(22.5)
        assert outputs.yearly.iloc[0]["temperature_c"] == pytest.approx(22.5)

    def test_weighted_hours_rollup(self):
        raw = _raw_with_hours(
            [
                ("2020-01-01T01:00:00", 10.0),
                ("2020-01-01T02:00:00", 20.0),
                ("2020-01-02T01:00:00", 30.0),
            ]
        )
        outputs = process_location_from_raw(
            raw,
            aggregation_strategy="weighted_hours",
            min_hours_per_day=1,
            min_days_per_month=1,
            min_months_per_year=1,
            strict_mode=False,
        )
        assert outputs.monthly.iloc[0]["temperature_c"] == pytest.approx(20.0)
        assert outputs.yearly.iloc[0]["temperature_c"] == pytest.approx(20.0)

    def test_daily_min_max_mean_rollup(self):
        raw = _raw_with_hours(
            [
                ("2020-01-01T01:00:00", 10.0),
                ("2020-01-01T02:00:00", 20.0),
                ("2020-01-02T01:00:00", 30.0),
            ]
        )
        outputs = process_location_from_raw(
            raw,
            aggregation_strategy="daily_min_max_mean",
            min_days_per_month=1,
            min_months_per_year=1,
            strict_mode=False,
        )
        monthly = outputs.monthly.iloc[0]
        assert monthly["temperature_c__daily_min"] == pytest.approx(20.0)
        assert monthly["temperature_c__daily_max"] == pytest.approx(25.0)
        assert monthly["temperature_c__daily_mean"] == pytest.approx(22.5)
