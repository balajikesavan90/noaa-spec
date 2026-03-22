"""Run a small cleaning example for reproducibility artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from noaa_spec.cleaning import clean_noaa_dataframe


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the reproducibility cleaning example"
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Optional output path for the cleaned CSV",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    raw_path = repo_root / "reproducibility" / "sample_station_raw.txt"
    cleaned_path = args.out or (repo_root / "reproducibility" / "sample_station_cleaned.csv")

    raw = pd.read_csv(raw_path, dtype=str)
    cleaned = clean_noaa_dataframe(raw, keep_raw=False, strict_mode=True)
    cleaned.to_csv(cleaned_path, index=False, float_format="%.1f")


if __name__ == "__main__":
    main()
