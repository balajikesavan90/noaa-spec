"""Command-line interface for NOAA climate data pipeline."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .constants import DEFAULT_END_YEAR, DEFAULT_START_YEAR
from .pipeline import (
    build_data_file_list,
    build_location_ids,
    build_year_counts,
    clean_parquet_file,
    aggregate_parquet_placeholder,
    pull_random_station_raw,
    process_location,
)
from .pdf_markdown import convert_pdf_to_markdown


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="NOAA Global Hourly pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)

    file_list_parser = subparsers.add_parser("file-list", help="Build NOAA file list")
    file_list_parser.add_argument(
        "--start-year",
        type=int,
        default=DEFAULT_START_YEAR,
    )
    file_list_parser.add_argument(
        "--end-year",
        type=int,
        default=DEFAULT_END_YEAR,
    )
    file_list_parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=0.0,
        help="Delay between year directory requests",
    )
    file_list_parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="Retry count for NOAA listing requests",
    )
    file_list_parser.add_argument(
        "--backoff-base",
        type=float,
        default=0.5,
        help="Base delay (seconds) for exponential backoff",
    )
    file_list_parser.add_argument(
        "--backoff-max",
        type=float,
        default=8.0,
        help="Maximum delay (seconds) for exponential backoff",
    )

    location_parser = subparsers.add_parser(
        "location-ids", help="Build station metadata list"
    )
    location_parser.add_argument(
        "--metadata-fallback",
        action="store_true",
        default=True,
        help="Search additional years for metadata if the primary year is missing",
    )
    location_parser.add_argument(
        "--resume",
        action="store_true",
        default=True,
        help="Resume from existing Stations.csv if present",
    )
    location_parser.add_argument(
        "--no-resume",
        action="store_false",
        dest="resume",
        help="Do not load existing Stations.csv",
    )
    location_parser.add_argument(
        "--start-index",
        type=int,
        default=0,
        help="1-based start index in DataFileList_YEARCOUNT (0 = start from first)",
    )
    location_parser.add_argument(
        "--max-locations",
        type=int,
        default=None,
        help="Limit to N new locations this run",
    )
    location_parser.add_argument(
        "--checkpoint-every",
        type=int,
        default=100,
        help="Write checkpoint copies every N locations",
    )
    location_parser.add_argument(
        "--checkpoint-dir",
        type=Path,
        default=None,
        help="Directory to write checkpoint copies",
    )
    location_parser.add_argument(
        "--start-year",
        type=int,
        default=DEFAULT_START_YEAR,
    )
    location_parser.add_argument(
        "--end-year",
        type=int,
        default=DEFAULT_END_YEAR,
    )
    location_parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=0.0,
        help="Delay between metadata fetch attempts",
    )
    location_parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="Retry count for metadata fetches",
    )
    location_parser.add_argument(
        "--backoff-base",
        type=float,
        default=0.5,
        help="Base delay (seconds) for exponential backoff",
    )
    location_parser.add_argument(
        "--backoff-max",
        type=float,
        default=8.0,
        help="Maximum delay (seconds) for exponential backoff",
    )

    process_parser = subparsers.add_parser(
        "process-location", help="Download and clean a station's data"
    )
    process_parser.add_argument("file_name", help="Station file name (.csv)")
    process_parser.add_argument(
        "--start-year",
        type=int,
        default=DEFAULT_START_YEAR,
    )
    process_parser.add_argument(
        "--end-year",
        type=int,
        default=DEFAULT_END_YEAR,
    )
    process_parser.add_argument("--location-id", type=int, default=None)
    process_parser.add_argument(
        "--aggregation-strategy",
        choices=[
            "best_hour",
            "fixed_hour",
            "hour_day_month_year",
            "weighted_hours",
            "daily_min_max_mean",
        ],
        default="best_hour",
        help="Aggregation strategy for hourly/daily/monthly/yearly outputs",
    )
    process_parser.add_argument(
        "--fixed-hour",
        type=int,
        default=None,
        help="Fixed UTC hour to use for fixed_hour strategy",
    )
    process_parser.add_argument(
        "--min-hours-per-day",
        type=int,
        default=18,
        help="Minimum hours/day required for weighted_hours strategy",
    )
    process_parser.add_argument(
        "--min-days-per-month",
        type=int,
        default=20,
        help="Minimum days/month required for completeness filters",
    )
    process_parser.add_argument(
        "--min-months-per-year",
        type=int,
        default=12,
        help="Minimum months/year required for completeness filters",
    )
    process_parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=0.0,
        help="Delay between yearly CSV downloads",
    )
    process_parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
    )
    process_parser.add_argument(
        "--add-unit-conversions",
        action="store_true",
        default=False,
        help="Add imperial/derived unit columns alongside metric outputs",
    )
    process_parser.add_argument(
        "--permissive",
        action="store_true",
        default=False,
        help="Disable strict parsing (allows unknown identifiers and malformed fields)",
    )

    pick_parser = subparsers.add_parser(
        "pick-location",
        help="Pick a random station, download raw data, and write parquet",
    )
    pick_parser.add_argument(
        "--stations-csv",
        type=Path,
        default=None,
        help="Path to Stations.csv (defaults to latest noaa_file_index folder)",
    )
    pick_parser.add_argument(
        "--start-year",
        type=int,
        default=DEFAULT_START_YEAR,
    )
    pick_parser.add_argument(
        "--end-year",
        type=int,
        default=DEFAULT_END_YEAR,
    )
    pick_parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=0.0,
        help="Delay between yearly CSV downloads",
    )
    pick_parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for station selection",
    )
    pick_parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
    )

    clean_parser = subparsers.add_parser(
        "clean-parquet",
        help="Clean a raw parquet file and write cleaned parquet",
    )
    clean_parser.add_argument("raw_parquet", type=Path)
    clean_parser.add_argument(
        "--stations-csv",
        type=Path,
        default=None,
        help="Path to Stations.csv (defaults to latest noaa_file_index folder)",
    )
    clean_parser.add_argument(
        "--file-name",
        type=str,
        default=None,
        help="Station file name (.csv) for status updates",
    )
    clean_parser.add_argument(
        "--station-id",
        type=str,
        default=None,
        help="Station ID override for status updates",
    )
    clean_parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory for cleaned parquet (default: same as input)",
    )

    aggregate_parser = subparsers.add_parser(
        "aggregate-parquet",
        help="Placeholder for aggregating cleaned parquet",
    )
    aggregate_parser.add_argument("cleaned_parquet", type=Path)

    pdf_parser = subparsers.add_parser(
        "pdf-to-markdown",
        help="Convert a PDF into deterministic markdown",
    )
    pdf_parser.add_argument("input_pdf", type=Path, help="Input PDF path")
    pdf_parser.add_argument(
        "--output-md",
        type=Path,
        default=None,
        help="Output markdown path (default: input basename with .md)",
    )
    pdf_parser.add_argument(
        "--no-page-headers",
        action="store_true",
        default=False,
        help="Do not include '## Page N' section headers",
    )

    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    base_index_dir = Path("noaa_file_index")

    def _today_dir() -> Path:
        return base_index_dir / datetime.now(timezone.utc).strftime("%Y%m%d")

    def _latest_index_dir() -> Path:
        if not base_index_dir.exists():
            raise FileNotFoundError("noaa_file_index folder not found")
        candidates = []
        for path in base_index_dir.iterdir():
            if path.is_dir() and path.name.isdigit() and len(path.name) == 8:
                candidates.append(path)
        if not candidates:
            raise FileNotFoundError("noaa_file_index has no dated subfolders")
        return sorted(candidates)[-1]

    if args.command == "file-list":
        run_dir = _today_dir()
        run_dir.mkdir(parents=True, exist_ok=True)
        output_path = run_dir / "DataFileList.csv"
        counts_path = run_dir / "DataFileList_YEARCOUNT.csv"
        file_list = build_data_file_list(
            output_path,
            sleep_seconds=args.sleep_seconds,
            retries=args.retries,
            backoff_base=args.backoff_base,
            backoff_max=args.backoff_max,
        )
        build_year_counts(file_list, counts_path, args.start_year, args.end_year)
        return

    if args.command == "location-ids":
        run_dir = _latest_index_dir()
        year_counts = run_dir / "DataFileList_YEARCOUNT.csv"
        file_list_path = run_dir / "DataFileList.csv"
        if year_counts.exists():
            counts = pd.read_csv(year_counts)
        else:
            raise FileNotFoundError(f"Missing {year_counts}")
        file_list = pd.read_csv(file_list_path) if file_list_path.exists() else None
        metadata_years = range(args.start_year, args.end_year + 1)
        build_location_ids(
            counts,
            run_dir / "Stations.csv",
            metadata_years=metadata_years,
            file_list=file_list,
            start_year=args.start_year,
            end_year=args.end_year,
            resume=args.resume,
            start_index=args.start_index,
            max_locations=args.max_locations,
            checkpoint_every=args.checkpoint_every,
            checkpoint_dir=args.checkpoint_dir,
            sleep_seconds=args.sleep_seconds,
            retries=args.retries,
            backoff_base=args.backoff_base,
            backoff_max=args.backoff_max,
        )
        return

    if args.command == "process-location":
        output_dir: Path = args.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        years = range(args.start_year, args.end_year + 1)
        outputs = process_location(
            args.file_name,
            years,
            args.location_id,
            aggregation_strategy=args.aggregation_strategy,
            min_hours_per_day=args.min_hours_per_day,
            min_days_per_month=args.min_days_per_month,
            min_months_per_year=args.min_months_per_year,
            fixed_hour=args.fixed_hour,
            sleep_seconds=args.sleep_seconds,
            add_unit_conversions=args.add_unit_conversions,
            strict_mode=not args.permissive,
        )

        outputs.raw.to_csv(output_dir / "LocationData_Raw.csv", index=False)
        outputs.cleaned.to_csv(output_dir / "LocationData_Cleaned.csv", index=False)
        outputs.hourly.to_csv(output_dir / "LocationData_Hourly.csv", index=False)
        outputs.monthly.to_csv(output_dir / "LocationData_Monthly.csv", index=False)
        outputs.yearly.to_csv(output_dir / "LocationData_Yearly.csv", index=False)
        return

    if args.command == "pick-location":
        output_dir = args.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        stations_csv = args.stations_csv
        if stations_csv is None:
            stations_csv = _latest_index_dir() / "Stations.csv"
        years = range(args.start_year, args.end_year + 1)
        pull_random_station_raw(
            stations_csv,
            years,
            output_dir,
            sleep_seconds=args.sleep_seconds,
            seed=args.seed,
        )
        return

    if args.command == "clean-parquet":
        stations_csv = args.stations_csv
        if stations_csv is None:
            stations_csv = _latest_index_dir() / "Stations.csv"
        clean_parquet_file(
            args.raw_parquet,
            output_dir=args.output_dir,
            stations_csv=stations_csv,
            file_name=args.file_name,
            station_id=args.station_id,
        )
        return

    if args.command == "aggregate-parquet":
        aggregate_parquet_placeholder(args.cleaned_parquet)
        return

    if args.command == "pdf-to-markdown":
        convert_pdf_to_markdown(
            args.input_pdf,
            output_md=args.output_md,
            include_page_headers=not args.no_page_headers,
        )
        return


if __name__ == "__main__":
    main()
