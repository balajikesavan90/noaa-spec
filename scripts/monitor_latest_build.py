"""Monitor progress for the latest cleaning build."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import math
from pathlib import Path
import sys
import time

import pandas as pd


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Monitor progress for the latest or selected cleaning build."
    )
    parser.add_argument(
        "--release-base-root",
        type=Path,
        default=None,
        help=(
            "Root containing build_<run_id> release folders "
            "(default: inferred from local state, otherwise ./release)"
        ),
    )
    parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="Specific run_id to inspect (default: latest build folder by name)",
    )
    parser.add_argument(
        "--watch-seconds",
        type=int,
        default=None,
        help="Refresh every N seconds until interrupted",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=5,
        help="How many slowest completed stations to print (default: 5)",
    )
    return parser.parse_args()


def _infer_release_base_root() -> Path:
    raw_pull_state_csv = Path("noaa_file_index/state/raw_pull_state.csv")
    if raw_pull_state_csv.exists():
        try:
            frame = pd.read_csv(raw_pull_state_csv, usecols=["raw_path"])
        except Exception:
            frame = pd.DataFrame(columns=["raw_path"])
        candidate_roots: list[Path] = []
        for raw_path in frame["raw_path"].dropna().astype(str):
            raw_path = raw_path.strip()
            if not raw_path:
                continue
            path = Path(raw_path)
            if len(path.parts) < 3:
                continue
            candidate_roots.append(path.parent.parent.parent / "NOAA_CLEANED_DATA")
        if candidate_roots:
            most_common_root, _ = Counter(candidate_roots).most_common(1)[0]
            if most_common_root.exists():
                return most_common_root

    return Path("release")


def _resolve_build_root(release_base_root: Path, run_id: str | None) -> Path:
    release_base_root = release_base_root.resolve()
    if run_id:
        build_root = release_base_root / f"build_{run_id}"
        if not build_root.exists():
            raise FileNotFoundError(f"Build not found: {build_root}")
        return build_root

    builds = sorted(
        path
        for path in release_base_root.glob("build_*")
        if path.is_dir()
    )
    if not builds:
        raise FileNotFoundError(f"No build_* folders found under {release_base_root}")
    return builds[-1]


def _load_progress(build_root: Path) -> dict[str, object]:
    manifest_path = build_root / "manifests" / "run_manifest.csv"
    status_path = build_root / "manifests" / "run_status.csv"
    run_state_path = build_root / "manifests" / "run_state.json"

    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing run manifest: {manifest_path}")
    if not status_path.exists():
        raise FileNotFoundError(f"Missing run status: {status_path}")

    manifest = pd.read_csv(manifest_path, dtype=str)
    status = pd.read_csv(status_path, dtype=str)

    manifest["input_size_bytes_num"] = pd.to_numeric(
        manifest.get("input_size_bytes"),
        errors="coerce",
    ).fillna(0)
    status["input_size_bytes_num"] = pd.to_numeric(
        status.get("input_size_bytes"),
        errors="coerce",
    ).fillna(0)
    status["elapsed_total_seconds_num"] = pd.to_numeric(
        status.get("elapsed_total_seconds"),
        errors="coerce",
    )

    status_counts = status["status"].fillna("").astype(str).value_counts().to_dict()

    completed = status[status["status"].astype(str) == "completed"].copy()
    running = status[status["status"].astype(str) == "running"].copy()
    retrying = status[status["status"].astype(str) == "retrying"].copy()
    failed = status[status["status"].astype(str) == "failed"].copy()
    pending = status[status["status"].astype(str) == "pending"].copy()

    total_count = int(len(manifest))
    completed_count = int(len(completed))
    running_count = int(len(running))
    pending_count = int(len(pending))

    total_bytes = int(manifest["input_size_bytes_num"].sum())
    completed_bytes = int(completed["input_size_bytes_num"].sum())
    running_bytes = int(running["input_size_bytes_num"].sum())
    remaining_bytes = total_bytes - completed_bytes

    completed_seconds = completed["elapsed_total_seconds_num"].dropna()
    mean_station_seconds = float(completed_seconds.mean()) if not completed_seconds.empty else math.nan
    median_station_seconds = (
        float(completed_seconds.median()) if not completed_seconds.empty else math.nan
    )
    seconds_per_byte = (
        float(completed_seconds.sum()) / float(completed_bytes)
        if completed_bytes > 0 and not completed_seconds.empty
        else math.nan
    )

    running_rows = running[
        [
            "station_id",
            "started_at",
            "input_size_bytes",
            "retry_count",
            "last_exit_code",
            "failure_stage",
            "last_error_summary",
        ]
    ].fillna("").to_dict(orient="records")
    retry_rows = retrying[
        [
            "station_id",
            "retry_count",
            "last_exit_code",
            "failure_stage",
            "last_error_summary",
        ]
    ].fillna("").to_dict(orient="records")
    failed_rows = failed[
        [
            "station_id",
            "retry_count",
            "last_exit_code",
            "failure_stage",
            "last_error_summary",
        ]
    ].fillna("").to_dict(orient="records")

    slowest_completed = []
    if not completed.empty:
        cols = ["station_id", "input_size_bytes", "elapsed_total_seconds", "retry_count"]
        slowest_completed = (
            completed.sort_values("elapsed_total_seconds_num", ascending=False)[cols]
            .head(10)
            .fillna("")
            .to_dict(orient="records")
        )

    return {
        "build_root": build_root,
        "manifest_path": manifest_path,
        "status_path": status_path,
        "run_state_exists": run_state_path.exists(),
        "status_counts": status_counts,
        "total_count": total_count,
        "completed_count": completed_count,
        "running_count": running_count,
        "pending_count": pending_count,
        "retrying_count": int(len(retrying)),
        "failed_count": int(len(failed)),
        "completed_fraction": (completed_count / total_count) if total_count else 0.0,
        "completed_plus_running_fraction": (
            (completed_count + running_count) / total_count if total_count else 0.0
        ),
        "total_bytes": total_bytes,
        "completed_bytes": completed_bytes,
        "running_bytes": running_bytes,
        "remaining_bytes": remaining_bytes,
        "completed_byte_fraction": (completed_bytes / total_bytes) if total_bytes else 0.0,
        "completed_plus_running_byte_fraction": (
            (completed_bytes + running_bytes) / total_bytes if total_bytes else 0.0
        ),
        "mean_station_seconds": mean_station_seconds,
        "median_station_seconds": median_station_seconds,
        "seconds_per_byte": seconds_per_byte,
        "estimated_remaining_mean_station_seconds": (
            (pending_count + running_count) * mean_station_seconds
            if not math.isnan(mean_station_seconds)
            else math.nan
        ),
        "estimated_remaining_median_station_seconds": (
            (pending_count + running_count) * median_station_seconds
            if not math.isnan(median_station_seconds)
            else math.nan
        ),
        "estimated_remaining_byte_seconds": (
            remaining_bytes * seconds_per_byte
            if not math.isnan(seconds_per_byte)
            else math.nan
        ),
        "running_rows": running_rows,
        "retry_rows": retry_rows,
        "failed_rows": failed_rows,
        "slowest_completed": slowest_completed,
    }


def _format_minutes(value: float) -> str:
    if value != value or value < 0:
        return "n/a"
    minutes = float(value) / 60.0
    return f"{minutes:.1f} min"


def _format_megabytes(value: int | float) -> str:
    size_mb = float(value) / (1024.0 * 1024.0)
    return f"{size_mb:.2f} MB"


def _print_progress(progress: dict[str, object], *, top: int) -> None:
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    print(f"As of: {now}")
    print(f"Build root: {progress['build_root']}")
    print(f"run_state.json exists: {progress['run_state_exists']}")
    print("")

    print("Counts")
    print(f"  completed: {progress['completed_count']} / {progress['total_count']}")
    print(f"  running:   {progress['running_count']}")
    print(f"  pending:   {progress['pending_count']}")
    print(f"  retrying:  {progress['retrying_count']}")
    print(f"  failed:    {progress['failed_count']}")
    print(f"  status_counts: {progress['status_counts']}")
    print("")

    print("Progress")
    print(f"  station fraction completed: {float(progress['completed_fraction']):.2%}")
    print(
        "  station fraction incl. running: "
        f"{float(progress['completed_plus_running_fraction']):.2%}"
    )
    print(
        "  bytes completed: "
        f"{_format_megabytes(int(progress['completed_bytes']))} / "
        f"{_format_megabytes(int(progress['total_bytes']))}"
    )
    print(
        "  byte fraction completed: "
        f"{float(progress['completed_byte_fraction']):.2%}"
    )
    print(
        "  byte fraction incl. running: "
        f"{float(progress['completed_plus_running_byte_fraction']):.2%}"
    )
    print("")

    print("ETA")
    print(
        "  mean-station estimate remaining: "
        f"{_format_minutes(float(progress['estimated_remaining_mean_station_seconds']))}"
    )
    print(
        "  median-station estimate remaining: "
        f"{_format_minutes(float(progress['estimated_remaining_median_station_seconds']))}"
    )
    print(
        "  byte-weighted estimate remaining: "
        f"{_format_minutes(float(progress['estimated_remaining_byte_seconds']))}"
    )
    print("")

    running_rows = list(progress["running_rows"])
    if running_rows:
        print("Running")
        for row in running_rows:
            print(
                f"  {row['station_id']} started_at={row['started_at']} "
                f"input_size={_format_megabytes(float(row['input_size_bytes'] or 0))} "
                f"retry_count={row['retry_count']}"
            )
        print("")

    retry_rows = list(progress["retry_rows"])
    if retry_rows:
        print("Retrying")
        for row in retry_rows:
            print(
                f"  {row['station_id']} retry_count={row['retry_count']} "
                f"last_exit_code={row['last_exit_code']} "
                f"failure_stage={row['failure_stage']} "
                f"last_error_summary={row['last_error_summary']}"
            )
        print("")

    failed_rows = list(progress["failed_rows"])
    if failed_rows:
        print("Failed")
        for row in failed_rows:
            print(
                f"  {row['station_id']} retry_count={row['retry_count']} "
                f"last_exit_code={row['last_exit_code']} "
                f"failure_stage={row['failure_stage']} "
                f"last_error_summary={row['last_error_summary']}"
            )
        print("")

    slowest_rows = list(progress["slowest_completed"])[:top]
    if slowest_rows:
        print(f"Slowest Completed Top {len(slowest_rows)}")
        for row in slowest_rows:
            print(
                f"  {row['station_id']} elapsed={_format_minutes(float(row['elapsed_total_seconds'] or 0))} "
                f"input_size={_format_megabytes(float(row['input_size_bytes'] or 0))} "
                f"retry_count={row['retry_count']}"
            )


def main() -> None:
    args = _parse_args()
    release_base_root = args.release_base_root or _infer_release_base_root()
    build_root = _resolve_build_root(release_base_root, args.run_id)

    while True:
        progress = _load_progress(build_root)
        _print_progress(progress, top=args.top)
        if args.watch_seconds is None:
            return
        time.sleep(args.watch_seconds)
        print("")


if __name__ == "__main__":
    main()
