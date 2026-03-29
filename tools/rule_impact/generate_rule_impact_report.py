#!/usr/bin/env python3
"""Generate deterministic rule-impact artifacts for NOAA cleaning.

Outputs:
- docs/internal/reports/RULE_IMPACT_REPORT.md
- rule_impact_summary.csv
- rule_family_impact_summary.csv

The analysis is bounded to local station data under output/<station>/LocationData_Raw.csv.
No network access or data download is performed.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import logging
from pathlib import Path
import re
from typing import Iterable

import pandas as pd

from noaa_spec.cleaning import clean_noaa_dataframe
from noaa_spec.constants import get_expected_part_count

QC_REASON_SUFFIX = "__qc_reason"
FLAG_DOMAIN_PREFIX = "qc_domain_invalid_"
FLAG_PATTERN_PREFIX = "qc_pattern_mismatch_"
FLAG_ARITY_PREFIX = "qc_arity_mismatch_"
RULE_TYPE_TO_FAMILY = {
    "sentinel": "sentinel_handling",
    "allowed_quality": "quality_code_handling",
    "domain": "domain_validation",
    "range": "range_validation",
    "arity": "arity_validation",
    "width": "width_validation",
    "structural_guard": "structural_parser_guard",
}
FAMILY_ORDER = [
    "sentinel_handling",
    "quality_code_handling",
    "domain_validation",
    "range_validation",
    "pattern_validation",
    "arity_validation",
    "width_validation",
    "structural_parser_guard",
]


@dataclass(frozen=True)
class SampleConfig:
    station_limit: int
    rows_per_station: int


def _identifier_family(identifier: str) -> str:
    m = re.match(r"^([A-Z_]+?)(\d+)?$", identifier)
    if m:
        return m.group(1)
    return identifier


def _extract_identifier_from_qc_reason_column(column: str) -> str | None:
    if not column.endswith(QC_REASON_SUFFIX):
        return None
    stem = column[: -len(QC_REASON_SUFFIX)]
    if "__part" in stem:
        return stem.split("__part", 1)[0]
    if "__" in stem:
        return stem.split("__", 1)[0]
    return stem


def _extract_identifier_from_flag_column(column: str) -> str | None:
    for prefix in (FLAG_DOMAIN_PREFIX, FLAG_PATTERN_PREFIX, FLAG_ARITY_PREFIX):
        if column.startswith(prefix):
            return column[len(prefix) :]
    return None


def _load_station_sample(raw_csv: Path, station_id: str, rows_per_station: int) -> pd.DataFrame:
    frame = pd.read_csv(raw_csv, nrows=rows_per_station, low_memory=False)
    frame["__station_id"] = station_id
    return frame


def _find_station_dirs(output_root: Path) -> list[Path]:
    station_dirs: list[Path] = []
    for child in sorted(output_root.iterdir()):
        if not child.is_dir():
            continue
        if not re.fullmatch(r"\d{11}", child.name):
            continue
        raw_csv = child / "LocationData_Raw.csv"
        if raw_csv.exists():
            station_dirs.append(child)
    return station_dirs


def _build_sample(output_root: Path, config: SampleConfig) -> tuple[pd.DataFrame, list[tuple[str, int]]]:
    stations = _find_station_dirs(output_root)
    selected = stations[: config.station_limit]
    if not selected:
        raise FileNotFoundError(f"No station raw files found under {output_root}")

    sample_frames: list[pd.DataFrame] = []
    sample_meta: list[tuple[str, int]] = []

    for station_dir in selected:
        raw_csv = station_dir / "LocationData_Raw.csv"
        sample = _load_station_sample(raw_csv, station_dir.name, config.rows_per_station)
        sample_frames.append(sample)
        sample_meta.append((station_dir.name, int(len(sample))))

    combined = pd.concat(sample_frames, ignore_index=True, sort=False)
    return combined, sample_meta


def _count_arity_mismatches(raw_df: pd.DataFrame) -> tuple[dict[str, int], dict[str, int]]:
    mismatch_counts: dict[str, int] = {}
    evaluated_counts: dict[str, int] = {}
    for column in sorted(raw_df.columns):
        if column.startswith("__"):
            continue
        expected = get_expected_part_count(column)
        if expected is None:
            continue
        series = raw_df[column]
        if series.empty:
            continue
        text = series.astype("string")
        present_mask = text.notna() & text.str.strip().ne("")
        if not present_mask.any():
            continue
        evaluated_counts[column] = int(present_mask.sum())
        present = text[present_mask]
        part_counts = present.str.count(",") + 1
        mismatch = int((part_counts != expected).sum())
        if mismatch:
            mismatch_counts[column] = mismatch
    return mismatch_counts, evaluated_counts


def _collect_qc_reason_counts(df: pd.DataFrame) -> tuple[dict[str, dict[str, int]], dict[str, int]]:
    by_identifier: dict[str, dict[str, int]] = {}
    by_field_reason: dict[str, int] = {}
    qc_cols = sorted(col for col in df.columns if col.endswith(QC_REASON_SUFFIX))

    for column in qc_cols:
        identifier = _extract_identifier_from_qc_reason_column(column)
        if identifier is None:
            continue
        value_counts = df[column].dropna().astype(str).value_counts()
        if value_counts.empty:
            continue
        if identifier not in by_identifier:
            by_identifier[identifier] = {}
        for reason, count in value_counts.items():
            by_identifier[identifier][reason] = by_identifier[identifier].get(reason, 0) + int(count)
            by_field_reason[f"{column}|{reason}"] = int(count)

    return by_identifier, by_field_reason


def _collect_flag_counts(df: pd.DataFrame) -> dict[str, int]:
    counts: dict[str, int] = {}
    flag_cols = sorted(
        col
        for col in df.columns
        if col.startswith((FLAG_DOMAIN_PREFIX, FLAG_PATTERN_PREFIX, FLAG_ARITY_PREFIX))
    )
    for col in flag_cols:
        true_count = int(df[col].fillna(False).astype(bool).sum())
        if true_count:
            counts[col] = true_count
    return counts


def _value_columns_for_stage(df: pd.DataFrame, raw_columns: set[str]) -> list[str]:
    cols: list[str] = []
    for col in sorted(df.columns):
        if col in raw_columns or col.startswith("__"):
            continue
        if col.startswith("qc_"):
            continue
        if col.endswith("__quality"):
            continue
        if col.endswith("__qc_pass") or col.endswith("__qc_status") or col.endswith("__qc_reason"):
            continue
        cols.append(col)
    return cols


def _field_null_stats(df: pd.DataFrame, stage: str, raw_columns: set[str]) -> list[dict[str, object]]:
    stats: list[dict[str, object]] = []
    total_rows = len(df)
    for col in _value_columns_for_stage(df, raw_columns):
        null_count = int(df[col].isna().sum())
        stats.append(
            {
                "level": "field",
                "stage": stage,
                "identifier": col,
                "identifier_family": "",
                "metric": "null_rate",
                "count": null_count,
                "denominator": total_rows,
                "rate": (null_count / total_rows) if total_rows else 0.0,
            }
        )
    return stats


def _compare_minimal_vs_canonical(
    minimal_df: pd.DataFrame,
    canonical_df: pd.DataFrame,
    raw_columns: set[str],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    fields = _value_columns_for_stage(canonical_df, raw_columns)
    for col in fields:
        if col not in minimal_df.columns:
            continue
        min_non_null = minimal_df[col].notna()
        denominator = int(min_non_null.sum())
        newly_null = int((min_non_null & canonical_df[col].isna()).sum())
        rows.append(
            {
                "level": "field",
                "stage": "minimal_vs_canonical",
                "identifier": col,
                "identifier_family": "",
                "metric": "newly_null_from_strict_cleaning",
                "count": newly_null,
                "denominator": denominator,
                "rate": (newly_null / denominator) if denominator else 0.0,
            }
        )
    return rows


def _identifier_qc_summary(
    qc_reasons_by_identifier: dict[str, dict[str, int]],
    flag_counts: dict[str, int],
    total_rows: int,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    identifier_counts: dict[str, int] = {}

    for identifier, reason_counts in qc_reasons_by_identifier.items():
        identifier_counts[identifier] = identifier_counts.get(identifier, 0) + int(sum(reason_counts.values()))

    for flag_col, count in flag_counts.items():
        identifier = _extract_identifier_from_flag_column(flag_col)
        if identifier is None:
            continue
        identifier_counts[identifier] = identifier_counts.get(identifier, 0) + int(count)

    id_rows: list[dict[str, object]] = []
    family_counts: dict[str, int] = {}

    for identifier in sorted(identifier_counts):
        count = int(identifier_counts[identifier])
        family = _identifier_family(identifier)
        family_counts[family] = family_counts.get(family, 0) + count
        id_rows.append(
            {
                "level": "identifier",
                "stage": "canonical_qc",
                "identifier": identifier,
                "identifier_family": family,
                "metric": "qc_trigger_count",
                "count": count,
                "denominator": total_rows,
                "rate": (count / total_rows) if total_rows else 0.0,
            }
        )

    family_rows: list[dict[str, object]] = []
    for family in sorted(family_counts):
        count = int(family_counts[family])
        family_rows.append(
            {
                "level": "identifier_family",
                "stage": "canonical_qc",
                "identifier": "",
                "identifier_family": family,
                "metric": "qc_trigger_count",
                "count": count,
                "denominator": total_rows,
                "rate": (count / total_rows) if total_rows else 0.0,
            }
        )

    return id_rows, family_rows


def _read_flag_only_identifiers(review_csv: Path) -> set[str]:
    if not review_csv.exists():
        return set()
    review = pd.read_csv(review_csv)
    if "recommended_action" not in review.columns or "field_identifier" not in review.columns:
        return set()
    flagged = review[review["recommended_action"].astype(str) == "weaken_to_flag_only"]
    return set(flagged["field_identifier"].dropna().astype(str).tolist())


def _read_provenance_family_map(ledger_csv: Path) -> dict[str, set[str]]:
    if not ledger_csv.exists():
        return {}
    ledger = pd.read_csv(ledger_csv)
    required = {"field_identifier", "rule_type"}
    if not required.issubset(ledger.columns):
        return {}
    work = ledger[list(required)].dropna().copy()
    work["field_identifier"] = work["field_identifier"].astype(str)
    work["rule_type"] = work["rule_type"].astype(str)
    mapping: dict[str, set[str]] = {}
    for row in work.itertuples(index=False):
        family = RULE_TYPE_TO_FAMILY.get(row.rule_type)
        if family is None:
            continue
        mapping.setdefault(row.field_identifier, set()).add(family)
    return mapping


def _family_from_qc_reason(reason: str) -> str | None:
    if reason == "SENTINEL_MISSING":
        return "sentinel_handling"
    if reason == "BAD_QUALITY_CODE":
        return "quality_code_handling"
    if reason == "OUT_OF_RANGE":
        return "range_validation"
    if reason == "MALFORMED_TOKEN":
        return "width_validation"
    return None


def _build_rule_family_impact_summary(
    *,
    qc_reason_field_counts: dict[str, int],
    flag_counts: dict[str, int],
    arity_mismatch_counts: dict[str, int],
    arity_evaluated_counts: dict[str, int],
    parse_error_total: int,
    total_rows: int,
    qc_reason_column_count: int,
    flag_column_count: int,
    has_parse_error_column: bool,
    provenance_family_map: dict[str, set[str]],
) -> list[dict[str, object]]:
    affected = {family: 0 for family in FAMILY_ORDER}

    for key, count in qc_reason_field_counts.items():
        column, reason = key.split("|", 1)
        family = _family_from_qc_reason(reason)
        if family is None:
            continue
        identifier = _extract_identifier_from_qc_reason_column(column)
        if identifier is not None:
            _ = provenance_family_map.get(identifier, set())
        affected[family] += int(count)

    for flag_col, count in flag_counts.items():
        if flag_col.startswith(FLAG_DOMAIN_PREFIX):
            family = "domain_validation"
        elif flag_col.startswith(FLAG_PATTERN_PREFIX):
            family = "pattern_validation"
        elif flag_col.startswith(FLAG_ARITY_PREFIX):
            family = "arity_validation"
        else:
            continue
        identifier = _extract_identifier_from_flag_column(flag_col)
        if identifier is not None:
            _ = provenance_family_map.get(identifier, set())
        affected[family] += int(count)

    affected["arity_validation"] += int(sum(arity_mismatch_counts.values()))
    affected["structural_parser_guard"] += int(parse_error_total)

    total_cells = (
        int(qc_reason_column_count * total_rows)
        + int(flag_column_count * total_rows)
        + int(sum(arity_evaluated_counts.values()))
        + (int(total_rows) if has_parse_error_column else 0)
    )
    total_impacts = int(sum(affected.values()))

    rows: list[dict[str, object]] = []
    for family in FAMILY_ORDER:
        cells = int(affected[family])
        rows.append(
            {
                "rule_family": family,
                "cells_affected": cells,
                "fraction_of_total_cells": (cells / total_cells) if total_cells else 0.0,
                "fraction_of_total_impacts": (cells / total_impacts) if total_impacts else 0.0,
            }
        )
    return rows


def _top_rows(rows: Iterable[dict[str, object]], *, metric: str, limit: int) -> list[dict[str, object]]:
    filtered = [row for row in rows if str(row.get("metric")) == metric]
    filtered.sort(key=lambda row: (float(row.get("rate", 0.0)), int(row.get("count", 0))), reverse=True)
    return filtered[:limit]


def _to_markdown_table(rows: list[dict[str, object]], columns: list[str]) -> str:
    header = "| " + " | ".join(columns) + " |"
    sep = "|" + "|".join(["---"] * len(columns)) + "|"
    body = []
    for row in rows:
        values = []
        for col in columns:
            value = row.get(col, "")
            if isinstance(value, float):
                values.append(f"{value:.6f}")
            else:
                values.append(str(value))
        body.append("| " + " | ".join(values) + " |")
    return "\n".join([header, sep] + body) if body else "(none)"


def _write_summary_csv(path: Path, rows: list[dict[str, object]]) -> None:
    ordered = sorted(
        rows,
        key=lambda r: (
            str(r.get("level", "")),
            str(r.get("stage", "")),
            str(r.get("metric", "")),
            str(r.get("identifier_family", "")),
            str(r.get("identifier", "")),
        ),
    )
    fieldnames = [
        "level",
        "stage",
        "identifier",
        "identifier_family",
        "metric",
        "count",
        "denominator",
        "rate",
    ]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in ordered:
            out = {key: row.get(key, "") for key in fieldnames}
            rate = out["rate"]
            if isinstance(rate, float):
                out["rate"] = f"{rate:.8f}"
            writer.writerow(out)


def _write_rule_family_csv(path: Path, rows: list[dict[str, object]]) -> None:
    ordered = sorted(rows, key=lambda r: FAMILY_ORDER.index(str(r["rule_family"])))
    fieldnames = [
        "rule_family",
        "cells_affected",
        "fraction_of_total_cells",
        "fraction_of_total_impacts",
    ]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in ordered:
            out = {key: row.get(key, "") for key in fieldnames}
            for key in ("fraction_of_total_cells", "fraction_of_total_impacts"):
                value = out[key]
                if isinstance(value, float):
                    out[key] = f"{value:.8f}"
            writer.writerow(out)


def _write_report(
    report_path: Path,
    *,
    sample_meta: list[tuple[str, int]],
    total_rows: int,
    row_excluded: int,
    structural_count: int,
    spec_count: int,
    flag_only_count: int,
    altered_row_fraction: float,
    altered_field_fraction: float,
    top_nullified_fields: list[dict[str, object]],
    top_qc_identifiers: list[dict[str, object]],
    stage_rows: list[dict[str, object]],
    rule_family_rows: list[dict[str, object]],
) -> None:
    stage_table = _to_markdown_table(
        stage_rows,
        ["stage", "rows_processed", "rows_retained", "rows_excluded"],
    )
    station_rows = [
        {"station_id": station, "sample_rows": rows}
        for station, rows in sample_meta
    ]
    station_table = _to_markdown_table(station_rows, ["station_id", "sample_rows"])

    impact_rows = [
        {
            "bucket": "structural_parser_integrity",
            "count": structural_count,
            "rate_vs_rows": (structural_count / total_rows) if total_rows else 0.0,
        },
        {
            "bucket": "spec_supported_cleaning",
            "count": spec_count,
            "rate_vs_rows": (spec_count / total_rows) if total_rows else 0.0,
        },
        {
            "bucket": "stricter_or_flag_only",
            "count": flag_only_count,
            "rate_vs_rows": (flag_only_count / total_rows) if total_rows else 0.0,
        },
    ]

    null_table = _to_markdown_table(
        top_nullified_fields,
        ["identifier", "count", "denominator", "rate"],
    )
    qc_table = _to_markdown_table(
        top_qc_identifiers,
        ["identifier", "count", "denominator", "rate"],
    )
    impact_table = _to_markdown_table(impact_rows, ["bucket", "count", "rate_vs_rows"])
    rule_family_table = _to_markdown_table(
        rule_family_rows,
        [
            "rule_family",
            "cells_affected",
            "fraction_of_total_cells",
            "fraction_of_total_impacts",
        ],
    )

    lines = [
        "# RULE_IMPACT_REPORT",
        "",
        "## Sample Description",
        "",
        "Representative bounded sample from local station raw files under `output/<station>/LocationData_Raw.csv`.",
        "No remote data was fetched.",
        "",
        station_table,
        "",
        f"Total sampled rows: **{total_rows}**",
        "",
        "## Methodology",
        "",
        "1. Read deterministic station sample in sorted station-id order with fixed row cap per station.",
        "2. Build staged views on the same sampled rows:",
        "   - raw input",
        "   - parsed/minimally normalized (`clean_noaa_dataframe(..., strict_mode=False)`)",
        "   - canonical cleaned (`clean_noaa_dataframe(..., strict_mode=True)`)",
        "   - QC-flag summaries from canonical outputs",
        "3. Compute row retention/exclusion, field null rates, QC reason counts, and identifier/family trigger rates.",
        "4. Bucket impacts into structural parser effects, spec-supported cleaning effects, and stricter/flag-only effects.",
        "",
        "## Overall Row/Field Impact Summary",
        "",
        stage_table,
        "",
        f"Rows excluded in canonical stage: **{row_excluded}**",
        f"Rows with any cleaning/QC impact signal: **{altered_row_fraction:.6f}**",
        f"Field-cell impacts (signals over evaluated cells): **{altered_field_fraction:.6f}**",
        "",
        "## Top Fields With Highest Nullification Rates",
        "",
        null_table,
        "",
        "## Top Identifiers With Highest QC-Flag Rates",
        "",
        qc_table,
        "",
        "## Impact Buckets",
        "",
        impact_table,
        "",
        "## Rule Family Impact Summary",
        "",
        rule_family_table,
        "",
        "## Interpretation",
        "",
        "- What changes most: fields/identifiers listed above with highest strict-cleaning nullification and QC trigger rates.",
        "- What changes little: fields with near-zero newly-null rates and low QC trigger counts in `rule_impact_summary.csv`.",
        "- Conservativeness vs destructiveness: compare `altered_row_fraction`, `altered_field_fraction`, and bucket magnitudes; this report provides empirical counts only.",
        "",
        "## Notes",
        "",
        "- `width/structure` counts are reported from parse/QC signals when available in sampled data.",
        "- This artifact quantifies cleaning-rule impact; it does not rate NOAA data quality.",
    ]

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def generate(
    *,
    repo_root: Path,
    station_limit: int,
    rows_per_station: int,
    report_path: Path,
    summary_csv_path: Path,
    rule_family_csv_path: Path,
) -> None:
    # Keep reruns fast and deterministic without emitting per-token strict warnings.
    logging.getLogger("noaa_spec.cleaning").setLevel(logging.ERROR)

    output_root = repo_root / "output"
    raw_sample, sample_meta = _build_sample(
        output_root,
        SampleConfig(station_limit=station_limit, rows_per_station=rows_per_station),
    )

    minimal = clean_noaa_dataframe(raw_sample.copy(), keep_raw=True, strict_mode=False)
    canonical = clean_noaa_dataframe(raw_sample.copy(), keep_raw=True, strict_mode=True)

    total_rows = len(raw_sample)
    raw_columns = set(raw_sample.columns)

    arity_mismatch_counts, arity_evaluated_counts = _count_arity_mismatches(raw_sample)
    qc_reasons_by_identifier, qc_reason_field_counts = _collect_qc_reason_counts(canonical)
    flag_counts = _collect_flag_counts(canonical)

    strict_vs_minimal_rows = _compare_minimal_vs_canonical(minimal, canonical, raw_columns)
    canonical_null_rows = _field_null_stats(canonical, "canonical", raw_columns)
    minimal_null_rows = _field_null_stats(minimal, "minimal", raw_columns)

    id_rows, family_rows = _identifier_qc_summary(qc_reasons_by_identifier, flag_counts, total_rows)

    reason_totals: dict[str, int] = {}
    for reason_map in qc_reasons_by_identifier.values():
        for reason, count in reason_map.items():
            reason_totals[reason] = reason_totals.get(reason, 0) + int(count)

    parse_error_total = int(canonical["__parse_error"].notna().sum()) if "__parse_error" in canonical.columns else 0
    malformed_total = int(reason_totals.get("MALFORMED_TOKEN", 0))
    sentinel_total = int(reason_totals.get("SENTINEL_MISSING", 0))
    quality_total = int(reason_totals.get("BAD_QUALITY_CODE", 0))
    range_total = int(reason_totals.get("OUT_OF_RANGE", 0))

    arity_total = int(sum(arity_mismatch_counts.values()))

    review_csv = repo_root / "undocumented_rules_review.csv"
    flag_only_identifiers = _read_flag_only_identifiers(review_csv)
    provenance_csv = repo_root / "RULE_PROVENANCE_LEDGER.csv"
    provenance_family_map = _read_provenance_family_map(provenance_csv)

    flag_only_total = 0
    for flag_col, count in flag_counts.items():
        ident = _extract_identifier_from_flag_column(flag_col)
        if ident in flag_only_identifiers:
            flag_only_total += int(count)

    structural_count = parse_error_total + malformed_total + arity_total
    spec_count = sentinel_total + quality_total + range_total

    all_qc_signal_count = int(sum(reason_totals.values()) + sum(flag_counts.values()) + parse_error_total)
    evaluated_cells = int(len([c for c in canonical.columns if c.endswith(QC_REASON_SUFFIX)]) * total_rows)
    altered_field_fraction = (all_qc_signal_count / evaluated_cells) if evaluated_cells else 0.0

    qc_reason_cols = [c for c in canonical.columns if c.endswith(QC_REASON_SUFFIX)]
    flag_cols = [c for c in canonical.columns if c.startswith("qc_")]
    row_impacted = pd.Series(False, index=canonical.index)
    if qc_reason_cols:
        row_impacted = row_impacted | canonical[qc_reason_cols].notna().any(axis=1)
    if flag_cols:
        row_impacted = row_impacted | canonical[flag_cols].fillna(False).astype(bool).any(axis=1)
    if "__parse_error" in canonical.columns:
        row_impacted = row_impacted | canonical["__parse_error"].notna()
    altered_row_fraction = float(row_impacted.mean()) if len(row_impacted) else 0.0

    stage_rows = [
        {
            "stage": "raw_input",
            "rows_processed": total_rows,
            "rows_retained": total_rows,
            "rows_excluded": 0,
        },
        {
            "stage": "parsed_minimal",
            "rows_processed": total_rows,
            "rows_retained": int(len(minimal)),
            "rows_excluded": int(total_rows - len(minimal)),
        },
        {
            "stage": "cleaned_canonical",
            "rows_processed": total_rows,
            "rows_retained": int(len(canonical)),
            "rows_excluded": int(total_rows - len(canonical)),
        },
    ]

    summary_rows: list[dict[str, object]] = []
    summary_rows.extend(minimal_null_rows)
    summary_rows.extend(canonical_null_rows)
    summary_rows.extend(strict_vs_minimal_rows)
    summary_rows.extend(id_rows)
    summary_rows.extend(family_rows)

    for identifier in sorted(arity_mismatch_counts):
        count = int(arity_mismatch_counts[identifier])
        summary_rows.append(
            {
                "level": "identifier",
                "stage": "raw_input",
                "identifier": identifier,
                "identifier_family": _identifier_family(identifier),
                "metric": "arity_mismatch_count",
                "count": count,
                "denominator": total_rows,
                "rate": (count / total_rows) if total_rows else 0.0,
            }
        )

    for key in sorted(qc_reason_field_counts):
        column, reason = key.split("|", 1)
        summary_rows.append(
            {
                "level": "field",
                "stage": "canonical_qc",
                "identifier": column,
                "identifier_family": _identifier_family(_extract_identifier_from_qc_reason_column(column) or column),
                "metric": f"qc_reason::{reason}",
                "count": int(qc_reason_field_counts[key]),
                "denominator": total_rows,
                "rate": (int(qc_reason_field_counts[key]) / total_rows) if total_rows else 0.0,
            }
        )

    for flag_col in sorted(flag_counts):
        ident = _extract_identifier_from_flag_column(flag_col) or flag_col
        summary_rows.append(
            {
                "level": "identifier",
                "stage": "canonical_qc",
                "identifier": ident,
                "identifier_family": _identifier_family(ident),
                "metric": f"flag::{flag_col}",
                "count": int(flag_counts[flag_col]),
                "denominator": total_rows,
                "rate": (int(flag_counts[flag_col]) / total_rows) if total_rows else 0.0,
            }
        )

    summary_rows.extend(
        [
            {
                "level": "overall",
                "stage": "raw_input",
                "identifier": "",
                "identifier_family": "",
                "metric": "rows_processed",
                "count": total_rows,
                "denominator": total_rows,
                "rate": 1.0 if total_rows else 0.0,
            },
            {
                "level": "overall",
                "stage": "cleaned_canonical",
                "identifier": "",
                "identifier_family": "",
                "metric": "rows_retained",
                "count": int(len(canonical)),
                "denominator": total_rows,
                "rate": (int(len(canonical)) / total_rows) if total_rows else 0.0,
            },
            {
                "level": "overall",
                "stage": "cleaned_canonical",
                "identifier": "",
                "identifier_family": "",
                "metric": "rows_excluded",
                "count": int(total_rows - len(canonical)),
                "denominator": total_rows,
                "rate": (int(total_rows - len(canonical)) / total_rows) if total_rows else 0.0,
            },
            {
                "level": "overall",
                "stage": "canonical_qc",
                "identifier": "",
                "identifier_family": "",
                "metric": "malformed_token_count",
                "count": malformed_total,
                "denominator": total_rows,
                "rate": (malformed_total / total_rows) if total_rows else 0.0,
            },
            {
                "level": "overall",
                "stage": "canonical_qc",
                "identifier": "",
                "identifier_family": "",
                "metric": "parse_structure_error_count",
                "count": parse_error_total,
                "denominator": total_rows,
                "rate": (parse_error_total / total_rows) if total_rows else 0.0,
            },
            {
                "level": "overall",
                "stage": "canonical_qc",
                "identifier": "",
                "identifier_family": "",
                "metric": "sentinel_to_null_count",
                "count": sentinel_total,
                "denominator": total_rows,
                "rate": (sentinel_total / total_rows) if total_rows else 0.0,
            },
            {
                "level": "overall",
                "stage": "canonical_qc",
                "identifier": "",
                "identifier_family": "",
                "metric": "bad_quality_code_count",
                "count": quality_total,
                "denominator": total_rows,
                "rate": (quality_total / total_rows) if total_rows else 0.0,
            },
            {
                "level": "overall",
                "stage": "canonical_qc",
                "identifier": "",
                "identifier_family": "",
                "metric": "out_of_range_count",
                "count": range_total,
                "denominator": total_rows,
                "rate": (range_total / total_rows) if total_rows else 0.0,
            },
            {
                "level": "overall",
                "stage": "canonical_qc",
                "identifier": "",
                "identifier_family": "",
                "metric": "bucket::structural_parser_integrity",
                "count": structural_count,
                "denominator": total_rows,
                "rate": (structural_count / total_rows) if total_rows else 0.0,
            },
            {
                "level": "overall",
                "stage": "canonical_qc",
                "identifier": "",
                "identifier_family": "",
                "metric": "bucket::spec_supported_cleaning",
                "count": spec_count,
                "denominator": total_rows,
                "rate": (spec_count / total_rows) if total_rows else 0.0,
            },
            {
                "level": "overall",
                "stage": "canonical_qc",
                "identifier": "",
                "identifier_family": "",
                "metric": "bucket::stricter_or_flag_only",
                "count": flag_only_total,
                "denominator": total_rows,
                "rate": (flag_only_total / total_rows) if total_rows else 0.0,
            },
            {
                "level": "overall",
                "stage": "canonical_qc",
                "identifier": "",
                "identifier_family": "",
                "metric": "rows_with_any_impact_fraction",
                "count": int(row_impacted.sum()),
                "denominator": total_rows,
                "rate": altered_row_fraction,
            },
            {
                "level": "overall",
                "stage": "canonical_qc",
                "identifier": "",
                "identifier_family": "",
                "metric": "field_cell_impact_fraction",
                "count": all_qc_signal_count,
                "denominator": evaluated_cells,
                "rate": altered_field_fraction,
            },
        ]
    )

    _write_summary_csv(summary_csv_path, summary_rows)

    rule_family_rows = _build_rule_family_impact_summary(
        qc_reason_field_counts=qc_reason_field_counts,
        flag_counts=flag_counts,
        arity_mismatch_counts=arity_mismatch_counts,
        arity_evaluated_counts=arity_evaluated_counts,
        parse_error_total=parse_error_total,
        total_rows=total_rows,
        qc_reason_column_count=len(qc_reason_cols),
        flag_column_count=len(flag_cols),
        has_parse_error_column="__parse_error" in canonical.columns,
        provenance_family_map=provenance_family_map,
    )
    _write_rule_family_csv(rule_family_csv_path, rule_family_rows)

    top_nullified = _top_rows(
        canonical_null_rows,
        metric="null_rate",
        limit=15,
    )
    top_qc_identifiers = _top_rows(
        id_rows,
        metric="qc_trigger_count",
        limit=15,
    )

    _write_report(
        report_path,
        sample_meta=sample_meta,
        total_rows=total_rows,
        row_excluded=int(total_rows - len(canonical)),
        structural_count=structural_count,
        spec_count=spec_count,
        flag_only_count=flag_only_total,
        altered_row_fraction=altered_row_fraction,
        altered_field_fraction=altered_field_fraction,
        top_nullified_fields=top_nullified,
        top_qc_identifiers=top_qc_identifiers,
        stage_rows=stage_rows,
        rule_family_rows=rule_family_rows,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root path.",
    )
    parser.add_argument(
        "--station-limit",
        type=int,
        default=4,
        help="Number of station directories to sample in sorted order.",
    )
    parser.add_argument(
        "--rows-per-station",
        type=int,
        default=1500,
        help="Row cap per sampled station file.",
    )
    parser.add_argument(
        "--report-path",
        type=Path,
        default=Path("docs/internal/reports/RULE_IMPACT_REPORT.md"),
        help="Markdown report output path.",
    )
    parser.add_argument(
        "--summary-csv",
        type=Path,
        default=Path("rule_impact_summary.csv"),
        help="CSV summary output path.",
    )
    parser.add_argument(
        "--rule-family-csv",
        type=Path,
        default=Path("rule_family_impact_summary.csv"),
        help="Rule-family impact CSV output path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.report_path.parent.mkdir(parents=True, exist_ok=True)
    generate(
        repo_root=args.repo_root,
        station_limit=args.station_limit,
        rows_per_station=args.rows_per_station,
        report_path=args.report_path,
        summary_csv_path=args.summary_csv,
        rule_family_csv_path=args.rule_family_csv,
    )


if __name__ == "__main__":
    main()
