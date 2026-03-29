from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
README_PATH = PROJECT_ROOT / "README.md"
DOCS_INDEX_PATH = PROJECT_ROOT / "docs" / "README.md"
DOCS_QUICKSTART_PATH = PROJECT_ROOT / "docs" / "QUICKSTART.md"
DOCS_OUTPUT_GUIDE_PATH = PROJECT_ROOT / "docs" / "UNDERSTANDING_OUTPUT.md"
DOCS_INTERNAL_INDEX_PATH = PROJECT_ROOT / "docs" / "internal" / "README.md"
EXAMPLES_README_PATH = PROJECT_ROOT / "examples" / "README.md"
DOCS_EXAMPLES_README_PATH = PROJECT_ROOT / "docs" / "examples" / "README.md"
REPRODUCIBILITY_README_PATH = PROJECT_ROOT / "reproducibility" / "README.md"
RELEASE_README_PATH = PROJECT_ROOT / "release" / "README.md"
INTERNAL_REPORTS_DIR = PROJECT_ROOT / "docs" / "internal" / "reports"
INTERNAL_ARCHIVE_DIR = PROJECT_ROOT / "docs" / "internal" / "archive"
INTERNAL_RECORD_BANNER = "INTERNAL DEVELOPMENT RECORD — NOT REVIEWER EVIDENCE"


def test_readme_is_user_first() -> None:
    text = README_PATH.read_text(encoding="utf-8")

    for section in (
        "## What this does",
        "## 2-minute quickstart",
        "## Which path should I use?",
        "## Use this on your own NOAA data",
        "## What you get",
        "## When to use this",
        "## Why not just use pandas?",
        "## Full docs",
    ):
        assert section in text

    assert "python3 -m venv .venv" in text
    assert "source .venv/bin/activate" in text
    assert "python3 -m noaa_spec.quickstart" in text
    assert "noaa-spec clean my_station.csv --out cleaned.csv" in text
    assert "/tmp/noaa-spec-quickstart/station_cleaned.csv" in text
    assert "## Reviewer Quickstart" not in text
    assert "## Supported Platform" not in text


def test_docs_index_only_surfaces_user_relevant_entrypoints() -> None:
    text = DOCS_INDEX_PATH.read_text(encoding="utf-8")

    assert "[QUICKSTART.md](QUICKSTART.md)" in text
    assert "[UNDERSTANDING_OUTPUT.md](UNDERSTANDING_OUTPUT.md)" in text
    assert "[examples/README.md](examples/README.md)" in text
    assert "[internal/README.md](internal/README.md)" in text
    assert "REVIEWER_GUIDE" not in text
    assert "ARTIFACT_BOUNDARY_POLICY" not in text
    assert "PIPELINE_VALIDATION_PLAN" not in text


def test_quickstart_and_output_docs_exist() -> None:
    quickstart_text = DOCS_QUICKSTART_PATH.read_text(encoding="utf-8")
    output_text = DOCS_OUTPUT_GUIDE_PATH.read_text(encoding="utf-8")

    assert "python3 -m venv .venv" in quickstart_text
    assert "source .venv/bin/activate" in quickstart_text
    assert "python3 -m noaa_spec.quickstart" in quickstart_text
    assert "noaa-spec clean my_station.csv --out cleaned.csv" in quickstart_text
    assert "python3 examples/run_minimal_cleaning.py --out /tmp/noaa-spec-example.csv" in quickstart_text

    assert "A 10-column subset" in output_text
    assert "Where to start" in output_text
    assert "Sentinel handling" in output_text
    assert "QC flags" in output_text
    assert "Missing values" in output_text
    assert "BEFORE -> AFTER example" in output_text
    assert "temperature_c" in output_text
    assert "TMP__qc_reason=SENTINEL_MISSING" in output_text


def test_examples_are_easy_to_run() -> None:
    examples_text = EXAMPLES_README_PATH.read_text(encoding="utf-8")
    docs_examples_text = DOCS_EXAMPLES_README_PATH.read_text(encoding="utf-8")

    assert "python3 examples/run_minimal_cleaning.py --out /tmp/noaa-spec-example.csv" in examples_text
    assert "/tmp/noaa-spec-example.csv" in examples_text
    assert "deterministic CSV" in examples_text

    assert "../QUICKSTART.md" in docs_examples_text
    assert "../UNDERSTANDING_OUTPUT.md" in docs_examples_text
    assert "run_minimal_cleaning.py" in docs_examples_text


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

    for path in (
        PROJECT_ROOT / "docs" / "REVIEWER_GUIDE.md",
        PROJECT_ROOT / "docs" / "LOCAL_DEV.md",
        PROJECT_ROOT / "docs" / "ARTIFACT_BOUNDARY_POLICY.md",
        PROJECT_ROOT / "docs" / "DOMAIN_DATASET_REGISTRY.md",
        PROJECT_ROOT / "docs" / "PIPELINE_VALIDATION_PLAN.md",
    ):
        assert not path.exists()

    internal_index_text = DOCS_INTERNAL_INDEX_PATH.read_text(encoding="utf-8")
    assert "Reviewer guide" in internal_index_text
    assert "Operations" in internal_index_text
    assert "Archive" in internal_index_text


def test_internal_markdown_records_keep_banner() -> None:
    markdown_paths = sorted(INTERNAL_REPORTS_DIR.rglob("*.md"))
    markdown_paths.extend(sorted(INTERNAL_ARCHIVE_DIR.rglob("*.md")))
    assert markdown_paths

    for path in markdown_paths:
        text = path.read_text(encoding="utf-8")
        assert text.startswith(f"# {INTERNAL_RECORD_BANNER}")


def test_reproducibility_doc_points_to_internal_local_dev_doc() -> None:
    text = REPRODUCIBILITY_README_PATH.read_text(encoding="utf-8")
    assert "[docs/internal/LOCAL_DEV.md](../docs/internal/LOCAL_DEV.md)" in text


def test_release_surface_remains_stubbed() -> None:
    text = RELEASE_README_PATH.read_text(encoding="utf-8")
    assert "NON-EVIDENCE PLACEHOLDER — NOT PART OF REVIEWER VERIFICATION FOR THIS REVISION" in text
    assert "No archived release bundle is linked for this revision." in text
