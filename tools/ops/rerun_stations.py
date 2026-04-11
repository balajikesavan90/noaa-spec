#!/usr/bin/env python3
"""Re-run pipeline for stations that need updated outputs."""
import sys
import time
from pathlib import Path

import pandas as pd

from noaa_spec.internal.pipeline import process_location_from_raw

STATIONS = [
    "57067099999",
    "01116099999",
    "16754399999",
    "78724099999",
    "82795099999",
    "83692099999",
    "03041099999",
    "27679099999",
    "34880099999",
    "40435099999",
    "94368099999",
]

OUTPUT_BASE = Path("output")


def main():
    for station in STATIONS:
        fname = f"{station}.csv"
        outdir = OUTPUT_BASE / station
        outdir.mkdir(parents=True, exist_ok=True)
        raw_path = outdir / "LocationData_Raw.csv"
        print(f"\n{'='*60}")
        print(f"Processing {station} ...")
        t0 = time.time()
        try:
            if not raw_path.exists():
                raise FileNotFoundError(f"Missing raw file: {raw_path}")
            raw = pd.read_csv(raw_path, dtype=str, low_memory=False)
            outputs = process_location_from_raw(raw, location_id=None)
            outputs.raw.to_csv(raw_path, index=False)
            outputs.cleaned.to_csv(outdir / "LocationData_Cleaned.csv", index=False)
            outputs.hourly.to_csv(outdir / "LocationData_Hourly.csv", index=False)
            outputs.monthly.to_csv(outdir / "LocationData_Monthly.csv", index=False)
            outputs.yearly.to_csv(outdir / "LocationData_Yearly.csv", index=False)
            elapsed = time.time() - t0
            print(f"  ✓ Done in {elapsed:.1f}s — raw rows: {len(outputs.raw)}")
        except Exception as e:
            elapsed = time.time() - t0
            print(f"  ✗ FAILED after {elapsed:.1f}s: {e}", file=sys.stderr)

    print(f"\n{'='*60}")
    print("All stations processed.")


if __name__ == "__main__":
    main()
