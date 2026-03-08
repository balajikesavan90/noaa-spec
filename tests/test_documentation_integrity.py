import csv
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
README_PATH = PROJECT_ROOT / "README.md"
SPEC_COVERAGE_PATH = PROJECT_ROOT / "spec_coverage.csv"
VALIDATION_PLAN_PATH = PROJECT_ROOT / "docs" / "PIPELINE_VALIDATION_PLAN.md"
NOAA_INDEX_README_PATH = PROJECT_ROOT / "noaa_file_index" / "20260207" / "README.md"
SUSPICIOUS_SUMMARY_PATH = (
    PROJECT_ROOT
    / "docs"
    / "validation_artifacts"
    / "suspicious_coverage"
    / "suspicious_summary.md"
)

REQUIRED_VALIDATION_PLAN_REFERENCES = (
    "tools/spec_coverage/generate_spec_coverage.py",
    "tools/spec_coverage/export_suspicious_summary.py",
    "tools/spec_coverage/generate_rule_provenance_ledger.py",
    "tools/rule_impact/generate_rule_impact_report.py",
    "tests/test_cleaning.py",
    "tests/test_qc_comprehensive.py",
    "tests/test_spec_coverage_generator.py",
    "tests/test_suspicious_coverage_integrity.py",
    "tests/test_documentation_integrity.py",
    "tests/test_integration.py",
    "tests/test_cleaning_runner.py",
    "tests/test_domain_split.py",
)

DISALLOWED_VALIDATION_PLAN_REFERENCES = (
    "tools/spec_coverage/export_suspicious_cases.py",
    "tests/test_suspicious_audit.py",
    "tools/spec_coverage/sample_audit_rules.py",
)

STALE_README_QUANTITATIVE_PHRASES = (
    "3,800+",
    "1,955+",
    "803 tests",
    "874 tests",
    "84 tests",
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


def test_validation_plan_references_existing_paths():
    validation_plan = VALIDATION_PLAN_PATH.read_text(encoding="utf-8")

    for relative_path in REQUIRED_VALIDATION_PLAN_REFERENCES:
        assert relative_path in validation_plan, f"Missing reference in plan: {relative_path}"
        assert (PROJECT_ROOT / relative_path).exists(), f"Referenced path missing: {relative_path}"


def test_validation_plan_excludes_stale_references():
    validation_plan = VALIDATION_PLAN_PATH.read_text(encoding="utf-8")

    for stale_reference in DISALLOWED_VALIDATION_PLAN_REFERENCES:
        assert stale_reference not in validation_plan, (
            f"Stale reference should not appear in plan: {stale_reference}"
        )


def test_noaa_index_readme_has_no_placeholder_cleaning_or_aggregation_sections():
    index_readme = NOAA_INDEX_README_PATH.read_text(encoding="utf-8")
    lowered = index_readme.lower()

    assert "cleaning cli entrypoint not yet implemented" not in lowered
    assert "aggregation cli entrypoint not yet implemented" not in lowered
    assert "placeholder only; cleaning pipeline is not yet wired for cron" not in lowered
    assert "placeholder only; aggregation pipeline is not yet wired for cron" not in lowered


def test_readme_excludes_known_stale_quantitative_claims():
    readme_text = README_PATH.read_text(encoding="utf-8")
    lowered = readme_text.lower()

    for stale_phrase in STALE_README_QUANTITATIVE_PHRASES:
        assert stale_phrase.lower() not in lowered, (
            f"Stale README phrase should not appear: {stale_phrase}"
        )
