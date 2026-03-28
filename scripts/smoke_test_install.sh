#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SMOKE_OUTPUT="${TMPDIR:-/tmp}/noaa-spec-smoke-test.csv"
TRACKED_EXPECTED="${REPO_ROOT}/reproducibility/minimal/station_cleaned_expected.csv"
TRACKED_ANCHOR="${REPO_ROOT}/reproducibility/minimal/station_cleaned.csv"

cd "${REPO_ROOT}"

if ! command -v poetry >/dev/null 2>&1; then
    echo "Missing 'poetry' on PATH. Install Poetry with pipx, then rerun 'poetry install'." >&2
    exit 1
fi

expected_before="$(sha256sum "${TRACKED_EXPECTED}" | cut -d' ' -f1)"
anchor_before="$(sha256sum "${TRACKED_ANCHOR}" | cut -d' ' -f1)"

poetry run python -c "import noaa_spec"
poetry run noaa-spec --help >/dev/null
poetry run python reproducibility/run_pipeline_example.py --example minimal --out "${SMOKE_OUTPUT}"

if [[ ! -s "${SMOKE_OUTPUT}" ]]; then
    echo "Smoke test failed: expected cleaned CSV at ${SMOKE_OUTPUT}." >&2
    exit 1
fi

if ! cmp -s "${SMOKE_OUTPUT}" "${TRACKED_EXPECTED}"; then
    echo "Smoke test failed: generated sample output does not match ${TRACKED_EXPECTED}." >&2
    exit 1
fi

expected_after="$(sha256sum "${TRACKED_EXPECTED}" | cut -d' ' -f1)"
anchor_after="$(sha256sum "${TRACKED_ANCHOR}" | cut -d' ' -f1)"

if [[ "${expected_before}" != "${expected_after}" || "${anchor_before}" != "${anchor_after}" ]]; then
    echo "Smoke test failed: reviewer flow modified tracked reproducibility files." >&2
    exit 1
fi

echo "Smoke test passed: Poetry can import noaa_spec, run the CLI, verify the sample anchor, and avoid tracked-file mutation."
