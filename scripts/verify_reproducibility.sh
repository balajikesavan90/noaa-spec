#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
OUTPUT_DIR="${1:-/tmp/noaa-spec-reproducibility}"

FIXTURES=(
    "minimal:20e571805ad6eafd0d538b57f64e94ddc6aebe78280e3c10c48095f375f49850"
    "minimal_second:e6f8ae6ca75c10bdbbc1714cc61f49d0afcbe7ad6767da58551fc73742dab934"
    "station_03041099999_aonach_mor:8a38e712e4fcb81bc26860b5a575c05951b3d6761fc04511a6237acfe454abe2"
    "station_01116099999_stokka:a13415c7916371aecdfe0b6e8d5c81eae63207ef7a46606e45b98f0e59b7ae6c"
    "station_94368099999_hamilton_island:1d741b69938780663c88d8f4b982f1d01fc6a8212fe4b4fa0878040e222f1f4e"
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
