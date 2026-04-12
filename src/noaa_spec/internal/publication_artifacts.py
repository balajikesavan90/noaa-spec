"""Deterministic build-root publication artifacts for NOAA-Spec releases."""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import pandas as pd

from ..constants import to_internal_column
from ..contracts import CANONICAL_DATASET_CONTRACT
from ..deterministic_io import write_deterministic_csv

try:
    import pyarrow.parquet as pq
except ImportError:  # pragma: no cover - parquet support is optional at import time
    pq = None


_RAW_TOKEN_RE = re.compile(r"^[A-Z][A-Z0-9]*$")
_INTERNAL_PART_RE = re.compile(r"^(?P<token>[A-Z][A-Z0-9]*)__part(?P<part>\d+)$")
_INTERNAL_SUFFIX_RE = re.compile(
    r"^(?P<base>[A-Z][A-Z0-9]*(?:__(?:part\d+|value|quality))?)__qc_(?P<kind>pass|status|reason)$"
)
_QC_CONTROL_RE = re.compile(r"^qc_(?P<scope>control|domain)_invalid_(?P<field>[a-z0-9_]+)$")

_COLUMN_DESCRIPTION_OVERRIDES: dict[str, str] = {
    "STATION": "NOAA station identifier for the observation row.",
    "station_id": "Station identifier normalized by NOAA-Spec for internal joins and station-level artifacts.",
    "DATE": "Observation timestamp preserved in canonical cleaned form.",
    "YEAR": "Calendar year derived from the canonical DATE column.",
    "SOURCE": "NOAA source flag preserved from the raw observation.",
    "LATITUDE": "Station latitude from the raw observation metadata.",
    "LONGITUDE": "Station longitude from the raw observation metadata.",
    "ELEVATION": "Station elevation from the raw observation metadata.",
    "REPORT_TYPE": "NOAA report type code preserved from the raw observation.",
    "CALL_SIGN": "Observed station call sign preserved from the raw observation.",
    "QUALITY_CONTROL": "NOAA processing or quality-control code from the raw observation.",
    "REM": "Raw NOAA remarks payload preserved from the source observation.",
    "EQD": "Raw NOAA equipment or auxiliary descriptor token preserved from the source observation.",
    "remarks_type_code": "Parsed remarks family identifier derived from the NOAA remarks payload.",
    "remarks_text": "Primary free-text remarks block extracted from the NOAA remarks payload.",
    "remarks_type_codes": "Pipe-delimited remarks family identifiers extracted from the NOAA remarks payload.",
    "remarks_text_blocks_json": "JSON array of remarks text blocks extracted from the NOAA remarks payload.",
    "wind_direction_variable": "Boolean indicator that the source wind token marked direction as variable.",
    "qc_calm_wind_detected": "Boolean indicator that NOAA-Spec detected a calm-wind condition in the source record.",
    "row_has_any_usable_metric": "Derived boolean indicator that at least one cleaned metric passed QC for the row.",
    "usable_metric_count": "Derived count of cleaned metrics whose QC pass indicator is true for the row.",
    "usable_metric_fraction": "Derived fraction of cleaned metrics whose QC pass indicator is true for the row.",
}

_COLUMN_NOTES_OVERRIDES: dict[str, str] = {
    "YEAR": "Derived by NOAA-Spec from DATE when not explicitly present.",
    "station_id": "Derived alias of STATION for internal release joins.",
    "remarks_type_codes": "Serialized deterministically using pipe delimiters.",
    "remarks_text_blocks_json": "Serialized deterministically as compact JSON text.",
    "row_has_any_usable_metric": "Derived from the set of *__qc_pass columns in the canonical dataset.",
    "usable_metric_count": "Derived from the set of *__qc_pass columns in the canonical dataset.",
    "usable_metric_fraction": "Derived from the set of *__qc_pass columns in the canonical dataset.",
}


@dataclass(frozen=True)
class SchemaDeviation:
    station_id: str
    path: Path
    column_count: int
    missing_columns: tuple[str, ...]
    added_columns: tuple[str, ...]
    reordered: bool


@dataclass(frozen=True)
class CanonicalSchemaSummary:
    station_files: tuple[Path, ...]
    station_ids: tuple[str, ...]
    canonical_columns: tuple[str, ...]
    union_columns: tuple[str, ...]
    deviations: tuple[SchemaDeviation, ...]

    @property
    def station_count(self) -> int:
        return len(self.station_files)

    @property
    def consistent(self) -> bool:
        return len(self.deviations) == 0


def enumerate_canonical_cleaned_files(output_root: Path) -> list[Path]:
    files: list[Path] = []
    if not output_root.exists():
        return files

    for station_dir in sorted(path for path in output_root.iterdir() if path.is_dir()):
        csv_path = station_dir / "LocationData_Cleaned.csv"
        parquet_path = station_dir / "LocationData_Cleaned.parquet"
        if csv_path.exists():
            files.append(csv_path.resolve())
            continue
        if parquet_path.exists():
            files.append(parquet_path.resolve())
    return files


def validate_canonical_schema_consistency(output_root: Path) -> CanonicalSchemaSummary:
    station_files = tuple(enumerate_canonical_cleaned_files(output_root))
    if not station_files:
        return CanonicalSchemaSummary(
            station_files=(),
            station_ids=(),
            canonical_columns=(),
            union_columns=(),
            deviations=(),
        )

    signatures = [(path, tuple(_read_cleaned_columns(path))) for path in station_files]
    reference_path, reference_columns = signatures[0]
    reference_set = set(reference_columns)
    deviations: list[SchemaDeviation] = []
    station_ids: list[str] = []
    union_columns: list[str] = []
    seen_union_columns: set[str] = set()

    for path, columns in signatures:
        station_ids.append(path.parent.name)
        for column in columns:
            if column not in seen_union_columns:
                seen_union_columns.add(column)
                union_columns.append(column)
        if columns == reference_columns:
            continue
        current_set = set(columns)
        deviations.append(
            SchemaDeviation(
                station_id=path.parent.name,
                path=path,
                column_count=len(columns),
                missing_columns=tuple(sorted(reference_set - current_set)),
                added_columns=tuple(sorted(current_set - reference_set)),
                reordered=(
                    len(columns) == len(reference_columns)
                    and current_set == reference_set
                    and columns != reference_columns
                ),
            )
        )

    return CanonicalSchemaSummary(
        station_files=station_files,
        station_ids=tuple(station_ids),
        canonical_columns=reference_columns,
        union_columns=tuple(union_columns),
        deviations=tuple(deviations),
    )


def build_data_dictionary_frame(columns: Sequence[str]) -> pd.DataFrame:
    rows = []
    for column in columns:
        metadata = _column_metadata(column)
        rows.append(metadata)
    return pd.DataFrame(rows, columns=["column_name", "description", "source_token", "notes"])


def write_build_publication_artifacts(
    *,
    build_root: Path,
    output_root: Path,
    reports_root: Path,
    manifest_root: Path,
) -> dict[str, Any]:
    schema_summary = validate_canonical_schema_consistency(output_root)
    if not schema_summary.station_files:
        raise ValueError("Cannot generate build publication artifacts without canonical cleaned outputs.")

    build_metadata = _load_json_if_exists(manifest_root / "build_metadata.json")
    readme_path = build_root / "README.md"
    dictionary_path = build_root / "data_dictionary.csv"

    readme_path.write_text(
        render_build_readme(
            build_root=build_root,
            reports_root=reports_root,
            build_metadata=build_metadata,
            station_count=schema_summary.station_count,
            schema_version=CANONICAL_DATASET_CONTRACT.schema_version,
            schema_summary=schema_summary,
        ),
        encoding="utf-8",
    )

    dictionary_frame = build_data_dictionary_frame(schema_summary.union_columns)
    write_deterministic_csv(dictionary_frame, dictionary_path)

    return {
        "readme_path": readme_path,
        "data_dictionary_path": dictionary_path,
        "schema_summary": schema_summary,
        "dictionary_frame": dictionary_frame,
    }


def render_build_readme(
    *,
    build_root: Path,
    reports_root: Path,
    build_metadata: dict[str, Any],
    station_count: int,
    schema_version: str,
    schema_summary: CanonicalSchemaSummary,
) -> str:
    build_id = str(build_metadata.get("build_id", build_root.name.removeprefix("build_")))
    build_timestamp = str(build_metadata.get("build_timestamp", "unknown"))
    code_revision = str(build_metadata.get("code_revision", "unknown")) or "unknown"

    lines = [
        f"# NOAA-Spec Build {build_id}",
        "",
        (
            "This build contains deterministic cleaned NOAA ISD / Global Hourly publication "
            "artifacts produced by NOAA-Spec. It includes canonical cleaned station outputs, "
            "quality evidence, integrity manifests, and the accompanying data dictionary "
            "needed to interpret the cleaned schema."
        ),
        "",
        f"- Build ID: `{build_id}`",
        f"- Build timestamp: `{build_timestamp}`",
        f"- Code revision: `{code_revision}`",
        f"- Canonical schema version: `{schema_version}`",
        f"- Station count: `{station_count}`",
        "",
        "## Included folders",
        "",
        "- `canonical_cleaned/`: station-level deterministic cleaned canonical outputs produced by NOAA-Spec from NOAA source observations.",
        "- `manifests/`: deterministic build manifests, integrity metadata, and release-audit artifacts for this build.",
        "- `quality_reports/`: build-level transparency artifacts summarizing completeness, sentinel impacts, QC exclusions, and related usability evidence.",
        "",
        "Canonical cleaned outputs should be interpreted together with the included `data_dictionary.csv`.",
        "",
        (
            "Use and citation note: cite the NOAA-Spec software, the specific build ID, and "
            "the included manifests when reusing these artifacts in research or "
            "publication workflows."
        ),
        "",
    ]

    if not reports_root.exists():
        lines = [line for line in lines if "`quality_reports/`" not in line]

    if not schema_summary.consistent:
        lines.extend(
            [
                "Schema note: canonical cleaned columns are not identical across all station files in this build.",
                (
                    "The included `data_dictionary.csv` lists the deterministic union of observed canonical "
                    "columns across completed station outputs."
                ),
                "",
            ]
        )

    return "\n".join(lines)


def _read_cleaned_columns(path: Path) -> list[str]:
    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle)
            try:
                return next(reader)
            except StopIteration:
                return []
    if path.suffix.lower() == ".parquet":
        if pq is None:
            raise RuntimeError("Parquet schema inspection requires pyarrow to be installed.")
        return list(pq.ParquetFile(path).schema_arrow.names)
    raise ValueError(f"Unsupported canonical cleaned artifact type: {path}")


def _load_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _column_metadata(column: str) -> dict[str, str]:
    source_token = _source_token_for_column(column)
    description = _describe_column(column, source_token)
    notes = _notes_for_column(column, source_token)
    return {
        "column_name": column,
        "description": description,
        "source_token": source_token,
        "notes": notes,
    }


def _source_token_for_column(column: str) -> str:
    if column in {"YEAR", "station_id", "row_has_any_usable_metric", "usable_metric_count", "usable_metric_fraction"}:
        return ""
    if column.startswith("qc_control_invalid_") or column.startswith("qc_domain_invalid_"):
        return "CONTROL"

    internal = to_internal_column(column)
    qc_match = _INTERNAL_SUFFIX_RE.match(internal)
    if qc_match is not None:
        base = qc_match.group("base")
        return base.split("__", 1)[0]

    if "__" in internal:
        return internal.split("__", 1)[0]
    if _RAW_TOKEN_RE.fullmatch(column):
        return column
    return ""


def _describe_column(column: str, source_token: str) -> str:
    override = _COLUMN_DESCRIPTION_OVERRIDES.get(column)
    if override is not None:
        return override

    internal = to_internal_column(column)
    qc_match = _INTERNAL_SUFFIX_RE.match(internal)
    if qc_match is not None:
        base = qc_match.group("base")
        kind = qc_match.group("kind")
        kind_text = {
            "pass": "pass indicator",
            "status": "status code",
            "reason": "reason code",
        }[kind]
        return (
            f"Derived QC {kind_text} for NOAA source token `{base}` after NOAA-Spec validation "
            "and sentinel handling."
        )

    control_match = _QC_CONTROL_RE.match(column)
    if control_match is not None:
        field_name = control_match.group("field").replace("_", " ")
        scope = control_match.group("scope")
        return f"Derived boolean flag that NOAA-Spec marked the {scope} field `{field_name}` as invalid."

    if column.endswith("_quality_code"):
        metric = column[: -len("_quality_code")].replace("_", " ")
        return f"NOAA quality code associated with `{metric}`."

    if _RAW_TOKEN_RE.fullmatch(column):
        return f"Preserved raw NOAA source token `{column}` from the original observation row."

    part_match = _INTERNAL_PART_RE.match(internal)
    if part_match is not None:
        token = part_match.group("token")
        part = part_match.group("part")
        return f"Normalized cleaned value derived from NOAA source token `{token}` part `{part}`."

    if internal.endswith("__quality"):
        token = internal.split("__", 1)[0]
        return f"Preserved NOAA quality code derived from source token `{token}`."

    if internal.endswith("__value"):
        token = internal.split("__", 1)[0]
        return f"Normalized cleaned value derived from NOAA source token `{token}`."

    label = column.replace("_", " ")
    return f"Canonical cleaned field `{label}` produced by NOAA-Spec."


def _notes_for_column(column: str, source_token: str) -> str:
    override = _COLUMN_NOTES_OVERRIDES.get(column)
    if override is not None:
        return override

    internal = to_internal_column(column)
    if _INTERNAL_SUFFIX_RE.match(internal) is not None:
        return "Derived by NOAA-Spec; not present as a standalone field in the raw NOAA row."
    if column.endswith("_quality_code") or internal.endswith("__quality"):
        return "Preserved NOAA quality code column."
    if source_token == "CONTROL":
        return "Derived structural validation signal emitted by NOAA-Spec."
    if _RAW_TOKEN_RE.fullmatch(column):
        return "Raw source token retained in the canonical dataset alongside cleaned derivatives."
    if "__" in internal:
        return "Sentinel-coded missing values are nullified during cleaning."
    return ""
