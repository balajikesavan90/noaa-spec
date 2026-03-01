"""End-to-end pipeline helpers for NOAA Global Hourly data."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Literal
import time
import math
import re

import pandas as pd
import numpy as np

from .cleaning import clean_noaa_dataframe
from .constants import (
    DEFAULT_END_YEAR,
    DEFAULT_START_YEAR,
    get_agg_func,
    get_field_rule,
    is_quality_column,
    to_friendly_column,
    to_internal_column,
)
from .noaa_client import (
    StationMetadata,
    build_file_list,
    count_years_per_file,
    fetch_station_metadata,
    fetch_station_metadata_for_years,
    get_years,
    normalize_station_file_name,
    url_for,
)


@dataclass(frozen=True)
class LocationDataOutputs:
    raw: pd.DataFrame
    cleaned: pd.DataFrame
    hourly: pd.DataFrame
    monthly: pd.DataFrame
    yearly: pd.DataFrame


AggregationStrategy = Literal[
    "best_hour",
    "fixed_hour",
    "hour_day_month_year",
    "weighted_hours",
    "daily_min_max_mean",
]

_TEMP_COL_RE = re.compile(r"^(temperature_c|dew_point_c|extreme_temp_c_\d+)(?P<suffix>.*)$")
_WIND_COL_RE = re.compile(r"^(wind_speed_ms|wind_gust_ms)(?P<suffix>.*)$")
_VIS_COL_RE = re.compile(r"^(visibility_m)(?P<suffix>.*)$")
_PRESSURE_COL_RE = re.compile(
    r"^(sea_level_pressure_hpa|altimeter_setting_hpa|station_pressure_hpa)(?P<suffix>.*)$"
)
_STATUS_COLUMNS = ("raw_data_pulled", "data_cleaned", "data_aggregated")


def _coerce_status_series(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series
    truthy = {"true", "1", "yes", "y", "t"}
    return series.fillna(False).astype(str).str.strip().str.lower().isin(truthy)


def _ensure_station_status_columns(frame: pd.DataFrame) -> pd.DataFrame:
    work = frame.copy()
    for col in _STATUS_COLUMNS:
        if col not in work.columns:
            work[col] = False
        else:
            work[col] = _coerce_status_series(work[col])
    return work


def _load_stations_csv(stations_csv: Path) -> pd.DataFrame:
    frame = pd.read_csv(stations_csv)
    return _ensure_station_status_columns(frame)


def _locate_station_index(
    frame: pd.DataFrame,
    file_name: str | None = None,
    station_id: str | None = None,
) -> int | None:
    if file_name:
        normalized = normalize_station_file_name(file_name)
        matches = frame[frame["FileName"].astype(str) == normalized]
        if not matches.empty:
            return int(matches.index[0])

    if station_id and "ID" in frame.columns:
        key = str(station_id).lstrip("0")
        id_series = frame["ID"].astype(str).str.lstrip("0")
        matches = frame[id_series == key]
        if not matches.empty:
            return int(matches.index[0])

    if station_id:
        key = str(station_id).lstrip("0")
        file_series = frame["FileName"].astype(str).str.replace(".csv", "", regex=False)
        file_series = file_series.str.lstrip("0")
        matches = frame[file_series == key]
        if not matches.empty:
            return int(matches.index[0])

    return None


def update_station_status(
    stations_csv: Path,
    *,
    file_name: str | None = None,
    station_id: str | None = None,
    raw_data_pulled: bool | None = None,
    data_cleaned: bool | None = None,
    data_aggregated: bool | None = None,
) -> None:
    frame = _load_stations_csv(stations_csv)
    idx = _locate_station_index(frame, file_name=file_name, station_id=station_id)
    if idx is None:
        raise ValueError("Unable to locate station row to update status.")
    if raw_data_pulled is not None:
        frame.loc[idx, "raw_data_pulled"] = bool(raw_data_pulled)
    if data_cleaned is not None:
        frame.loc[idx, "data_cleaned"] = bool(data_cleaned)
    if data_aggregated is not None:
        frame.loc[idx, "data_aggregated"] = bool(data_aggregated)
    frame.to_csv(stations_csv, index=False)


def pick_random_station(
    stations_csv: Path,
    seed: int | None = None,
) -> dict[str, object]:
    frame = _load_stations_csv(stations_csv)
    candidates = frame[~frame["raw_data_pulled"]]
    if candidates.empty:
        raise ValueError("No stations available with raw_data_pulled == False.")
    return candidates.sample(n=1, random_state=seed).iloc[0].to_dict()


def pull_random_station_raw(
    stations_csv: Path,
    years: Iterable[int],
    output_dir: Path,
    sleep_seconds: float = 0.0,
    seed: int | None = None,
) -> Path:
    station = pick_random_station(stations_csv, seed=seed)
    file_name = str(station["FileName"])
    raw = download_location_data(
        file_name,
        years,
        sleep_seconds=sleep_seconds,
        log_years=True,
    )
    if raw.empty:
        raise ValueError("No raw data returned for selected station.")
    station_id = Path(normalize_station_file_name(file_name)).stem
    station_dir = output_dir / station_id
    station_dir.mkdir(parents=True, exist_ok=True)
    output_path = station_dir / "LocationData_Raw.parquet"
    raw.to_parquet(output_path, index=False)
    update_station_status(stations_csv, file_name=file_name, raw_data_pulled=True)
    return output_path


def clean_parquet_file(
    raw_parquet: Path,
    output_dir: Path | None = None,
    stations_csv: Path | None = None,
    file_name: str | None = None,
    station_id: str | None = None,
    strict_mode: bool = True,
) -> Path:
    raw = pd.read_parquet(raw_parquet)
    cleaned = clean_noaa_dataframe(raw, keep_raw=True, strict_mode=strict_mode)
    cleaned = _extract_time_columns(cleaned)
    target_dir = output_dir or raw_parquet.parent
    target_dir.mkdir(parents=True, exist_ok=True)
    output_path = target_dir / "LocationData_Cleaned.parquet"
    cleaned.to_parquet(output_path, index=False)
    if stations_csv is not None:
        if station_id is None:
            station_id = raw_parquet.parent.name
        update_station_status(
            stations_csv,
            file_name=file_name,
            station_id=station_id,
            data_cleaned=True,
        )
    return output_path


def aggregate_parquet_placeholder(*_: object, **__: object) -> None:
    raise NotImplementedError("Aggregation from parquet is not implemented yet.")


def build_data_file_list(
    output_csv: Path,
    sleep_seconds: float = 0.0,
    retries: int = 3,
    backoff_base: float = 0.5,
    backoff_max: float = 8.0,
) -> pd.DataFrame:
    years = get_years(
        retries=retries,
        backoff_base=backoff_base,
        backoff_max=backoff_max,
    )
    file_list = build_file_list(
        years,
        sleep_seconds=sleep_seconds,
        retries=retries,
        backoff_base=backoff_base,
        backoff_max=backoff_max,
    )
    file_list.to_csv(output_csv, index=False)
    return file_list


def build_year_counts(
    file_list: pd.DataFrame,
    output_csv: Path,
    start_year: int = DEFAULT_START_YEAR,
    end_year: int = DEFAULT_END_YEAR,
) -> pd.DataFrame:
    counts = count_years_per_file(file_list, start_year, end_year)
    counts.to_csv(output_csv, index=False)
    return counts


def build_location_ids(
    year_counts: pd.DataFrame,
    output_csv: Path,
    metadata_years: Iterable[int],
    file_list: pd.DataFrame | None = None,
    start_year: int | None = None,
    end_year: int | None = None,
    include_legacy_id: bool = True,
    resume: bool = True,
    start_index: int = 0,
    max_locations: int | None = None,
    checkpoint_every: int = 100,
    checkpoint_dir: Path | None = None,
    sleep_seconds: float = 0.0,
    retries: int = 3,
    backoff_base: float = 0.5,
    backoff_max: float = 8.0,
) -> pd.DataFrame:
    full_coverage = year_counts
    rows: list[dict[str, object]] = []
    processed: set[str] = set()
    total = len(full_coverage)
    year_summary: dict[str, tuple[int | None, int | None, int | None]] = {}
    if resume and output_csv.exists():
        existing = pd.read_csv(output_csv)
        if not existing.empty:
            existing = _ensure_station_status_columns(existing)
            rows = existing.to_dict(orient="records")
            processed = set(existing["FileName"].dropna().astype(str))
            print(
                f"Resuming Stations.csv: {len(rows)} rows already written; "
                f"{len(processed)} stations will be skipped."
            )
    metadata_years = list(metadata_years)
    if not metadata_years:
        raise ValueError("metadata_years must contain at least one year")
    if checkpoint_every is not None and checkpoint_every <= 0:
        raise ValueError("checkpoint_every must be positive")
    if start_index < 0:
        raise ValueError("start_index must be >= 0")
    if file_list is not None:
        work = file_list.copy()
        if "YEAR" in work.columns:
            work["YEAR"] = pd.to_numeric(work["YEAR"], errors="coerce")
        if start_year is not None:
            work = work[work["YEAR"] >= start_year]
        if end_year is not None:
            work = work[work["YEAR"] <= end_year]
        grouped = work.groupby("FileName")["YEAR"].agg(["min", "max", "count"]).reset_index()
        year_summary = {
            row["FileName"]: (
                int(row["min"]) if pd.notna(row["min"]) else None,
                int(row["max"]) if pd.notna(row["max"]) else None,
                int(row["count"]) if pd.notna(row["count"]) else None,
            )
            for _, row in grouped.iterrows()
        }

    new_count = 0
    print(
        f"Starting metadata fetch for {total} stations "
        f"(start_index={start_index}, max_locations={max_locations})."
    )
    for idx, file_name in enumerate(full_coverage["FileName"], start=1):
        if idx <= start_index:
            continue
        if max_locations is not None and new_count >= max_locations:
            break
        if file_name in processed:
            continue
        metadata, metadata_year = fetch_station_metadata_for_years(
            file_name,
            metadata_years,
            sleep_seconds=sleep_seconds,
            retries=retries,
            backoff_base=backoff_base,
            backoff_max=backoff_max,
        )
        if metadata is None or metadata_year is None:
            continue
        station_id = Path(normalize_station_file_name(metadata.file_name)).stem
        metadata_complete = all(
            value is not None
            for value in (
                metadata.latitude,
                metadata.longitude,
                metadata.elevation,
                metadata.name,
            )
        )
        first_year, last_year, year_count = year_summary.get(file_name, (None, None, None))
        row: dict[str, object] = {
            "ID": station_id,
            "FileName": metadata.file_name,
            "LATITUDE": metadata.latitude,
            "LONGITUDE": metadata.longitude,
            "ELEVATION": metadata.elevation,
            "NAME": metadata.name,
            "No_Of_Years": int(
                year_counts.loc[year_counts["FileName"] == file_name, "No_Of_Years"].iloc[0]
            ),
            "FIRST_YEAR": first_year,
            "LAST_YEAR": last_year,
            "YEAR_COUNT": year_count,
            "METADATA_YEAR": metadata_year,
            "METADATA_COMPLETE": metadata_complete,
            "raw_data_pulled": False,
            "data_cleaned": False,
            "data_aggregated": False,
        }
        if include_legacy_id:
            row["LegacyID"] = idx
        rows.append(
            row
        )
        processed.add(file_name)
        new_count += 1
        print(
            f"Fetched {file_name} (year={metadata_year}) -> "
            f"{len(rows)}/{total} total, {new_count} new."
        )
        if checkpoint_every and (len(rows) % checkpoint_every == 0):
            frame = pd.DataFrame(rows)
            frame.to_csv(output_csv, index=False)
            target_dir = checkpoint_dir or output_csv.parent
            checkpoint_path = target_dir / f"{output_csv.stem}_checkpoint_{len(rows):05d}.csv"
            frame.to_csv(checkpoint_path, index=False)
            print(
                f"Progress: {len(rows)}/{total} rows saved "
                f"(new this run: {new_count})."
            )
        if sleep_seconds > 0:
            time.sleep(sleep_seconds)
    frame = pd.DataFrame(rows)
    frame.to_csv(output_csv, index=False)
    print(
        f"Finished metadata fetch. Total rows: {len(rows)} "
        f"(new this run: {new_count})."
    )
    return frame


def download_location_data(
    file_name: str,
    years: Iterable[int],
    sleep_seconds: float = 0.0,
    log_years: bool = False,
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for year in years:
        url = url_for(year, file_name)
        try:
            frame = pd.read_csv(url, dtype=str, low_memory=False)
        except Exception:
            continue
        if not frame.empty:
            frame["YEAR"] = year
            frames.append(frame)
            if log_years:
                print(f"Downloaded {file_name} for year {year} ({len(frame)} rows).")
        if sleep_seconds > 0:
            time.sleep(sleep_seconds)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def _extract_time_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    date_series = pd.to_datetime(df["DATE"], errors="coerce", utc=True)
    time_offsets = None
    if "TIME" in df.columns:
        time_series = df["TIME"].astype("string")
        valid_times = time_series.str.fullmatch(r"\d{4}")
        hours = pd.to_numeric(time_series.str.slice(0, 2), errors="coerce")
        minutes = pd.to_numeric(time_series.str.slice(2, 4), errors="coerce")
        valid_times = valid_times & hours.between(0, 23) & minutes.between(0, 59)
        time_offsets = (
            pd.to_timedelta(hours.fillna(0), unit="h")
            + pd.to_timedelta(minutes.fillna(0), unit="m")
        ).where(valid_times)

    def _combine_date_and_time(
        timestamps: pd.Series,
        offsets: pd.Series | None,
    ) -> pd.Series:
        if offsets is None:
            return timestamps
        date_only = timestamps.notna() & (timestamps.dt.floor("D") == timestamps)
        combine_mask = date_only & offsets.notna()
        combined = timestamps.copy()
        combined.loc[combine_mask] = (
            timestamps.loc[combine_mask].dt.floor("D") + offsets.loc[combine_mask]
        )
        return combined

    date_series = _combine_date_and_time(date_series, time_offsets)
    if "DATE_PARSED" in df.columns:
        fallback = pd.to_datetime(df["DATE_PARSED"], errors="coerce", utc=True)
        fallback = _combine_date_and_time(fallback, time_offsets)
        date_series = date_series.fillna(fallback)
        df = df.drop(columns=["DATE_PARSED"])
    df["DATE"] = date_series
    df = df.dropna(subset=["DATE"])
    df["Year"] = df["DATE"].dt.year
    df["MonthNum"] = df["DATE"].dt.month
    df["Day"] = df["DATE"].dt.date
    df["Hour"] = df["DATE"].dt.hour
    return df


def _best_hour(df: pd.DataFrame) -> int | None:
    if df.empty:
        return None
    counts = df.groupby("Hour")["Day"].nunique().sort_values(ascending=False)
    if counts.empty:
        return None
    return int(counts.index[0])


def _filter_full_months(df: pd.DataFrame, min_days: int = 20) -> pd.DataFrame:
    days = df.groupby(["Year", "MonthNum"])['Day'].nunique().reset_index(name="days")
    full = days[days["days"] >= min_days]
    return df.merge(full[["Year", "MonthNum"]], on=["Year", "MonthNum"], how="inner")


def _filter_full_years(df: pd.DataFrame, min_months: int = 12) -> pd.DataFrame:
    months = df.groupby("Year")["MonthNum"].nunique().reset_index(name="months")
    full = months[months["months"] >= min_months]
    return df[df["Year"].isin(full["Year"])]


def _coerce_numeric(
    df: pd.DataFrame,
    group_cols: list[str],
) -> tuple[pd.DataFrame, list[str]]:
    work = df.copy()
    numeric_cols = set(work.select_dtypes(include=["number"]).columns)
    candidates = [col for col in work.columns if col not in group_cols]

    for col in candidates:
        if col in numeric_cols:
            continue
        # Skip quality and categorical columns — they should never be
        # coerced into numbers for aggregation.
        if is_quality_column(col) or get_agg_func(col) == "drop":
            continue
        if work[col].dtype == "object":
            converted = pd.to_numeric(work[col], errors="coerce")
            if converted.notna().any():
                work[col] = converted
                numeric_cols.add(col)

    numeric_cols = [col for col in numeric_cols if col not in group_cols]
    # Defragment after column-by-column coercion to avoid PerformanceWarning
    # from pandas when the DataFrame has many internal blocks.
    work = work.copy()
    return work, numeric_cols


def _classify_columns(
    numeric_cols: list[str],
) -> dict[str, list[str]]:
    """Split *numeric_cols* into buckets keyed by aggregation function.

    Returns a dict like ``{"mean": [...], "max": [...], "min": [...], "drop": [...]}``.
    """
    buckets: dict[str, list[str]] = {}
    for col in numeric_cols:
        func = get_agg_func(col)
        buckets.setdefault(func, []).append(col)
    return buckets


def _circular_mean_deg(values: pd.Series, weights: pd.Series | None = None) -> float | None:
    series = pd.to_numeric(values, errors="coerce")
    if weights is None:
        series = series.dropna()
        if series.empty:
            return None
        radians = np.deg2rad(series)
        mean_sin = np.sin(radians).mean()
        mean_cos = np.cos(radians).mean()
    else:
        combined = pd.concat([series, weights], axis=1).dropna()
        if combined.empty:
            return None
        radians = np.deg2rad(combined.iloc[:, 0])
        w = pd.to_numeric(combined.iloc[:, 1], errors="coerce").fillna(0.0)
        total = w.sum()
        if total == 0:
            return None
        mean_sin = (np.sin(radians) * w).sum() / total
        mean_cos = (np.cos(radians) * w).sum() / total
    angle = math.atan2(mean_sin, mean_cos)
    return (math.degrees(angle) + 360.0) % 360.0


def _aggregate_numeric(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    work, numeric_cols = _coerce_numeric(df, group_cols)
    if not numeric_cols:
        return work[group_cols].drop_duplicates()

    buckets = _classify_columns(numeric_cols)
    # Drop categorical / quality columns from aggregation entirely.
    drop_cols = set(buckets.pop("drop", []))
    circular_cols = buckets.pop("circular_mean", [])
    agg_cols = [c for c in numeric_cols if c not in drop_cols]
    if not agg_cols:
        return work[group_cols].drop_duplicates()

    # Build per-column aggregation spec.
    agg_spec: dict[str, str | list[str]] = {}
    for func_name, cols in buckets.items():
        for col in cols:
            agg_spec[col] = func_name  # "mean", "max", "min", "sum"

    grouped = work.groupby(group_cols)

    # Handle mode separately (not natively supported by groupby.agg).
    mode_cols = buckets.pop("mode", [])
    for col in mode_cols:
        agg_spec.pop(col, None)
    for col in circular_cols:
        agg_spec.pop(col, None)

    agg = grouped.agg(agg_spec).reset_index() if agg_spec else work[group_cols].drop_duplicates()

    if mode_cols:
        for col in mode_cols:
            mode_series = grouped[col].agg(
                lambda x: x.mode().iloc[0] if not x.mode().empty else None
            ).reset_index(name=col)
            agg = agg.merge(mode_series, on=group_cols, how="left")

    if circular_cols:
        for col in circular_cols:
            circ_series = grouped[col].agg(_circular_mean_deg).reset_index(name=col)
            agg = agg.merge(circ_series, on=group_cols, how="left")

    return agg


def _drop_metadata_columns(df: pd.DataFrame) -> pd.DataFrame:
    drop_cols = [
        col
        for col in df.columns
        if col not in {"ID", "Year", "MonthNum", "Day", "Hour"}
        and (is_quality_column(col) or get_agg_func(col) == "drop")
    ]
    if not drop_cols:
        return df
    return df.drop(columns=drop_cols)


def _apply_quality_filters_for_aggregation(df: pd.DataFrame) -> pd.DataFrame:
    """Null values with erroneous quality codes (3, 7) before aggregation."""
    bad_quality = {"3", "7"}
    work = df.copy()
    for col in df.columns:
        internal = to_internal_column(col)
        parts = internal.split("__", 1)
        if len(parts) != 2:
            continue
        prefix, suffix = parts
        if suffix in {"quality", "qc"}:
            continue
        rule = get_field_rule(prefix)
        if rule is None:
            continue
        if suffix == "value":
            quality_col_internal = f"{prefix}__quality"
        elif suffix.startswith("part"):
            try:
                part_idx = int(suffix[4:])
            except ValueError:
                continue
            part_rule = rule.parts.get(part_idx)
            if part_rule is None or part_rule.quality_part is None:
                continue
            quality_col_internal = f"{prefix}__part{part_rule.quality_part}"
        else:
            continue
        quality_col = to_friendly_column(quality_col_internal)
        if quality_col not in work.columns:
            continue
        mask = work[quality_col].astype(str).isin(bad_quality)
        if mask.any():
            work.loc[mask, col] = pd.NA
    return work


def _add_unit_conversions(df: pd.DataFrame) -> pd.DataFrame:
    work = df.copy()
    for col in df.columns:
        series = pd.to_numeric(df[col], errors="coerce")
        if series.isna().all():
            continue
        temp_match = _TEMP_COL_RE.match(col)
        if temp_match:
            suffix = temp_match.group("suffix")
            work[f"{temp_match.group(1)}_f{suffix}"] = (series * 9.0 / 5.0) + 32.0
            continue
        wind_match = _WIND_COL_RE.match(col)
        if wind_match:
            suffix = wind_match.group("suffix")
            work[f"{wind_match.group(1)}_kt{suffix}"] = series * 1.9438444924
            work[f"{wind_match.group(1)}_mph{suffix}"] = series * 2.2369362921
            continue
        vis_match = _VIS_COL_RE.match(col)
        if vis_match:
            suffix = vis_match.group("suffix")
            work[f"visibility_mi{suffix}"] = series / 1609.344
            continue
        pressure_match = _PRESSURE_COL_RE.match(col)
        if pressure_match:
            suffix = pressure_match.group("suffix")
            work[f"{pressure_match.group(1)}_inhg{suffix}"] = series * 0.0295299830714
    return work


def _weighted_aggregate(
    df: pd.DataFrame,
    group_cols: list[str],
    weight_col: str,
) -> pd.DataFrame:
    work, numeric_cols = _coerce_numeric(df, group_cols + [weight_col])
    if not numeric_cols:
        return work[group_cols].drop_duplicates()

    # Exclude drop-columns (categorical / quality).
    buckets = _classify_columns(numeric_cols)
    drop_cols = set(buckets.pop("drop", []))
    keep_cols = [c for c in numeric_cols if c not in drop_cols]
    if not keep_cols:
        return work[group_cols].drop_duplicates()

    group = work.groupby(group_cols)
    weight_sum = group[weight_col].sum()
    data: dict[str, pd.Series] = {}
    for col in keep_cols:
        func = get_agg_func(col)
        if func == "max":
            data[col] = group[col].max()
        elif func == "min":
            data[col] = group[col].min()
        elif func == "sum":
            data[col] = group[col].sum()
        elif func == "circular_mean":
            data[col] = group.apply(lambda g: _circular_mean_deg(g[col], g[weight_col]))
        else:
            weighted_sum = (work[col] * work[weight_col]).groupby(
                [work[g] for g in group_cols]
            ).sum()
            data[col] = weighted_sum / weight_sum
    return pd.DataFrame(data).reset_index()


def _daily_min_max_mean(
    df: pd.DataFrame,
    group_cols: list[str],
) -> pd.DataFrame:
    work, numeric_cols = _coerce_numeric(df, group_cols)
    if not numeric_cols:
        return work[group_cols].drop_duplicates()

    # Exclude drop-columns (categorical / quality).
    buckets = _classify_columns(numeric_cols)
    drop_cols = set(buckets.pop("drop", []))
    keep_cols = [c for c in numeric_cols if c not in drop_cols]
    if not keep_cols:
        return work[group_cols].drop_duplicates()

    group = work.groupby(group_cols)
    frames: list[pd.Series] = []
    for col in keep_cols:
        if get_agg_func(col) == "circular_mean":
            frames.append(
                group[col].agg(_circular_mean_deg).rename(f"{col}__daily_mean")
            )
            continue
        frames.append(group[col].min().rename(f"{col}__daily_min"))
        frames.append(group[col].max().rename(f"{col}__daily_max"))
        frames.append(group[col].mean().rename(f"{col}__daily_mean"))
    return pd.concat(frames, axis=1).reset_index()


def process_location(
    file_name: str,
    years: Iterable[int],
    location_id: int | None = None,
    aggregation_strategy: AggregationStrategy = "best_hour",
    min_hours_per_day: int = 18,
    min_days_per_month: int = 20,
    min_months_per_year: int = 12,
    fixed_hour: int | None = None,
    sleep_seconds: float = 0.0,
    add_unit_conversions: bool = False,
    strict_mode: bool = True,
) -> LocationDataOutputs:
    raw = download_location_data(file_name, years, sleep_seconds=sleep_seconds)
    return process_location_from_raw(
        raw,
        location_id=location_id,
        aggregation_strategy=aggregation_strategy,
        min_hours_per_day=min_hours_per_day,
        min_days_per_month=min_days_per_month,
        min_months_per_year=min_months_per_year,
        fixed_hour=fixed_hour,
        add_unit_conversions=add_unit_conversions,
        strict_mode=strict_mode,
    )


def process_location_from_raw(
    raw: pd.DataFrame,
    location_id: int | None = None,
    aggregation_strategy: AggregationStrategy = "best_hour",
    min_hours_per_day: int = 18,
    min_days_per_month: int = 20,
    min_months_per_year: int = 12,
    fixed_hour: int | None = None,
    add_unit_conversions: bool = False,
    strict_mode: bool = True,
) -> LocationDataOutputs:
    if raw.empty:
        return LocationDataOutputs(
            raw=raw,
            cleaned=raw,
            hourly=raw,
            monthly=raw,
            yearly=raw,
        )

    raw = raw.copy()
    if "DATE" in raw.columns:
        raw["DATE_PARSED"] = pd.to_datetime(raw["DATE"], errors="coerce", utc=True)
    cleaned = clean_noaa_dataframe(raw, keep_raw=True, strict_mode=strict_mode)
    cleaned = _extract_time_columns(cleaned)
    if location_id is not None:
        cleaned["ID"] = location_id

    agg_ready = _apply_quality_filters_for_aggregation(cleaned)

    month_group = ["Year", "MonthNum"]
    year_group = ["Year"]
    if "ID" in cleaned.columns:
        month_group = ["ID"] + month_group
        year_group = ["ID"] + year_group

    if aggregation_strategy == "best_hour":
        hourly = cleaned
        best_hour = _best_hour(hourly)
        if best_hour is not None:
            hourly = hourly[hourly["Hour"] == best_hour]
        hourly_agg = _apply_quality_filters_for_aggregation(hourly)
        hourly_agg = _filter_full_months(hourly_agg, min_days=min_days_per_month)
        hourly_agg = _filter_full_years(hourly_agg, min_months=min_months_per_year)
        monthly = _aggregate_numeric(hourly_agg, month_group)
        yearly = _aggregate_numeric(hourly_agg, year_group)
    elif aggregation_strategy == "fixed_hour":
        if fixed_hour is None:
            raise ValueError("fixed_hour must be provided for fixed_hour strategy")
        hourly = cleaned[cleaned["Hour"] == fixed_hour]
        hourly_agg = _apply_quality_filters_for_aggregation(hourly)
        hourly_agg = _filter_full_months(hourly_agg, min_days=min_days_per_month)
        hourly_agg = _filter_full_years(hourly_agg, min_months=min_months_per_year)
        monthly = _aggregate_numeric(hourly_agg, month_group)
        yearly = _aggregate_numeric(hourly_agg, year_group)
    elif aggregation_strategy == "hour_day_month_year":
        hour_group = ["Year", "MonthNum", "Day", "Hour"]
        day_group = ["Year", "MonthNum", "Day"]
        if "ID" in cleaned.columns:
            hour_group = ["ID"] + hour_group
            day_group = ["ID"] + day_group
        hourly = _aggregate_numeric(agg_ready, hour_group)
        daily = _aggregate_numeric(hourly, day_group)
        daily = _filter_full_months(daily, min_days=min_days_per_month)
        daily = _filter_full_years(daily, min_months=min_months_per_year)
        valid_months = daily[["Year", "MonthNum"]].drop_duplicates()
        hourly = hourly.merge(valid_months, on=["Year", "MonthNum"], how="inner")
        hourly = hourly[hourly["Year"].isin(daily["Year"].unique())]
        monthly = _aggregate_numeric(daily, month_group)
        yearly = _aggregate_numeric(daily, year_group)
    elif aggregation_strategy == "weighted_hours":
        hour_group = ["Year", "MonthNum", "Day", "Hour"]
        day_group = ["Year", "MonthNum", "Day"]
        if "ID" in cleaned.columns:
            hour_group = ["ID"] + hour_group
            day_group = ["ID"] + day_group
        hourly = _aggregate_numeric(agg_ready, hour_group)
        hours_per_day = (
            hourly.groupby(day_group)["Hour"].nunique().reset_index(name="hours")
        )
        hours_per_day = hours_per_day[hours_per_day["hours"] >= min_hours_per_day]
        daily = _aggregate_numeric(hourly, day_group)
        daily = daily.merge(hours_per_day, on=day_group, how="inner")
        daily = _filter_full_months(daily, min_days=min_days_per_month)
        daily = _filter_full_years(daily, min_months=min_months_per_year)
        valid_days = daily[day_group].drop_duplicates()
        hourly = hourly.merge(valid_days, on=day_group, how="inner")
        monthly = _weighted_aggregate(daily, month_group, "hours")
        yearly = _weighted_aggregate(daily, year_group, "hours")
    elif aggregation_strategy == "daily_min_max_mean":
        hour_group = ["Year", "MonthNum", "Day", "Hour"]
        day_group = ["Year", "MonthNum", "Day"]
        if "ID" in cleaned.columns:
            hour_group = ["ID"] + hour_group
            day_group = ["ID"] + day_group
        hourly = _aggregate_numeric(agg_ready, hour_group)
        daily = _daily_min_max_mean(hourly, day_group)
        daily = _filter_full_months(daily, min_days=min_days_per_month)
        daily = _filter_full_years(daily, min_months=min_months_per_year)
        valid_days = daily[day_group].drop_duplicates()
        hourly = hourly.merge(valid_days, on=day_group, how="inner")
        monthly = _aggregate_numeric(daily, month_group)
        yearly = _aggregate_numeric(daily, year_group)
    else:
        raise ValueError(f"Unknown aggregation strategy: {aggregation_strategy}")

    monthly = _drop_metadata_columns(monthly)
    yearly = _drop_metadata_columns(yearly)

    if add_unit_conversions:
        cleaned = _add_unit_conversions(cleaned)
        hourly = _add_unit_conversions(hourly)
        monthly = _add_unit_conversions(monthly)
        yearly = _add_unit_conversions(yearly)

    return LocationDataOutputs(
        raw=raw,
        cleaned=cleaned,
        hourly=hourly,
        monthly=monthly,
        yearly=yearly,
    )
