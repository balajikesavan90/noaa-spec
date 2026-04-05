"""Public command-line interface for deterministic NOAA cleaning."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .cleaning import clean_noaa_dataframe
from .deterministic_io import write_deterministic_csv
from .domains.publisher import (
    available_views_text,
    get_view_definition,
    project_view_from_canonical,
)


def _clean_csv_to_csv(input_csv: Path, output_csv: Path, *, view_name: str | None = None) -> Path:
    raw = pd.read_csv(input_csv, dtype=str)
    cleaned = clean_noaa_dataframe(raw, keep_raw=False, strict_mode=True)
    output_frame = cleaned
    sort_by = ("STATION", "DATE")

    if view_name is not None:
        _definition, output_frame = project_view_from_canonical(cleaned, view_name)
        sort_by = ("station_id", "DATE")

    write_deterministic_csv(
        output_frame,
        output_csv,
        sort_by=sort_by,
        float_format="%.1f",
    )
    return output_csv


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="noaa-spec",
        description=(
            "Clean a NOAA ISD / Global Hourly raw CSV into a deterministic "
            "observation-level canonical CSV with normalized sentinels, preserved QC "
            "semantics, and a stable output schema. The public canonical CSV uses "
            "STATION and DATE as the reviewer-visible identifier columns."
        ),
        epilog=(
            "Primary workflow: noaa-spec clean INPUT.csv OUTPUT.csv "
            "or noaa-spec clean INPUT.csv --out OUTPUT.csv. "
            f"Optional views: {available_views_text()}"
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    clean_parser = subparsers.add_parser(
        "clean",
        help="Clean a NOAA raw CSV into the canonical cleaned CSV.",
        description=(
            "Read a NOAA ISD / Global Hourly CSV, replace sentinel-coded values "
            "with nulls, preserve QC columns, and write a deterministic canonical "
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
        "--view",
        type=str,
        default=None,
        help=(
            "Optional secondary dataset derived from the canonical output. "
            "View outputs use 'station_id' instead of 'STATION' as the "
            "station identifier column. "
            f"Available views: {available_views_text()}."
        ),
    )

    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    if args.command != "clean":
        raise ValueError(f"Unsupported public command: {args.command}")

    output_path = args.output_csv_flag or args.output_csv
    if output_path is None:
        raise SystemExit("Provide an output path as OUTPUT.csv or with --out OUTPUT.csv.")

    if args.view is not None:
        try:
            view_definition = get_view_definition(args.view)
        except KeyError as exc:
            raise SystemExit(
                f"Invalid view {args.view!r}. Available views: {available_views_text()}"
            ) from exc
        written_path = _clean_csv_to_csv(
            args.input_csv,
            output_path,
            view_name=view_definition.view_name,
        )
        print(
            f"Wrote {view_definition.view_name} view to {written_path.resolve()}"
        )
        return

    written_path = _clean_csv_to_csv(args.input_csv, output_path)
    print(f"Wrote cleaned CSV to {written_path.resolve()}")


if __name__ == "__main__":
    main()
