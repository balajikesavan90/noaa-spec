"""Versioned artifact contract declarations for publication outputs."""

from __future__ import annotations

from dataclasses import dataclass


SHARED_JOIN_KEYS: tuple[str, ...] = ("station_id", "DATE")

REQUIRED_ARTIFACT_METADATA_FIELDS: tuple[str, ...] = (
    "artifact_id",
    "schema_version",
    "build_id",
    "input_lineage",
    "row_count",
    "checksum",
    "creation_timestamp",
)

SUCCESS_MARKER_SCHEMA_VERSION = "1.0.0"

QUALITY_REPORT_TYPES: tuple[str, ...] = (
    "field_completeness",
    "sentinel_frequency",
    "quality_code_exclusions",
    "domain_usability_summary",
    "station_year_quality",
)


@dataclass(frozen=True)
class ArtifactContract:
    artifact_type: str
    schema_version: str
    required_columns: tuple[str, ...]
    join_keys: tuple[str, ...]
    required_metadata_fields: tuple[str, ...]
    null_semantics: tuple[str, ...]


CANONICAL_DATASET_CONTRACT = ArtifactContract(
    artifact_type="canonical_dataset",
    schema_version="1.0.0",
    required_columns=(
        "station_id",
        "DATE",
        "YEAR",
        "row_has_any_usable_metric",
        "usable_metric_count",
        "usable_metric_fraction",
    ),
    join_keys=SHARED_JOIN_KEYS,
    required_metadata_fields=REQUIRED_ARTIFACT_METADATA_FIELDS,
    null_semantics=(
        "sentinel values are nullified; sentinel literals must not remain in cleaned numeric values",
        "QC exclusion reason columns remain nullable string columns",
    ),
)

DOMAIN_DATASET_CONTRACT = ArtifactContract(
    artifact_type="domain_dataset",
    schema_version="1.0.0",
    required_columns=(
        "station_id",
        "DATE",
    ),
    join_keys=SHARED_JOIN_KEYS,
    required_metadata_fields=REQUIRED_ARTIFACT_METADATA_FIELDS,
    null_semantics=(
        "domain values inherit canonical null semantics",
        "join keys are stable and nullable only when source observations are malformed",
    ),
)

QUALITY_REPORT_CONTRACT = ArtifactContract(
    artifact_type="quality_report",
    schema_version="1.0.0",
    required_columns=("artifact_id", "report_type"),
    join_keys=("artifact_id",),
    required_metadata_fields=REQUIRED_ARTIFACT_METADATA_FIELDS,
    null_semantics=(
        "quality counts use explicit zero values, not implicit missing values",
        "report references must preserve lineage to canonical or domain artifacts",
    ),
)

RELEASE_MANIFEST_CONTRACT = ArtifactContract(
    artifact_type="release_manifest",
    schema_version="1.0.0",
    required_columns=(
        "artifact_id",
        "artifact_type",
        "artifact_path",
        "schema_version",
        "build_id",
        "input_lineage",
        "row_count",
        "checksum",
        "creation_timestamp",
    ),
    join_keys=("artifact_id",),
    required_metadata_fields=REQUIRED_ARTIFACT_METADATA_FIELDS,
    null_semantics=(
        "manifest columns are non-null except input_lineage for source roots",
        "lineage lists are serialized deterministically",
    ),
)


def publication_artifact_contracts() -> tuple[ArtifactContract, ...]:
    return (
        CANONICAL_DATASET_CONTRACT,
        DOMAIN_DATASET_CONTRACT,
        QUALITY_REPORT_CONTRACT,
        RELEASE_MANIFEST_CONTRACT,
    )
