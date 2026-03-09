"""Deterministic tabular serialization helpers for release artifacts."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable
import uuid

import pandas as pd


def write_deterministic_csv(
    frame: pd.DataFrame,
    output_path: Path,
    *,
    sort_by: tuple[str, ...] = (),
) -> None:
    """Write CSV with deterministic ordering and serialization settings."""
    prepared = _prepare_frame(frame, sort_by=sort_by)

    def _writer(path: Path) -> None:
        prepared.to_csv(
            path,
            index=False,
            lineterminator="\n",
            na_rep="",
            encoding="utf-8",
        )

    _atomic_replace(output_path, _writer)


def write_deterministic_parquet(
    frame: pd.DataFrame,
    output_path: Path,
    *,
    sort_by: tuple[str, ...] = (),
) -> None:
    """Write parquet with deterministic ordering and explicit codec choice."""
    prepared = _prepare_frame(frame, sort_by=sort_by)

    def _writer(path: Path) -> None:
        prepared.to_parquet(path, index=False, compression="snappy")

    _atomic_replace(output_path, _writer)


def _atomic_replace(output_path: Path, writer: Callable[[Path], None]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = output_path.parent / f".{output_path.name}.tmp-{os.getpid()}-{uuid.uuid4().hex}"
    try:
        writer(tmp_path)
        os.replace(tmp_path, output_path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def _prepare_frame(frame: pd.DataFrame, *, sort_by: tuple[str, ...]) -> pd.DataFrame:
    prepared = frame.copy()
    if prepared.empty:
        return prepared

    sort_keys = [column for column in sort_by if column in prepared.columns]
    if sort_keys:
        prepared = prepared.sort_values(sort_keys, kind="stable").reset_index(drop=True)
    return prepared
