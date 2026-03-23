import csv
import re
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
README_PATH = PROJECT_ROOT / "README.md"
DOCS_INDEX_PATH = PROJECT_ROOT / "docs" / "README.md"
RUN_MODES_PATH = PROJECT_ROOT / "docs" / "CLEANING_RUN_MODES.md"
ARTIFACT_BOUNDARY_POLICY_PATH = PROJECT_ROOT / "docs" / "ARTIFACT_BOUNDARY_POLICY.md"
ARCHIVE_README_PATH = PROJECT_ROOT / "docs" / "archive" / "README.md"
SNAPSHOT_README_PATH = (
    PROJECT_ROOT / "docs" / "archive" / "snapshots" / "noaa_file_index_20260207_README.md"
)
SUSPICIOUS_SUMMARY_PATH = (
    PROJECT_ROOT
    / "docs"
    / "reports"
    / "validation_artifacts"
    / "suspicious_coverage"
    / "suspicious_summary.md"
)
SPEC_COVERAGE_PATH = PROJECT_ROOT / "spec_coverage.csv"
GITIGNORE_PATH = PROJECT_ROOT / ".gitignore"
SPLIT_CLEANED_SCRIPT_PATH = PROJECT_ROOT / "scripts" / "split_cleaned_by_domain.py"
SPLIT_BY_STATION_SCRIPT_PATH = PROJECT_ROOT / "scripts" / "split_domains_by_station.py"

REQUIRED_README_SECTIONS = (
    "## What NOAA-Spec does",
    "## Why NOAA ISD is not analysis-ready",
    "## Installation",
    "## 5-minute example",
    "## Contracts and Validation",
    "## When to use / when not to use",
    "## Paper and docs links",
)


def _compute_suspicious_stats() -> tuple[int, float]:
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
    return suspicious_count, percentage


def test_readme_has_required_joss_sections() -> None:
    readme_text = README_PATH.read_text(encoding="utf-8")
    for section in REQUIRED_README_SECTIONS:
        assert section in readme_text


def test_docs_index_and_archive_docs_exist() -> None:
    assert DOCS_INDEX_PATH.exists()
    assert ARCHIVE_README_PATH.exists()
    assert SNAPSHOT_README_PATH.exists()


def test_archive_readme_documents_station_report_archive_location() -> None:
    archive_text = ARCHIVE_README_PATH.read_text(encoding="utf-8")
    assert "data/archive/station_reports_full/" in archive_text
    assert "not tracked in git" in archive_text.lower()
    assert "regenerated" in archive_text.lower()


def test_snapshot_readme_has_no_placeholder_cleaning_or_aggregation_sections() -> None:
    snapshot_text = SNAPSHOT_README_PATH.read_text(encoding="utf-8").lower()
    assert "cleaning cli entrypoint not yet implemented" not in snapshot_text
    assert "aggregation cli entrypoint not yet implemented" not in snapshot_text
    assert "placeholder only; cleaning pipeline is not yet wired for cron" not in snapshot_text
    assert "placeholder only; aggregation pipeline is not yet wired for cron" not in snapshot_text


def test_suspicious_summary_matches_spec_coverage() -> None:
    summary_text = SUSPICIOUS_SUMMARY_PATH.read_text(encoding="utf-8")

    count_match = re.search(r"Total Suspicious Entries\*\*:\s*(\d+)", summary_text)
    pct_match = re.search(r"Percentage of Total Rules\*\*:\s*([\d.]+)%", summary_text)

    assert count_match
    assert pct_match

    suspicious_count, suspicious_percentage = _compute_suspicious_stats()
    assert int(count_match.group(1)) == suspicious_count
    assert float(pct_match.group(1)) == round(suspicious_percentage, 2)


def test_cleaning_run_docs_enforce_release_contract_paths() -> None:
    run_modes_text = RUN_MODES_PATH.read_text(encoding="utf-8")
    expected_layout = "release/build_<run_id>/{canonical_cleaned,domains,quality_reports,manifests}"
    assert expected_layout in run_modes_text
    assert "artifacts/test_runs" not in run_modes_text
    assert "artifacts/parquet_runs" not in run_modes_text


def test_artifact_boundary_policy_declares_publication_and_runtime_surfaces() -> None:
    policy_text = ARTIFACT_BOUNDARY_POLICY_PATH.read_text(encoding="utf-8")
    assert "release/build_<build_id>/" in policy_text
    assert "output/" in policy_text
    assert "artifacts/test_runs/" in policy_text
    assert "docs/examples/" in policy_text
    assert "tests/fixtures/" in policy_text


def test_station_examples_are_curated_under_docs_examples() -> None:
    assert (PROJECT_ROOT / "docs" / "examples" / "stations").exists()
    assert (PROJECT_ROOT / "docs" / "examples" / "noaa_demo").exists()
    curated = sorted(path.name for path in (PROJECT_ROOT / "docs" / "examples" / "stations").iterdir())
    assert curated == ["03041099999", "16754399999", "94368099999"]


def test_operational_snapshots_are_not_tracked_in_publication_facing_paths() -> None:
    tracked_test_runs = subprocess.run(
        ["git", "ls-files", "artifacts/test_runs/**"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert tracked_test_runs == ""

    tracked_timing_logs = subprocess.run(
        ["git", "ls-files", "reprocess_timing*.log"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert tracked_timing_logs == ""


def test_legacy_split_scripts_do_not_duplicate_domain_contract_rules() -> None:
    split_cleaned_text = SPLIT_CLEANED_SCRIPT_PATH.read_text(encoding="utf-8")
    assert "from noaa_spec.domain_split import COMMON_COLUMNS, classify_columns" in split_cleaned_text
    assert "DOMAIN_RULES" not in split_cleaned_text
    assert "class DomainRule" not in split_cleaned_text

    split_by_station_text = SPLIT_BY_STATION_SCRIPT_PATH.read_text(encoding="utf-8").lower()
    assert "deprecated" in split_by_station_text
    assert "cleaning-run" in split_by_station_text


def test_gitignore_enforces_runtime_blocklist_and_station_archive_ignore() -> None:
    gitignore_text = GITIGNORE_PATH.read_text(encoding="utf-8")
    for expected_entry in (
        "output/",
        "artifacts/test_runs/",
        "artifacts/parquet_runs/",
        "data/archive/station_reports_full/",
    ):
        assert expected_entry in gitignore_text
