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

tmpdir="$(mktemp -d)"
trap 'rm -rf "${tmpdir}"' EXIT

if ! python3 -m venv "${tmpdir}/review-venv" >/dev/null 2>&1; then
    echo "FAIL: python3 cannot create a virtual environment." >&2
    echo "python3-venv is required on Ubuntu/Debian reviewer systems." >&2
    print_fix
    exit 1
fi

echo "PASS: reviewer environment prerequisites are available."
echo "python3=$(command -v python3)"
echo "git=$(command -v git)"
echo "bash=$(command -v bash)"
echo "sha256sum=$(command -v sha256sum)"
echo "venv_creation=ok"
