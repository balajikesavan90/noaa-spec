"""Guardrail checks that protect parser/spec coverage guarantees."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_spec_coverage_has_no_implemented_without_tests_or_suspicious_rows() -> None:
    coverage_path = PROJECT_ROOT / "spec_coverage.csv"
    coverage = pd.read_csv(coverage_path, dtype=str).fillna("")

    implemented_without_tests = (
        (coverage["code_implemented"].str.upper() == "TRUE")
        & (coverage["test_covered_any"].str.upper() != "TRUE")
    ).sum()
    suspicious = (
        (coverage["code_implemented"].str.upper() != "TRUE")
        & (coverage["test_covered_any"].str.upper() == "TRUE")
    ).sum()

    assert int(implemented_without_tests) == 0
    assert int(suspicious) == 0
