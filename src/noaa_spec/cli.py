"""Public command-line interface for deterministic NOAA cleaning."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd

from . import __version__
from .cleaning import clean_noaa_dataframe
from .deterministic_io import write_deterministic_csv
from .internal.domain_split import sanitize_station_slug, split_station_cleaned_by_domain


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


def _first_non_null_text(frame: pd.DataFrame, column: str) -> str | None:
    if column not in frame.columns:
        return None
    values = frame[column].dropna()
    if values.empty:
        return None
    text = str(values.iloc[0]).strip()
    return text or None


def _split_domains(
    cleaned_csv: Path,
    output_dir: Path,
    *,
    prefix: str | None = None,
    include_other: bool = True,
) -> Path:
    cleaned = pd.read_csv(cleaned_csv, low_memory=False)
    station_name = (
        _first_non_null_text(cleaned, "NAME")
        or _first_non_null_text(cleaned, "station_name")
        or cleaned_csv.stem
    )
    station_slug = sanitize_station_slug(prefix or station_name or cleaned_csv.stem)
    manifest_rows = split_station_cleaned_by_domain(
        cleaned,
        station_slug=station_slug,
        station_name=station_name,
        output_dir=output_dir,
        include_other=include_other,
        output_format="csv",
    )
    manifest_path = output_dir / f"{station_slug}__manifest.csv"
    write_deterministic_csv(
        pd.DataFrame(manifest_rows),
        manifest_path,
        sort_by=("domain",),
    )
    return manifest_path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="noaa-spec",
        description=(
            "Clean a NOAA ISD / Global Hourly raw CSV into a deterministic "
            "observation-level cleaned CSV with normalized sentinels, preserved QC "
            "semantics, and deterministic output for a given input. The public "
            "cleaned CSV uses STATION and DATE as the reviewer-visible identifier "
            "columns."
        ),
        epilog=(
            "Primary workflow: noaa-spec clean INPUT.csv OUTPUT.csv "
            "or noaa-spec clean INPUT.csv --out OUTPUT.csv. "
            "Optional utility outside the core JOSS contribution: "
            "noaa-spec split-domains CLEANED.csv OUTPUT_DIR."
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
            "cleaned CSV."
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
        help="Output path for the cleaned CSV.",
    )
    clean_parser.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help="Show detailed [PARSE_STRICT] validation warnings during cleaning.",
    )

    split_parser = subparsers.add_parser(
        "split-domains",
        help=(
            "Optional utility outside the core JOSS contribution: split a "
            "cleaned CSV into convenience domain CSVs."
        ),
        description=(
            "Read an existing canonical cleaned CSV and write analysis-friendly "
            "domain subsets. This is a convenience layer derived from cleaned "
            "output, not the core JOSS contribution or primary reproducibility "
            "workflow."
        ),
    )
    split_parser.add_argument(
        "cleaned_csv",
        type=Path,
        help="Canonical cleaned CSV produced by noaa-spec clean.",
    )
    split_parser.add_argument(
        "output_dir",
        type=Path,
        help="Directory where optional domain CSVs and a manifest are written.",
    )
    split_parser.add_argument(
        "--prefix",
        type=str,
        default=None,
        help="Output filename prefix. Defaults to the station name or input stem.",
    )
    split_parser.add_argument(
        "--exclude-other",
        action="store_true",
        default=False,
        help="Do not write the catch-all other domain file.",
    )

    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    if args.command not in {"clean", "split-domains"}:
        raise ValueError(f"Unsupported public command: {args.command}")

    if args.command == "split-domains":
        manifest_path = _split_domains(
            args.cleaned_csv,
            args.output_dir,
            prefix=args.prefix,
            include_other=not args.exclude_other,
        )
        print(
            "Wrote optional domain split CSVs derived from canonical cleaned output; "
            f"manifest: {manifest_path.resolve()}"
        )
        return

    cleaning_logger = logging.getLogger("noaa_spec.cleaning")
    if not args.verbose:
        cleaning_logger.setLevel(logging.ERROR)

    output_path = args.output_csv_flag or args.output_csv
    if output_path is None:
        raise SystemExit("Provide an output path as OUTPUT.csv or with --out OUTPUT.csv.")

    written_path = _clean_csv_to_csv(args.input_csv, output_path)
    print(f"Wrote cleaned CSV to {written_path.resolve()}")


if __name__ == "__main__":
    main()
