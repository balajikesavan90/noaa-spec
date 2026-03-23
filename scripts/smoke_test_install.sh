#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_PYTHON="${REPO_ROOT}/.venv/bin/python"

if [[ ! -x "${VENV_PYTHON}" ]]; then
    echo "Missing ${VENV_PYTHON}. Run 'poetry install' to create the project-local virtualenv." >&2
    exit 1
fi

"${VENV_PYTHON}" -c "import noaa_spec"
"${VENV_PYTHON}" -m noaa_spec.cli --help >/dev/null

echo "Smoke test passed: .venv can import noaa_spec and run the CLI."
