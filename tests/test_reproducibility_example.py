"""Reproducibility tests for the tracked cleaning examples."""

from __future__ import annotations

from pathlib import Path
import difflib
import subprocess
import sys


def _diff_text(expected: str, actual: str) -> str:
    diff = difflib.unified_diff(
        expected.splitlines(keepends=True),
        actual.splitlines(keepends=True),
        fromfile="expected",
        tofile="actual",
    )
    return "".join(diff)


def _assert_example_matches_expected(
    repo_root: Path, tmp_path: Path, *, example: str, output_name: str
) -> None:
    script_path = repo_root / "reproducibility" / "run_pipeline_example.py"
    example_root = repo_root / "reproducibility" / example
    tracked_anchor_path = example_root / "station_cleaned.csv"
    expected_path = example_root / "station_cleaned_expected.csv"
    output_path = tmp_path / output_name

    subprocess.run(
        [sys.executable, str(script_path), "--example", example, "--out", str(output_path)],
        check=True,
        cwd=repo_root,
    )

    output_text = output_path.read_text(encoding="utf-8")
    tracked_anchor_text = tracked_anchor_path.read_text(encoding="utf-8")
    expected_text = expected_path.read_text(encoding="utf-8")
    if output_text != expected_text:
        diff = _diff_text(expected_text, output_text)
        raise AssertionError(f"Reproducibility output mismatch for {example}:\n" + diff)
    if tracked_anchor_text != expected_text:
        diff = _diff_text(expected_text, tracked_anchor_text)
        raise AssertionError(f"Tracked reproducibility anchor drifted for {example}:\n" + diff)


def test_minimal_reproducibility_example_output_matches_expected(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    _assert_example_matches_expected(
        repo_root,
        tmp_path,
        example="minimal",
        output_name="minimal_station_cleaned.csv",
    )


def test_full_station_reproducibility_example_output_matches_expected(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    _assert_example_matches_expected(
        repo_root,
        tmp_path,
        example="full_station",
        output_name="full_station_cleaned.csv",
    )
