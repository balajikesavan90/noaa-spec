"""Export a reproducibility snapshot with coverage metrics and git hash."""

from __future__ import annotations

import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

RULE_TYPE_ORDER = [
    "range",
    "sentinel",
    "allowed_quality",
    "domain",
    "cardinality",
    "width",
    "arity",
    "unknown",
]
METRIC_RULE_TYPES = [rule_type for rule_type in RULE_TYPE_ORDER if rule_type != "unknown"]


def _as_bool(value: str | None) -> bool:
    return str(value or "").strip().upper() == "TRUE"


def _git_commit_hash(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _load_coverage_metrics(spec_coverage_path: Path) -> dict[str, int]:
    total_spec_rules = 0
    total_metric_rules = 0
    total_synthetic_rows = 0
    implemented = 0
    tested_any = 0
    tested_strict = 0
    wildcard_only = 0
    any_non_wild = 0

    with spec_coverage_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            row_kind = (row.get("row_kind") or "").strip()
            if row_kind == "synthetic":
                total_synthetic_rows += 1
            if row_kind != "spec_rule":
                continue
            total_spec_rules += 1
            rule_type = (row.get("rule_type") or "").strip()
            if rule_type not in METRIC_RULE_TYPES:
                continue
            total_metric_rules += 1
            if _as_bool(row.get("code_implemented")):
                implemented += 1
            covered_any = _as_bool(row.get("test_covered_any"))
            covered_strict = _as_bool(row.get("test_covered_strict"))
            if covered_any:
                tested_any += 1
            if covered_strict:
                tested_strict += 1
            if covered_any and not covered_strict:
                wildcard_only += 1
            if covered_any and (row.get("test_match_strength") or "") != "wildcard_assertion":
                any_non_wild += 1

    return {
        "total_spec_rules": total_spec_rules,
        "total_synthetic_rows": total_synthetic_rows,
        "total_metric_rules": total_metric_rules,
        "unknown_excluded": total_spec_rules - total_metric_rules,
        "rules_implemented": implemented,
        "tested_any": tested_any,
        "tested_strict": tested_strict,
        "tested_any_non_wild": any_non_wild,
        "wildcard_only_tested_any": wildcard_only,
    }


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    spec_coverage_path = repo_root / "maintainer" / "exports" / "spec_coverage.csv"
    if not spec_coverage_path.exists():
        raise FileNotFoundError(f"Missing spec_coverage.csv at {spec_coverage_path}")

    snapshot = {
        "git_commit": _git_commit_hash(repo_root),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "coverage_metrics": _load_coverage_metrics(spec_coverage_path),
    }

    output_path = repo_root / "reproducibility" / "pipeline_snapshot.json"
    output_path.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
