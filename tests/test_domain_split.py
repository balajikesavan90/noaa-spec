"""Tests for optional domain split utilities."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from noaa_spec.internal.domain_split import (
    split_station_cleaned_by_domain,
    station_metadata_mapping_row,
)


def _sample_cleaned() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "station_id": ["01116099999", "01116099999"],
            "station_name": ["TEST STATION", "TEST STATION"],
            "DATE": ["2020-01-01T00:00:00Z", "2020-01-01T01:00:00Z"],
            "LATITUDE": [12.34, 12.34],
            "LONGITUDE": [56.78, 56.78],
            "ELEVATION": [100.0, 100.0],
            "Year": [2020, 2020],
            "MonthNum": [1, 1],
            "Day": ["2020-01-01", "2020-01-01"],
            "Hour": [0, 1],
            "temperature_c": [10.0, 11.0],
            "TMP__qc_pass": [True, True],
            "wind_speed_ms": [3.0, 4.0],
        }
    )


def test_split_station_cleaned_by_domain_excludes_station_metadata_columns(
    tmp_path: Path,
) -> None:
    manifest_rows = split_station_cleaned_by_domain(
        _sample_cleaned(),
        station_slug="TEST_STATION",
        station_name="TEST STATION",
        output_dir=tmp_path,
    )

    assert manifest_rows
    temp_df = pd.read_csv(tmp_path / "TEST_STATION__temperature.csv")
    assert "station_name" not in temp_df.columns
    assert "LATITUDE" not in temp_df.columns
    assert "LONGITUDE" not in temp_df.columns
    assert "ELEVATION" not in temp_df.columns
    assert "station_id" in temp_df.columns


def test_station_metadata_mapping_row_includes_separate_mapping_fields() -> None:
    row = station_metadata_mapping_row(
        _sample_cleaned(),
        station_slug="TEST_STATION",
        station_name="TEST STATION",
        station_id_fallback="FALLBACK_ID",
    )

    assert row["station_id"] == "01116099999"
    assert row["station_slug"] == "TEST_STATION"
    assert row["station_name"] == "TEST STATION"
    assert row["LATITUDE"] == 12.34
    assert row["LONGITUDE"] == 56.78
    assert row["ELEVATION"] == 100.0
