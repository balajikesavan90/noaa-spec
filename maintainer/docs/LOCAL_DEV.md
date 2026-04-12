# Optional Local Development

This document describes an optional developer workflow for maintainers and contributors.

For the shortest first run, use the core CLI workflow in the root [README.md](../../README.md). Local development setup is intended for debugging, testing, and repository maintenance work.

## Local Setup

Host requirements typically include Python 3.11 or 3.12 with `venv` support, `git`, `bash`, and `sha256sum`. Python 3.13 is not yet supported. If you do not already have a supported interpreter, install Python 3.12 first and then continue.

```bash
python3.12 --version
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-review.txt
python -m pip install -e .
python reproducibility/run_pipeline_example.py --out /tmp/noaa-spec-sample.csv
bash scripts/verify_reproducibility.sh
pytest -q
```

On macOS/Linux the exact command for the installed Python 3.12 interpreter may vary by system, but `python3.12` is the standard example shown here.

The exact pytest count is expected to change as the repository evolves; use this path to confirm local success, not to assert a frozen count.

System package requirements may vary by host OS. For a clean-environment fixture check, use the Docker commands in [../../REPRODUCIBILITY.md](../../REPRODUCIBILITY.md).
