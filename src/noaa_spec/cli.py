"""Public command-line interface for deterministic NOAA cleaning."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd

from . import __version__
from .cleaning import clean_noaa_dataframe
from .deterministic_io import write_deterministic_csv


def _clean_csv_to_csv(input_csv: Path, output_csv: Path) -> Path:
    raw = pd.read_csv(input_csv, dtype=str)
    cleaned = clean_noaa_dataframe(raw, keep_raw=False, strict_mode=True)
    write_deterministic_csv(
        cleaned,
        output_csv,
        sort_by=("STATION", "DATE"),
        float_format="%.1f",
    )
    return output_csv


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="noaa-spec",
        description=(
            "Clean a NOAA ISD / Global Hourly raw CSV into a deterministic "
            "observation-level cleaned CSV with normalized documented sentinels, "
            "preserved QC context, and checksum-stable output for the documented "
            "supported fields. When the input includes a `raw_line` or `RAW_LINE` "
            "source column, the cleaner also performs raw record/header structural "
            "validation on that column. The public cleaned CSV uses STATION and DATE "
            "as the reviewer-visible identifier columns."
        ),
        epilog=(
            "Primary reviewer workflow: noaa-spec clean INPUT.csv OUTPUT.csv"
        ),
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    clean_parser = subparsers.add_parser(
        "clean",
        help="Clean a NOAA raw CSV into the cleaned CSV.",
        description=(
            "Read a NOAA ISD / Global Hourly CSV, replace sentinel-coded values "
            "with nulls, preserve QC columns, and write a deterministic "
            "cleaned CSV. Raw fixed-width record/header validation is applied only "
            "when the input supplies a raw_line or RAW_LINE source column."
        ),
    )
    clean_parser.add_argument("input_csv", type=Path, help="Input NOAA raw CSV path.")
    clean_parser.add_argument(
        "output_csv",
        nargs="?",
        type=Path,
        help="Output path for the cleaned CSV.",
    )
    clean_parser.add_argument(
        "--out",
        dest="output_csv_flag",
        type=Path,
        default=None,
        help=(
            "Legacy alternate output path form. The canonical reviewer form is "
            "the positional OUTPUT.csv argument."
        ),
    )
    clean_parser.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help="Show detailed [PARSE_STRICT] validation warnings during cleaning.",
    )

    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    if args.command != "clean":
        raise ValueError(f"Unsupported public command: {args.command}")

    cleaning_logger = logging.getLogger("noaa_spec.cleaning")
    if not args.verbose:
        cleaning_logger.setLevel(logging.ERROR)

    output_path = args.output_csv_flag or args.output_csv
    if output_path is None:
        raise SystemExit(
            "Provide an output path as OUTPUT.csv. "
            "--out OUTPUT.csv remains supported as a legacy alternate."
        )

    written_path = _clean_csv_to_csv(args.input_csv, output_path)
    print(f"Wrote cleaned CSV to {written_path.resolve()}")


if __name__ == "__main__":
    main()
