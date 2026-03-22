from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import pytest

from scripts import check_station_sync


def test_check_station_sync_uses_raw_pull_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)

    index_dir = tmp_path / "noaa_file_index" / "20250101"
    index_dir.mkdir(parents=True)
    pd.DataFrame(
        [
            {"ID": "01234567890", "FileName": "01234567890.csv"},
            {"ID": "01234567891", "FileName": "01234567891.csv"},
        ]
    ).to_csv(index_dir / "Stations.csv", index=False)

    state_dir = tmp_path / "noaa_file_index" / "state"
    state_dir.mkdir(parents=True)
    pd.DataFrame(
        [
            {
                "station_id": "01234567890",
                "FileName": "01234567890.csv",
                "raw_data_pulled": True,
                "raw_path": "",
                "pulled_at": "",
                "registry_snapshot": str(index_dir / "Stations.csv"),
            }
        ]
    ).to_csv(state_dir / "raw_pull_state.csv", index=False)

    output_dir = tmp_path / "output"
    station_dir = output_dir / "01234567890"
    station_dir.mkdir(parents=True)
    (station_dir / "LocationData_Raw.parquet").write_text("fake", encoding="utf-8")

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "prog",
            "--output-dir",
            str(output_dir),
        ],
    )
    check_station_sync.main()

    output = capsys.readouterr().out
    assert "raw_pull_state.csv:" in output
    assert "Total stations: 2" in output
    assert "raw_data_pulled=True: 1" in output
    assert "raw_data_pulled=False: 1" in output
    assert "Missing parquet (should exist): 0" in output
    assert "Unexpected parquet (should not exist): 0" in output


def test_check_station_sync_requires_state_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    index_dir = tmp_path / "noaa_file_index" / "20250101"
    index_dir.mkdir(parents=True)
    pd.DataFrame(
        [
            {"ID": "01234567890", "FileName": "01234567890.csv"},
        ]
    ).to_csv(index_dir / "Stations.csv", index=False)

    monkeypatch.setattr(sys, "argv", ["prog"])

    with pytest.raises(FileNotFoundError, match="materialize-raw-pull-state"):
        check_station_sync.main()
