"""Diagnostic identifier investigation for reviewer-facing validation bundles."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import statistics
from typing import Any

import pandas as pd

from .constants import (
    KNOWN_IDENTIFIERS,
    get_field_rule,
    is_valid_eqd_identifier,
    is_valid_identifier,
    is_valid_repeated_identifier,
    is_valid_section_identifier_token,
)
from .validation import _station_id_from_path

TEXT_SCAN_SUFFIXES = {".md", ".py", ".txt", ".json", ".csv"}
ROW_LOCATOR_COLUMNS = ("STATION", "DATE", "REPORT_TYPE")
COOCCURRENCE_COLUMNS = ("AG1", "AJ1", "GJ1")
AW_IDENTIFIERS = ("AW5", "AW6")
REQUIRED_CONCLUSION = (
    "HL1 appears in the operational validation sample as a stable unsupported "
    "optional identifier. It was skipped by strict parsing and did not cause "
    "station-level failure or row loss. This report does not establish HL1 as "
    "an official documented NOAA ISD section; it documents observed behavior "
    "and preserves examples for reviewer inspection."
)


def inspect_identifier_bundle(
    *,
    bundle_root: Path,
    identifier: str,
    output_path: Path,
    max_stations: int = 10,
    max_rows_per_station: int = 5,
) -> dict[str, Any]:
    bundle_root = bundle_root.resolve()
    raw_inputs_dir = bundle_root / "raw_inputs"
    if not raw_inputs_dir.exists():
        raise FileNotFoundError(f"Bundle raw_inputs directory not found: {raw_inputs_dir}")

    normalized_identifier = identifier.strip().upper()
    if not normalized_identifier:
        raise ValueError("identifier must not be empty")
    if max_stations <= 0 or max_rows_per_station <= 0:
        raise ValueError("max-stations and max-rows-per-station must be positive")

    repo_root = Path(__file__).resolve().parents[2]
    spec_presence = _search_repository_specs(
        repo_root=repo_root,
        identifier=normalized_identifier,
    )
    station_results = _read_station_results(bundle_root)
    bundle_presence = _scan_bundle_raw_inputs(
        raw_inputs_dir=raw_inputs_dir,
        identifier=normalized_identifier,
        max_stations=max_stations,
        max_rows_per_station=max_rows_per_station,
    )
    parser_classification = _build_parser_classification(
        identifier=normalized_identifier,
        spec_presence=spec_presence,
    )
    relationship = _build_relationship_to_cleaning(
        station_results=station_results,
        station_ids=bundle_presence["station_ids"],
    )
    aw_notes = _investigate_aw_identifiers(
        raw_inputs_dir=raw_inputs_dir,
        station_results=station_results,
    )

    report = {
        "artifact_id": "identifier_investigation_report",
        "artifact_version": bundle_root.name,
        "schema_version": "1.0.0",
        "generated_utc": _now_utc_isoformat(),
        "bundle_root": str(bundle_root),
        "identifier": normalized_identifier,
        "purpose": (
            "Diagnostic evidence report for an unsupported identifier observed in "
            "the reviewer-facing validation bundle."
        ),
        "summary": _build_summary(
            identifier=normalized_identifier,
            bundle_presence=bundle_presence,
            spec_presence=spec_presence,
            relationship=relationship,
        ),
        "presence_in_repository_specs": spec_presence,
        "presence_in_100_station_validation_bundle": bundle_presence,
        "raw_examples": bundle_presence["example_rows"],
        "structural_observations": bundle_presence["structural_observations"],
        "parser_classification": parser_classification,
        "relationship_to_successful_cleaning": relationship,
        "aw5_aw6_notes": aw_notes,
        "interpretation": _build_interpretation(
            identifier=normalized_identifier,
            spec_presence=spec_presence,
            bundle_presence=bundle_presence,
        ),
        "recommendation": _build_recommendation(identifier=normalized_identifier),
        "required_conclusion": (
            REQUIRED_CONCLUSION if normalized_identifier == "HL1" else ""
        ),
    }

    output_path = output_path.resolve()
    json_path = output_path.with_suffix(".json")
    output_path.write_text(_render_markdown(report), encoding="utf-8")
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "identifier": normalized_identifier,
        "bundle_root": bundle_root,
        "markdown_report": output_path,
        "json_report": json_path,
        "station_count": bundle_presence["station_count"],
        "row_count": bundle_presence["row_count"],
    }


def _search_repository_specs(*, repo_root: Path, identifier: str) -> dict[str, Any]:
    search_targets = [
        repo_root / "spec_sources",
        repo_root / "docs" / "supported_fields.md",
        repo_root / "docs" / "rule_provenance.md",
        repo_root / "src" / "noaa_spec" / "constants.py",
    ]
    pattern = re.compile(rf"\b{re.escape(identifier)}\b")
    hits: list[dict[str, Any]] = []
    searched_files = 0

    for target in search_targets:
        if not target.exists():
            continue
        if target.is_file():
            paths = [target]
        else:
            paths = sorted(item for item in target.rglob("*") if item.is_file())
        for path in paths:
            if path.suffix.lower() not in TEXT_SCAN_SUFFIXES:
                continue
            searched_files += 1
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for line_number, line in enumerate(text.splitlines(), start=1):
                if pattern.search(line):
                    hits.append(
                        {
                            "path": path.relative_to(repo_root).as_posix(),
                            "line_number": line_number,
                            "line_text": line.strip(),
                        }
                    )

    return {
        "identifier": identifier,
        "searched_roots": [path.relative_to(repo_root).as_posix() for path in search_targets if path.exists()],
        "searched_file_count": searched_files,
        "exact_match_count": len(hits),
        "exact_match_hits": hits[:20],
        "appears_in_committed_spec_or_rule_text": bool(hits),
    }


def _read_station_results(bundle_root: Path) -> pd.DataFrame | None:
    station_results_path = bundle_root / "station_results.csv"
    if not station_results_path.exists():
        return None
    return pd.read_csv(station_results_path, dtype=str, keep_default_na=False)


def _scan_bundle_raw_inputs(
    *,
    raw_inputs_dir: Path,
    identifier: str,
    max_stations: int,
    max_rows_per_station: int,
) -> dict[str, Any]:
    station_ids: list[str] = []
    examples: list[dict[str, Any]] = []
    payload_counter: Counter[str] = Counter()
    payload_lengths: list[int] = []
    detection_modes: Counter[str] = Counter()
    cooccurrence_station_counts: Counter[str] = Counter()
    per_station_summary: list[dict[str, Any]] = []
    total_rows = 0
    total_nonempty_payloads = 0

    for path in sorted(item for item in raw_inputs_dir.iterdir() if item.is_file()):
        station_id = _station_id_from_path(path)
        frame = _read_raw_input(path)
        station_record = _scan_station_frame(
            frame=frame,
            raw_input_path=path.relative_to(raw_inputs_dir.parent),
            station_id=station_id,
            identifier=identifier,
            max_rows_per_station=max_rows_per_station,
        )
        if not station_record["present"]:
            continue

        station_ids.append(station_id)
        total_rows += station_record["row_count"]
        total_nonempty_payloads += station_record["nonempty_payload_count"]
        payload_counter.update(station_record["payload_counter"])
        payload_lengths.extend(station_record["payload_lengths"])
        detection_modes.update(station_record["detection_modes"])
        cooccurrence_station_counts.update(station_record["cooccurrence_station_counts"])
        per_station_summary.append(
            {
                "station_id": station_id,
                "raw_input_path": station_record["raw_input_path"],
                "detection_modes": station_record["detection_modes"],
                "row_count": station_record["row_count"],
                "nonempty_payload_count": station_record["nonempty_payload_count"],
                "distinct_payload_examples": station_record["distinct_payload_examples"],
                "cooccurring_supported_identifiers": station_record["cooccurring_supported_identifiers"],
            }
        )
        if len(examples) < max_stations * max_rows_per_station:
            remaining = (max_stations * max_rows_per_station) - len(examples)
            if len({item["station_id"] for item in examples}) < max_stations:
                examples.extend(station_record["examples"][:remaining])

    distinct_payloads = sorted(payload_counter)
    station_ids_sorted = sorted(station_ids)
    structural_observations = _build_structural_observations(
        identifier=identifier,
        payload_counter=payload_counter,
        payload_lengths=payload_lengths,
        detection_modes=detection_modes,
        cooccurrence_station_counts=cooccurrence_station_counts,
    )

    return {
        "identifier": identifier,
        "raw_inputs_directory": raw_inputs_dir.as_posix(),
        "station_count": len(station_ids_sorted),
        "station_ids": station_ids_sorted,
        "row_count": total_rows,
        "nonempty_payload_row_count": total_nonempty_payloads,
        "distinct_payload_count": len(distinct_payloads),
        "distinct_payload_examples": distinct_payloads[:20],
        "example_rows": examples,
        "detection_mode_counts": dict(sorted(detection_modes.items())),
        "station_summaries": per_station_summary,
        "structural_observations": structural_observations,
    }


def _scan_station_frame(
    *,
    frame: pd.DataFrame,
    raw_input_path: Path,
    station_id: str,
    identifier: str,
    max_rows_per_station: int,
) -> dict[str, Any]:
    detection_modes: list[str] = []
    payload_counter: Counter[str] = Counter()
    payload_lengths: list[int] = []
    examples: list[dict[str, Any]] = []
    row_count = 0
    nonempty_payload_count = 0
    cooccurrence_station_counts: Counter[str] = Counter()
    cooccurring_supported_identifiers: list[str] = []

    if identifier in frame.columns:
        detection_modes.append("column_name")
        series = frame[identifier]
        mask = _nonempty_mask(series)
        indexes = list(frame.index[mask])
        row_count += len(indexes)
        nonempty_payload_count += len(indexes)
        for index in indexes:
            payload = _stringify_value(series.loc[index])
            payload_counter[payload] += 1
            payload_lengths.append(len(payload))
        for column in COOCCURRENCE_COLUMNS:
            if column in frame.columns and _nonempty_mask(frame.loc[mask, column]).any():
                cooccurrence_station_counts[column] += 1
                cooccurring_supported_identifiers.append(column)
        for index in indexes[:max_rows_per_station]:
            examples.append(
                {
                    "station_id": station_id,
                    "row_locator": _build_row_locator(frame.loc[index]),
                    "detection_mode": "column_name",
                    "identifier": identifier,
                    "payload": _stringify_value(series.loc[index]),
                    "context": _build_row_context(frame.loc[index], identifier),
                }
            )

    for raw_line_column in ("RAW_LINE", "raw_line"):
        if raw_line_column not in frame.columns:
            continue
        contains_mask = frame[raw_line_column].fillna("").astype(str).str.contains(identifier, regex=False)
        if not contains_mask.any():
            continue
        detection_modes.append("raw_line_token")
        indexes = list(frame.index[contains_mask])
        if identifier not in frame.columns:
            row_count += len(indexes)
        for index in indexes[:max_rows_per_station]:
            raw_line = _stringify_value(frame.loc[index, raw_line_column])
            examples.append(
                {
                    "station_id": station_id,
                    "row_locator": _build_row_locator(frame.loc[index]),
                    "detection_mode": "raw_line_token",
                    "identifier": identifier,
                    "payload": None,
                    "context": {
                        raw_line_column: _extract_substring_context(raw_line, identifier),
                    },
                }
            )

    return {
        "present": bool(detection_modes),
        "raw_input_path": raw_input_path.as_posix(),
        "detection_modes": detection_modes,
        "row_count": row_count,
        "nonempty_payload_count": nonempty_payload_count,
        "payload_counter": payload_counter,
        "payload_lengths": payload_lengths,
        "examples": examples,
        "distinct_payload_examples": sorted(payload_counter)[:10],
        "cooccurrence_station_counts": cooccurrence_station_counts,
        "cooccurring_supported_identifiers": sorted(cooccurring_supported_identifiers),
    }


def _build_structural_observations(
    *,
    identifier: str,
    payload_counter: Counter[str],
    payload_lengths: list[int],
    detection_modes: Counter[str],
    cooccurrence_station_counts: Counter[str],
) -> dict[str, Any]:
    distinct_payloads = sorted(payload_counter)
    all_payloads = list(payload_counter.elements())
    all_match_digit_quality = bool(all_payloads) and all(
        re.fullmatch(r"\d{3},[A-Z0-9]", payload) for payload in all_payloads
    )
    quality_suffixes = sorted({payload.split(",", 1)[1] for payload in all_payloads if "," in payload})
    payload_length_counter = Counter(payload_lengths)

    if payload_lengths:
        length_summary = {
            "min": min(payload_lengths),
            "median": statistics.median(payload_lengths),
            "max": max(payload_lengths),
        }
    else:
        length_summary = {"min": None, "median": None, "max": None}

    return {
        "identifier": identifier,
        "payload_length_summary": length_summary,
        "payload_length_distribution": dict(sorted(payload_length_counter.items())),
        "payload_lengths_appear_stable": len(set(payload_lengths)) <= 1 if payload_lengths else False,
        "appears_as_column_name": detection_modes.get("column_name", 0) > 0,
        "appears_as_embedded_raw_line_token": detection_modes.get("raw_line_token", 0) > 0,
        "all_nonempty_payloads_are_null_or_empty": not all_payloads,
        "all_payloads_match_digit_comma_quality_pattern": all_match_digit_quality,
        "observed_quality_suffixes": quality_suffixes,
        "distinct_payload_examples": distinct_payloads[:20],
        "payloads_always_include_comma_delimiter": bool(all_payloads) and all("," in payload for payload in all_payloads),
        "cooccurring_supported_identifier_station_counts": dict(sorted(cooccurrence_station_counts.items())),
    }


def _build_parser_classification(
    *,
    identifier: str,
    spec_presence: dict[str, Any],
) -> dict[str, Any]:
    field_rule = get_field_rule(identifier)
    return {
        "identifier": identifier,
        "looks_like_three_character_uppercase_token": bool(re.fullmatch(r"[A-Z0-9]{3}", identifier)),
        "is_valid_section_identifier_token": is_valid_section_identifier_token(identifier),
        "is_valid_repeated_identifier": is_valid_repeated_identifier(identifier),
        "is_valid_eqd_identifier": is_valid_eqd_identifier(identifier),
        "is_valid_identifier": is_valid_identifier(identifier),
        "get_field_rule_returns_none": field_rule is None,
        "known_identifiers_contains_identifier": identifier in KNOWN_IDENTIFIERS,
        "appears_in_committed_spec_or_rule_text": spec_presence["appears_in_committed_spec_or_rule_text"],
        "syntactic_assessment": _syntactic_assessment(identifier=identifier, field_rule=field_rule),
    }


def _build_relationship_to_cleaning(
    *,
    station_results: pd.DataFrame | None,
    station_ids: list[str],
) -> dict[str, Any]:
    if station_results is None or not station_ids:
        return {
            "station_results_available": station_results is not None,
            "stations_with_identifier_in_station_results": 0,
            "station_success_count": 0,
            "station_failure_count": 0,
            "row_parity_station_count": 0,
            "notes": "station_results.csv was not available or no stations contained the identifier.",
        }

    filtered = station_results[station_results["station_id"].isin(station_ids)].copy()
    success_count = int((filtered["status"] == "success").sum())
    failure_count = len(filtered) - success_count
    row_parity_count = int((filtered["input_rows"] == filtered["output_rows"]).sum())
    return {
        "station_results_available": True,
        "stations_with_identifier_in_station_results": len(filtered),
        "station_success_count": success_count,
        "station_failure_count": failure_count,
        "row_parity_station_count": row_parity_count,
        "row_parity_holds_for_all_matching_stations": row_parity_count == len(filtered),
        "matching_station_statuses": filtered[["station_id", "status", "input_rows", "output_rows"]]
        .sort_values(["station_id"])
        .to_dict(orient="records"),
    }


def _investigate_aw_identifiers(
    *,
    raw_inputs_dir: Path,
    station_results: pd.DataFrame | None,
) -> dict[str, Any]:
    notes: dict[str, Any] = {
        "documented_supported_aw_identifiers": ["AW1", "AW2", "AW3", "AW4"],
        "parser_allows_aw_range": "AW1-AW4",
        "identifiers": {},
    }
    for identifier in AW_IDENTIFIERS:
        matching_stations: list[dict[str, Any]] = []
        for path in sorted(item for item in raw_inputs_dir.iterdir() if item.is_file()):
            station_id = _station_id_from_path(path)
            frame = _read_raw_input(path)
            if identifier not in frame.columns:
                continue
            mask = _nonempty_mask(frame[identifier])
            if not mask.any():
                continue
            matching_stations.append(
                {
                    "station_id": station_id,
                    "raw_input_path": path.relative_to(raw_inputs_dir.parent).as_posix(),
                    "nonnull_row_count": int(mask.sum()),
                    "payload_examples": [
                        _stringify_value(value)
                        for value in frame.loc[mask, identifier].head(5).tolist()
                    ],
                }
            )
        notes["identifiers"][identifier] = {
            "is_valid_identifier": is_valid_identifier(identifier),
            "is_valid_repeated_identifier": is_valid_repeated_identifier(identifier),
            "get_field_rule_returns_none": get_field_rule(identifier) is None,
            "appears_as_raw_column": bool(matching_stations),
            "matching_station_count": len(matching_stations),
            "matching_stations": matching_stations,
            "assessment": (
                "Malformed repeated identifier relative to the documented/parser-supported AW1-AW4 range."
                if matching_stations
                else "Not observed in this bundle."
            ),
        }

    affected_station_ids = sorted(
        {
            station["station_id"]
            for identifier_data in notes["identifiers"].values()
            for station in identifier_data["matching_stations"]
        }
    )
    if station_results is not None and affected_station_ids:
        filtered = station_results[station_results["station_id"].isin(affected_station_ids)].copy()
        notes["relationship_to_station_results"] = filtered[
            ["station_id", "status", "input_rows", "output_rows"]
        ].sort_values(["station_id"]).to_dict(orient="records")
    else:
        notes["relationship_to_station_results"] = []

    return notes


def _build_summary(
    *,
    identifier: str,
    bundle_presence: dict[str, Any],
    spec_presence: dict[str, Any],
    relationship: dict[str, Any],
) -> dict[str, Any]:
    return {
        "identifier": identifier,
        "appears_in_committed_specs": spec_presence["appears_in_committed_spec_or_rule_text"],
        "station_count": bundle_presence["station_count"],
        "row_count": bundle_presence["row_count"],
        "distinct_payload_count": bundle_presence["distinct_payload_count"],
        "payload_lengths_appear_stable": bundle_presence["structural_observations"]["payload_lengths_appear_stable"],
        "row_parity_holds_for_all_matching_stations": relationship.get(
            "row_parity_holds_for_all_matching_stations",
            False,
        ),
    }


def _build_interpretation(
    *,
    identifier: str,
    spec_presence: dict[str, Any],
    bundle_presence: dict[str, Any],
) -> str:
    if identifier == "HL1":
        return REQUIRED_CONCLUSION
    if spec_presence["appears_in_committed_spec_or_rule_text"]:
        return (
            f"{identifier} appears in committed repository text and in the validation "
            "bundle. This report documents observed raw payloads without changing parser behavior."
        )
    if bundle_presence["station_count"] == 0:
        return f"{identifier} was not observed in the scanned validation raw inputs."
    return (
        f"{identifier} appears in the validation bundle but was not confirmed in the "
        "committed repository spec/rule text searched by this diagnostic report."
    )


def _build_recommendation(*, identifier: str) -> str:
    if identifier == "HL1":
        return (
            "Keep HL1 as an explicit strict-parse diagnostic exclusion until separate "
            "documentation support or upstream NOAA evidence justifies parser support."
        )
    return (
        f"Preserve {identifier} as a diagnostic finding unless a separate spec-backed "
        "change adds support."
    )


def _render_markdown(report: dict[str, Any]) -> str:
    spec_presence = report["presence_in_repository_specs"]
    bundle_presence = report["presence_in_100_station_validation_bundle"]
    structural = report["structural_observations"]
    parser_classification = report["parser_classification"]
    relationship = report["relationship_to_successful_cleaning"]
    aw_notes = report["aw5_aw6_notes"]
    lines = [
        "# HL1 Investigation" if report["identifier"] == "HL1" else f"# {report['identifier']} Investigation",
        "",
        "## Purpose",
        "",
        report["purpose"],
        "",
        "## Summary",
        "",
        f"- Identifier: `{report['identifier']}`",
        f"- Stations containing `{report['identifier']}`: {bundle_presence['station_count']}",
        f"- Rows containing `{report['identifier']}`: {bundle_presence['row_count']}",
        f"- Appears in committed repo spec/rule text: {'yes' if spec_presence['appears_in_committed_spec_or_rule_text'] else 'no'}",
        f"- Station failures among matching stations: {relationship.get('station_failure_count', 0)}",
        f"- Row parity among matching stations: {'all matching stations preserved input/output row parity' if relationship.get('row_parity_holds_for_all_matching_stations') else 'not established for all matching stations'}",
        "",
        "## Presence in repository specs",
        "",
        f"- Searched roots: {', '.join(spec_presence['searched_roots'])}",
        f"- Searched files: {spec_presence['searched_file_count']}",
        f"- Exact `{report['identifier']}` hits: {spec_presence['exact_match_count']}",
    ]
    if spec_presence["exact_match_hits"]:
        for hit in spec_presence["exact_match_hits"]:
            lines.append(
                f"- {hit['path']}:{hit['line_number']} -> `{hit['line_text']}`"
            )
    else:
        lines.append(f"- No exact committed text hits for `{report['identifier']}` were found.")

    lines.extend(
        [
            "",
            "## Presence in 100-station validation bundle",
            "",
            f"- Detection modes: {bundle_presence['detection_mode_counts']}",
            f"- Distinct payload examples: {', '.join(f'`{value}`' for value in bundle_presence['distinct_payload_examples']) or 'none'}",
            f"- Matching station ids: {', '.join(f'`{value}`' for value in bundle_presence['station_ids']) or 'none'}",
            "",
            "## Raw examples",
            "",
        ]
    )
    if bundle_presence["example_rows"]:
        for example in bundle_presence["example_rows"]:
            locator = ", ".join(f"{key}={value}" for key, value in example["row_locator"].items())
            context = ", ".join(
                f"{key}={value}" for key, value in example["context"].items() if value not in ("", None)
            )
            payload_text = f", payload=`{example['payload']}`" if example["payload"] is not None else ""
            lines.append(
                f"- station `{example['station_id']}` ({locator}) [{example['detection_mode']}]"
                f"{payload_text}; {context}"
            )
    else:
        lines.append(f"- `{report['identifier']}` was not found in the scanned raw inputs.")

    lines.extend(
        [
            "",
            "## Structural observations",
            "",
            f"- Appears as raw column name: {'yes' if structural['appears_as_column_name'] else 'no'}",
            f"- Appears as embedded raw-line token: {'yes' if structural['appears_as_embedded_raw_line_token'] else 'no'}",
            f"- Payload length summary: min={structural['payload_length_summary']['min']}, median={structural['payload_length_summary']['median']}, max={structural['payload_length_summary']['max']}",
            f"- Payload lengths appear stable: {'yes' if structural['payload_lengths_appear_stable'] else 'no'}",
            f"- All payloads match `DDD,Q`-style pattern: {'yes' if structural['all_payloads_match_digit_comma_quality_pattern'] else 'no'}",
            f"- Observed quality suffixes: {', '.join(f'`{value}`' for value in structural['observed_quality_suffixes']) or 'none'}",
            f"- Co-occurring supported identifiers by station count: {structural['cooccurring_supported_identifier_station_counts']}",
            f"- All observed payloads empty/null: {'yes' if structural['all_nonempty_payloads_are_null_or_empty'] else 'no'}",
            "",
            "## Parser classification",
            "",
            f"- Superficially NOAA-style 3-character token: {'yes' if parser_classification['looks_like_three_character_uppercase_token'] else 'no'}",
            f"- `is_valid_identifier(\"{report['identifier']}\")`: {parser_classification['is_valid_identifier']}",
            f"- `get_field_rule(\"{report['identifier']}\") is None`: {parser_classification['get_field_rule_returns_none']}",
            f"- `KNOWN_IDENTIFIERS` contains `{report['identifier']}`: {parser_classification['known_identifiers_contains_identifier']}",
            f"- `is_valid_section_identifier_token(\"{report['identifier']}\")`: {parser_classification['is_valid_section_identifier_token']}",
            f"- `is_valid_repeated_identifier(\"{report['identifier']}\")`: {parser_classification['is_valid_repeated_identifier']}",
            f"- `is_valid_eqd_identifier(\"{report['identifier']}\")`: {parser_classification['is_valid_eqd_identifier']}",
            f"- Assessment: {parser_classification['syntactic_assessment']}",
            "",
            "## Relationship to successful cleaning",
            "",
            f"- Matching stations in `station_results.csv`: {relationship.get('stations_with_identifier_in_station_results', 0)}",
            f"- Matching station successes: {relationship.get('station_success_count', 0)}",
            f"- Matching station failures: {relationship.get('station_failure_count', 0)}",
            f"- Matching stations with input/output row parity: {relationship.get('row_parity_station_count', 0)}",
        ]
    )

    lines.extend(
        [
            "",
            "## AW5/AW6 notes",
            "",
            f"- Documented/parser-supported AW range: {aw_notes['parser_allows_aw_range']}",
        ]
    )
    for identifier, details in aw_notes["identifiers"].items():
        lines.append(
            f"- `{identifier}`: appears_as_raw_column={details['appears_as_raw_column']}, "
            f"is_valid_identifier={details['is_valid_identifier']}, "
            f"is_valid_repeated_identifier={details['is_valid_repeated_identifier']}, "
            f"matching_station_count={details['matching_station_count']}; {details['assessment']}"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            report["interpretation"],
            "",
            "## Recommendation",
            "",
            report["recommendation"],
        ]
    )
    if report["required_conclusion"]:
        lines.extend(["", report["required_conclusion"]])
    return "\n".join(lines) + "\n"


def _syntactic_assessment(*, identifier: str, field_rule: Any) -> str:
    if field_rule is not None:
        return f"{identifier} is parser-supported."
    if re.fullmatch(r"[A-Z0-9]{3}", identifier):
        return (
            f"{identifier} superficially looks like a 3-character NOAA-style token, "
            "but it does not map to a documented/generated rule in this repository."
        )
    return f"{identifier} does not match the repository's known identifier patterns."


def _build_row_locator(row: pd.Series) -> dict[str, Any]:
    locator: dict[str, Any] = {}
    for column in ROW_LOCATOR_COLUMNS:
        if column in row.index:
            value = _stringify_value(row[column])
            if value:
                locator[column] = value
    return locator


def _build_row_context(row: pd.Series, identifier: str) -> dict[str, Any]:
    context: dict[str, Any] = {}
    for column in (identifier,) + COOCCURRENCE_COLUMNS + AW_IDENTIFIERS:
        if column in row.index:
            value = _stringify_value(row[column])
            if value:
                context[column] = value
    return context


def _extract_substring_context(raw_line: str, identifier: str) -> str:
    index = raw_line.find(identifier)
    if index < 0:
        return raw_line[:80]
    start = max(0, index - 20)
    end = min(len(raw_line), index + len(identifier) + 20)
    return raw_line[start:end]


def _read_raw_input(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    if path.name.lower().endswith(".csv.gz"):
        return pd.read_csv(path, dtype=str, low_memory=False, compression="gzip")
    return pd.read_csv(path, dtype=str, low_memory=False)


def _nonempty_mask(series: pd.Series) -> pd.Series:
    text = series.fillna("").astype(str)
    return text.str.len() > 0


def _stringify_value(value: Any) -> str:
    if pd.isna(value):
        return ""
    return str(value)


def _now_utc_isoformat() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
