# Reproducibility

This directory contains the tracked bounded reproducibility fixtures used for reviewer verification.

The supported reproducibility path for this revision is the Docker reviewer workflow in the root [README.md](../README.md).

The containerized reviewer environment uses Python 3.12.

The canonical reviewer example is under `reproducibility/minimal/`.

`requirements-review.txt` is the exact tested dependency set used inside the reviewer container.

Local installation is optional and intended for development only; it is not required for reproducibility validation. See [docs/LOCAL_DEV.md](../docs/LOCAL_DEV.md).

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

`bash scripts/verify_reproducibility.sh` checks the installed package, reruns the canonical minimal example, computes the checksum with `sha256sum`, and compares it against the tracked expected artifact. The script runs unchanged inside the Docker reviewer path.

Expected pytest result in the reviewer container:

- `2194 passed, 15 skipped`

This submission validates deterministic canonical cleaning using a bounded, checksum-verified example included in-repo. Broader publication artifacts (release bundles, manifests, and quality reports) are part of the system design but are not included in this review package.

No archived release bundle is linked for this revision.
