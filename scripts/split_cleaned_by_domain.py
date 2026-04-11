#!/usr/bin/env python3
"""Split a cleaned NOAA CSV into domain-specific CSV files.

This script intentionally delegates domain classification to
``noaa_spec.domain_split`` so classification rules remain centralized
in package-governed code.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from noaa_spec.internal.domain_split import COMMON_COLUMNS, classify_columns


def _coerce_qc_pass(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series.fillna(False)
    truthy = {"true", "1", "yes", "y", "t"}
    return series.fillna(False).astype(str).str.strip().str.lower().isin(truthy)


def _recompute_usability_columns(
    chunk: pd.DataFrame,
    metric_columns: list[str],
) -> pd.DataFrame:
    qc_pass_columns = [col for col in chunk.columns if col.endswith("__qc_pass")]

    if qc_pass_columns:
        qc_frame = pd.DataFrame(
            {col: _coerce_qc_pass(chunk[col]) for col in qc_pass_columns},
            index=chunk.index,
        )
        usable_metric_count = qc_frame.sum(axis=1).astype(int)
        total_metrics = len(qc_pass_columns)
        usable_metric_fraction = usable_metric_count / total_metrics
        row_has_any_usable_metric = usable_metric_count > 0
    elif metric_columns:
        usable_metric_count = chunk[metric_columns].notna().sum(axis=1).astype(int)
        total_metrics = len(metric_columns)
        usable_metric_fraction = usable_metric_count / total_metrics
        row_has_any_usable_metric = usable_metric_count > 0
    else:
        usable_metric_count = pd.Series(0, index=chunk.index, dtype="int64")
        usable_metric_fraction = pd.Series(0.0, index=chunk.index, dtype="float64")
        row_has_any_usable_metric = pd.Series(False, index=chunk.index, dtype="bool")

    if "row_has_any_usable_metric" in chunk.columns:
        chunk["row_has_any_usable_metric"] = row_has_any_usable_metric
    if "usable_metric_count" in chunk.columns:
        chunk["usable_metric_count"] = usable_metric_count
    if "usable_metric_fraction" in chunk.columns:
        chunk["usable_metric_fraction"] = usable_metric_fraction

    return chunk


def _write_subset_csv(
    input_csv: Path,
    output_csv: Path,
    selected_columns: list[str],
    metric_columns: list[str],
    chunksize: int,
) -> int:
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    rows_written = 0
    first_chunk = True

    for chunk in pd.read_csv(
        input_csv,
        usecols=selected_columns,
        chunksize=chunksize,
        low_memory=False,
    ):
        chunk = _recompute_usability_columns(chunk, metric_columns)
        chunk.to_csv(
            output_csv,
            index=False,
            mode="w" if first_chunk else "a",
            header=first_chunk,
        )
        first_chunk = False
        rows_written += len(chunk)

    if first_chunk:
        pd.DataFrame(columns=selected_columns).to_csv(output_csv, index=False)

    return rows_written


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Split cleaned NOAA CSV into domain-specific CSV files."
    )
    parser.add_argument("input_csv", type=Path, help="Path to cleaned input CSV")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Target directory (default: <input parent>/<input stem>_domains)",
    )
    parser.add_argument(
        "--prefix",
        type=str,
        default=None,
        help="Output filename prefix (default: input stem)",
    )
    parser.add_argument(
        "--chunksize",
        type=int,
        default=50000,
        help="Rows per chunk while writing split files",
    )
    parser.add_argument(
        "--exclude-other",
        action="store_true",
        default=False,
        help="Do not write the catch-all 'other' domain file",
    )
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    input_csv = args.input_csv
    if not input_csv.exists():
        raise FileNotFoundError(f"Input file not found: {input_csv}")

    output_dir = args.output_dir
    if output_dir is None:
        output_dir = input_csv.parent / f"{input_csv.stem}_domains"
    prefix = args.prefix or input_csv.stem

    input_columns = list(pd.read_csv(input_csv, nrows=0).columns)
    common_columns, domain_columns = classify_columns(input_columns)
    if args.exclude_other:
        domain_columns.pop("other", None)

    manifest_rows: list[dict[str, object]] = []
    for domain_name, columns in domain_columns.items():
        if not columns:
            continue
        selected_columns = common_columns + columns
        metric_columns = [
            col
            for col in selected_columns
            if col not in COMMON_COLUMNS
            and col
            not in {
                "row_has_any_usable_metric",
                "usable_metric_count",
                "usable_metric_fraction",
            }
        ]
        output_file = output_dir / f"{prefix}__{domain_name}.csv"
        rows = _write_subset_csv(
            input_csv=input_csv,
            output_csv=output_file,
            selected_columns=selected_columns,
            metric_columns=metric_columns,
            chunksize=args.chunksize,
        )
        size_mb = output_file.stat().st_size / (1024 * 1024)
        manifest_rows.append(
            {
                "domain": domain_name,
                "rows": rows,
                "columns": len(selected_columns),
                "domain_columns": len(columns),
                "file": str(output_file),
                "size_mb": round(size_mb, 2),
            }
        )
        print(
            f"{domain_name}: rows={rows} columns={len(selected_columns)} "
            f"file={output_file}"
        )

    manifest_path = output_dir / f"{prefix}__manifest.csv"
    pd.DataFrame(manifest_rows).to_csv(manifest_path, index=False)
    print(f"manifest={manifest_path}")


if __name__ == "__main__":
    main()
