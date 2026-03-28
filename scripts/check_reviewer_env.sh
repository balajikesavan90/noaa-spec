#!/usr/bin/env bash

set -euo pipefail

python - <<'PY'
import importlib.util
import pathlib
import platform
import sys

print(f"python_executable={sys.executable}")
print(f"python_version={platform.python_version()}")

spec = importlib.util.find_spec("noaa_spec")
if spec is None or spec.origin is None:
    print("noaa_spec_import=missing")
else:
    print(f"noaa_spec_import={pathlib.Path(spec.origin).resolve()}")
PY

python -m pip --version
