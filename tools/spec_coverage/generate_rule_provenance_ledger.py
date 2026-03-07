#!/usr/bin/env python3
"""Generate rule provenance ledger artifacts from enforced repository behavior.

Outputs:
- RULE_PROVENANCE_LEDGER.csv
- RULE_PROVENANCE_LEDGER.md

This script is deterministic and uses local repository files only.
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import importlib
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

CSV_COLUMNS = [
    "rule_id",
    "field_identifier",
    "rule_type",
    "rule_description",
    "enforcement_location",
    "enforcement_function",
    "code_reference",
    "source_class",
    "source_reference",
    "doc_support_status",
    "strictness_vs_doc",
    "behavior_on_violation",
    "output_effect",
    "matched_spec_rule_id",
    "keep_decision",
    "rationale",
    "review_status",
]

RULE_TYPE_VALUES = {
    "range",
    "sentinel",
    "domain",
    "allowed_quality",
    "width",
    "arity",
    "structural_guard",
    "null_semantics",
    "normalization",
    "exclusion",
    "other",
}

SOURCE_CLASS_VALUES = {
    "documented_exact",
    "documented_inferred",
    "implementation_only",
    "legacy_behavior",
    "defensive_sanity_check",
}

DOC_SUPPORT_VALUES = {"supported_exact", "supported_partial", "unsupported", "unknown"}
STRICTNESS_VALUES = {"equal", "looser", "stricter", "not_comparable"}
VIOLATION_VALUES = {"null", "exclude", "flag", "raise", "coerce", "ignore", "mixed"}
REVIEW_VALUES = {"auto_classified", "needs_manual_review"}

IDENT_WITH_DIGITS_RE = re.compile(r"^([A-Z_]+?)(\d+)$")
POS_RANGE_RE = re.compile(r"\bPOS\s*:?\s*(\d+)\s*-\s*(\d+)\b", re.IGNORECASE)
FLD_LEN_RE = re.compile(r"\bFLD\s+LEN\s*:\s*(\d+)\b", re.IGNORECASE)


@dataclass(slots=True)
class ConstantsAstIndex:
    field_rule_lines: dict[str, int] = field(default_factory=dict)
    part_lines: dict[tuple[str, int], int] = field(default_factory=dict)
    part_keyword_lines: dict[tuple[str, int, str], int] = field(default_factory=dict)


@dataclass(slots=True)
class SpecRule:
    rule_id: str
    identifier: str
    identifier_family: str
    rule_type: str
    min_value: float | None
    max_value: float | None
    sentinels: set[str]
    allowed_values: set[str]
    token_width: int | None
    expected_parts: int | None


@dataclass(slots=True)
class CodeRule:
    field_identifier: str
    rule_type: str
    rule_description: str
    enforcement_location: str
    enforcement_function: str
    code_reference: str
    behavior_on_violation: str
    output_effect: str
    source_reference: str
    source_class_hint: str | None = None
    doc_support_hint: str | None = None
    strictness_hint: str | None = None
    review_hint: str | None = None
    keep_decision: str = ""
    rationale_hint: str = ""
    match_identifier: str | None = None
    match_rule_type: str | None = None
    min_value: float | None = None
    max_value: float | None = None
    sentinel_values: set[str] = field(default_factory=set)
    allowed_values: set[str] = field(default_factory=set)
    token_width: int | None = None
    expected_parts: int | None = None
    quality_codes: set[str] = field(default_factory=set)


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def short_sha1(text: str, length: int = 12) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:length]


def normalize_identifier_family(identifier: str) -> str:
    if identifier.startswith("CONTROL_POS_"):
        return "CONTROL"
    m = IDENT_WITH_DIGITS_RE.match(identifier)
    if m:
        return m.group(1)
    return identifier


def parse_num_token(token: str) -> float | None:
    text = token.strip()
    if not text:
        return None
    if text.startswith("+"):
        text = text[1:]
    if re.fullmatch(r"[+-]?\d+", text):
        try:
            return float(int(text))
        except ValueError:
            return None
    if re.fullmatch(r"[+-]?\d+\.\d+", text):
        try:
            return float(text)
        except ValueError:
            return None
    return None


def parse_pipe_tokens(value: str) -> set[str]:
    if not value:
        return set()
    return {token.strip() for token in value.split("|") if token.strip()}


def parse_expected_parts(value: str) -> int | None:
    if not value:
        return None
    if value.isdigit():
        return int(value)
    return None


def parse_token_width(spec_rule_text: str, allowed_value: str) -> int | None:
    if allowed_value.isdigit():
        return int(allowed_value)
    pos = POS_RANGE_RE.search(spec_rule_text)
    if pos:
        start = int(pos.group(1))
        end = int(pos.group(2))
        return abs(end - start) + 1
    fld = FLD_LEN_RE.search(spec_rule_text)
    if fld:
        return int(fld.group(1))
    return None


def ast_literal_str(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def ast_literal_int(node: ast.AST | None) -> int | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, int):
        return node.value
    return None


def parse_constants_ast(constants_path: Path) -> ConstantsAstIndex:
    source = constants_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(constants_path))
    index = ConstantsAstIndex()

    def parse_field_rules_dict(node: ast.Dict) -> None:
        for key_node, value_node in zip(node.keys, node.values):
            key_value = ast_literal_str(key_node)
            if not key_value:
                continue
            index.field_rule_lines.setdefault(key_value, getattr(key_node, "lineno", value_node.lineno))
            if not isinstance(value_node, ast.Call):
                continue
            if getattr(value_node.func, "id", "") != "FieldRule":
                continue
            parts_dict = None
            for kw in value_node.keywords:
                if kw.arg == "parts" and isinstance(kw.value, ast.Dict):
                    parts_dict = kw.value
                    break
            if parts_dict is None:
                continue
            for part_key_node, part_value_node in zip(parts_dict.keys, parts_dict.values):
                part_idx = ast_literal_int(part_key_node)
                if part_idx is None or not isinstance(part_value_node, ast.Call):
                    continue
                if getattr(part_value_node.func, "id", "") != "FieldPartRule":
                    continue
                index.part_lines[(key_value, part_idx)] = part_value_node.lineno
                for kw in part_value_node.keywords:
                    if kw.arg in {
                        "min_value",
                        "max_value",
                        "missing_values",
                        "allowed_values",
                        "allowed_quality",
                        "allowed_pattern",
                        "token_width",
                        "token_pattern",
                        "scale",
                    }:
                        index.part_keyword_lines[(key_value, part_idx, kw.arg)] = kw.value.lineno

    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id in {"FIELD_RULES", "FIELD_RULE_PREFIXES"} and isinstance(node.value, ast.Dict):
                parse_field_rules_dict(node.value)
        if isinstance(node, ast.Assign):
            targets = [target.id for target in node.targets if isinstance(target, ast.Name)]
            if "FIELD_RULES" in targets and isinstance(node.value, ast.Dict):
                parse_field_rules_dict(node.value)
            if "FIELD_RULE_PREFIXES" in targets and isinstance(node.value, ast.Dict):
                parse_field_rules_dict(node.value)
    return index


def load_constants_module(repo_root: Path):
    src = str(repo_root / "src")
    if src not in sys.path:
        sys.path.insert(0, src)
    return importlib.import_module("noaa_climate_data.constants")


def first_line_containing(path: Path, pattern: str) -> int | None:
    for idx, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if pattern in line:
            return idx
    return None


def build_code_reference(path: str, line: int | None, symbol: str) -> str:
    if line is None:
        return f"{symbol}"
    return f"{path}:{line}::{symbol}"


def rule_payload(rule: CodeRule) -> dict[str, Any]:
    return {
        "field_identifier": rule.field_identifier,
        "rule_type": rule.rule_type,
        "match_identifier": rule.match_identifier,
        "match_rule_type": rule.match_rule_type,
        "min_value": rule.min_value,
        "max_value": rule.max_value,
        "sentinel_values": sorted(rule.sentinel_values),
        "allowed_values": sorted(rule.allowed_values),
        "quality_codes": sorted(rule.quality_codes),
        "token_width": rule.token_width,
        "expected_parts": rule.expected_parts,
        "enforcement_location": rule.enforcement_location,
        "code_reference": rule.code_reference,
        "behavior_on_violation": rule.behavior_on_violation,
    }


def build_rule_id(rule: CodeRule) -> str:
    payload = canonical_json(rule_payload(rule))
    prefix = rule.field_identifier.replace(" ", "_")
    return f"RPL::{prefix}::{rule.rule_type}::{short_sha1(payload, 14)}"


def load_spec_rules(spec_coverage_csv: Path) -> list[SpecRule]:
    rules: list[SpecRule] = []
    with spec_coverage_csv.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            identifier = row["identifier"].strip().upper()
            rule_type = row["rule_type"].strip().lower()
            if rule_type not in {"range", "sentinel", "domain", "allowed_quality", "width", "arity"}:
                continue
            min_value = parse_num_token(row["min_value"])
            max_value = parse_num_token(row["max_value"])
            sentinels = parse_pipe_tokens(row["sentinel_values"])
            allowed = parse_pipe_tokens(row["allowed_values_or_codes"])
            width = parse_token_width(row["spec_rule_text"], row["allowed_values_or_codes"].strip())
            expected_parts = parse_expected_parts(row["allowed_values_or_codes"].strip()) if rule_type == "arity" else None
            rules.append(
                SpecRule(
                    rule_id=row["rule_id"],
                    identifier=identifier,
                    identifier_family=row["identifier_family"].strip().upper() or normalize_identifier_family(identifier),
                    rule_type=rule_type,
                    min_value=min_value,
                    max_value=max_value,
                    sentinels=sentinels,
                    allowed_values=allowed,
                    token_width=width,
                    expected_parts=expected_parts,
                )
            )
    return rules


def supported_rule_type(code_rule_type: str) -> bool:
    return code_rule_type in {"range", "sentinel", "domain", "allowed_quality", "width", "arity"}


def compatible_spec_types(code_type: str) -> tuple[str, ...]:
    if code_type == "allowed_quality":
        return ("allowed_quality", "domain")
    if code_type == "domain":
        return ("domain", "allowed_quality")
    if code_type in {"range", "sentinel", "width", "arity"}:
        return (code_type,)
    return ()


def set_strictness(code_set: set[str], spec_set: set[str]) -> tuple[str, float, bool]:
    if not code_set or not spec_set:
        return "not_comparable", 0.0, False
    if code_set == spec_set:
        return "equal", 1.0, True
    intersection = code_set & spec_set
    union = code_set | spec_set
    ratio = len(intersection) / len(union) if union else 0.0
    if not intersection:
        return "not_comparable", 0.0, False
    if code_set < spec_set:
        return "stricter", ratio, False
    if code_set > spec_set:
        return "looser", ratio, False
    return "not_comparable", ratio, False


def range_strictness(
    code_min: float | None,
    code_max: float | None,
    spec_min: float | None,
    spec_max: float | None,
) -> tuple[str, float, bool]:
    if code_min is None and code_max is None:
        return "not_comparable", 0.0, False
    if spec_min is None and spec_max is None:
        return "not_comparable", 0.0, False

    min_score = 0.0
    max_score = 0.0
    if code_min is not None and spec_min is not None:
        min_score = 1.0 if code_min == spec_min else 0.5
    if code_max is not None and spec_max is not None:
        max_score = 1.0 if code_max == spec_max else 0.5
    payload_score = (min_score + max_score) / 2.0
    is_exact = (code_min == spec_min) and (code_max == spec_max)

    if code_min is None or code_max is None or spec_min is None or spec_max is None:
        return "not_comparable", payload_score, is_exact
    if is_exact:
        return "equal", payload_score, True
    if code_min >= spec_min and code_max <= spec_max:
        return "stricter", payload_score, False
    if code_min <= spec_min and code_max >= spec_max:
        return "looser", payload_score, False
    return "not_comparable", payload_score, False


def width_strictness(code_width: int | None, spec_width: int | None) -> tuple[str, float, bool]:
    if code_width is None or spec_width is None:
        return "not_comparable", 0.0, False
    if code_width == spec_width:
        return "equal", 1.0, True
    return "not_comparable", 0.0, False


def arity_strictness(code_parts: int | None, spec_parts: int | None) -> tuple[str, float, bool]:
    if code_parts is None or spec_parts is None:
        return "not_comparable", 0.0, False
    if code_parts == spec_parts:
        return "equal", 1.0, True
    if code_parts < spec_parts:
        return "stricter", 0.25, False
    return "looser", 0.25, False


def match_code_rule(
    rule: CodeRule,
    spec_rules_by_identifier: dict[tuple[str, str], list[SpecRule]],
    spec_rules_by_family: dict[tuple[str, str], list[SpecRule]],
) -> tuple[SpecRule | None, str, float, bool]:
    identifier = (rule.match_identifier or rule.field_identifier).upper()
    family = normalize_identifier_family(identifier)
    match_type = (rule.match_rule_type or rule.rule_type).lower()
    if not supported_rule_type(match_type):
        return None, "not_comparable", 0.0, False

    candidates: list[tuple[SpecRule, float, str, bool]] = []
    for candidate_type in compatible_spec_types(match_type):
        id_candidates = spec_rules_by_identifier.get((identifier, candidate_type), [])
        fam_candidates = spec_rules_by_family.get((family, candidate_type), [])
        for spec in id_candidates:
            strictness, payload_score, exact_payload = compare_payload(rule, spec, match_type)
            score = 2.0 + 1.0 + payload_score
            candidates.append((spec, score, strictness, exact_payload))
        for spec in fam_candidates:
            if spec.identifier == identifier:
                continue
            strictness, payload_score, exact_payload = compare_payload(rule, spec, match_type)
            score = 1.0 + 1.0 + payload_score
            candidates.append((spec, score, strictness, exact_payload))

    if not candidates:
        return None, "not_comparable", 0.0, False

    candidates.sort(key=lambda item: (item[1], item[3], item[0].rule_id), reverse=True)
    best_spec, best_score, best_strictness, best_exact = candidates[0]
    ambiguous = len(candidates) > 1 and abs(candidates[0][1] - candidates[1][1]) < 0.05
    if best_score < 2.25:
        return None, "not_comparable", 0.0, False
    return best_spec, best_strictness, best_score, ambiguous


def compare_payload(rule: CodeRule, spec: SpecRule, match_type: str) -> tuple[str, float, bool]:
    if match_type == "range":
        return range_strictness(rule.min_value, rule.max_value, spec.min_value, spec.max_value)
    if match_type == "sentinel":
        return set_strictness(rule.sentinel_values, spec.sentinels)
    if match_type == "domain":
        if rule.allowed_values:
            return set_strictness(rule.allowed_values, spec.allowed_values)
        return "not_comparable", 0.0, False
    if match_type == "allowed_quality":
        if rule.quality_codes:
            return set_strictness(rule.quality_codes, spec.allowed_values)
        if rule.allowed_values:
            return set_strictness(rule.allowed_values, spec.allowed_values)
        return "not_comparable", 0.0, False
    if match_type == "width":
        return width_strictness(rule.token_width, spec.token_width)
    if match_type == "arity":
        return arity_strictness(rule.expected_parts, spec.expected_parts)
    return "not_comparable", 0.0, False


def resolve_field_rule_symbol(constants_module, identifier: str) -> tuple[str, str]:
    alias_map: dict[str, str] = getattr(constants_module, "_IDENTIFIER_ALIASES", {})
    canonical = alias_map.get(identifier, identifier)
    if canonical in constants_module.FIELD_RULES:
        return "FIELD_RULES", canonical

    best = ""
    for key in constants_module.FIELD_RULE_PREFIXES.keys():
        if canonical.startswith(key) and len(key) > len(best):
            best = key
    if best:
        return "FIELD_RULE_PREFIXES", best
    return "FIELD_RULES", canonical


def part_value_quality_mode(rule) -> bool:
    if len(rule.parts) != 1:
        return False
    part_rule = rule.parts.get(1)
    if part_rule is None:
        return False
    return part_rule.quality_part is not None


def build_constants_rules(constants_module, constants_index: ConstantsAstIndex) -> list[CodeRule]:
    alias_map: dict[str, str] = getattr(constants_module, "_IDENTIFIER_ALIASES", {})
    identifiers = sorted(
        identifier
        for identifier in constants_module.KNOWN_IDENTIFIERS
        if constants_module.is_valid_identifier(identifier) and identifier not in alias_map
    )

    rules: list[CodeRule] = []
    for identifier in identifiers:
        rule = constants_module.get_field_rule(identifier)
        if rule is None:
            continue
        symbol_scope, symbol_key = resolve_field_rule_symbol(constants_module, identifier)
        rule_line = constants_index.field_rule_lines.get(symbol_key)
        enforcement_function = "clean_value_quality" if part_value_quality_mode(rule) else "_expand_parsed"

        arity_reference = build_code_reference(
            "src/noaa_climate_data/cleaning.py",
            744,
            f"get_expected_part_count({identifier})",
        )
        rules.append(
            CodeRule(
                field_identifier=identifier,
                rule_type="arity",
                rule_description=f"{identifier} requires {len(rule.parts)} parsed part(s) in strict mode.",
                enforcement_location="src/noaa_climate_data/cleaning.py",
                enforcement_function="clean_value_quality",
                code_reference=arity_reference,
                behavior_on_violation="exclude",
                output_effect="Payload expansion returns empty object for arity mismatch in strict mode.",
                source_reference=f"{symbol_scope}.{symbol_key}",
                match_identifier=identifier,
                match_rule_type="arity",
                expected_parts=len(rule.parts),
            )
        )

        for part_idx, part_rule in sorted(rule.parts.items()):
            part_symbol = f"{symbol_scope}['{symbol_key}'].parts[{part_idx}]"
            part_line = constants_index.part_lines.get((symbol_key, part_idx), rule_line)

            if part_rule.min_value is not None or part_rule.max_value is not None:
                keyword_line = constants_index.part_keyword_lines.get((symbol_key, part_idx, "min_value")) or constants_index.part_keyword_lines.get((symbol_key, part_idx, "max_value")) or part_line
                rules.append(
                    CodeRule(
                        field_identifier=identifier,
                        rule_type="range",
                        rule_description=(
                            f"{identifier} part {part_idx} numeric bounds: "
                            f"min={part_rule.min_value}, max={part_rule.max_value}."
                        ),
                        enforcement_location="src/noaa_climate_data/cleaning.py",
                        enforcement_function=enforcement_function,
                        code_reference=build_code_reference(
                            "src/noaa_climate_data/constants.py",
                            keyword_line,
                            f"{part_symbol}.min_value/max_value",
                        ),
                        behavior_on_violation="null",
                        output_effect="Out-of-range values are nullified and QC reason marks OUT_OF_RANGE.",
                        source_reference=f"{symbol_scope}.{symbol_key}",
                        match_identifier=identifier,
                        match_rule_type="range",
                        min_value=part_rule.min_value,
                        max_value=part_rule.max_value,
                    )
                )

            if part_rule.missing_values and part_rule.missing_values != {"__none__"}:
                keyword_line = constants_index.part_keyword_lines.get((symbol_key, part_idx, "missing_values")) or part_line
                sentinel_values = {str(token) for token in part_rule.missing_values if str(token) != "__none__"}
                rules.append(
                    CodeRule(
                        field_identifier=identifier,
                        rule_type="sentinel",
                        rule_description=f"{identifier} part {part_idx} sentinel tokens treated as missing.",
                        enforcement_location="src/noaa_climate_data/cleaning.py",
                        enforcement_function=enforcement_function,
                        code_reference=build_code_reference(
                            "src/noaa_climate_data/constants.py",
                            keyword_line,
                            f"{part_symbol}.missing_values",
                        ),
                        behavior_on_violation="null",
                        output_effect="Sentinel tokens map to null and QC status may become MISSING.",
                        source_reference=f"{symbol_scope}.{symbol_key}",
                        match_identifier=identifier,
                        match_rule_type="sentinel",
                        sentinel_values=sentinel_values,
                    )
                )

            if part_rule.allowed_values:
                keyword_line = constants_index.part_keyword_lines.get((symbol_key, part_idx, "allowed_values")) or part_line
                rules.append(
                    CodeRule(
                        field_identifier=identifier,
                        rule_type="domain",
                        rule_description=f"{identifier} part {part_idx} allowed domain values are enumerated.",
                        enforcement_location="src/noaa_climate_data/cleaning.py",
                        enforcement_function=enforcement_function,
                        code_reference=build_code_reference(
                            "src/noaa_climate_data/constants.py",
                            keyword_line,
                            f"{part_symbol}.allowed_values",
                        ),
                        behavior_on_violation="null",
                        output_effect="Tokens outside allowed domain are nullified.",
                        source_reference=f"{symbol_scope}.{symbol_key}",
                        match_identifier=identifier,
                        match_rule_type="domain",
                        allowed_values={str(token) for token in part_rule.allowed_values},
                    )
                )

            if part_rule.allowed_pattern is not None:
                keyword_line = constants_index.part_keyword_lines.get((symbol_key, part_idx, "allowed_pattern")) or part_line
                rules.append(
                    CodeRule(
                        field_identifier=identifier,
                        rule_type="domain",
                        rule_description=f"{identifier} part {part_idx} must satisfy regex domain pattern.",
                        enforcement_location="src/noaa_climate_data/cleaning.py",
                        enforcement_function=enforcement_function,
                        code_reference=build_code_reference(
                            "src/noaa_climate_data/constants.py",
                            keyword_line,
                            f"{part_symbol}.allowed_pattern",
                        ),
                        behavior_on_violation="null",
                        output_effect="Pattern mismatch values are nullified.",
                        source_reference=f"{symbol_scope}.{symbol_key}",
                        match_identifier=identifier,
                        match_rule_type="domain",
                        allowed_values={str(part_rule.allowed_pattern.pattern)},
                    )
                )

            if part_rule.allowed_quality:
                keyword_line = constants_index.part_keyword_lines.get((symbol_key, part_idx, "allowed_quality")) or part_line
                rules.append(
                    CodeRule(
                        field_identifier=identifier,
                        rule_type="allowed_quality",
                        rule_description=f"{identifier} part {part_idx} quality codes constrained to allowed set.",
                        enforcement_location="src/noaa_climate_data/cleaning.py",
                        enforcement_function=enforcement_function,
                        code_reference=build_code_reference(
                            "src/noaa_climate_data/constants.py",
                            keyword_line,
                            f"{part_symbol}.allowed_quality",
                        ),
                        behavior_on_violation="null",
                        output_effect="Invalid quality flags nullify governed value and QC reason is BAD_QUALITY_CODE.",
                        source_reference=f"{symbol_scope}.{symbol_key}",
                        match_identifier=identifier,
                        match_rule_type="allowed_quality",
                        quality_codes={str(token) for token in part_rule.allowed_quality},
                    )
                )

            if part_rule.token_width is not None or part_rule.token_pattern is not None:
                keyword_line = (
                    constants_index.part_keyword_lines.get((symbol_key, part_idx, "token_width"))
                    or constants_index.part_keyword_lines.get((symbol_key, part_idx, "token_pattern"))
                    or part_line
                )
                desc = f"{identifier} part {part_idx} fixed token format is validated"
                if part_rule.token_width is not None:
                    desc += f" (width={part_rule.token_width})"
                desc += "."
                rules.append(
                    CodeRule(
                        field_identifier=identifier,
                        rule_type="width",
                        rule_description=desc,
                        enforcement_location="src/noaa_climate_data/cleaning.py",
                        enforcement_function=enforcement_function,
                        code_reference=build_code_reference(
                            "src/noaa_climate_data/constants.py",
                            keyword_line,
                            f"{part_symbol}.token_width/token_pattern",
                        ),
                        behavior_on_violation="null",
                        output_effect="Malformed token is nullified and QC reason is MALFORMED_TOKEN.",
                        source_reference=f"{symbol_scope}.{symbol_key}",
                        match_identifier=identifier,
                        match_rule_type="width",
                        token_width=part_rule.token_width,
                    )
                )

            if part_rule.scale is not None and part_rule.scale != 1:
                keyword_line = constants_index.part_keyword_lines.get((symbol_key, part_idx, "scale")) or part_line
                rules.append(
                    CodeRule(
                        field_identifier=identifier,
                        rule_type="normalization",
                        rule_description=f"{identifier} part {part_idx} numeric value is scaled by factor {part_rule.scale}.",
                        enforcement_location="src/noaa_climate_data/cleaning.py",
                        enforcement_function=enforcement_function,
                        code_reference=build_code_reference(
                            "src/noaa_climate_data/constants.py",
                            keyword_line,
                            f"{part_symbol}.scale",
                        ),
                        behavior_on_violation="coerce",
                        output_effect="Parsed numeric value is deterministically transformed by scale factor.",
                        source_reference=f"{symbol_scope}.{symbol_key}",
                        source_class_hint="documented_inferred",
                        doc_support_hint="unknown",
                        strictness_hint="not_comparable",
                        review_hint="needs_manual_review",
                    )
                )

    # Legacy identifier aliases are enforced via normalization before lookup.
    alias_line = first_line_containing(Path("src/noaa_climate_data/constants.py"), "_IDENTIFIER_ALIASES")
    if alias_line:
        alias_map = getattr(constants_module, "_IDENTIFIER_ALIASES", {})
        for alias, canonical in sorted(alias_map.items()):
            rules.append(
                CodeRule(
                    field_identifier=alias,
                    rule_type="normalization",
                    rule_description=f"Identifier alias {alias} normalizes to canonical identifier {canonical}.",
                    enforcement_location="src/noaa_climate_data/constants.py",
                    enforcement_function="get_field_rule",
                    code_reference=build_code_reference(
                        "src/noaa_climate_data/constants.py",
                        alias_line,
                        "_IDENTIFIER_ALIASES",
                    ),
                    behavior_on_violation="coerce",
                    output_effect="Alias tokens are interpreted as canonical identifiers before rule lookup.",
                    source_reference="legacy_alias_map",
                    source_class_hint="legacy_behavior",
                    doc_support_hint="unknown",
                    strictness_hint="not_comparable",
                    review_hint="needs_manual_review",
                )
            )

    return rules


def build_custom_cleaning_rules(cleaning_path: Path) -> list[CodeRule]:
    rules: list[CodeRule] = []
    cpath = "src/noaa_climate_data/cleaning.py"

    def line(token: str) -> int | None:
        return first_line_containing(cleaning_path, token)

    rules.extend(
        [
            CodeRule(
                field_identifier="GLOBAL",
                rule_type="structural_guard",
                rule_description="Strict mode skips expansion for malformed section identifier tokens.",
                enforcement_location=cpath,
                enforcement_function="clean_noaa_dataframe",
                code_reference=build_code_reference(cpath, line("section_identifier_valid = is_valid_section_identifier_token(column)"), "is_valid_section_identifier_token(column)"),
                behavior_on_violation="ignore",
                output_effect="Malformed identifier columns remain raw and are not expanded.",
                source_reference="A1_strict_identifier_gate",
                source_class_hint="defensive_sanity_check",
                doc_support_hint="unknown",
                strictness_hint="not_comparable",
                review_hint="auto_classified",
                rationale_hint="Guarded by strict parsing tests for malformed identifiers.",
            ),
            CodeRule(
                field_identifier="GLOBAL",
                rule_type="exclusion",
                rule_description="Strict mode skips expansion for unknown identifiers outside allowlist/valid families.",
                enforcement_location=cpath,
                enforcement_function="clean_noaa_dataframe",
                code_reference=build_code_reference(cpath, line("known_identifier = ("), "known_identifier allowlist gate"),
                behavior_on_violation="ignore",
                output_effect="Unknown data sections are preserved as raw columns and excluded from parsed outputs.",
                source_reference="A1_known_identifier_gate",
                source_class_hint="defensive_sanity_check",
                doc_support_hint="unknown",
                strictness_hint="not_comparable",
                review_hint="auto_classified",
            ),
            CodeRule(
                field_identifier="GLOBAL",
                rule_type="null_semantics",
                rule_description="Fallback missing heuristic: unsigned all-9 numeric tokens of length >=2 are treated as missing when no field rule exists.",
                enforcement_location=cpath,
                enforcement_function="_is_missing_numeric",
                code_reference=build_code_reference(cpath, line("def _is_missing_numeric"), "_is_missing_numeric"),
                behavior_on_violation="null",
                output_effect="Unruled numeric all-9 tokens are coerced to null during parsing.",
                source_reference="fallback_missing_numeric_heuristic",
                source_class_hint="legacy_behavior",
                doc_support_hint="unknown",
                strictness_hint="not_comparable",
                review_hint="needs_manual_review",
            ),
            CodeRule(
                field_identifier="GLOBAL",
                rule_type="normalization",
                rule_description="Missing token normalization strips leading plus signs and redundant leading zeros before sentinel comparison.",
                enforcement_location=cpath,
                enforcement_function="_normalize_missing",
                code_reference=build_code_reference(cpath, line("def _normalize_missing"), "_normalize_missing"),
                behavior_on_violation="coerce",
                output_effect="Sentinel matching is canonicalized across formatting variants.",
                source_reference="sentinel_normalization_precheck",
                source_class_hint="defensive_sanity_check",
                doc_support_hint="unknown",
                strictness_hint="not_comparable",
                review_hint="auto_classified",
            ),
            CodeRule(
                field_identifier="WND",
                rule_type="null_semantics",
                rule_description="WND variable direction special case: direction token 999 with type code V is interpreted as variable and direction is null.",
                enforcement_location=cpath,
                enforcement_function="_expand_parsed",
                code_reference=build_code_reference(cpath, line("is_variable_direction = ("), "is_variable_direction"),
                behavior_on_violation="coerce",
                output_effect="Direction value nulls and `WND__direction_variable` is set True.",
                source_reference="WND variable direction interpretation",
                source_class_hint="documented_inferred",
                doc_support_hint="supported_partial",
                strictness_hint="not_comparable",
                review_hint="needs_manual_review",
            ),
            CodeRule(
                field_identifier="WND",
                rule_type="normalization",
                rule_description="WND calm condition is detected and surfaced as an explicit QC flag while preserving the original type token.",
                enforcement_location=cpath,
                enforcement_function="_expand_parsed",
                code_reference=build_code_reference(cpath, line("is_wnd_calm = ("), "is_wnd_calm"),
                behavior_on_violation="flag",
                output_effect="Calm wind condition sets QC flag and preserves original type code token.",
                source_reference="WND calm condition flagging",
                source_class_hint="implementation_only",
                doc_support_hint="unknown",
                strictness_hint="not_comparable",
                review_hint="needs_manual_review",
            ),
            CodeRule(
                field_identifier="OD",
                rule_type="normalization",
                rule_description="OD calm condition is detected and surfaced as QC evidence while preserving the original direction token.",
                enforcement_location=cpath,
                enforcement_function="_expand_parsed",
                code_reference=build_code_reference(cpath, line("is_od_calm = ("), "is_od_calm"),
                behavior_on_violation="flag",
                output_effect="Supplementary-wind calm condition sets QC flag and preserves direction token.",
                source_reference="OD calm condition flagging",
                source_class_hint="implementation_only",
                doc_support_hint="unknown",
                strictness_hint="not_comparable",
                review_hint="needs_manual_review",
            ),
            CodeRule(
                field_identifier="OE",
                rule_type="normalization",
                rule_description="OE calm condition is detected and surfaced as QC evidence while preserving the original speed token.",
                enforcement_location=cpath,
                enforcement_function="_expand_parsed",
                code_reference=build_code_reference(cpath, line("is_oe_calm = ("), "is_oe_calm"),
                behavior_on_violation="flag",
                output_effect="Summary-wind calm condition sets QC flag and preserves speed token.",
                source_reference="OE calm condition flagging",
                source_class_hint="implementation_only",
                doc_support_hint="unknown",
                strictness_hint="not_comparable",
                review_hint="needs_manual_review",
            ),
            CodeRule(
                field_identifier="CIG",
                rule_type="normalization",
                rule_description="CIG ceiling height is clipped to 22000.0 instead of nulling when above the cap.",
                enforcement_location=cpath,
                enforcement_function="_expand_parsed",
                code_reference=build_code_reference(cpath, line('if prefix == "CIG" and idx == 1'), "CIG clamp"),
                behavior_on_violation="coerce",
                output_effect="Above-cap values are clamped to the cap and retained.",
                source_reference="CIG clamp behavior",
                source_class_hint="implementation_only",
                doc_support_hint="supported_partial",
                strictness_hint="looser",
                review_hint="needs_manual_review",
                match_identifier="CIG",
                match_rule_type="range",
                max_value=22000.0,
            ),
            CodeRule(
                field_identifier="VIS",
                rule_type="normalization",
                rule_description="VIS visibility is clipped to 160000.0 instead of nulling when above the cap.",
                enforcement_location=cpath,
                enforcement_function="_expand_parsed",
                code_reference=build_code_reference(cpath, line('if prefix == "VIS" and idx == 1'), "VIS clamp"),
                behavior_on_violation="coerce",
                output_effect="Above-cap values are clamped to the cap and retained.",
                source_reference="VIS clamp behavior",
                source_class_hint="implementation_only",
                doc_support_hint="supported_partial",
                strictness_hint="looser",
                review_hint="needs_manual_review",
                match_identifier="VIS",
                match_rule_type="range",
                max_value=160000.0,
            ),
            CodeRule(
                field_identifier="CRN",
                rule_type="null_semantics",
                rule_description="CRN prefixes CB/CF/CG/CH/CI/CN force numeric parts to missing when associated quality token is 9.",
                enforcement_location=cpath,
                enforcement_function="_is_crn_missing_qc",
                code_reference=build_code_reference(cpath, line("def _is_crn_missing_qc"), "_is_crn_missing_qc"),
                behavior_on_violation="null",
                output_effect="Numeric measurements are nullified solely from quality-missing marker semantics.",
                source_reference="CRN quality-missing coercion",
                source_class_hint="documented_inferred",
                doc_support_hint="supported_partial",
                strictness_hint="not_comparable",
                review_hint="needs_manual_review",
            ),
            CodeRule(
                field_identifier="EQD",
                rule_type="domain",
                rule_description="EQD N-family parameter code requires 6-char structure: 4-char element + 2 flags, each validated against allowed enums.",
                enforcement_location=cpath,
                enforcement_function="_is_valid_eqd_parameter_code",
                code_reference=build_code_reference(cpath, line("def _is_valid_eqd_parameter_code"), "_is_valid_eqd_parameter_code"),
                behavior_on_violation="null",
                output_effect="Malformed EQD parameter tokens are nullified.",
                source_reference="EQD parameter token validator",
                source_class_hint="documented_inferred",
                doc_support_hint="supported_partial",
                strictness_hint="not_comparable",
                review_hint="needs_manual_review",
            ),
            CodeRule(
                field_identifier="EQD",
                rule_type="normalization",
                rule_description="Legacy EQD parameter aliases are accepted for compatibility, including legacy MSD pattern for R-family tokens.",
                enforcement_location=cpath,
                enforcement_function="_is_valid_eqd_parameter_code",
                code_reference=build_code_reference(cpath, line("if normalized in LEGACY_EQD_PARAMETER_CODES"), "LEGACY_EQD_PARAMETER_CODES"),
                behavior_on_violation="coerce",
                output_effect="Legacy parameter encodings are preserved instead of being rejected.",
                source_reference="legacy_EQD_parameter_aliases",
                source_class_hint="legacy_behavior",
                doc_support_hint="unknown",
                strictness_hint="not_comparable",
                review_hint="needs_manual_review",
            ),
            CodeRule(
                field_identifier="REM",
                rule_type="structural_guard",
                rule_description="Structured REM parsing enforces known remark type code, 3-digit text length, ASCII-only text, and exact payload slicing.",
                enforcement_location=cpath,
                enforcement_function="_parse_structured_remark",
                code_reference=build_code_reference(cpath, line("def _parse_structured_remark"), "_parse_structured_remark"),
                behavior_on_violation="coerce",
                output_effect="Invalid structured REM payloads fall back to plain text parsing.",
                source_reference="REM structured parser",
                source_class_hint="documented_inferred",
                doc_support_hint="supported_partial",
                strictness_hint="not_comparable",
                review_hint="needs_manual_review",
            ),
            CodeRule(
                field_identifier="QNN",
                rule_type="structural_guard",
                rule_description="QNN parser enforces dynamic block arity and fixed token widths (1/4/6), valid element identifiers, and no trailing payload.",
                enforcement_location=cpath,
                enforcement_function="_parse_qnn",
                code_reference=build_code_reference(cpath, line("def _parse_qnn(value: object)"), "_parse_qnn"),
                behavior_on_violation="null",
                output_effect="Malformed QNN payloads result in null parsed QNN columns.",
                source_reference="QNN strict parser",
                source_class_hint="documented_inferred",
                doc_support_hint="supported_partial",
                strictness_hint="not_comparable",
                review_hint="needs_manual_review",
            ),
            CodeRule(
                field_identifier="GLOBAL",
                rule_type="exclusion",
                rule_description="Rows with raw block length above 8192 are rejected before per-field parsing.",
                enforcement_location=cpath,
                enforcement_function="_record_structure_error",
                code_reference=build_code_reference(cpath, line("if actual_length > 8192"), "block_length_exceeds_max"),
                behavior_on_violation="exclude",
                output_effect="Rejected rows receive parse error and no parsed field payload is produced.",
                source_reference="record_structure_guard",
                source_class_hint="defensive_sanity_check",
                doc_support_hint="unknown",
                strictness_hint="not_comparable",
                review_hint="auto_classified",
            ),
            CodeRule(
                field_identifier="GLOBAL",
                rule_type="exclusion",
                rule_description="Rows with raw record length above 2844 are rejected before per-field parsing.",
                enforcement_location=cpath,
                enforcement_function="_record_structure_error",
                code_reference=build_code_reference(cpath, line("if actual_length > 2844"), "record_length_exceeds_max"),
                behavior_on_violation="exclude",
                output_effect="Rejected rows receive parse error and no parsed field payload is produced.",
                source_reference="record_structure_guard",
                source_class_hint="defensive_sanity_check",
                doc_support_hint="unknown",
                strictness_hint="not_comparable",
                review_hint="auto_classified",
            ),
            CodeRule(
                field_identifier="GLOBAL",
                rule_type="exclusion",
                rule_description="Rows shorter than mandatory section length 105 are rejected.",
                enforcement_location=cpath,
                enforcement_function="_record_structure_error",
                code_reference=build_code_reference(cpath, line("if actual_length < 105"), "mandatory_section_short"),
                behavior_on_violation="exclude",
                output_effect="Rejected rows receive parse error and no parsed field payload is produced.",
                source_reference="record_structure_guard",
                source_class_hint="defensive_sanity_check",
                doc_support_hint="unknown",
                strictness_hint="not_comparable",
                review_hint="auto_classified",
            ),
            CodeRule(
                field_identifier="GLOBAL",
                rule_type="exclusion",
                rule_description="Rows are rejected when actual record length does not equal 105 + TOTAL_VARIABLE_CHARACTERS header value.",
                enforcement_location=cpath,
                enforcement_function="_record_structure_error",
                code_reference=build_code_reference(cpath, line("expected_length = 105 + total_variable_characters"), "record_length_mismatch"),
                behavior_on_violation="exclude",
                output_effect="Rejected rows receive parse error and no parsed field payload is produced.",
                source_reference="record_structure_guard",
                source_class_hint="documented_inferred",
                doc_support_hint="supported_partial",
                strictness_hint="not_comparable",
                review_hint="needs_manual_review",
            ),
            CodeRule(
                field_identifier="CONTROL",
                rule_type="structural_guard",
                rule_description="Control header parser enforces fixed slices, numeric/ASCII token formats, and strict sentinel encodings for latitude/longitude/elevation.",
                enforcement_location=cpath,
                enforcement_function="_validate_control_header",
                code_reference=build_code_reference(cpath, line("def _validate_control_header"), "_validate_control_header"),
                behavior_on_violation="exclude",
                output_effect="Rows with invalid header structure are rejected prior to parsed metric expansion.",
                source_reference="control_header_validator",
                source_class_hint="documented_inferred",
                doc_support_hint="supported_partial",
                strictness_hint="not_comparable",
                review_hint="needs_manual_review",
            ),
            CodeRule(
                field_identifier="CONTROL",
                rule_type="range",
                rule_description="Control header validator enforces DATE calendar validity and TIME HHMM validity beyond simple numeric width checks.",
                enforcement_location=cpath,
                enforcement_function="_validate_control_header",
                code_reference=build_code_reference(cpath, line("if date_day > month_lengths[date_month]"), "DATE/TIME calendar guard"),
                behavior_on_violation="exclude",
                output_effect="Rows with invalid calendar/time values are rejected.",
                source_reference="control_header_calendar_guard",
                source_class_hint="documented_inferred",
                doc_support_hint="supported_partial",
                strictness_hint="stricter",
                review_hint="needs_manual_review",
                match_identifier="DATE",
                match_rule_type="range",
                min_value=101.0,
                max_value=99991231.0,
            ),
            CodeRule(
                field_identifier="CONTROL",
                rule_type="normalization",
                rule_description="Control field normalization logic is used as a validator reference to emit deterministic control QC flags while preserving original control tokens.",
                enforcement_location=cpath,
                enforcement_function="_annotate_control_field_qc_flags",
                code_reference=build_code_reference(cpath, line("def _annotate_control_field_qc_flags"), "_annotate_control_field_qc_flags"),
                behavior_on_violation="flag",
                output_effect="Control-field anomalies emit QC flags while original control values are preserved.",
                source_reference="control_field_qc_annotation",
                source_class_hint="defensive_sanity_check",
                doc_support_hint="unknown",
                strictness_hint="not_comparable",
                review_hint="needs_manual_review",
            ),
            CodeRule(
                field_identifier="GLOBAL",
                rule_type="null_semantics",
                rule_description="Post-parse cleanup converts textual sentinel tokens in parsed columns to null based on FieldPartRule missing_values.",
                enforcement_location=cpath,
                enforcement_function="_cleanup_rule_missing_text",
                code_reference=build_code_reference(cpath, line("def _cleanup_rule_missing_text"), "_cleanup_rule_missing_text"),
                behavior_on_violation="null",
                output_effect="String-level sentinel remnants are replaced with null in cleaned output.",
                source_reference="post_parse_missing_cleanup",
                source_class_hint="documented_inferred",
                doc_support_hint="supported_partial",
                strictness_hint="not_comparable",
                review_hint="needs_manual_review",
            ),
            CodeRule(
                field_identifier="ADD",
                rule_type="exclusion",
                rule_description="ADD marker column is dropped when all non-empty values are literal ADD.",
                enforcement_location=cpath,
                enforcement_function="clean_noaa_dataframe",
                code_reference=build_code_reference(cpath, line('if "ADD" in cleaned.columns'), "ADD marker drop"),
                behavior_on_violation="exclude",
                output_effect="Structural marker column is removed from cleaned output.",
                source_reference="ADD structural marker handling",
                source_class_hint="implementation_only",
                doc_support_hint="unknown",
                strictness_hint="not_comparable",
                review_hint="auto_classified",
            ),
            CodeRule(
                field_identifier="GLOBAL",
                rule_type="normalization",
                rule_description="Row-level usability metrics derive from all __qc_pass columns: any-usable flag, usable count, usable fraction.",
                enforcement_location=cpath,
                enforcement_function="clean_noaa_dataframe",
                code_reference=build_code_reference(cpath, line('cleaned["row_has_any_usable_metric"] ='), "row-level QC usability metrics"),
                behavior_on_violation="flag",
                output_effect="Cleaned output includes deterministic quality usability summary columns.",
                source_reference="QC usability summary derivation",
                source_class_hint="implementation_only",
                doc_support_hint="unknown",
                strictness_hint="not_comparable",
                review_hint="auto_classified",
            ),
        ]
    )

    return rules


def _is_constants_declared_rule(rule: CodeRule) -> bool:
    return rule.source_reference.startswith("FIELD_RULES") or rule.source_reference.startswith("FIELD_RULE_PREFIXES")


def build_source_class(
    rule: CodeRule,
    matched: SpecRule | None,
    doc_support: str,
    strictness: str,
) -> str:
    if rule.source_class_hint in SOURCE_CLASS_VALUES:
        return rule.source_class_hint
    if matched is None:
        if _is_constants_declared_rule(rule):
            return "documented_inferred"
        if rule.rule_type in {"structural_guard", "exclusion"} and rule.field_identifier == "GLOBAL":
            return "defensive_sanity_check"
        return "implementation_only"
    if doc_support == "supported_exact" and strictness == "equal":
        return "documented_exact"
    return "documented_inferred"


def build_doc_support(rule: CodeRule, matched: SpecRule | None, payload_exact: bool, ambiguous: bool) -> str:
    if rule.doc_support_hint in DOC_SUPPORT_VALUES:
        return rule.doc_support_hint
    if matched is None:
        if _is_constants_declared_rule(rule):
            return "unknown"
        return "unsupported"
    if payload_exact and not ambiguous:
        return "supported_exact"
    return "supported_partial"


def build_strictness(rule: CodeRule, matched_strictness: str) -> str:
    if rule.strictness_hint in STRICTNESS_VALUES:
        return rule.strictness_hint
    if matched_strictness in STRICTNESS_VALUES:
        return matched_strictness
    return "not_comparable"


def build_review_status(rule: CodeRule, doc_support: str, strictness: str, ambiguous: bool) -> str:
    if rule.review_hint in REVIEW_VALUES:
        return rule.review_hint
    if ambiguous:
        return "needs_manual_review"
    if doc_support in {"unsupported", "unknown"}:
        return "needs_manual_review"
    if strictness in {"stricter", "looser"}:
        return "needs_manual_review"
    return "auto_classified"


def build_rationale(
    rule: CodeRule,
    matched: SpecRule | None,
    doc_support: str,
    strictness: str,
    ambiguous: bool,
) -> str:
    if rule.rationale_hint:
        return rule.rationale_hint
    if matched is None:
        return "No spec-coverage rule matched this enforced behavior."
    if doc_support == "supported_exact" and strictness == "equal":
        return f"Matched spec rule {matched.rule_id} on identifier/type/payload."
    if ambiguous:
        return f"Matched {matched.rule_id}, but multiple comparable spec rows exist."
    return f"Best matched to spec rule {matched.rule_id}; payload differs ({strictness})."


def normalize_behavior(value: str) -> str:
    normalized = value.strip().lower()
    if normalized in VIOLATION_VALUES:
        return normalized
    return "mixed"


def render_row(
    rule: CodeRule,
    matched: SpecRule | None,
    matched_strictness: str,
    payload_exact: bool,
    ambiguous: bool,
) -> dict[str, str]:
    doc_support = build_doc_support(rule, matched, payload_exact, ambiguous)
    strictness = build_strictness(rule, matched_strictness)
    source_class = build_source_class(rule, matched, doc_support, strictness)
    review_status = build_review_status(rule, doc_support, strictness, ambiguous)
    rationale = build_rationale(rule, matched, doc_support, strictness, ambiguous)
    rule_id = build_rule_id(rule)

    if rule.rule_type not in RULE_TYPE_VALUES:
        rule_type = "other"
    else:
        rule_type = rule.rule_type

    return {
        "rule_id": rule_id,
        "field_identifier": rule.field_identifier,
        "rule_type": rule_type,
        "rule_description": rule.rule_description,
        "enforcement_location": rule.enforcement_location,
        "enforcement_function": rule.enforcement_function,
        "code_reference": rule.code_reference,
        "source_class": source_class,
        "source_reference": rule.source_reference,
        "doc_support_status": doc_support,
        "strictness_vs_doc": strictness,
        "behavior_on_violation": normalize_behavior(rule.behavior_on_violation),
        "output_effect": rule.output_effect,
        "matched_spec_rule_id": matched.rule_id if matched else "",
        "keep_decision": rule.keep_decision,
        "rationale": rationale,
        "review_status": review_status,
    }


def build_spec_indexes(spec_rules: list[SpecRule]) -> tuple[dict[tuple[str, str], list[SpecRule]], dict[tuple[str, str], list[SpecRule]]]:
    by_identifier: dict[tuple[str, str], list[SpecRule]] = defaultdict(list)
    by_family: dict[tuple[str, str], list[SpecRule]] = defaultdict(list)
    for rule in spec_rules:
        by_identifier[(rule.identifier, rule.rule_type)].append(rule)
        by_family[(rule.identifier_family, rule.rule_type)].append(rule)
    return by_identifier, by_family


def sort_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return sorted(rows, key=lambda row: (row["field_identifier"], row["rule_type"], row["rule_id"]))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in CSV_COLUMNS})


def top_counts(rows: list[dict[str, str]], key: str, limit: int = 10) -> list[tuple[str, int]]:
    counter = Counter(row.get(key, "") for row in rows if row.get(key))
    return counter.most_common(limit)


def make_markdown_summary(rows: list[dict[str, str]]) -> str:
    total = len(rows)
    source_counts = Counter(row["source_class"] for row in rows)
    doc_counts = Counter(row["doc_support_status"] for row in rows)
    strict_counts = Counter(row["strictness_vs_doc"] for row in rows)

    high_risk = [
        row
        for row in rows
        if (
            row["doc_support_status"] == "unsupported"
            or row["strictness_vs_doc"] in {"stricter", "looser"}
        )
    ]
    high_risk.sort(
        key=lambda row: (
            0 if row["doc_support_status"] == "unsupported" else 1,
            row["field_identifier"],
            row["rule_id"],
        )
    )
    high_risk = high_risk[:25]

    ambiguous = [
        row
        for row in rows
        if "multiple comparable spec rows exist" in row["rationale"]
    ][:30]
    manual_review_count = sum(1 for row in rows if row["review_status"] == "needs_manual_review")

    file_counts = top_counts(rows, "enforcement_location", limit=8)
    function_counts = top_counts(rows, "enforcement_function", limit=12)

    lines: list[str] = []
    lines.append("# RULE_PROVENANCE_LEDGER Summary")
    lines.append("")
    lines.append(f"- Total enforced rules inventoried: **{total}**")
    lines.append("")
    lines.append("## Counts by `source_class`")
    for key in sorted(source_counts):
        lines.append(f"- `{key}`: {source_counts[key]}")
    lines.append("")
    lines.append("## Counts by `doc_support_status`")
    for key in sorted(doc_counts):
        lines.append(f"- `{key}`: {doc_counts[key]}")
    lines.append("")
    lines.append("## Counts by `strictness_vs_doc`")
    for key in sorted(strict_counts):
        lines.append(f"- `{key}`: {strict_counts[key]}")
    lines.append(f"- `needs_manual_review` rows: {manual_review_count}")
    lines.append("")
    lines.append("## Top Contributing Files")
    for path, count in file_counts:
        lines.append(f"- `{path}`: {count}")
    lines.append("")
    lines.append("## Top Contributing Functions")
    for fn, count in function_counts:
        lines.append(f"- `{fn}`: {count}")
    lines.append("")
    lines.append("## Highest-Risk Unsupported / Strictness-Divergent Rules")
    if not high_risk:
        lines.append("- None")
    else:
        for row in high_risk:
            lines.append(
                "- "
                f"`{row['rule_id']}` | `{row['field_identifier']}` | `{row['rule_type']}` | "
                f"doc=`{row['doc_support_status']}` strictness=`{row['strictness_vs_doc']}` | "
                f"{row['rule_description']}"
            )
    lines.append("")
    lines.append("## Ambiguous / Manual Review Rows")
    if not ambiguous:
        lines.append("- None")
    else:
        for row in ambiguous:
            lines.append(
                "- "
                f"`{row['rule_id']}` | `{row['field_identifier']}` | `{row['rule_type']}` | "
                f"match=`{row['matched_spec_rule_id'] or 'none'}` | {row['rationale']}"
            )
    lines.append("")
    lines.append("## Extraction Limitations")
    lines.append("- Rule extraction is static: runtime branches dependent on unseen data payloads may not surface additional behavior.")
    lines.append("- Spec matching relies on `spec_coverage.csv` normalization; ambiguous rows are intentionally marked for manual review.")
    lines.append("- `normalization` and some structural guards are implementation-centric and may map only partially (or not at all) to deterministic spec rows.")
    lines.append("- `keep_decision` is intentionally left blank unless objectively obvious from current code.")
    lines.append("")
    return "\n".join(lines)


def validate_row_schema(row: dict[str, str]) -> None:
    if row["rule_type"] not in RULE_TYPE_VALUES:
        raise ValueError(f"Invalid rule_type: {row['rule_type']}")
    if row["source_class"] not in SOURCE_CLASS_VALUES:
        raise ValueError(f"Invalid source_class: {row['source_class']}")
    if row["doc_support_status"] not in DOC_SUPPORT_VALUES:
        raise ValueError(f"Invalid doc_support_status: {row['doc_support_status']}")
    if row["strictness_vs_doc"] not in STRICTNESS_VALUES:
        raise ValueError(f"Invalid strictness_vs_doc: {row['strictness_vs_doc']}")
    if row["behavior_on_violation"] not in VIOLATION_VALUES:
        raise ValueError(f"Invalid behavior_on_violation: {row['behavior_on_violation']}")
    if row["review_status"] not in REVIEW_VALUES:
        raise ValueError(f"Invalid review_status: {row['review_status']}")


def generate_rows(repo_root: Path, spec_coverage_csv: Path) -> list[dict[str, str]]:
    constants_module = load_constants_module(repo_root)
    constants_path = repo_root / "src/noaa_climate_data/constants.py"
    cleaning_path = repo_root / "src/noaa_climate_data/cleaning.py"

    constants_index = parse_constants_ast(constants_path)
    code_rules = build_constants_rules(constants_module, constants_index)
    code_rules.extend(build_custom_cleaning_rules(cleaning_path))

    spec_rules = load_spec_rules(spec_coverage_csv)
    spec_by_identifier, spec_by_family = build_spec_indexes(spec_rules)

    rows: list[dict[str, str]] = []
    for code_rule in code_rules:
        matched, strictness, _, ambiguous = match_code_rule(code_rule, spec_by_identifier, spec_by_family)
        payload_exact = strictness == "equal"
        row = render_row(code_rule, matched, strictness, payload_exact, ambiguous)
        validate_row_schema(row)
        rows.append(row)

    # Deterministic de-duplication on rule_id.
    deduped: dict[str, dict[str, str]] = {}
    for row in rows:
        deduped[row["rule_id"]] = row
    return sort_rows(list(deduped.values()))


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate rule provenance ledger artifacts.")
    parser.add_argument(
        "--spec-coverage",
        type=Path,
        default=Path("spec_coverage.csv"),
        help="Path to spec_coverage.csv",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("RULE_PROVENANCE_LEDGER.csv"),
        help="Output CSV path",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("RULE_PROVENANCE_LEDGER.md"),
        help="Output markdown summary path",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    spec_csv = (repo_root / args.spec_coverage).resolve() if not args.spec_coverage.is_absolute() else args.spec_coverage
    output_csv = (repo_root / args.output_csv).resolve() if not args.output_csv.is_absolute() else args.output_csv
    output_md = (repo_root / args.output_md).resolve() if not args.output_md.is_absolute() else args.output_md

    if not spec_csv.exists():
        raise FileNotFoundError(f"Spec coverage file not found: {spec_csv}")

    rows = generate_rows(repo_root, spec_csv)
    write_csv(output_csv, rows)
    output_md.write_text(make_markdown_summary(rows), encoding="utf-8")
    print(f"Wrote {len(rows)} rule rows to {output_csv}")
    print(f"Wrote summary to {output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
