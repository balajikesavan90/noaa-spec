"""Internal helper for rerunning the minimal cleaning fixture.

The reviewer-facing workflow is the public `noaa-spec clean` CLI documented in
REPRODUCIBILITY.md. This helper remains for maintainer convenience only.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import tempfile

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from noaa_spec.cleaning import clean_noaa_dataframe
from noaa_spec.deterministic_io import write_deterministic_csv


RAW_RELPATH = Path("reproducibility/minimal/station_raw.csv")
DEFAULT_OUT = "noaa-spec-sample.csv"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the tracked public NOAA-Spec cleaning example."
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
    raw_path = PROJECT_ROOT / RAW_RELPATH
    cleaned_path = args.out or (Path(tempfile.gettempdir()) / DEFAULT_OUT)
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
