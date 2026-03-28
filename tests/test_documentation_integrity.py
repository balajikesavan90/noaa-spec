import csv
import re
import shutil
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
README_PATH = PROJECT_ROOT / "README.md"
DOCS_INDEX_PATH = PROJECT_ROOT / "docs" / "README.md"
REVIEWER_GUIDE_PATH = PROJECT_ROOT / "docs" / "REVIEWER_GUIDE.md"
REPRODUCIBILITY_README_PATH = PROJECT_ROOT / "reproducibility" / "README.md"
RUN_MODES_PATH = PROJECT_ROOT / "docs" / "operations" / "CLEANING_RUN_MODES.md"
OPERATIONS_README_PATH = PROJECT_ROOT / "docs" / "operations" / "README.md"
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
CHECK_REVIEWER_ENV_PATH = PROJECT_ROOT / "scripts" / "check_reviewer_env.sh"
VERIFY_REPRODUCIBILITY_PATH = PROJECT_ROOT / "scripts" / "verify_reproducibility.sh"

REQUIRED_README_SECTIONS = (
    "## Supported Platform",
    "## What NOAA-Spec does",
    "## Why NOAA ISD is not analysis-ready",
    "## Installation",
    "## System Prerequisites",
    "## Reviewer Quickstart",
    "## Contracts and Validation",
    "## When to use / when not to use",
    "## Paper and docs links",
)

CANONICAL_QUICKSTART = """```bash
bash scripts/check_reviewer_env.sh
python3 -m venv .review-venv
source .review-venv/bin/activate
which python
python -m pip install --upgrade pip
pip install -r requirements-review.txt
pip install -e .
python reproducibility/run_pipeline_example.py --example minimal --out /tmp/noaa-spec-sample.csv
bash scripts/verify_reproducibility.sh
pytest -q
```"""

INTERNAL_RECORD_BANNER = "INTERNAL DEVELOPMENT RECORD — NOT REVIEWER EVIDENCE"


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


def _require_git() -> None:
    assert shutil.which("git"), "git is required for this test suite. Install it with: sudo apt-get install -y git"


def test_readme_has_required_joss_sections() -> None:
    readme_text = README_PATH.read_text(encoding="utf-8")
    for section in REQUIRED_README_SECTIONS:
        assert section in readme_text


def test_readme_defines_linux_only_supported_platform() -> None:
    text = README_PATH.read_text(encoding="utf-8")
    assert "This reviewer workflow is validated on Linux (Ubuntu/Debian-like systems) with Python 3.12+ and bash." in text
    assert "Other platforms (macOS, Windows) are not part of the canonical reviewer path for this revision." in text


def test_readme_lists_explicit_system_prerequisites() -> None:
    text = README_PATH.read_text(encoding="utf-8")
    for expected in (
        "- `python3`",
        "- `python3-venv`",
        "- `git`",
        "- `bash`",
        "- `sha256sum`",
        "sudo apt-get update",
        "sudo apt-get install -y python3 python3-venv git coreutils bash",
        "These are OS-level dependencies and are not installed via pip.",
    ):
        assert expected in text


def test_reviewer_docs_use_single_linux_quickstart() -> None:
    readme_text = README_PATH.read_text(encoding="utf-8")
    assert CANONICAL_QUICKSTART in readme_text
    assert readme_text.count("## Reviewer Quickstart") == 1
    assert "The canonical reviewer example is under `reproducibility/minimal/`." in readme_text
    assert "## Supported Reviewer Commands" not in readme_text
    assert "Poetry" not in readme_text
    assert "poetry" not in readme_text

    reproducibility_text = REPRODUCIBILITY_README_PATH.read_text(encoding="utf-8")
    assert "The supported reproducibility path for this revision is the Linux reviewer workflow in the root [README.md](../README.md)." in reproducibility_text
    assert "The supported reviewer interpreter requirement is Python 3.12+." in reproducibility_text
    assert "The canonical reviewer example is under `reproducibility/minimal/`." in reproducibility_text
    assert "requirements-review.txt" in reproducibility_text
    assert "pip install -e ." in reproducibility_text
    assert "sha256sum" in reproducibility_text
    assert "Additional tracked non-canonical fixture coverage:" in reproducibility_text
    assert "reproducibility/full_station/station_cleaned_expected.csv" in reproducibility_text
    assert "No archived release bundle is linked for this revision." in reproducibility_text
    assert "poetry" not in reproducibility_text.lower()

    guide_text = REVIEWER_GUIDE_PATH.read_text(encoding="utf-8")
    assert "Use the root [README.md](../README.md) line-by-line." in guide_text
    assert "The supported reviewer interpreter requirement is Python 3.12+." in guide_text
    assert "The canonical reviewer example is under `reproducibility/minimal/`." in guide_text
    assert "No archived release bundle is linked for this revision." in guide_text
    assert "poetry" not in guide_text.lower()


def test_readme_and_reproducibility_docs_define_authoritative_dependency_story() -> None:
    readme_text = README_PATH.read_text(encoding="utf-8")
    reproducibility_text = REPRODUCIBILITY_README_PATH.read_text(encoding="utf-8")

    assert "`requirements-review.txt` is the exact tested reviewer dependency set for this revision." in readme_text
    assert "`pip install -e .` installs the `noaa_spec` package from this repository checkout." in readme_text
    assert "Tested in a fresh virtual environment with no pre-installed package." in readme_text
    assert "For this revision, only the Reviewer Quickstart and `reproducibility/README.md` define the supported reproducibility path." in readme_text
    assert "`requirements-review.txt` is the exact tested reviewer dependency set for this revision." in reproducibility_text
    assert "`pip install -e .` installs the `noaa_spec` package from this repository checkout." in reproducibility_text


def test_reviewer_scripts_enforce_linux_prerequisites_and_checksum_verification() -> None:
    env_text = CHECK_REVIEWER_ENV_PATH.read_text(encoding="utf-8")
    verify_text = VERIFY_REPRODUCIBILITY_PATH.read_text(encoding="utf-8")

    assert "for command_name in python3 git bash sha256sum; do" in env_text
    assert "command -v \"${command_name}\"" in env_text
    assert "python3 -m venv" in env_text
    assert "python3 must be Python 3.12 or newer" in env_text
    assert "Missing python3-venv. Run: sudo apt-get install python3-venv" in env_text
    assert "test_venv_tmp" in env_text
    assert "sudo apt-get install -y python3 python3-venv git coreutils bash" in env_text

    assert "command -v sha256sum" in verify_text
    assert "FAIL: sha256sum is required for reproducibility verification." in verify_text
    assert "python reproducibility/run_pipeline_example.py --example minimal --out" in verify_text
    assert "PASS: reproducibility verification succeeded." in verify_text


def test_reproducibility_fixtures_are_tracked_and_legacy_flat_samples_are_removed() -> None:
    _require_git()

    tracked_reproducibility = subprocess.run(
        ["git", "ls-files", "reproducibility"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()

    assert "reproducibility/minimal/station_raw.csv" in tracked_reproducibility
    assert "reproducibility/minimal/station_cleaned.csv" in tracked_reproducibility
    assert "reproducibility/minimal/station_cleaned_expected.csv" in tracked_reproducibility
    assert "reproducibility/full_station/station_raw.csv" in tracked_reproducibility
    assert "reproducibility/full_station/station_cleaned.csv" in tracked_reproducibility
    assert "reproducibility/full_station/station_cleaned_expected.csv" in tracked_reproducibility
    assert "reproducibility/sample_station_cleaned.csv" not in tracked_reproducibility
    assert "reproducibility/sample_station_cleaned_expected.csv" not in tracked_reproducibility


def test_readme_includes_expected_reproducibility_hash() -> None:
    readme_text = README_PATH.read_text(encoding="utf-8")
    expected_hash = (
        "b48aba1b8a304451dc3874b963d76275bf79ad68c6f28d9190e0e636f2887597"
    )
    assert f"Expected SHA256: `{expected_hash}`" in readme_text


def test_docs_index_and_archive_docs_exist() -> None:
    assert DOCS_INDEX_PATH.exists()
    assert OPERATIONS_README_PATH.exists()
    assert ARCHIVE_README_PATH.exists()
    assert SNAPSHOT_README_PATH.exists()


def test_archive_and_report_markdown_files_have_internal_record_banner() -> None:
    markdown_paths = sorted((PROJECT_ROOT / "docs" / "archive").rglob("*.md"))
    markdown_paths.extend(sorted((PROJECT_ROOT / "docs" / "reports").rglob("*.md")))
    assert markdown_paths
    for path in markdown_paths:
        text = path.read_text(encoding="utf-8")
        assert text.startswith(f"# {INTERNAL_RECORD_BANNER}")


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
    operations_text = OPERATIONS_README_PATH.read_text(encoding="utf-8")
    expected_layout = "release/build_<run_id>/{canonical_cleaned,domains,quality_reports,manifests}"
    assert "NOT part of reviewer reproducibility" in operations_text
    assert expected_layout in run_modes_text
    assert "artifacts/test_runs" not in run_modes_text
    assert "artifacts/parquet_runs" not in run_modes_text


def test_release_surface_is_a_non_evidence_stub() -> None:
    release_readme = PROJECT_ROOT / "release" / "README.md"
    assert release_readme.exists()
    text = release_readme.read_text(encoding="utf-8")
    assert "NON-EVIDENCE PLACEHOLDER — NOT PART OF REVIEWER VERIFICATION FOR THIS REVISION" in text
    assert "No archived release bundle is linked for this revision." in text
    assert not (PROJECT_ROOT / "release" / "sample_build").exists()


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
    _require_git()

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
