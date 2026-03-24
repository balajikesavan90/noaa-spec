#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SMOKE_OUTPUT="${TMPDIR:-/tmp}/noaa-spec-smoke-test.csv"

cd "${REPO_ROOT}"

if ! command -v poetry >/dev/null 2>&1; then
    echo "Missing 'poetry' on PATH. Install Poetry, then rerun 'poetry install'." >&2
    exit 1
fi

poetry run python -c "import noaa_spec"
poetry run noaa-spec --help >/dev/null
poetry run python reproducibility/run_pipeline_example.py --out "${SMOKE_OUTPUT}"

if [[ ! -s "${SMOKE_OUTPUT}" ]]; then
    echo "Smoke test failed: expected cleaned CSV at ${SMOKE_OUTPUT}." >&2
    exit 1
fi

echo "Smoke test passed: Poetry can import noaa_spec, run the CLI, and produce the sample cleaned CSV."
