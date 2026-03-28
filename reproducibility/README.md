# Reproducibility

This folder contains the minimal deterministic cleaning example used for local verification and reviewer orientation.

The NOAA ISD specification snapshot used for rule provenance and spec-coverage generation is stored separately under `spec_sources/isd-format-document-parts/`; it is not part of the reviewer sample-run surface.

## Reviewer flow

1. Install the project:

```bash
python3 --version
python3 -m pip install --user pipx
python3 -m pipx ensurepath
pipx install poetry
poetry install
```

Requirements:

- Python `>=3.12`
- `pipx` used to install Poetry on a clean machine
- Poetry available on `PATH`

Recommended Poetry installation path:

- install Poetry with `pipx`
- if `pipx` is already installed, run `pipx install poetry`
- the official Poetry installer is an acceptable fallback, but this repository documents `pipx` as the primary path

2. Run the bounded cleaning example:

```bash
poetry run python reproducibility/run_pipeline_example.py --out /tmp/noaa-spec-sample.csv
```

3. Verify that the installed CLI is available:

```bash
poetry run noaa-spec --help
```

This reads `reproducibility/sample_station_raw.txt` and writes a cleaned CSV to the path passed with `--out`.

Optional: write the cleaned CSV to a different custom path:

```bash
poetry run python reproducibility/run_pipeline_example.py --out /tmp/sample_station_cleaned.csv
```

The reviewer path writes outside the repository by default and should exit cleanly without `[PARSE_STRICT]` warnings.

Tracked anchor files:

- `reproducibility/sample_station_cleaned.csv` is the tracked sample artifact
- `reproducibility/sample_station_cleaned_expected.csv` is the verification fixture used by tests and the smoke script

`bash scripts/smoke_test_install.sh` automates the reviewer verification path: it runs the sample command with `poetry run`, compares the generated CSV with the tracked fixture, and fails if the reviewer flow mutates tracked reproducibility files.

This example is the active reproducibility anchor in the repository. Revision-specific environment captures and pipeline snapshots are intentionally not tracked here during active development because they become stale quickly and can be mistaken for frozen submission evidence.

## Run coverage generator

```bash
poetry run python tools/spec_coverage/generate_spec_coverage.py
```

## Run tests

```bash
poetry run pytest -q
```

## Data provenance

The sample station data is a synthetic, minimal extract based on the NOAA ISD
Global Hourly CSV schema. It uses a placeholder station ID and two rows of
well-formed TMP, DEW, and SLP fields to exercise scaling, quality parsing, and
QC signal generation without relying on external data downloads.

Pipeline transformations applied by the example script:

- Read the raw CSV into a DataFrame.
- Parse comma-encoded fields (TMP, DEW, SLP) in strict mode.
- Apply missing-value checks, quality filtering, and min/max range enforcement.
- Scale numeric values per field rules and emit QC columns.
- Produce row-level usability summaries.

## How to read this with the rest of the repo

- Use this example to verify that installation and the cleaning engine work on a bounded input.
- Use `docs/REVIEWER_GUIDE.md` for the reviewer path through install, outputs, manifests, and quality reports.
- Treat larger batch builds as separate validation evidence that will be paired to a frozen submission revision later, not as part of this active development snapshot.

## Archived full station reports

The full historical station-report example tree is stored outside the tracked repository surface in `data/archive/station_reports_full/`.

This local archive is not required for reproduction. Only a curated subset remains tracked under `docs/examples/stations/`.
