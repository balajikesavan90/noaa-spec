"""Download and clean one NOAA Global Hourly station across a year range."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from noaa_spec import noaa_client
from noaa_spec.cleaning import clean_noaa_dataframe
from noaa_spec.deterministic_io import write_deterministic_csv


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download and clean a single NOAA Global Hourly station.",
    )
    parser.add_argument("--station", required=True, help="NOAA station identifier or CSV filename.")
    parser.add_argument("--start-year", required=True, type=int, help="First year to download.")
    parser.add_argument("--end-year", required=True, type=int, help="Last year to download.")
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Directory where Raw.csv and Cleaned.csv will be written.",
    )
    return parser.parse_args()


def _year_range(start_year: int, end_year: int) -> range:
    if end_year < start_year:
        raise ValueError("--end-year must be greater than or equal to --start-year")
    return range(start_year, end_year + 1)


def main() -> None:
    args = _parse_args()

    try:
        years = _year_range(args.start_year, args.end_year)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    output_dir = args.output_dir
    raw_path = output_dir / "Raw.csv"
    cleaned_path = output_dir / "Cleaned.csv"
    station_file = noaa_client.normalize_station_file_name(args.station)

    frames: list[pd.DataFrame] = []
    for year in years:
        url = noaa_client.url_for(year, station_file)
        print(f"Downloading {station_file} for {year}")
        try:
            frame = noaa_client.read_csv_url_with_retries(url)
        except RuntimeError as exc:
            raise SystemExit(str(exc)) from exc
        if frame is None:
            print(f"No data found for {year}")
            continue
        print(f"Downloaded {len(frame)} rows for {year}")
        frames.append(frame)

    if not frames:
        raise SystemExit(
            "No NOAA rows were downloaded. Check the station identifier, year range, "
            "network access, and whether the station has Global Hourly CSV files for those years."
        )

    raw = pd.concat(frames, ignore_index=True)

    print(f"Writing raw data to {raw_path}")
    write_deterministic_csv(raw, raw_path, sort_by=("STATION", "DATE"))

    print("Cleaning downloaded data")
    cleaned = clean_noaa_dataframe(raw, keep_raw=False, strict_mode=True)

    print(f"Writing cleaned data to {cleaned_path}")
    write_deterministic_csv(
        cleaned,
        cleaned_path,
        sort_by=("STATION", "DATE"),
        float_format="%.1f",
    )

    print(f"Wrote {len(raw)} raw rows and {len(cleaned)} cleaned rows to {output_dir.resolve()}")


if __name__ == "__main__":
    main()
