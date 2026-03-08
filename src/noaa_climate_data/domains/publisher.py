"""Domain dataset publisher backed by package-governed registry contracts."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ..contracts import DOMAIN_DATASET_CONTRACT
from ..deterministic_io import write_deterministic_csv, write_deterministic_parquet
from .registry import DomainDefinition, domain_definitions


def write_domain_datasets_from_registry(
    cleaned: pd.DataFrame,
    *,
    station_slug: str,
    station_name: str,
    output_dir: Path,
    output_format: str,
) -> list[dict[str, object]]:
    cleaned = _with_standard_join_keys(cleaned)
    output_dir.mkdir(parents=True, exist_ok=True)
    if output_format not in {"csv", "parquet"}:
        raise ValueError(f"Unsupported domain split output format: {output_format}")

    manifest_rows: list[dict[str, object]] = []
    for definition in domain_definitions():
        selected_columns = _selected_columns_for_definition(cleaned, definition)
        if not selected_columns:
            continue
        _validate_emitted_columns(definition, selected_columns)

        output_suffix = "csv" if output_format == "csv" else "parquet"
        output_file = output_dir / f"{station_slug}__{definition.domain_name}.{output_suffix}"
        domain_df = cleaned[selected_columns]
        if output_format == "csv":
            write_deterministic_csv(domain_df, output_file, sort_by=tuple(definition.join_keys))
        else:
            write_deterministic_parquet(
                _normalize_object_columns_for_parquet(domain_df),
                output_file,
                sort_by=tuple(definition.join_keys),
            )

        size_mb = output_file.stat().st_size / (1024 * 1024)
        manifest_rows.append(
            {
                "station_name": station_name,
                "domain": definition.domain_name,
                "rows": int(len(cleaned)),
                "columns": int(len(selected_columns)),
                "file": str(output_file),
                "size_mb": round(size_mb, 2),
                "contract_schema_version": DOMAIN_DATASET_CONTRACT.schema_version,
            }
        )
    return manifest_rows


def _with_standard_join_keys(cleaned: pd.DataFrame) -> pd.DataFrame:
    if "station_id" in cleaned.columns:
        return cleaned
    if "STATION" not in cleaned.columns:
        return cleaned
    normalized = cleaned.copy()
    normalized["station_id"] = normalized["STATION"].astype(str)
    return normalized


def _selected_columns_for_definition(
    cleaned: pd.DataFrame,
    definition: DomainDefinition,
) -> list[str]:
    if any(key not in cleaned.columns for key in definition.join_keys):
        return []

    schema_columns = [column for column, _dtype in definition.output_schema]
    present = [column for column in schema_columns if column in cleaned.columns]
    if not present:
        return []

    join_keys = list(definition.join_keys)
    domain_specific = [column for column in present if column not in join_keys]
    if not domain_specific:
        return []
    return join_keys + domain_specific


def _validate_emitted_columns(definition: DomainDefinition, columns: list[str]) -> None:
    schema_columns = {column for column, _dtype in definition.output_schema}
    unexpected = [column for column in columns if column not in schema_columns]
    if unexpected:
        raise ValueError(
            f"Domain {definition.domain_name} emitted columns outside OUTPUT_SCHEMA: {unexpected}"
        )
    missing_join = [key for key in definition.join_keys if key not in columns]
    if missing_join:
        raise ValueError(
            f"Domain {definition.domain_name} emitted without required join keys: {missing_join}"
        )


def _normalize_object_columns_for_parquet(frame: pd.DataFrame) -> pd.DataFrame:
    normalized = frame.copy()
    for column in normalized.columns:
        series = normalized[column]
        if not pd.api.types.is_object_dtype(series):
            continue
        normalized[column] = series.map(_coerce_to_nullable_text).astype("string")
    return normalized


def _coerce_to_nullable_text(value: object) -> object:
    if value is None:
        return pd.NA
    if isinstance(value, float) and pd.isna(value):
        return pd.NA
    if isinstance(value, (bytes, bytearray)):
        return value.decode("utf-8", errors="replace")
    return str(value)
