"""Tests for publication contract validation helpers."""

from __future__ import annotations

import pandas as pd
import pytest

from noaa_climate_data.contract_validation import (
    find_sentinel_leakage,
    sentinel_values_for_column,
    validate_no_sentinel_leakage,
)


def test_sentinel_values_for_column_resolves_friendly_column_names() -> None:
    sentinels = sentinel_values_for_column("temperature_c")
    assert 999.9 in sentinels


def test_find_sentinel_leakage_detects_leaked_values() -> None:
    cleaned = pd.DataFrame(
        {
            "station_id": ["01234567890", "01234567890"],
            "DATE": ["2020-01-01T00:00:00", "2020-01-01T01:00:00"],
            "temperature_c": [999.9, 12.3],
            "wind_speed_ms": [1.2, 2.5],
        }
    )

    leaks = find_sentinel_leakage(cleaned)
    assert leaks == {"temperature_c": 1}


def test_validate_no_sentinel_leakage_raises_on_contract_violation() -> None:
    cleaned = pd.DataFrame({"temperature_c": [999.9, 5.0]})
    with pytest.raises(ValueError, match="sentinel leakage"):
        validate_no_sentinel_leakage(cleaned)


def test_validate_no_sentinel_leakage_allows_clean_numeric_values() -> None:
    cleaned = pd.DataFrame({"temperature_c": [12.0, 5.0, None], "remarks_text": ["ok", None, "ok"]})
    validate_no_sentinel_leakage(cleaned)
