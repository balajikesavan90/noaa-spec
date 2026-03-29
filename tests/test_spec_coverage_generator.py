"""Smoke test for spec coverage generator outputs."""

from __future__ import annotations

import csv
import importlib.util
from pathlib import Path
import re
import sys

import pytest


def _load_generator_module(repo_root: Path):
    script_path = repo_root / "tools" / "spec_coverage" / "generate_spec_coverage.py"
    spec = importlib.util.spec_from_file_location("spec_coverage_generator", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load generator module from {script_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _read_csv_rows(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader)


def _stable_sort_key(row: dict[str, str]) -> tuple[object, ...]:
    row_kind_rank = {
        "spec_rule": 0,
        "structural_rule": 1,
        "documentation_rule": 2,
        "synthetic": 3,
    }.get(row.get("row_kind", ""), 4)
    line_start = int(row["spec_line_start"]) if row.get("spec_line_start", "").isdigit() else 10**9
    line_end = int(row["spec_line_end"]) if row.get("spec_line_end", "").isdigit() else 10**9
    return (
        row_kind_rank,
        row.get("spec_file", ""),
        line_start,
        line_end,
        row.get("identifier", ""),
        row.get("rule_type", ""),
        row.get("rule_id", ""),
    )


def _write_fixture_spec_doc(
    module,
    path: Path,
    part_bodies: dict[str, list[str]] | None = None,
    preface_lines: list[str] | None = None,
) -> list[str]:
    part_bodies = part_bodies or {}
    lines = list(preface_lines or ["Preface"])
    for spec_part, anchor in module.SPEC_PART_ANCHORS:
        lines.append(anchor)
        lines.extend(part_bodies.get(spec_part, []))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return lines


def _line_numbers(lines: list[str], text: str) -> list[int]:
    return [idx for idx, line in enumerate(lines, start=1) if line == text]


def test_rule_ids_are_line_stable_and_rows_are_not_merged() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    module = _load_generator_module(repo_root)

    row_a = module.SpecRuleRow(
        spec_part="99",
        spec_doc="part-99-fixture.md",
        spec_file="part-99-fixture.md",
        spec_line_start=10,
        spec_line_end=10,
        identifier="AB1",
        identifier_family="AB",
        rule_type="range",
        spec_rule_text="MIN 0 MAX 9",
        min_value="0",
        max_value="9",
    )
    row_b = module.SpecRuleRow(
        spec_part="99",
        spec_doc="part-99-fixture.md",
        spec_file="part-99-fixture.md",
        spec_line_start=20,
        spec_line_end=20,
        identifier="AB1",
        identifier_family="AB",
        rule_type="range",
        spec_rule_text="MIN 0 MAX 9",
        min_value="0",
        max_value="9",
    )

    rows = module.normalize_and_assign_rule_ids([row_a, row_b])
    assert rows[0].rule_id == rows[1].rule_id
    assert re.fullmatch(r"part-99-fixture\.md::[0-9a-f]{12}::AB1::range::[0-9a-f]{10}", rows[0].rule_id)

    merged = module.merge_duplicate_rows(rows)
    assert len(merged) == 2, "Rows with identical payload but different line ranges must remain separate"


def _fixture_row(module, identifier: str, rule_type: str = "range"):
    return module.SpecRuleRow(
        spec_part="99",
        spec_doc="part-99-fixture.md",
        spec_file="part-99-fixture.md",
        spec_line_start=1,
        spec_line_end=1,
        identifier=identifier,
        identifier_family=module.identifier_family(identifier),
        rule_type=rule_type,
        spec_rule_text=f"{identifier} {rule_type} fixture",
    )


def test_wildcard_match_is_any_but_not_strict() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    module = _load_generator_module(repo_root)

    row = _fixture_row(module, "TMP")
    test_index = module.TestEvidenceIndex()
    test_index.add_wildcard_assertion("range", ("tests/test_cleaning.py", 123))

    location, strength = test_index.find(
        row.identifier,
        row.identifier_family,
        row.rule_type,
        row.min_value,
        row.max_value,
        row.sentinel_values,
        row.allowed_values_or_codes,
    )
    module.apply_test_match_result(row, strength, location)

    assert row.test_match_strength == "wildcard_assertion"
    assert row.test_covered_any is True
    assert row.test_covered_strict is False
    assert row.test_covered is True
    assert row.test_location == "tests/test_cleaning.py:123"


def test_exact_match_is_strict() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    module = _load_generator_module(repo_root)

    row = _fixture_row(module, "TMP")
    test_index = module.TestEvidenceIndex()
    test_index.add_exact_assertion("TMP", "range", ("tests/test_cleaning.py", 222))

    location, strength = test_index.find(
        row.identifier,
        row.identifier_family,
        row.rule_type,
        row.min_value,
        row.max_value,
        row.sentinel_values,
        row.allowed_values_or_codes,
    )
    module.apply_test_match_result(row, strength, location)

    assert row.test_match_strength == "exact_assertion"
    assert row.test_covered_any is True
    assert row.test_covered_strict is True
    assert row.test_covered is True
    assert row.test_location == "tests/test_cleaning.py:222"


def test_no_test_match_sets_none_and_false() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    module = _load_generator_module(repo_root)

    row = _fixture_row(module, "TMP")
    test_index = module.TestEvidenceIndex()

    location, strength = test_index.find(
        row.identifier,
        row.identifier_family,
        row.rule_type,
        row.min_value,
        row.max_value,
        row.sentinel_values,
        row.allowed_values_or_codes,
    )
    module.apply_test_match_result(row, strength, location)

    assert row.test_match_strength == "none"
    assert row.test_covered_any is False
    assert row.test_covered_strict is False
    assert row.test_covered is False
    assert row.test_location == ""


def test_strict_coverage_guard_wildcards_cannot_make_full_strict_coverage() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    module = _load_generator_module(repo_root)

    rows = [
        _fixture_row(module, "TMP1"),
        _fixture_row(module, "TMP2"),
        _fixture_row(module, "TMP3"),
        _fixture_row(module, "TMP4"),
    ]
    for row in rows:
        row.code_implemented = False

    test_index = module.TestEvidenceIndex()
    test_index.add_wildcard_assertion("range", ("tests/test_cleaning.py", 300))
    test_index.add_exact_assertion("TMP1", "range", ("tests/test_cleaning.py", 301))

    for row in rows:
        location, strength = test_index.find(
            row.identifier,
            row.identifier_family,
            row.rule_type,
            row.min_value,
            row.max_value,
            row.sentinel_values,
            row.allowed_values_or_codes,
        )
        module.apply_test_match_result(row, strength, location)

    strict_tested_pct = 100.0 * sum(1 for row in rows if row.test_covered_strict) / len(rows)
    any_tested_pct = 100.0 * sum(1 for row in rows if row.test_covered_any) / len(rows)
    assert strict_tested_pct < 100.0
    assert any_tested_pct == 100.0


def test_exact_only_width_and_arity_ignore_family_and_wildcard() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    module = _load_generator_module(repo_root)

    test_index = module.TestEvidenceIndex()
    test_index.add_family_assertion("TMP", "width", ("tests/test_cleaning.py", 401))
    test_index.add_wildcard_assertion("width", ("tests/test_cleaning.py", 402))
    test_index.add_family_assertion("TMP", "arity", ("tests/test_cleaning.py", 403))
    test_index.add_wildcard_assertion("arity", ("tests/test_cleaning.py", 404))

    width_row = _fixture_row(module, "TMP1", "width")
    width_row.allowed_values_or_codes = "5"
    width_loc, width_strength = test_index.find(
        width_row.identifier,
        width_row.identifier_family,
        width_row.rule_type,
        width_row.min_value,
        width_row.max_value,
        width_row.sentinel_values,
        width_row.allowed_values_or_codes,
    )
    assert width_loc is None
    assert width_strength == "none"

    arity_row = _fixture_row(module, "TMP1", "arity")
    arity_row.allowed_values_or_codes = "3"
    arity_loc, arity_strength = test_index.find(
        arity_row.identifier,
        arity_row.identifier_family,
        arity_row.rule_type,
        arity_row.min_value,
        arity_row.max_value,
        arity_row.sentinel_values,
        arity_row.allowed_values_or_codes,
    )
    assert arity_loc is None
    assert arity_strength == "none"


def test_exact_only_explicit_token_sets_ignore_family_and_wildcard() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    module = _load_generator_module(repo_root)

    test_index = module.TestEvidenceIndex()
    test_index.add_family_assertion("TMP", "sentinel", ("tests/test_cleaning.py", 451))
    test_index.add_wildcard_assertion("sentinel", ("tests/test_cleaning.py", 452))
    test_index.add_family_assertion("TMP", "domain", ("tests/test_cleaning.py", 453))
    test_index.add_wildcard_assertion("domain", ("tests/test_cleaning.py", 454))
    test_index.add_family_assertion("TMP", "allowed_quality", ("tests/test_cleaning.py", 455))
    test_index.add_wildcard_assertion("allowed_quality", ("tests/test_cleaning.py", 456))

    sentinel_row = _fixture_row(module, "TMP1", "sentinel")
    sentinel_row.sentinel_values = "9999"
    sentinel_loc, sentinel_strength = test_index.find(
        sentinel_row.identifier,
        sentinel_row.identifier_family,
        sentinel_row.rule_type,
        sentinel_row.min_value,
        sentinel_row.max_value,
        sentinel_row.sentinel_values,
        sentinel_row.allowed_values_or_codes,
    )
    assert sentinel_loc is None
    assert sentinel_strength == "none"

    domain_row = _fixture_row(module, "TMP1", "domain")
    domain_row.allowed_values_or_codes = "A|B"
    domain_loc, domain_strength = test_index.find(
        domain_row.identifier,
        domain_row.identifier_family,
        domain_row.rule_type,
        domain_row.min_value,
        domain_row.max_value,
        domain_row.sentinel_values,
        domain_row.allowed_values_or_codes,
    )
    assert domain_loc is None
    assert domain_strength == "none"

    quality_row = _fixture_row(module, "TMP1", "allowed_quality")
    quality_row.allowed_values_or_codes = "V01|V02"
    quality_loc, quality_strength = test_index.find(
        quality_row.identifier,
        quality_row.identifier_family,
        quality_row.rule_type,
        quality_row.min_value,
        quality_row.max_value,
        quality_row.sentinel_values,
        quality_row.allowed_values_or_codes,
    )
    assert quality_loc is None
    assert quality_strength == "none"


def test_report_uses_strict_kpi_and_quarantines_wildcard_only(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    module = _load_generator_module(repo_root)

    strict_row = _fixture_row(module, "AA1", "range")
    strict_row.spec_part = "01"
    strict_row.code_implemented = True
    module.apply_test_match_result(strict_row, "exact_assertion", ("tests/test_cleaning.py", 500))

    wildcard_row = _fixture_row(module, "AA2", "width")
    wildcard_row.spec_part = "02"
    wildcard_row.code_implemented = False
    module.apply_test_match_result(wildcard_row, "wildcard_assertion", ("tests/test_cleaning.py", 501))

    none_row = _fixture_row(module, "AA3", "domain")
    none_row.spec_part = "03"
    none_row.code_implemented = False
    module.apply_test_match_result(none_row, "none", None)

    report_path = tmp_path / "docs/internal/reports/SPEC_COVERAGE_REPORT.md"
    module.build_report(
        [strict_row, wildcard_row, none_row],
        report_path,
        arity_tests_detected=True,
    )
    report_text = report_path.read_text(encoding="utf-8")

    assert "Progress KPI (`tested_strict`): **1** (33.3%)" in report_text
    assert "Weak coverage (`tested_any`, includes wildcard): **2** (66.7%)" in report_text
    assert "Wildcard-only tested_any (not counted toward progress): **1** (33.3%)" in report_text
    assert "## Wildcard-only coverage (not counted toward progress)" in report_text
    assert "| width | 1 | 33.3% |" in report_text


def test_report_metrics_include_structural_and_exclude_documentation(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    module = _load_generator_module(repo_root)

    structural_row = _fixture_row(module, "CONTROL_POS_1_4", "width")
    structural_row.row_kind = "structural_rule"
    structural_row.code_implemented = False
    module.apply_test_match_result(structural_row, "none", None)

    documentation_row = _fixture_row(module, "UNSPECIFIED", "unknown")
    documentation_row.row_kind = "documentation_rule"
    documentation_row.code_implemented = False
    module.apply_test_match_result(documentation_row, "none", None)

    report_path = tmp_path / "docs/internal/reports/SPEC_COVERAGE_REPORT.md"
    module.build_report(
        [structural_row, documentation_row],
        report_path,
        arity_tests_detected=True,
    )
    report_text = report_path.read_text(encoding="utf-8")

    assert "Structural rules (control-position rules like `POS 1-4 width 4`): **1**" in report_text
    assert "Documentation rules count (excluded): **1**" in report_text
    assert "Metric-eligible rules (excluding `unknown`): **1**" in report_text


def test_top_50_real_gaps_ranking_priority_is_stable(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    module = _load_generator_module(repo_root)

    top_row = _fixture_row(module, "AA1", "range")
    top_row.spec_part = "01"
    top_row.enforcement_layer = "neither"
    top_row.code_implemented = False
    top_row.test_covered_any = False
    top_row.test_covered_strict = False
    top_row.test_match_strength = "none"

    second_row = _fixture_row(module, "AA2", "range")
    second_row.spec_line_start = 2
    second_row.spec_line_end = 2
    second_row.enforcement_layer = "neither"
    second_row.code_implemented = True
    second_row.test_covered_any = True
    second_row.test_covered_strict = False
    second_row.test_match_strength = "family_assertion"

    third_row = _fixture_row(module, "AA3", "range")
    third_row.spec_line_start = 3
    third_row.spec_line_end = 3
    third_row.enforcement_layer = "both"
    third_row.code_implemented = False
    third_row.test_covered_any = False
    third_row.test_covered_strict = False
    third_row.test_match_strength = "none"

    excluded_unspecified = _fixture_row(module, "UNSPECIFIED", "range")
    excluded_unspecified.spec_line_start = 4
    excluded_unspecified.spec_line_end = 4
    excluded_unspecified.enforcement_layer = "neither"
    excluded_unspecified.code_implemented = False
    excluded_unspecified.test_covered_any = False
    excluded_unspecified.test_covered_strict = False
    excluded_unspecified.test_match_strength = "none"

    report_path = tmp_path / "docs/internal/reports/SPEC_COVERAGE_REPORT.md"
    module.build_report(
        [top_row, second_row, third_row, excluded_unspecified],
        report_path,
        arity_tests_detected=True,
    )
    report_text = report_path.read_text(encoding="utf-8")

    section = report_text.split("## Top 50 real gaps (strict)", 1)[1]
    table_lines = [line for line in section.splitlines() if line.startswith("| ")]
    data_lines = table_lines[2:5]
    identifiers = [line.split("|")[3].strip() for line in data_lines]
    assert identifiers == ["AA1", "AA2", "AA3"]
    assert "UNSPECIFIED" not in "\n".join(data_lines)


def test_segment_spec_doc_lines_detects_expected_order_on_real_document() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    module = _load_generator_module(repo_root)

    spec_path = repo_root / "spec_sources/isd-format-document-parts" / module.SPEC_DOC_NAME
    lines = spec_path.read_text(encoding="utf-8").splitlines()
    segments = module.segment_spec_doc_lines(lines)

    assert [segment.spec_part for segment in segments] == [part for part, _ in module.SPEC_PART_ANCHORS]
    late_positions = {segment.spec_part: segment.anchor_line for segment in segments}
    assert [late_positions[part] for part in module.LATE_DOCUMENT_PART_ORDER] == sorted(
        late_positions[part] for part in module.LATE_DOCUMENT_PART_ORDER
    )


def test_segment_spec_doc_lines_uses_exact_anchor_matching(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    module = _load_generator_module(repo_root)

    spec_path = tmp_path / module.SPEC_DOC_NAME
    lines = _write_fixture_spec_doc(
        module,
        spec_path,
        preface_lines=["Control Data Section - preface prose"],
    )
    segments = module.segment_spec_doc_lines(lines)
    by_part = {segment.spec_part: segment for segment in segments}

    assert by_part["02"].anchor_line == _line_numbers(lines, "Control Data Section")[0]
    assert by_part["10"].anchor_line == _line_numbers(lines, "Hourly Temperature Section identifier")[0]
    assert by_part["10"].anchor_line != _line_numbers(lines, "Subhourly Temperature Section identifier")[0]


def test_segment_spec_doc_lines_uses_first_duplicate_after_prior_boundary(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    module = _load_generator_module(repo_root)

    spec_path = tmp_path / module.SPEC_DOC_NAME
    lines = _write_fixture_spec_doc(
        module,
        spec_path,
        part_bodies={"15": ["SUNSHINE-OBSERVATION identifier"]},
    )
    segments = module.segment_spec_doc_lines(lines)
    by_part = {segment.spec_part: segment for segment in segments}

    sunshine_lines = _line_numbers(lines, "SUNSHINE-OBSERVATION identifier")
    assert len(sunshine_lines) == 2
    assert by_part["16"].anchor_line == sunshine_lines[0]
    assert by_part["16"].end_line < by_part["17"].anchor_line


def test_segment_spec_doc_lines_missing_anchor_raises(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    module = _load_generator_module(repo_root)

    spec_path = tmp_path / module.SPEC_DOC_NAME
    lines = _write_fixture_spec_doc(module, spec_path)
    lines.remove("Hourly Solar Angle Section identifier")

    with pytest.raises(module.SpecSegmentationError, match="Missing required anchor"):
        module.segment_spec_doc_lines(lines)


def test_segment_spec_doc_lines_out_of_order_anchor_raises(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    module = _load_generator_module(repo_root)

    spec_path = tmp_path / module.SPEC_DOC_NAME
    lines = _write_fixture_spec_doc(module, spec_path)
    part_25_idx = lines.index("SEA-SURFACE-TEMPERATURE-OBSERVATION identifier")
    part_29_idx = lines.index("SUPPLEMENTARY-WIND-OBSERVATION identifier")
    part_25_anchor = lines.pop(part_25_idx)
    lines.insert(part_29_idx, part_25_anchor)

    with pytest.raises(module.SpecSegmentationError):
        module.segment_spec_doc_lines(lines)


def test_parse_spec_doc_part02_backfills_pos_identifier_and_assigns_control_pos_fallback(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    module = _load_generator_module(repo_root)

    spec_path = tmp_path / module.SPEC_DOC_NAME
    lines = _write_fixture_spec_doc(
        module,
        spec_path,
        part_bodies={
            "02": [
                "POS: 24-27",
                "GEOPHYSICAL-POINT-OBSERVATION time",
                "MIN: 0000 MAX: 2359",
                "",
                "POS: 42-46",
                "GEOPHYSICAL-REPORT-TYPE code",
                "SY-AU = Synoptic and auto merged report",
                "99999 = Missing",
                "",
                "POS: 1-4",
                "TOTAL-VARIABLE-CHARACTERS",
                "MIN: 0000 MAX: 9999",
                "",
                "POS: 29-34",
                "GEOPHYSICAL-POINT-OBSERVATION latitude coordinate",
                "MIN: -90000 MAX: +90000",
                "",
            ]
        },
    )

    known_identifiers = {
        "DATE",
        "TIME",
        "LATITUDE",
        "LONGITUDE",
        "ELEVATION",
        "CALL_SIGN",
        "REPORT_TYPE",
        "QC_PROCESS",
        "AU",
        "SA",
    }
    known_families = {module.identifier_family(value) for value in known_identifiers}

    rows = module.parse_spec_doc(spec_path, known_identifiers, known_families)

    pos_24_27_line = _line_numbers(lines, "POS: 24-27")[0]
    time_range_line = _line_numbers(lines, "MIN: 0000 MAX: 2359")[0]
    missing_line = _line_numbers(lines, "99999 = Missing")[0]
    pos_1_4_line = _line_numbers(lines, "POS: 1-4")[0]
    total_range_line = _line_numbers(lines, "MIN: 0000 MAX: 9999")[0]
    pos_29_34_line = _line_numbers(lines, "POS: 29-34")[0]

    width_24_27 = [r for r in rows if r.rule_type == "width" and r.spec_line_start == pos_24_27_line]
    assert width_24_27 and all(r.identifier == "CONTROL_POS_24_27" for r in width_24_27)

    range_24_27 = [r for r in rows if r.rule_type == "range" and r.spec_line_start == time_range_line]
    assert range_24_27 and all(r.identifier == "TIME" for r in range_24_27)

    sentinel_rows = [r for r in rows if r.rule_type == "sentinel" and r.spec_line_start == missing_line]
    assert sentinel_rows and all(r.identifier == "REPORT_TYPE" for r in sentinel_rows)

    domain_rows = [r for r in rows if r.rule_type == "domain"]
    assert domain_rows and all(r.identifier == "REPORT_TYPE" for r in domain_rows)
    assert all(r.identifier != "AU" for r in domain_rows)

    control_pos_width_rows = [r for r in rows if r.rule_type == "width" and r.spec_line_start == pos_1_4_line]
    assert control_pos_width_rows and all(r.identifier == "CONTROL_POS_1_4" for r in control_pos_width_rows)
    control_pos_range_rows = [r for r in rows if r.rule_type == "range" and r.spec_line_start == total_range_line]
    assert control_pos_range_rows and all(r.identifier == "CONTROL_POS_1_4" for r in control_pos_range_rows)

    control_pos_29_34_width_rows = [r for r in rows if r.rule_type == "width" and r.spec_line_start == pos_29_34_line]
    assert control_pos_29_34_width_rows and all(
        r.identifier == "CONTROL_POS_29_34" for r in control_pos_29_34_width_rows
    )


def test_parse_spec_doc_part03_reanchors_context_between_mandatory_sections(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    module = _load_generator_module(repo_root)

    spec_path = tmp_path / module.SPEC_DOC_NAME
    _write_fixture_spec_doc(
        module,
        spec_path,
        part_bodies={
            "03": [
                "POS: 60-63",
                "WIND-OBSERVATION direction angle",
                "MIN: 001 MAX: 360",
                "999 = Missing.",
                "",
                "POS: 71-75",
                "SKY-CONDITION-OBSERVATION ceiling height dimension",
                "MIN: 00000 MAX: 22000",
                "99999 = Missing.",
                "",
                "POS: 79-84",
                "VISIBILITY-OBSERVATION distance dimension",
                "MIN: 000000 MAX: 160000",
                "Missing = 999999",
                "",
                "POS: 88-92",
                "AIR-TEMPERATURE-OBSERVATION air temperature",
                "MIN: -0932 MAX: +0618",
                "+9999 = Missing.",
                "",
                "POS: 94-98",
                "AIR-TEMPERATURE-OBSERVATION dew point temperature",
                "MIN: -0982 MAX: +0368",
                "+9999 = Missing.",
                "",
                "POS: 100-104",
                "ATMOSPHERIC-PRESSURE-OBSERVATION sea level pressure",
                "MIN: 08600 MAX: 10900",
                "99999 = Missing.",
                "",
            ]
        },
    )

    known_identifiers = {"WND", "CIG", "VIS", "TMP", "DEW", "SLP"}
    known_families = {module.identifier_family(value) for value in known_identifiers}

    rows = module.parse_spec_doc(spec_path, known_identifiers, known_families)

    def _range_rows(min_value: str, max_value: str):
        return [
            r
            for r in rows
            if r.rule_type == "range" and r.min_value == min_value and r.max_value == max_value
        ]

    cigs = _range_rows("00000", "22000")
    viss = _range_rows("000000", "160000")
    tmps = _range_rows("-0932", "0618")
    dews = _range_rows("-0982", "0368")
    slps = _range_rows("08600", "10900")

    assert cigs and all(r.identifier == "CIG" for r in cigs)
    assert viss and all(r.identifier == "VIS" for r in viss)
    assert tmps and all(r.identifier == "TMP" for r in tmps)
    assert dews and all(r.identifier == "DEW" for r in dews)
    assert slps and all(r.identifier == "SLP" for r in slps)
    assert not any(r.identifier == "WND" for r in cigs + viss + tmps + dews + slps)


def test_parse_spec_doc_maps_fld_len_three_header_context_rows(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    module = _load_generator_module(repo_root)

    spec_path = tmp_path / module.SPEC_DOC_NAME
    mapping_items = sorted(module.SECTION_IDENTIFIER_CONTEXT_MAP.items())
    part_bodies: dict[str, list[str]] = {}
    phrase_to_identifier = {phrase: identifier for (_, phrase), identifier in mapping_items}
    for (part, phrase), identifier in mapping_items:
        part_bodies.setdefault(part, []).extend(["FLD LEN: 3", phrase])

    lines = _write_fixture_spec_doc(module, spec_path, part_bodies=part_bodies)
    expected_by_start_line = {
        idx: phrase_to_identifier[lines[idx].lower()]
        for idx, value in enumerate(lines, start=1)
        if value == "FLD LEN: 3" and idx < len(lines) and lines[idx].lower() in phrase_to_identifier
    }
    known_identifiers = set(expected_by_start_line.values())
    known_families = {module.identifier_family(value) for value in known_identifiers}

    rows = module.parse_spec_doc(spec_path, known_identifiers, known_families)
    width_rows = [row for row in rows if row.rule_type == "width" and row.allowed_values_or_codes == "3"]

    matched_starts = {row.spec_line_start for row in width_rows if row.spec_line_start in expected_by_start_line}
    assert matched_starts == set(expected_by_start_line)
    for row in width_rows:
        if row.spec_line_start not in expected_by_start_line:
            continue
        assert row.identifier == expected_by_start_line[row.spec_line_start]
        assert row.identifier != "UNSPECIFIED"


def test_parse_spec_doc_part03_pos_width_uses_next_context_for_wnd(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    module = _load_generator_module(repo_root)

    spec_path = tmp_path / module.SPEC_DOC_NAME
    lines = _write_fixture_spec_doc(
        module,
        spec_path,
        part_bodies={"03": ["POS: 61-63", "WIND-OBSERVATION direction angle"]},
    )

    known_identifiers = {"WND"}
    known_families = {module.identifier_family(value) for value in known_identifiers}

    rows = module.parse_spec_doc(spec_path, known_identifiers, known_families)
    width_line = _line_numbers(lines, "POS: 61-63")[0]
    width_rows = [row for row in rows if row.rule_type == "width" and row.spec_line_start == width_line]

    assert width_rows
    assert all(row.identifier == "WND" for row in width_rows)
    assert all(row.allowed_values_or_codes == "3" for row in width_rows)


def test_parse_spec_doc_rule_ids_survive_blank_line_shifts(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    module = _load_generator_module(repo_root)

    spec_path = tmp_path / module.SPEC_DOC_NAME
    part_bodies = {
        "02": [
            "POS: 24-27",
            "GEOPHYSICAL-POINT-OBSERVATION time",
            "MIN: 0000 MAX: 2359",
        ]
    }
    _write_fixture_spec_doc(module, spec_path, part_bodies=part_bodies, preface_lines=["Preface"])
    known_identifiers = {"TIME"}
    known_families = {module.identifier_family(value) for value in known_identifiers}
    rows_a = module.normalize_and_assign_rule_ids(module.parse_spec_doc(spec_path, known_identifiers, known_families))
    range_a = next(row for row in rows_a if row.identifier == "TIME" and row.rule_type == "range")

    _write_fixture_spec_doc(module, spec_path, part_bodies=part_bodies, preface_lines=["Preface", "", "", ""])
    rows_b = module.normalize_and_assign_rule_ids(module.parse_spec_doc(spec_path, known_identifiers, known_families))
    range_b = next(row for row in rows_b if row.identifier == "TIME" and row.rule_type == "range")

    assert range_a.rule_id == range_b.rule_id
    assert range_a.spec_line_start != range_b.spec_line_start


def test_constants_coverage_matches_control_pos_identifier_rules() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    module = _load_generator_module(repo_root)
    constants_module = module.load_constants_module(repo_root)
    constants_ast = module.parse_constants_ast(repo_root / "src" / "noaa_spec" / "constants.py")

    width_row = _fixture_row(module, "CONTROL_POS_57_60", "width")
    width_row.spec_rule_text = "POS: 57-60"
    width_row.allowed_values_or_codes = "4"
    width_impl, width_location, width_reason = module.coverage_in_constants_for_row(
        width_row,
        constants_module,
        constants_ast,
    )
    assert width_impl is True
    assert width_reason == "strict_gate_width"
    assert "src/noaa_spec/constants.py:" in width_location

    sentinel_row = _fixture_row(module, "CONTROL_POS_28_28", "sentinel")
    sentinel_row.sentinel_values = "9"
    sentinel_impl, sentinel_location, sentinel_reason = module.coverage_in_constants_for_row(
        sentinel_row,
        constants_module,
        constants_ast,
    )
    assert sentinel_impl is True
    assert sentinel_reason == "field_rule_sentinel"
    assert "src/noaa_spec/constants.py:" in sentinel_location

    domain_row = _fixture_row(module, "CONTROL_POS_47_51", "domain")
    domain_row.allowed_values_or_codes = "FM-15|SY-MT"
    domain_impl, domain_location, domain_reason = module.coverage_in_constants_for_row(
        domain_row,
        constants_module,
        constants_ast,
    )
    assert domain_impl is True
    assert domain_reason in {"field_rule_domain_values", "field_rule_domain_pattern"}
    assert "src/noaa_spec/constants.py:" in domain_location


def test_classify_extracted_row_kinds_marks_structural_and_documentation_rows() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    module = _load_generator_module(repo_root)

    structural = module.SpecRuleRow(
        spec_part="02",
        spec_doc="part-02-control-data-section.md",
        spec_file="part-02-control-data-section.md",
        spec_line_start=7,
        spec_line_end=7,
        spec_evidence="POS: 1-4",
        identifier="CONTROL_POS_1_4",
        identifier_family="CONTROL",
        rule_type="width",
        spec_rule_text="POS 1-4 width 4",
        allowed_values_or_codes="4",
    )
    documentation = module.SpecRuleRow(
        spec_part="02",
        spec_doc="part-02-control-data-section.md",
        spec_file="part-02-control-data-section.md",
        spec_line_start=99,
        spec_line_end=99,
        spec_evidence="Reference notes for section layout",
        identifier="UNSPECIFIED",
        identifier_family="UNSPECIFIED",
        rule_type="unknown",
        spec_rule_text="Layout notes for reference only",
    )
    normal = module.SpecRuleRow(
        spec_part="03",
        spec_doc="part-03-mandatory-data-section.md",
        spec_file="part-03-mandatory-data-section.md",
        spec_line_start=10,
        spec_line_end=10,
        spec_evidence="MIN: -0932 MAX: +0618",
        identifier="TMP",
        identifier_family="TMP",
        rule_type="range",
        spec_rule_text="MIN -0932 MAX +0618",
        min_value="-0932",
        max_value="0618",
    )

    rows = module.classify_extracted_row_kinds([structural, documentation, normal])
    by_text = {row.spec_rule_text: row.row_kind for row in rows}
    assert by_text["POS 1-4 width 4"] == "structural_rule"
    assert by_text["Layout notes for reference only"] == "documentation_rule"
    assert by_text["MIN -0932 MAX +0618"] == "spec_rule"


def test_parse_tests_evidence_detects_control_identifiers_with_long_names(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    module = _load_generator_module(repo_root)

    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    tests_path = tests_dir / "test_control_identifiers.py"
    tests_path.write_text(
        "\n".join(
            [
                "def test_latitude_width_positive():",
                "    field = 'LATITUDE'",
                "    assert field == 'LATITUDE'",
                "    assert len('+12345') == 6",
                "",
                "def test_report_type_width_positive():",
                "    field = 'REPORT_TYPE'",
                "    assert field == 'REPORT_TYPE'",
                "    assert len('FM-12') == 5",
                "",
            ]
        ),
        encoding="utf-8",
    )

    known_identifiers = {"LATITUDE", "REPORT_TYPE"}
    known_families = {module.identifier_family(value) for value in known_identifiers}
    index = module.parse_tests_evidence(tests_path, known_identifiers, known_families)

    assert ("LATITUDE", "width") in index.exact_assertions
    assert ("REPORT_TYPE", "width") in index.exact_assertions
    assert "width" not in index.wildcard_assertions


def test_parse_tests_evidence_detects_static_short_identifiers_as_exact(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    module = _load_generator_module(repo_root)

    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    tests_path = tests_dir / "test_static_identifiers.py"
    tests_path.write_text(
        "\n".join(
            [
                "def test_cig_width_rejects_bad_token():",
                "    field = 'CIG'",
                "    result = {'CIG__part1': None}",
                "    assert field == 'CIG'",
                "    assert result['CIG__part1'] is None",
                "",
                "def test_tmp_range_rejects_out_of_range_value():",
                "    field = 'TMP'",
                "    result = {'TMP__value': None}",
                "    assert field == 'TMP'",
                "    assert result['TMP__value'] is None",
                "",
            ]
        ),
        encoding="utf-8",
    )

    known_identifiers = {"CIG", "TMP"}
    known_families = {module.identifier_family(value) for value in known_identifiers}
    index = module.parse_tests_evidence(tests_path, known_identifiers, known_families)

    assert ("CIG", "width") in index.exact_assertions
    assert ("TMP", "range") in index.exact_assertions
    assert "width" not in index.wildcard_assertions
    assert "range" not in index.wildcard_assertions


def test_parse_tests_evidence_detects_control_pos_identifiers(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    module = _load_generator_module(repo_root)

    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    tests_path = tests_dir / "test_control_pos_identifiers.py"
    tests_path.write_text(
        "\n".join(
            [
                "def test_control_pos_1_4_width_rejects_bad_token():",
                "    field = 'CONTROL_POS_1_4'",
                "    assert field == 'CONTROL_POS_1_4'",
                "    assert True",
                "",
            ]
        ),
        encoding="utf-8",
    )

    known_identifiers = {"CONTROL_POS_1_4"}
    known_families = {module.identifier_family(value) for value in known_identifiers}
    index = module.parse_tests_evidence(tests_path, known_identifiers, known_families)

    assert ("CONTROL_POS_1_4", "width") in index.exact_assertions


def test_parse_tests_evidence_ignores_unrelated_underscore_tokens(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    module = _load_generator_module(repo_root)

    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    tests_path = tests_dir / "test_unrelated_underscore_tokens.py"
    tests_path.write_text(
        "\n".join(
            [
                "def test_width_rejects_unrelated_underscore_token():",
                "    field = 'FOO_BAR'",
                "    assert field == 'FOO_BAR'",
                "    assert True",
                "",
            ]
        ),
        encoding="utf-8",
    )

    known_identifiers = {"CONTROL_POS_1_4"}
    known_families = {module.identifier_family(value) for value in known_identifiers}
    index = module.parse_tests_evidence(tests_path, known_identifiers, known_families)

    assert ("FOO_BAR", "width") not in index.exact_assertions
    assert all(identifier != "FOO_BAR" for identifier, _rule_type in index.exact_assertions)
    assert "width" in index.wildcard_assertions


def test_parse_tests_evidence_width_signature_matches_control_pos_exactly(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    module = _load_generator_module(repo_root)

    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    tests_path = tests_dir / "test_control_pos_width_signature.py"
    tests_path.write_text(
        "\n".join(
            [
                "def test_control_pos_1_4_token_width_guard():",
                "    field = 'CONTROL_POS_1_4'",
                "    assert True, 'CONTROL_POS_1_4 token width expected 4'",
                "",
            ]
        ),
        encoding="utf-8",
    )

    known_identifiers = {"CONTROL_POS_1_4", "CONTROL_POS_24_27"}
    known_families = {module.identifier_family(value) for value in known_identifiers}
    index = module.parse_tests_evidence(tests_path, known_identifiers, known_families)

    signature_key = ("CONTROL_POS_1_4", "width", "", "", "", "4")
    assert signature_key in index.signature_locations

    # Prove the width signature path itself (not exact_assertion fallback).
    index.exact_assertions.clear()

    target_row = _fixture_row(module, "CONTROL_POS_1_4", "width")
    target_row.allowed_values_or_codes = "4"
    location, strength = index.find(
        target_row.identifier,
        target_row.identifier_family,
        target_row.rule_type,
        target_row.min_value,
        target_row.max_value,
        target_row.sentinel_values,
        target_row.allowed_values_or_codes,
    )
    assert location is not None
    assert strength == "exact_signature"


def test_parse_tests_evidence_width_signature_does_not_cross_identifiers(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    module = _load_generator_module(repo_root)

    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    tests_path = tests_dir / "test_control_pos_width_no_cross_match.py"
    tests_path.write_text(
        "\n".join(
            [
                "def test_control_pos_1_4_width_signature_only():",
                "    assert True, 'CONTROL_POS_1_4 fixed-width 4 token width check'",
                "",
            ]
        ),
        encoding="utf-8",
    )

    known_identifiers = {"CONTROL_POS_1_4", "CONTROL_POS_24_27"}
    known_families = {module.identifier_family(value) for value in known_identifiers}
    index = module.parse_tests_evidence(tests_path, known_identifiers, known_families)

    # Force signature-only matching and verify exact identifier scoping.
    index.exact_assertions.clear()

    other_row = _fixture_row(module, "CONTROL_POS_24_27", "width")
    other_row.allowed_values_or_codes = "4"
    location, strength = index.find(
        other_row.identifier,
        other_row.identifier_family,
        other_row.rule_type,
        other_row.min_value,
        other_row.max_value,
        other_row.sentinel_values,
        other_row.allowed_values_or_codes,
    )
    assert location is None
    assert strength == "none"


def test_augment_known_test_identifiers_includes_spec_only_identifiers() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    module = _load_generator_module(repo_root)

    known_identifiers = {"WND"}
    known_families = {"WND"}

    row_ab1 = _fixture_row(module, "AB1", "width")
    row_unspecified = _fixture_row(module, "UNSPECIFIED", "width")
    row_synthetic = _fixture_row(module, "AB2", "width")
    row_synthetic.row_kind = "synthetic"

    identifiers, families = module.augment_known_test_identifiers(
        known_identifiers,
        known_families,
        [row_ab1, row_unspecified, row_synthetic],
    )

    assert "AB1" in identifiers
    assert "AB" in families
    assert "AB" in identifiers
    assert "UNSPECIFIED" not in identifiers
    assert "AB2" not in identifiers


def test_augmented_identifier_set_enables_exact_test_evidence_for_ab1(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    module = _load_generator_module(repo_root)

    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    tests_path = tests_dir / "test_ab1_width.py"
    tests_path.write_text(
        "\n".join(
            [
                "def test_ab1_width_rejects_bad_part1_token():",
                "    prefix = 'AB1'",
                "    assert prefix == 'AB1'",
                "    assert True",
                "",
            ]
        ),
        encoding="utf-8",
    )

    rows = [_fixture_row(module, "AB1", "width")]
    identifiers, families = module.augment_known_test_identifiers({"WND"}, {"WND"}, rows)
    index = module.parse_tests_evidence(tests_path, identifiers, families)

    assert ("AB1", "width") in index.exact_assertions


def test_spec_coverage_generator_smoke() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    module = _load_generator_module(repo_root)

    module.main()

    csv_path = repo_root / "spec_coverage.csv"
    report_path = repo_root / "docs/internal/reports/SPEC_COVERAGE_REPORT.md"

    assert csv_path.exists(), "spec_coverage.csv should be generated"
    assert report_path.exists(), "docs/internal/reports/SPEC_COVERAGE_REPORT.md should be generated"

    rows = _read_csv_rows(csv_path)

    assert len(rows) > 200, f"Expected >200 spec rows, got {len(rows)}"

    report_text = report_path.read_text(encoding="utf-8")
    assert report_text.startswith("# INTERNAL DEVELOPMENT RECORD — NOT REVIEWER EVIDENCE")
    assert "Overall coverage" in report_text
    assert "Enforcement layer breakdown" in report_text
    assert "Confidence breakdown" in report_text
    assert "Match quality" in report_text
    assert "Suspicious coverage" in report_text
    assert "Precision warnings" in report_text
    assert "Rule Identity & Provenance" in report_text
    assert "Top 50 real gaps (strict)" in report_text
    assert "Implementation gaps (strict): Not implemented + not tested_strict" in report_text
    assert "Missing tests (strict): Implemented + not tested_strict" in report_text
    assert "Wildcard-only coverage (not counted toward progress)" in report_text
    assert "line-only shifts do not churn IDs" in report_text
    assert "Progress KPI (`tested_strict`)" in report_text
    assert "Weak coverage (`tested_any`, includes wildcard)" in report_text
    assert "NOAA_CLEANING_ALIGNMENT_REPORT.md" not in report_text
    assert "docs/internal/archive/NEXT_STEPS.md" not in report_text
    assert "docs/internal/architecture/ARCHITECTURE_NEXT_STEPS.md" not in report_text
    assert "Known-gap traceability" not in report_text

    metric_rows = [
        row
        for row in rows
        if row.get("row_kind") in {"spec_rule", "structural_rule"} and row.get("rule_type") != "unknown"
    ]

    required_columns = {
        "rule_id",
        "row_kind",
        "spec_file",
        "spec_line_start",
        "spec_line_end",
        "spec_evidence",
        "implemented_in_constants",
        "constants_location",
        "implemented_in_cleaning",
        "cleaning_location",
        "implementation_confidence",
        "enforcement_layer",
        "code_implemented",
        "test_covered",
        "test_covered_any",
        "test_covered_strict",
        "test_match_strength",
    }
    missing_columns = required_columns - set(rows[0].keys())
    assert not missing_columns, f"Missing expected CSV columns: {sorted(missing_columns)}"

    assert [row["rule_id"] for row in rows] == [row["rule_id"] for row in sorted(rows, key=_stable_sort_key)]

    synthetic_rows = [row for row in rows if row.get("row_kind") == "synthetic"]
    assert not synthetic_rows, "Synthetic rows should not be emitted"

    for row in rows:
        assert row["rule_id"], "rule_id must be populated"
        assert row["row_kind"] in {"spec_rule", "structural_rule", "documentation_rule"}
        assert row["implemented_in_constants"] in {"TRUE", "FALSE"}
        assert row["implemented_in_cleaning"] in {"TRUE", "FALSE"}
        assert row["implementation_confidence"] in {"high", "medium", "low"}
        assert row["enforcement_layer"] in {"constants_only", "cleaning_only", "both", "neither"}
        assert row["test_covered"] in {"TRUE", "FALSE"}
        assert row["test_covered_any"] in {"TRUE", "FALSE"}
        assert row["test_covered_strict"] in {"TRUE", "FALSE"}
        assert row["test_match_strength"] in {
            "exact_signature",
            "exact_assertion",
            "family_assertion",
            "wildcard_assertion",
            "none",
        }
        assert row["test_covered"] == row["test_covered_any"]
        if row["test_covered_strict"] == "TRUE":
            assert row["test_covered_any"] == "TRUE"
        if row["test_match_strength"] == "wildcard_assertion":
            assert row["test_covered_any"] == "TRUE"
            assert row["test_covered_strict"] == "FALSE"
        if row["test_match_strength"] == "none":
            assert row["test_covered_any"] == "FALSE"
            assert row["test_covered_strict"] == "FALSE"
        assert re.fullmatch(
            r"isd-format-document\.deterministic\.md::[0-9a-f]{12}::.+::[a-z_]+::[0-9a-f]{10}",
            row["rule_id"],
        )
        assert row["spec_file"] == "isd-format-document.deterministic.md"
        assert row["spec_doc"] == "isd-format-document.deterministic.md"
        assert row["spec_line_start"].isdigit()
        assert row["spec_line_end"].isdigit()

        expected_implemented = (
            row["implemented_in_constants"] == "TRUE" or row["implemented_in_cleaning"] == "TRUE"
        )
        assert row["code_implemented"] == ("TRUE" if expected_implemented else "FALSE")

        if row["enforcement_layer"] == "constants_only":
            assert row["implemented_in_constants"] == "TRUE"
            assert row["implemented_in_cleaning"] == "FALSE"
        elif row["enforcement_layer"] == "cleaning_only":
            assert row["implemented_in_constants"] == "FALSE"
            assert row["implemented_in_cleaning"] == "TRUE"
        elif row["enforcement_layer"] == "both":
            assert row["implemented_in_constants"] == "TRUE"
            assert row["implemented_in_cleaning"] == "TRUE"
        else:
            assert row["implemented_in_constants"] == "FALSE"
            assert row["implemented_in_cleaning"] == "FALSE"

    range_rows = [row for row in metric_rows if row.get("rule_type") == "range"]
    assert range_rows, "Expected at least one range rule row"
    range_tested_count = sum(1 for row in range_rows if row.get("test_covered_strict") == "TRUE")
    range_tested_pct = (100.0 * range_tested_count / len(range_rows)) if range_rows else 0.0
    if range_tested_pct >= 99.5:
        assert all(
            row.get("test_match_strength") in {"exact_signature", "exact_assertion", "family_assertion"}
            for row in range_rows
            if row.get("test_covered_strict") == "TRUE"
        ), "High range coverage must come from strict exact/family evidence, not wildcard matches"

    arity_rows = [row for row in metric_rows if row.get("rule_type") == "arity"]
    arity_tested_any_count = sum(1 for row in arity_rows if row.get("test_covered_any") == "TRUE")
    arity_tested_strict_count = sum(1 for row in arity_rows if row.get("test_covered_strict") == "TRUE")
    tests_cleaning_text = (repo_root / "tests" / "test_cleaning.py").read_text(encoding="utf-8")
    arity_tests_detected = bool(
        re.search(r"\barity\b", tests_cleaning_text, re.IGNORECASE)
        or re.search(r"truncated payload", tests_cleaning_text, re.IGNORECASE)
        or re.search(r"expected\s+\d+\s+parts", tests_cleaning_text, re.IGNORECASE)
    )
    if arity_tests_detected:
        assert arity_rows, "Arity tests detected in tests/test_cleaning.py but no arity rows were extracted"
        assert arity_tested_any_count > 0, "Arity tests are present but arity tested-any coverage is 0"
        assert arity_tested_strict_count <= arity_tested_any_count
    else:
        assert (
            "Arity tests not detected; arity tested% may be 0." in report_text
        ), "Report should explicitly explain why arity tested% may be 0 when no arity tests are detected"

    cleaning_only_rows = [
        row
        for row in metric_rows
        if row.get("implemented_in_constants") == "FALSE"
        and row.get("implemented_in_cleaning") == "TRUE"
        and row.get("enforcement_layer") == "cleaning_only"
    ]
    assert cleaning_only_rows, "Expected at least one cleaning-only implemented rule"

    known_cleaning_only = [
        row
        for row in cleaning_only_rows
        if row.get("row_kind") == "spec_rule"
        and row.get("rule_type") == "domain"
        and row.get("implementation_confidence") in {"high", "medium"}
        and "src/noaa_spec/cleaning.py:" in (row.get("cleaning_location") or "")
    ]
    assert known_cleaning_only, "Expected at least one spec-derived domain rule to be cleaning-only with medium/high confidence"

    neither_rows = [
        row
        for row in metric_rows
        if row.get("implemented_in_constants") == "FALSE"
        and row.get("implemented_in_cleaning") == "FALSE"
        and row.get("enforcement_layer") == "neither"
    ]
    if neither_rows:
        assert any(
            row.get("test_covered_strict") == "FALSE"
            for row in neither_rows
        ), "Unimplemented rules should not be marked tested_strict"

    implemented_rows = [row for row in metric_rows if row.get("code_implemented") == "TRUE"]
    cleaning_only_share = (len(cleaning_only_rows) / len(implemented_rows)) if implemented_rows else 0.0
    assert (
        cleaning_only_share <= 0.5
    ), f"Cleaning-only implementation share too high ({cleaning_only_share:.2%}); likely overmatching"

    total_match = re.search(r"Total spec rules extracted: \*\*(\d+)\*\*", report_text)
    assert total_match, "Expected total extracted rule count in report"
    report_total = int(total_match.group(1))
    expected_total = sum(
        1 for row in rows if row.get("row_kind") in {"spec_rule", "structural_rule", "documentation_rule"}
    )
    assert report_total == expected_total, "Synthetic rows must be excluded from total spec rule metrics"

    metric_match = re.search(r"Metric-eligible rules \(excluding `unknown`\): \*\*(\d+)\*\*", report_text)
    assert metric_match, "Expected metric-eligible count in report"
    report_metric_total = int(metric_match.group(1))
    expected_metric_total = sum(
        1
        for row in rows
        if row.get("row_kind") in {"spec_rule", "structural_rule"} and row.get("rule_type") != "unknown"
    )
    assert report_metric_total == expected_metric_total, "Documentation rows must be excluded from metric denominator"

    first_run_rule_ids = [row["rule_id"] for row in rows]
    module.main()
    second_run_rule_ids = [row["rule_id"] for row in _read_csv_rows(csv_path)]
    assert first_run_rule_ids == second_run_rule_ids, "rule_id sequence should be stable across runs"
