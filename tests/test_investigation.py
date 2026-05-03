from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd
import pytest

import noaa_spec.cli as cli
from noaa_spec.investigation import inspect_identifier_bundle


def _write_bundle_fixture(bundle_root: Path) -> None:
    raw_inputs = bundle_root / "raw_inputs"
    raw_inputs.mkdir(parents=True)

    pd.DataFrame(
        [
            {
                "STATION": "12345678901",
                "DATE": "2000-01-01T00:00:00",
                "REPORT_TYPE": "FM-15",
                "HL1": "003,9",
                "AG1": "0000,1,01,1",
                "AJ1": "1200,1,1,120000,1,1",
            },
            {
                "STATION": "12345678901",
                "DATE": "2000-01-01T01:00:00",
                "REPORT_TYPE": "FM-15",
                "HL1": "005,9",
                "AG1": "0001,1,01,1",
                "AJ1": "1201,1,1,120100,1,1",
            },
            {
                "STATION": "12345678901",
                "DATE": "2000-01-01T02:00:00",
                "REPORT_TYPE": "FM-15",
                "HL1": "",
                "AG1": "",
                "AJ1": "",
            },
        ]
    ).to_csv(raw_inputs / "12345678901.csv", index=False)

    pd.DataFrame(
        [
            {
                "STATION": "23456789012",
                "DATE": "2000-01-02T00:00:00",
                "REPORT_TYPE": "FM-15",
                "HL1": "001,9",
                "GJ1": "00500,1,000600,1,000700,1",
            },
            {
                "STATION": "23456789012",
                "DATE": "2000-01-02T01:00:00",
                "REPORT_TYPE": "FM-15",
                "HL1": "002,9",
                "GJ1": "00510,1,000610,1,000710,1",
            },
            {
                "STATION": "23456789012",
                "DATE": "2000-01-02T02:00:00",
                "REPORT_TYPE": "FM-15",
                "HL1": "013,9",
                "GJ1": "",
            },
        ]
    ).to_csv(raw_inputs / "23456789012.csv", index=False)

    pd.DataFrame(
        [
            {
                "STATION": "34567890123",
                "DATE": "2000-01-03T00:00:00",
                "REPORT_TYPE": "FM-15",
                "TMP": "+0010,1",
                "AW5": "95,5",
                "AW6": "96,5",
            }
        ]
    ).to_csv(raw_inputs / "34567890123.csv", index=False)

    pd.DataFrame(
        [
            {
                "station_id": "12345678901",
                "status": "success",
                "input_rows": "3",
                "output_rows": "3",
            },
            {
                "station_id": "23456789012",
                "status": "success",
                "input_rows": "3",
                "output_rows": "3",
            },
            {
                "station_id": "34567890123",
                "status": "success",
                "input_rows": "1",
                "output_rows": "1",
            },
        ]
    ).to_csv(bundle_root / "station_results.csv", index=False)


def test_inspect_identifier_bundle_writes_reports_and_summary(tmp_path: Path) -> None:
    bundle_root = tmp_path / "bundle"
    _write_bundle_fixture(bundle_root)
    output_path = bundle_root / "hl1_investigation.md"

    result = inspect_identifier_bundle(
        bundle_root=bundle_root,
        identifier="HL1",
        output_path=output_path,
        max_stations=2,
        max_rows_per_station=2,
    )

    assert result["station_count"] == 2
    assert result["row_count"] == 5
    assert output_path.exists()
    assert output_path.with_suffix(".json").exists()

    payload = json.loads(output_path.with_suffix(".json").read_text(encoding="utf-8"))
    assert payload["summary"]["appears_in_committed_specs"] is False
    assert payload["summary"]["station_count"] == 2
    assert payload["summary"]["row_count"] == 5
    assert payload["structural_observations"]["appears_as_column_name"] is True
    assert payload["structural_observations"]["payload_lengths_appear_stable"] is True
    assert payload["structural_observations"]["observed_quality_suffixes"] == ["9"]
    assert payload["parser_classification"]["is_valid_identifier"] is False
    assert payload["parser_classification"]["get_field_rule_returns_none"] is True
    assert payload["relationship_to_successful_cleaning"]["row_parity_holds_for_all_matching_stations"] is True
    assert payload["aw5_aw6_notes"]["identifiers"]["AW5"]["appears_as_raw_column"] is True
    assert payload["required_conclusion"].startswith("HL1 appears in the operational validation sample")


def test_inspect_identifier_bundle_caps_examples(tmp_path: Path) -> None:
    bundle_root = tmp_path / "bundle"
    _write_bundle_fixture(bundle_root)
    output_path = bundle_root / "hl1_investigation.md"

    inspect_identifier_bundle(
        bundle_root=bundle_root,
        identifier="HL1",
        output_path=output_path,
        max_stations=1,
        max_rows_per_station=1,
    )

    payload = json.loads(output_path.with_suffix(".json").read_text(encoding="utf-8"))
    assert len(payload["raw_examples"]) == 1
    assert {example["station_id"] for example in payload["raw_examples"]} == {"12345678901"}


def test_inspect_identifier_bundle_handles_missing_identifier_cleanly(tmp_path: Path) -> None:
    bundle_root = tmp_path / "bundle"
    _write_bundle_fixture(bundle_root)
    output_path = bundle_root / "zz1_investigation.md"

    inspect_identifier_bundle(
        bundle_root=bundle_root,
        identifier="ZZ1",
        output_path=output_path,
    )

    payload = json.loads(output_path.with_suffix(".json").read_text(encoding="utf-8"))
    assert payload["summary"]["station_count"] == 0
    assert payload["summary"]["row_count"] == 0
    assert payload["raw_examples"] == []
    assert "was not found in the scanned raw inputs" in output_path.read_text(encoding="utf-8")


def test_cli_inspect_identifier_writes_reports(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    bundle_root = tmp_path / "bundle"
    _write_bundle_fixture(bundle_root)
    output_path = bundle_root / "hl1_cli.md"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "prog",
            "inspect-identifier",
            "--bundle-root",
            str(bundle_root),
            "--identifier",
            "HL1",
            "--max-stations",
            "2",
            "--max-rows-per-station",
            "2",
            "--output",
            str(output_path),
        ],
    )

    cli.main()

    captured = capsys.readouterr()
    assert "Wrote identifier investigation to" in captured.out
    assert output_path.exists()
    assert output_path.with_suffix(".json").exists()
