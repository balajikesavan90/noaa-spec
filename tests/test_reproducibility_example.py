"""Reproducibility tests for the tracked public cleaning fixture."""

from __future__ import annotations

import difflib
import os
from pathlib import Path
import subprocess
import sys

import pytest


def _fixture_cases_from_checksum_manifest(repo_root: Path) -> tuple[str, ...]:
    manifest = repo_root / "reproducibility" / "checksums.sha256"
    fixtures: list[str] = []
    for line in manifest.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        _hash, rel_path = line.split(maxsplit=1)
        prefix = "reproducibility/"
        suffix = "/station_cleaned_expected.csv"
        if rel_path.startswith(prefix) and rel_path.endswith(suffix):
            fixtures.append(rel_path.removeprefix(prefix).removesuffix(suffix))
    return tuple(fixtures)


def _diff_text(expected: str, actual: str) -> str:
    diff = difflib.unified_diff(
        expected.splitlines(keepends=True),
        actual.splitlines(keepends=True),
        fromfile="expected",
        tofile="actual",
    )
    return "".join(diff)


def _assert_fixture_matches_expected(
    repo_root: Path, tmp_path: Path, *, fixture_name: str
) -> None:
    raw_path = repo_root / "reproducibility" / fixture_name / "station_raw.csv"
    expected_path = (
        repo_root / "reproducibility" / fixture_name / "station_cleaned_expected.csv"
    )
    output_path = tmp_path / f"{fixture_name}_station_cleaned.csv"
    env = os.environ.copy()
    src_path = str(repo_root / "src")
    env["PYTHONPATH"] = (
        f"{src_path}{os.pathsep}{env['PYTHONPATH']}"
        if env.get("PYTHONPATH")
        else src_path
    )

    subprocess.run(
        [
            sys.executable,
            "-m",
            "noaa_spec.cli",
            "clean",
            str(raw_path),
            str(output_path),
        ],
        check=True,
        cwd=repo_root,
        env=env,
    )

    output_text = output_path.read_text(encoding="utf-8")
    expected_text = expected_path.read_text(encoding="utf-8")
    if output_text != expected_text:
        diff = _diff_text(expected_text, output_text)
        raise AssertionError(
            f"Reproducibility output mismatch for {fixture_name}:\n" + diff
        )


def _assert_public_example_script_matches_expected(
    repo_root: Path, tmp_path: Path, *, output_name: str
) -> None:
    script_path = repo_root / "reproducibility" / "run_pipeline_example.py"
    expected_path = (
        repo_root / "reproducibility" / "minimal" / "station_cleaned_expected.csv"
    )
    output_path = tmp_path / output_name

    subprocess.run(
        [sys.executable, str(script_path), str(output_path)],
        check=True,
        cwd=repo_root,
    )

    output_text = output_path.read_text(encoding="utf-8")
    expected_text = expected_path.read_text(encoding="utf-8")
    if output_text != expected_text:
        diff = _diff_text(expected_text, output_text)
        raise AssertionError(
            "Reproducibility output mismatch for public example:\n" + diff
        )


def test_reproducibility_fixture_output_matches_expected(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    fixture_cases = _fixture_cases_from_checksum_manifest(repo_root)
    assert fixture_cases, "No expected reproducibility fixtures in checksum manifest."
    for fixture_name in fixture_cases:
        _assert_fixture_matches_expected(repo_root, tmp_path, fixture_name=fixture_name)


def test_minimal_reproducibility_example_script_matches_expected(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    _assert_public_example_script_matches_expected(
        repo_root,
        tmp_path,
        output_name="minimal_station_cleaned.csv",
    )
