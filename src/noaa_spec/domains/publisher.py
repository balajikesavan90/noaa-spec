"""Domain dataset publisher backed by package-governed registry contracts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from ..contracts import DOMAIN_DATASET_CONTRACT
from ..deterministic_io import write_deterministic_csv, write_deterministic_parquet
from .registry import DomainDefinition, domain_definitions


@dataclass(frozen=True)
class ViewDefinition:
    view_name: str
    domain_name: str
    description: str


VIEW_DEFINITIONS: tuple[ViewDefinition, ...] = (
    ViewDefinition(
        view_name="core",
        domain_name="core_meteorology",
        description="alias for core_meteorology",
    ),
    ViewDefinition(
        view_name="core_meteorology",
        domain_name="core_meteorology",
        description="station/time context and identifying metadata",
    ),
    ViewDefinition(
        view_name="wind",
        domain_name="wind",
        description="wind speed, direction, gust, and wind QC fields",
    ),
    ViewDefinition(
        view_name="precipitation",
        domain_name="precipitation",
        description="precipitation amount, period, snow depth, and precip QC fields",
    ),
    ViewDefinition(
        view_name="clouds_visibility",
        domain_name="clouds_visibility",
        description="visibility, ceiling, cloud cover, and related QC fields",
    ),
    ViewDefinition(
        view_name="pressure_temperature",
        domain_name="pressure_temperature",
        description="temperature, dew point, pressure, and related QC fields",
    ),
    ViewDefinition(
        view_name="remarks",
        domain_name="remarks",
        description="free-text remarks associated with each observation",
    ),
)


def available_view_names() -> tuple[str, ...]:
    return tuple(definition.view_name for definition in VIEW_DEFINITIONS)


def available_views_text() -> str:
    return ", ".join(available_view_names())


def get_view_definition(view_name: str) -> ViewDefinition:
    normalized = view_name.strip().lower()
    for definition in VIEW_DEFINITIONS:
        if definition.view_name == normalized:
            return definition
    raise KeyError(view_name)


def project_view_from_canonical(
    cleaned: pd.DataFrame,
    view_name: str,
) -> tuple[ViewDefinition, pd.DataFrame]:
    definition = get_view_definition(view_name)
    projected_by_domain = {
        domain_definition.domain_name: domain_df
        for domain_definition, domain_df in project_domain_datasets_from_registry(cleaned)
    }

    if definition.domain_name not in projected_by_domain:
        raise ValueError(
            f"View {definition.view_name!r} could not be projected from the canonical output."
        )
    return definition, projected_by_domain[definition.domain_name]


def project_domain_datasets_from_registry(
    cleaned: pd.DataFrame,
) -> list[tuple[DomainDefinition, pd.DataFrame]]:
    normalized = _with_standard_join_keys(cleaned)
    projected: list[tuple[DomainDefinition, pd.DataFrame]] = []
    for definition in domain_definitions():
        selected_columns = _selected_columns_for_definition(normalized, definition)
        if not selected_columns:
            continue
        _validate_emitted_columns(definition, selected_columns)
        projected.append((definition, normalized[selected_columns]))
    return projected


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
    for definition, domain_df in project_domain_datasets_from_registry(cleaned):
        output_suffix = "csv" if output_format == "csv" else "parquet"
        output_file = output_dir / f"{station_slug}__{definition.domain_name}.{output_suffix}"
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
                "rows": int(len(domain_df)),
                "columns": int(len(domain_df.columns)),
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
