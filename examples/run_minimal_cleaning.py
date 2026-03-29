"""Minimal runnable example for the installed noaa_spec package."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from noaa_spec.cleaning import clean_noaa_dataframe
from noaa_spec.deterministic_io import write_deterministic_csv


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a minimal NOAA-Spec cleaning example")
    parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Output CSV path for the cleaned example data.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    raw_path = Path(__file__).resolve().parents[1] / "reproducibility" / "minimal" / "station_raw.csv"
    raw = pd.read_csv(raw_path, dtype=str)
    cleaned = clean_noaa_dataframe(raw, keep_raw=False, strict_mode=True)
    write_deterministic_csv(
        cleaned,
        args.out,
        sort_by=("STATION", "DATE"),
        float_format="%.1f",
    )

    preview_columns = [
        "STATION",
        "DATE",
        "temperature_c",
        "temperature_quality_code",
        "wind_speed_ms",
        "visibility_m",
    ]
    existing_preview_columns = [column for column in preview_columns if column in cleaned.columns]

    print(f"Wrote cleaned example to: {args.out.resolve()}")
    print("Preview:")
    print(cleaned[existing_preview_columns].head().to_string(index=False))


if __name__ == "__main__":
    main()
