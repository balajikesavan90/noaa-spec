"""Domain dataset publisher backed by package-governed registry contracts."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ..contracts import DOMAIN_DATASET_CONTRACT
from .registry import DomainDefinition, domain_definitions


def write_domain_datasets_from_registry(
    cleaned: pd.DataFrame,
    *,
    station_slug: str,
    station_name: str,
    output_dir: Path,
    output_format: str,
) -> list[dict[str, object]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    if output_format not in {"csv", "parquet"}:
        raise ValueError(f"Unsupported domain split output format: {output_format}")

    manifest_rows: list[dict[str, object]] = []
    for definition in domain_definitions():
        selected_columns = _selected_columns_for_definition(cleaned, definition)
        if not selected_columns:
            continue

        output_suffix = "csv" if output_format == "csv" else "parquet"
        output_file = output_dir / f"{station_slug}__{definition.domain_name}.{output_suffix}"
        domain_df = cleaned[selected_columns]
        if output_format == "csv":
            domain_df.to_csv(output_file, index=False)
        else:
            _normalize_object_columns_for_parquet(domain_df).to_parquet(output_file, index=False)

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


def _selected_columns_for_definition(
    cleaned: pd.DataFrame,
    definition: DomainDefinition,
) -> list[str]:
    schema_columns = [column for column, _dtype in definition.output_schema]
    present = [column for column in schema_columns if column in cleaned.columns]
    if not present:
        return []

    join_keys = [key for key in definition.join_keys if key in cleaned.columns]
    domain_specific = [column for column in present if column not in join_keys]
    if not domain_specific:
        return []
    return join_keys + domain_specific


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
