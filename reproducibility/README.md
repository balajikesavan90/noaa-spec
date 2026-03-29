# Reproducibility

This directory contains the bounded reproducibility example for NOAA-Spec's public contribution: deterministic observation-level cleaning for NOAA ISD / Global Hourly data.

## Authority

For ordinary usage, use the Python install and public `noaa-spec clean` CLI documented in the root [README.md](../README.md).

For reviewer verification in a clean environment, use the Docker workflow below. That is the authoritative reviewer path for confirming the tracked example and expected checksum.

## Tracked Example

- Raw input: `reproducibility/minimal/station_raw.csv`
- Raw input SHA256: `50e8bfb9ffae8278652bb7410cfbc9683a48711c35cfcf9e9dd3c38bbc403d47`
- Expected output: `reproducibility/minimal/station_cleaned_expected.csv`
- Expected output SHA256: `b48aba1b8a304451dc3874b963d76275bf79ad68c6f28d9190e0e636f2887597`

The tracked output is the canonical cleaned representation for the sample input. It is intentionally wider than the preview shown in the README because it preserves normalized observation fields, QC context, and supporting metadata in one deterministic artifact.

Exact command:

```bash
python3 reproducibility/run_pipeline_example.py --example minimal --out /tmp/noaa-spec-sample.csv
```

Verify the checksum:

```bash
sha256sum /tmp/noaa-spec-sample.csv
```

Expected checksum:

```text
b48aba1b8a304451dc3874b963d76275bf79ad68c6f28d9190e0e636f2887597
```

## Python Validation Path

Requires Python 3.12 with `python3.12-venv` installed. This path is useful for local inspection after following the install steps in the root [README.md](../README.md).

## Docker Verification Path

```bash
docker build -f Dockerfile -t noaa-spec-review .
docker run --rm noaa-spec-review bash scripts/verify_reproducibility.sh
```

This is the supported reviewer workflow for verifying the example in a clean environment.

## Boundary

This reproducibility surface covers the cleaning layer only. Batch orchestration, domain outputs, manifests, and report-generation workflows are maintainer-facing and outside the public JOSS claim for this revision.
