"""Utilities for listing and downloading NOAA Global Hourly data."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import time
import pandas as pd
import requests

from .constants import BASE_URL


@dataclass(frozen=True)
class StationMetadata:
    latitude: float | None
    longitude: float | None
    elevation: float | None
    name: str | None
    file_name: str


def fetch_station_metadata_for_years(
    file_name: str,
    years: Iterable[int],
    sleep_seconds: float = 0.0,
    retries: int = 3,
    backoff_base: float = 0.5,
    backoff_max: float = 8.0,
) -> tuple[StationMetadata | None, int | None]:
    """Fetch station metadata by trying multiple years in order."""
    for year in years:
        metadata = fetch_station_metadata(
            file_name,
            year,
            retries=retries,
            backoff_base=backoff_base,
            backoff_max=backoff_max,
        )
        if metadata is not None:
            return metadata, int(year)
        if sleep_seconds > 0:
            time.sleep(sleep_seconds)
    return None, None


def _normalize_year_dir(text: str | object) -> str | None:
    if text is None:
        return None
    text = str(text).strip()
    if text.lower() == "nan":
        return None
    if not text.endswith("/"):
        return None
    year = text[:-1]
    if not year.isdigit():
        return None
    if len(year) != 4:
        return None
    return year


def _sleep_backoff(attempt: int, backoff_base: float, backoff_max: float) -> None:
    delay = min(backoff_max, backoff_base * (2**attempt))
    time.sleep(delay)


def _read_html_with_retries(
    url: str,
    retries: int,
    backoff_base: float,
    backoff_max: float,
) -> list[pd.DataFrame]:
    for attempt in range(retries + 1):
        try:
            return pd.read_html(url)
        except Exception:
            if attempt >= retries:
                return []
            _sleep_backoff(attempt, backoff_base, backoff_max)
    return []


def _read_csv_head_with_retries(
    url: str,
    retries: int,
    backoff_base: float,
    backoff_max: float,
) -> pd.DataFrame | None:
    for attempt in range(retries + 1):
        try:
            return pd.read_csv(url, nrows=1, dtype=str, low_memory=False)
        except Exception:
            if attempt >= retries:
                return None
            _sleep_backoff(attempt, backoff_base, backoff_max)
    return None


def get_years(
    retries: int = 3,
    backoff_base: float = 0.5,
    backoff_max: float = 8.0,
) -> list[str]:
    """Fetch available year directories from NOAA access page."""
    tables = _read_html_with_retries(
        BASE_URL + "/",
        retries=retries,
        backoff_base=backoff_base,
        backoff_max=backoff_max,
    )
    if not tables:
        return []
    year_cells = tables[0].iloc[:, 0].astype(str).tolist()
    years = [
        year
        for cell in year_cells
        if (year := _normalize_year_dir(cell)) is not None
    ]
    return sorted(set(years))


def get_file_list_for_year(
    year: str,
    retries: int = 3,
    backoff_base: float = 0.5,
    backoff_max: float = 8.0,
) -> list[str]:
    """Fetch available CSV filenames for a given year directory."""
    url = f"{BASE_URL}/{year}/"
    tables = _read_html_with_retries(
        url,
        retries=retries,
        backoff_base=backoff_base,
        backoff_max=backoff_max,
    )
    if not tables:
        return []
    entries = tables[0].iloc[:, 0].tolist()
    results: list[str] = []
    for entry in entries:
        if entry is None:
            continue
        value = str(entry).strip()
        if value.lower() == "nan":
            continue
        if value.endswith(".csv"):
            results.append(value)
    return results


def build_file_list(
    years: Iterable[str],
    sleep_seconds: float = 0.0,
    retries: int = 3,
    backoff_base: float = 0.5,
    backoff_max: float = 8.0,
) -> pd.DataFrame:
    """Build a dataframe with YEAR and FileName columns."""
    frames: list[pd.DataFrame] = []
    for year in years:
        files = get_file_list_for_year(
            year,
            retries=retries,
            backoff_base=backoff_base,
            backoff_max=backoff_max,
        )
        if not files:
            continue
        frames.append(pd.DataFrame({"YEAR": year, "FileName": files}))
        if sleep_seconds > 0:
            time.sleep(sleep_seconds)
    if not frames:
        return pd.DataFrame(columns=["YEAR", "FileName"])
    return pd.concat(frames, ignore_index=True)


def count_years_per_file(
    file_list: pd.DataFrame,
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    """Count occurrences per file within the given year range."""
    filtered = file_list[
        (file_list["YEAR"].astype(int) >= start_year)
        & (file_list["YEAR"].astype(int) <= end_year)
    ]
    counts = (
        filtered.groupby("FileName", as_index=False)["YEAR"]
        .count()
        .rename(columns={"YEAR": "No_Of_Years"})
    )
    return counts


def url_for(year: int | str, file_name: str) -> str:
    normalized = normalize_station_file_name(file_name)
    return f"{BASE_URL}/{year}/{normalized}"


def normalize_station_file_name(file_name: str) -> str:
    """Normalize station file names to the Global Hourly CSV convention.

    NOAA documentation notes filenames can use USAF and WBAN identifiers with
    a dash and, for archive files, a year suffix (e.g., 723150-03812-2006).
    The Global Hourly CSV access directory uses the concatenated identifier
    without dashes and no year suffix. This helper accepts either style and
    returns the access-compatible name ending in .csv.
    """
    name = Path(file_name).name.strip()
    if name.lower().endswith(".csv"):
        name = name[:-4]

    parts = [part for part in name.split("-") if part]
    if len(parts) >= 2 and parts[-1].isdigit() and len(parts[-1]) == 4:
        parts = parts[:-1]

    if parts:
        name = "".join(parts)

    return f"{name}.csv"


def _url_exists(
    url: str,
    timeout: int = 20,
    retries: int = 3,
    backoff_base: float = 0.5,
    backoff_max: float = 8.0,
) -> bool:
    for attempt in range(retries + 1):
        try:
            response = requests.head(url, timeout=timeout)
        except requests.RequestException:
            response = None
        if response is not None and response.status_code == 200:
            return True
        if response is not None and response.status_code == 404:
            return False
        if attempt >= retries:
            return False
        _sleep_backoff(attempt, backoff_base, backoff_max)
    return False


def fetch_station_metadata(
    file_name: str,
    year: int,
    retries: int = 3,
    backoff_base: float = 0.5,
    backoff_max: float = 8.0,
) -> StationMetadata | None:
    """Fetch station metadata by reading the first row of a CSV file."""
    normalized = normalize_station_file_name(file_name)
    url = url_for(year, normalized)
    if not _url_exists(
        url,
        retries=retries,
        backoff_base=backoff_base,
        backoff_max=backoff_max,
    ):
        return None
    frame = _read_csv_head_with_retries(
        url,
        retries=retries,
        backoff_base=backoff_base,
        backoff_max=backoff_max,
    )
    if frame is None:
        return None
    if frame.empty:
        return None
    row = frame.iloc[0]
    def _to_float(value: object) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    return StationMetadata(
        latitude=_to_float(row.get("LATITUDE")),
        longitude=_to_float(row.get("LONGITUDE")),
        elevation=_to_float(row.get("ELEVATION")),
        name=str(row.get("NAME")) if row.get("NAME") is not None else None,
        file_name=normalized,
    )
