#!/usr/bin/env python3
"""Deprecated legacy domain split utility.

This script is intentionally hard-deprecated to avoid maintaining a parallel
set of domain contract logic outside package-governed modules.

Use one of these instead:

- `poetry run python -m noaa_spec.cli cleaning-run --write-domain-splits`
- `poetry run python scripts/split_cleaned_by_domain.py <cleaned_csv>`
"""

from __future__ import annotations


def main() -> None:
    raise SystemExit(
        "scripts/split_domains_by_station.py is deprecated. "
        "Use package-governed domain publishing via cleaning-run or "
        "scripts/split_cleaned_by_domain.py."
    )


if __name__ == "__main__":
    main()
