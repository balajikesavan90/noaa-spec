# Reproducibility

This directory contains the tracked bounded reproducibility fixtures used for reviewer verification.

The reproducible software surface for this revision is intentionally narrow:

- in scope: the deterministic canonical cleaning path for NOAA ISD / Global Hourly records
- in scope: the tracked minimal fixture under `reproducibility/minimal/`
- in scope: checksum-backed rerun verification for that fixture
- out of scope: broader release bundles, domain-publication outputs, and publication orchestration workflows elsewhere in the repository

The purpose of these fixtures is to let reviewers rerun the demonstrated NOAA-specific cleaning path and confirm that the same cleaned output is produced for the same input and configuration, rather than relying on undocumented local preprocessing differences.

The supported reviewer path is the Docker workflow below. Use a clean checkout and do not rely on an existing editable install or active local virtual environment.

## Supported reviewer workflow

Build the reviewer image from the repository root:

```bash
docker build -f Dockerfile -t noaa-spec-review .
```

Run the bounded reproducibility verification:

```bash
docker run --rm noaa-spec-review bash scripts/verify_reproducibility.sh
```

Run the example itself inside the same container if you want the generated CSV separately:

```bash
docker run --rm noaa-spec-review python3 reproducibility/run_pipeline_example.py --example minimal --out /tmp/noaa-spec-sample.csv
```

The reviewer container uses Python 3.12 and installs the exact pinned dependencies from `requirements-review.txt` plus the repository checkout via `pip install -e .`.

## Tracked fixtures

Tracked reviewer fixtures:

- `reproducibility/minimal/station_raw.csv`
- `reproducibility/minimal/station_cleaned.csv`
- `reproducibility/minimal/station_cleaned_expected.csv`

Additional tracked non-canonical fixture coverage:

- `reproducibility/full_station/station_raw.csv`
- `reproducibility/full_station/station_cleaned.csv`
- `reproducibility/full_station/station_cleaned_expected.csv`

Expected SHA256 for the minimal cleaned output:

`b48aba1b8a304451dc3874b963d76275bf79ad68c6f28d9190e0e636f2887597`

`bash scripts/verify_reproducibility.sh` reruns the canonical minimal example, computes the checksum with `sha256sum`, and compares it against the tracked expected artifact.

## Optional local debugging path

Docker is the supported reviewer path. A local installation can still be useful for debugging or development:

```bash
bash scripts/check_reviewer_env.sh
python3 -m venv .review-venv
source .review-venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements-review.txt
python3 -m pip install -e .
bash scripts/verify_reproducibility.sh
pytest -q
```

This local path is not the clean-room reviewer claim. It is a maintainer convenience path for reproducing the same bounded check outside Docker.

## Interpretation

This submission validates deterministic canonical cleaning using a bounded, checksum-verified example included in-repo. Broader publication artifacts (release bundles, manifests, domain publication outputs, and quality reports) are part of the documented system design but are not included in this review package.

No archived release bundle is linked for this revision.
