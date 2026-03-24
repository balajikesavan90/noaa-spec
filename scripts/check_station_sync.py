"""Check raw_pull_state.csv status against station parquet outputs."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from datetime import datetime, timezone

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from noaa_spec.noaa_client import normalize_station_file_name
from noaa_spec.pipeline import default_raw_pull_state_path

DEFAULT_OUTPUT_DIR = Path("output")
RAW_PULL_STATE_COLUMNS = {
    "station_id",
    "FileName",
    "raw_data_pulled",
    "raw_path",
    "pulled_at",
    "registry_snapshot",
}


def _latest_index_dir(base_index_dir: Path) -> Path:
    if not base_index_dir.exists():
        raise FileNotFoundError("noaa_file_index folder not found")
    candidates = [
        path
        for path in base_index_dir.iterdir()
        if path.is_dir() and path.name.isdigit() and len(path.name) == 8
    ]
    if not candidates:
        raise FileNotFoundError("noaa_file_index has no dated subfolders")
    return sorted(candidates)[-1]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate raw_pull_state.csv against station raw parquet files"
    )
    parser.add_argument(
        "--stations-csv",
        type=Path,
        default=None,
        help="Path to Stations.csv (defaults to latest noaa_file_index folder)",
    )
    parser.add_argument(
        "--raw-pull-state-csv",
        type=Path,
        default=None,
        help="Path to raw_pull_state.csv (defaults to noaa_file_index/state/raw_pull_state.csv)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Root directory containing station parquet outputs (default: ./output)",
    )
    parser.add_argument(
        "--max-mismatches",
        type=int,
        default=25,
        help="Max mismatches to print per category (default 25)",
    )
    parser.add_argument(
        "--write-report",
        type=Path,
        default=None,
        help="Optional path to write a CSV report of mismatches",
    )
    parser.add_argument(
        "--stale-threshold-minutes",
        type=float,
        default=5.0,
        help="Minutes since last successful pull before reporting stale progress (default 5)",
    )
    return parser.parse_args()


def _station_dir(output_dir: Path, file_name: str) -> Path:
    station_id = Path(normalize_station_file_name(file_name)).stem
    return output_dir / station_id


def _station_parquet_path(output_dir: Path, file_name: str) -> Path:
    return _station_dir(output_dir, file_name) / "LocationData_Raw.parquet"


def _coerce_boolean_series(series: pd.Series) -> pd.Series:
    truthy = {"true", "1", "yes", "y", "t"}
    return series.fillna(False).astype(str).str.strip().str.lower().isin(truthy)


def _load_raw_pull_state(raw_pull_state_csv: Path) -> pd.DataFrame:
    if not raw_pull_state_csv.exists():
        raise FileNotFoundError(
            "raw_pull_state.csv not found: "
            f"{raw_pull_state_csv}. Run "
            "`poetry run noaa-spec materialize-raw-pull-state` "
            "if you need to bootstrap it from legacy state."
        )

    frame = pd.read_csv(raw_pull_state_csv, keep_default_na=False)
    missing = RAW_PULL_STATE_COLUMNS.difference(frame.columns)
    if missing:
        missing_cols = ", ".join(sorted(missing))
        raise ValueError(
            f"raw_pull_state.csv missing required columns: {missing_cols}"
        )

    work = frame.copy()
    work["FileName"] = work["FileName"].fillna("").astype(str).map(normalize_station_file_name)
    work["raw_data_pulled"] = _coerce_boolean_series(work["raw_data_pulled"])
    work["pulled_at"] = pd.to_datetime(work["pulled_at"], utc=True, errors="coerce")
    return work


def main() -> None:
    args = _parse_args()
    base_index_dir = Path("noaa_file_index")
    stations_csv = args.stations_csv
    if stations_csv is None:
        stations_csv = _latest_index_dir(base_index_dir) / "Stations.csv"
    raw_pull_state_csv = args.raw_pull_state_csv or default_raw_pull_state_path(stations_csv)

    frame = pd.read_csv(stations_csv)
    if "FileName" not in frame.columns:
        raise ValueError("Stations.csv missing FileName column")
    frame["FileName"] = frame["FileName"].fillna("").astype(str).map(normalize_station_file_name)

    raw_pull_state = _load_raw_pull_state(raw_pull_state_csv)
    pulled_files = set(
        raw_pull_state[raw_pull_state["raw_data_pulled"]]["FileName"].astype(str).tolist()
    )
    pulled_rows = raw_pull_state[raw_pull_state["raw_data_pulled"]].copy()
    expected_true = frame[frame["FileName"].isin(pulled_files)].copy()
    expected_false = frame[~frame["FileName"].isin(pulled_files)].copy()

    missing_files: list[dict[str, object]] = []
    unexpected_files: list[dict[str, object]] = []
    present_sizes: list[int] = []

    for _, row in expected_true.iterrows():
        file_name = str(row["FileName"])
        parquet_path = _station_parquet_path(args.output_dir, file_name)
        if not parquet_path.exists():
            missing_files.append(
                {
                    "FileName": file_name,
                    "Expected": True,
                    "ParquetPath": str(parquet_path),
                }
            )
        else:
            present_sizes.append(parquet_path.stat().st_size)

    for _, row in expected_false.iterrows():
        file_name = str(row["FileName"])
        parquet_path = _station_parquet_path(args.output_dir, file_name)
        if parquet_path.exists():
            unexpected_files.append(
                {
                    "FileName": file_name,
                    "Expected": False,
                    "ParquetPath": str(parquet_path),
                }
            )

    total = len(frame)
    print(f"Stations.csv: {stations_csv}")
    print(f"raw_pull_state.csv: {raw_pull_state_csv}")
    print(f"Output dir: {args.output_dir}")
    print(f"Total stations: {total}")
    print(f"raw_data_pulled=True: {len(expected_true)}")
    print(f"raw_data_pulled=False: {len(expected_false)}")
    if not pulled_rows.empty:
        latest_pulled_at = pulled_rows["pulled_at"].max()
        if pd.notna(latest_pulled_at):
            minutes_since_progress = (
                datetime.now(timezone.utc) - latest_pulled_at.to_pydatetime()
            ).total_seconds() / 60.0
            progress_status = (
                "stale"
                if minutes_since_progress > args.stale_threshold_minutes
                else "ok"
            )
            print(f"Latest successful pull: {latest_pulled_at.isoformat()}")
            print(f"Minutes since latest pull: {minutes_since_progress:.2f}")
            print(f"Progress freshness status: {progress_status}")
        else:
            print("Latest successful pull: n/a")
            print("Minutes since latest pull: n/a")
            print("Progress freshness status: unknown")
    else:
        print("Latest successful pull: n/a")
        print("Minutes since latest pull: n/a")
        print("Progress freshness status: no_pulls")
    print(f"Missing parquet (should exist): {len(missing_files)}")
    print(f"Unexpected parquet (should not exist): {len(unexpected_files)}")
    if present_sizes:
        size_series = pd.Series(present_sizes, dtype="float") / (1024 * 1024)
        avg_mb = size_series.mean()
        median_mb = size_series.median()
        min_mb = size_series.min()
        max_mb = size_series.max()
        percentiles = size_series.quantile([0.25, 0.75])
        mode_values = size_series.mode()
        mode_mb = mode_values.iloc[0] if not mode_values.empty else float("nan")
        print(f"Average raw parquet size: {avg_mb:.2f} MB")
        print(f"Median raw parquet size: {median_mb:.2f} MB")
        print(f"Mode raw parquet size: {mode_mb:.2f} MB")
        print(f"Min raw parquet size: {min_mb:.2f} MB")
        print(f"Max raw parquet size: {max_mb:.2f} MB")
        print(f"25th percentile size: {percentiles.loc[0.25]:.2f} MB")
        print(f"75th percentile size: {percentiles.loc[0.75]:.2f} MB")
        est_total_mb = avg_mb * total
        est_total_gb = est_total_mb / 1024
        est_total_tb = est_total_gb / 1024
        print(f"Estimated total storage: {est_total_gb:.2f} GB")
        # print(f"Estimated total storage: {est_total_tb:.3f} TB")
    else:
        print("Average raw parquet size: n/a")
        print("Median raw parquet size: n/a")
        print("Mode raw parquet size: n/a")
        print("Min raw parquet size: n/a")
        print("Max raw parquet size: n/a")
        print("25th percentile size: n/a")
        print("75th percentile size: n/a")
        print("Estimated total storage: n/a")
        print("Estimated total storage: n/a")

    def _print_rows(title: str, rows: list[dict[str, object]]) -> None:
        if not rows:
            return
        print("")
        print(title)
        limit = args.max_mismatches
        for item in rows[:limit]:
            print(f"- {item['FileName']} -> {item['ParquetPath']}")
        if len(rows) > limit:
            print(f"... ({len(rows) - limit} more)")

    _print_rows("Missing parquet files:", missing_files)
    _print_rows("Unexpected parquet files:", unexpected_files)

    if args.write_report is not None:
        report_rows = (
            [
                {
                    "Issue": "missing_parquet",
                    **row,
                }
                for row in missing_files
            ]
            + [
                {
                    "Issue": "unexpected_parquet",
                    **row,
                }
                for row in unexpected_files
            ]
        )
        report_path = args.write_report
        report_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(report_rows).to_csv(report_path, index=False)
        print(f"Report written: {report_path}")


if __name__ == "__main__":
    main()
