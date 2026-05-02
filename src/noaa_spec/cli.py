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
from .validation import (
    DEFAULT_VALIDATION_COUNT,
    DEFAULT_VALIDATION_SEED,
    default_build_id,
    run_validation_workflow,
)


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
    malformed_identifier_columns = list(summary.get("malformed_identifier_columns", ()))
    unsupported_columns = list(
        summary.get(
            "unsupported_identifier_columns",
            summary.get("unknown_identifier_columns", ()),
        )
    )
    details: list[str] = []
    if malformed_columns:
        details.append(
            "malformed section identifier token(s): "
            + ", ".join(sorted(malformed_columns))
        )
    if malformed_identifier_columns:
        details.append(
            "malformed identifier(s): "
            + ", ".join(sorted(malformed_identifier_columns))
        )
    if unsupported_columns:
        details.append(
            "unsupported identifier(s): " + ", ".join(sorted(unsupported_columns))
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

    validate_parser = subparsers.add_parser(
        "validate-100-stations",
        help="Run deterministic operational validation over a stratified station sample.",
        description=(
            "Select a deterministic file-size-stratified station sample, run the "
            "existing NOAA-Spec cleaning workflow against each selected station, "
            "and write reviewer-facing manifests, checksums, and summary artifacts."
        ),
    )
    validate_parser.add_argument(
        "--input-root",
        required=True,
        type=Path,
        help="Directory containing downloaded station files.",
    )
    validate_parser.add_argument(
        "--output-root",
        type=Path,
        default=None,
        help=(
            "Destination directory for validation artifacts. Defaults to "
            "artifacts/validation_100_station/build_<build_id>."
        ),
    )
    validate_parser.add_argument(
        "--count",
        type=int,
        default=DEFAULT_VALIDATION_COUNT,
        help="Number of stations to select. Default: 100.",
    )
    validate_parser.add_argument(
        "--strategy",
        default="size-stratified",
        choices=("size-stratified",),
        help="Sampling strategy. Default: size-stratified.",
    )
    validate_parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_VALIDATION_SEED,
        help="Deterministic selection seed. Default: 20260430.",
    )
    validate_parser.add_argument(
        "--continue-on-error",
        action="store_true",
        default=False,
        help="Continue after station-level failures and preserve partial results.",
    )
    validate_parser.add_argument(
        "--build-id",
        default=None,
        help="Optional build identifier recorded in manifests.",
    )

    bundle_parser = subparsers.add_parser(
        "build-validation-bundle",
        help="Build a reviewer-facing 100-station validation bundle with archived raw inputs.",
        description=(
            "Select a deterministic file-size-stratified station sample from a local "
            "station corpus, copy the selected raw inputs into the output bundle, run "
            "the existing NOAA-Spec cleaning workflow against those frozen inputs, and "
            "write reviewer-facing manifests, checksums, and summary artifacts."
        ),
    )
    bundle_parser.add_argument(
        "--source-root",
        required=True,
        type=Path,
        help="Directory containing the local station corpus used for selection.",
    )
    bundle_parser.add_argument(
        "--output-root",
        type=Path,
        default=None,
        help=(
            "Destination directory for bundle artifacts. Defaults to "
            "artifacts/validation_100_station/build_<build_id>."
        ),
    )
    bundle_parser.add_argument(
        "--count",
        type=int,
        default=DEFAULT_VALIDATION_COUNT,
        help="Number of stations to select. Default: 100.",
    )
    bundle_parser.add_argument(
        "--strategy",
        default="size-stratified",
        choices=("size-stratified",),
        help="Sampling strategy. Default: size-stratified.",
    )
    bundle_parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_VALIDATION_SEED,
        help="Deterministic selection seed. Default: 20260430.",
    )
    bundle_parser.add_argument(
        "--continue-on-error",
        action="store_true",
        default=False,
        help="Continue after station-level failures and preserve partial results.",
    )
    bundle_parser.add_argument(
        "--build-id",
        default=None,
        help="Optional build identifier recorded in manifests.",
    )

    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    if args.command == "clean":
        cleaning_logger = logging.getLogger("noaa_spec.cleaning")
        if not args.verbose:
            cleaning_logger.setLevel(logging.ERROR)

        written_path = _clean_csv_to_csv(args.input_csv, args.output_csv)
        print(f"Wrote cleaned CSV to {written_path.resolve()}")
        return

    if args.command == "validate-100-stations":
        output_root = args.output_root
        build_id = args.build_id or default_build_id()
        if output_root is None:
            output_root = Path("artifacts") / "validation_100_station" / f"build_{build_id}"
        result = run_validation_workflow(
            source_root=args.input_root,
            output_root=output_root,
            count=args.count,
            strategy=args.strategy,
            seed=args.seed,
            continue_on_error=args.continue_on_error,
            build_id=build_id,
            command=" ".join(sys.argv),
            selected_by="noaa-spec validate-100-stations",
        )
        print(f"Wrote validation artifacts to {result['output_root']}")
        if result["failed"]:
            raise SystemExit(1)
        return

    if args.command == "build-validation-bundle":
        output_root = args.output_root
        build_id = args.build_id or default_build_id()
        if output_root is None:
            output_root = Path("artifacts") / "validation_100_station" / f"build_{build_id}"
        result = run_validation_workflow(
            source_root=args.source_root,
            output_root=output_root,
            count=args.count,
            strategy=args.strategy,
            seed=args.seed,
            continue_on_error=args.continue_on_error,
            build_id=build_id,
            command=" ".join(sys.argv),
            selected_by="noaa-spec build-validation-bundle",
        )
        print(f"Wrote validation artifacts to {result['output_root']}")
        if result["failed"]:
            raise SystemExit(1)
        return

    raise ValueError(f"Unsupported public command: {args.command}")


if __name__ == "__main__":
    main()
