"""Tests for the public ``noaa-spec clean`` command."""

from __future__ import annotations

from pathlib import Path
import sys
import textwrap

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


def test_cli_clean_exposes_raw_line_structural_validation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    input_csv = tmp_path / "raw_line_input.csv"
    output_csv = tmp_path / "raw_line_output.csv"
    raw_line = (
        "0004"  # TOTAL_VARIABLE_CHARACTERS
        "723150"  # USAF
        "03812"  # WBAN
        "20240201"  # DATE
        "1230"  # TIME
        "4"  # SOURCE_FLAG
        "+12345"  # LATITUDE
        "+123456"  # LONGITUDE
        "+0123"  # ELEVATION
        "FM-15"  # REPORT_TYPE
        "KJFK "  # CALL_SIGN
        "V02 "  # QC_PROCESS
    )
    assert len(raw_line) == 60
    input_csv.write_text(
        textwrap.dedent(
            """\
            raw_line,TMP
            {raw_line},"+0010,1"
            """
        ).format(raw_line=raw_line + ("X" * 44)),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        sys,
        "argv",
        ["prog", "clean", str(input_csv), str(output_csv)],
    )
    cli.main()

    cleaned = pd.read_csv(output_csv, low_memory=False)
    assert "__parse_error" in cleaned.columns
    assert cleaned.loc[0, "__parse_error"] == "mandatory_section_short"
    assert "temperature_c" not in cleaned.columns


def test_cli_clean_reports_skipped_unsupported_encoded_field(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_csv = tmp_path / "unsupported_field_input.csv"
    output_csv = tmp_path / "unsupported_field_output.csv"
    input_csv.write_text(
        textwrap.dedent(
            """\
            STATION,DATE,ZZZ,TMP
            12345678901,2000-01-01T00:00:00,"abc,def","+0010,1"
            """
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        sys,
        "argv",
        ["prog", "clean", str(input_csv), str(output_csv)],
    )
    cli.main()

    captured = capsys.readouterr()
    assert "strict parsing left 1 encoded NOAA-looking column unexpanded" in captured.err
    assert "unsupported identifier(s): ZZZ" in captured.err
