"""Minimal runnable example for the installed noaa_spec package."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from noaa_spec.cleaning import clean_noaa_dataframe


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
    repo_root = Path(__file__).resolve().parents[1]
    raw_path = repo_root / "reproducibility" / "minimal" / "station_raw.csv"
    raw = pd.read_csv(raw_path, dtype=str)
    cleaned = clean_noaa_dataframe(raw, keep_raw=False, strict_mode=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(args.out, index=False, float_format="%.1f")


if __name__ == "__main__":
    main()
