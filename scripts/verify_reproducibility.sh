#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
OUTPUT_DIR="${1:-/tmp/noaa-spec-reproducibility}"

FIXTURES=(
    "minimal:b48aba1b8a304451dc3874b963d76275bf79ad68c6f28d9190e0e636f2887597"
    "minimal_second:223efb068df6d605646a1288feedf6621fa55b4c9074c027f6347cbe7ca2f30e"
    "station_03041099999_aonach_mor:94913da579dc08b9c80a8a8f80d76cfb996ff9c28376aa2835b41161f0f7f134"
    "station_01116099999_stokka:30e71fd2c6bed1fcecf5fd5922f96c47b11b63b4bacb4425ddbcbd078798e92d"
    "station_94368099999_hamilton_island:9589ec020704b9d1fdd6e3675272badfd8e758302807f306ed8bbc9f91dc5a1a"
)

cd "${REPO_ROOT}"

if ! command -v python3 >/dev/null 2>&1; then
    echo "FAIL: python3 is not available on PATH. Activate the reviewer virtual environment first." >&2
    exit 1
fi

if ! command -v sha256sum >/dev/null 2>&1; then
    echo "FAIL: sha256sum is required for reproducibility verification." >&2
    exit 1
fi

mkdir -p "${OUTPUT_DIR}"

for fixture_entry in "${FIXTURES[@]}"; do
    fixture="${fixture_entry%%:*}"
    expected_hash_value="${fixture_entry##*:}"
    raw_path="reproducibility/${fixture}/station_raw.csv"
    expected_path="${REPO_ROOT}/reproducibility/${fixture}/station_cleaned_expected.csv"
    output_path="${OUTPUT_DIR}/${fixture}_station_cleaned.csv"

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
done

echo "PASS: reproducibility verification succeeded."
echo "Output directory: ${OUTPUT_DIR}"
