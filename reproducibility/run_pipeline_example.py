"""Run tracked cleaning fixtures used by public verification and maintainer tests."""

from __future__ import annotations

import argparse
from pathlib import Path
import tempfile

import pandas as pd

from noaa_spec.cleaning import clean_noaa_dataframe
from noaa_spec.deterministic_io import write_deterministic_csv


EXAMPLES = {
    "minimal": {
        "raw_relpath": Path("reproducibility/minimal/station_raw.csv"),
        "default_out": "noaa-spec-sample.csv",
    },
    "full_station": {
        "raw_relpath": Path("maintainer/reproducibility/full_station/station_raw.csv"),
        "default_out": "noaa-spec-full-station.csv",
    },
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the reproducibility cleaning example"
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Optional output path for the canonical cleaned CSV",
    )
    parser.add_argument(
        "--example",
        choices=sorted(EXAMPLES),
        default="minimal",
        help="Tracked reproducibility example to run",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    example = EXAMPLES[args.example]
    raw_path = repo_root / example["raw_relpath"]
    cleaned_path = args.out or (Path(tempfile.gettempdir()) / example["default_out"])
    cleaned_path.parent.mkdir(parents=True, exist_ok=True)

    raw = pd.read_csv(raw_path, dtype=str)
    cleaned = clean_noaa_dataframe(raw, keep_raw=False, strict_mode=True)
    write_deterministic_csv(
        cleaned,
        cleaned_path,
        sort_by=("STATION", "DATE"),
        float_format="%.1f",
    )


if __name__ == "__main__":
    main()
