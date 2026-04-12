#!/usr/bin/env python3
"""find_example_rows.py — Mine real NOAA ISD / Global Hourly Parquet rows for
reviewer-facing cleaning fixture candidates.

This script scans a local corpus of raw NOAA station Parquet files and identifies
rows that demonstrate edge-case patterns relevant to deterministic
sentinel-aware cleaning.  Each match is written out verbatim with provenance
metadata so candidates can be manually curated into small reproducible fixtures.

Patterns detected
-----------------
1.  tmp_missing_sentinel       TMP numeric part == +9999
2.  tmp_negative_sentinel      TMP numeric part == -9999  (unusual but possible)
3.  vis_missing_sentinel       VIS distance field == 999999
4.  wnd_calm_valid             WND direction 000, speed 0000
5.  wnd_missing_dir_valid_spd  WND direction 999, speed not 9999
6.  wnd_fully_missing          WND direction 999 AND speed 9999
7.  aa1_valid_precip           AA1 present; amount != 9999 and period != 99
8.  aa1_missing_sentinel       AA1 amount == 9999
9.  mixed_validity             >=1 valid core field AND >=1 sentinel core field
10. multi_family_informative   TMP + VIS + WND + AA1 all present and non-empty

Outputs (written to --outdir)
------------------------------
  all_matches.csv          all matched rows across all patterns
  pattern_<name>.csv       one CSV per pattern class (max --max-per-pattern rows)
  summary.csv              match counts by pattern
  report.md                human-readable mining summary

Input format
------------
Files must be Parquet (*.parquet).  Each file is read row-group by row-group
using pyarrow so peak memory stays bounded regardless of file size.

Usage
-----
    python tools/find_example_rows.py \\
        --root /media/balaji-kesavan/LaCie/NOAA_Data \\
        --outdir artifacts/example_row_mining \\
        --max-per-pattern 25

    # limit files for a quick smoke-test
    python tools/find_example_rows.py \\
        --root /media/balaji-kesavan/LaCie/NOAA_Data \\
        --outdir artifacts/example_row_mining \\
        --max-per-pattern 10 \\
        --max-files 500

Suggested workflow after running
---------------------------------
1.  Review summary.csv and report.md for a high-level overview.
2.  Open all_matches.csv (or per-pattern CSVs) to inspect candidates.
3.  Manually curate 1 main reviewer example with ~15–25 rows covering
    several distinct patterns.
4.  Keep the final fixture small and fully traceable using the
    source_file_path + line_number columns that appear in every output row.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import logging
import re
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Generator

import pyarrow.parquet as pq

# ---------------------------------------------------------------------------
# Logging — writes to stderr so stdout remains clean for any piping
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stderr,
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Minimum set of core columns required before we consider a CSV worth scanning
MIN_REQUIRED_COLS: frozenset[str] = frozenset({"TMP", "VIS", "WND"})

# All column names we care about extracting
INTEREST_COLS: frozenset[str] = frozenset({"TMP", "VIS", "WND", "AA1", "DATE", "STATION"})

# Normalised sentinel marker values (raw field token before first comma)
TMP_SENTINEL_POS = "+9999"       # documented positive missing sentinel
TMP_SENTINEL_NEG = "-9999"       # negative missing sentinel (unusual)
VIS_SENTINEL = "999999"          # 6-digit missing sentinel
WND_DIR_SENTINEL = "999"         # missing/unknown direction
WND_SPEED_SENTINEL = "9999"      # missing/unknown speed
WND_DIR_CALM = "000"             # calm wind direction
WND_SPEED_CALM = "0000"          # calm wind speed
AA_PERIOD_SENTINEL = "99"        # missing accumulation period
AA_AMOUNT_SENTINEL = "9999"      # missing precipitation amount

# Pattern name registry — order matters for output ordering
PATTERN_NAMES: list[str] = [
    "tmp_missing_sentinel",
    "tmp_negative_sentinel",
    "vis_missing_sentinel",
    "wnd_calm_valid",
    "wnd_missing_dir_valid_spd",
    "wnd_fully_missing",
    "aa1_valid_precip",
    "aa1_missing_sentinel",
    "mixed_validity",
    "multi_family_informative",
]

# Station-ID regex tries to extract 11-char WMO-like ids from file/dir names
_STATION_RE = re.compile(r"\b(\d{5,11})\b")

# Internal scan cap: collect up to this many raw matches before diversity
# downsampling to --max-per-pattern.  Keeps memory bounded.
_INTERNAL_CAP_MULTIPLIER = 40

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class Match:
    """Single matched row with full provenance."""

    pattern_name: str
    source_file_path: str
    station_id: str
    line_number: int
    datetime: str         # full ISO-8601 timestamp (e.g. 2006-01-02T15:00:00)
    raw_row: str          # key fields joined by | (tmp|vis|wnd|aa1|datetime)
    tmp_value: str
    vis_value: str
    wnd_value: str
    aa1_value: str
    reason: str


# Column names for the output CSVs
MATCH_FIELDNAMES: list[str] = list(Match.__dataclass_fields__)

# ---------------------------------------------------------------------------
# Field parsers
# ---------------------------------------------------------------------------


def parse_tmp(raw: str) -> dict[str, str]:
    """Parse a raw TMP token (e.g. '+0235,1') into component parts.

    Returns keys: numeric (e.g. '+0235'), qc (e.g. '1').
    Returns empty strings on unexpected shape.

    >>> parse_tmp('+9999,9')
    {'numeric': '+9999', 'qc': '9'}
    >>> parse_tmp('+0235,1')
    {'numeric': '+0235', 'qc': '1'}
    """
    parts = raw.strip().split(",")
    if len(parts) >= 2:
        return {"numeric": parts[0].strip(), "qc": parts[1].strip()}
    return {"numeric": "", "qc": ""}


def parse_vis(raw: str) -> dict[str, str]:
    """Parse a raw VIS token (e.g. '000100,1,N,1') into component parts.

    Returns keys: distance, quality, variability, var_qc.

    >>> parse_vis('999999,9,N,1')
    {'distance': '999999', 'quality': '9', 'variability': 'N', 'var_qc': '1'}
    """
    parts = raw.strip().split(",")
    keys = ["distance", "quality", "variability", "var_qc"]
    return {k: parts[i].strip() if i < len(parts) else "" for i, k in enumerate(keys)}


def parse_wnd(raw: str) -> dict[str, str]:
    """Parse a raw WND token (e.g. '210,1,N,0010,1') into component parts.

    Returns keys: direction, dir_qc, type_code, speed, speed_qc.

    >>> parse_wnd('000,1,N,0000,1')
    {'direction': '000', 'dir_qc': '1', 'type_code': 'N', 'speed': '0000', 'speed_qc': '1'}
    >>> parse_wnd('999,9,N,9999,9')
    {'direction': '999', 'dir_qc': '9', 'type_code': 'N', 'speed': '9999', 'speed_qc': '9'}
    """
    parts = raw.strip().split(",")
    keys = ["direction", "dir_qc", "type_code", "speed", "speed_qc"]
    return {k: parts[i].strip() if i < len(parts) else "" for i, k in enumerate(keys)}


def parse_aa1(raw: str) -> dict[str, str]:
    """Parse a raw AA1 token (e.g. '01,0007,9,1') into component parts.

    Returns keys: period, amount, condition, quality.

    >>> parse_aa1('01,0007,9,1')
    {'period': '01', 'amount': '0007', 'condition': '9', 'quality': '1'}
    >>> parse_aa1('24,9999,9,9')
    {'period': '24', 'amount': '9999', 'condition': '9', 'quality': '9'}
    """
    parts = raw.strip().split(",")
    keys = ["period", "amount", "condition", "quality"]
    return {k: parts[i].strip() if i < len(parts) else "" for i, k in enumerate(keys)}


# ---------------------------------------------------------------------------
# Validity helpers
# ---------------------------------------------------------------------------


def _tmp_is_valid(p: dict[str, str]) -> bool:
    """Return True if TMP has a non-sentinel numeric value."""
    return p["numeric"] not in ("", TMP_SENTINEL_POS, TMP_SENTINEL_NEG)


def _vis_is_valid(p: dict[str, str]) -> bool:
    """Return True if VIS distance is not the missing sentinel."""
    return p["distance"] not in ("", VIS_SENTINEL)


def _wnd_is_valid_speed(p: dict[str, str]) -> bool:
    """Return True if WND speed is not the missing sentinel."""
    return p["speed"] not in ("", WND_SPEED_SENTINEL)


def _wnd_is_valid_direction(p: dict[str, str]) -> bool:
    """Return True if WND direction is an actual bearing (not sentinel/calm)."""
    return p["direction"] not in ("", WND_DIR_SENTINEL, WND_DIR_CALM)


def _aa1_is_valid(p: dict[str, str]) -> bool:
    """Return True if AA1 has a non-sentinel period and amount."""
    return (
        p["period"] not in ("", AA_PERIOD_SENTINEL)
        and p["amount"] not in ("", AA_AMOUNT_SENTINEL)
    )


# ---------------------------------------------------------------------------
# Pattern detectors
# ---------------------------------------------------------------------------
# Each detector receives the parsed field dicts (may be empty dicts when the
# column is absent from the row) and returns (matched: bool, reason: str).


def detect_tmp_missing_sentinel(
    tmp: dict, vis: dict, wnd: dict, aa1: dict
) -> tuple[bool, str]:
    if tmp and tmp["numeric"] == TMP_SENTINEL_POS:
        return True, f"TMP numeric part is {TMP_SENTINEL_POS} (documented missing sentinel)"
    return False, ""


def detect_tmp_negative_sentinel(
    tmp: dict, vis: dict, wnd: dict, aa1: dict
) -> tuple[bool, str]:
    if tmp and tmp["numeric"] == TMP_SENTINEL_NEG:
        return True, f"TMP numeric part is {TMP_SENTINEL_NEG} (negative sentinel — unusual)"
    return False, ""


def detect_vis_missing_sentinel(
    tmp: dict, vis: dict, wnd: dict, aa1: dict
) -> tuple[bool, str]:
    if vis and vis["distance"] == VIS_SENTINEL:
        return True, f"VIS distance is {VIS_SENTINEL} (missing sentinel)"
    return False, ""


def detect_wnd_calm_valid(
    tmp: dict, vis: dict, wnd: dict, aa1: dict
) -> tuple[bool, str]:
    if wnd and wnd["direction"] == WND_DIR_CALM and wnd["speed"] == WND_SPEED_CALM:
        return True, "WND direction 000 + speed 0000 = calm wind, both fields valid"
    return False, ""


def detect_wnd_missing_dir_valid_spd(
    tmp: dict, vis: dict, wnd: dict, aa1: dict
) -> tuple[bool, str]:
    if wnd and wnd["direction"] == WND_DIR_SENTINEL and _wnd_is_valid_speed(wnd):
        return (
            True,
            f"WND direction 999 (missing/unknown) but speed {wnd['speed']} is valid",
        )
    return False, ""


def detect_wnd_fully_missing(
    tmp: dict, vis: dict, wnd: dict, aa1: dict
) -> tuple[bool, str]:
    if wnd and wnd["direction"] == WND_DIR_SENTINEL and wnd["speed"] == WND_SPEED_SENTINEL:
        return True, "WND direction 999 AND speed 9999 — fully missing wind observation"
    return False, ""


def detect_aa1_valid_precip(
    tmp: dict, vis: dict, wnd: dict, aa1: dict
) -> tuple[bool, str]:
    if aa1 and _aa1_is_valid(aa1):
        return (
            True,
            f"AA1 has valid period={aa1['period']}h amount={aa1['amount']}×0.1mm",
        )
    return False, ""


def detect_aa1_missing_sentinel(
    tmp: dict, vis: dict, wnd: dict, aa1: dict
) -> tuple[bool, str]:
    if aa1 and aa1.get("amount") == AA_AMOUNT_SENTINEL:
        return True, f"AA1 amount is {AA_AMOUNT_SENTINEL} (missing sentinel)"
    return False, ""


def detect_mixed_validity(
    tmp: dict, vis: dict, wnd: dict, aa1: dict
) -> tuple[bool, str]:
    """At least one valid core field AND at least one sentinel/missing core field."""
    valid_fields: list[str] = []
    sentinel_fields: list[str] = []

    # TMP
    if tmp:
        if _tmp_is_valid(tmp):
            valid_fields.append("TMP")
        elif tmp["numeric"] in (TMP_SENTINEL_POS, TMP_SENTINEL_NEG):
            sentinel_fields.append("TMP")
    # VIS
    if vis:
        if _vis_is_valid(vis):
            valid_fields.append("VIS")
        elif vis["distance"] == VIS_SENTINEL:
            sentinel_fields.append("VIS")
    # WND speed
    if wnd:
        if _wnd_is_valid_speed(wnd):
            valid_fields.append("WND_speed")
        elif wnd["speed"] == WND_SPEED_SENTINEL:
            sentinel_fields.append("WND_speed")

    if valid_fields and sentinel_fields:
        return (
            True,
            f"Mixed validity — valid: {','.join(valid_fields)} | sentinel: {','.join(sentinel_fields)}",
        )
    return False, ""


def detect_multi_family_informative(
    tmp: dict, vis: dict, wnd: dict, aa1: dict
) -> tuple[bool, str]:
    """TMP, VIS, WND, and AA1 all present and non-empty (any value)."""
    present = [
        bool(tmp and tmp["numeric"]),
        bool(vis and vis["distance"]),
        bool(wnd and wnd["direction"]),
        bool(aa1 and aa1["period"]),
    ]
    labels = ["TMP", "VIS", "WND", "AA1"]
    populated = [labels[i] for i, p in enumerate(present) if p]
    if len(populated) == 4:
        return True, f"All four families populated: {', '.join(populated)}"
    return False, ""


# Map pattern name → detector function
PATTERN_DETECTORS: dict[str, object] = {
    "tmp_missing_sentinel": detect_tmp_missing_sentinel,
    "tmp_negative_sentinel": detect_tmp_negative_sentinel,
    "vis_missing_sentinel": detect_vis_missing_sentinel,
    "wnd_calm_valid": detect_wnd_calm_valid,
    "wnd_missing_dir_valid_spd": detect_wnd_missing_dir_valid_spd,
    "wnd_fully_missing": detect_wnd_fully_missing,
    "aa1_valid_precip": detect_aa1_valid_precip,
    "aa1_missing_sentinel": detect_aa1_missing_sentinel,
    "mixed_validity": detect_mixed_validity,
    "multi_family_informative": detect_multi_family_informative,
}

# ---------------------------------------------------------------------------
# Station ID extraction
# ---------------------------------------------------------------------------


def infer_station_id(file_path: Path) -> str:
    """Attempt to infer a station identifier from the file path.

    Tries the parent directory name first (common layout: 02536099999/Raw.csv),
    then the file stem, then a regex match on any path component.
    Returns an empty string if nothing plausible is found.
    """
    # Parent dir name — often the 11-char station id
    parent = file_path.parent.name
    m = _STATION_RE.fullmatch(parent)
    if m:
        return m.group(1)
    # File stem
    stem = file_path.stem
    m = _STATION_RE.fullmatch(stem)
    if m:
        return m.group(1)
    # Any part of the full path
    for part in reversed(file_path.parts):
        m = _STATION_RE.search(part)
        if m:
            return m.group(1)
    return ""


# ---------------------------------------------------------------------------
# Parquet file scanning
# ---------------------------------------------------------------------------


def _parquet_files(root: Path) -> Generator[Path, None, None]:
    """Yield all .parquet files under root recursively."""
    yield from root.rglob("*.parquet")


def _row_fingerprint(raw_row: str) -> str:
    """Short hash to deduplicate identical raw rows within a pattern."""
    return hashlib.md5(raw_row.encode("utf-8", errors="replace")).hexdigest()[:16]


def scan_file(
    parquet_path: Path,
    internal_cap: int,
    pattern_counts: dict[str, int],  # mutable: running total per pattern
    seen_fps: dict[str, set[str]],   # mutable: seen fingerprints per pattern per-file
) -> tuple[list[Match], int, list[str]]:
    """Stream a single Parquet file row-group by row-group and return
    (matches, rows_scanned, warnings).

    Reading is done via pyarrow.parquet.ParquetFile so only one row group is
    materialised in memory at a time — the file is never fully loaded.

    Parameters
    ----------
    parquet_path:
        Path to the Parquet file to scan.
    internal_cap:
        Maximum matches to collect per pattern across the whole run (pre-diversity
        downsampling).  When a pattern's count reaches this, new matches for that
        pattern are silently skipped.
    pattern_counts:
        Shared mutable counter for matches found so far per pattern.  Updated in-place.
    seen_fps:
        Unused — kept for API symmetry; deduplication uses file_seen below.
    """
    matches: list[Match] = []
    warnings: list[str] = []
    rows_scanned = 0
    station_id = infer_station_id(parquet_path)

    # Columns to request from parquet (avoids deserialising unneeded columns)
    WANT_COLS = ["TMP", "VIS", "WND", "AA1", "DATE", "STATION"]

    try:
        pf = pq.ParquetFile(parquet_path)

        # Check schema for required columns before doing any real work
        schema_names: set[str] = set(pf.schema_arrow.names)
        missing_core = MIN_REQUIRED_COLS - schema_names
        if missing_core:
            warnings.append(
                f"Skipping {parquet_path}: missing core columns {missing_core}. "
                f"Found: {sorted(schema_names & {'TMP','VIS','WND','AA1','DATE','STATION'})}"
            )
            return matches, rows_scanned, warnings

        # Only request columns that actually exist in this file
        read_cols = [c for c in WANT_COLS if c in schema_names]

        # Per-file fingerprint set to deduplicate identical rows within this file
        file_seen: dict[str, set[str]] = defaultdict(set)

        # Row offset counter (used as a surrogate line number)
        row_offset = 1

        for batch in pf.iter_batches(columns=read_cols):
            # Convert batch to a list of dicts for row-level access
            # pyarrow RecordBatch → pandas DataFrame is the cleanest path
            df = batch.to_pydict()  # {col: [values...]}
            n_rows = batch.num_rows

            for i in range(n_rows):
                rows_scanned += 1
                row_offset += 1

                def _get(col: str) -> str:  # noqa: E306
                    vals = df.get(col)
                    if vals is None:
                        return ""
                    v = vals[i]
                    # pyarrow may return None for null cells
                    return str(v).strip() if v is not None else ""

                tmp_raw = _get("TMP")
                vis_raw = _get("VIS")
                wnd_raw = _get("WND")
                aa1_raw = _get("AA1")
                date_val = _get("DATE")
                station_col_val = _get("STATION")

                effective_station = station_col_val if station_col_val else station_id

                # Parse field tokens
                tmp_p = parse_tmp(tmp_raw) if tmp_raw else {}
                vis_p = parse_vis(vis_raw) if vis_raw else {}
                wnd_p = parse_wnd(wnd_raw) if wnd_raw else {}
                aa1_p = parse_aa1(aa1_raw) if aa1_raw else {}

                # Canonical row fingerprint: hash of the key field values
                raw_row_str = "|".join([tmp_raw, vis_raw, wnd_raw, aa1_raw, date_val])
                row_fp = _row_fingerprint(raw_row_str)

                # --- Run detectors ---
                for pattern_name, detector in PATTERN_DETECTORS.items():
                    if pattern_counts.get(pattern_name, 0) >= internal_cap:
                        continue
                    if row_fp in file_seen[pattern_name]:
                        continue

                    matched, reason = detector(tmp_p, vis_p, wnd_p, aa1_p)
                    if matched:
                        file_seen[pattern_name].add(row_fp)
                        pattern_counts[pattern_name] = pattern_counts.get(pattern_name, 0) + 1
                        matches.append(
                            Match(
                                pattern_name=pattern_name,
                                source_file_path=str(parquet_path),
                                station_id=effective_station,
                                line_number=row_offset,
                                datetime=date_val,
                                raw_row=raw_row_str,
                                tmp_value=tmp_raw,
                                vis_value=vis_raw,
                                wnd_value=wnd_raw,
                                aa1_value=aa1_raw,
                                reason=reason,
                            )
                        )

    except PermissionError as exc:
        warnings.append(f"Permission denied: {parquet_path}: {exc}")
    except OSError as exc:
        warnings.append(f"OS error reading {parquet_path}: {exc}")
    except Exception as exc:  # pyarrow raises various internal errors on corrupt files
        warnings.append(f"Failed to read {parquet_path}: {type(exc).__name__}: {exc}")

    return matches, rows_scanned, warnings


# ---------------------------------------------------------------------------
# Diversity downsampling
# ---------------------------------------------------------------------------


def diverse_sample(matches: list[Match], max_n: int) -> list[Match]:
    """Return up to max_n matches with station diversity.

    Interleaves matches grouped by station_id so the output contains
    representatives from as many different stations as possible before
    repeating any single station.
    """
    if len(matches) <= max_n:
        return matches

    # Group by station_id, preserving discovery order within each station
    groups: dict[str, list[Match]] = defaultdict(list)
    for m in matches:
        key = m.station_id or m.source_file_path
        groups[key].append(m)

    result: list[Match] = []
    # Round-robin across station groups
    station_lists = list(groups.values())
    idx = 0
    while len(result) < max_n:
        advanced = False
        for station_list in station_lists:
            if idx < len(station_list):
                result.append(station_list[idx])
                advanced = True
                if len(result) >= max_n:
                    break
        if not advanced:
            break
        idx += 1

    return result


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------


def write_csv(path: Path, rows: list[Match]) -> None:
    """Write a list of Match objects to a CSV file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=MATCH_FIELDNAMES)
        writer.writeheader()
        for m in rows:
            writer.writerow(asdict(m))


def write_summary_csv(path: Path, counts: dict[str, tuple[int, int]]) -> None:
    """Write a summary CSV with raw and final match counts per pattern.

    counts: pattern_name → (raw_match_count, final_count_after_downsampling)
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["pattern_name", "raw_matches_found", "rows_in_output"])
        for pattern in PATTERN_NAMES:
            raw, final = counts.get(pattern, (0, 0))
            writer.writerow([pattern, raw, final])


def write_report_md(
    path: Path,
    root: Path,
    outdir: Path,
    total_files: int,
    total_rows: int,
    counts: dict[str, tuple[int, int]],
    top_stations: dict[str, list[str]],
    skipped_warnings: list[str],
    max_per_pattern: int,
) -> None:
    """Write a human-readable markdown mining report."""
    path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    lines += [
        "# NOAA ISD Example Row Mining Report",
        "",
        f"**Corpus root:** `{root}`",
        f"**Output directory:** `{outdir}`",
        f"**Max per pattern:** {max_per_pattern}",
        "",
        "---",
        "",
        "## Scan Statistics",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total files scanned | {total_files:,} |",
        f"| Total rows scanned | {total_rows:,} |",
        f"| Skipped / bad files | {len(skipped_warnings)} |",
        "",
        "---",
        "",
        "## Matches Per Pattern",
        "",
        "| Pattern | Raw matches found | Rows in output (after diversity capping) |",
        "|---------|:-----------------:|:-----------------------------------------:|",
    ]
    for pattern in PATTERN_NAMES:
        raw, final = counts.get(pattern, (0, 0))
        lines.append(f"| `{pattern}` | {raw:,} | {final:,} |")

    lines += [
        "",
        "---",
        "",
        "## Top Candidate Stations / Files Per Pattern",
        "",
    ]
    for pattern in PATTERN_NAMES:
        stations = top_stations.get(pattern, [])
        lines.append(f"### `{pattern}`")
        if stations:
            for s in stations[:10]:
                lines.append(f"- `{s}`")
        else:
            lines.append("- *(no matches)*")
        lines.append("")

    lines += [
        "---",
        "",
        "## Malformed / Skipped Files",
        "",
    ]
    if skipped_warnings:
        for w in skipped_warnings[:200]:
            lines.append(f"- {w}")
        if len(skipped_warnings) > 200:
            lines.append(f"- … and {len(skipped_warnings) - 200} more (see stderr log)")
    else:
        lines.append("- *(none)*")

    lines += [
        "",
        "---",
        "",
        "## Suggested Next Steps",
        "",
        "1. **Review `summary.csv`** — check which patterns found matches.",
        "2. **Open `all_matches.csv`** — sort by `pattern_name` or `station_id` "
        "to spot useful candidates.",
        "3. **Use per-pattern CSVs** — each `pattern_<name>.csv` has already been "
        "diversity-sampled to ≤ `max_per_pattern` rows.",
        "4. **Manually curate a reviewer fixture** — pick ~15–25 rows that collectively "
        "illustrate several distinct patterns.  Keep the fixture small and traceable "
        "(preserve `source_file_path` and `line_number` columns).",
        "5. **Validate with the cleaner** — run curated rows through "
        "`noaa_spec.cleaning.clean_noaa_dataframe()` to confirm expected cleaning "
        "behaviour before committing them as fixtures.",
        "",
    ]

    path.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Main entrypoint
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Mine real NOAA ISD CSV rows matching edge-case cleaning patterns.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Example:\n"
            "  python tools/find_example_rows.py \\\n"
            "      --root /media/balaji-kesavan/LaCie/NOAA_Data \\\n"
            "      --outdir artifacts/example_row_mining \\\n"
            "      --max-per-pattern 25\n"
        ),
    )
    parser.add_argument(
        "--root",
        required=True,
        type=Path,
        help="Root directory to scan recursively for Parquet (*.parquet) files.",
    )
    parser.add_argument(
        "--outdir",
        required=True,
        type=Path,
        help="Directory to write all output artifacts.",
    )
    parser.add_argument(
        "--max-per-pattern",
        type=int,
        default=25,
        metavar="N",
        help="Maximum rows per pattern in final output (default: 25).  "
             "Actual matches found may be higher; the output is diversity-downsampled.",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=0,
        metavar="N",
        help="Stop after scanning N files (0 = unlimited).  Useful for quick tests.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity (default: INFO).",
    )
    args = parser.parse_args()

    logging.getLogger().setLevel(args.log_level)

    root: Path = args.root.resolve()
    outdir: Path = args.outdir.resolve()
    max_per_pattern: int = args.max_per_pattern
    max_files: int = args.max_files

    if not root.exists():
        log.error("Root directory does not exist: %s", root)
        sys.exit(1)

    # Internal cap: collect many more than max_per_pattern before diversity
    # downsampling so we get a good representative pool.
    internal_cap = max(1000, max_per_pattern * _INTERNAL_CAP_MULTIPLIER)

    log.info("Scanning corpus under: %s", root)
    log.info("Output directory: %s", outdir)
    log.info("Max per pattern (output): %d | Internal cap: %d", max_per_pattern, internal_cap)

    # Shared state across all files
    pattern_counts: dict[str, int] = defaultdict(int)   # raw matches per pattern
    all_matches: list[Match] = []
    all_warnings: list[str] = []
    total_files = 0
    total_rows = 0
    files_with_matches = 0

    for csv_path in _parquet_files(root):
        if max_files and total_files >= max_files:
            log.info("Reached --max-files=%d limit, stopping scan.", max_files)
            break

        total_files += 1
        if total_files % 500 == 0:
            log.info(
                "Progress: %d files scanned, %d rows, %d total raw matches",
                total_files,
                total_rows,
                sum(pattern_counts.values()),
            )

        # Pass empty per-file seen-set (reset per file for dedup logic)
        file_seen: dict[str, set[str]] = defaultdict(set)

        file_matches, rows_scanned, warnings = scan_file(
            parquet_path=csv_path,
            internal_cap=internal_cap,
            pattern_counts=pattern_counts,
            seen_fps=file_seen,
        )

        total_rows += rows_scanned
        all_warnings.extend(warnings)

        if file_matches:
            all_matches.extend(file_matches)
            files_with_matches += 1

        if warnings:
            for w in warnings:
                log.debug("Warning: %s", w)

    log.info(
        "Scan complete: %d files, %d rows, %d raw matches across all patterns",
        total_files,
        total_rows,
        len(all_matches),
    )

    # --- Diversity downsampling per pattern ---
    per_pattern_matches: dict[str, list[Match]] = defaultdict(list)
    for m in all_matches:
        per_pattern_matches[m.pattern_name].append(m)

    final_per_pattern: dict[str, list[Match]] = {}
    summary_counts: dict[str, tuple[int, int]] = {}
    top_stations: dict[str, list[str]] = {}

    for pattern in PATTERN_NAMES:
        raw_list = per_pattern_matches.get(pattern, [])
        final_list = diverse_sample(raw_list, max_per_pattern)
        final_per_pattern[pattern] = final_list
        summary_counts[pattern] = (len(raw_list), len(final_list))

        # Top stations by match frequency
        station_freq: dict[str, int] = defaultdict(int)
        for m in raw_list:
            station_freq[m.station_id or m.source_file_path] += 1
        top_stations[pattern] = sorted(station_freq, key=lambda s: -station_freq[s])

    # All output rows (diversity-downsampled each pattern)
    all_final: list[Match] = []
    for pattern in PATTERN_NAMES:
        all_final.extend(final_per_pattern[pattern])

    # --- Write outputs ---
    outdir.mkdir(parents=True, exist_ok=True)

    # all_matches.csv
    all_out = outdir / "all_matches.csv"
    write_csv(all_out, all_final)
    log.info("Wrote %s (%d rows)", all_out, len(all_final))

    # Per-pattern CSVs
    for pattern in PATTERN_NAMES:
        ppath = outdir / f"pattern_{pattern}.csv"
        write_csv(ppath, final_per_pattern[pattern])
        log.info(
            "Wrote %s (%d rows, %d raw)",
            ppath,
            len(final_per_pattern[pattern]),
            summary_counts[pattern][0],
        )

    # summary.csv
    summary_out = outdir / "summary.csv"
    write_summary_csv(summary_out, summary_counts)
    log.info("Wrote %s", summary_out)

    # report.md
    report_out = outdir / "report.md"
    write_report_md(
        path=report_out,
        root=root,
        outdir=outdir,
        total_files=total_files,
        total_rows=total_rows,
        counts=summary_counts,
        top_stations=top_stations,
        skipped_warnings=all_warnings,
        max_per_pattern=max_per_pattern,
    )
    log.info("Wrote %s", report_out)

    # --- Console summary ---
    print("\n=== Mining Summary ===")
    print(f"Files scanned : {total_files:>10,}")
    print(f"Rows scanned  : {total_rows:>10,}")
    print(f"Files with hits: {files_with_matches:>9,}")
    print(f"Skipped/bad   : {len(all_warnings):>10,}")
    print()
    print(f"{'Pattern':<35}  {'Raw':>8}  {'Output':>8}")
    print("-" * 56)
    for pattern in PATTERN_NAMES:
        raw, final = summary_counts.get(pattern, (0, 0))
        print(f"  {pattern:<33}  {raw:>8,}  {final:>8,}")
    print()
    print(f"Output directory: {outdir}")
    print(f"  all_matches.csv  ({len(all_final)} rows total)")
    print(f"  summary.csv")
    print(f"  report.md")
    for pattern in PATTERN_NAMES:
        n = len(final_per_pattern[pattern])
        if n:
            print(f"  pattern_{pattern}.csv  ({n} rows)")


if __name__ == "__main__":
    main()
