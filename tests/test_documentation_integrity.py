import csv
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
README_PATH = PROJECT_ROOT / "README.md"
SPEC_COVERAGE_PATH = PROJECT_ROOT / "spec_coverage.csv"
SUSPICIOUS_SUMMARY_PATH = (
    PROJECT_ROOT
    / "docs"
    / "validation_artifacts"
    / "suspicious_coverage"
    / "suspicious_summary.md"
)


def _compute_suspicious_stats() -> tuple[int, int, float]:
    with open(SPEC_COVERAGE_PATH, "r", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    suspicious_count = 0
    for row in rows:
        test_covered_any = row.get("test_covered_any", "").strip().upper()
        code_implemented = row.get("code_implemented", "").strip().upper()
        if test_covered_any == "TRUE" and code_implemented == "FALSE":
            suspicious_count += 1

    total_rules = len(rows)
    percentage = (suspicious_count / total_rules * 100.0) if total_rules else 0.0
    return suspicious_count, total_rules, percentage


def test_readme_compatibility_docs_exist():
    for compatibility_doc in (
        PROJECT_ROOT / "QC_SIGNALS_ARCHITECTURE.md",
        PROJECT_ROOT / "CLEANING_RECOMMENDATIONS.md",
    ):
        assert compatibility_doc.exists(), f"Missing compatibility doc: {compatibility_doc}"


def test_readme_suspicious_kpi_matches_spec_coverage():
    readme_text = README_PATH.read_text(encoding="utf-8")
    match = re.search(
        r"Current suspicious entries:\s*\*\*(\d+)\*\*\s*\(([\d.]+)% of rules\)",
        readme_text,
    )

    assert match, "README suspicious KPI line is missing or malformed"

    documented_count = int(match.group(1))
    documented_percentage = float(match.group(2))

    suspicious_count, _, suspicious_percentage = _compute_suspicious_stats()
    assert documented_count == suspicious_count
    assert documented_percentage == round(suspicious_percentage, 1)


def test_suspicious_summary_matches_spec_coverage():
    summary_text = SUSPICIOUS_SUMMARY_PATH.read_text(encoding="utf-8")

    count_match = re.search(r"Total Suspicious Entries\*\*:\s*(\d+)", summary_text)
    pct_match = re.search(r"Percentage of Total Rules\*\*:\s*([\d.]+)%", summary_text)

    assert count_match, "Suspicious summary count line is missing"
    assert pct_match, "Suspicious summary percentage line is missing"

    documented_count = int(count_match.group(1))
    documented_percentage = float(pct_match.group(1))

    suspicious_count, _, suspicious_percentage = _compute_suspicious_stats()
    assert documented_count == suspicious_count
    assert documented_percentage == round(suspicious_percentage, 2)
