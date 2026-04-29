"""Public command-line interface for deterministic NOAA cleaning."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
import sys

import pandas as pd

from . import __version__
from .cleaning import clean_noaa_dataframe
from .deterministic_io import write_deterministic_csv


def _clean_csv_to_csv(input_csv: Path, output_csv: Path) -> Path:
    raw = pd.read_csv(input_csv, dtype=str)
    cleaned = clean_noaa_dataframe(raw, keep_raw=False, strict_mode=True)
    _print_strict_parse_summary(cleaned)
    write_deterministic_csv(
        cleaned,
        output_csv,
        sort_by=("STATION", "DATE"),
        float_format="%.1f",
    )
    return output_csv


def _print_strict_parse_summary(cleaned: pd.DataFrame) -> None:
    summary = cleaned.attrs.get("strict_parse_summary")
    if not summary:
        return

    skipped_count = int(summary.get("skipped_encoded_column_count", 0))
    if skipped_count <= 0:
        return

    malformed_columns = list(summary.get("malformed_section_identifier_columns", ()))
    unknown_columns = list(summary.get("unknown_identifier_columns", ()))
    details: list[str] = []
    if malformed_columns:
        details.append(
            "malformed section identifier token(s): "
            + ", ".join(sorted(malformed_columns))
        )
    if unknown_columns:
        details.append(
            "unsupported identifier(s): " + ", ".join(sorted(unknown_columns))
        )

    noun = "column" if skipped_count == 1 else "columns"
    detail_text = "; ".join(details)
    sys.stderr.write(
        "WARNING: strict parsing left "
        f"{skipped_count} encoded NOAA-looking {noun} unexpanded"
        + (f" ({detail_text})" if detail_text else "")
        + ". Use --verbose for detailed parse warnings.\n"
    )


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
            "as the primary observation identifier columns."
        ),
        epilog=(
            "Primary reproducibility workflow: noaa-spec clean INPUT.csv OUTPUT.csv"
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
        type=Path,
        help="Output path for the cleaned CSV.",
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

    written_path = _clean_csv_to_csv(args.input_csv, args.output_csv)
    print(f"Wrote cleaned CSV to {written_path.resolve()}")


if __name__ == "__main__":
    main()
