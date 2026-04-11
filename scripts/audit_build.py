#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from noaa_spec.internal.build_audit import write_build_audit_report


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit a completed NOAA climate data build.")
    parser.add_argument("--build-root", required=True, help="Path to build_<build_id> root")
    parser.add_argument("--output", required=True, help="Markdown report output path")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    write_build_audit_report(
        Path(args.build_root).resolve(),
        Path(args.output).resolve(),
    )


if __name__ == "__main__":
    main()
