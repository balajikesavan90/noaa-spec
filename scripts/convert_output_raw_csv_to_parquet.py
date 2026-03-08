#!/usr/bin/env python3
"""Create parquet copies of station raw CSV files under an output root.

This utility does not change cleaning-run behavior. It only materializes
`LocationData_Raw.parquet` files next to existing `LocationData_Raw.csv` files.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create LocationData_Raw.parquet beside LocationData_Raw.csv for each station.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("output"),
        help="Root containing station folders (default: output)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite existing LocationData_Raw.parquet files",
    )
    return parser.parse_args()


def _is_station_dir(path: Path) -> bool:
    return path.is_dir() and path.name.isdigit() and len(path.name) == 11


def main() -> None:
    args = _parse_args()
    output_root: Path = args.output_root

    if not output_root.exists() or not output_root.is_dir():
        raise FileNotFoundError(f"Output root not found or not a directory: {output_root}")

    station_dirs = sorted(path for path in output_root.iterdir() if _is_station_dir(path))
    created = 0
    skipped_missing_csv = 0
    skipped_existing = 0

    for station_dir in station_dirs:
        csv_path = station_dir / "LocationData_Raw.csv"
        parquet_path = station_dir / "LocationData_Raw.parquet"

        if not csv_path.exists():
            skipped_missing_csv += 1
            print(f"SKIP {station_dir.name}: missing {csv_path.name}")
            continue

        if parquet_path.exists() and not args.overwrite:
            skipped_existing += 1
            print(f"SKIP {station_dir.name}: {parquet_path.name} already exists")
            continue

        raw = pd.read_csv(csv_path, low_memory=False)
        raw.to_parquet(parquet_path, index=False)
        created += 1
        print(f"OK   {station_dir.name}: wrote {parquet_path.name} ({len(raw)} rows)")

    print(
        "Conversion summary: "
        f"stations={len(station_dirs)} created={created} "
        f"skipped_existing={skipped_existing} skipped_missing_csv={skipped_missing_csv}"
    )


if __name__ == "__main__":
    main()
