from pathlib import Path
import pytest

from scripts.run_readme_commands import _normalize_line, _should_skip


PROJECT_ROOT = Path(__file__).resolve().parent.parent
README_PATH = PROJECT_ROOT / "README.md"
DOCS_INDEX_PATH = PROJECT_ROOT / "docs" / "README.md"
DOCS_OUTPUT_GUIDE_PATH = PROJECT_ROOT / "docs" / "UNDERSTANDING_OUTPUT.md"
MAINTAINER_INDEX_PATH = PROJECT_ROOT / "maintainer" / "README.md"
MAINTAINER_DOCS_INDEX_PATH = PROJECT_ROOT / "maintainer" / "docs" / "README.md"
EXAMPLES_README_PATH = PROJECT_ROOT / "examples" / "README.md"
DOCS_EXAMPLES_README_PATH = PROJECT_ROOT / "docs" / "examples" / "README.md"
PUBLIC_REPRODUCIBILITY_PATH = PROJECT_ROOT / "REPRODUCIBILITY.md"
REPRODUCIBILITY_README_PATH = PROJECT_ROOT / "reproducibility" / "README.md"
INTERNAL_REPORTS_DIR = PROJECT_ROOT / "maintainer" / "docs" / "reports"
INTERNAL_ARCHIVE_DIR = PROJECT_ROOT / "maintainer" / "docs" / "archive"
INTERNAL_RECORD_BANNER = "INTERNAL DEVELOPMENT RECORD — NOT REVIEWER EVIDENCE"


def test_readme_locks_public_contribution_and_workflow() -> None:
    text = README_PATH.read_text(encoding="utf-8")

    for section in (
        "## JOSS Scope",
        "## Docker First Run",
        "## Optional Local Install",
        "## Run The Canonical Contract",
        "## Optional Derived Views",
        "## Minimal Workflow",
        "## Further Reading",
        "## Quick Reviewer Inspection",
        "## Reproducibility Verification",
        "## Docs",
    ):
        assert section in text

    assert "deterministic canonicalization layer" in text
    assert "bundled checksum-backed reproducibility fixture" in text
    assert "For independent reviewer verification and the cleanest first run, use Docker" in text
    assert "recommended reviewer-safe path" in text
    assert "NOAA-Spec currently declares support for Python `>=3.11,<3.13`" in text
    assert "reviewers should use Python 3.11 or 3.12 for the local path" in text
    assert "Python 3.13 is not yet supported" in text
    assert "install Python 3.12 first and then continue" in text
    assert "py -3.12 -m venv .venv" in text
    assert "python3.12 -m venv .venv" in text
    assert "noaa-spec clean reproducibility/minimal/station_raw.csv /tmp/station_cleaned.csv" in text
    assert "noaa-spec clean reproducibility/minimal/station_raw.csv /tmp/station_metadata.csv --view metadata" in text
    assert "pathlib.Path('/tmp/station_cleaned.csv').read_bytes()" in text
    assert "docker build -f Dockerfile -t noaa-spec-review ." in text
    assert "TMP__qc_reason" in text
    assert "SENTINEL_MISSING" in text
    assert "The canonical dataset defines the reproducible interpretation contract." in text
    assert "many users begin with a smaller derived view" in text
    assert "Optional views are narrower usability-oriented datasets derived from that canonical output" in text
    assert "`metadata`" in text
    assert "clouds_visibility" in text
    assert "intentionally minimal (5 rows)" in text


def test_docs_index_points_to_single_first_run_and_reproducibility_path() -> None:
    text = DOCS_INDEX_PATH.read_text(encoding="utf-8")

    assert "README.md](../README.md)" in text
    assert "[UNDERSTANDING_OUTPUT.md](UNDERSTANDING_OUTPUT.md)" in text
    assert "[../REPRODUCIBILITY.md](../REPRODUCIBILITY.md)" in text
    assert "[examples/CANONICAL_WALKTHROUGH.md](examples/CANONICAL_WALKTHROUGH.md)" in text
    assert "small public documentation set" in text
    assert "canonical `noaa-spec clean` workflow" in text


def test_output_guide_provides_practical_subset_and_qc_context() -> None:
    output_text = DOCS_OUTPUT_GUIDE_PATH.read_text(encoding="utf-8")

    assert "A 10-column subset" in output_text
    assert "Where to start" in output_text
    assert "How most users should approach this output" in output_text
    assert "Practical downstream subset" in output_text
    assert "Optional views" in output_text
    assert "Sentinel handling" in output_text
    assert "QC flags" in output_text
    assert "Missing values" in output_text
    assert "BEFORE -> AFTER example" in output_text
    assert "temperature_c" in output_text
    assert "TMP__qc_reason=SENTINEL_MISSING" in output_text
    assert "`--view`" in output_text
    assert "derived from the canonical table" in output_text
    assert "defines the reproducible interpretation contract" in output_text


def test_examples_docs_no_longer_duplicate_first_run_commands() -> None:
    examples_text = EXAMPLES_README_PATH.read_text(encoding="utf-8")
    docs_examples_text = DOCS_EXAMPLES_README_PATH.read_text(encoding="utf-8")

    assert "small supplemental examples" in examples_text
    assert "not a second installation guide" in examples_text
    assert "Use [../README.md](../README.md) for installation and the canonical first run." in examples_text
    assert "optional follow-on to the canonical workflow" in examples_text
    assert "python3 examples/run_minimal_cleaning.py --out /tmp/noaa-spec-example.csv" not in examples_text

    assert "short public example artifacts" in docs_examples_text
    assert "README.md](../../README.md)" in docs_examples_text
    assert "CANONICAL_WALKTHROUGH.md" in docs_examples_text


def test_maintainer_docs_are_moved_out_of_public_docs() -> None:
    if not MAINTAINER_INDEX_PATH.exists():
        pytest.skip("maintainer/ tree not present")
    for path in (
        PROJECT_ROOT / "maintainer" / "docs" / "REVIEWER_GUIDE.md",
        PROJECT_ROOT / "maintainer" / "docs" / "LOCAL_DEV.md",
        PROJECT_ROOT / "maintainer" / "docs" / "ARTIFACT_BOUNDARY_POLICY.md",
        PROJECT_ROOT / "maintainer" / "docs" / "DOMAIN_DATASET_REGISTRY.md",
        PROJECT_ROOT / "maintainer" / "docs" / "PIPELINE_DESIGN_RATIONALE.md",
        PROJECT_ROOT / "maintainer" / "docs" / "PIPELINE_VALIDATION_PLAN.md",
        PROJECT_ROOT / "maintainer" / "docs" / "operations" / "README.md",
    ):
        assert path.exists()

    maintainer_index_text = MAINTAINER_INDEX_PATH.read_text(encoding="utf-8")
    maintainer_docs_index_text = MAINTAINER_DOCS_INDEX_PATH.read_text(encoding="utf-8")
    assert "Maintainer Material" in maintainer_index_text
    assert "not part of the public JOSS reviewer path" in maintainer_index_text
    assert "maintainer material only" in maintainer_docs_index_text
    assert "Operations" in maintainer_docs_index_text
    assert "Archive" in maintainer_docs_index_text


def test_internal_markdown_records_keep_banner() -> None:
    markdown_paths = sorted(INTERNAL_REPORTS_DIR.rglob("*.md"))
    markdown_paths.extend(sorted(INTERNAL_ARCHIVE_DIR.rglob("*.md")))
    if not markdown_paths:
        pytest.skip("Maintainer-only internal markdown is intentionally excluded from the reviewer container.")

    for path in markdown_paths:
        text = path.read_text(encoding="utf-8")
        assert text.startswith(f"# {INTERNAL_RECORD_BANNER}")


def test_reproducibility_doc_is_single_reproducibility_path() -> None:
    public_text = PUBLIC_REPRODUCIBILITY_PATH.read_text(encoding="utf-8")
    directory_text = REPRODUCIBILITY_README_PATH.read_text(encoding="utf-8")

    assert "Local installation is a convenience path for users and developers." in public_text
    assert "working Python environment with `venv` support" in public_text
    assert "NOAA-Spec currently declares support for Python `>=3.11,<3.13`" in public_text
    assert "reviewers should use Python 3.11 or 3.12 for the local path" in public_text
    assert "Python 3.13 is not yet supported" in public_text
    assert "install Python 3.12 first and then continue" in public_text
    assert "py -3.12 -m venv .venv" in public_text
    assert "python3.12 -m venv .venv" in public_text
    assert "`python3.12` is the standard example used here" in public_text
    assert "For independent reviewer verification, use Docker" in public_text
    assert "Inspect a small subset from the tracked canonical fixture:" in public_text
    assert "python3 reproducibility/run_pipeline_example.py --out /tmp/noaa-spec-sample.csv" in public_text
    assert "Views are available through the public `noaa-spec clean --view ...` CLI" in public_text
    assert "with `STATION` and `DATE` as the reviewer-visible identifier columns" in public_text
    assert "`--view metadata`" in public_text
    assert "50e8bfb9ffae8278652bb7410cfbc9683a48711c35cfcf9e9dd3c38bbc403d47" in public_text
    assert "b48aba1b8a304451dc3874b963d76275bf79ad68c6f28d9190e0e636f2887597" in public_text
    assert "docker build -f Dockerfile -t noaa-spec-review ." in public_text
    assert "docker run --rm noaa-spec-review bash scripts/verify_reproducibility.sh" in public_text
    assert "tracked artifacts behind the public reproducibility claim" in directory_text
    assert "The active reviewer workflow is documented in [../REPRODUCIBILITY.md](../REPRODUCIBILITY.md)." in directory_text


def test_readme_command_runner_skips_infra_and_privileged_setup_steps() -> None:
    assert _normalize_line("> sudo apt install python3-venv") == "sudo apt install python3-venv"
    assert _normalize_line(">") == ""
    assert _normalize_line("    reader = csv.DictReader(handle)") == "    reader = csv.DictReader(handle)"
    assert _should_skip("sudo apt install python3-venv")
    assert _should_skip("> sudo apt install python3-venv")
    assert _should_skip("python3 -m venv .venv")
    assert _should_skip("python3.12 --version")
    assert _should_skip("python3.12 -m venv .venv")
    assert _should_skip("python -m pip install -e .")
    assert _should_skip("python3 -m pip install -e .")
    assert not _should_skip("noaa-spec clean reproducibility/minimal/station_raw.csv /tmp/station_cleaned.csv")
