"""Reproducibility test for the sample cleaning pipeline."""

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


def test_reproducibility_example_output_matches_expected(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "reproducibility" / "run_pipeline_example.py"
    tracked_anchor_path = repo_root / "reproducibility" / "sample_station_cleaned.csv"
    expected_path = repo_root / "reproducibility" / "sample_station_cleaned_expected.csv"
    output_path = tmp_path / "sample_station_cleaned.csv"

    subprocess.run(
        [sys.executable, str(script_path), "--out", str(output_path)],
        check=True,
        cwd=repo_root,
    )

    output_text = output_path.read_text(encoding="utf-8")
    tracked_anchor_text = tracked_anchor_path.read_text(encoding="utf-8")
    expected_text = expected_path.read_text(encoding="utf-8")
    if output_text != expected_text:
        diff = _diff_text(expected_text, output_text)
        raise AssertionError("Reproducibility output mismatch:\n" + diff)
    if tracked_anchor_text != expected_text:
        diff = _diff_text(expected_text, tracked_anchor_text)
        raise AssertionError("Tracked reproducibility anchor drifted:\n" + diff)
