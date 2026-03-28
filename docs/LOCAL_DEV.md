# Optional Local Development

This document describes an optional developer workflow. It is not the supported reviewer path for this submission.

Reviewers should use the Docker workflow in the root [README.md](../README.md). Local installation is intended only for development, debugging, or contributor work.

## Local Setup

Host requirements typically include `python3`, `python3-venv`, `git`, `bash`, and `sha256sum`.

```bash
bash scripts/check_reviewer_env.sh
python3 -m venv .review-venv
source .review-venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-review.txt
pip install -e .
python reproducibility/run_pipeline_example.py --example minimal --out /tmp/noaa-spec-sample.csv
bash scripts/verify_reproducibility.sh
pytest -q
```

Expected pytest result in the tested environment:

- `2194 passed, 15 skipped`

System package requirements may vary by host OS and are outside the supported reviewer workflow.
