# NON-EVIDENCE PLACEHOLDER — NOT PART OF REVIEWER VERIFICATION FOR THIS REVISION

No archived release bundle is linked for this revision.

This repository snapshot does not include frozen release manifests, quality reports, or archived build outputs as reviewer evidence.

This directory belongs to the broader publication workflow, not to the bounded JOSS-facing contribution. Reviewers should evaluate NOAA-Spec here as a deterministic NOAA-specific canonical cleaner with the in-repo reproducibility fixture, not as a fully reviewer-reproduced release platform.

Reviewers should rely on:

- `python3 reproducibility/run_pipeline_example.py --example minimal --out /tmp/noaa-spec-sample.csv`
- `bash scripts/verify_reproducibility.sh`
- `pytest -q`

Frozen release artifacts belong to the broader publication workflow and are not part of reviewer verification for this revision.
