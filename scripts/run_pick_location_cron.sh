#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

export PATH="/usr/local/bin:/usr/bin:/bin:${HOME}/.local/bin:${PATH:-}"
export POETRY_VIRTUALENVS_IN_PROJECT=false

POETRY_BIN="${POETRY_BIN:-}"
if [[ -z "${POETRY_BIN}" ]]; then
    if command -v poetry >/dev/null 2>&1; then
        POETRY_BIN="$(command -v poetry)"
    elif [[ -x "${HOME}/.local/bin/poetry" ]]; then
        POETRY_BIN="${HOME}/.local/bin/poetry"
    else
        echo "Poetry executable not found in PATH or ${HOME}/.local/bin/poetry" >&2
        exit 1
    fi
fi

cd "${REPO_ROOT}"

exec "${POETRY_BIN}" run python -m noaa_spec.cli pick-location \
    --start-year "${NOAA_PICK_START_YEAR:-1975}" \
    --end-year "${NOAA_PICK_END_YEAR:-2025}" \
    --sleep-seconds "${NOAA_PICK_SLEEP_SECONDS:-0.5}" \
    --output-dir "${NOAA_PICK_OUTPUT_DIR:-/media/balaji-kesavan/LaCie/NOAA_Data}"
