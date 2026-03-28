# Reproducibility

This folder contains the tracked deterministic cleaning examples used for local verification and reviewer orientation:

- `minimal/`: the default fast reviewer path using a small real-station excerpt
- `full_station/`: a bounded reproduction of one complete real station

The NOAA ISD specification snapshot used for rule provenance and spec-coverage generation is stored separately under `spec_sources/isd-format-document-parts/`; it is not part of the reviewer sample-run surface.

## Reviewer command sequence

Use the same Poetry-managed environment documented in the root `README.md`.

Tested on Linux with `Python 3.12`.

Network access is required for the Poetry installer and dependency resolution.

Linux prerequisites:

- `python3`
- `curl`
- virtual environment support for your Python installation
- Debian/Ubuntu-like systems commonly need `python3-venv`

Install and verify the environment:

```bash
python3 --version
curl --version
curl -sSL https://install.python-poetry.org | python3 - --version 2.1.3
export PATH="$HOME/.local/bin:$PATH"
poetry --version
poetry install
poetry run noaa-spec --help
poetry run python3 reproducibility/run_pipeline_example.py --example minimal --out /tmp/noaa-spec-sample.csv
bash scripts/verify_reproducibility.sh
poetry run pytest -q
```

If this checkout already contains a leftover `.venv` from an older revision, remove it before running `poetry install`. The reviewer quickstart does not use an in-project virtual environment.

Manual checksum verification:

```bash
sha256sum /tmp/noaa-spec-sample.csv
sha256sum reproducibility/minimal/station_cleaned_expected.csv
```

Expected SHA256: `b48aba1b8a304451dc3874b963d76275bf79ad68c6f28d9190e0e636f2887597`

This reads `reproducibility/minimal/station_raw.csv` and writes a cleaned CSV to the path passed with `--out`. This project relies on `poetry.lock` for deterministic dependency resolution. Do not regenerate it unless you are intentionally updating dependencies.

This revision demonstrates deterministic, specification-constrained cleaning at bounded scale using tracked reproducibility fixtures. Full release-scale artifacts are part of the broader publication workflow but are not bundled as reviewer evidence in this development snapshot.

No archived release bundle is linked for this revision.

## Optional local development path

Optional local development path — not part of reviewer quickstart.

The full-station example is intentionally secondary:

```bash
poetry run python3 reproducibility/run_pipeline_example.py --example full_station --out /tmp/noaa-spec-full-station.csv
```

The reviewer path writes outside the repository by default.

Tracked anchor files:

- `reproducibility/minimal/station_cleaned.csv` is the tracked minimal example artifact
- `reproducibility/minimal/station_cleaned_expected.csv` is the verification fixture used by tests and the verification script
- `reproducibility/full_station/station_cleaned.csv` is the tracked full-station artifact
- `reproducibility/full_station/station_cleaned_expected.csv` is the verification fixture for the bounded full-station path

`bash scripts/verify_reproducibility.sh` automates the primary reviewer verification path: it runs the minimal example with `poetry run`, compares the generated CSV with the tracked fixture, and fails if the reviewer flow mutates tracked reproducibility files.

The minimal example is the active reviewer anchor in the repository. The full-station example is a secondary bounded reproduction path for a complete real station. Revision-specific environment captures and pipeline snapshots are intentionally not tracked here during active development because they become stale quickly and can be mistaken for frozen submission evidence.

## Run coverage generator

```bash
poetry run python3 tools/spec_coverage/generate_spec_coverage.py
```

## Run tests

```bash
poetry run pytest -q
```

## Data provenance

The minimal example uses a small tracked excerpt from real NOAA-derived station output to exercise cleaning behavior on a bounded input. The full-station example uses one complete tracked real station from the repository's generated outputs to demonstrate bounded end-to-end station reproduction.

Pipeline transformations applied by the example script:

- Read the raw CSV into a DataFrame.
- Parse NOAA comma-encoded fields in strict mode.
- Apply missing-value checks, quality filtering, and min/max range enforcement.
- Scale numeric values per field rules and emit QC columns.
- Produce row-level usability summaries.

## How to read this with the rest of the repo

- Use the root `README.md` for the canonical reviewer quickstart.
- Use the minimal example to verify that installation and the cleaning engine work on a bounded input.
- Use the full-station example only as an optional local development check.
- Use `docs/REVIEWER_GUIDE.md` for submission framing and evidence boundaries.
