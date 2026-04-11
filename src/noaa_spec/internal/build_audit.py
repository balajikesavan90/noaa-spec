from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .cleaning_runner import (
    _checksum_for_output_bundle,
    _publication_checksum_check,
    _resolve_manifest_artifact_path,
)


RELEASE_COLUMNS = [
    "artifact_id",
    "artifact_type",
    "artifact_path",
    "schema_version",
    "build_id",
    "input_lineage",
    "row_count",
    "checksum",
    "creation_timestamp",
]

EXPECTED_RELEASE_TYPES = {"raw_source", "canonical_dataset", "domain_dataset", "quality_report"}
EXPECTED_QUALITY_IDS = {
    "field_completeness",
    "sentinel_frequency",
    "quality_code_exclusions",
    "domain_usability_summary",
    "station_year_quality",
}


@dataclass(frozen=True)
class AuditPaths:
    build_root: Path
    canonical_root: Path
    domains_root: Path
    quality_root: Path
    manifests_root: Path
    release_manifest: Path
    file_manifest: Path
    run_state: Path
    run_status: Path
    build_metadata: Path
    publication_gate: Path
    quality_assessment: Path


def build_audit_paths(build_root: Path) -> AuditPaths:
    manifests_root = build_root / "manifests"
    return AuditPaths(
        build_root=build_root,
        canonical_root=build_root / "canonical_cleaned",
        domains_root=build_root / "domains",
        quality_root=build_root / "quality_reports",
        manifests_root=manifests_root,
        release_manifest=manifests_root / "release_manifest.csv",
        file_manifest=manifests_root / "file_manifest.csv",
        run_state=manifests_root / "run_state.json",
        run_status=manifests_root / "run_status.csv",
        build_metadata=manifests_root / "build_metadata.json",
        publication_gate=manifests_root / "publication_readiness_gate.json",
        quality_assessment=build_root / "quality_reports" / "quality_assessment.json",
    )


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_lineage(value: object) -> list[str]:
    if value is None:
        return []
    text = str(value).strip()
    if not text:
        return []
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item) for item in parsed]


def _artifact_path_exists(frame: pd.DataFrame, *, build_root: Path) -> pd.Series:
    return frame["artifact_path"].astype(str).map(
        lambda value: _resolve_manifest_artifact_path(value, build_root=build_root).exists()
    )


def _existing_dir_entries(path: Path) -> list[Path]:
    if not path.exists() or not path.is_dir():
        return []
    return list(path.iterdir())


def _recompute_checksum_mismatches(frame: pd.DataFrame, *, build_root: Path) -> list[str]:
    invalid: list[str] = []
    for row in frame.to_dict(orient="records"):
        artifact_id = str(row["artifact_id"])
        artifact_path = _resolve_manifest_artifact_path(str(row["artifact_path"]), build_root=build_root)
        if not artifact_path.exists():
            invalid.append(artifact_id)
            continue
        actual = _checksum_for_output_bundle([artifact_path])
        if actual != str(row["checksum"]):
            invalid.append(artifact_id)
    return sorted(set(invalid))


def _markdown_table(rows: list[tuple[str, str]]) -> str:
    lines = ["| Check | Result |", "| --- | --- |"]
    for key, value in rows:
        lines.append(f"| {key} | {value} |")
    return "\n".join(lines)


def _cross_manifest_checksum_disagreements(
    release: pd.DataFrame,
    file_manifest: pd.DataFrame,
) -> list[str]:
    if release.empty or file_manifest.empty:
        return []
    file_rows = file_manifest[
        file_manifest["artifact_type"].astype(str).isin({"canonical_dataset", "domain_dataset", "quality_report"})
    ].copy()
    release_lookup = {
        str(row["artifact_path"]): str(row["checksum"])
        for row in release.to_dict(orient="records")
    }
    disagreements: list[str] = []
    for row in file_rows.to_dict(orient="records"):
        artifact_path = str(row["artifact_path"])
        release_checksum = release_lookup.get(artifact_path)
        file_checksum = str(row["checksum"])
        if release_checksum is None:
            continue
        if release_checksum != file_checksum:
            disagreements.append(artifact_path)
    return sorted(set(disagreements))


def render_build_audit_report(build_root: Path) -> str:
    audit_paths = build_audit_paths(build_root.resolve())

    release = pd.read_csv(audit_paths.release_manifest, dtype=str)
    file_manifest = pd.read_csv(audit_paths.file_manifest, dtype=str)
    run_status = pd.read_csv(audit_paths.run_status, dtype=str)
    run_state = _load_json(audit_paths.run_state)
    build_metadata = _load_json(audit_paths.build_metadata)
    publication_gate = _load_json(audit_paths.publication_gate)
    quality_assessment = _load_json(audit_paths.quality_assessment)

    canonical_station_dirs = sorted(path.name for path in _existing_dir_entries(audit_paths.canonical_root) if path.is_dir())
    domain_station_dirs = sorted(path.name for path in _existing_dir_entries(audit_paths.domains_root) if path.is_dir())
    station_quality_root = audit_paths.quality_root / "station_quality"
    station_quality_profiles = sorted(station_quality_root.glob("station_*.json")) if station_quality_root.exists() else []

    release_types = set(release["artifact_type"].astype(str))
    release_artifact_ids = set(release["artifact_id"].astype(str))
    quality_rows = release[release["artifact_type"].astype(str) == "quality_report"].copy()
    quality_names = {
        str(value).rsplit("/", 1)[-1] for value in quality_rows["artifact_id"].astype(str).tolist()
    }

    canonical_rows = release[release["artifact_type"].astype(str) == "canonical_dataset"].copy()
    domain_rows = release[release["artifact_type"].astype(str) == "domain_dataset"].copy()
    raw_rows = release[release["artifact_type"].astype(str) == "raw_source"].copy()

    canonical_lineage_ok = all(
        len(lineage) == 1 and lineage[0].startswith("raw_source/")
        for lineage in canonical_rows["input_lineage"].map(_parse_lineage)
    )
    domain_lineage_ok = all(
        len(lineage) == 1 and lineage[0].startswith("canonical_dataset/")
        for lineage in domain_rows["input_lineage"].map(_parse_lineage)
    )
    quality_lineage_ok = True
    for lineage in quality_rows["input_lineage"].map(_parse_lineage):
        if not lineage:
            quality_lineage_ok = False
            break
        if not any(item.startswith("canonical_dataset/") for item in lineage):
            quality_lineage_ok = False
            break
        if not any(item.startswith("domain_dataset/") for item in lineage):
            quality_lineage_ok = False
            break
        if not all(item in release_artifact_ids for item in lineage):
            quality_lineage_ok = False
            break

    recomputed_release_mismatches = _recompute_checksum_mismatches(release, build_root=build_root)
    recomputed_file_mismatches = _recompute_checksum_mismatches(
        file_manifest[file_manifest["artifact_type"].astype(str) != "publication_readiness_gate"].copy(),
        build_root=build_root,
    )
    recomputed_gate_checksum = _publication_checksum_check(
        build_root=build_root,
        release_manifest=release,
        file_manifest=file_manifest,
    )
    cross_manifest_disagreements = _cross_manifest_checksum_disagreements(release, file_manifest)

    release_paths_exist = bool(_artifact_path_exists(release, build_root=build_root).all())
    file_paths_exist = bool(
        _artifact_path_exists(
            file_manifest[file_manifest["artifact_type"].astype(str) != "publication_readiness_gate"].copy(),
            build_root=build_root,
        ).all()
    )

    completed_rows = run_status[run_status["status"].astype(str) == "completed"].copy()
    completed_station_ids = sorted(completed_rows["station_id"].astype(str).tolist())

    gate_invalid_rows = publication_gate.get("checks", {}).get("checksum_policy_conformance", {}).get("invalid_rows", [])
    gate_invalid_rows = [str(item) for item in gate_invalid_rows]
    stale_gate_difference = sorted(set(gate_invalid_rows) ^ set(recomputed_gate_checksum["invalid_rows"]))

    overview_rows = [
        ("Build root", str(build_root.resolve())),
        ("Build id", str(build_metadata.get("build_id", ""))),
        ("Build timestamp", str(build_metadata.get("build_timestamp", ""))),
        ("Run state", str(run_state.get("state", ""))),
        ("Finalized", str(run_state.get("finalized", False))),
        ("Completed stations", f"{len(completed_station_ids)} / {run_state.get('counts', {}).get('total', 0)}"),
        ("Canonical station dirs", str(len(canonical_station_dirs))),
        ("Domain station dirs", str(len(domain_station_dirs))),
        ("Station quality profiles", str(len(station_quality_profiles))),
        ("Release manifest rows", str(len(release))),
        ("File manifest rows", str(len(file_manifest))),
    ]

    contract_rows = [
        ("Release manifest columns", "pass" if list(release.columns) == RELEASE_COLUMNS else "fail"),
        ("Release artifact types", "pass" if EXPECTED_RELEASE_TYPES.issubset(release_types) else "fail"),
        ("Required quality artifacts", "pass" if EXPECTED_QUALITY_IDS.issubset(quality_names) else "fail"),
        ("Release artifact_id unique", "pass" if release["artifact_id"].is_unique else "fail"),
        ("File manifest artifact_id unique", "pass" if file_manifest["artifact_id"].is_unique else "fail"),
        ("Release artifact paths exist", "pass" if release_paths_exist else "fail"),
        ("File artifact paths exist", "pass" if file_paths_exist else "fail"),
    ]

    lineage_rows = [
        ("Raw source lineage non-empty", "pass" if all(raw_rows["input_lineage"].map(lambda value: len(_parse_lineage(value)) >= 1)) else "fail"),
        ("Canonical lineage -> raw_source", "pass" if canonical_lineage_ok else "fail"),
        ("Domain lineage -> canonical_dataset", "pass" if domain_lineage_ok else "fail"),
        ("Quality lineage references release artifacts", "pass" if quality_lineage_ok else "fail"),
    ]

    checksum_rows = [
        ("Embedded publication gate checksum check", "pass" if publication_gate.get("checks", {}).get("checksum_policy_conformance", {}).get("passed", False) else "fail"),
        ("Recomputed checksum check", "pass" if recomputed_gate_checksum["passed"] else "fail"),
        ("Release manifest checksum mismatches", str(len(recomputed_release_mismatches))),
        ("File manifest checksum mismatches", str(len(recomputed_file_mismatches))),
        ("Cross-manifest checksum disagreements", str(len(cross_manifest_disagreements))),
        ("Gate/report mismatch set", "none" if not stale_gate_difference else ", ".join(stale_gate_difference)),
    ]

    assessment_lines = [
        "# Post-Run Audit Report",
        "",
        "## Overview",
        "",
        _markdown_table(overview_rows),
        "",
        "## Contract Checks",
        "",
        _markdown_table(contract_rows),
        "",
        "## Lineage Checks",
        "",
        _markdown_table(lineage_rows),
        "",
        "## Checksum Checks",
        "",
        _markdown_table(checksum_rows),
        "",
        "## Key Findings",
        "",
    ]

    findings: list[str] = []
    if str(run_state.get("state", "")) == "completed" and bool(run_state.get("finalized", False)):
        findings.append("Run completed and finalization artifacts were written.")
    else:
        findings.append("Run did not reach a fully finalized completed state.")

    if len(completed_station_ids) == len(canonical_station_dirs) == len(domain_station_dirs) == len(station_quality_profiles):
        findings.append("Station-level artifact families are complete across canonical, domain, and quality-profile outputs.")
    else:
        findings.append("Station-level artifact families are not balanced across canonical, domain, and quality-profile outputs.")

    if publication_gate.get("passed", False):
        findings.append("Embedded publication gate passed.")
    else:
        findings.append("Embedded publication gate failed.")

    if stale_gate_difference:
        findings.append(
            "Embedded publication gate checksum findings are stale relative to the final manifest set."
        )

    if recomputed_gate_checksum["invalid_rows"]:
        findings.append(
            "Recomputed checksum mismatches remain for: "
            + ", ".join(recomputed_gate_checksum["invalid_rows"])
            + "."
        )
    else:
        findings.append("Recomputed checksum validation passed for all release and file-manifest rows.")

    if cross_manifest_disagreements:
        findings.append(
            "Release and file manifests disagree on the checksum for the same artifact path in "
            + str(len(cross_manifest_disagreements))
            + " cases."
        )

    descriptive_notes = quality_assessment.get("descriptive_notes", [])
    if isinstance(descriptive_notes, list) and descriptive_notes:
        findings.append(
            "Quality assessment is emitted as a descriptive diagnostic artifact separate from publication integrity checks."
        )

    assessment_lines.extend(f"- {line}" for line in findings)
    assessment_lines.extend(
        [
            "",
            "## Recomputed Checksum Mismatches",
            "",
            "### Release Manifest",
            "",
        ]
    )
    if recomputed_release_mismatches:
        assessment_lines.extend(f"- {item}" for item in recomputed_release_mismatches)
    else:
        assessment_lines.append("- none")

    assessment_lines.extend(
        [
            "",
            "### File Manifest",
            "",
        ]
    )
    if recomputed_file_mismatches:
        assessment_lines.extend(f"- {item}" for item in recomputed_file_mismatches)
    else:
        assessment_lines.append("- none")

    assessment_lines.extend(
        [
            "",
            "## Cross-Manifest Checksum Disagreements",
            "",
        ]
    )
    if cross_manifest_disagreements:
        assessment_lines.extend(f"- {item}" for item in cross_manifest_disagreements)
    else:
        assessment_lines.append("- none")

    assessment_lines.extend(
        [
            "",
            "## Embedded Gate Snapshot",
            "",
            "```json",
            json.dumps(publication_gate, indent=2),
            "```",
            "",
            "## Recomputed Checksum Snapshot",
            "",
            "```json",
            json.dumps(recomputed_gate_checksum, indent=2),
            "```",
        ]
    )
    return "\n".join(assessment_lines) + "\n"


def write_build_audit_report(build_root: Path, output_path: Path) -> Path:
    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_build_audit_report(build_root), encoding="utf-8")
    return output_path
