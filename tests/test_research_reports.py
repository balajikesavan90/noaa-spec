"""Tests for research report generation (P3 artifacts)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from noaa_climate_data.research_reports import (
    ResearchReportContext,
    generate_aggregation_report,
    generate_quality_report,
    write_research_reports,
)


def _sample_raw() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "DATE": [
                "2020-01-01T00:00:00",
                "2020-01-01T01:00:00",
                "bad-date",
                "2020-01-02T00:00:00",
            ],
            "TMP": ["0123,1", "9999,1", "0110,3", "0100,1"],
            "DEW": ["0050,1", "9999,1", "0040,1", "0030,1"],
        }
    )


def _sample_cleaned() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "DATE": [
                "2020-01-01T00:00:00Z",
                "2020-01-01T01:00:00Z",
                "2020-01-02T00:00:00Z",
            ],
            "Year": [2020, 2020, 2020],
            "MonthNum": [1, 1, 1],
            "Day": ["2020-01-01", "2020-01-01", "2020-01-02"],
            "Hour": [0, 1, 0],
            "station_name": ["TEST", "TEST", "TEST"],
            "temperature_c": [12.3, None, 10.0],
            "TMP__part2": ["1", "1", "1"],
            "dew_point_c": [5.0, None, 3.0],
            "DEW__part2": ["1", "1", "1"],
            "wind_speed_ms": [4.0, 5.0, 3.0],
            "wind_direction_deg": [350.0, 10.0, 20.0],
            "present_weather_code_1": [10, 20, 30],
            "TMP__qc_pass": [True, False, True],
            "row_has_any_usable_metric": [True, True, True],
            "usable_metric_fraction": [1.0, 0.5, 1.0],
        }
    )


def test_generate_quality_report_has_required_sections() -> None:
    context = ResearchReportContext(
        station_id="01234567890",
        station_name="TEST",
        access_date="2026-02-28",
        run_date_utc="2026-02-28T00:00:00Z",
        version="0.1.0",
        authors="Balaji Kesavan",
    )
    report, summary = generate_quality_report(_sample_raw(), _sample_cleaned(), context)

    assert report["metadata"]["report_type"] == "data_quality"
    assert report["row_counts"]["raw_rows"] == 4
    assert report["row_counts"]["cleaned_rows"] == 3
    assert report["row_counts"]["dropped_rows"] == 1
    assert "coverage_completeness" in report
    assert "sentinel_replacement_counts" in report
    assert "quality_flag_filtering_counts" in report
    assert "applied_scale_factors" in report
    assert "citation" in report

    assert {"column", "missing_count", "missing_pct"}.issubset(summary.columns)
    assert len(summary) == len(_sample_cleaned().columns)


def test_generate_aggregation_report_includes_strategy_and_drop_columns() -> None:
    cleaned = _sample_cleaned()
    hourly = cleaned.copy()
    monthly = pd.DataFrame({"Year": [2020], "MonthNum": [1], "temperature_c": [11.15]})
    yearly = pd.DataFrame({"Year": [2020], "temperature_c": [11.15]})
    context = ResearchReportContext(
        station_id="01234567890",
        station_name="TEST",
        access_date="2026-02-28",
        run_date_utc="2026-02-28T00:00:00Z",
        version="0.1.0",
        authors="Balaji Kesavan",
    )

    report = generate_aggregation_report(
        cleaned,
        hourly,
        monthly,
        yearly,
        context,
        aggregation_strategy="best_hour",
        fixed_hour=None,
        min_days_per_month=1,
        min_months_per_year=1,
    )

    assert report["metadata"]["report_type"] == "aggregation_assumptions"
    assert report["strategy"]["name"] == "best_hour"
    assert report["strategy"]["best_hour_selected"] in {0, 1}
    assert isinstance(report["strategy"]["day_coverage_per_hour"], list)
    assert "dropped_columns" in report
    assert "present_weather_code_1" in report["dropped_columns"]
    assert "citation" in report


def test_write_research_reports_writes_expected_files(tmp_path: Path) -> None:
    context = ResearchReportContext(
        station_id="01234567890",
        station_name="TEST",
        access_date="2026-02-28",
        run_date_utc="2026-02-28T00:00:00Z",
        version="0.1.0",
        authors="Balaji Kesavan",
    )
    quality_report, quality_summary = generate_quality_report(
        _sample_raw(),
        _sample_cleaned(),
        context,
    )
    aggregation_report = generate_aggregation_report(
        _sample_cleaned(),
        _sample_cleaned(),
        pd.DataFrame({"Year": [2020], "MonthNum": [1], "temperature_c": [11.15]}),
        pd.DataFrame({"Year": [2020], "temperature_c": [11.15]}),
        context,
        aggregation_strategy="best_hour",
        fixed_hour=None,
        min_days_per_month=1,
        min_months_per_year=1,
    )

    paths = write_research_reports(tmp_path, quality_report, quality_summary, aggregation_report)
    assert paths["quality_json"].exists()
    assert paths["quality_md"].exists()
    assert paths["quality_csv"].exists()
    assert paths["aggregation_json"].exists()
    assert paths["aggregation_md"].exists()