from __future__ import annotations

import pandas as pd

from tools.rule_impact.generate_rule_impact_report import (
    _build_rule_family_impact_summary,
    _collect_qc_reason_counts,
    _count_arity_mismatches,
    _identifier_qc_summary,
)


def test_count_arity_mismatches_detects_expected_part_violations() -> None:
    df = pd.DataFrame(
        {
            "WND": ["090,1,N,0010,1", "090,1,N", None, ""],
            "MA1": ["09000,1,09500,1", "09000,1,09500", None, ""],
            "STATION": ["A", "A", "A", "A"],
        }
    )

    counts, evaluated = _count_arity_mismatches(df)

    assert counts["WND"] == 1
    assert counts["MA1"] == 1
    assert "STATION" not in counts
    assert evaluated["WND"] == 2
    assert evaluated["MA1"] == 2


def test_collect_qc_reason_counts_aggregates_by_identifier_and_field() -> None:
    df = pd.DataFrame(
        {
            "WND__part1__qc_reason": ["OUT_OF_RANGE", None, "SENTINEL_MISSING"],
            "WND__part4__qc_reason": ["OUT_OF_RANGE", "OUT_OF_RANGE", None],
            "TMP__qc_reason": [None, "BAD_QUALITY_CODE", None],
        }
    )

    by_identifier, by_field_reason = _collect_qc_reason_counts(df)

    assert by_identifier["WND"]["OUT_OF_RANGE"] == 3
    assert by_identifier["WND"]["SENTINEL_MISSING"] == 1
    assert by_identifier["TMP"]["BAD_QUALITY_CODE"] == 1
    assert by_field_reason["WND__part1__qc_reason|OUT_OF_RANGE"] == 1
    assert by_field_reason["WND__part4__qc_reason|OUT_OF_RANGE"] == 2


def test_identifier_qc_summary_rolls_up_identifiers_and_families() -> None:
    qc_reasons = {
        "AH1": {"SENTINEL_MISSING": 2},
        "AH2": {"BAD_QUALITY_CODE": 3},
        "TMP": {"OUT_OF_RANGE": 4},
    }
    flag_counts = {
        "qc_arity_mismatch_AH1": 5,
        "qc_pattern_mismatch_AD": 7,
    }

    id_rows, family_rows = _identifier_qc_summary(qc_reasons, flag_counts, total_rows=10)

    id_map = {row["identifier"]: row for row in id_rows}
    fam_map = {row["identifier_family"]: row for row in family_rows}

    assert id_map["AH1"]["count"] == 7
    assert id_map["AH2"]["count"] == 3
    assert id_map["AD"]["count"] == 7
    assert fam_map["AH"]["count"] == 10
    assert fam_map["AD"]["count"] == 7


def test_build_rule_family_impact_summary_computes_expected_fractions() -> None:
    rows = _build_rule_family_impact_summary(
        qc_reason_field_counts={
            "TMP__qc_reason|SENTINEL_MISSING": 4,
            "TMP__qc_reason|OUT_OF_RANGE": 2,
            "WND__part1__qc_reason|MALFORMED_TOKEN": 1,
            "DEW__qc_reason|BAD_QUALITY_CODE": 3,
        },
        flag_counts={
            "qc_domain_invalid_AD": 5,
            "qc_pattern_mismatch_AD": 6,
            "qc_arity_mismatch_AH1": 7,
        },
        arity_mismatch_counts={"WND": 2},
        arity_evaluated_counts={"WND": 10},
        parse_error_total=8,
        total_rows=20,
        qc_reason_column_count=4,
        flag_column_count=3,
        has_parse_error_column=True,
        provenance_family_map={"TMP": {"sentinel_handling", "range_validation"}},
    )

    row_map = {row["rule_family"]: row for row in rows}
    assert row_map["sentinel_handling"]["cells_affected"] == 4
    assert row_map["quality_code_handling"]["cells_affected"] == 3
    assert row_map["range_validation"]["cells_affected"] == 2
    assert row_map["width_validation"]["cells_affected"] == 1
    assert row_map["domain_validation"]["cells_affected"] == 5
    assert row_map["pattern_validation"]["cells_affected"] == 6
    assert row_map["arity_validation"]["cells_affected"] == 9
    assert row_map["structural_parser_guard"]["cells_affected"] == 8
    assert abs(sum(row["fraction_of_total_impacts"] for row in rows) - 1.0) < 1e-9
