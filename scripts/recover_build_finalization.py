#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from noaa_climate_data.cleaning_runner import recover_completed_build_finalization


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Recover missing terminal publication artifacts for a completed build."
    )
    parser.add_argument("--build-root", required=True, help="Path to build_<build_id> root")
    parser.add_argument(
        "--overwrite-existing",
        action="store_true",
        help="Allow rewriting publication_readiness_gate.json, run_state.json, and post_run_audit.md if they already exist",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    result = recover_completed_build_finalization(
        Path(args.build_root),
        overwrite_existing=bool(args.overwrite_existing),
    )
    print(f"Recovered publication gate: {result['publication_readiness_gate']}")
    print(f"Recovered run state: {result['run_state']}")
    print(f"Recovered post-run audit: {result['post_run_audit']}")


if __name__ == "__main__":
    main()
