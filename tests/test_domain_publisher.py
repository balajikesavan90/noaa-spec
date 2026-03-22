"""Tests for registry-driven domain publisher."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from noaa_spec.domains.publisher import write_domain_datasets_from_registry


def test_write_domain_datasets_from_registry_uses_registry_domain_names(tmp_path: Path) -> None:
    cleaned = pd.DataFrame(
        {
            "station_id": ["01234567890"],
            "DATE": ["2020-01-01T00:00:00"],
            "YEAR": [2020],
            "REPORT_TYPE": ["FM-15"],
            "wind_speed_ms": [2.1],
            "WND__part4__qc_pass": [True],
            "remarks_text": ["clear sky"],
        }
    )

    rows = write_domain_datasets_from_registry(
        cleaned,
        station_slug="TEST_STATION",
        station_name="Test Station",
        output_dir=tmp_path,
        output_format="csv",
    )

    domain_names = {str(row["domain"]) for row in rows}
    assert domain_names == {"core_meteorology", "wind", "remarks"}

    wind_path = tmp_path / "TEST_STATION__wind.csv"
    assert wind_path.exists()
    wind_df = pd.read_csv(wind_path)
    assert wind_df.columns.tolist() == [
        "station_id",
        "DATE",
        "wind_speed_ms",
        "WND__part4__qc_pass",
    ]


def test_write_domain_datasets_from_registry_rejects_unknown_output_format(tmp_path: Path) -> None:
    cleaned = pd.DataFrame({"station_id": ["01234567890"], "DATE": ["2020-01-01T00:00:00"]})
    with pytest.raises(ValueError, match="Unsupported domain split output format"):
        write_domain_datasets_from_registry(
            cleaned,
            station_slug="TEST_STATION",
            station_name="Test Station",
            output_dir=tmp_path,
            output_format="json",
        )


def test_write_domain_datasets_from_registry_skips_domains_when_join_keys_missing(
    tmp_path: Path,
) -> None:
    cleaned = pd.DataFrame(
        {
            "DATE": ["2020-01-01T00:00:00"],
            "wind_speed_ms": [2.1],
            "WND__part4__qc_pass": [True],
        }
    )

    rows = write_domain_datasets_from_registry(
        cleaned,
        station_slug="TEST_STATION",
        station_name="Test Station",
        output_dir=tmp_path,
        output_format="csv",
    )
    assert rows == []


def test_write_domain_datasets_from_registry_derives_station_id_from_station_column(
    tmp_path: Path,
) -> None:
    cleaned = pd.DataFrame(
        {
            "STATION": ["01234567890"],
            "DATE": ["2020-01-01T00:00:00"],
            "YEAR": [2020],
        }
    )

    rows = write_domain_datasets_from_registry(
        cleaned,
        station_slug="TEST_STATION",
        station_name="Test Station",
        output_dir=tmp_path,
        output_format="csv",
    )
    domain_names = {str(row["domain"]) for row in rows}
    assert "core_meteorology" in domain_names
