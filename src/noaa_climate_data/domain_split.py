"""Domain split utilities for cleaned station outputs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

import pandas as pd


@dataclass(frozen=True)
class DomainRule:
    keywords: tuple[str, ...]
    prefixes: tuple[str, ...]


COMMON_COLUMNS = (
    "station_id",
    "STATION",
    "DATE",
    "YEAR",
    "SOURCE",
    "NAME",
    "REPORT_TYPE",
    "CALL_SIGN",
    "QUALITY_CONTROL",
    "Year",
    "MonthNum",
    "MonthName",
    "Day",
    "Hour",
    "row_has_any_usable_metric",
    "usable_metric_count",
    "usable_metric_fraction",
)


MAPPING_COLUMNS = (
    "station_id",
    "station_slug",
    "station_name",
    "LATITUDE",
    "LONGITUDE",
    "ELEVATION",
)


DOMAIN_RULES: tuple[tuple[str, DomainRule], ...] = (
    (
        "temperature",
        DomainRule(
            keywords=(
                "temperature",
                "extreme_temp",
                "temp_c",
                "heat_index",
                "wind_chill",
            ),
            prefixes=(
                "TMP",
                "KA",
                "KB",
                "KC",
                "KD",
                "KE",
                "KF",
                "KG",
                "KH",
                "KI",
                "KJ",
                "KK",
                "KL",
                "KM",
                "KN",
                "KO",
                "KP",
                "KQ",
                "KR",
                "KS",
                "KT",
                "KU",
                "KV",
                "CW",
                "CT",
                "CU",
                "CV",
                "CX",
            ),
        ),
    ),
    (
        "dew_point",
        DomainRule(
            keywords=("dew_point", "dew_"),
            prefixes=("DEW",),
        ),
    ),
    (
        "wind",
        DomainRule(
            keywords=(
                "wind_",
                "windspeed",
                "wind_speed",
                "wind_direction",
                "wind_type",
                "gust",
            ),
            prefixes=("WND", "OA", "OB", "OC", "OD", "OE"),
        ),
    ),
    (
        "pressure",
        DomainRule(
            keywords=("pressure", "altimeter", "barometer"),
            prefixes=("SLP", "MA", "MD", "MF", "MG", "MH"),
        ),
    ),
    (
        "visibility_ceiling",
        DomainRule(
            keywords=("visibility", "ceiling", "cavok"),
            prefixes=("VIS", "CIG"),
        ),
    ),
    (
        "precipitation",
        DomainRule(
            keywords=("precip", "rain", "snow", "drizzle", "hail", "liquid"),
            prefixes=(
                "AA",
                "AB",
                "AC",
                "AD",
                "AE",
                "AF",
                "AG",
                "AH",
                "AI",
                "AJ",
                "AK",
                "AL",
                "AM",
                "AN",
                "AO",
                "AP",
                "AQ",
                "AR",
                "AS",
            ),
        ),
    ),
    (
        "cloud_solar",
        DomainRule(
            keywords=("cloud", "sky_cover", "solar", "sun", "irradiance", "radiation"),
            prefixes=(
                "GA",
                "GD",
                "GE",
                "GF",
                "GG",
                "GH",
                "GJ",
                "GK",
                "GL",
                "GM",
                "GN",
                "GO",
                "GP",
                "GQ",
                "GR",
                "GS",
                "GT",
                "GU",
                "GV",
                "GW",
                "GX",
                "GY",
                "GZ",
            ),
        ),
    ),
    (
        "weather_occurrence",
        DomainRule(
            keywords=("weather", "thunder", "lightning", "storm", "tornado", "funnel"),
            prefixes=("AY", "AZ", "AW", "MW"),
        ),
    ),
)


def sanitize_station_slug(name: str) -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "_", str(name).strip())
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "UNKNOWN_STATION"


def _column_matches_rule(column_name: str, rule: DomainRule) -> bool:
    lowered = column_name.lower()
    uppered = column_name.upper()
    if any(keyword in lowered for keyword in rule.keywords):
        return True
    if any(uppered.startswith(prefix) for prefix in rule.prefixes):
        return True
    return False


def classify_columns(columns: list[str]) -> tuple[list[str], dict[str, list[str]]]:
    common = [col for col in COMMON_COLUMNS if col in columns]
    domain_columns: dict[str, list[str]] = {name: [] for name, _ in DOMAIN_RULES}
    assigned: set[str] = set()

    for column in columns:
        if column in common:
            continue
        for domain_name, domain_rule in DOMAIN_RULES:
            if _column_matches_rule(column, domain_rule):
                domain_columns[domain_name].append(column)
                assigned.add(column)
                break

    other_columns = [col for col in columns if col not in assigned and col not in common]
    domain_columns["other"] = other_columns
    return common, domain_columns


def split_station_cleaned_by_domain(
    cleaned: pd.DataFrame,
    *,
    station_slug: str,
    station_name: str,
    output_dir: Path,
    include_other: bool = True,
) -> list[dict[str, object]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    columns = list(cleaned.columns)
    common_columns, domain_columns = classify_columns(columns)

    if not include_other:
        domain_columns.pop("other", None)

    manifest_rows: list[dict[str, object]] = []
    for domain_name, cols in domain_columns.items():
        if not cols:
            continue
        selected = common_columns + cols
        output_file = output_dir / f"{station_slug}__{domain_name}.csv"
        cleaned[selected].to_csv(output_file, index=False)
        size_mb = output_file.stat().st_size / (1024 * 1024)
        manifest_rows.append(
            {
                "station_name": station_name,
                "domain": domain_name,
                "rows": int(len(cleaned)),
                "columns": int(len(selected)),
                "file": str(output_file),
                "size_mb": round(size_mb, 2),
            }
        )
    return manifest_rows


def station_metadata_mapping_row(
    cleaned: pd.DataFrame,
    *,
    station_slug: str,
    station_name: str,
    station_id_fallback: str,
) -> dict[str, object]:
    row: dict[str, object] = {
        "station_id": station_id_fallback,
        "station_slug": station_slug,
        "station_name": station_name,
        "LATITUDE": None,
        "LONGITUDE": None,
        "ELEVATION": None,
    }

    if "station_id" in cleaned.columns and not cleaned["station_id"].dropna().empty:
        row["station_id"] = str(cleaned["station_id"].dropna().iloc[0])

    for column in ("LATITUDE", "LONGITUDE", "ELEVATION"):
        if column in cleaned.columns and not cleaned[column].dropna().empty:
            row[column] = cleaned[column].dropna().iloc[0]

    return row
