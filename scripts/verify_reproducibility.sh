#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
OUTPUT_PATH="${1:-${TMPDIR:-/tmp}/noaa-spec-sample.csv}"
EXPECTED_PATH="${REPO_ROOT}/reproducibility/minimal/station_cleaned_expected.csv"
EXPECTED_HASH="b48aba1b8a304451dc3874b963d76275bf79ad68c6f28d9190e0e636f2887597"

cd "${REPO_ROOT}"

if ! command -v python >/dev/null 2>&1; then
    echo "FAIL: python is not available on PATH." >&2
    exit 1
fi

expected_before="$(sha256sum "${EXPECTED_PATH}" | cut -d' ' -f1)"

python -c "import noaa_spec"
python reproducibility/run_pipeline_example.py --example minimal --out "${OUTPUT_PATH}"

if [[ ! -s "${OUTPUT_PATH}" ]]; then
    echo "FAIL: expected cleaned CSV at ${OUTPUT_PATH}." >&2
    exit 1
fi

actual_hash="$(sha256sum "${OUTPUT_PATH}" | cut -d' ' -f1)"
expected_hash="$(sha256sum "${EXPECTED_PATH}" | cut -d' ' -f1)"

if [[ "${expected_hash}" != "${EXPECTED_HASH}" ]]; then
    echo "FAIL: tracked expected artifact hash changed unexpectedly." >&2
    echo "Expected: ${EXPECTED_HASH}" >&2
    echo "Actual:   ${expected_hash}" >&2
    exit 1
fi

if [[ "${actual_hash}" != "${EXPECTED_HASH}" ]]; then
    echo "FAIL: generated output hash does not match expected artifact." >&2
    echo "Expected: ${EXPECTED_HASH}" >&2
    echo "Actual:   ${actual_hash}" >&2
    exit 1
fi

expected_after="$(sha256sum "${EXPECTED_PATH}" | cut -d' ' -f1)"
if [[ "${expected_before}" != "${expected_after}" ]]; then
    echo "FAIL: verification modified tracked reproducibility files." >&2
    exit 1
fi

echo "PASS: ${OUTPUT_PATH}"
echo "SHA256: ${actual_hash}"
