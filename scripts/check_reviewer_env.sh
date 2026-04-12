#!/usr/bin/env bash

set -euo pipefail

FIX_LINE_1="sudo apt-get update"
FIX_LINE_2="sudo apt-get install -y python3 python3-venv git coreutils bash"

print_fix() {
    echo "Install the missing OS dependencies with:" >&2
    echo "${FIX_LINE_1}" >&2
    echo "${FIX_LINE_2}" >&2
}

missing=()

for command_name in python3 git bash sha256sum; do
    if ! command -v "${command_name}" >/dev/null 2>&1; then
        missing+=("${command_name}")
    fi
done

if ((${#missing[@]} > 0)); then
    echo "FAIL: missing required system tools: ${missing[*]}" >&2
    print_fix
    exit 1
fi

if ! python3 -c 'import sys; raise SystemExit(0 if (3, 11) <= sys.version_info[:2] < (3, 13) else 1)' >/dev/null 2>&1; then
    echo "FAIL: python3 must be Python 3.11 or 3.12." >&2
    print_fix
    exit 1
fi

tmpdir="$(mktemp -d)"
test_venv_tmp="${tmpdir}/test_venv_tmp"
trap 'rm -rf "${tmpdir}"' EXIT

if ! python3 -m venv "${test_venv_tmp}" >/dev/null 2>&1; then
    echo "Missing python3-venv. Run: sudo apt-get install python3-venv" >&2
    exit 1
fi

rm -rf "${test_venv_tmp}"

echo "PASS: reproducibility environment prerequisites are available."
echo "python3=$(command -v python3)"
echo "python3_version=$(python3 -c 'import sys; print(\".\".join(map(str, sys.version_info[:3])))')"
echo "git=$(command -v git)"
echo "bash=$(command -v bash)"
echo "sha256sum=$(command -v sha256sum)"
echo "venv_creation=ok"
