"""Fast local quickstart for the bundled NOAA-Spec sample."""

from __future__ import annotations

import argparse
from pathlib import Path
import tempfile

import pandas as pd

from .cleaning import clean_noaa_dataframe
from .deterministic_io import write_deterministic_csv


def bundled_sample_path() -> Path:
    return Path(__file__).resolve().parents[2] / "reproducibility" / "minimal" / "station_raw.csv"


def default_output_dir() -> Path:
    return Path(tempfile.gettempdir()) / "noaa-spec-quickstart"


def run_quickstart(*, output_dir: Path) -> Path:
    raw_path = bundled_sample_path()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "station_cleaned.csv"

    raw = pd.read_csv(raw_path, dtype=str)
    cleaned = clean_noaa_dataframe(raw, keep_raw=False, strict_mode=True)
    write_deterministic_csv(
        cleaned,
        output_path,
        sort_by=("STATION", "DATE"),
        float_format="%.1f",
    )
    return output_path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the bundled NOAA-Spec quickstart sample")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=default_output_dir(),
        help="Directory where the cleaned quickstart CSV will be written.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    output_path = run_quickstart(output_dir=args.output_dir)
    cleaned = pd.read_csv(output_path, low_memory=False)

    preview_columns = [
        "STATION",
        "DATE",
        "temperature_c",
        "temperature_quality_code",
        "wind_speed_ms",
        "visibility_m",
    ]
    existing_preview_columns = [column for column in preview_columns if column in cleaned.columns]

    print(f"Cleaned sample written to: {output_path.resolve()}")
    print("Key columns:")
    print("- STATION: NOAA station identifier.")
    print("- DATE: observation timestamp from the raw record.")
    print("- temperature_c: cleaned air temperature in Celsius.")
    print("- temperature_quality_code: NOAA QC code kept alongside the cleaned value.")
    print("- wind_speed_ms and visibility_m: normalized numeric weather fields.")
    print()
    print("Example transformation:")
    print("- Raw TMP token +9999,9 becomes an empty temperature_c value with QC code 9 preserved.")
    print()
    print("Preview:")
    print(cleaned[existing_preview_columns].head().to_string(index=False))


if __name__ == "__main__":
    main()
