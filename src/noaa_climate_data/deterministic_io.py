"""Deterministic tabular serialization helpers for release artifacts."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def write_deterministic_csv(
    frame: pd.DataFrame,
    output_path: Path,
    *,
    sort_by: tuple[str, ...] = (),
) -> None:
    """Write CSV with deterministic ordering and serialization settings."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    prepared = _prepare_frame(frame, sort_by=sort_by)
    prepared.to_csv(
        output_path,
        index=False,
        lineterminator="\n",
        na_rep="",
        encoding="utf-8",
    )


def write_deterministic_parquet(
    frame: pd.DataFrame,
    output_path: Path,
    *,
    sort_by: tuple[str, ...] = (),
) -> None:
    """Write parquet with deterministic ordering and explicit codec choice."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    prepared = _prepare_frame(frame, sort_by=sort_by)
    prepared.to_parquet(output_path, index=False, compression="snappy")


def _prepare_frame(frame: pd.DataFrame, *, sort_by: tuple[str, ...]) -> pd.DataFrame:
    prepared = frame.copy()
    if prepared.empty:
        return prepared

    sort_keys = [column for column in sort_by if column in prepared.columns]
    if sort_keys:
        prepared = prepared.sort_values(sort_keys, kind="stable").reset_index(drop=True)
    return prepared
