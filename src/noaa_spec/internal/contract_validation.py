"""Validation helpers that enforce publication contract requirements."""

from __future__ import annotations

from typing import Any

import pandas as pd

from ..constants import FIELD_RULES, to_internal_column
from ..contracts import CANONICAL_CORE_COLUMN_TYPES, CANONICAL_DATASET_CONTRACT


_SENTINEL_TOLERANCE = 1e-6


def sentinel_values_for_column(column_name: str) -> set[float]:
    internal = to_internal_column(column_name)
    parts = internal.split("__", 1)
    if len(parts) != 2:
        return set()
    field_prefix, suffix = parts

    if suffix == "value":
        part_idx = 1
    elif suffix.startswith("part"):
        try:
            part_idx = int(suffix[4:])
        except ValueError:
            return set()
    else:
        return set()

    rule = FIELD_RULES.get(field_prefix)
    if rule is None:
        return set()
    part_rule = rule.parts.get(part_idx)
    if part_rule is None or not part_rule.missing_values:
        return set()

    scale = part_rule.scale or 1.0
    return {round(float(value) * scale, 6) for value in part_rule.missing_values}


def find_sentinel_leakage(cleaned: pd.DataFrame) -> dict[str, int]:
    leaks: dict[str, int] = {}
    for column in cleaned.columns:
        sentinel_values = sentinel_values_for_column(column)
        if not sentinel_values:
            continue
        numeric = pd.to_numeric(cleaned[column], errors="coerce").dropna()
        if numeric.empty:
            continue
        leaked_mask = pd.Series(False, index=numeric.index)
        for sentinel in sentinel_values:
            leaked_mask = leaked_mask | numeric.sub(sentinel).abs().le(_SENTINEL_TOLERANCE)
        leaked_count = int(leaked_mask.sum())
        if leaked_count > 0:
            leaks[column] = leaked_count
    return leaks


def validate_canonical_schema_contract(cleaned: pd.DataFrame) -> None:
    missing = [column for column in CANONICAL_DATASET_CONTRACT.required_columns if column not in cleaned.columns]
    if missing:
        raise ValueError(f"Canonical schema contract violation: missing required columns {missing}")

    for column, expected_type in CANONICAL_CORE_COLUMN_TYPES:
        series = cleaned[column]
        if expected_type == "string":
            if not (pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series)):
                raise ValueError(f"Canonical schema contract violation: {column} must be string-like")
            continue
        if expected_type == "integer":
            coerced = pd.to_numeric(series, errors="coerce")
            invalid = series.notna() & coerced.isna()
            if invalid.any():
                raise ValueError(f"Canonical schema contract violation: {column} must be numeric integer-like")
            numeric = coerced.dropna()
            if numeric.empty:
                continue
            if not ((numeric % 1).abs() <= _SENTINEL_TOLERANCE).all():
                raise ValueError(f"Canonical schema contract violation: {column} must be integer-like")
            continue
        if expected_type == "float":
            coerced = pd.to_numeric(series, errors="coerce")
            invalid = series.notna() & coerced.isna()
            if invalid.any():
                raise ValueError(f"Canonical schema contract violation: {column} must be numeric")
            continue
        if expected_type == "boolean":
            if pd.api.types.is_bool_dtype(series):
                continue
            normalized = series.dropna().astype(str).str.strip().str.lower()
            if not normalized.isin({"true", "false", "1", "0"}).all():
                raise ValueError(f"Canonical schema contract violation: {column} must be boolean-like")
            continue
        raise ValueError(f"Unknown canonical schema expected type: {expected_type}")


def validate_no_sentinel_leakage(cleaned: pd.DataFrame) -> None:
    leaks = find_sentinel_leakage(cleaned)
    if not leaks:
        return
    sample = ", ".join(f"{column}={count}" for column, count in sorted(leaks.items())[:8])
    raise ValueError(f"Canonical contract violation: sentinel leakage detected ({sample})")
