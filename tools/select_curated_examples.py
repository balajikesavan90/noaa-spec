#!/usr/bin/env python3
"""Select a compact, reviewer-facing subset from mined NOAA-Spec examples."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


DEFAULT_INPUT = Path("artifacts/example_row_mining/all_matches.csv")
DEFAULT_OUTPUT_DIR = Path("artifacts/curated_examples")
DEFAULT_TARGET_COUNT = 18

OUTPUT_FIELDS = [
    "example_id",
    "station_id",
    "datetime",
    "noaa_source_url",
    "noaa_csv_line_number",
    "field_families",
    "rule_behaviors",
    "patterns",
    "provenance_status",
    "selection_reason",
    "tmp_value",
    "vis_value",
    "wnd_value",
    "aa1_value",
    "raw_row",
]

PATTERN_LABELS = {
    "aa1_missing_sentinel": "AA1 precipitation amount sentinel",
    "aa1_valid_precip": "valid AA1 precipitation amount",
    "mixed_validity": "mixed valid and nullified fields",
    "multi_family_informative": "multi-family row context",
    "tmp_missing_sentinel": "TMP documented missing sentinel",
    "vis_missing_sentinel": "VIS documented missing sentinel",
    "wnd_fully_missing": "WND fully missing token",
    "wnd_missing_dir_valid_spd": "WND direction context with valid speed",
}

BEHAVIOR_LABELS = {
    "aa1_amount_sentinel": "precipitation amount sentinel is nullified while QC/context remain inspectable",
    "aa1_period_sentinel": "precipitation period sentinel is handled independently from amount",
    "calm_wind_context": "calm wind type code changes how direction 999 is interpreted",
    "estimated_qc_preserved": "estimated NOAA QC code remains visible",
    "four_family_context": "TMP, VIS, WND, and AA1 appear together for cross-field inspection",
    "mixed_validity": "valid fields are preserved while sentinel fields are nullified",
    "valid_precip_zero": "AA1 amount 0000 is preserved as a real zero, not a missing value",
    "valid_wind_speed_with_missing_direction": "wind speed remains usable when direction context is non-directional",
    "vis_missing_sentinel": "visibility sentinel 999999 is nullified",
    "wnd_fully_missing": "fully missing wind token is nullified without dropping the row",
    "tmp_missing_sentinel": "temperature sentinel +9999/9999 is nullified",
}

VERIFIED_NOAA_CSV_LINE_NUMBERS = {
    ("55696099999", "1975-01-15T06:00:00", "-0010,1", "020000,1,N,9", "999,1,C,0000,1", "06,9999,2,9"): 70,
    ("63250099999", "1978-07-10T15:00:00", "+0290,1", "020000,1,N,9", "200,1,N,0051,1", "99,9999,2,9"): 18,
    ("63250099999", "1978-07-22T03:00:00", "+9999,9", "010000,1,N,9", "999,1,C,0000,1", ""): 29,
    ("63250099999", "1978-08-20T03:00:00", "+0260,1", "010000,1,N,9", "999,1,C,0000,1", "99,0000,9,1"): 63,
    ("63250099999", "1978-09-02T06:00:00", "+0280,1", "030000,1,N,9", "999,9,9,9999,9", ""): 85,
    ("63250099999", "1978-12-11T15:00:00", "+0290,1", "999999,9,N,9", "090,1,N,0051,1", "99,0000,9,1"): 239,
    ("63250099999", "1978-12-30T15:00:00", "+9999,9", "035000,1,N,9", "050,1,N,0031,1", "99,0000,9,1"): 269,
    ("63250099999", "1982-02-10T03:00:00", "+0268,1", "020000,1,N,9", "999,1,C,0000,1", "06,0000,9,1"): 112,
    ("46737399999", "1988-11-14T22:00:00", "+0200,1", "003200,1,N,1", "030,1,N,0015,1", "99,9999,2,9"): 3713,
    ("72547299999", "1997-02-13T12:53:00", "-0180,1", "008046,1,N,1", "999,1,C,0000,1", ""): 80,
    ("72547299999", "1997-02-25T14:53:00", "+9999,9", "016093,1,N,1", "220,1,N,0067,1", ""): 354,
    ("72547299999", "1997-06-11T13:53:00", "+9999,9", "999999,9,N,9", "999,9,9,9999,9", ""): 2358,
    ("72547299999", "1997-06-14T00:53:00", "+0250,1", "999999,9,N,9", "999,9,9,9999,9", ""): 2411,
    ("72547299999", "1998-04-22T17:53:00", "+0180,1", "999999,9,N,9", "999,9,9,9999,9", "06,0000,9,1"): 2608,
    ("72547299999", "1998-04-23T17:53:00", "+0210,1", "999999,9,N,9", "280,1,N,0041,1", "06,0000,9,1"): 2632,
    ("72214904899", "2006-01-11T05:59:00", "+9999,9", "999999,9,9,9", "999,9,9,9999,9", ""): 733,
    ("72214904899", "2014-02-21T11:55:00", "-0015,5", "011265,5,N,5", "260,5,N,0139,5", "24,9999,1,9"): 3616,
    ("72344154921", "2014-07-31T11:55:00", "+0161,5", "016093,5,N,5", "999,9,C,0000,5", "24,9999,1,9"): 15253,
}


@dataclass(frozen=True)
class Candidate:
    key: tuple[str, str, str, str]
    station_id: str
    datetime: str
    noaa_source_url: str
    noaa_csv_line_number: int | None
    source_pool_line_number: int
    tmp_value: str
    vis_value: str
    wnd_value: str
    aa1_value: str
    raw_row: str
    patterns: tuple[str, ...]
    field_families: tuple[str, ...]
    rule_behaviors: tuple[str, ...]
    provenance_status: str
    base_score: int


def _split_token(token: str) -> list[str]:
    return token.split(",") if token else []


def _field_families(row: dict[str, str]) -> tuple[str, ...]:
    families = []
    for family, column in (
        ("TMP", "tmp_value"),
        ("VIS", "vis_value"),
        ("WND", "wnd_value"),
        ("AA1", "aa1_value"),
    ):
        if row.get(column):
            families.append(family)
    return tuple(families)


def _rule_behaviors(row: dict[str, str], patterns: set[str]) -> tuple[str, ...]:
    behaviors: set[str] = set()

    tmp = row.get("tmp_value", "")
    vis = row.get("vis_value", "")
    wnd = row.get("wnd_value", "")
    aa1 = row.get("aa1_value", "")

    if "tmp_missing_sentinel" in patterns or tmp.startswith(("+9999", "9999")):
        behaviors.add("tmp_missing_sentinel")
    if "vis_missing_sentinel" in patterns or vis.startswith("999999"):
        behaviors.add("vis_missing_sentinel")
    if "wnd_fully_missing" in patterns or wnd == "999,9,9,9999,9":
        behaviors.add("wnd_fully_missing")
    if "mixed_validity" in patterns:
        behaviors.add("mixed_validity")
    if "multi_family_informative" in patterns or all(row.get(c) for c in ("tmp_value", "vis_value", "wnd_value", "aa1_value")):
        behaviors.add("four_family_context")
    if "aa1_valid_precip" in patterns:
        behaviors.add("valid_precip_zero")

    wnd_parts = _split_token(wnd)
    if len(wnd_parts) >= 5 and wnd_parts[0] == "999":
        if wnd_parts[2] == "C":
            behaviors.add("calm_wind_context")
        if wnd_parts[3] != "9999":
            behaviors.add("valid_wind_speed_with_missing_direction")

    aa1_parts = _split_token(aa1)
    if len(aa1_parts) >= 4:
        if aa1_parts[0] == "99":
            behaviors.add("aa1_period_sentinel")
        if aa1_parts[1] == "9999" or "aa1_missing_sentinel" in patterns:
            behaviors.add("aa1_amount_sentinel")
        if aa1_parts[1] == "0000" and "aa1_missing_sentinel" not in patterns:
            behaviors.add("valid_precip_zero")

    token_text = ",".join((tmp, vis, wnd, aa1))
    if ",5" in token_text:
        behaviors.add("estimated_qc_preserved")

    return tuple(sorted(behaviors))


def _provenance_status(row: dict[str, str]) -> str:
    if row.get("station_id", "") and row.get("date", ""):
        return "NOAA station-year source URL and CSV line number recorded; upstream checksum not recorded"
    return "NOAA source URL unavailable; upstream retrieval not recorded"


def _noaa_source_url(*, station_id: str, datetime: str) -> str:
    year = datetime[:4]
    if not station_id or len(year) != 4 or not year.isdigit():
        return ""
    return f"https://www.ncei.noaa.gov/data/global-hourly/access/{year}/{station_id}.csv"


def _verified_noaa_csv_line_number(row: dict[str, str]) -> int | None:
    key = (
        row.get("station_id", ""),
        row.get("date", ""),
        row.get("tmp_value", ""),
        row.get("vis_value", ""),
        row.get("wnd_value", ""),
        row.get("aa1_value", ""),
    )
    return VERIFIED_NOAA_CSV_LINE_NUMBERS.get(key)


def _read_candidates(path: Path) -> list[Candidate]:
    grouped: dict[tuple[str, str, str, str], dict[str, object]] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            key = (
                row["station_id"],
                row["line_number"],
                row["date"],
                row["raw_row"],
            )
            entry = grouped.setdefault(key, {"row": row, "patterns": set()})
            entry["patterns"].add(row["pattern_name"])  # type: ignore[index, union-attr]

    candidates = []
    for key, entry in grouped.items():
        row = entry["row"]  # type: ignore[assignment]
        patterns = tuple(sorted(entry["patterns"]))  # type: ignore[arg-type]
        families = _field_families(row)  # type: ignore[arg-type]
        behaviors = _rule_behaviors(row, set(patterns))  # type: ignore[arg-type]
        station_id = str(row.get("station_id", ""))  # type: ignore[union-attr]
        datetime = str(row.get("date", ""))  # type: ignore[union-attr]
        noaa_source_url = _noaa_source_url(station_id=station_id, datetime=datetime)
        noaa_csv_line_number = _verified_noaa_csv_line_number(row)  # type: ignore[arg-type]
        source_pool_line_number = int(str(row.get("line_number", "0")))  # type: ignore[union-attr]
        base_score = (
            20 * len(patterns)
            + 8 * len(behaviors)
            + 5 * len(families)
            + (5 if noaa_source_url else 0)
            + (4 if len(families) >= 4 else 0)
        )
        candidates.append(
            Candidate(
                key=key,
                station_id=station_id,
                datetime=datetime,
                noaa_source_url=noaa_source_url,
                noaa_csv_line_number=noaa_csv_line_number,
                source_pool_line_number=source_pool_line_number,
                tmp_value=str(row.get("tmp_value", "")),  # type: ignore[union-attr]
                vis_value=str(row.get("vis_value", "")),  # type: ignore[union-attr]
                wnd_value=str(row.get("wnd_value", "")),  # type: ignore[union-attr]
                aa1_value=str(row.get("aa1_value", "")),  # type: ignore[union-attr]
                raw_row=str(row.get("raw_row", "")),  # type: ignore[union-attr]
                patterns=patterns,
                field_families=families,
                rule_behaviors=behaviors,
                provenance_status=_provenance_status(row),  # type: ignore[arg-type]
                base_score=base_score,
            )
        )
    return sorted(candidates, key=_candidate_tie_key)


def _candidate_tie_key(candidate: Candidate) -> tuple[object, ...]:
    return (
        candidate.datetime,
        candidate.station_id,
        candidate.source_pool_line_number,
        candidate.raw_row,
    )


def _marginal_score(
    candidate: Candidate,
    selected: list[Candidate],
    covered_patterns: set[str],
    covered_behaviors: set[str],
    covered_families: set[str],
    covered_stations: set[str],
) -> tuple[int, tuple[object, ...]]:
    pattern_counts = Counter(pattern for item in selected for pattern in item.patterns)
    behavior_counts = Counter(behavior for item in selected for behavior in item.rule_behaviors)
    family_counts = Counter(family for item in selected for family in item.field_families)

    score = candidate.base_score
    score += 120 * len(set(candidate.patterns) - covered_patterns)
    score += 35 * len(set(candidate.rule_behaviors) - covered_behaviors)
    score += 20 * len(set(candidate.field_families) - covered_families)
    score += 45 if candidate.station_id not in covered_stations else 0

    # Reward underrepresented coverage, then softly penalize near-duplicates.
    score += sum(max(0, 3 - pattern_counts[pattern]) * 8 for pattern in candidate.patterns)
    score += sum(max(0, 2 - behavior_counts[behavior]) * 4 for behavior in candidate.rule_behaviors)
    score += sum(max(0, 4 - family_counts[family]) for family in candidate.field_families)

    same_station = sum(1 for item in selected if item.station_id == candidate.station_id)
    same_pattern_set = sum(1 for item in selected if item.patterns == candidate.patterns)
    same_behavior_set = sum(1 for item in selected if item.rule_behaviors == candidate.rule_behaviors)
    same_station_pattern_set = sum(
        1
        for item in selected
        if item.station_id == candidate.station_id and item.patterns == candidate.patterns
    )
    same_station_behavior_set = sum(
        1
        for item in selected
        if item.station_id == candidate.station_id
        and item.rule_behaviors == candidate.rule_behaviors
    )
    score -= 24 * same_station
    score -= 45 * same_pattern_set
    score -= 25 * same_behavior_set
    score -= 60 * same_station_pattern_set
    score -= 60 * same_station_behavior_set

    return (score, _candidate_tie_key(candidate))


def select_candidates(candidates: list[Candidate], target_count: int) -> list[Candidate]:
    if target_count <= 0:
        return []

    selected: list[Candidate] = []
    remaining = list(candidates)
    covered_patterns: set[str] = set()
    covered_behaviors: set[str] = set()
    covered_families: set[str] = set()
    covered_stations: set[str] = set()

    available_patterns = sorted({pattern for item in candidates for pattern in item.patterns})

    def add(candidate: Candidate) -> None:
        selected.append(candidate)
        remaining.remove(candidate)
        covered_patterns.update(candidate.patterns)
        covered_behaviors.update(candidate.rule_behaviors)
        covered_families.update(candidate.field_families)
        covered_stations.add(candidate.station_id)

    for pattern in available_patterns:
        if len(selected) >= target_count:
            break
        choices = [item for item in remaining if pattern in item.patterns]
        if not choices:
            continue
        best = max(
            choices,
            key=lambda item: _marginal_score(
                item,
                selected,
                covered_patterns,
                covered_behaviors,
                covered_families,
                covered_stations,
            ),
        )
        add(best)

    while remaining and len(selected) < target_count:
        best = max(
            remaining,
            key=lambda item: _marginal_score(
                item,
                selected,
                covered_patterns,
                covered_behaviors,
                covered_families,
                covered_stations,
            ),
        )
        add(best)

    return sorted(selected, key=_candidate_tie_key)


def _selection_reason(candidate: Candidate) -> str:
    labels = [PATTERN_LABELS.get(pattern, pattern.replace("_", " ")) for pattern in candidate.patterns]
    behaviors = [BEHAVIOR_LABELS.get(behavior, behavior.replace("_", " ")) for behavior in candidate.rule_behaviors]
    return "; ".join(labels + behaviors)


def _row(candidate: Candidate, index: int) -> dict[str, str]:
    return {
        "example_id": f"CE{index:02d}",
        "station_id": candidate.station_id,
        "datetime": candidate.datetime,
        "noaa_source_url": candidate.noaa_source_url,
        "noaa_csv_line_number": (
            str(candidate.noaa_csv_line_number)
            if candidate.noaa_csv_line_number is not None
            else ""
        ),
        "field_families": " | ".join(candidate.field_families),
        "rule_behaviors": " | ".join(candidate.rule_behaviors),
        "patterns": " | ".join(candidate.patterns),
        "provenance_status": candidate.provenance_status,
        "selection_reason": _selection_reason(candidate),
        "tmp_value": candidate.tmp_value,
        "vis_value": candidate.vis_value,
        "wnd_value": candidate.wnd_value,
        "aa1_value": candidate.aa1_value,
        "raw_row": candidate.raw_row,
    }


def _write_csv(rows: list[dict[str, str]], output_path: Path) -> None:
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _md_escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def _md_link(label: str, url: str) -> str:
    if not url:
        return ""
    return f"[{label}]({url})"


def _write_curated_markdown(rows: list[dict[str, str]], output_path: Path) -> None:
    lines = [
        "# Curated NOAA-Spec Cleaning Examples",
        "",
        "This table is generated from the existing mined example pool. It is a compact reviewer-facing view, not a new data-mining pass and not a claim of exhaustive NOAA coverage.",
        "",
        "| Example | Station / datetime | NOAA source | Families | Rule behaviors | Provenance | Why selected |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {example_id} | `{station_id}` / `{datetime}` | {noaa_source_url} | {field_families} | {rule_behaviors} | {provenance_status} | {selection_reason} |".format(
                **{
                    key: (
                        _md_link("NOAA CSV", value)
                        if key == "noaa_source_url"
                        else _md_escape(value)
                    )
                    for key, value in row.items()
                }
            )
        )
    lines.append("")
    output_path.write_text("\n".join(lines), encoding="utf-8")


def _write_summary(rows: list[dict[str, str]], output_path: Path, input_path: Path) -> None:
    pattern_counts = Counter(pattern for row in rows for pattern in row["patterns"].split(" | ") if pattern)
    behavior_counts = Counter(behavior for row in rows for behavior in row["rule_behaviors"].split(" | ") if behavior)
    family_counts = Counter(family for row in rows for family in row["field_families"].split(" | ") if family)
    station_counts = Counter(row["station_id"] for row in rows)

    lines = [
        "# Curated Example Selection Summary",
        "",
        f"Generated from `{input_path}` by `tools/select_curated_examples.py`.",
        "",
        "Selection is deterministic. Rows are aggregated by station, source-pool row key, timestamp, and raw token summary; duplicate mined pattern hits for the same source row become one candidate with multiple pattern labels. The selector first ensures each available mined pattern is represented where possible, then greedily adds rows that improve pattern, rule-behavior, field-family, and station coverage while penalizing near-duplicates.",
        "",
        "Rerun the canonical repo artifact with:",
        "",
        "```bash",
        f"python3 tools/select_curated_examples.py --input {input_path} --output-dir {DEFAULT_OUTPUT_DIR} --target-count {len(rows)}",
        "```",
        "",
        f"Selected rows: {len(rows)}",
        "",
        "## Coverage",
        "",
        "| Dimension | Values |",
        "| --- | --- |",
        f"| Field families | {_format_counter(family_counts)} |",
        f"| Mined patterns | {_format_counter(pattern_counts)} |",
        f"| Rule behaviors | {_format_counter(behavior_counts)} |",
        f"| Stations | {_format_counter(station_counts)} |",
        "",
        "## Selected Rows",
        "",
        "| Example | NOAA source | Families | Failure / rule type | Provenance | Selection reason |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {example_id} | {noaa_source_url} | {field_families} | {rule_behaviors} | {provenance_status} | {selection_reason} |".format(
                **{
                    key: (
                        _md_link("NOAA CSV", value)
                        if key == "noaa_source_url"
                        else _md_escape(value)
                    )
                    for key, value in row.items()
                }
            )
        )
    lines.append("")
    output_path.write_text("\n".join(lines), encoding="utf-8")


def _format_counter(counter: Counter[str]) -> str:
    return ", ".join(f"{key} ({counter[key]})" for key in sorted(counter))


def run(input_path: Path, output_dir: Path, target_count: int) -> list[dict[str, str]]:
    candidates = _read_candidates(input_path)
    selected = select_candidates(candidates, target_count)
    rows = [_row(candidate, index) for index, candidate in enumerate(selected, start=1)]

    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(rows, output_dir / "curated_examples.csv")
    _write_curated_markdown(rows, output_dir / "curated_examples.md")
    _write_summary(rows, output_dir / "selection_summary.md", input_path)
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Select deterministic curated examples from the mined example pool."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Mined all_matches.csv path. Default: {DEFAULT_INPUT}",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory for generated curated artifacts. Default: {DEFAULT_OUTPUT_DIR}",
    )
    parser.add_argument(
        "--target-count",
        type=int,
        default=DEFAULT_TARGET_COUNT,
        help=f"Approximate curated row count. Default: {DEFAULT_TARGET_COUNT}",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = run(args.input, args.output_dir, args.target_count)
    print(f"Selected {len(rows)} curated examples into {args.output_dir}")


if __name__ == "__main__":
    main()
