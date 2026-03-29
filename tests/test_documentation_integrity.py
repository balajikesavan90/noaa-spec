from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
README_PATH = PROJECT_ROOT / "README.md"
DOCS_INDEX_PATH = PROJECT_ROOT / "docs" / "README.md"
DOCS_QUICKSTART_PATH = PROJECT_ROOT / "docs" / "QUICKSTART.md"
DOCS_OUTPUT_GUIDE_PATH = PROJECT_ROOT / "docs" / "UNDERSTANDING_OUTPUT.md"
DOCS_INTERNAL_INDEX_PATH = PROJECT_ROOT / "docs" / "internal" / "README.md"
EXAMPLES_README_PATH = PROJECT_ROOT / "examples" / "README.md"
DOCS_EXAMPLES_README_PATH = PROJECT_ROOT / "docs" / "examples" / "README.md"
PUBLIC_REPRODUCIBILITY_PATH = PROJECT_ROOT / "REPRODUCIBILITY.md"
REPRODUCIBILITY_README_PATH = PROJECT_ROOT / "reproducibility" / "README.md"
INTERNAL_REPORTS_DIR = PROJECT_ROOT / "docs" / "internal" / "reports"
INTERNAL_ARCHIVE_DIR = PROJECT_ROOT / "docs" / "internal" / "archive"
INTERNAL_RECORD_BANNER = "INTERNAL DEVELOPMENT RECORD — NOT REVIEWER EVIDENCE"


def test_readme_locks_public_contribution_and_workflow() -> None:
    text = README_PATH.read_text(encoding="utf-8")

    for section in (
        "## What this does",
        "## What this is / What this is not",
        "## Public Scope",
        "## Environment",
        "## Minimal Workflow",
        "## Reproducibility Verification",
        "## Docs",
    ):
        assert section in text

    assert "deterministic canonicalization layer" in text
    assert "implicit project-local preprocessing" in text
    assert "stable intermediate representation" in text
    assert "Requires Python 3.12 with `python3.12-venv` installed" in text
    assert "noaa-spec clean reproducibility/minimal/station_raw.csv /tmp/station_cleaned.csv" in text
    assert "TMP__qc_reason" in text
    assert "SENTINEL_MISSING" in text
    assert "publication system" not in text
    assert "general climate analytics platform" in text


def test_docs_index_points_to_single_first_run_and_reproducibility_path() -> None:
    text = DOCS_INDEX_PATH.read_text(encoding="utf-8")

    assert "README.md](../README.md)" in text
    assert "[UNDERSTANDING_OUTPUT.md](UNDERSTANDING_OUTPUT.md)" in text
    assert "[../REPRODUCIBILITY.md](../REPRODUCIBILITY.md)" in text
    assert "[examples/CANONICAL_WALKTHROUGH.md](examples/CANONICAL_WALKTHROUGH.md)" in text
    assert "[internal/README.md](internal/README.md)" in text
    assert "[QUICKSTART.md](QUICKSTART.md)" not in text


def test_quickstart_is_reduced_to_readme_pointer() -> None:
    quickstart_text = DOCS_QUICKSTART_PATH.read_text(encoding="utf-8").strip()
    output_text = DOCS_OUTPUT_GUIDE_PATH.read_text(encoding="utf-8")

    assert quickstart_text == (
        "# Quickstart\n\n"
        "Quickstart is in [README.md]"
        "(/home/balaji-kesavan/Documents/AI_Projects/noaa-climate-data/README.md)."
    )

    assert "A 10-column subset" in output_text
    assert "Where to start" in output_text
    assert "How most users should approach this output" in output_text
    assert "Sentinel handling" in output_text
    assert "QC flags" in output_text
    assert "Missing values" in output_text
    assert "BEFORE -> AFTER example" in output_text
    assert "temperature_c" in output_text
    assert "TMP__qc_reason=SENTINEL_MISSING" in output_text


def test_examples_docs_no_longer_duplicate_first_run_commands() -> None:
    examples_text = EXAMPLES_README_PATH.read_text(encoding="utf-8")
    docs_examples_text = DOCS_EXAMPLES_README_PATH.read_text(encoding="utf-8")

    assert "The first runnable workflow is in [README.md]" in examples_text
    assert "python3 examples/run_minimal_cleaning.py --out /tmp/noaa-spec-example.csv" not in examples_text

    assert "curated example artifacts" in docs_examples_text
    assert "README.md](../../README.md)" in docs_examples_text
    assert "../UNDERSTANDING_OUTPUT.md" in docs_examples_text
    assert "CANONICAL_WALKTHROUGH.md" in docs_examples_text


def test_internal_docs_are_moved_under_docs_internal() -> None:
    for path in (
        PROJECT_ROOT / "docs" / "internal" / "REVIEWER_GUIDE.md",
        PROJECT_ROOT / "docs" / "internal" / "LOCAL_DEV.md",
        PROJECT_ROOT / "docs" / "internal" / "ARTIFACT_BOUNDARY_POLICY.md",
        PROJECT_ROOT / "docs" / "internal" / "DOMAIN_DATASET_REGISTRY.md",
        PROJECT_ROOT / "docs" / "internal" / "PIPELINE_DESIGN_RATIONALE.md",
        PROJECT_ROOT / "docs" / "internal" / "PIPELINE_VALIDATION_PLAN.md",
        PROJECT_ROOT / "docs" / "internal" / "operations" / "README.md",
    ):
        assert path.exists()

    internal_index_text = DOCS_INTERNAL_INDEX_PATH.read_text(encoding="utf-8")
    assert "maintainer material only" in internal_index_text
    assert "Operations" in internal_index_text
    assert "Archive" in internal_index_text


def test_internal_markdown_records_keep_banner() -> None:
    markdown_paths = sorted(INTERNAL_REPORTS_DIR.rglob("*.md"))
    markdown_paths.extend(sorted(INTERNAL_ARCHIVE_DIR.rglob("*.md")))
    assert markdown_paths

    for path in markdown_paths:
        text = path.read_text(encoding="utf-8")
        assert text.startswith(f"# {INTERNAL_RECORD_BANNER}")


def test_reproducibility_doc_is_single_reproducibility_path() -> None:
    public_text = PUBLIC_REPRODUCIBILITY_PATH.read_text(encoding="utf-8")
    directory_text = REPRODUCIBILITY_README_PATH.read_text(encoding="utf-8")

    assert "Requires Python 3.12 with `python3.12-venv` installed." in public_text
    assert "python3 reproducibility/run_pipeline_example.py --example minimal --out /tmp/noaa-spec-sample.csv" in public_text
    assert "50e8bfb9ffae8278652bb7410cfbc9683a48711c35cfcf9e9dd3c38bbc403d47" in public_text
    assert "b48aba1b8a304451dc3874b963d76275bf79ad68c6f28d9190e0e636f2887597" in public_text
    assert "docker build -f Dockerfile -t noaa-spec-review ." in public_text
    assert "docker run --rm noaa-spec-review bash scripts/verify_reproducibility.sh" in public_text
    assert "authoritative public reviewer workflow" in directory_text
