"""
Test for suspicious spec coverage integrity.

This test checks for cases where test coverage exists but implementation does not,
which indicates either:
- Test coverage is incorrectly marked
- Implementation is incorrectly marked
- A genuine gap in implementation

This should never happen in a healthy codebase.
"""

import csv
from pathlib import Path

import pytest


def test_no_suspicious_coverage():
    """
    Fail if any spec rules have test coverage but no implementation.
    
    Suspicious coverage = test_covered_any == TRUE AND code_implemented == FALSE
    
    This indicates a mismatch where tests claim to cover a spec rule
    that is marked as not implemented.
    """
    spec_coverage_path = Path(__file__).parent.parent / "maintainer" / "exports" / "spec_coverage.csv"
    
    if not spec_coverage_path.exists():
        pytest.skip("spec_coverage.csv not found")
    
    suspicious_rows = []
    
    with open(spec_coverage_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            test_covered_any = row.get("test_covered_any", "").strip().upper()
            code_implemented = row.get("code_implemented", "").strip().upper()
            
            # Find suspicious coverage
            if test_covered_any == "TRUE" and code_implemented == "FALSE":
                suspicious_rows.append({
                    "rule_id": row.get("rule_id", ""),
                    "identifier": row.get("identifier", ""),
                    "rule_type": row.get("rule_type", ""),
                })
    
    if suspicious_rows:
        # Build detailed error message
        error_lines = [
            f"\n❌ Found {len(suspicious_rows)} suspicious coverage entries!",
            "",
            "These rules have test coverage but no implementation:",
            "-" * 80,
        ]
        
        for entry in suspicious_rows:
            error_lines.append(
                f"  • rule_id: {entry['rule_id']}"
            )
            error_lines.append(
                f"    identifier: {entry['identifier']}"
            )
            error_lines.append(
                f"    rule_type: {entry['rule_type']}"
            )
            error_lines.append("")
        
        error_lines.append("-" * 80)
        error_lines.append(
            "Action required: Review maintainer/exports/spec_coverage.csv and verify whether:"
        )
        error_lines.append(
            "  1. Test coverage is incorrectly marked (should be FALSE)"
        )
        error_lines.append(
            "  2. Implementation is incorrectly marked (should be TRUE)"
        )
        error_lines.append(
            "  3. This is a genuine gap requiring implementation or test removal"
        )
        
        pytest.fail("\n".join(error_lines))
