# Quickstart

Use this path if you want the shortest reviewer workflow without reading the full README first.

## Prerequisites

- working Python 3.12 environment
- `venv` support

On some Linux systems, `venv` support is provided by a separate OS package. If local `venv` setup is unavailable, use the Docker fallback in [../REPRODUCIBILITY.md](../REPRODUCIBILITY.md).

## Run the Minimal Example

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e .
noaa-spec clean reproducibility/minimal/station_raw.csv /tmp/station_cleaned.csv
sha256sum /tmp/station_cleaned.csv
```

Expected checksum:

```text
b48aba1b8a304451dc3874b963d76275bf79ad68c6f28d9190e0e636f2887597
```

Inspect a small subset:

```bash
python3 - <<'PY'
import pandas as pd

cols = [
    "STATION",
    "DATE",
    "temperature_c",
    "temperature_quality_code",
    "visibility_m",
    "TMP__qc_reason",
]
print(pd.read_csv("/tmp/station_cleaned.csv", usecols=cols).head(5).to_string(index=False))
PY
```

Use [UNDERSTANDING_OUTPUT.md](UNDERSTANDING_OUTPUT.md) if you need help reading the canonical columns.
