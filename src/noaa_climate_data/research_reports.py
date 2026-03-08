"""Research-facing report generation for cleaned station outputs.

This module implements P3 report artifacts:
- LocationData_QualityReport.json
- LocationData_QualityReport.md
- LocationData_QualitySummary.csv
- LocationData_AggregationReport.json
- LocationData_AggregationReport.md
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

import pandas as pd

from . import __version__
from .constants import get_agg_func, get_field_rule, is_quality_column, to_internal_column
from .domain_split import DOMAIN_RULES, classify_columns
from .pipeline import _best_hour, _filter_full_months, _filter_full_years


_BAD_QUALITY_CODES = {"3", "7"}
_TIME_COLUMNS = {"DATE", "Year", "MonthNum", "MonthName", "Day", "Hour", "YEAR"}
_ID_COLUMNS = {
    "ID",
    "station_id",
    "station_name",
    "STATION",
    "SOURCE",
    "LATITUDE",
    "LONGITUDE",
    "ELEVATION",
    "NAME",
    "REPORT_TYPE",
    "CALL_SIGN",
    "QUALITY_CONTROL",
}


@dataclass(frozen=True)
class ResearchReportContext:
    station_id: str
    station_name: str | None
    access_date: str
    run_date_utc: str
    version: str
    authors: str


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _today_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _json_default(value: Any) -> Any:
    if isinstance(value, (pd.Timestamp, datetime)):
        if value.tzinfo is None:
            return value.isoformat()
        return value.astimezone(timezone.utc).isoformat()
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"Object of type {type(value)!r} is not JSON serializable")


def _metric_columns(df: pd.DataFrame) -> list[str]:
    cols: list[str] = []
    for col in df.columns:
        if col in _TIME_COLUMNS or col in _ID_COLUMNS:
            continue
        if is_quality_column(col):
            continue
        cols.append(col)
    return cols


def _parse_dates(frame: pd.DataFrame) -> pd.Series:
    if "DATE" not in frame.columns:
        return pd.Series(dtype="datetime64[ns, UTC]")
    return pd.to_datetime(frame["DATE"], errors="coerce", utc=True)


def _coverage_counts(date_series: pd.Series) -> dict[str, int]:
    valid = date_series.dropna()
    if valid.empty:
        return {"hours": 0, "days": 0, "months": 0}
    naive = valid.dt.tz_localize(None)
    return {
        "hours": int(valid.dt.floor("h").nunique()),
        "days": int(valid.dt.floor("D").nunique()),
        "months": int(naive.dt.to_period("M").nunique()),
    }


def _find_quality_column_for_metric(metric_col: str) -> str | None:
    internal = to_internal_column(metric_col)
    parts = internal.split("__", 1)
    if len(parts) != 2:
        return None
    prefix, suffix = parts
    rule = get_field_rule(prefix)
    if rule is None:
        return None

    if suffix == "value":
        part_index = 1
    elif suffix.startswith("part"):
        try:
            part_index = int(suffix[4:])
        except ValueError:
            return None
    else:
        return None

    part_rule = rule.parts.get(part_index)
    if part_rule is None or part_rule.quality_part is None:
        return None
    return f"{prefix}__part{part_rule.quality_part}"


def _raw_sentinel_mask_for_metric(raw: pd.DataFrame, metric_col: str) -> pd.Series:
    internal = to_internal_column(metric_col)
    parts = internal.split("__", 1)
    if len(parts) != 2:
        return pd.Series(False, index=raw.index)
    prefix, suffix = parts
    if prefix not in raw.columns:
        return pd.Series(False, index=raw.index)

    if suffix == "value":
        part_index = 1
    elif suffix.startswith("part"):
        try:
            part_index = int(suffix[4:])
        except ValueError:
            return pd.Series(False, index=raw.index)
    else:
        return pd.Series(False, index=raw.index)

    rule = get_field_rule(prefix)
    part_rule = rule.parts.get(part_index) if rule else None
    known_missing = set(part_rule.missing_values) if part_rule and part_rule.missing_values else set()

    series = raw[prefix].astype("string")

    def _is_missing_token(value: object) -> bool:
        if value is None or pd.isna(value):
            return False
        text = str(value)
        token_parts = text.split(",")
        if part_index - 1 >= len(token_parts):
            return False
        token = token_parts[part_index - 1].strip().lstrip("+")
        if token in known_missing:
            return True
        if token.startswith("-"):
            return False
        if token and set(token) == {"9"} and len(token) >= 2:
            return True
        return False

    return series.apply(_is_missing_token)


def _scale_factor_rows(cleaned: pd.DataFrame) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    seen: set[tuple[str, int]] = set()
    for col in cleaned.columns:
        internal = to_internal_column(col)
        parts = internal.split("__", 1)
        if len(parts) != 2:
            continue
        prefix, suffix = parts
        if suffix == "value":
            part_idx = 1
        elif suffix.startswith("part"):
            try:
                part_idx = int(suffix[4:])
            except ValueError:
                continue
        else:
            continue
        key = (prefix, part_idx)
        if key in seen:
            continue
        seen.add(key)
        rule = get_field_rule(prefix)
        if rule is None:
            continue
        part_rule = rule.parts.get(part_idx)
        if part_rule is None or part_rule.scale is None or part_rule.scale == 1:
            continue
        rows.append(
            {
                "field": prefix,
                "part": part_idx,
                "column": col,
                "scale": float(part_rule.scale),
            }
        )
    return sorted(rows, key=lambda row: (str(row["field"]), int(row["part"])))


def _longest_missing_runs(
    cleaned: pd.DataFrame,
    *,
    max_columns: int = 25,
) -> list[dict[str, object]]:
    if "DATE" not in cleaned.columns:
        return []
    work = cleaned.copy()
    work["DATE"] = pd.to_datetime(work["DATE"], errors="coerce", utc=True)
    work = work.dropna(subset=["DATE"]).sort_values("DATE")
    if work.empty:
        return []

    metric_cols = [col for col in _metric_columns(work) if col != "DATE"][:max_columns]
    results: list[dict[str, object]] = []
    for col in metric_cols:
        missing = work[col].isna()
        if not missing.any():
            continue

        run_groups = (missing != missing.shift(fill_value=False)).cumsum()
        run_lengths = (
            pd.DataFrame({"missing": missing, "grp": run_groups})
            .groupby("grp")["missing"]
            .agg(["first", "size"])
        )
        run_lengths = run_lengths[run_lengths["first"]]
        if run_lengths.empty:
            continue
        longest_group = int(run_lengths["size"].idxmax())
        longest_len = int(run_lengths.loc[longest_group, "size"])

        idx = run_groups[run_groups == longest_group].index
        start_ts = work.loc[idx.min(), "DATE"]
        end_ts = work.loc[idx.max(), "DATE"]
        duration_hours = (end_ts - start_ts).total_seconds() / 3600.0

        results.append(
            {
                "column": col,
                "longest_missing_observations": longest_len,
                "gap_start_utc": start_ts.isoformat(),
                "gap_end_utc": end_ts.isoformat(),
                "gap_duration_hours": round(float(duration_hours), 2),
            }
        )

    return sorted(results, key=lambda row: row["longest_missing_observations"], reverse=True)


def _citation_text(ctx: ResearchReportContext) -> str:
    station_ref = ctx.station_id
    return (
        f"{ctx.authors}. ({ctx.run_date_utc[:4]}). noaa-climate-data (Version {ctx.version}). "
        f"NOAA ISD Global Hourly data processed for station {station_ref}. "
        f"Retrieved {ctx.access_date} from "
        "https://www.ncei.noaa.gov/products/land-based-station/integrated-surface-database"
    )


def generate_quality_report(
    raw: pd.DataFrame,
    cleaned: pd.DataFrame,
    context: ResearchReportContext,
) -> tuple[dict[str, object], pd.DataFrame]:
    raw_dates = _parse_dates(raw)
    cleaned_dates = _parse_dates(cleaned)

    raw_rows = int(len(raw))
    cleaned_rows = int(len(cleaned))
    dropped_rows = int(max(raw_rows - cleaned_rows, 0))
    invalid_date_rows = int(raw_dates.isna().sum()) if "DATE" in raw.columns else 0

    missingness = pd.DataFrame(
        {
            "column": list(cleaned.columns),
            "missing_count": [int(cleaned[col].isna().sum()) for col in cleaned.columns],
            "rows": cleaned_rows,
        }
    )
    if cleaned_rows > 0:
        missingness["missing_pct"] = (missingness["missing_count"] / cleaned_rows).round(6)
    else:
        missingness["missing_pct"] = 0.0
    missingness = missingness.sort_values(["missing_pct", "column"], ascending=[False, True]).reset_index(drop=True)

    sentinel_rows: list[dict[str, object]] = []
    quality_filter_rows: list[dict[str, object]] = []
    for col in _metric_columns(cleaned):
        if col not in cleaned.columns:
            continue
        sentinel_mask = _raw_sentinel_mask_for_metric(raw, col)
        sentinel_count = int((sentinel_mask & cleaned[col].isna()).sum()) if len(sentinel_mask) == len(cleaned) else int(sentinel_mask.sum())
        if sentinel_count > 0:
            sentinel_rows.append({"column": col, "sentinel_replacements": sentinel_count})

        quality_col_internal = _find_quality_column_for_metric(col)
        if quality_col_internal and quality_col_internal in cleaned.columns:
            qmask = cleaned[quality_col_internal].astype("string").isin(_BAD_QUALITY_CODES)
            if qmask.any():
                quality_filter_rows.append(
                    {
                        "column": col,
                        "quality_column": quality_col_internal,
                        "bad_quality_rows": int(qmask.sum()),
                        "null_after_bad_quality": int((qmask & cleaned[col].isna()).sum()),
                    }
                )

    raw_coverage = _coverage_counts(raw_dates)
    cleaned_coverage = _coverage_counts(cleaned_dates)

    def _pct(retained: int, original: int) -> float:
        if original <= 0:
            return 0.0
        return round(retained / original, 6)

    report = {
        "station": {
            "station_id": context.station_id,
            "station_name": context.station_name,
        },
        "metadata": {
            "report_type": "data_quality",
            "generated_at_utc": context.run_date_utc,
            "data_access_date": context.access_date,
            "version": context.version,
        },
        "row_counts": {
            "raw_rows": raw_rows,
            "cleaned_rows": cleaned_rows,
            "dropped_rows": dropped_rows,
            "dropped_fraction": _pct(dropped_rows, raw_rows),
            "drop_reason_estimates": {
                "invalid_or_missing_date": invalid_date_rows,
                "unclassified_other": max(dropped_rows - invalid_date_rows, 0),
            },
        },
        "coverage_completeness": {
            "raw": raw_coverage,
            "cleaned": cleaned_coverage,
            "retained_fraction": {
                "hours": _pct(cleaned_coverage["hours"], raw_coverage["hours"]),
                "days": _pct(cleaned_coverage["days"], raw_coverage["days"]),
                "months": _pct(cleaned_coverage["months"], raw_coverage["months"]),
            },
        },
        "sentinel_replacement_counts": sorted(
            sentinel_rows,
            key=lambda row: row["sentinel_replacements"],
            reverse=True,
        ),
        "quality_flag_filtering_counts": sorted(
            quality_filter_rows,
            key=lambda row: row["bad_quality_rows"],
            reverse=True,
        ),
        "applied_scale_factors": _scale_factor_rows(cleaned),
        "notable_data_gaps": _longest_missing_runs(cleaned),
        "citation": _citation_text(context),
    }
    return report, missingness


def domain_quality_report_names() -> tuple[str, ...]:
    return tuple(name for name, _ in DOMAIN_RULES) + ("other",)


def generate_domain_quality_reports(
    cleaned: pd.DataFrame,
    context: ResearchReportContext,
) -> dict[str, tuple[dict[str, object], pd.DataFrame]]:
    rows_total = int(len(cleaned))
    _, domain_columns = classify_columns(list(cleaned.columns))
    metric_columns = set(_metric_columns(cleaned))

    reports: dict[str, tuple[dict[str, object], pd.DataFrame]] = {}
    for domain_name in domain_quality_report_names():
        selected_columns = sorted(domain_columns.get(domain_name, []))
        selected_metric_columns = [
            column for column in selected_columns if column in metric_columns
        ]

        if selected_metric_columns:
            domain_frame = cleaned[selected_metric_columns]
            rows_with_any_metric = int(domain_frame.notna().any(axis=1).sum())
            missingness = pd.DataFrame(
                {
                    "column": selected_metric_columns,
                    "missing_count": [
                        int(domain_frame[column].isna().sum())
                        for column in selected_metric_columns
                    ],
                    "rows": rows_total,
                }
            )
            if rows_total > 0:
                missingness["missing_pct"] = (
                    missingness["missing_count"] / rows_total
                ).round(6)
            else:
                missingness["missing_pct"] = 0.0
            missingness = missingness.sort_values(
                ["missing_pct", "column"],
                ascending=[False, True],
            ).reset_index(drop=True)
        else:
            rows_with_any_metric = 0
            missingness = pd.DataFrame(
                columns=["column", "missing_count", "rows", "missing_pct"]
            )

        fraction_rows_with_any_metric = (
            round(rows_with_any_metric / rows_total, 6) if rows_total > 0 else 0.0
        )

        report = {
            "station": {
                "station_id": context.station_id,
                "station_name": context.station_name,
            },
            "metadata": {
                "report_type": "domain_data_quality",
                "domain": domain_name,
                "generated_at_utc": context.run_date_utc,
                "data_access_date": context.access_date,
                "version": context.version,
            },
            "domain_summary": {
                "domain": domain_name,
                "rows_total": rows_total,
                "domain_columns_count": int(len(selected_columns)),
                "domain_metric_columns_count": int(len(selected_metric_columns)),
                "rows_with_any_domain_metric": rows_with_any_metric,
                "fraction_rows_with_any_domain_metric": fraction_rows_with_any_metric,
            },
            "domain_columns": selected_columns,
            "domain_metric_columns": selected_metric_columns,
            "citation": _citation_text(context),
        }
        reports[domain_name] = (report, missingness)

    return reports


def _aggregation_function_rows(cleaned: pd.DataFrame) -> list[dict[str, object]]:
    rows = []
    for col in cleaned.columns:
        if col in _TIME_COLUMNS or col in _ID_COLUMNS:
            continue
        rows.append(
            {
                "column": col,
                "aggregation": get_agg_func(col),
                "is_quality_column": bool(is_quality_column(col)),
            }
        )
    return sorted(rows, key=lambda row: row["column"])


def generate_aggregation_report(
    cleaned: pd.DataFrame,
    hourly: pd.DataFrame,
    monthly: pd.DataFrame,
    yearly: pd.DataFrame,
    context: ResearchReportContext,
    *,
    aggregation_strategy: str,
    fixed_hour: int | None,
    min_days_per_month: int,
    min_months_per_year: int,
) -> dict[str, object]:
    best_hour: int | None = None
    day_coverage_per_hour: list[dict[str, object]] = []
    if "Hour" in cleaned.columns and "Day" in cleaned.columns and not cleaned.empty:
        hour_counts = (
            cleaned.groupby("Hour")["Day"]
            .nunique()
            .sort_values(ascending=False)
        )
        day_coverage_per_hour = [
            {"hour": int(hour), "unique_days": int(count)}
            for hour, count in hour_counts.items()
        ]
        best_hour = _best_hour(cleaned)

    selected = hourly.copy()
    if {"Year", "MonthNum", "Day"}.issubset(selected.columns):
        after_months = _filter_full_months(selected, min_days=min_days_per_month)
        if {"Year", "MonthNum"}.issubset(after_months.columns):
            after_years = _filter_full_years(after_months, min_months=min_months_per_year)
        else:
            after_years = after_months.copy()
    else:
        after_months = selected.copy()
        after_years = selected.copy()

    agg_rows = _aggregation_function_rows(cleaned)
    dropped = [row["column"] for row in agg_rows if row["aggregation"] == "drop"]

    return {
        "station": {
            "station_id": context.station_id,
            "station_name": context.station_name,
        },
        "metadata": {
            "report_type": "aggregation_assumptions",
            "generated_at_utc": context.run_date_utc,
            "data_access_date": context.access_date,
            "version": context.version,
        },
        "strategy": {
            "name": aggregation_strategy,
            "best_hour_selected": best_hour if aggregation_strategy == "best_hour" else None,
            "fixed_hour_selected": fixed_hour if aggregation_strategy == "fixed_hour" else None,
            "day_coverage_per_hour": day_coverage_per_hour,
        },
        "completeness_filters": {
            "min_days_per_month": int(min_days_per_month),
            "min_months_per_year": int(min_months_per_year),
            "rows_before_filters": int(len(selected)),
            "rows_after_min_days_per_month": int(len(after_months)),
            "rows_after_min_months_per_year": int(len(after_years)),
            "rows_filtered_out": int(max(len(selected) - len(after_years), 0)),
        },
        "output_rows": {
            "cleaned": int(len(cleaned)),
            "hourly": int(len(hourly)),
            "monthly": int(len(monthly)),
            "yearly": int(len(yearly)),
        },
        "aggregation_functions": agg_rows,
        "dropped_columns": sorted(dropped),
        "citation": _citation_text(context),
    }


def _quality_report_markdown(report: dict[str, object], missingness: pd.DataFrame) -> str:
    row_counts = report["row_counts"]
    coverage = report["coverage_completeness"]
    missing_top = missingness.head(20)

    lines = [
        "# Location Data Quality Report",
        "",
        f"- Station ID: {report['station']['station_id']}",
        f"- Station Name: {report['station']['station_name']}",
        f"- Generated: {report['metadata']['generated_at_utc']}",
        f"- Data Access Date: {report['metadata']['data_access_date']}",
        "",
        "## Row Counts",
        "",
        f"- Raw rows: {row_counts['raw_rows']}",
        f"- Cleaned rows: {row_counts['cleaned_rows']}",
        f"- Dropped rows: {row_counts['dropped_rows']}",
        f"- Dropped fraction: {row_counts['dropped_fraction']:.4f}",
        "",
        "## Coverage Completeness",
        "",
        f"- Hours retained: {coverage['retained_fraction']['hours']:.4f}",
        f"- Days retained: {coverage['retained_fraction']['days']:.4f}",
        f"- Months retained: {coverage['retained_fraction']['months']:.4f}",
        "",
        "## Missingness (Top 20 Columns)",
        "",
        "| Column | Missing Count | Missing % |",
        "|---|---:|---:|",
    ]
    for _, row in missing_top.iterrows():
        lines.append(
            f"| {row['column']} | {int(row['missing_count'])} | {float(row['missing_pct']):.4f} |"
        )

    lines.extend(
        [
            "",
            "## Citation",
            "",
            report["citation"],
            "",
        ]
    )
    return "\n".join(lines)


def _aggregation_report_markdown(report: dict[str, object]) -> str:
    strategy = report["strategy"]
    completeness = report["completeness_filters"]

    lines = [
        "# Location Aggregation Assumptions Report",
        "",
        f"- Station ID: {report['station']['station_id']}",
        f"- Station Name: {report['station']['station_name']}",
        f"- Generated: {report['metadata']['generated_at_utc']}",
        f"- Strategy: {strategy['name']}",
        "",
        "## Strategy Parameters",
        "",
        f"- Best hour selected: {strategy['best_hour_selected']}",
        f"- Fixed hour selected: {strategy['fixed_hour_selected']}",
        "",
        "## Completeness Filters",
        "",
        f"- min_days_per_month: {completeness['min_days_per_month']}",
        f"- min_months_per_year: {completeness['min_months_per_year']}",
        f"- rows_before_filters: {completeness['rows_before_filters']}",
        f"- rows_after_min_days_per_month: {completeness['rows_after_min_days_per_month']}",
        f"- rows_after_min_months_per_year: {completeness['rows_after_min_months_per_year']}",
        "",
        "## Dropped Columns",
        "",
    ]
    if report["dropped_columns"]:
        lines.extend([f"- {col}" for col in report["dropped_columns"]])
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Citation",
            "",
            report["citation"],
            "",
        ]
    )
    return "\n".join(lines)


def _domain_quality_report_markdown(report: dict[str, object], missingness: pd.DataFrame) -> str:
    summary = report["domain_summary"]
    lines = [
        "# Domain Data Quality Report",
        "",
        f"- Station ID: {report['station']['station_id']}",
        f"- Station Name: {report['station']['station_name']}",
        f"- Domain: {report['metadata']['domain']}",
        f"- Generated: {report['metadata']['generated_at_utc']}",
        f"- Data Access Date: {report['metadata']['data_access_date']}",
        "",
        "## Domain Summary",
        "",
        f"- Rows total: {summary['rows_total']}",
        f"- Domain columns: {summary['domain_columns_count']}",
        f"- Domain metric columns: {summary['domain_metric_columns_count']}",
        f"- Rows with any domain metric: {summary['rows_with_any_domain_metric']}",
        (
            "- Fraction rows with any domain metric: "
            f"{summary['fraction_rows_with_any_domain_metric']:.4f}"
        ),
        "",
        "## Domain Missingness (Top 20 Metric Columns)",
        "",
        "| Column | Missing Count | Missing % |",
        "|---|---:|---:|",
    ]

    for _, row in missingness.head(20).iterrows():
        lines.append(
            f"| {row['column']} | {int(row['missing_count'])} | {float(row['missing_pct']):.4f} |"
        )

    lines.extend(
        [
            "",
            "## Citation",
            "",
            report["citation"],
            "",
        ]
    )
    return "\n".join(lines)


def write_research_reports(
    output_dir: Path,
    quality_report: dict[str, object],
    quality_summary: pd.DataFrame,
    aggregation_report: dict[str, object] | None = None,
    domain_quality_reports: dict[str, tuple[dict[str, object], pd.DataFrame]] | None = None,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    quality_json = output_dir / "LocationData_QualityReport.json"
    quality_md = output_dir / "LocationData_QualityReport.md"
    quality_csv = output_dir / "LocationData_QualitySummary.csv"

    quality_json.write_text(json.dumps(quality_report, indent=2, default=_json_default), encoding="utf-8")
    quality_md.write_text(_quality_report_markdown(quality_report, quality_summary), encoding="utf-8")
    quality_summary.to_csv(quality_csv, index=False)

    report_paths: dict[str, Path] = {
        "quality_json": quality_json,
        "quality_md": quality_md,
        "quality_csv": quality_csv,
    }

    if aggregation_report is not None:
        aggregation_json = output_dir / "LocationData_AggregationReport.json"
        aggregation_md = output_dir / "LocationData_AggregationReport.md"
        aggregation_json.write_text(
            json.dumps(aggregation_report, indent=2, default=_json_default),
            encoding="utf-8",
        )
        aggregation_md.write_text(_aggregation_report_markdown(aggregation_report), encoding="utf-8")
        report_paths["aggregation_json"] = aggregation_json
        report_paths["aggregation_md"] = aggregation_md

    if domain_quality_reports:
        domain_quality_dir = output_dir / "domain_quality"
        domain_quality_dir.mkdir(parents=True, exist_ok=True)
        for domain_name in sorted(domain_quality_reports.keys()):
            report, missingness = domain_quality_reports[domain_name]
            domain_json = domain_quality_dir / f"LocationData_DomainQuality_{domain_name}.json"
            domain_md = domain_quality_dir / f"LocationData_DomainQuality_{domain_name}.md"
            domain_json.write_text(
                json.dumps(report, indent=2, default=_json_default),
                encoding="utf-8",
            )
            domain_md.write_text(
                _domain_quality_report_markdown(report, missingness),
                encoding="utf-8",
            )
            report_paths[f"domain_quality_json_{domain_name}"] = domain_json
            report_paths[f"domain_quality_md_{domain_name}"] = domain_md

    return report_paths


def build_reports_for_station_dir(
    station_dir: Path,
    *,
    access_date: str | None = None,
    version: str = __version__,
    authors: str = "Balaji Kesavan",
) -> dict[str, Path]:
    raw_path = station_dir / "LocationData_Raw.csv"
    cleaned_path = station_dir / "LocationData_Cleaned.csv"

    required = [raw_path, cleaned_path]
    missing = [path for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "Missing required station files: " + ", ".join(str(path) for path in missing)
        )

    raw = pd.read_csv(raw_path, low_memory=False)
    cleaned = pd.read_csv(cleaned_path, low_memory=False)

    station_id = station_dir.name
    station_name = None
    if "station_name" in cleaned.columns and not cleaned["station_name"].dropna().empty:
        station_name = str(cleaned["station_name"].dropna().iloc[0])
    elif "NAME" in cleaned.columns and not cleaned["NAME"].dropna().empty:
        station_name = str(cleaned["NAME"].dropna().iloc[0])

    context = ResearchReportContext(
        station_id=station_id,
        station_name=station_name,
        access_date=access_date or _today_utc(),
        run_date_utc=_utc_now_iso(),
        version=version,
        authors=authors,
    )

    quality_report, quality_summary = generate_quality_report(raw, cleaned, context)
    domain_quality_reports = generate_domain_quality_reports(cleaned, context)
    return write_research_reports(
        station_dir,
        quality_report,
        quality_summary,
        aggregation_report=None,
        domain_quality_reports=domain_quality_reports,
    )