#!/usr/bin/env python3
"""
generate_audit_queue.py

Generate ordered NOAA ISD identifier-family audit batches (combinations),
sorted by a recommended tier order.

Why not permutations?
- Full permutations of N families is N! (explodes instantly).
- Instead, generate combinations (choose k) and sort them by priority order.

Usage examples:
  python generate_audit_queue.py --k 1 2 3 --format md --out audit_queue.md
  python generate_audit_queue.py --k 2 --format csv --out audit_pairs.csv
  python generate_audit_queue.py --k 1 --limit 50 --format md

"""

from __future__ import annotations

import argparse
import csv
import itertools
from dataclasses import dataclass
from typing import Iterable, List, Tuple


@dataclass(frozen=True)
class Family:
    key: str
    tier: int
    tier_name: str
    description: str


def get_families() -> List[Family]:
    """
    Tier order recommendation (highest priority first):

    Tier 1: Control + Mandatory
    Tier 2: Common operational weather
    Tier 3: Text/tricky sections (REM/QNN/EQD)
    Tier 4: Specialized/less common
    """
    return [
        # Tier 1 — Mandatory + Control
        Family("CONTROL", 1, "Tier 1 — Control + Mandatory", "Control section (DATE, TIME, LAT, LON, CALL_SIGN, etc.)"),
        Family("MANDATORY", 1, "Tier 1 — Control + Mandatory", "Mandatory data section (TMP/WND/VIS/CIG/DEW/SLP etc.)"),

        # Tier 2 — Common operational weather
        Family("AA_AZ", 2, "Tier 2 — Core weather add-ons", "Weather/precip occurrence families (AA–AZ)"),
        Family("OA_OE", 2, "Tier 2 — Core weather add-ons", "Supplementary wind families (OA–OE)"),
        Family("MA_MK", 2, "Tier 2 — Core weather add-ons", "Pressure extension families (MA–MK)"),
        Family("RH", 2, "Tier 2 — Core weather add-ons", "Relative humidity families (RH*)"),
        Family("GA_GQ", 2, "Tier 2 — Core weather add-ons", "Cloud + solar/sunshine families (GA–GQ)"),

        # Tier 3 — Text/tricky
        Family("REM", 3, "Tier 3 — Text/tricky", "Remarks section (free text, typed)"),
        Family("QNN", 3, "Tier 3 — Text/tricky", "Original observations section (tokenized payload)"),
        Family("EQD", 3, "Tier 3 — Text/tricky", "Element quality data section (Q##/P##/R##/C##/D##/N##)"),

        # Tier 4 — Specialized/less common
        Family("CO_CW", 4, "Tier 4 — Specialized", "Network metadata families (CO–CW)"),
        Family("CB_CX", 4, "Tier 4 — Specialized", "CRN families (CB–CX)"),
        Family("IA_KF", 4, "Tier 4 — Specialized", "Ground/soil/temperature families (IA–KF)"),
        Family("SA_ST", 4, "Tier 4 — Specialized", "Sea/soil temperature families (SA–ST)"),
        Family("UA_WJ", 4, "Tier 4 — Specialized", "Marine families (UA–WJ)"),
    ]


def family_rank_map(families: List[Family]) -> dict[str, int]:
    """Lower is higher priority."""
    return {fam.key: i for i, fam in enumerate(families)}


def combo_sort_key(combo: Tuple[str, ...], rank: dict[str, int]) -> Tuple[int, ...]:
    """Sort a combo by the priority rank of each family in it."""
    return tuple(rank[x] for x in combo)


def generate_combos(
    families: List[Family],
    k: int,
    limit: int | None = None,
) -> List[Tuple[str, ...]]:
    """
    Generate combinations of size k, then sort:
    - Primary: by the priority rank of the first family (and then next...)
    - Secondary: lexicographically by keys (stable tie-breaker)
    """
    keys = [f.key for f in families]
    rank = family_rank_map(families)

    combos = list(itertools.combinations(keys, k))
    combos.sort(key=lambda c: (combo_sort_key(c, rank), c))

    if limit is not None:
        combos = combos[:limit]
    return combos


def render_markdown(families: List[Family], all_combos: List[Tuple[int, List[Tuple[str, ...]]]]) -> str:
    fam_by_key = {f.key: f for f in families}

    lines: List[str] = []
    lines.append("# NOAA ISD Family Audit Queue\n")
    lines.append("This queue is sorted by the recommended tier order (Tier 1 → Tier 4).\n")
    lines.append("## Family tiers\n")
    current_tier = None
    for f in families:
        if f.tier != current_tier:
            current_tier = f.tier
            lines.append(f"### {f.tier_name}\n")
        lines.append(f"- **{f.key}** — {f.description}")
    lines.append("")

    for k, combos in all_combos:
        lines.append(f"## Combinations of size k={k}\n")
        for idx, combo in enumerate(combos, start=1):
            # Show expanded descriptions inline (quick scan)
            desc = " + ".join(f"{x}" for x in combo)
            long_desc = " | ".join(f"{x}: {fam_by_key[x].description}" for x in combo)
            lines.append(f"{idx}. **{desc}**  \n   {long_desc}")
        lines.append("")

    return "\n".join(lines)


def write_csv(out_path: str, families: List[Family], combos: List[Tuple[str, ...]], k: int) -> None:
    fam_by_key = {f.key: f for f in families}
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["k", "combo_index", "families", "tiers", "descriptions"])
        for i, combo in enumerate(combos, start=1):
            tiers = [fam_by_key[x].tier for x in combo]
            descs = [fam_by_key[x].description for x in combo]
            w.writerow([k, i, "+".join(combo), "+".join(map(str, tiers)), " | ".join(descs)])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, nargs="+", default=[1, 2, 3], help="Combination sizes to generate (e.g., 1 2 3).")
    ap.add_argument("--limit", type=int, default=None, help="Limit combos per k (for readability).")
    ap.add_argument("--format", choices=["md", "csv"], default=None, help="Output format (auto-detected from --out if omitted).")
    ap.add_argument("--out", type=str, default=None, help="Output path. If omitted: prints to stdout.")
    args = ap.parse_args()

    # Auto-detect format from --out extension if not explicitly specified
    if args.format is None:
        if args.out and args.out.lower().endswith(".csv"):
            args.format = "csv"
        else:
            args.format = "md"

    families = get_families()

    all_combos: List[Tuple[int, List[Tuple[str, ...]]]] = []
    for k in args.k:
        combos = generate_combos(families, k=k, limit=args.limit)
        all_combos.append((k, combos))

    if args.format == "md":
        md = render_markdown(families, all_combos)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(md)
        else:
            print(md)
    else:
        # CSV: write one file per k unless user provided --out (then write that single k if only one)
        if args.out and len(args.k) == 1:
            k = args.k[0]
            combos = all_combos[0][1]
            write_csv(args.out, families, combos, k)
        else:
            for k, combos in all_combos:
                out_path = args.out or f"audit_combos_k{k}.csv"
                # If args.out provided with multiple ks, suffix it
                if args.out:
                    base = args.out.rsplit(".", 1)
                    out_path = f"{base[0]}_k{k}.{base[1]}" if len(base) == 2 else f"{args.out}_k{k}.csv"
                write_csv(out_path, families, combos, k)


if __name__ == "__main__":
    main()