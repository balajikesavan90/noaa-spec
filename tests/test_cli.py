"""Tests for the public ``noaa-spec clean`` command."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import pytest

import noaa_spec.cli as cli


def test_cli_clean_writes_canonical_csv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    input_csv = repo_root / "reproducibility" / "minimal" / "station_raw.csv"
    expected_csv = repo_root / "reproducibility" / "minimal" / "station_cleaned_expected.csv"
    output_csv = tmp_path / "station_cleaned.csv"

    monkeypatch.setattr(
        sys,
        "argv",
        ["prog", "clean", str(input_csv), str(output_csv)],
    )
    cli.main()

    assert output_csv.read_text(encoding="utf-8") == expected_csv.read_text(encoding="utf-8")


def test_cli_clean_accepts_legacy_out_flag(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    input_csv = repo_root / "reproducibility" / "minimal" / "station_raw.csv"
    output_csv = tmp_path / "station_cleaned.csv"

    monkeypatch.setattr(
        sys,
        "argv",
        ["prog", "clean", str(input_csv), "--out", str(output_csv)],
    )
    cli.main()

    assert output_csv.exists()


def test_cli_clean_preserves_quality_code_when_sentinel_is_null(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    input_csv = repo_root / "reproducibility" / "minimal" / "station_raw.csv"
    output_csv = tmp_path / "station_cleaned.csv"

    monkeypatch.setattr(
        sys,
        "argv",
        ["prog", "clean", str(input_csv), str(output_csv)],
    )
    cli.main()

    cleaned = pd.read_csv(output_csv, low_memory=False)
    sentinel_row = cleaned.loc[cleaned["DATE"] == "2000-03-17T09:00:00"].iloc[0]
    assert pd.isna(sentinel_row["temperature_c"])
    assert str(sentinel_row["temperature_quality_code"]) == "9"
    assert sentinel_row["TMP__qc_reason"] == "SENTINEL_MISSING"


def test_cli_clean_requires_output_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    input_csv = repo_root / "reproducibility" / "minimal" / "station_raw.csv"

    monkeypatch.setattr(sys, "argv", ["prog", "clean", str(input_csv)])

    with pytest.raises(SystemExit, match="Provide an output path"):
        cli.main()

