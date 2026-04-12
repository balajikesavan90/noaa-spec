"""Minimal pandas-vs-NOAA-Spec sentinel example."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from noaa_spec.cleaning import clean_noaa_dataframe


def main() -> None:
    raw = pd.DataFrame(
        [
            {
                "STATION": "99999999999",
                "DATE": "2024-01-01T00:00:00",
                "VIS": "999999,9,N,1",
                "TMP": "+9999,9",
            }
        ]
    )

    visibility_token = raw.loc[0, "VIS"]
    naive_visibility = float(visibility_token.split(",")[0])

    cleaned = clean_noaa_dataframe(raw, keep_raw=False, strict_mode=True)
    row = cleaned.iloc[0]

    print(f"Naive pandas-style visibility value: {naive_visibility}")
    print(f"NOAA-Spec visibility_m: {row['visibility_m']}")
    print(f"NOAA-Spec visibility_quality_code: {row['visibility_quality_code']}")
    print(f"NOAA-Spec VIS__part1__qc_reason: {row['VIS__part1__qc_reason']}")
    print(f"NOAA-Spec temperature_c: {row['temperature_c']}")
    print(f"NOAA-Spec temperature_quality_code: {row['temperature_quality_code']}")
    print(f"NOAA-Spec TMP__qc_reason: {row['TMP__qc_reason']}")


if __name__ == "__main__":
    main()
