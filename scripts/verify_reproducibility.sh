#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
OUTPUT_DIR="${1:-/tmp/noaa-spec-reproducibility}"
CHECKSUM_MANIFEST="${REPO_ROOT}/reproducibility/checksums.sha256"

cd "${REPO_ROOT}"

if ! command -v python3 >/dev/null 2>&1; then
    echo "FAIL: python3 is not available on PATH. Activate the reproducibility virtual environment first." >&2
    exit 1
fi

if ! command -v sha256sum >/dev/null 2>&1; then
    echo "FAIL: sha256sum is required for reproducibility verification." >&2
    exit 1
fi

if [[ ! -f "${CHECKSUM_MANIFEST}" ]]; then
    echo "FAIL: missing checksum manifest at ${CHECKSUM_MANIFEST}." >&2
    exit 1
fi

if ! sha256sum -c "${CHECKSUM_MANIFEST}" >/dev/null; then
    echo "FAIL: tracked reproducibility artifact checksum mismatch." >&2
    exit 1
fi

mkdir -p "${OUTPUT_DIR}"

fixture_count=0

while read -r expected_hash_value expected_rel_path; do
    [[ -n "${expected_hash_value:-}" ]] || continue
    [[ "${expected_hash_value}" != \#* ]] || continue
    [[ "${expected_rel_path:-}" == reproducibility/*/station_cleaned_expected.csv ]] || continue

    fixture="${expected_rel_path#reproducibility/}"
    fixture="${fixture%/station_cleaned_expected.csv}"
    raw_path="reproducibility/${fixture}/station_raw.csv"
    expected_path="${REPO_ROOT}/reproducibility/${fixture}/station_cleaned_expected.csv"
    output_path="${OUTPUT_DIR}/${fixture}_station_cleaned.csv"

    if [[ ! -f "${raw_path}" ]]; then
        echo "FAIL: missing tracked raw fixture at ${raw_path}." >&2
        exit 1
    fi

    if [[ ! -f "${expected_path}" ]]; then
        echo "FAIL: missing tracked expected fixture at ${expected_path}." >&2
        exit 1
    fi

    expected_before="$(sha256sum "${expected_path}" | cut -d' ' -f1)"

    PYTHONPATH="${REPO_ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}" \
        python3 -m noaa_spec.cli clean "${raw_path}" "${output_path}" >/dev/null

    if [[ ! -s "${output_path}" ]]; then
        echo "FAIL: expected cleaned CSV at ${output_path}." >&2
        exit 1
    fi

    actual_hash="$(sha256sum "${output_path}" | cut -d' ' -f1)"
    expected_hash="$(sha256sum "${expected_path}" | cut -d' ' -f1)"

    if [[ "${expected_hash}" != "${expected_hash_value}" ]]; then
        echo "FAIL: tracked expected artifact hash changed unexpectedly for ${fixture}." >&2
        echo "Expected: ${expected_hash_value}" >&2
        echo "Actual:   ${expected_hash}" >&2
        exit 1
    fi

    if [[ "${actual_hash}" != "${expected_hash_value}" ]]; then
        echo "FAIL: generated output hash does not match expected artifact for ${fixture}." >&2
        echo "Expected: ${expected_hash_value}" >&2
        echo "Actual:   ${actual_hash}" >&2
        exit 1
    fi

    expected_after="$(sha256sum "${expected_path}" | cut -d' ' -f1)"
    if [[ "${expected_before}" != "${expected_after}" ]]; then
        echo "FAIL: verification modified tracked reproducibility files for ${fixture}." >&2
        exit 1
    fi

    echo "PASS: ${fixture} ${actual_hash}"
    fixture_count=$((fixture_count + 1))
done < "${CHECKSUM_MANIFEST}"

if [[ "${fixture_count}" -eq 0 ]]; then
    echo "FAIL: no station_cleaned_expected.csv entries found in ${CHECKSUM_MANIFEST}." >&2
    exit 1
fi

echo "PASS: reproducibility verification succeeded."
echo "Output directory: ${OUTPUT_DIR}"
