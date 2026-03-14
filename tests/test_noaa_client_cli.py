"""Tests for NOAA client helpers and CLI commands without network access."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import fcntl
from pathlib import Path
import sys

import pandas as pd
import pytest

from noaa_climate_data import noaa_client
import noaa_climate_data.pipeline as pipeline
from noaa_climate_data.pipeline import LocationDataOutputs
import noaa_climate_data.cli as cli


@dataclass(frozen=True)
class _FakeDateTime:
    @staticmethod
    def now(tz: timezone | None = None) -> datetime:
        return datetime(2025, 1, 1, 0, 0, 0, tzinfo=tz)


class TestNoaaClient:
    def test_get_years_parses_dirs(self, monkeypatch: pytest.MonkeyPatch) -> None:
        table = pd.DataFrame({0: ["2020/", "2021/", "bad/", "202A/", "2021/", None]})
        monkeypatch.setattr(noaa_client.pd, "read_html", lambda url: [table])
        years = noaa_client.get_years(retries=0)
        assert years == ["2020", "2021"]

    def test_get_file_list_for_year(self, monkeypatch: pytest.MonkeyPatch) -> None:
        table = pd.DataFrame({0: ["AAA.csv", "BBB.txt", None, "CCC.csv"]})
        monkeypatch.setattr(noaa_client.pd, "read_html", lambda url: [table])
        files = noaa_client.get_file_list_for_year("2020", retries=0)
        assert files == ["AAA.csv", "CCC.csv"]

    def test_build_file_list(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def fake_get_file_list(year: str, **_: object) -> list[str]:
            return [f"{year}.csv"] if year != "2021" else []

        monkeypatch.setattr(noaa_client, "get_file_list_for_year", fake_get_file_list)
        result = noaa_client.build_file_list(["2020", "2021", "2022"], retries=0)
        assert result.shape[0] == 2
        assert set(result["YEAR"]) == {"2020", "2022"}

    def test_count_years_per_file(self) -> None:
        file_list = pd.DataFrame(
            {
                "YEAR": [2019, 2020, 2021, 2021],
                "FileName": ["A.csv", "A.csv", "A.csv", "B.csv"],
            }
        )
        counts = noaa_client.count_years_per_file(file_list, 2020, 2021)
        row_a = counts[counts["FileName"] == "A.csv"].iloc[0]
        row_b = counts[counts["FileName"] == "B.csv"].iloc[0]
        assert row_a["No_Of_Years"] == 2
        assert row_b["No_Of_Years"] == 1

    def test_normalize_station_file_name(self) -> None:
        assert (
            noaa_client.normalize_station_file_name("723150-03812-2006.csv")
            == "72315003812.csv"
        )
        assert (
            noaa_client.normalize_station_file_name("723150-03812")
            == "72315003812.csv"
        )

    def test_fetch_station_metadata(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(noaa_client, "_url_exists", lambda *_args, **_kwargs: True)
        frame = pd.DataFrame(
            [
                {
                    "LATITUDE": "10.5",
                    "LONGITUDE": "-20.25",
                    "ELEVATION": "15",
                    "NAME": "Test Station",
                }
            ]
        )
        monkeypatch.setattr(
            noaa_client,
            "_read_csv_head_with_retries",
            lambda *_args, **_kwargs: frame,
        )
        metadata = noaa_client.fetch_station_metadata("723150-03812-2006.csv", 2020, retries=0)
        assert metadata is not None
        assert metadata.latitude == 10.5
        assert metadata.longitude == -20.25
        assert metadata.elevation == 15.0
        assert metadata.name == "Test Station"
        assert metadata.file_name == "72315003812.csv"

    def test_fetch_station_metadata_for_years(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def fake_fetch(file_name: str, year: int, **_: object) -> noaa_client.StationMetadata | None:
            if year == 2021:
                return noaa_client.StationMetadata(
                    latitude=1.0,
                    longitude=2.0,
                    elevation=3.0,
                    name="Test",
                    file_name=file_name,
                )
            return None

        monkeypatch.setattr(noaa_client, "fetch_station_metadata", fake_fetch)
        metadata, metadata_year = noaa_client.fetch_station_metadata_for_years(
            "ABC.csv",
            [2020, 2021],
            retries=0,
        )
        assert metadata is not None
        assert metadata_year == 2021


class TestCliCommands:
    def test_cli_file_list_invokes_builders(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(cli, "datetime", _FakeDateTime)
        called: dict[str, object] = {}

        def fake_build_data_file_list(output_csv: Path, **_: object) -> pd.DataFrame:
            called["output_csv"] = output_csv
            return pd.DataFrame({"YEAR": ["2020"], "FileName": ["A.csv"]})

        def fake_build_year_counts(
            file_list: pd.DataFrame,
            output_csv: Path,
            start_year: int,
            end_year: int,
        ) -> pd.DataFrame:
            called["counts_csv"] = output_csv
            called["start_year"] = start_year
            called["end_year"] = end_year
            return pd.DataFrame()

        monkeypatch.setattr(cli, "build_data_file_list", fake_build_data_file_list)
        monkeypatch.setattr(cli, "build_year_counts", fake_build_year_counts)

        monkeypatch.setattr(
            sys,
            "argv",
            ["prog", "file-list", "--start-year", "2000", "--end-year", "2001"],
        )
        cli.main()

        output_csv = called["output_csv"]
        counts_csv = called["counts_csv"]
        assert output_csv.name == "DataFileList.csv"
        assert counts_csv.name == "DataFileList_YEARCOUNT.csv"
        assert output_csv.parent.parent == Path("noaa_file_index")
        assert called["start_year"] == 2000
        assert called["end_year"] == 2001

    def test_cli_location_ids_invokes_builder(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.chdir(tmp_path)
        base_dir = tmp_path / "noaa_file_index" / "20250101"
        base_dir.mkdir(parents=True)
        counts_path = base_dir / "DataFileList_YEARCOUNT.csv"
        file_list_path = base_dir / "DataFileList.csv"
        pd.DataFrame({"FileName": ["A.csv"], "No_Of_Years": [1]}).to_csv(
            counts_path, index=False
        )
        pd.DataFrame({"YEAR": [2020], "FileName": ["A.csv"]}).to_csv(
            file_list_path, index=False
        )

        called: dict[str, object] = {}

        def fake_build_location_ids(
            counts: pd.DataFrame,
            output_csv: Path,
            metadata_years: range,
            **kwargs: object,
        ) -> pd.DataFrame:
            called["counts_rows"] = len(counts)
            called["output_csv"] = output_csv
            called["metadata_years"] = list(metadata_years)
            called["resume"] = kwargs.get("resume")
            return pd.DataFrame()

        monkeypatch.setattr(cli, "build_location_ids", fake_build_location_ids)

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "prog",
                "location-ids",
                "--start-year",
                "2000",
                "--end-year",
                "2001",
                "--no-resume",
            ],
        )
        cli.main()

        assert called["counts_rows"] == 1
        assert called["output_csv"].resolve() == (base_dir / "Stations.csv").resolve()
        assert called["metadata_years"] == [2000, 2001]
        assert called["resume"] is False

    def test_cli_process_location_writes_outputs(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.chdir(tmp_path)
        output_dir = tmp_path / "out"
        sample = pd.DataFrame({"value": [1]})

        def fake_process_location(*_: object, **__: object) -> LocationDataOutputs:
            return LocationDataOutputs(
                raw=sample,
                cleaned=sample,
                hourly=sample,
                monthly=sample,
                yearly=sample,
            )

        monkeypatch.setattr(cli, "process_location", fake_process_location)
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "prog",
                "process-location",
                "TEST.csv",
                "--start-year",
                "2020",
                "--end-year",
                "2020",
                "--output-dir",
                str(output_dir),
            ],
        )
        cli.main()

        assert (output_dir / "LocationData_Raw.csv").exists()
        assert (output_dir / "LocationData_Cleaned.csv").exists()
        assert (output_dir / "LocationData_Hourly.csv").exists()
        assert (output_dir / "LocationData_Monthly.csv").exists()
        assert (output_dir / "LocationData_Yearly.csv").exists()

    def test_cli_pick_location_invokes_pull(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.chdir(tmp_path)
        base_dir = tmp_path / "noaa_file_index" / "20250101"
        base_dir.mkdir(parents=True)
        (base_dir / "Stations.csv").write_text("FileName\nTEST.csv\n")

        called: dict[str, object] = {}

        def fake_pull_random_station_raw(
            stations_csv: Path,
            years: range,
            output_dir: Path,
            **kwargs: object,
        ) -> Path:
            called["stations_csv"] = stations_csv
            called["years"] = list(years)
            called["output_dir"] = output_dir
            called.update(kwargs)
            return output_dir / "LocationData_Raw.parquet"

        monkeypatch.setattr(cli, "pull_random_station_raw", fake_pull_random_station_raw)

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "prog",
                "pick-location",
                "--start-year",
                "2020",
                "--end-year",
                "2021",
                "--sleep-seconds",
                "0.25",
                "--seed",
                "7",
            ],
        )
        cli.main()

        assert called["stations_csv"].resolve() == (base_dir / "Stations.csv").resolve()
        assert called["raw_pull_state_csv"].resolve() == (
            tmp_path / "noaa_file_index" / "state" / "raw_pull_state.csv"
        ).resolve()
        assert called["years"] == [2020, 2021]
        assert called["output_dir"].resolve() == (tmp_path / "output").resolve()
        assert called["sleep_seconds"] == 0.25
        assert called["seed"] == 7

    def test_cli_clean_parquet_invokes_cleaner(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.chdir(tmp_path)
        raw_path = tmp_path / "raw.parquet"
        raw_path.write_text("fake")

        called: dict[str, object] = {}

        def fake_clean_parquet_file(
            raw_parquet: Path,
            **kwargs: object,
        ) -> Path:
            called["raw_parquet"] = raw_parquet
            called.update(kwargs)
            return tmp_path / "LocationData_Cleaned.parquet"

        monkeypatch.setattr(cli, "clean_parquet_file", fake_clean_parquet_file)

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "prog",
                "clean-parquet",
                str(raw_path),
            ],
        )
        cli.main()

        assert called["raw_parquet"].resolve() == raw_path.resolve()
        assert called["output_dir"] is None

    def test_cli_materialize_raw_pull_state_invokes_migrator(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(tmp_path)
        base_dir = tmp_path / "noaa_file_index" / "20250101"
        base_dir.mkdir(parents=True)
        stations_csv = base_dir / "Stations.csv"
        stations_csv.write_text("FileName,raw_data_pulled\nTEST.csv,True\n", encoding="utf-8")

        called: dict[str, object] = {}

        def fake_materialize_raw_pull_state(
            stations_csv_arg: Path,
            raw_pull_state_csv: Path | None = None,
            *,
            normalize_stations_csv: bool = True,
        ) -> pd.DataFrame:
            called["stations_csv"] = stations_csv_arg
            called["raw_pull_state_csv"] = raw_pull_state_csv
            called["normalize_stations_csv"] = normalize_stations_csv
            return pd.DataFrame(
                [
                    {
                        "station_id": "01234567890",
                        "FileName": "TEST.csv",
                        "raw_data_pulled": True,
                        "raw_path": "",
                        "pulled_at": "",
                        "registry_snapshot": str(stations_csv_arg),
                    }
                ]
            )

        monkeypatch.setattr(cli, "materialize_raw_pull_state", fake_materialize_raw_pull_state)

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "prog",
                "materialize-raw-pull-state",
            ],
        )
        cli.main()

        assert called["stations_csv"].resolve() == stations_csv.resolve()
        assert called["raw_pull_state_csv"].resolve() == (
            tmp_path / "noaa_file_index" / "state" / "raw_pull_state.csv"
        ).resolve()
        assert called["normalize_stations_csv"] is True
        assert "Materialized" in capsys.readouterr().out

    def test_build_location_ids_excludes_operational_status_columns(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        year_counts = pd.DataFrame({"FileName": ["01234567890.csv"], "No_Of_Years": [1]})
        file_list = pd.DataFrame({"YEAR": [2020], "FileName": ["01234567890.csv"]})

        def fake_fetch_station_metadata_for_years(
            file_name: str,
            metadata_years: list[int],
            **_: object,
        ) -> tuple[noaa_client.StationMetadata, int]:
            assert metadata_years == [2020]
            return (
                noaa_client.StationMetadata(
                    latitude=1.0,
                    longitude=2.0,
                    elevation=3.0,
                    name="Test Station",
                    file_name=file_name,
                ),
                2020,
            )

        monkeypatch.setattr(pipeline, "fetch_station_metadata_for_years", fake_fetch_station_metadata_for_years)

        output_csv = tmp_path / "Stations.csv"
        frame = pipeline.build_location_ids(
            year_counts,
            output_csv,
            metadata_years=[2020],
            file_list=file_list,
            sleep_seconds=0.0,
            retries=0,
            checkpoint_every=1000,
        )

        assert "raw_data_pulled" not in frame.columns
        assert "data_cleaned" not in frame.columns
        written = pd.read_csv(output_csv)
        assert "raw_data_pulled" not in written.columns
        assert "data_cleaned" not in written.columns

    def test_materialize_raw_pull_state_bootstraps_and_normalizes_registry(
        self,
        tmp_path: Path,
    ) -> None:
        stations_csv = tmp_path / "noaa_file_index" / "20260207" / "Stations.csv"
        stations_csv.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(
            [
                {
                    "ID": "01234567890",
                    "FileName": "01234567890.csv",
                    "NAME": "Pulled",
                    "raw_data_pulled": True,
                    "data_cleaned": False,
                },
                {
                    "ID": "01234567891",
                    "FileName": "01234567891.csv",
                    "NAME": "Pending",
                    "raw_data_pulled": False,
                    "data_cleaned": False,
                },
            ]
        ).to_csv(stations_csv, index=False)

        state = pipeline.materialize_raw_pull_state(stations_csv)

        raw_pull_state_csv = tmp_path / "noaa_file_index" / "state" / "raw_pull_state.csv"
        assert raw_pull_state_csv.exists()
        written_state = pipeline._load_raw_pull_state(raw_pull_state_csv)
        assert list(written_state["FileName"]) == ["01234567890.csv"]
        assert written_state.loc[0, "station_id"] == "01234567890"
        assert bool(written_state.loc[0, "raw_data_pulled"]) is True
        assert written_state.loc[0, "raw_path"] == ""
        assert written_state.loc[0, "registry_snapshot"] == str(stations_csv.resolve())
        assert list(state["FileName"]) == ["01234567890.csv"]

        normalized_registry = pd.read_csv(stations_csv)
        assert "raw_data_pulled" not in normalized_registry.columns
        assert "data_cleaned" not in normalized_registry.columns
        assert list(normalized_registry["FileName"]) == ["01234567890.csv", "01234567891.csv"]

    def test_materialize_raw_pull_state_corrects_station_id_and_preserves_existing_metadata(
        self,
        tmp_path: Path,
    ) -> None:
        stations_csv = tmp_path / "noaa_file_index" / "20260207" / "Stations.csv"
        stations_csv.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(
            [
                {
                    "ID": "00826099999",
                    "FileName": "00826099999.csv",
                    "NAME": "Pulled",
                    "raw_data_pulled": True,
                }
            ]
        ).to_csv(stations_csv, index=False)

        raw_pull_state_csv = tmp_path / "noaa_file_index" / "state" / "raw_pull_state.csv"
        raw_pull_state_csv.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(
            [
                {
                    "station_id": "826099999",
                    "FileName": "00826099999.csv",
                    "raw_data_pulled": True,
                    "raw_path": "/tmp/raw.parquet",
                    "pulled_at": "2026-03-14T00:00:00+00:00",
                    "registry_snapshot": "legacy",
                }
            ]
        ).to_csv(raw_pull_state_csv, index=False)

        pipeline.materialize_raw_pull_state(stations_csv)

        written_state = pipeline._load_raw_pull_state(raw_pull_state_csv)
        assert written_state.loc[0, "station_id"] == "00826099999"
        assert written_state.loc[0, "raw_path"] == "/tmp/raw.parquet"
        assert written_state.loc[0, "pulled_at"] == "2026-03-14T00:00:00+00:00"
        assert written_state.loc[0, "registry_snapshot"] == str(stations_csv.resolve())

    def test_pick_random_station_uses_separate_raw_pull_state(
        self,
        tmp_path: Path,
    ) -> None:
        stations_csv = tmp_path / "Stations.csv"
        pd.DataFrame(
            [
                {"ID": "01234567890", "FileName": "01234567890.csv"},
                {"ID": "01234567891", "FileName": "01234567891.csv"},
            ]
        ).to_csv(stations_csv, index=False)

        raw_pull_state_csv = tmp_path / "state" / "raw_pull_state.csv"
        raw_pull_state_csv.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(
            [
                {
                    "station_id": "01234567890",
                    "FileName": "01234567890.csv",
                    "raw_data_pulled": True,
                    "raw_path": "/tmp/raw.parquet",
                    "pulled_at": "2026-03-14T00:00:00+00:00",
                    "registry_snapshot": str(stations_csv),
                }
            ]
        ).to_csv(raw_pull_state_csv, index=False)

        picked = pipeline.pick_random_station(
            stations_csv,
            raw_pull_state_csv=raw_pull_state_csv,
            seed=7,
        )
        assert picked["FileName"] == "01234567891.csv"

    def test_pull_random_station_raw_writes_separate_state_file(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        stations_csv = tmp_path / "Stations.csv"
        pd.DataFrame([{"ID": "01234567890", "FileName": "01234567890.csv"}]).to_csv(
            stations_csv, index=False
        )
        output_dir = tmp_path / "raw_output"
        raw_pull_state_csv = tmp_path / "state" / "raw_pull_state.csv"

        monkeypatch.setattr(
            pipeline,
            "download_location_data",
            lambda *_args, **_kwargs: pd.DataFrame({"DATE": ["2020-01-01T00:00:00"], "TMP": ["0010,1"]}),
        )

        output_path = pipeline.pull_random_station_raw(
            stations_csv,
            years=[2020],
            output_dir=output_dir,
            sleep_seconds=0.0,
            seed=1,
            raw_pull_state_csv=raw_pull_state_csv,
        )

        assert output_path is not None
        assert output_path.exists()
        state = pd.read_csv(raw_pull_state_csv)
        assert state.loc[0, "FileName"] == "01234567890.csv"
        assert bool(state.loc[0, "raw_data_pulled"]) is True
        assert Path(state.loc[0, "raw_path"]).resolve() == output_path.resolve()

    def test_pull_random_station_raw_skips_when_lock_is_held(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        stations_csv = tmp_path / "Stations.csv"
        pd.DataFrame([{"ID": "01234567890", "FileName": "01234567890.csv"}]).to_csv(
            stations_csv, index=False
        )
        output_dir = tmp_path / "raw_output"
        raw_pull_state_csv = tmp_path / "state" / "raw_pull_state.csv"
        lock_path = pipeline._raw_pull_lock_path(raw_pull_state_csv)
        lock_path.parent.mkdir(parents=True, exist_ok=True)

        def fail_download(*_: object, **__: object) -> pd.DataFrame:
            raise AssertionError("download_location_data should not run when lock is held")

        monkeypatch.setattr(pipeline, "download_location_data", fail_download)

        with lock_path.open("a+", encoding="utf-8") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            result = pipeline.pull_random_station_raw(
                stations_csv,
                years=[2020],
                output_dir=output_dir,
                sleep_seconds=0.0,
                seed=1,
                raw_pull_state_csv=raw_pull_state_csv,
            )

        assert result is None

    def test_cli_research_reports_invokes_builder(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.chdir(tmp_path)
        station_dir = tmp_path / "output" / "01234567890"
        station_dir.mkdir(parents=True)

        called: dict[str, object] = {}

        def fake_build_reports_for_station_dir(
            station_dir_arg: Path,
            **kwargs: object,
        ) -> dict[str, Path]:
            called["station_dir"] = station_dir_arg
            called.update(kwargs)
            return {}

        monkeypatch.setattr(cli, "build_reports_for_station_dir", fake_build_reports_for_station_dir)
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "prog",
                "research-reports",
                str(station_dir),
                "--access-date",
                "2026-02-28",
                "--authors",
                "Test Author",
            ],
        )
        cli.main()

        assert called["station_dir"].resolve() == station_dir.resolve()
        assert called["access_date"] == "2026-02-28"
        assert called["authors"] == "Test Author"

    def test_cli_reprocess_output_dir_runs_clean_and_reports(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.chdir(tmp_path)
        output_root = tmp_path / "output"
        station_ok = output_root / "01234567890"
        station_skip = output_root / "NO_RAW"
        station_ok.mkdir(parents=True)
        station_skip.mkdir(parents=True)

        pd.DataFrame({"DATE": ["2020-01-01T00:00:00"], "TMP": ["0100,1"]}).to_csv(
            station_ok / "LocationData_Raw.csv",
            index=False,
        )

        sample = pd.DataFrame({"value": [1]})
        process_called: dict[str, object] = {}
        report_called: dict[str, object] = {}

        def fake_process_location_from_raw(raw: pd.DataFrame, **kwargs: object) -> LocationDataOutputs:
            process_called["rows"] = len(raw)
            process_called.update(kwargs)
            return LocationDataOutputs(
                raw=sample,
                cleaned=sample,
                hourly=sample,
                monthly=sample,
                yearly=sample,
            )

        def fake_build_reports_for_station_dir(station_dir: Path, **kwargs: object) -> dict[str, Path]:
            report_called["station_dir"] = station_dir
            report_called.update(kwargs)
            return {}

        monkeypatch.setattr(cli, "process_location_from_raw", fake_process_location_from_raw)
        monkeypatch.setattr(cli, "build_reports_for_station_dir", fake_build_reports_for_station_dir)

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "prog",
                "reprocess-output-dir",
                "--output-root",
                str(output_root),
                "--aggregation-strategy",
                "fixed_hour",
                "--fixed-hour",
                "6",
                "--min-days-per-month",
                "18",
                "--min-months-per-year",
                "10",
                "--access-date",
                "2026-02-28",
                "--authors",
                "Test Author",
            ],
        )
        cli.main()

        assert process_called["rows"] == 1
        assert process_called["aggregation_strategy"] == "fixed_hour"
        assert process_called["fixed_hour"] == 6
        assert process_called["min_days_per_month"] == 18
        assert process_called["min_months_per_year"] == 10

        assert report_called["station_dir"].resolve() == station_ok.resolve()
        assert report_called["access_date"] == "2026-02-28"
        assert report_called["authors"] == "Test Author"

        assert (station_ok / "LocationData_Cleaned.csv").exists()
        assert not (station_skip / "LocationData_Cleaned.csv").exists()
        mapping_path = output_root / "domains" / "station_metadata_mapping.csv"
        assert mapping_path.exists()
        mapping_df = pd.read_csv(mapping_path)
        assert {"station_id", "station_slug", "station_name", "LATITUDE", "LONGITUDE", "ELEVATION"}.issubset(mapping_df.columns)

    def test_cli_reprocess_output_dir_defaults_domains_to_release_sibling(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.chdir(tmp_path)
        output_root = tmp_path / "release" / "build_TEST" / "canonical_cleaned"
        station_ok = output_root / "01234567890"
        station_ok.mkdir(parents=True)

        pd.DataFrame({"DATE": ["2020-01-01T00:00:00"], "TMP": ["0100,1"]}).to_csv(
            station_ok / "LocationData_Raw.csv",
            index=False,
        )

        sample = pd.DataFrame({"value": [1]})

        def fake_process_location_from_raw(raw: pd.DataFrame, **kwargs: object) -> LocationDataOutputs:
            _ = kwargs
            return LocationDataOutputs(
                raw=sample,
                cleaned=sample,
                hourly=sample,
                monthly=sample,
                yearly=sample,
            )

        monkeypatch.setattr(cli, "process_location_from_raw", fake_process_location_from_raw)
        monkeypatch.setattr(
            cli,
            "build_reports_for_station_dir",
            lambda *_args, **_kwargs: {},
        )

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "prog",
                "reprocess-output-dir",
                "--output-root",
                str(output_root),
                "--access-date",
                "2026-02-28",
            ],
        )
        cli.main()

        domains_root = output_root.parent / "domains"
        assert (domains_root / "station_split_manifest.csv").exists()
        assert (domains_root / "station_metadata_mapping.csv").exists()

    def test_cli_cleaning_run_invokes_runner_with_batch_defaults(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(cli, "datetime", _FakeDateTime)
        input_root = tmp_path / "inputs"
        input_root.mkdir(parents=True)

        called: dict[str, object] = {}

        def fake_run_cleaning_run(config: object) -> dict[str, object]:
            called["config"] = config
            return {}

        monkeypatch.setattr(cli, "run_cleaning_run", fake_run_cleaning_run)
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "prog",
                "cleaning-run",
                "--mode",
                "batch_parquet_dir",
                "--input-root",
                str(input_root),
                "--input-format",
                "parquet",
                "--station-id",
                "01234567890,09876543210",
                "--limit",
                "5",
            ],
        )
        cli.main()

        config = called["config"]
        assert str(config.mode) == "batch_parquet_dir"
        assert str(config.input_format) == "parquet"
        assert config.input_root.resolve() == input_root.resolve()
        assert config.station_ids == ("01234567890", "09876543210")
        assert config.limit == 5
        assert config.run_id == "20250101T000000Z"
        assert config.manifest_first is True
        assert config.write_flags.write_cleaned_station is True
        assert config.write_flags.write_domain_splits is False
        assert config.write_flags.write_station_quality_profile is True
        assert config.write_flags.write_station_reports is False
        assert config.write_flags.write_global_summary is True
        assert config.output_root.resolve() == (
            tmp_path / "release" / "build_20250101T000000Z" / "canonical_cleaned"
        ).resolve()
        assert config.manifest_root.resolve() == (
            tmp_path / "release" / "build_20250101T000000Z" / "manifests"
        ).resolve()

    def test_cli_cleaning_run_honors_test_mode_flag_overrides(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.chdir(tmp_path)
        input_root = tmp_path / "inputs"
        input_root.mkdir(parents=True)

        called: dict[str, object] = {}

        def fake_run_cleaning_run(config: object) -> dict[str, object]:
            called["config"] = config
            return {}

        monkeypatch.setattr(cli, "run_cleaning_run", fake_run_cleaning_run)
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "prog",
                "cleaning-run",
                "--mode",
                "test_csv_dir",
                "--input-root",
                str(input_root),
                "--input-format",
                "csv",
                "--run-id",
                "RUN_123",
                "--manifest-first",
                "--no-write-domain-splits",
                "--write-station-reports",
            ],
        )
        cli.main()

        config = called["config"]
        assert str(config.mode) == "test_csv_dir"
        assert str(config.input_format) == "csv"
        assert config.run_id == "RUN_123"
        assert config.manifest_first is True
        assert config.write_flags.write_cleaned_station is True
        assert config.write_flags.write_domain_splits is False
        assert config.write_flags.write_station_quality_profile is True
        assert config.write_flags.write_station_reports is True
        assert config.write_flags.write_global_summary is False

    def test_cli_cleaning_run_invokes_runner_with_test_parquet_defaults(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(cli, "datetime", _FakeDateTime)
        input_root = tmp_path / "inputs"
        input_root.mkdir(parents=True)

        called: dict[str, object] = {}

        def fake_run_cleaning_run(config: object) -> dict[str, object]:
            called["config"] = config
            return {}

        monkeypatch.setattr(cli, "run_cleaning_run", fake_run_cleaning_run)
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "prog",
                "cleaning-run",
                "--mode",
                "test_parquet_dir",
                "--input-root",
                str(input_root),
                "--input-format",
                "parquet",
            ],
        )
        cli.main()

        config = called["config"]
        assert str(config.mode) == "test_parquet_dir"
        assert str(config.input_format) == "parquet"
        assert config.input_root.resolve() == input_root.resolve()
        assert config.run_id == "20250101T000000Z"
        assert config.manifest_first is False
        assert config.write_flags.write_cleaned_station is True
        assert config.write_flags.write_domain_splits is True
        assert config.write_flags.write_station_quality_profile is True
        assert config.write_flags.write_station_reports is False
        assert config.write_flags.write_global_summary is False
        assert config.output_root.resolve() == (
            tmp_path / "release" / "build_20250101T000000Z" / "canonical_cleaned"
        ).resolve()
        assert config.manifest_root.resolve() == (
            tmp_path / "release" / "build_20250101T000000Z" / "manifests"
        ).resolve()

    def test_cli_pdf_to_markdown_invokes_converter(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.chdir(tmp_path)
        pdf_path = tmp_path / "input.pdf"
        pdf_path.write_text("placeholder")
        out_path = tmp_path / "out.md"

        called: dict[str, object] = {}

        def fake_convert_pdf_to_markdown(
            input_pdf: Path,
            output_md: Path | None = None,
            include_page_headers: bool = True,
        ) -> Path:
            called["input_pdf"] = input_pdf
            called["output_md"] = output_md
            called["include_page_headers"] = include_page_headers
            return out_path

        monkeypatch.setattr(cli, "convert_pdf_to_markdown", fake_convert_pdf_to_markdown)

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "prog",
                "pdf-to-markdown",
                str(pdf_path),
                "--output-md",
                str(out_path),
                "--no-page-headers",
            ],
        )
        cli.main()

        assert called["input_pdf"].resolve() == pdf_path.resolve()
        assert called["output_md"].resolve() == out_path.resolve()
        assert called["include_page_headers"] is False
