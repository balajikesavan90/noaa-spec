"""Command-line interface for NOAA climate data pipeline."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import logging
import time

import pandas as pd

from .cleaning_runner import (
    CleaningRunConfig,
    RunWriteFlags,
    default_roots_for_mode,
    parse_station_filters,
    run_cleaning_run,
)
from .constants import DEFAULT_END_YEAR, DEFAULT_START_YEAR
from .pipeline import (
    build_data_file_list,
    build_location_ids,
    build_year_counts,
    clean_parquet_file,
    aggregate_parquet_placeholder,
    pull_random_station_raw,
    process_location,
    process_location_from_raw,
)
from .pdf_markdown import convert_pdf_to_markdown
from .domain_split import (
    classify_columns,
    MAPPING_COLUMNS,
    station_metadata_mapping_row,
    split_station_cleaned_by_domain,
    sanitize_station_slug,
)
from .research_reports import build_reports_for_station_dir


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

    reports_parser = subparsers.add_parser(
        "research-reports",
        help="Generate P3 quality and aggregation reports for a station folder",
    )
    reports_parser.add_argument(
        "station_dir",
        type=Path,
        help="Station folder containing LocationData_Raw/Cleaned/Hourly/Monthly/Yearly.csv",
    )
    reports_parser.add_argument(
        "--aggregation-strategy",
        choices=[
            "best_hour",
            "fixed_hour",
            "hour_day_month_year",
            "weighted_hours",
            "daily_min_max_mean",
        ],
        default="best_hour",
        help="Aggregation strategy used when creating hourly/monthly/yearly outputs",
    )
    reports_parser.add_argument(
        "--fixed-hour",
        type=int,
        default=None,
        help="Fixed hour used if aggregation strategy was fixed_hour",
    )
    reports_parser.add_argument(
        "--min-days-per-month",
        type=int,
        default=20,
        help="Minimum days/month threshold used by completeness filters",
    )
    reports_parser.add_argument(
        "--min-months-per-year",
        type=int,
        default=12,
        help="Minimum months/year threshold used by completeness filters",
    )
    reports_parser.add_argument(
        "--access-date",
        type=str,
        default=None,
        help="NOAA data access date (YYYY-MM-DD). Defaults to current UTC date.",
    )
    reports_parser.add_argument(
        "--authors",
        type=str,
        default="Balaji Kesavan",
        help="Citation author string for generated reports",
    )

    reprocess_parser = subparsers.add_parser(
        "reprocess-output-dir",
        help=(
            "[DEPRECATED] Re-clean all station folders in an output directory from "
            "LocationData_Raw.csv and optionally generate research reports"
        ),
    )
    reprocess_parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("output"),
        help="Root directory containing station folders (default: output)",
    )
    reprocess_parser.add_argument(
        "--aggregation-strategy",
        choices=[
            "best_hour",
            "fixed_hour",
            "hour_day_month_year",
            "weighted_hours",
            "daily_min_max_mean",
        ],
        default="best_hour",
        help="Aggregation strategy to use while regenerating outputs",
    )
    reprocess_parser.add_argument(
        "--fixed-hour",
        type=int,
        default=None,
        help="Fixed UTC hour when using fixed_hour aggregation strategy",
    )
    reprocess_parser.add_argument(
        "--min-hours-per-day",
        type=int,
        default=18,
        help="Minimum hours/day required for weighted_hours strategy",
    )
    reprocess_parser.add_argument(
        "--min-days-per-month",
        type=int,
        default=20,
        help="Minimum days/month completeness threshold",
    )
    reprocess_parser.add_argument(
        "--min-months-per-year",
        type=int,
        default=12,
        help="Minimum months/year completeness threshold",
    )
    reprocess_parser.add_argument(
        "--add-unit-conversions",
        action="store_true",
        default=False,
        help="Add imperial/derived unit columns while regenerating outputs",
    )
    reprocess_parser.add_argument(
        "--permissive",
        action="store_true",
        default=False,
        help="Disable strict parsing while regenerating outputs",
    )
    reprocess_parser.add_argument(
        "--no-reports",
        action="store_true",
        default=False,
        help="Skip research report generation after cleaning",
    )
    reprocess_parser.add_argument(
        "--access-date",
        type=str,
        default=None,
        help="NOAA data access date (YYYY-MM-DD) for report citation",
    )
    reprocess_parser.add_argument(
        "--authors",
        type=str,
        default="Balaji Kesavan",
        help="Citation author string for generated reports",
    )
    reprocess_parser.add_argument(
        "--show-parse-strict-logs",
        action="store_true",
        default=False,
        help="Show verbose [PARSE_STRICT] cleaning warnings during batch processing",
    )
    reprocess_parser.add_argument(
        "--domain-output-dir",
        type=Path,
        default=Path("output") / "NOAA Demo Data",
        help="Directory where station-domain split CSV files are written",
    )
    reprocess_parser.add_argument(
        "--no-domain-split",
        action="store_true",
        default=False,
        help="Do not generate domain-split CSV files",
    )

    cleaning_run_parser = subparsers.add_parser(
        "cleaning-run",
        help="Production-safe cleaning orchestration with explicit mode/roots",
    )
    cleaning_run_parser.add_argument(
        "--mode",
        required=True,
        choices=["test_csv_dir", "test_parquet_dir", "batch_parquet_dir"],
        help="Execution mode (CSV test folders, parquet test folders, or parquet batch input tree)",
    )
    cleaning_run_parser.add_argument(
        "--input-root",
        required=True,
        type=Path,
        help="Root directory containing station folders with raw inputs",
    )
    cleaning_run_parser.add_argument(
        "--input-format",
        required=True,
        choices=["csv", "parquet"],
        help="Raw input format (must match selected mode)",
    )
    cleaning_run_parser.add_argument(
        "--output-root",
        type=Path,
        default=None,
        help="Root directory for cleaned station outputs and domain splits",
    )
    cleaning_run_parser.add_argument(
        "--reports-root",
        type=Path,
        default=None,
        help="Root directory for optional station/global reports",
    )
    cleaning_run_parser.add_argument(
        "--quality-profile-root",
        type=Path,
        default=None,
        help="Root directory for station quality profile sidecars",
    )
    cleaning_run_parser.add_argument(
        "--manifest-root",
        type=Path,
        default=None,
        help="Root directory for run_config/run_manifest/run_status artifacts",
    )
    cleaning_run_parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="Run identifier (default: UTC timestamp)",
    )
    cleaning_run_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional limit on number of stations processed in this invocation",
    )
    cleaning_run_parser.add_argument(
        "--station-id",
        action="append",
        default=[],
        help="Station filter (repeatable or comma-separated 11-digit IDs)",
    )
    cleaning_run_parser.add_argument(
        "--force",
        action="store_true",
        default=False,
        help="Recompute stations even if status and outputs indicate completion",
    )
    cleaning_run_parser.add_argument(
        "--manifest-first",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Lock station processing to run_manifest snapshot semantics",
    )
    cleaning_run_parser.add_argument(
        "--manifest-refresh",
        action="store_true",
        default=False,
        help="Rebuild run_config/run_manifest/run_status for the same run_id",
    )
    cleaning_run_parser.add_argument(
        "--write-cleaned-station",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Write cleaned station datasets",
    )
    cleaning_run_parser.add_argument(
        "--write-domain-splits",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Write optional domain split datasets",
    )
    cleaning_run_parser.add_argument(
        "--write-station-quality-profile",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Write station quality profile JSON sidecars",
    )
    cleaning_run_parser.add_argument(
        "--write-station-reports",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Write heavier per-station research report artifacts",
    )
    cleaning_run_parser.add_argument(
        "--write-global-summary",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Write global summary from station quality profiles",
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

    if args.command == "research-reports":
        build_reports_for_station_dir(
            args.station_dir,
            aggregation_strategy=args.aggregation_strategy,
            fixed_hour=args.fixed_hour,
            min_days_per_month=args.min_days_per_month,
            min_months_per_year=args.min_months_per_year,
            access_date=args.access_date,
            authors=args.authors,
        )
        return

    if args.command == "cleaning-run":
        run_id = args.run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        station_ids = parse_station_filters(args.station_id)
        default_roots = default_roots_for_mode(args.mode, run_id)

        def _resolve_flag(value: bool | None, default: bool) -> bool:
            return default if value is None else bool(value)

        if args.mode in {"test_csv_dir", "test_parquet_dir"}:
            write_flags = RunWriteFlags(
                write_cleaned_station=_resolve_flag(args.write_cleaned_station, True),
                write_domain_splits=_resolve_flag(args.write_domain_splits, True),
                write_station_quality_profile=_resolve_flag(args.write_station_quality_profile, True),
                write_station_reports=_resolve_flag(args.write_station_reports, False),
                write_global_summary=_resolve_flag(args.write_global_summary, False),
            )
            manifest_first_default = False
        else:
            write_flags = RunWriteFlags(
                write_cleaned_station=_resolve_flag(args.write_cleaned_station, True),
                write_domain_splits=_resolve_flag(args.write_domain_splits, False),
                write_station_quality_profile=_resolve_flag(args.write_station_quality_profile, True),
                write_station_reports=_resolve_flag(args.write_station_reports, False),
                write_global_summary=_resolve_flag(args.write_global_summary, True),
            )
            manifest_first_default = True

        config = CleaningRunConfig(
            mode=args.mode,
            input_root=args.input_root,
            input_format=args.input_format,
            output_root=args.output_root or default_roots["output_root"],
            reports_root=args.reports_root or default_roots["reports_root"],
            quality_profile_root=args.quality_profile_root or default_roots["quality_profile_root"],
            manifest_root=args.manifest_root or default_roots["manifest_root"],
            run_id=run_id,
            limit=args.limit,
            station_ids=station_ids,
            force=args.force,
            manifest_first=(
                manifest_first_default if args.manifest_first is None else bool(args.manifest_first)
            ),
            manifest_refresh=bool(args.manifest_refresh),
            write_flags=write_flags,
        )
        run_cleaning_run(config)
        return

    if args.command == "reprocess-output-dir":
        output_root: Path = args.output_root
        if not output_root.exists() or not output_root.is_dir():
            raise FileNotFoundError(f"Output root not found or not a directory: {output_root}")

        cleaning_logger = logging.getLogger("noaa_climate_data.cleaning")
        previous_cleaning_level = cleaning_logger.level
        if not args.show_parse_strict_logs:
            cleaning_logger.setLevel(logging.ERROR)

        station_dirs = sorted(path for path in output_root.iterdir() if path.is_dir())
        processed = 0
        skipped = 0
        failed = 0
        total = len(station_dirs)
        batch_start = time.monotonic()
        domain_manifest_rows: list[dict[str, object]] = []
        station_mapping_rows: list[dict[str, object]] = []
        columns_by_domain_rows: list[dict[str, object]] | None = None

        print(
            "Starting reprocess-output-dir: "
            f"output_root={output_root} total_station_dirs={total} "
            f"reports={'off' if args.no_reports else 'on'}"
        )

        try:
            for idx, station_dir in enumerate(station_dirs, start=1):
                station_start = time.monotonic()
                print(f"[{idx}/{total}] Station {station_dir.name}: begin")
                raw_csv = station_dir / "LocationData_Raw.csv"
                if not raw_csv.exists():
                    skipped += 1
                    station_elapsed = time.monotonic() - station_start
                    print(
                        f"[{idx}/{total}] SKIP {station_dir.name}: "
                        f"missing LocationData_Raw.csv | elapsed={station_elapsed:.2f}s"
                    )
                    continue

                try:
                    print(f"[{idx}/{total}] {station_dir.name}: reading raw CSV")
                    raw = pd.read_csv(raw_csv, low_memory=False)
                    print(
                        f"[{idx}/{total}] {station_dir.name}: "
                        f"cleaning + aggregation ({len(raw)} raw rows)"
                    )

                    strict_mode_for_station = not args.permissive
                    if strict_mode_for_station and "DATE" in raw.columns:
                        sample_dates = raw["DATE"].dropna().astype(str).head(10)
                        if not sample_dates.empty:
                            # Legacy/staged output raws often store ISO timestamps.
                            # Running strict mode on these can be very slow and then
                            # drop all rows, so route directly to permissive mode.
                            if sample_dates.str.contains("T").any() or sample_dates.str.contains("-").any():
                                strict_mode_for_station = False
                                print(
                                    f"[{idx}/{total}] {station_dir.name}: detected ISO DATE values; "
                                    "using permissive mode directly"
                                )

                    outputs = process_location_from_raw(
                        raw,
                        aggregation_strategy=args.aggregation_strategy,
                        min_hours_per_day=args.min_hours_per_day,
                        min_days_per_month=args.min_days_per_month,
                        min_months_per_year=args.min_months_per_year,
                        fixed_hour=args.fixed_hour,
                        add_unit_conversions=args.add_unit_conversions,
                        strict_mode=strict_mode_for_station,
                    )

                    if (
                        strict_mode_for_station
                        and len(raw) > 0
                        and len(outputs.cleaned) == 0
                    ):
                        print(
                            f"[{idx}/{total}] {station_dir.name}: strict mode produced 0 cleaned rows; "
                            "retrying with permissive mode to preserve legacy timestamp DATE formats"
                        )
                        outputs = process_location_from_raw(
                            raw,
                            aggregation_strategy=args.aggregation_strategy,
                            min_hours_per_day=args.min_hours_per_day,
                            min_days_per_month=args.min_days_per_month,
                            min_months_per_year=args.min_months_per_year,
                            fixed_hour=args.fixed_hour,
                            add_unit_conversions=args.add_unit_conversions,
                            strict_mode=False,
                        )

                    print(f"[{idx}/{total}] {station_dir.name}: writing station CSV outputs")
                    outputs.raw.to_csv(station_dir / "LocationData_Raw.csv", index=False)
                    outputs.cleaned.to_csv(station_dir / "LocationData_Cleaned.csv", index=False)

                    # Remove roll-up files; reprocess-output-dir now focuses on
                    # cleaned outputs plus domain-level splits/reports.
                    for rollup_name in (
                        "LocationData_Hourly.csv",
                        "LocationData_Monthly.csv",
                        "LocationData_Yearly.csv",
                    ):
                        rollup_path = station_dir / rollup_name
                        if rollup_path.exists():
                            rollup_path.unlink()

                    if not args.no_domain_split:
                        if columns_by_domain_rows is None:
                            common_cols, domain_cols = classify_columns(list(outputs.cleaned.columns))
                            columns_by_domain_rows = []
                            for domain_name in sorted(domain_cols.keys()):
                                cols = domain_cols[domain_name]
                                if not cols:
                                    continue
                                selected = common_cols + cols
                                columns_by_domain_rows.append(
                                    {
                                        "domain": domain_name,
                                        "columns_count": len(selected),
                                        "columns": "|".join(selected),
                                    }
                                )

                        station_name = station_dir.name
                        if (
                            "station_name" in outputs.cleaned.columns
                            and not outputs.cleaned["station_name"].dropna().empty
                        ):
                            station_name = str(outputs.cleaned["station_name"].dropna().iloc[0])
                        station_slug = sanitize_station_slug(station_name)
                        print(
                            f"[{idx}/{total}] {station_dir.name}: generating domain split files "
                            f"in {args.domain_output_dir}"
                        )
                        domain_rows = split_station_cleaned_by_domain(
                            outputs.cleaned,
                            station_slug=station_slug,
                            station_name=station_name,
                            output_dir=args.domain_output_dir,
                        )
                        domain_manifest_rows.extend(domain_rows)
                        station_mapping_rows.append(
                            station_metadata_mapping_row(
                                outputs.cleaned,
                                station_slug=station_slug,
                                station_name=station_name,
                                station_id_fallback=station_dir.name,
                            )
                        )

                    if not args.no_reports:
                        print(f"[{idx}/{total}] {station_dir.name}: generating research reports")
                        build_reports_for_station_dir(
                            station_dir,
                            aggregation_strategy=args.aggregation_strategy,
                            fixed_hour=args.fixed_hour,
                            min_days_per_month=args.min_days_per_month,
                            min_months_per_year=args.min_months_per_year,
                            access_date=args.access_date,
                            authors=args.authors,
                        )

                    processed += 1
                    station_elapsed = time.monotonic() - station_start
                    batch_elapsed = time.monotonic() - batch_start
                    print(
                        f"[{idx}/{total}] DONE {station_dir.name} | "
                        f"elapsed={station_elapsed:.2f}s "
                        f"processed={processed} skipped={skipped} failed={failed} "
                        f"batch_elapsed={batch_elapsed:.2f}s"
                    )
                except Exception as exc:
                    failed += 1
                    station_elapsed = time.monotonic() - station_start
                    batch_elapsed = time.monotonic() - batch_start
                    print(
                        f"[{idx}/{total}] FAIL {station_dir.name}: {exc} | "
                        f"elapsed={station_elapsed:.2f}s "
                        f"processed={processed} skipped={skipped} failed={failed} "
                        f"batch_elapsed={batch_elapsed:.2f}s"
                    )

            total_elapsed = time.monotonic() - batch_start
            if not args.no_domain_split and (
                domain_manifest_rows or columns_by_domain_rows or station_mapping_rows
            ):
                if domain_manifest_rows:
                    domain_manifest_path = args.domain_output_dir / "station_split_manifest.csv"
                    pd.DataFrame(domain_manifest_rows).to_csv(domain_manifest_path, index=False)
                    print(f"domain split manifest: {domain_manifest_path}")
                if columns_by_domain_rows:
                    columns_by_domain_path = args.domain_output_dir / "columns_by_domain.csv"
                    pd.DataFrame(columns_by_domain_rows).to_csv(columns_by_domain_path, index=False)
                    print(f"columns by domain: {columns_by_domain_path}")
                if station_mapping_rows:
                    mapping_df = pd.DataFrame(station_mapping_rows)
                    mapping_df = mapping_df.drop_duplicates(subset=["station_id"], keep="first")
                    for column in MAPPING_COLUMNS:
                        if column not in mapping_df.columns:
                            mapping_df[column] = None
                    mapping_df = mapping_df[list(MAPPING_COLUMNS)]
                    mapping_path = args.domain_output_dir / "station_metadata_mapping.csv"
                    mapping_df.to_csv(mapping_path, index=False)
                    print(f"station metadata mapping: {mapping_path}")
            print(
                "reprocess-output-dir summary: "
                f"processed={processed} skipped={skipped} failed={failed} total={total} "
                f"elapsed={total_elapsed:.2f}s"
            )
            return
        finally:
            cleaning_logger.setLevel(previous_cleaning_level)


if __name__ == "__main__":
    main()
