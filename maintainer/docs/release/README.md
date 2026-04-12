# Release Workflow Notes

No archived release bundle is linked for this revision.

This repository snapshot does not include a frozen release build with manifests, quality reports, or archived build outputs.

This directory belongs to the broader artifact publication workflow. It is useful when working on release manifests and validation evidence, but the portable first-run path remains the core canonical cleaner and the in-repo reproducibility fixtures.

For fixture-level verification, use:

- `python3 reproducibility/run_pipeline_example.py --out /tmp/noaa-spec-sample.csv`
- `bash scripts/verify_reproducibility.sh`
- `pytest -q`

Frozen release artifacts belong to the broader publication workflow and are not bundled in this checkout.
