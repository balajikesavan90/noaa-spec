# Optional Local Development

This document describes an optional developer workflow. It is not the supported reviewer path for this submission.

Reviewers should use the Docker workflow in the root [README.md](../README.md). Local installation is intended only for development, debugging, or contributor work.

## Local Setup

Host requirements typically include `python3`, `python3-venv`, `git`, `bash`, and `sha256sum`.

```bash
bash scripts/check_reviewer_env.sh
python3 -m venv .review-venv
source .review-venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements-review.txt
python3 -m pip install -e .
python3 reproducibility/run_pipeline_example.py --example minimal --out /tmp/noaa-spec-sample.csv
bash scripts/verify_reproducibility.sh
pytest -q
```

The exact pytest count is expected to change as the repository evolves; use this path to confirm local success, not to assert a frozen reviewer count.

System package requirements may vary by host OS and are outside the supported reviewer workflow. For the clean reviewer path, use the Docker commands in [reproducibility/README.md](../../reproducibility/README.md).
