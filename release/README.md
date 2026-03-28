# NON-EVIDENCE PLACEHOLDER FOR FUTURE FROZEN RELEASE ARTIFACTS

No archived release bundle is linked for this revision.

This repository snapshot does not include frozen release manifests, quality reports, or archived build outputs as reviewer evidence.

Reviewer evidence for this revision is limited to:

- the tracked minimal fixture under `reproducibility/minimal/`
- `poetry run noaa-spec --help`
- `poetry run python3 reproducibility/run_pipeline_example.py --example minimal --out /tmp/noaa-spec-sample.csv`
- `bash scripts/verify_reproducibility.sh`
- `poetry run pytest -q`

Frozen release artifacts belong to the broader publication workflow and will be created only from a frozen revision.
