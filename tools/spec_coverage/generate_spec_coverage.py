#!/usr/bin/env python3
"""Generate NOAA ISD spec coverage artifacts.

Outputs:
- spec_coverage.csv
- docs/reports/SPEC_COVERAGE_REPORT.md

Test-coverage semantics:
- `test_covered_any` is TRUE for any non-`none` test match strength.
- `test_covered_strict` is TRUE only for exact/family matches:
  `exact_signature`, `exact_assertion`, or `family_assertion`.
- `wildcard_assertion` remains visible as weak coverage and does not count as strict.
- `test_covered` is kept for compatibility and mirrors `test_covered_any`.

This script is deterministic and uses local files only.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping

OUTPUT_COLUMNS = [
    "rule_id",
    "row_kind",
    "spec_file",
    "spec_line_start",
    "spec_line_end",
    "spec_evidence",
    "spec_part",
    "spec_doc",
    "identifier",
    "identifier_family",
    "rule_type",
    "spec_rule_text",
    "min_value",
    "max_value",
    "sentinel_values",
    "allowed_values_or_codes",
    "implemented_in_constants",
    "constants_location",
    "implemented_in_cleaning",
    "cleaning_location",
    "implementation_confidence",
    "enforcement_layer",
    "code_implemented",
    "code_location",
    "test_covered",
    "test_covered_any",
    "test_covered_strict",
    "test_match_strength",
    "test_location",
    "notes",
]

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
RULE_TYPE_SET = set(RULE_TYPE_ORDER)
METRIC_RULE_TYPES = [rule_type for rule_type in RULE_TYPE_ORDER if rule_type != "unknown"]
ROW_KIND_SPEC = "spec_rule"
ROW_KIND_STRUCTURAL = "structural_rule"
ROW_KIND_DOCUMENTATION = "documentation_rule"
ROW_KIND_SYNTHETIC = "synthetic"
VALID_ROW_KINDS = {
    ROW_KIND_SPEC,
    ROW_KIND_STRUCTURAL,
    ROW_KIND_DOCUMENTATION,
    ROW_KIND_SYNTHETIC,
}
METRIC_ROW_KINDS = {ROW_KIND_SPEC, ROW_KIND_STRUCTURAL}
EXTRACTED_ROW_KINDS = {ROW_KIND_SPEC, ROW_KIND_STRUCTURAL, ROW_KIND_DOCUMENTATION}
IMPLEMENTATION_CONFIDENCE_ORDER = {"high": 3, "medium": 2, "low": 1}
IMPLEMENTATION_CONFIDENCE_VALUES = set(IMPLEMENTATION_CONFIDENCE_ORDER)
ENFORCEMENT_LAYER_VALUES = {"constants_only", "cleaning_only", "both", "neither"}
TEST_MATCH_STRENGTH_ORDER = [
    "exact_signature",
    "exact_assertion",
    "family_assertion",
    "wildcard_assertion",
    "none",
]
TEST_MATCH_STRENGTH_SET = set(TEST_MATCH_STRENGTH_ORDER)
STRICT_TEST_MATCH_STRENGTHS = {"exact_signature", "exact_assertion", "family_assertion"}

IDENTIFIER_RE = re.compile(r"\b[A-Z][A-Z0-9]{1,5}\b")
IDENTIFIER_WITH_DIGIT_RE = re.compile(r"\b([A-Z]{1,4})(\d{1,2})\b")
IDENTIFIER_RANGE_RE = re.compile(r"\b([A-Z]{1,4})(\d{1,2})\s*[-–]\s*([A-Z]{1,4})(\d{1,2})\b")
CONTROL_POS_IDENTIFIER_RE = re.compile(r"\bCONTROL_POS_\d+_\d+\b")
WIDTH_SIGNATURE_KEYWORDS = ("width", "token_width", "token width", "fixed-width", "fixed width")
MIN_MAX_INLINE_RE = re.compile(
    r"\bMIN\b\s*:?\s*([+\-]?\s*\d+)\b.*?\bMAX\b\s*:?\s*([+\-]?\s*\d+)\b",
    re.IGNORECASE,
)
MIN_ONLY_RE = re.compile(
    r"\bMIN\b\s*:?\s*([+\-]?\s*\d+)\b",
    re.IGNORECASE,
)
MAX_ONLY_RE = re.compile(
    r"\bMAX\b\s*:?\s*([+\-]?\s*\d+)\b",
    re.IGNORECASE,
)
MISSING_EQ_RE = re.compile(r"\b([+\-]?\d+)\s*=\s*Missing\b", re.IGNORECASE)
EQ_MISSING_RE = re.compile(r"\bMissing\s*=\s*([+\-]?\d+)\b", re.IGNORECASE)
FLD_LEN_RE = re.compile(r"\bFLD\s+LEN\s*:\s*(\d+)\b", re.IGNORECASE)
POS_RE = re.compile(r"\bPOS\s*:\s*(\d+)\s*-\s*(\d+)\b", re.IGNORECASE)
UP_TO_RE = re.compile(r"up\s+to\s+(\d+)", re.IGNORECASE)
NUMERIC_TOKEN_RE = re.compile(r"(?<![A-Z0-9_])([+\-]?\d+(?:\.\d+)?)(?![A-Z0-9_])")
DDHHMM_PATTERN_TEXT = r"^(0[1-9]|[12][0-9]|3[01])([01][0-9]|2[0-3])[0-5][0-9]$"
HHMM_PATTERN_TEXT = r"^([01][0-9]|2[0-3])[0-5][0-9]$"
DAY_PAIR_PATTERN_TEXT = r"^(0[1-9]|[12][0-9]|3[01]){2}$"
DAY_PAIR_TRIPLE_PATTERN_TEXT = r"^(?:0[1-9]|[12][0-9]|3[01]|99){3}$"

SPEC_DOC_NAME = "isd-format-document.deterministic.md"
SPEC_PART_ANCHORS: list[tuple[str, str]] = [
    ("02", "Control Data Section"),
    ("03", "Mandatory Data Section"),
    ("04", "GEOPHYSICAL-POINT-OBSERVATION additional data identifier"),
    ("05", "PRESENT-WEATHER-OBSERVATION automated occurrence identifier for ASOS/AWOS data"),
    ("06", "Subhourly Observed Liquid Precipitation Section: Secondary Sensor identifier"),
    ("07", "US-NETWORK-METADATA identifier"),
    ("08", "CRN Control Section identifier"),
    ("09", "Subhourly Temperature Section identifier"),
    ("10", "Hourly Temperature Section identifier"),
    ("11", "Hourly Temperature Extreme Section identifier"),
    ("12", "Subhourly Wetness Section identifier"),
    ("13", "Hourly Geonor Vibrating Wire Summary Section identifier"),
    ("14", "RUNWAY-VISUAL-RANGE-OBSERVATION identifier"),
    ("15", "SKY-COVER-LAYER identifier"),
    ("16", "SUNSHINE-OBSERVATION identifier"),
    ("17", "Solar Irradiance Section identifier"),
    ("18", "Net Solar Radiation Section identifier"),
    ("19", "Modeled Solar Irradiance Section identifier"),
    ("20", "Hourly Solar Angle Section identifier"),
    ("21", "Hourly Extraterrestrial Radiation Section identifier"),
    ("22", "HAIL identifier"),
    ("23", "GROUND-SURFACE-OBSERVATION identifier"),
    ("24", "EXTREME-AIR-TEMPERATURE identifier"),
    ("27", "ATMOSPHERIC-PRESSURE-OBSERVATION identifier"),
    ("28", "PRESENT-WEATHER-IN-VICINITY-OBSERVATION occurrence identifier"),
    ("29", "SUPPLEMENTARY-WIND-OBSERVATION identifier"),
    ("25", "SEA-SURFACE-TEMPERATURE-OBSERVATION identifier"),
    ("26", "SOIL-TEMPERATURE identifier"),
    ("30", "WAVE-MEASUREMENT identifier"),
]
LATE_DOCUMENT_PART_ORDER = ("24", "27", "28", "29", "25", "26", "30")

CONTROL_CONTEXT_MAP = {
    "date of observation": "DATE",
    "geophysical-point-observation date": "DATE",
    "time of observation": "TIME",
    "geophysical-point-observation time": "TIME",
    "latitude coordinate": "LATITUDE",
    "geophysical-point-observation latitude coordinate": "LATITUDE",
    "longitude coordinate": "LONGITUDE",
    "geophysical-point-observation longitude coordinate": "LONGITUDE",
    "elevation dimension": "ELEVATION",
    "geophysical-point-observation elevation dimension": "ELEVATION",
    "call letter identifier": "CALL_SIGN",
    "fixed-weather-station call letter identifier": "CALL_SIGN",
    "report type code": "REPORT_TYPE",
    "geophysical-report-type code": "REPORT_TYPE",
    "quality control process name": "QC_PROCESS",
    "meteorological-point-observation quality control process name": "QC_PROCESS",
}

MANDATORY_CONTEXT_MAP = {
    "wind-observation": "WND",
    "sky-condition-observation": "CIG",
    "visibility-observation": "VIS",
    "air-temperature-observation air temperature": "TMP",
    "air-temperature-observation dew point": "DEW",
    "atmospheric-pressure-observation sea level pressure": "SLP",
    "sea level pressure": "SLP",
}

# Deterministic attribution for section-header identifier width rows (FLD LEN: 3).
# Keys are (spec_part, normalized context line that follows FLD LEN: 3).
SECTION_IDENTIFIER_CONTEXT_MAP: dict[tuple[str, str], str] = {
    ("04", "geophysical-point-observation additional data identifier"): "ADD",
    ("04", "liquid-precipitation occurrence identifier"): "AA1",
    ("05", "present-weather-observation automated occurrence identifier for asos/awos data"): "AT1",
    ("06", "subhourly observed liquid precipitation section: secondary sensor identifier"): "CB1",
    ("07", "us-network-metadata identifier"): "CO1",
    ("08", "crn control section identifier"): "CR1",
    ("09", "subhourly temperature section identifier"): "CT1",
    ("10", "hourly temperature section identifier"): "CU1",
    ("11", "hourly temperature extreme section identifier"): "CV1",
    ("12", "subhourly wetness section identifier"): "CW1",
    ("13", "hourly geonor vibrating wire summary section identifier"): "CX1",
    ("14", "runway-visual-range-observation identifier"): "ED1",
    ("15", "sky-cover-layer identifier"): "GA1",
    ("16", "sunshine-observation identifier"): "GJ1",
    ("17", "solar irradiance section identifier"): "GM1",
    ("18", "net solar radiation section identifier"): "GO1",
    ("19", "modeled solar irradiance section identifier"): "GP1",
    ("20", "hourly solar angle section identifier"): "GQ1",
    ("21", "hourly extraterrestrial radiation section identifier"): "GR1",
    # Parser uses static identifier HAIL for this section.
    ("22", "hail identifier"): "HAIL",
    ("23", "ground-surface-observation identifier"): "IA1",
    ("24", "extreme-air-temperature identifier"): "KA1",
    ("25", "sea-surface-temperature-observation identifier"): "SA1",
    ("26", "soil-temperature identifier"): "ST1",
    ("27", "atmospheric-pressure-observation identifier"): "MA1",
    ("28", "present-weather-in-vicinity-observation occurrence identifier"): "MV1",
    ("29", "supplementary-wind-observation identifier"): "OA1",
    ("30", "wave-measurement identifier"): "UA1",
}
SECTION_IDENTIFIER_LOOKAHEAD_LINES = 4


@dataclass(slots=True)
class SpecRuleRow:
    spec_part: str
    spec_doc: str
    identifier: str
    identifier_family: str
    rule_type: str
    spec_rule_text: str
    rule_id: str = ""
    row_kind: str = "spec_rule"
    spec_file: str = ""
    spec_line_start: int | None = None
    spec_line_end: int | None = None
    spec_evidence: str = ""
    min_value: str = ""
    max_value: str = ""
    sentinel_values: str = ""
    allowed_values_or_codes: str = ""
    implemented_in_constants: bool = False
    constants_location: str = ""
    implemented_in_cleaning: bool = False
    cleaning_location: str = ""
    implementation_confidence: str = "low"
    enforcement_layer: str = "neither"
    code_implemented: bool = False
    code_location: str = ""
    test_covered: bool = False
    test_covered_any: bool = False
    test_covered_strict: bool = False
    test_match_strength: str = "none"
    test_location: str = ""
    notes: set[str] = field(default_factory=set)

    def key(self) -> tuple[str, ...]:
        return (
            self.rule_id,
            self.row_kind,
            self.spec_file,
            str(self.spec_line_start if self.spec_line_start is not None else ""),
            str(self.spec_line_end if self.spec_line_end is not None else ""),
            self.spec_part,
            self.spec_doc,
            self.identifier,
            self.identifier_family,
            self.rule_type,
            self.spec_rule_text,
            self.min_value,
            self.max_value,
            self.sentinel_values,
            self.allowed_values_or_codes,
        )

    def sort_key(self) -> tuple[str, ...]:
        return stable_row_sort_key(self)

    def csv_record(self) -> dict[str, str]:
        return {
            "rule_id": self.rule_id,
            "row_kind": self.row_kind,
            "spec_file": self.spec_file,
            "spec_line_start": str(self.spec_line_start) if self.spec_line_start is not None else "",
            "spec_line_end": str(self.spec_line_end) if self.spec_line_end is not None else "",
            "spec_evidence": self.spec_evidence,
            "spec_part": self.spec_part,
            "spec_doc": self.spec_doc,
            "identifier": self.identifier,
            "identifier_family": self.identifier_family,
            "rule_type": self.rule_type,
            "spec_rule_text": self.spec_rule_text,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "sentinel_values": self.sentinel_values,
            "allowed_values_or_codes": self.allowed_values_or_codes,
            "implemented_in_constants": "TRUE" if self.implemented_in_constants else "FALSE",
            "constants_location": self.constants_location,
            "implemented_in_cleaning": "TRUE" if self.implemented_in_cleaning else "FALSE",
            "cleaning_location": self.cleaning_location,
            "implementation_confidence": self.implementation_confidence,
            "enforcement_layer": self.enforcement_layer,
            "code_implemented": "TRUE" if self.code_implemented else "FALSE",
            "code_location": self.code_location,
            "test_covered": "TRUE" if self.test_covered else "FALSE",
            "test_covered_any": "TRUE" if self.test_covered_any else "FALSE",
            "test_covered_strict": "TRUE" if self.test_covered_strict else "FALSE",
            "test_match_strength": self.test_match_strength,
            "test_location": self.test_location,
            "notes": ";".join(sorted(self.notes)),
        }


@dataclass(slots=True)
class SpecPartSegment:
    spec_part: str
    anchor_text: str
    anchor_line: int
    start_line: int
    end_line: int


@dataclass(slots=True)
class ConstantsAstIndex:
    field_rule_lines: dict[str, int] = field(default_factory=dict)
    part_lines: dict[tuple[str, int], int] = field(default_factory=dict)
    part_keyword_lines: dict[tuple[str, int, str], int] = field(default_factory=dict)
    repeated_range_lines: dict[str, int] = field(default_factory=dict)
    function_lines: dict[str, int] = field(default_factory=dict)


@dataclass(slots=True)
class CleaningEvidence:
    identifier: str
    identifier_family: str
    rule_type: str
    evidence_kind: str
    location: str
    confidence: str


@dataclass(slots=True)
class CleaningIndex:
    function_lines: dict[str, int] = field(default_factory=dict)
    strict_arity_line: int | None = None
    strict_width_line: int | None = None
    generic_domain_line: int | None = None
    evidence: list[CleaningEvidence] = field(default_factory=list)
    _evidence_seen: set[tuple[str, str, str, str, str, str]] = field(default_factory=set)

    def add_evidence(
        self,
        identifier: str,
        family: str,
        rule_type: str,
        evidence_kind: str,
        line: int | None,
        confidence: str,
    ) -> None:
        confidence_norm = confidence if confidence in IMPLEMENTATION_CONFIDENCE_VALUES else "low"
        rule_type_norm = rule_type if rule_type in RULE_TYPE_SET else "other"
        location = f"src/noaa_spec/cleaning.py:{line}" if line else ""
        family_norm = family or (identifier_family(identifier) if identifier else "")
        key = (identifier, family_norm, rule_type_norm, evidence_kind, location, confidence_norm)
        if key in self._evidence_seen:
            return
        self._evidence_seen.add(key)
        self.evidence.append(
            CleaningEvidence(
                identifier=identifier,
                identifier_family=family_norm,
                rule_type=rule_type_norm,
                evidence_kind=evidence_kind,
                location=location,
                confidence=confidence_norm,
            )
        )


@dataclass(slots=True)
class TestEvidenceIndex:
    signature_locations: dict[tuple[str, str, str, str, str, str], tuple[str, int]] = field(default_factory=dict)
    exact_assertions: dict[tuple[str, str], tuple[str, int]] = field(default_factory=dict)
    family_assertions: dict[tuple[str, str], tuple[str, int]] = field(default_factory=dict)
    wildcard_assertions: dict[str, tuple[str, int]] = field(default_factory=dict)
    arity_tests_detected: bool = False

    def add_signature(
        self,
        identifier: str,
        rule_type: str,
        min_value: str = "",
        max_value: str = "",
        sentinel_values: str = "",
        allowed_values_or_codes: str = "",
        location: tuple[str, int] = ("", 0),
    ) -> None:
        key = (
            identifier,
            rule_type,
            min_value,
            max_value,
            sentinel_values,
            allowed_values_or_codes,
        )
        if key not in self.signature_locations:
            self.signature_locations[key] = location

    def add_exact_assertion(self, identifier: str, rule_type: str, location: tuple[str, int]) -> None:
        key = (identifier, rule_type)
        if key not in self.exact_assertions:
            self.exact_assertions[key] = location

    def add_family_assertion(self, family: str, rule_type: str, location: tuple[str, int]) -> None:
        key = (family, rule_type)
        if key not in self.family_assertions:
            self.family_assertions[key] = location

    def add_wildcard_assertion(self, rule_type: str, location: tuple[str, int]) -> None:
        if rule_type not in self.wildcard_assertions:
            self.wildcard_assertions[rule_type] = location

    def _signature_keys_for_row(
        self,
        identifier: str,
        rule_type: str,
        min_value: str,
        max_value: str,
        sentinel_values: str,
        allowed_values_or_codes: str,
    ) -> list[tuple[str, str, str, str, str, str]]:
        keys: list[tuple[str, str, str, str, str, str]] = []
        if min_value or max_value or sentinel_values or allowed_values_or_codes:
            keys.append((identifier, rule_type, min_value, max_value, sentinel_values, allowed_values_or_codes))
        if min_value:
            keys.append((identifier, rule_type, min_value, "", "", ""))
        if max_value:
            keys.append((identifier, rule_type, "", max_value, "", ""))
        if sentinel_values:
            for token in sentinel_values.split("|"):
                token_norm = normalize_num_token(token)
                if token_norm:
                    keys.append((identifier, rule_type, "", "", token_norm, ""))
        if allowed_values_or_codes:
            for token in allowed_values_or_codes.split("|"):
                token_norm = normalize_num_token(token)
                if token_norm:
                    keys.append((identifier, rule_type, "", "", "", token_norm))
        # deterministic de-dupe preserving insertion order
        seen: set[tuple[str, str, str, str, str, str]] = set()
        deduped: list[tuple[str, str, str, str, str, str]] = []
        for key in keys:
            if key in seen:
                continue
            seen.add(key)
            deduped.append(key)
        return deduped

    def _requires_exact_test_evidence(
        self,
        rule_type: str,
        min_value: str,
        max_value: str,
        sentinel_values: str,
        allowed_values_or_codes: str,
    ) -> bool:
        if rule_type == "range" and bool(min_value or max_value):
            return True
        if rule_type in {"width", "arity"} and bool(allowed_values_or_codes):
            return True
        if rule_type == "sentinel" and bool(sentinel_values):
            return True
        if rule_type in {"domain", "allowed_quality"} and bool(allowed_values_or_codes):
            return True
        return False

    def find(
        self,
        identifier: str,
        family: str,
        rule_type: str,
        min_value: str = "",
        max_value: str = "",
        sentinel_values: str = "",
        allowed_values_or_codes: str = "",
    ) -> tuple[tuple[str, int] | None, str]:
        alt_rule_types: list[str] = [rule_type]
        if rule_type == "allowed_quality":
            alt_rule_types.append("domain")
        elif rule_type == "domain":
            alt_rule_types.append("allowed_quality")

        exact_only = self._requires_exact_test_evidence(
            rule_type,
            min_value,
            max_value,
            sentinel_values,
            allowed_values_or_codes,
        )

        for rt in alt_rule_types:
            for signature_key in self._signature_keys_for_row(
                identifier,
                rt,
                min_value,
                max_value,
                sentinel_values,
                allowed_values_or_codes,
            ):
                location = self.signature_locations.get(signature_key)
                if location is not None:
                    return location, "exact_signature"

            location = self.exact_assertions.get((identifier, rt))
            if location is not None:
                return location, "exact_assertion"

            if exact_only:
                continue

            location = self.family_assertions.get((family, rt))
            if location is not None:
                return location, "family_assertion"

            location = self.wildcard_assertions.get(rt)
            if location is not None:
                return location, "wildcard_assertion"

        return None, "none"


class SpecSegmentationError(RuntimeError):
    """Raised when the deterministic spec document cannot be segmented safely."""


def normalize_num_token(token: str) -> str:
    token = token.strip().strip(".,;:")
    token = token.replace(" ", "")
    if token.startswith("+"):
        token = token[1:]
    return token


def float_to_int_token(value: float | None) -> int | None:
    if value is None:
        return None
    rounded = int(round(value))
    if abs(value - float(rounded)) > 1e-9:
        return None
    return rounded


def parse_int_token(token: str) -> int | None:
    normalized = normalize_num_token(token)
    if not normalized:
        return None
    if not re.fullmatch(r"[+-]?\d+", normalized):
        return None
    try:
        return int(normalized)
    except ValueError:
        return None


def contiguous_numeric_bounds(values: Iterable[str]) -> tuple[int, int, bool] | None:
    numbers: list[int] = []
    for raw in values:
        parsed = parse_int_token(raw)
        if parsed is None:
            return None
        numbers.append(parsed)
    if not numbers:
        return None
    uniq = sorted(set(numbers))
    contiguous = all((b - a) == 1 for a, b in zip(uniq, uniq[1:]))
    return uniq[0], uniq[-1], contiguous


def normalized_token_set(values: Iterable[str]) -> set[str]:
    return {normalize_num_token(v) for v in values if normalize_num_token(v)}


def repeated_token_match(single_token: str, composite_token: str) -> bool:
    if not single_token or not composite_token:
        return False
    if single_token == composite_token:
        return True
    if len(composite_token) % len(single_token) != 0:
        return False
    return single_token * (len(composite_token) // len(single_token)) == composite_token


def pattern_supports_range(
    allowed_pattern: re.Pattern[str] | None,
    spec_min: float | None,
    spec_max: float | None,
) -> bool:
    if allowed_pattern is None:
        return False
    spec_min_int = float_to_int_token(spec_min)
    spec_max_int = float_to_int_token(spec_max)
    if spec_min_int is None or spec_max_int is None:
        return False

    pattern_text = allowed_pattern.pattern
    if pattern_text == DDHHMM_PATTERN_TEXT:
        return spec_min_int == 10000 and spec_max_int == 312359
    if pattern_text == HHMM_PATTERN_TEXT:
        return spec_min_int == 0 and spec_max_int == 2359
    if pattern_text in {DAY_PAIR_PATTERN_TEXT, DAY_PAIR_TRIPLE_PATTERN_TEXT}:
        # Some spec lines encode MMDD/MMDDMM ranges directly for day-pair fields.
        if (spec_min_int, spec_max_int) in {(101, 3131), (10101, 313131)}:
            return True
        return spec_min_int == 1 and spec_max_int == 31
    return False


def normalize_text_line(value: str) -> str:
    return " ".join(value.replace("\u2013", "-").replace("\u2014", "-").split())


def identifier_family(identifier: str) -> str:
    if identifier.startswith("CONTROL_POS_"):
        return "CONTROL"
    match = IDENTIFIER_WITH_DIGIT_RE.match(identifier)
    if match:
        return match.group(1)
    return identifier


def natural_key(value: str) -> tuple:
    parts = re.split(r"(\d+)", value)
    out: list[object] = []
    for part in parts:
        if part.isdigit():
            out.append(int(part))
        else:
            out.append(part)
    return tuple(out)


def short_text(value: str, limit: int = 160) -> str:
    clean = normalize_text_line(value)
    if len(clean) <= limit:
        return clean
    return clean[: limit - 3].rstrip() + "..."


def pipe_join(values: Iterable[str]) -> str:
    uniq = {v for v in values if v}
    return "|".join(sorted(uniq, key=natural_key)) if uniq else ""


def parse_numeric_or_text(value: str) -> int | float | str | None:
    token = normalize_num_token(value)
    if token == "":
        return None
    if re.fullmatch(r"[+-]?\d+", token):
        return int(token)
    if re.fullmatch(r"[+-]?\d+\.\d+", token):
        return float(token)
    return token


def parse_pipe_tokens(value: str) -> list[str]:
    if not value:
        return []
    tokens = [token.strip() for token in value.split("|") if token.strip()]
    return sorted(set(tokens), key=natural_key)


def normalize_pipe_field(value: str) -> str:
    return "|".join(parse_pipe_tokens(value))


def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def short_sha1(value: str, length: int = 10) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:length]


def parse_pos_range(value: str) -> tuple[int, int] | None:
    match = re.search(r"\bPOS\s*:?\s*(\d+)\s*-\s*(\d+)\b", value, re.IGNORECASE)
    if not match:
        return None
    start = int(match.group(1))
    end = int(match.group(2))
    return (start, end) if start <= end else (end, start)


def parse_cardinality_range(value: str) -> tuple[int | None, int | None]:
    if not value:
        return None, None
    match = re.fullmatch(r"\s*(\d+)\s*-\s*(\d+)\s*", value)
    if match:
        low = int(match.group(1))
        high = int(match.group(2))
        if low > high:
            low, high = high, low
        return low, high
    one = parse_numeric_or_text(value)
    if isinstance(one, int):
        return one, one
    return None, None


def list_payload_values(value: str) -> list[int | float | str]:
    out: list[int | float | str] = []
    for token in parse_pipe_tokens(value):
        normalized = parse_numeric_or_text(token)
        out.append(token if normalized is None else normalized)
    return out


def build_row_payload(row: SpecRuleRow) -> dict[str, object]:
    if row.rule_type == "range":
        return {
            "min_value": parse_numeric_or_text(row.min_value),
            "max_value": parse_numeric_or_text(row.max_value),
        }
    if row.rule_type == "sentinel":
        return {"missing_values": list_payload_values(row.sentinel_values)}
    if row.rule_type == "allowed_quality":
        return {"allowed_quality": list_payload_values(row.allowed_values_or_codes)}
    if row.rule_type == "domain":
        tokens = parse_pipe_tokens(row.allowed_values_or_codes)
        if len(tokens) == 1 and tokens[0].startswith("^") and tokens[0].endswith("$"):
            return {"allowed_pattern": tokens[0]}
        return {"allowed_values": list_payload_values(row.allowed_values_or_codes)}
    if row.rule_type == "width":
        pos = parse_pos_range(row.spec_rule_text)
        if pos is not None:
            return {"pos_start": pos[0], "pos_end": pos[1]}
        width = parse_numeric_or_text(row.allowed_values_or_codes)
        return {"token_width": width}
    if row.rule_type == "arity":
        expected_parts = parse_numeric_or_text(row.allowed_values_or_codes)
        return {"expected_parts": expected_parts}
    if row.rule_type == "cardinality":
        min_occurs, max_occurs = parse_cardinality_range(row.allowed_values_or_codes)
        return {"min_occurs": min_occurs, "max_occurs": max_occurs}
    return {}


def row_payload_hash(row: SpecRuleRow) -> str:
    payload = build_row_payload(row)
    return short_sha1(canonical_json(payload))


def row_stable_id(row: SpecRuleRow) -> str:
    payload_json = canonical_json(build_row_payload(row))
    stable_input = "|".join(
        [
            normalize_text_line(row.spec_rule_text),
            row.identifier,
            row.rule_type,
            payload_json,
        ]
    )
    return short_sha1(stable_input, length=12)


def normalize_row(row: SpecRuleRow) -> None:
    row.identifier = row.identifier.strip().upper()
    row.rule_type = row.rule_type.strip().lower()
    row.identifier_family = identifier_family(row.identifier)
    row.sentinel_values = normalize_pipe_field(row.sentinel_values)
    row.allowed_values_or_codes = normalize_pipe_field(row.allowed_values_or_codes)
    row.spec_evidence = normalize_text_line(row.spec_evidence).strip()

    row_kind = row.row_kind.strip().lower() if row.row_kind else ROW_KIND_SPEC
    row.row_kind = row_kind if row_kind in VALID_ROW_KINDS else ROW_KIND_SPEC

    if not row.spec_file or row.spec_file == "N/A":
        row.spec_file = row.spec_doc if row.spec_doc.endswith(".md") else SPEC_DOC_NAME
    if row.spec_line_start is None:
        row.spec_line_start = 1
    if row.spec_line_end is None:
        row.spec_line_end = row.spec_line_start
    if row.spec_line_end < row.spec_line_start:
        row.spec_line_start, row.spec_line_end = row.spec_line_end, row.spec_line_start


def assign_rule_id(row: SpecRuleRow) -> None:
    payload_hash = row_payload_hash(row)
    row.rule_id = f"{row.spec_file}::{row_stable_id(row)}::{row.identifier}::{row.rule_type}::{payload_hash}"


def normalize_and_assign_rule_ids(rows: list[SpecRuleRow]) -> list[SpecRuleRow]:
    for row in rows:
        normalize_row(row)
        assign_rule_id(row)
    return rows


def row_kind_rank(value: str) -> int:
    if value == ROW_KIND_SPEC:
        return 0
    if value == ROW_KIND_STRUCTURAL:
        return 1
    if value == ROW_KIND_DOCUMENTATION:
        return 2
    if value == ROW_KIND_SYNTHETIC:
        return 3
    return 4


def classify_extracted_row_kinds(rows: list[SpecRuleRow]) -> list[SpecRuleRow]:
    structural_types = {"width", "range", "sentinel"}
    for row in rows:
        if row.row_kind == ROW_KIND_SYNTHETIC:
            continue

        has_pos = bool(parse_pos_range(row.spec_rule_text) or POS_RE.search(row.spec_evidence))
        has_numeric_bounds = bool(row.min_value or row.max_value)
        has_sentinel = bool(row.sentinel_values)
        is_mapped_identifier = bool(
            row.identifier
            and row.identifier != "UNSPECIFIED"
            and not row.identifier.startswith("CONTROL_POS_")
        )

        if has_pos and row.rule_type in structural_types and not is_mapped_identifier:
            row.row_kind = ROW_KIND_STRUCTURAL
            continue

        if row.rule_type == "unknown" and not has_pos and not has_numeric_bounds and not has_sentinel:
            row.row_kind = ROW_KIND_DOCUMENTATION
            continue

        row.row_kind = ROW_KIND_SPEC

    return rows


def line_sort_value(value: int | None) -> int:
    return value if value is not None else 10**9


def stable_row_sort_key(row: SpecRuleRow) -> tuple[object, ...]:
    return (
        row_kind_rank(row.row_kind),
        row.spec_file,
        line_sort_value(row.spec_line_start),
        line_sort_value(row.spec_line_end),
        row.identifier,
        row.rule_type,
        row.rule_id,
    )


def build_spec_evidence(raw_lines: list[str], line_start: int, line_end: int, limit: int = 200) -> str:
    if not raw_lines:
        return ""
    start = max(1, line_start)
    end = min(len(raw_lines), line_end)
    if end < start:
        end = start
    snippet_parts = [
        normalize_text_line(raw_lines[idx - 1]).strip()
        for idx in range(start, end + 1)
        if normalize_text_line(raw_lines[idx - 1]).strip()
    ]
    snippet = " ".join(snippet_parts).strip()
    if len(snippet) <= limit:
        return snippet
    return snippet[: limit - 3].rstrip() + "..."


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
                        "allowed_quality",
                        "allowed_values",
                        "allowed_pattern",
                        "token_width",
                        "token_pattern",
                    }:
                        index.part_keyword_lines[(key_value, part_idx, kw.arg)] = kw.value.lineno

    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            if node.name in {
                "is_valid_repeated_identifier",
                "is_valid_eqd_identifier",
                "is_valid_identifier",
                "get_field_rule",
                "get_expected_part_count",
                "get_token_width_rules",
                "get_field_registry_entry",
            }:
                index.function_lines[node.name] = node.lineno
        if isinstance(node, ast.Assign):
            targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if "_REPEATED_IDENTIFIER_RANGES" in targets and isinstance(node.value, ast.Dict):
                for key_node, _ in zip(node.value.keys, node.value.values):
                    key_value = ast_literal_str(key_node)
                    if key_value:
                        index.repeated_range_lines[key_value] = getattr(key_node, "lineno", node.lineno)
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id in {"FIELD_RULES", "FIELD_RULE_PREFIXES"} and isinstance(node.value, ast.Dict):
                parse_field_rules_dict(node.value)
        if isinstance(node, ast.Assign):
            targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if "FIELD_RULE_PREFIXES" in targets and isinstance(node.value, ast.Dict):
                parse_field_rules_dict(node.value)

    return index


def ast_literal_float(node: ast.AST | None) -> float | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        nested = ast_literal_float(node.operand)
        if nested is not None:
            return -nested
    return None


def ast_call_name(func: ast.AST) -> str:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return ""


def between_bounds_from_call(node: ast.AST) -> tuple[float, float] | None:
    if not isinstance(node, ast.Call):
        return None
    if not isinstance(node.func, ast.Attribute) or node.func.attr != "between":
        return None
    if len(node.args) < 2:
        return None
    low = ast_literal_float(node.args[0])
    high = ast_literal_float(node.args[1])
    if low is None or high is None:
        return None
    return low, high


def control_column_from_if_test(test: ast.AST) -> str | None:
    if not isinstance(test, ast.Compare):
        return None
    if len(test.ops) != 1 or not isinstance(test.ops[0], ast.In):
        return None
    if len(test.comparators) != 1:
        return None
    comparator = test.comparators[0]
    if not (
        isinstance(comparator, ast.Attribute)
        and comparator.attr == "columns"
        and isinstance(comparator.value, ast.Name)
        and comparator.value.id == "work"
    ):
        return None
    return ast_literal_str(test.left)


def parse_cleaning_index(cleaning_path: Path) -> CleaningIndex:
    source = cleaning_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(cleaning_path))
    index = CleaningIndex()
    lines = source.splitlines()

    function_defs: dict[str, ast.FunctionDef] = {}
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        function_defs[node.name] = node
        if node.name in {
            "clean_value_quality",
            "_expand_parsed",
            "clean_noaa_dataframe",
            "_normalize_control_fields",
        }:
            index.function_lines[node.name] = node.lineno

    # AST-first: strict gates, parse rejects, and local clamp/minmax evidence.
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            call_name = ast_call_name(node.func)
            if call_name == "get_expected_part_count":
                if index.strict_arity_line is None:
                    index.strict_arity_line = node.lineno
                index.add_evidence("", "", "arity", "strict_gate", node.lineno, "low")
            elif call_name == "get_token_width_rules":
                if index.strict_width_line is None:
                    index.strict_width_line = node.lineno
                index.add_evidence("", "", "width", "strict_gate", node.lineno, "low")
            elif call_name == "is_valid_eqd_identifier":
                for fam in ("Q", "P", "R", "C", "D", "N"):
                    index.add_evidence("", fam, "cardinality", "parse_reject", node.lineno, "medium")
            elif call_name == "is_valid_repeated_identifier":
                index.add_evidence("", "", "cardinality", "parse_reject", node.lineno, "low")
            elif call_name == "enforce_domain" and index.generic_domain_line is None:
                index.generic_domain_line = node.lineno

        if isinstance(node, ast.If):
            prefix_value = ""
            prefix_family = ""
            has_scaled_numeric_compare = False
            for test_node in ast.walk(node.test):
                if isinstance(test_node, ast.Compare):
                    if (
                        isinstance(test_node.left, ast.Name)
                        and test_node.left.id == "prefix"
                        and len(test_node.ops) == 1
                        and isinstance(test_node.ops[0], ast.Eq)
                        and len(test_node.comparators) == 1
                    ):
                        token = ast_literal_str(test_node.comparators[0])
                        if token:
                            prefix_value = token
                    if (
                        isinstance(test_node.left, ast.Name)
                        and test_node.left.id == "scaled"
                        and len(test_node.ops) == 1
                        and isinstance(test_node.ops[0], (ast.Gt, ast.GtE, ast.Lt, ast.LtE))
                        and len(test_node.comparators) == 1
                        and ast_literal_float(test_node.comparators[0]) is not None
                    ):
                        has_scaled_numeric_compare = True
                if (
                    isinstance(test_node, ast.Call)
                    and isinstance(test_node.func, ast.Attribute)
                    and isinstance(test_node.func.value, ast.Name)
                    and test_node.func.value.id == "prefix"
                    and test_node.func.attr == "startswith"
                    and test_node.args
                ):
                    token = ast_literal_str(test_node.args[0])
                    if token:
                        prefix_family = token

            clamp_assignment_line: int | None = None
            for stmt in node.body:
                if not isinstance(stmt, ast.Assign):
                    continue
                if not any(isinstance(target, ast.Name) and target.id == "scaled" for target in stmt.targets):
                    continue
                if ast_literal_float(stmt.value) is None:
                    continue
                clamp_assignment_line = stmt.lineno
                break

            if clamp_assignment_line and (prefix_value or prefix_family):
                confidence = "high" if prefix_value and has_scaled_numeric_compare else "medium"
                evidence_kind = "clamp" if has_scaled_numeric_compare else "special_case"
                family = identifier_family(prefix_value) if prefix_value else prefix_family
                index.add_evidence(prefix_value, family, "range", evidence_kind, clamp_assignment_line, confidence)

    normalize_control = function_defs.get("_normalize_control_fields")
    if normalize_control:
        date_validation_line: int | None = None
        time_validation_line: int | None = None
        for stmt in normalize_control.body:
            if not isinstance(stmt, ast.FunctionDef):
                continue
            if stmt.name == "_normalize_date":
                for sub in ast.walk(stmt):
                    if (
                        isinstance(sub, ast.Call)
                        and isinstance(sub.func, ast.Attribute)
                        and sub.func.attr == "fullmatch"
                    ):
                        date_validation_line = sub.lineno
                        break
            if stmt.name == "_normalize_time":
                for sub in ast.walk(stmt):
                    if between_bounds_from_call(sub) is not None:
                        time_validation_line = sub.lineno
                        break

        for stmt in normalize_control.body:
            if not isinstance(stmt, ast.If):
                continue
            column = control_column_from_if_test(stmt.test)
            if not column:
                continue
            if column == "DATE" and date_validation_line is not None:
                index.add_evidence("DATE", "DATE", "domain", "strict_gate", date_validation_line, "high")
            if column == "TIME" and time_validation_line is not None:
                index.add_evidence("TIME", "TIME", "range", "fallback_bounds", time_validation_line, "high")

            for sub in ast.walk(stmt):
                bounds = between_bounds_from_call(sub)
                if bounds is not None:
                    index.add_evidence(column, column, "range", "fallback_bounds", sub.lineno, "high")
                    continue
                if (
                    isinstance(sub, ast.Call)
                    and isinstance(sub.func, ast.Attribute)
                    and sub.func.attr == "isin"
                ):
                    rule_type = "allowed_quality" if column == "QUALITY_CONTROL" else "domain"
                    index.add_evidence(column, column, rule_type, "strict_gate", sub.lineno, "high")
                    continue
                if (
                    isinstance(sub, ast.Compare)
                    and len(sub.ops) == 1
                    and isinstance(sub.left, ast.Name)
                    and sub.left.id == "series"
                    and len(sub.comparators) == 1
                ):
                    sentinel = ast_literal_str(sub.comparators[0])
                    if sentinel is None:
                        continue
                    if sentinel in {"99999", "9", "None", "nan", ""}:
                        rule_type = "sentinel"
                    else:
                        rule_type = "domain"
                    index.add_evidence(column, column, rule_type, "fallback_bounds", sub.lineno, "high")

    # Conservative regex fallback for line-oriented rules.
    active_column: str | None = None
    active_indent: int = -1
    for line_no, line in enumerate(lines, start=1):
        stripped = line.strip()
        indent = len(line) - len(line.lstrip(" "))

        match_column = re.match(r'^\s*if\s+"([A-Z_]+)"\s+in\s+work\.columns\s*:', line)
        if match_column:
            active_column = match_column.group(1)
            active_indent = indent
        elif active_column and stripped and indent <= active_indent:
            active_column = None
            active_indent = -1

        if "hour.between(0, 23)" in line and "minute.between(0, 59)" in line:
            index.add_evidence("TIME", "TIME", "range", "fallback_bounds", line_no, "high")

        if re.search(r"\bvalue\s*<\s*part_rule\.min_value\b", line) or re.search(
            r"\bvalue\s*>\s*part_rule\.max_value\b",
            line,
        ):
            index.add_evidence("", "", "range", "minmax_check", line_no, "low")

        if "_is_missing_numeric(value)" in line:
            index.add_evidence("", "", "sentinel", "fallback_bounds", line_no, "low")

        if "is_wnd_calm" in line and "=" in line:
            index.add_evidence("WND", "WND", "domain", "special_case", line_no, "medium")
        if "is_od_calm" in line and "=" in line:
            index.add_evidence("", "OD", "domain", "special_case", line_no, "medium")
        if "is_oe_calm" in line and "=" in line:
            index.add_evidence("", "OE", "domain", "special_case", line_no, "medium")

        clamp_match = re.search(
            r'if\s+prefix\s*==\s*"([A-Z0-9]+)".*scaled\s*[<>]=?\s*([+-]?\d+(?:\.\d+)?)',
            line,
        )
        if clamp_match:
            ident = clamp_match.group(1)
            index.add_evidence(ident, identifier_family(ident), "range", "clamp", line_no, "high")

        if active_column:
            between_match = re.search(
                r"series\.between\(\s*([+-]?\d+(?:\.\d+)?)\s*,\s*([+-]?\d+(?:\.\d+)?)\s*\)",
                line,
            )
            if between_match:
                index.add_evidence(active_column, active_column, "range", "fallback_bounds", line_no, "high")
            if "series.isin(" in line:
                rule_type = "allowed_quality" if active_column == "QUALITY_CONTROL" else "domain"
                index.add_evidence(active_column, active_column, rule_type, "strict_gate", line_no, "high")
            sentinel_match = re.search(r'series\s*!=\s*"([^"]+)"', line)
            if sentinel_match:
                token = sentinel_match.group(1)
                if token in {"99999", "9", "None", "nan", ""}:
                    rule_type = "sentinel"
                else:
                    rule_type = "domain"
                index.add_evidence(active_column, active_column, rule_type, "fallback_bounds", line_no, "high")

    return index


def load_constants_module(repo_root: Path):
    src = str(repo_root / "src")
    if src not in sys.path:
        sys.path.insert(0, src)
    import noaa_spec.constants as constants  # type: ignore

    return constants


def ast_literal_str(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def ast_literal_int(node: ast.AST | None) -> int | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, int):
        return node.value
    return None


def expand_identifier_range(start_family: str, start_num: int, end_family: str, end_num: int, width: int) -> list[str]:
    if start_family != end_family:
        return [f"{start_family}{start_num:0{width}d}", f"{end_family}{end_num:0{width}d}"]
    low, high = sorted((start_num, end_num))
    if high - low > 20:
        return [f"{start_family}{low:0{width}d}", f"{start_family}{high:0{width}d}"]
    return [f"{start_family}{idx:0{width}d}" for idx in range(low, high + 1)]


def extract_identifiers_from_line(
    line: str,
    known_identifiers: set[str],
    known_families: set[str],
) -> list[str]:
    normalized = line.replace("\u2013", "-").replace("\u2014", "-")
    found: list[str] = []

    for m in IDENTIFIER_RANGE_RE.finditer(normalized):
        fam_a, num_a, fam_b, num_b = m.groups()
        width = max(len(num_a), len(num_b))
        expanded = expand_identifier_range(fam_a, int(num_a), fam_b, int(num_b), width)
        for item in expanded:
            if item in known_identifiers or identifier_family(item) in known_families:
                found.append(item)

    for match in IDENTIFIER_RE.finditer(normalized):
        token = match.group(0)
        if token in known_identifiers or token in known_families:
            found.append(token)
            continue
        token_match = IDENTIFIER_WITH_DIGIT_RE.fullmatch(token)
        if token_match and token_match.group(1) in known_families:
            found.append(token)

    dedup = sorted(set(found), key=natural_key)
    return dedup


def infer_rule_types_from_text(text: str) -> set[str]:
    lower = text.lower()
    out: set[str] = set()

    if any(k in lower for k in ["min", "max", "range", "out_of_range", "out of range", "boundary", "bounds"]):
        out.add("range")
    if any(k in lower for k in ["sentinel", "missing"]):
        out.add("sentinel")
    if any(k in lower for k in ["quality", "bad_quality", "allowed_quality", "qc code"]):
        out.add("allowed_quality")
    if any(k in lower for k in ["domain", "code", "categorical", "allowed_values", "valid values"]):
        out.add("domain")
    if any(k in lower for k in ["cardinality", "identifier", "suffix", "repeated", "allowlist"]):
        out.add("cardinality")
    if any(k in lower for k in ["width", "fixed-width", "fixed width", "token format", "token width", "pattern"]):
        out.add("width")
    if any(k in lower for k in ["arity", "part count", "truncated", "extra parts", "expected parts"]):
        out.add("arity")

    if not out:
        out.add("unknown")

    return out & RULE_TYPE_SET


def classify_assertion_rule_types(text: str) -> set[str]:
    lower = text.lower()
    out: set[str] = set()

    if any(
        k in lower
        for k in [
            "out_of_range",
            "range_enforced",
            "boundary",
            "just_above",
            "just_below",
            "min",
            "max",
            "between(",
            "<",
            ">",
        ]
    ):
        out.add("range")
    if any(k in lower for k in ["sentinel", "missing", "is_missing_value", "sentinel_missing"]):
        out.add("sentinel")
    if any(k in lower for k in ["bad_quality_code", "quality_rejects", "__qc_reason", "quality"]):
        out.add("allowed_quality")
    if any(k in lower for k in ["invalid_", "domain", "allowed_values", "code domain", "code"]):
        out.add("domain")
    if any(k in lower for k in ["identifier", "suffix", "allowlist", "repeated"]):
        out.add("cardinality")
    if any(k in lower for k in ["arity", "expected", "parts", "truncated", "extra"]):
        out.add("arity")
    if any(k in lower for k in ["token width", "token_width", "malformed_token", "pattern", "fixed-width"]):
        out.add("width")

    return out & RULE_TYPE_SET


def extract_numeric_tokens(text: str) -> set[str]:
    tokens: set[str] = set()
    for raw in NUMERIC_TOKEN_RE.findall(text):
        token = normalize_num_token(raw)
        if token:
            tokens.add(token)
    return tokens


def extract_width_signature_tokens(text: str) -> set[str]:
    lower = text.lower()
    if not any(keyword in lower for keyword in WIDTH_SIGNATURE_KEYWORDS):
        return set()

    tokens: set[str] = set()
    for raw in NUMERIC_TOKEN_RE.findall(text):
        normalized = normalize_num_token(raw)
        parsed = parse_int_token(normalized)
        if parsed is None or parsed < 0:
            continue
        tokens.add(str(parsed))
    return tokens


EXACT_NON_DIGIT_IDENTIFIERS = {
    "DATE",
    "TIME",
    "LATITUDE",
    "LONGITUDE",
    "ELEVATION",
    "CALL_SIGN",
    "REPORT_TYPE",
    "QC_PROCESS",
}


def extract_test_identifiers(
    text: str,
    known_identifiers: set[str],
    known_families: set[str],
) -> tuple[set[str], set[str]]:
    identifiers: set[str] = set()
    families: set[str] = set()
    for token in IDENTIFIER_RE.findall(text):
        if token not in known_identifiers and token not in known_families:
            continue
        is_static_identifier = (
            token in known_identifiers
            and token == token.upper()
            and not IDENTIFIER_WITH_DIGIT_RE.match(token)
            and len(token) >= 3
        )
        if IDENTIFIER_WITH_DIGIT_RE.match(token) or token in EXACT_NON_DIGIT_IDENTIFIERS or is_static_identifier:
            identifiers.add(token)
            families.add(identifier_family(token))
            continue
        if token in known_families:
            families.add(token)

    for token in CONTROL_POS_IDENTIFIER_RE.findall(text):
        if token not in known_identifiers:
            continue
        identifiers.add(token)
        families.add(identifier_family(token))

    for token in EXACT_NON_DIGIT_IDENTIFIERS:
        if token not in known_identifiers:
            continue
        if re.search(rf"(?<![A-Z0-9_]){re.escape(token)}(?![A-Z0-9_])", text):
            identifiers.add(token)
            families.add(identifier_family(token))
    return identifiers, families


def iter_test_functions(tree: ast.AST) -> Iterable[tuple[ast.FunctionDef, str]]:
    if not isinstance(tree, ast.Module):
        return []
    out: list[tuple[ast.FunctionDef, str]] = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name.startswith("test_"):
                    out.append((child, node.name))
        elif isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            out.append((node, ""))
    return out


def parse_tests_evidence(
    tests_path: Path,
    known_identifiers: set[str],
    known_families: set[str],
) -> TestEvidenceIndex:
    source = tests_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(tests_path))
    index = TestEvidenceIndex()

    rel_path = str(tests_path.relative_to(tests_path.parents[1]))
    for node, class_name in iter_test_functions(tree):
        text_parts: list[str] = [node.name, class_name]
        numeric_tokens: set[str] = set()
        width_signature_tokens: set[str] = set()
        assert_segments: list[str] = []
        assertion_rule_types: set[str] = set()

        for sub in ast.walk(node):
            if isinstance(sub, ast.Constant):
                if isinstance(sub.value, str):
                    text_parts.append(sub.value)
                    numeric_tokens.update(extract_numeric_tokens(sub.value))
                    width_signature_tokens.update(extract_width_signature_tokens(sub.value))
                elif isinstance(sub.value, (int, float)):
                    numeric_tokens.add(normalize_num_token(str(sub.value)))
            if isinstance(sub, ast.Assert):
                segment = ast.get_source_segment(source, sub)
                if not segment:
                    try:
                        segment = ast.unparse(sub)
                    except Exception:
                        segment = ""
                if segment:
                    assert_segments.append(segment)
                    text_parts.append(segment)
                    numeric_tokens.update(extract_numeric_tokens(segment))
                    width_signature_tokens.update(extract_width_signature_tokens(segment))
                    assertion_rule_types.update(classify_assertion_rule_types(segment))

        joined = "\n".join(text_parts)
        inferred_rule_types = infer_rule_types_from_text(joined)
        rule_types = (inferred_rule_types | assertion_rule_types) - {"unknown"}
        if not rule_types:
            continue

        if re.search(r"\barity\b", joined.lower()) or re.search(r"truncated payload", joined.lower()) or re.search(
            r"expected\s+\d+\s+parts",
            joined.lower(),
        ):
            index.arity_tests_detected = True

        identifiers, families = extract_test_identifiers(joined, known_identifiers, known_families)
        location = (rel_path, node.lineno)

        for rule_type in sorted(rule_types, key=RULE_TYPE_ORDER.index):
            for identifier in sorted(identifiers, key=natural_key):
                index.add_exact_assertion(identifier, rule_type, location)
                index.add_family_assertion(identifier_family(identifier), rule_type, location)
                for token in sorted(numeric_tokens, key=natural_key):
                    if rule_type == "range":
                        index.add_signature(identifier, rule_type, min_value=token, location=location)
                        index.add_signature(identifier, rule_type, max_value=token, location=location)
                    elif rule_type == "sentinel":
                        index.add_signature(identifier, rule_type, sentinel_values=token, location=location)
                    elif rule_type in {"allowed_quality", "domain"}:
                        index.add_signature(identifier, rule_type, allowed_values_or_codes=token, location=location)
                if rule_type == "width":
                    for token in sorted(width_signature_tokens, key=natural_key):
                        index.add_signature(identifier, rule_type, allowed_values_or_codes=token, location=location)

            if not identifiers and families:
                for family in sorted(families, key=natural_key):
                    index.add_family_assertion(family, rule_type, location)
            if not identifiers and not families:
                index.add_wildcard_assertion(rule_type, location)

    return index


def infer_context_from_line(
    part: str,
    line: str,
    current_identifiers: list[str],
    known_identifiers: set[str],
    known_families: set[str],
) -> list[str]:
    lower = line.lower().strip()

    def strongly_anchored(phrase: str) -> bool:
        return (
            lower.startswith(phrase)
            or lower.startswith(f"identifier: {phrase}")
            or lower.startswith(f"- {phrase}")
            or lower.startswith(f"| {phrase}")
            or lower == phrase
        )

    # Avoid replacing active context with enum-value lines (e.g., "ST: Spring tide").
    if current_identifiers:
        enum_like = re.match(r"^[A-Z0-9][A-Z0-9-]{0,11}\s*[:=]\s+.+$", line)
        if enum_like and "identifier" not in lower and "indicator" not in lower:
            return current_identifiers

    ids = extract_identifiers_from_line(line, known_identifiers, known_families)
    if ids:
        explicit_ids = [value for value in ids if IDENTIFIER_WITH_DIGIT_RE.fullmatch(value)]
        if explicit_ids:
            ids = explicit_ids
        elif current_identifiers and "identifier" not in lower and "indicator" not in lower:
            return current_identifiers
        return ids

    if part == "02":
        for phrase, ident in CONTROL_CONTEXT_MAP.items():
            if strongly_anchored(phrase):
                return [ident]

    if part == "03":
        for phrase, ident in MANDATORY_CONTEXT_MAP.items():
            if strongly_anchored(phrase):
                return [ident]

    # Keep previously inferred context unless a strongly anchored phrase identifies a new section.
    if current_identifiers:
        return current_identifiers

    return current_identifiers


def normalize_section_context_line(value: str) -> str:
    return normalize_text_line(value).strip().lower().rstrip(".")


def infer_identifiers_from_adjacent_structural_context(
    spec_part: str,
    line_idx: int,
    raw_lines: list[str],
    known_identifiers: set[str],
    known_families: set[str],
) -> list[str]:
    """Resolve identifier context for structural width rows lacking active context."""
    for offset in range(1, SECTION_IDENTIFIER_LOOKAHEAD_LINES + 1):
        probe_idx = line_idx + offset
        if probe_idx > len(raw_lines):
            break

        probe_line = normalize_text_line(raw_lines[probe_idx - 1]).strip()
        if not probe_line:
            continue
        if probe_line.startswith("FLD LEN") or probe_line.startswith("POS:"):
            break

        mapped = SECTION_IDENTIFIER_CONTEXT_MAP.get((spec_part, normalize_section_context_line(probe_line)))
        if mapped:
            return [mapped]

        context_ids = infer_context_from_line(spec_part, probe_line, [], known_identifiers, known_families)
        if context_ids:
            return context_ids

        extracted_ids = extract_identifiers_from_line(probe_line, known_identifiers, known_families)
        if extracted_ids:
            explicit_ids = [value for value in extracted_ids if IDENTIFIER_WITH_DIGIT_RE.fullmatch(value)]
            return explicit_ids if explicit_ids else extracted_ids

    return []


def add_row(
    rows: list[SpecRuleRow],
    spec_part: str,
    spec_doc: str,
    spec_file: str,
    spec_line_start: int,
    spec_line_end: int,
    spec_evidence: str,
    identifiers: list[str],
    rule_type: str,
    spec_rule_text: str,
    min_value: str = "",
    max_value: str = "",
    sentinel_values: str = "",
    allowed_values_or_codes: str = "",
) -> None:
    if rule_type not in RULE_TYPE_SET:
        return

    if not identifiers:
        identifiers = ["UNSPECIFIED"]

    for ident in identifiers:
        fam = identifier_family(ident)
        rows.append(
            SpecRuleRow(
                spec_part=spec_part,
                spec_doc=spec_doc,
                spec_file=spec_file,
                spec_line_start=spec_line_start,
                spec_line_end=spec_line_end,
                spec_evidence=spec_evidence,
                identifier=ident,
                identifier_family=fam,
                rule_type=rule_type,
                spec_rule_text=short_text(spec_rule_text),
                min_value=min_value,
                max_value=max_value,
                sentinel_values=sentinel_values,
                allowed_values_or_codes=allowed_values_or_codes,
            )
        )


def segment_spec_doc_lines(raw_lines: list[str]) -> list[SpecPartSegment]:
    if not raw_lines:
        raise SpecSegmentationError("Spec document is empty; cannot segment deterministic markdown.")

    normalized_lines = [normalize_text_line(line).strip() for line in raw_lines]
    anchor_matches: list[tuple[str, str, int]] = []
    previous_line = 0

    for spec_part, anchor_text in SPEC_PART_ANCHORS:
        anchor_line: int | None = None
        for line_no in range(previous_line + 1, len(normalized_lines) + 1):
            if normalized_lines[line_no - 1] == anchor_text:
                anchor_line = line_no
                break
        if anchor_line is None:
            raise SpecSegmentationError(f"Missing required anchor for Part {spec_part}: {anchor_text!r}")
        anchor_matches.append((spec_part, anchor_text, anchor_line))
        previous_line = anchor_line

    for (_, _, prev_line), (part, _, current_line) in zip(anchor_matches, anchor_matches[1:]):
        if current_line <= prev_line:
            raise SpecSegmentationError(
                f"Non-increasing anchor order while segmenting Part {part}: line {current_line} follows {prev_line}"
            )

    late_lines = {part: line for part, _, line in anchor_matches if part in LATE_DOCUMENT_PART_ORDER}
    missing_late_parts = [part for part in LATE_DOCUMENT_PART_ORDER if part not in late_lines]
    if missing_late_parts:
        raise SpecSegmentationError(f"Late-document order check missing parts: {', '.join(missing_late_parts)}")
    late_line_values = [late_lines[part] for part in LATE_DOCUMENT_PART_ORDER]
    if late_line_values != sorted(late_line_values):
        order_repr = ", ".join(f"{part}@{late_lines[part]}" for part in LATE_DOCUMENT_PART_ORDER)
        raise SpecSegmentationError(f"Late-document anchor order is invalid: {order_repr}")

    segments: list[SpecPartSegment] = []
    for idx, (spec_part, anchor_text, anchor_line) in enumerate(anchor_matches):
        next_anchor_line = anchor_matches[idx + 1][2] if idx + 1 < len(anchor_matches) else len(raw_lines) + 1
        end_line = next_anchor_line - 1
        if end_line < anchor_line:
            raise SpecSegmentationError(
                f"Part {spec_part} has an empty or overlapping slice ({anchor_line}-{end_line})"
            )
        segments.append(
            SpecPartSegment(
                spec_part=spec_part,
                anchor_text=anchor_text,
                anchor_line=anchor_line,
                start_line=anchor_line,
                end_line=end_line,
            )
        )

    return segments


def parse_spec_part(
    spec_part: str,
    spec_doc: str,
    spec_file: str,
    raw_lines: list[str],
    part_lines: list[str],
    part_start_line: int,
    known_identifiers: set[str],
    known_families: set[str],
) -> list[SpecRuleRow]:
    rows: list[SpecRuleRow] = []
    current_identifiers: list[str] = []
    block_type: str | None = None
    block_codes: set[str] = set()
    block_identifiers: list[str] = []
    block_start_line = 0
    pending_min_token = ""
    pending_min_identifiers: list[str] = []
    pending_min_line = 0
    part02_active_pos_identifier = ""
    part02_pending_pos_row_indices: list[int] = []

    def to_global_line(local_line: int) -> int:
        return part_start_line + local_line - 1

    def effective_identifiers() -> list[str]:
        if current_identifiers:
            return current_identifiers
        if spec_part == "02" and part02_active_pos_identifier:
            return [part02_active_pos_identifier]
        return current_identifiers

    def evidence(line_start: int, line_end: int) -> str:
        return build_spec_evidence(raw_lines, line_start, line_end)

    def add_extracted_row(
        identifiers: list[str],
        rule_type: str,
        spec_rule_text: str,
        min_value: str = "",
        max_value: str = "",
        sentinel_values: str = "",
        allowed_values_or_codes: str = "",
        line_start: int | None = None,
        line_end: int | None = None,
    ) -> None:
        start_idx = len(rows)
        row_start = to_global_line(idx if line_start is None else line_start)
        row_end = to_global_line(idx if line_end is None else line_end)
        add_row(
            rows,
            spec_part,
            spec_doc,
            spec_file,
            row_start,
            row_end,
            evidence(row_start, row_end),
            identifiers,
            rule_type,
            spec_rule_text,
            min_value=min_value,
            max_value=max_value,
            sentinel_values=sentinel_values,
            allowed_values_or_codes=allowed_values_or_codes,
        )
        if spec_part == "02" and not current_identifiers and part02_active_pos_identifier:
            for row_idx in range(start_idx, len(rows)):
                if rows[row_idx].identifier == part02_active_pos_identifier:
                    part02_pending_pos_row_indices.append(row_idx)

    def flush_block(force_line: int) -> None:
        nonlocal block_type, block_codes, block_identifiers, block_start_line
        if block_type and block_codes and block_identifiers:
            line_end = max(block_start_line, force_line - 1)
            add_extracted_row(
                block_identifiers,
                block_type,
                f"Enumerated codes near line {to_global_line(block_start_line)}",
                allowed_values_or_codes=pipe_join(block_codes),
                line_start=block_start_line,
                line_end=line_end,
            )
        block_type = None
        block_codes = set()
        block_identifiers = []
        block_start_line = force_line

    for idx, raw_line in enumerate(part_lines, start=1):
        line = normalize_text_line(raw_line)
        if not line:
            flush_block(idx)
            if pending_min_token and idx - pending_min_line > 2:
                pending_min_token = ""
                pending_min_identifiers = []
                pending_min_line = 0
            continue

        new_context = infer_context_from_line(
            spec_part,
            line,
            current_identifiers,
            known_identifiers,
            known_families,
        )
        current_identifiers = new_context

        lower = line.lower()
        if spec_part == "02" and line.startswith("POS:"):
            current_identifiers = []
            part02_pending_pos_row_indices = []

        if spec_part == "02":
            pos = POS_RE.search(line)
            if pos:
                start_pos = int(pos.group(1))
                end_pos = int(pos.group(2))
                part02_active_pos_identifier = f"CONTROL_POS_{start_pos}_{end_pos}"
            for phrase, ident in CONTROL_CONTEXT_MAP.items():
                if lower.startswith(phrase):
                    current_identifiers = [ident]
                    if part02_pending_pos_row_indices:
                        for row_idx in part02_pending_pos_row_indices:
                            if row_idx < 0 or row_idx >= len(rows):
                                continue
                            row = rows[row_idx]
                            if not row.identifier.startswith("CONTROL_POS_"):
                                continue
                            if row.rule_type == "width":
                                continue
                            row.identifier = ident
                            row.identifier_family = identifier_family(ident)
                        part02_pending_pos_row_indices = []
                    break

        if pending_min_token and idx - pending_min_line > 3:
            pending_min_token = ""
            pending_min_identifiers = []
            pending_min_line = 0

        if "quality code" in lower:
            flush_block(idx)
            block_type = "allowed_quality"
            block_identifiers = effective_identifiers().copy()
            block_start_line = idx
        elif (
            " code" in lower
            and "quality code" not in lower
            and "identifier" not in lower
            and "table" not in lower
        ):
            flush_block(idx)
            block_type = "domain"
            block_identifiers = effective_identifiers().copy()
            block_start_line = idx
        elif line.startswith("FLD LEN") or line.startswith("POS:"):
            flush_block(idx)

        enum_match = re.match(r"^([A-Z0-9]{1,6})\s*=\s*", line)
        if enum_match and block_type:
            block_codes.add(enum_match.group(1))
        elif enum_match and not block_type:
            if "quality" in lower:
                block_type = "allowed_quality"
            else:
                block_type = "domain"
            block_identifiers = effective_identifiers().copy()
            block_codes.add(enum_match.group(1))
            block_start_line = idx

        mm = MIN_MAX_INLINE_RE.search(line)
        min_only = MIN_ONLY_RE.search(line)
        max_only = MAX_ONLY_RE.search(line)

        if mm:
            min_token = normalize_num_token(mm.group(1))
            max_token = normalize_num_token(mm.group(2))
            add_extracted_row(
                effective_identifiers(),
                "range",
                f"MIN {min_token} MAX {max_token}",
                min_value=min_token,
                max_value=max_token,
            )
            pending_min_token = ""
            pending_min_identifiers = []
            pending_min_line = 0
        elif min_only and max_only:
            min_token = normalize_num_token(min_only.group(1))
            max_token = normalize_num_token(max_only.group(1))
            add_extracted_row(
                effective_identifiers(),
                "range",
                f"MIN {min_token} MAX {max_token}",
                min_value=min_token,
                max_value=max_token,
            )
            pending_min_token = ""
            pending_min_identifiers = []
            pending_min_line = 0
        elif min_only:
            pending_min_token = normalize_num_token(min_only.group(1))
            pending_min_identifiers = current_identifiers.copy()
            pending_min_line = idx
        elif max_only:
            max_token = normalize_num_token(max_only.group(1))
            if pending_min_token and idx - pending_min_line <= 3:
                add_extracted_row(
                    pending_min_identifiers or effective_identifiers(),
                    "range",
                    f"MIN {pending_min_token} MAX {max_token}",
                    min_value=pending_min_token,
                    max_value=max_token,
                    line_start=pending_min_line,
                    line_end=idx,
                )
            pending_min_token = ""
            pending_min_identifiers = []
            pending_min_line = 0

        sentinels: set[str] = set()
        sentinels.update(normalize_num_token(v) for v in MISSING_EQ_RE.findall(line))
        sentinels.update(normalize_num_token(v) for v in EQ_MISSING_RE.findall(line))
        if sentinels:
            add_extracted_row(
                effective_identifiers(),
                "sentinel",
                f"Missing sentinels {pipe_join(sentinels)}",
                sentinel_values=pipe_join(sentinels),
            )

        fld = FLD_LEN_RE.search(line)
        if fld:
            width = fld.group(1)
            width_identifiers = effective_identifiers().copy()
            if not width_identifiers and width == "3":
                width_identifiers = infer_identifiers_from_adjacent_structural_context(
                    spec_part,
                    idx,
                    part_lines,
                    known_identifiers,
                    known_families,
                )
            add_extracted_row(
                width_identifiers,
                "width",
                f"FLD LEN {width}",
                allowed_values_or_codes=width,
            )

        pos = POS_RE.search(line)
        if pos:
            start_pos = int(pos.group(1))
            end_pos = int(pos.group(2))
            width = end_pos - start_pos + 1
            width_identifiers = effective_identifiers().copy()
            if not width_identifiers and spec_part == "03":
                width_identifiers = infer_identifiers_from_adjacent_structural_context(
                    spec_part,
                    idx,
                    part_lines,
                    known_identifiers,
                    known_families,
                )
            add_extracted_row(
                width_identifiers,
                "width",
                f"POS {start_pos}-{end_pos} width {width}",
                allowed_values_or_codes=str(width),
            )

        if current_identifiers and "indicator" in lower and ("up to" in lower or "-" in line):
            up_to_match = UP_TO_RE.search(line)
            if up_to_match:
                limit = up_to_match.group(1)
                global_idx = to_global_line(idx)
                add_row(
                    rows,
                    spec_part,
                    spec_doc,
                    spec_file,
                    global_idx,
                    global_idx,
                    evidence(global_idx, global_idx),
                    current_identifiers,
                    "cardinality",
                    short_text(line),
                    allowed_values_or_codes=f"1-{limit}",
                )
            elif len(current_identifiers) > 1:
                global_idx = to_global_line(idx)
                add_row(
                    rows,
                    spec_part,
                    spec_doc,
                    spec_file,
                    global_idx,
                    global_idx,
                    evidence(global_idx, global_idx),
                    current_identifiers,
                    "cardinality",
                    short_text(line),
                    allowed_values_or_codes=f"1-{len(current_identifiers)}",
                )

        if "following item" in lower and current_identifiers:
            item_count = 0
            for j in range(idx, len(part_lines)):
                probe = normalize_text_line(part_lines[j])
                if not probe:
                    if item_count > 0:
                        break
                    continue
                probe_lower = probe.lower()
                if (
                    probe.startswith("FLD LEN")
                    or probe.startswith("POS:")
                    or probe.startswith("---")
                    or "dom:" in probe_lower
                    or "scaling factor" in probe_lower
                    or "min:" in probe_lower
                    or "max:" in probe_lower
                ):
                    if item_count > 0:
                        break
                    continue
                if re.match(r"^[A-Z0-9]{1,6}\s*=", probe):
                    if item_count > 0:
                        break
                    continue
                if probe.startswith("▀"):
                    if item_count > 0:
                        break
                    continue
                if "identifier" in probe_lower and item_count > 0:
                    break
                if any(k in probe_lower for k in ["note:", "units:"]):
                    continue
                item_count += 1
            if item_count > 0:
                global_idx = to_global_line(idx)
                add_row(
                    rows,
                    spec_part,
                    spec_doc,
                    spec_file,
                    global_idx,
                    global_idx,
                    evidence(global_idx, global_idx),
                    current_identifiers,
                    "arity",
                    short_text(line),
                    allowed_values_or_codes=str(item_count),
                )

    flush_block(len(part_lines) + 1)
    return rows


def parse_spec_doc(spec_path: Path, known_identifiers: set[str], known_families: set[str]) -> list[SpecRuleRow]:
    spec_doc = spec_path.name
    spec_file = spec_path.name
    raw_lines = spec_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    segments = segment_spec_doc_lines(raw_lines)

    rows: list[SpecRuleRow] = []
    for segment in segments:
        part_lines = raw_lines[segment.start_line - 1 : segment.end_line]
        rows.extend(
            parse_spec_part(
                segment.spec_part,
                spec_doc,
                spec_file,
                raw_lines,
                part_lines,
                segment.start_line,
                known_identifiers,
                known_families,
            )
        )
    return rows


def filter_known_spec_extraction_errors(
    rows: list[SpecRuleRow],
    constants_module,
) -> list[SpecRuleRow]:
    """Drop rows produced by known parser-context attribution errors.

    These rows are not actionable implementation gaps; they come from section-header
    and subsection tables that were attributed to the wrong identifier context.
    """

    legacy_eqd_codes = set(getattr(constants_module, "LEGACY_EQD_PARAMETER_CODES", set()))
    rem_type_codes = set(getattr(constants_module, "REM_TYPE_CODES", set()))
    qprd_reason_codes = {str(v) for v in range(0, 8)}

    filtered: list[SpecRuleRow] = []
    for row in rows:
        if row.row_kind != "spec_rule":
            filtered.append(row)
            continue

        allowed_tokens = set(parse_pipe_tokens(row.allowed_values_or_codes))

        # Part 30: Reason/legacy EQD parameter tables apply to Q/P/R/C/D blocks,
        # not Nxx element-schema rows.
        if row.spec_part == "30" and row.identifier_family == "N" and row.rule_type == "domain":
            if allowed_tokens and (allowed_tokens.issubset(qprd_reason_codes) or bool(allowed_tokens & legacy_eqd_codes)):
                continue

        # Part 30: Remarks-section rows were previously attributed to WJ1.
        if row.spec_part == "30" and row.identifier == "WJ1":
            if row.rule_type == "range" and row.min_value == "001" and row.max_value == "999":
                continue
            if row.rule_type == "allowed_quality" and "EQD" in allowed_tokens:
                continue
            if row.rule_type == "domain" and allowed_tokens:
                if "REM" in allowed_tokens or allowed_tokens.issubset(rem_type_codes):
                    continue

        # Part 28: Identifier-list prose (MV1-MV7 / MW1-MW7) is not a value-domain rule.
        if row.spec_part == "28" and row.identifier == "MV1" and row.rule_type == "domain" and allowed_tokens:
            if any(token.startswith("MV") for token in allowed_tokens) or any(token.startswith("MW") for token in allowed_tokens):
                continue

        filtered.append(row)

    return filtered


def merge_duplicate_rows(rows: list[SpecRuleRow]) -> list[SpecRuleRow]:
    merged: dict[tuple[str, ...], SpecRuleRow] = {}
    for row in rows:
        key = row.key()
        existing = merged.get(key)
        if existing is None:
            merged[key] = row
            continue
        existing.notes.update(row.notes)

    return sorted(merged.values(), key=lambda r: r.sort_key())


def parse_float_safe(value: str) -> float | None:
    if value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def coverage_in_constants_for_row(
    row: SpecRuleRow,
    constants_module,
    constants_ast: ConstantsAstIndex,
) -> tuple[bool, str, str]:
    get_field_rule = getattr(constants_module, "get_field_rule")
    known_identifiers: set[str] = set(getattr(constants_module, "KNOWN_IDENTIFIERS", set()))
    repeated_ranges: Mapping[str, range] = getattr(constants_module, "_REPEATED_IDENTIFIER_RANGES", {})
    legacy_eqd_codes = normalized_token_set(getattr(constants_module, "LEGACY_EQD_PARAMETER_CODES", set()))
    eqd_unit_codes = normalized_token_set(getattr(constants_module, "EQD_UNIT_CODES", set()))

    candidates: list[str] = []
    if row.identifier and row.identifier != "UNSPECIFIED":
        candidates.append(row.identifier)
    if row.identifier_family and row.identifier_family != row.identifier:
        candidates.append(row.identifier_family)
    if row.identifier in known_identifiers:
        candidates.append(row.identifier)
    if row.identifier_family in known_identifiers:
        candidates.append(row.identifier_family)
    if f"{row.identifier_family}1" in known_identifiers:
        candidates.append(f"{row.identifier_family}1")

    seen = set()
    normalized_candidates: list[str] = []
    for cand in candidates:
        if cand not in seen:
            normalized_candidates.append(cand)
            seen.add(cand)

    rules: list[tuple[str, object]] = []
    for cand in normalized_candidates:
        try:
            rule = get_field_rule(cand)
        except Exception:
            rule = None
        if rule is not None:
            rules.append((cand, rule))

    def part_location(prefix: str, part_idx: int, keyword: str) -> str:
        lookup_prefixes = [prefix]
        family_prefix = identifier_family(prefix)
        if family_prefix != prefix:
            lookup_prefixes.append(family_prefix)

        line = None
        for lookup_prefix in lookup_prefixes:
            line = constants_ast.part_keyword_lines.get((lookup_prefix, int(part_idx), keyword))
            if line is not None:
                break
        if line is None:
            for lookup_prefix in lookup_prefixes:
                line = constants_ast.part_lines.get((lookup_prefix, int(part_idx)))
                if line is not None:
                    break
        return f"src/noaa_spec/constants.py:{line}" if line else ""

    if row.rule_type == "cardinality":
        if row.identifier_family in repeated_ranges:
            line = constants_ast.repeated_range_lines.get(row.identifier_family)
            return True, (f"src/noaa_spec/constants.py:{line}" if line else ""), "repeated_identifier_range"
        if row.identifier.startswith(tuple("QPRCDN")) or row.identifier_family.startswith(tuple("QPRCDN")):
            line = constants_ast.function_lines.get("is_valid_eqd_identifier")
            return (
                line is not None,
                (f"src/noaa_spec/constants.py:{line}" if line else ""),
                "repeated_identifier_range" if line is not None else "none",
            )
        line = constants_ast.function_lines.get("is_valid_repeated_identifier")
        if line is not None and row.identifier_family in constants_ast.repeated_range_lines:
            return True, f"src/noaa_spec/constants.py:{line}", "repeated_identifier_range"
        return False, "", "none"

    if row.rule_type == "arity":
        line = constants_ast.function_lines.get("get_expected_part_count")
        if line is not None and rules:
            return True, f"src/noaa_spec/constants.py:{line}", "strict_gate_arity"
        return False, "", "none"

    if row.rule_type == "width":
        for cand, rule in rules:
            parts = getattr(rule, "parts", {})
            for part_idx, part_rule in parts.items():
                token_width = getattr(part_rule, "token_width", None)
                token_pattern = getattr(part_rule, "token_pattern", None)
                if token_width is not None or token_pattern is not None:
                    line = constants_ast.part_keyword_lines.get((cand, int(part_idx), "token_width"))
                    if line is None:
                        line = constants_ast.part_keyword_lines.get((identifier_family(cand), int(part_idx), "token_width"))
                    if line is None:
                        line = constants_ast.part_lines.get((cand, int(part_idx)))
                    if line is None:
                        line = constants_ast.part_lines.get((identifier_family(cand), int(part_idx)))
                    return True, (f"src/noaa_spec/constants.py:{line}" if line else ""), "strict_gate_width"
        return False, "", "none"

    if not rules:
        return False, "", "none"

    spec_min = parse_float_safe(row.min_value)
    spec_max = parse_float_safe(row.max_value)
    sentinel_set = normalized_token_set(row.sentinel_values.split("|")) if row.sentinel_values else set()
    allowed_set = normalized_token_set(row.allowed_values_or_codes.split("|")) if row.allowed_values_or_codes else set()

    for cand, rule in rules:
        parts = getattr(rule, "parts", {})
        for part_idx, part_rule in parts.items():
            key_prefix = cand
            allowed_values_raw = set(getattr(part_rule, "allowed_values", None) or [])
            missing_values_raw = set(getattr(part_rule, "missing_values", None) or [])
            allowed_quality_raw = set(getattr(part_rule, "allowed_quality", None) or [])
            allowed_values = normalized_token_set(allowed_values_raw)
            missing_values = normalized_token_set(missing_values_raw)
            allowed_quality = normalized_token_set(allowed_quality_raw)

            if row.rule_type == "range":
                min_value = getattr(part_rule, "min_value", None)
                max_value = getattr(part_rule, "max_value", None)
                if min_value is None or max_value is None:
                    pass
                else:
                    exact_match = True
                    if spec_min is not None:
                        exact_match = exact_match and abs(float(min_value) - spec_min) < 1e-9
                    if spec_max is not None:
                        exact_match = exact_match and abs(float(max_value) - spec_max) < 1e-9
                    if exact_match or (spec_min is None and spec_max is None):
                        return True, part_location(key_prefix, part_idx, "min_value"), "field_rule_minmax"

                    # Keep mismatch rows visible elsewhere, but still acknowledge
                    # implementation when the rule enforces overlapping bounds.
                    if spec_min is not None and spec_max is not None:
                        if not (float(max_value) < spec_min or float(min_value) > spec_max):
                            return True, part_location(key_prefix, part_idx, "min_value"), "field_rule_minmax_overlap"

                if spec_min is not None and spec_max is not None:
                    spec_min_int = float_to_int_token(spec_min)
                    spec_max_int = float_to_int_token(spec_max)
                    bounds = contiguous_numeric_bounds(allowed_values_raw)
                    if bounds is not None and spec_min_int is not None and spec_max_int is not None:
                        low, high, contiguous = bounds
                        if contiguous and low == spec_min_int and high == spec_max_int:
                            return (
                                True,
                                part_location(key_prefix, part_idx, "allowed_values"),
                                "field_rule_allowed_values_range",
                            )
                        if contiguous and abs(low - spec_min_int) <= 1 and abs(high - spec_max_int) <= 1:
                            return (
                                True,
                                part_location(key_prefix, part_idx, "allowed_values"),
                                "field_rule_allowed_values_near_range",
                            )

                    quality_bounds = contiguous_numeric_bounds(allowed_quality_raw)
                    if quality_bounds is not None and spec_min_int is not None and spec_max_int is not None:
                        q_low, q_high, q_contiguous = quality_bounds
                        if q_contiguous and q_low == spec_min_int and q_high == spec_max_int:
                            return (
                                True,
                                part_location(key_prefix, part_idx, "allowed_quality"),
                                "field_rule_allowed_quality_range",
                            )

                    allowed_pattern = getattr(part_rule, "allowed_pattern", None)
                    if pattern_supports_range(allowed_pattern, spec_min, spec_max):
                        return (
                            True,
                            part_location(key_prefix, part_idx, "allowed_pattern"),
                            "field_rule_pattern_range",
                        )

            if row.rule_type == "sentinel":
                if not missing_values and not allowed_quality and not allowed_values:
                    continue
                if not sentinel_set:
                    if missing_values:
                        return True, part_location(key_prefix, part_idx, "missing_values"), "field_rule_sentinel"
                    continue
                if sentinel_set.intersection(missing_values):
                    return True, part_location(key_prefix, part_idx, "missing_values"), "field_rule_sentinel"
                if sentinel_set.intersection(allowed_quality):
                    return True, part_location(key_prefix, part_idx, "allowed_quality"), "field_rule_sentinel_quality"
                if sentinel_set.intersection(allowed_values):
                    return True, part_location(key_prefix, part_idx, "allowed_values"), "field_rule_sentinel_values"
                for sentinel_token in sentinel_set:
                    if any(repeated_token_match(sentinel_token, missing_token) for missing_token in missing_values):
                        return (
                            True,
                            part_location(key_prefix, part_idx, "missing_values"),
                            "field_rule_sentinel_repeated_pattern",
                        )

            if row.rule_type == "allowed_quality":
                if not allowed_quality and not allowed_values:
                    continue
                if not allowed_set or allowed_set.intersection(allowed_quality):
                    return (
                        True,
                        part_location(key_prefix, part_idx, "allowed_quality"),
                        "field_rule_allowed_quality",
                    )
                if allowed_set.intersection(allowed_values):
                    return (
                        True,
                        part_location(key_prefix, part_idx, "allowed_values"),
                        "field_rule_allowed_quality_as_values",
                    )

            if row.rule_type == "domain":
                allowed_pattern = getattr(part_rule, "allowed_pattern", None)
                if allowed_pattern is not None:
                    return True, part_location(key_prefix, part_idx, "allowed_pattern"), "field_rule_domain_pattern"
                if not allowed_values and not allowed_quality and not missing_values:
                    continue
                if not allowed_set:
                    if allowed_values:
                        return True, part_location(key_prefix, part_idx, "allowed_values"), "field_rule_domain_values"
                    if allowed_quality:
                        return True, part_location(key_prefix, part_idx, "allowed_quality"), "field_rule_domain_quality"
                    if missing_values:
                        return True, part_location(key_prefix, part_idx, "missing_values"), "field_rule_domain_missing"
                    continue
                if allowed_set.intersection(allowed_values):
                    return True, part_location(key_prefix, part_idx, "allowed_values"), "field_rule_domain_values"
                if allowed_set.intersection(allowed_quality):
                    return True, part_location(key_prefix, part_idx, "allowed_quality"), "field_rule_domain_quality"
                if allowed_set.intersection(missing_values):
                    return True, part_location(key_prefix, part_idx, "missing_values"), "field_rule_domain_missing"

                # EQD parameter domains are validated via helper constants and cleaning logic.
                if row.identifier_family in {"Q", "P", "R", "C", "D"} and allowed_set.intersection(legacy_eqd_codes):
                    line = constants_ast.function_lines.get("get_field_rule")
                    return (
                        line is not None,
                        (f"src/noaa_spec/constants.py:{line}" if line else ""),
                        "eqd_parameter_domain",
                    )
                if row.identifier_family == "N" and allowed_set.intersection(eqd_unit_codes):
                    line = constants_ast.function_lines.get("get_field_rule")
                    return (
                        line is not None,
                        (f"src/noaa_spec/constants.py:{line}" if line else ""),
                        "eqd_unit_domain",
                    )

    # Fallback signal for range rules: if any range exists for candidate identifier
    # and the spec row does not carry explicit bounds.
    if row.rule_type == "range":
        if spec_min is None and spec_max is None:
            for cand, rule in rules:
                parts = getattr(rule, "parts", {})
                for part_idx, part_rule in parts.items():
                    min_value = getattr(part_rule, "min_value", None)
                    max_value = getattr(part_rule, "max_value", None)
                    if min_value is not None and max_value is not None:
                        return True, part_location(cand, part_idx, "min_value"), "field_rule_minmax"

    return False, "", "none"


def equivalent_rule_types(rule_type: str) -> set[str]:
    out = {rule_type}
    if rule_type == "allowed_quality":
        out.add("domain")
    elif rule_type == "domain":
        out.add("allowed_quality")
    return out


def evidence_sort_key(evidence: CleaningEvidence) -> tuple[int, int, int]:
    evidence_kind_rank = {
        "clamp": 6,
        "minmax_check": 5,
        "special_case": 4,
        "strict_gate": 3,
        "fallback_bounds": 2,
        "parse_reject": 1,
    }.get(evidence.evidence_kind, 0)
    location_line = 0
    if evidence.location and ":" in evidence.location:
        raw_line = evidence.location.rsplit(":", 1)[-1]
        if raw_line.isdigit():
            location_line = -int(raw_line)
    return (
        IMPLEMENTATION_CONFIDENCE_ORDER.get(evidence.confidence, 0),
        evidence_kind_rank,
        location_line,
    )


def best_cleaning_evidence(candidates: list[CleaningEvidence]) -> CleaningEvidence | None:
    if not candidates:
        return None
    return max(candidates, key=evidence_sort_key)


def coverage_in_cleaning_for_row(
    row: SpecRuleRow,
    cleaning_index: CleaningIndex,
    constants_implemented: bool,
) -> tuple[bool, str, str, str]:
    if row.identifier == "UNSPECIFIED":
        return False, "", "low", "none"

    rule_types = equivalent_rule_types(row.rule_type)
    exact_candidates: list[CleaningEvidence] = []
    family_candidates: list[CleaningEvidence] = []
    for evidence in cleaning_index.evidence:
        if evidence.rule_type not in rule_types:
            continue
        if evidence.identifier and evidence.identifier == row.identifier:
            exact_candidates.append(evidence)
            continue
        if evidence.identifier_family and evidence.identifier_family == row.identifier_family:
            if evidence.identifier and evidence.identifier != row.identifier and evidence.confidence == "high":
                continue
            family_candidates.append(evidence)

    selected = best_cleaning_evidence(exact_candidates)
    if selected is not None:
        return True, selected.location, selected.confidence, f"exact_{selected.evidence_kind}"

    selected = best_cleaning_evidence(family_candidates)
    if selected is not None:
        return True, selected.location, selected.confidence, f"family_{selected.evidence_kind}"

    if (
        row.rule_type == "domain"
        and constants_implemented
        and cleaning_index.generic_domain_line is not None
    ):
        return (
            True,
            f"src/noaa_spec/cleaning.py:{cleaning_index.generic_domain_line}",
            "medium",
            "global_domain_gate",
        )

    return False, "", "low", "none"


def enforcement_layer(
    implemented_in_constants: bool,
    implemented_in_cleaning: bool,
) -> str:
    if implemented_in_constants and implemented_in_cleaning:
        return "both"
    if implemented_in_constants:
        return "constants_only"
    if implemented_in_cleaning:
        return "cleaning_only"
    return "neither"


def normalize_test_match_strength(match_strength: str) -> str:
    return match_strength if match_strength in TEST_MATCH_STRENGTH_SET else "none"


def augment_known_test_identifiers(
    known_identifiers: set[str],
    known_families: set[str],
    rows: Iterable[SpecRuleRow],
) -> tuple[set[str], set[str]]:
    identifiers = set(known_identifiers)
    families = set(known_families)

    for row in rows:
        if row.row_kind not in METRIC_ROW_KINDS:
            continue
        identifier = (row.identifier or "").strip()
        if not identifier or identifier == "UNSPECIFIED":
            continue
        identifiers.add(identifier)
        families.add(identifier_family(identifier))

    identifiers.update(families)
    return identifiers, families


def apply_test_match_result(
    row: SpecRuleRow,
    match_strength: str,
    match_location: tuple[str, int] | None,
) -> None:
    strength = normalize_test_match_strength(match_strength)
    row.test_match_strength = strength
    row.test_covered_any = strength != "none"
    row.test_covered_strict = strength in STRICT_TEST_MATCH_STRENGTHS
    # Backward-compatible alias for existing consumers.
    row.test_covered = row.test_covered_any

    if row.test_covered_any and match_location:
        test_path, line = match_location
        row.test_location = f"{test_path}:{line}"
    else:
        row.test_location = ""

    row.notes.add(f"test_match={strength}")


def apply_coverage(
    rows: list[SpecRuleRow],
    constants_module,
    constants_ast: ConstantsAstIndex,
    cleaning_index: CleaningIndex,
    test_index: TestEvidenceIndex,
) -> list[SpecRuleRow]:
    for row in rows:
        constants_implemented, constants_location, constants_reason = coverage_in_constants_for_row(
            row,
            constants_module,
            constants_ast,
        )
        cleaning_implemented, cleaning_location, cleaning_confidence, cleaning_reason = coverage_in_cleaning_for_row(
            row,
            cleaning_index,
            constants_implemented,
        )

        row.implemented_in_constants = constants_implemented
        row.constants_location = constants_location
        row.implemented_in_cleaning = cleaning_implemented
        row.cleaning_location = cleaning_location
        row.implementation_confidence = (
            cleaning_confidence if cleaning_confidence in IMPLEMENTATION_CONFIDENCE_VALUES else "low"
        )
        row.enforcement_layer = enforcement_layer(constants_implemented, cleaning_implemented)
        row.code_implemented = constants_implemented or cleaning_implemented
        row.code_location = constants_location or cleaning_location
        row.notes.add(f"coverage_reason_constants={constants_reason}")
        row.notes.add(f"coverage_reason_cleaning={cleaning_reason}")

        if row.row_kind == "synthetic":
            apply_test_match_result(row, "none", None)
        else:
            test_location, match_reason = test_index.find(
                row.identifier,
                row.identifier_family,
                row.rule_type,
                row.min_value,
                row.max_value,
                row.sentinel_values,
                row.allowed_values_or_codes,
            )
            apply_test_match_result(row, match_reason, test_location)

        if row.identifier == "UNSPECIFIED":
            row.notes.add("synthetic_unmapped")

    return rows


def write_csv(path: Path, rows: list[SpecRuleRow]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS, lineterminator="\n")
        writer.writeheader()
        for row in sorted(rows, key=lambda r: r.sort_key()):
            writer.writerow(row.csv_record())


def pct(num: int, den: int) -> str:
    if den == 0:
        return "0.0%"
    return f"{(100.0 * num / den):.1f}%"


def note_has(row: SpecRuleRow, token: str) -> bool:
    return token in row.notes


def row_gap_score(row: SpecRuleRow) -> int:
    score = 0
    if not row.code_implemented:
        score += 20
    if not row.test_covered_strict:
        score += 10
    if row.rule_type in {"range", "cardinality", "arity", "width"}:
        score += 3
    if note_has(row, "synthetic_unmapped") or row.identifier == "UNSPECIFIED":
        score -= 30
    return score


def pointer_for_gap(row: SpecRuleRow, cleaning_index: CleaningIndex) -> str:
    if row.code_location:
        return row.code_location
    if row.cleaning_location:
        return row.cleaning_location
    if row.constants_location:
        return row.constants_location
    if row.rule_type == "arity" and cleaning_index.strict_arity_line:
        return f"src/noaa_spec/cleaning.py:{cleaning_index.strict_arity_line}"
    if row.rule_type == "width" and cleaning_index.strict_width_line:
        return f"src/noaa_spec/cleaning.py:{cleaning_index.strict_width_line}"
    return f"src/noaa_spec/constants.py (FIELD_RULES for {row.identifier_family})"


def format_table(headers: list[str], rows: list[list[str]]) -> str:
    def esc(cell: str) -> str:
        return cell.replace("|", "\\|")

    out = []
    out.append("| " + " | ".join(esc(v) for v in headers) + " |")
    out.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for row in rows:
        out.append("| " + " | ".join(esc(v) for v in row) + " |")
    return "\n".join(out)


def bool_flag(value: bool) -> str:
    return "TRUE" if value else "FALSE"


def is_wildcard_only_row(row: SpecRuleRow) -> bool:
    return row.test_covered_any and not row.test_covered_strict


def is_real_gap_row(row: SpecRuleRow) -> bool:
    return not row.code_implemented or not row.test_covered_strict


def is_actionable_real_gap_row(row: SpecRuleRow) -> bool:
    if row.identifier == "UNSPECIFIED":
        return False
    if "synthetic_unmapped" in row.notes:
        return False
    return True


def real_gap_sort_key(row: SpecRuleRow) -> tuple[object, ...]:
    return (
        0 if row.enforcement_layer == "neither" else 1,
        0 if not row.code_implemented else 1,
        -row_gap_score(row),
        row.sort_key(),
    )


def short_notes(row: SpecRuleRow, limit: int = 140) -> str:
    return short_text(";".join(sorted(row.notes)), limit=limit)


def ranked_real_gap_table_rows(group: list[SpecRuleRow]) -> list[list[str]]:
    rows_out: list[list[str]] = []
    for rank, row in enumerate(group, start=1):
        rows_out.append(
            [
                str(rank),
                row.spec_part,
                row.identifier,
                row.rule_type,
                row.enforcement_layer,
                bool_flag(row.code_implemented),
                bool_flag(row.test_covered_strict),
                bool_flag(row.test_covered_any),
                normalize_test_match_strength(row.test_match_strength),
                short_notes(row),
            ]
        )
    if not rows_out:
        rows_out.append(["-", "-", "-", "-", "-", "-", "-", "-", "-", "(none)"])
    return rows_out


def build_report(
    rows: list[SpecRuleRow],
    report_path: Path,
    arity_tests_detected: bool,
) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    extracted_rows = [row for row in rows if row.row_kind in EXTRACTED_ROW_KINDS]
    coverage_rows = [row for row in rows if row.row_kind in METRIC_ROW_KINDS]
    structural_rows_list = [row for row in rows if row.row_kind == ROW_KIND_STRUCTURAL]
    documentation_rows_list = [row for row in rows if row.row_kind == ROW_KIND_DOCUMENTATION]
    total = len(extracted_rows)
    metric_rows = [row for row in coverage_rows if row.rule_type in METRIC_RULE_TYPES]
    total_metric = len(metric_rows)
    unknown_excluded = len(coverage_rows) - total_metric
    implemented = sum(1 for r in metric_rows if r.code_implemented)
    tested_any = sum(1 for r in metric_rows if r.test_covered_any)
    tested_strict = sum(1 for r in metric_rows if r.test_covered_strict)
    strict_count = tested_strict
    wildcard_only_rows = [r for r in metric_rows if is_wildcard_only_row(r)]
    wildcard_only_count = len(wildcard_only_rows)
    any_non_wild_count = sum(
        1
        for r in metric_rows
        if r.test_covered_any and normalize_test_match_strength(r.test_match_strength) != "wildcard_assertion"
    )

    layer_counter = Counter(r.enforcement_layer for r in metric_rows)
    cleaning_implemented_rows = [r for r in metric_rows if r.implemented_in_cleaning]
    cleaning_confidence_counter = Counter(
        r.implementation_confidence
        for r in cleaning_implemented_rows
        if r.implementation_confidence in IMPLEMENTATION_CONFIDENCE_VALUES
    )
    tested_any_rows = [r for r in metric_rows if r.test_covered_any]
    tested_match_counter = Counter(normalize_test_match_strength(r.test_match_strength) for r in tested_any_rows)
    match_strength_counter = Counter(normalize_test_match_strength(r.test_match_strength) for r in metric_rows)
    wildcard_only_by_part = Counter(r.spec_part for r in wildcard_only_rows)
    wildcard_only_by_rule_type = Counter(r.rule_type for r in wildcard_only_rows)

    by_part: dict[str, list[SpecRuleRow]] = defaultdict(list)
    by_family: dict[str, list[SpecRuleRow]] = defaultdict(list)
    by_type: dict[str, list[SpecRuleRow]] = defaultdict(list)

    for row in coverage_rows:
        by_part[row.spec_part].append(row)
        by_family[row.identifier_family].append(row)
        by_type[row.rule_type].append(row)

    part_rows: list[list[str]] = []
    for part in [f"{i:02d}" for i in range(1, 31)]:
        group = by_part.get(part, [])
        metric_group = [r for r in group if r.rule_type in METRIC_RULE_TYPES]
        part_implemented = sum(1 for r in metric_group if r.code_implemented)
        part_tested_strict = sum(1 for r in metric_group if r.test_covered_strict)
        part_tested_any = sum(1 for r in metric_group if r.test_covered_any)
        part_rows.append(
            [
                part,
                str(len(group)),
                str(len(metric_group)),
                str(part_implemented),
                str(part_tested_strict),
                str(part_tested_any),
                pct(part_implemented, len(metric_group)),
                pct(part_tested_strict, len(metric_group)),
                pct(part_tested_any, len(metric_group)),
            ]
        )

    family_rows: list[list[str]] = []
    for family in sorted(by_family, key=natural_key):
        group = by_family[family]
        metric_group = [r for r in group if r.rule_type in METRIC_RULE_TYPES]
        family_implemented = sum(1 for r in metric_group if r.code_implemented)
        family_tested_strict = sum(1 for r in metric_group if r.test_covered_strict)
        family_tested_any = sum(1 for r in metric_group if r.test_covered_any)
        family_rows.append(
            [
                family,
                str(len(group)),
                str(len(metric_group)),
                str(family_implemented),
                str(family_tested_strict),
                str(family_tested_any),
                pct(family_implemented, len(metric_group)),
                pct(family_tested_strict, len(metric_group)),
                pct(family_tested_any, len(metric_group)),
            ]
        )

    type_rows: list[list[str]] = []
    for rule_type in RULE_TYPE_ORDER:
        group = by_type.get(rule_type, [])
        type_implemented = sum(1 for r in group if r.code_implemented)
        type_tested_strict = sum(1 for r in group if r.test_covered_strict)
        type_tested_any = sum(1 for r in group if r.test_covered_any)
        if rule_type in METRIC_RULE_TYPES:
            type_rows.append(
                [
                    rule_type,
                    str(len(group)),
                    str(type_implemented),
                    str(type_tested_strict),
                    str(type_tested_any),
                    pct(type_implemented, len(group)),
                    pct(type_tested_strict, len(group)),
                    pct(type_tested_any, len(group)),
                ]
            )
        else:
            type_rows.append(
                [
                    rule_type,
                    str(len(group)),
                    str(type_implemented),
                    str(type_tested_strict),
                    str(type_tested_any),
                    "excluded",
                    "excluded",
                    "excluded",
                ]
            )

    strict_gap_rows = [r for r in metric_rows if is_real_gap_row(r)]
    actionable_strict_gap_rows = [r for r in strict_gap_rows if is_actionable_real_gap_row(r)]
    ranked_real_gaps = sorted(actionable_strict_gap_rows, key=real_gap_sort_key)
    top_50_real_gaps = ranked_real_gaps[:50]

    implementation_gaps_top_25 = [
        row for row in ranked_real_gaps if (not row.code_implemented and not row.test_covered_strict)
    ][:25]
    missing_tests_top_25 = [
        row for row in ranked_real_gaps if (row.code_implemented and not row.test_covered_strict)
    ][:25]

    wildcard_part_rows: list[list[str]] = []
    for part in [f"{i:02d}" for i in range(1, 31)]:
        count = wildcard_only_by_part.get(part, 0)
        if count == 0:
            continue
        wildcard_part_rows.append([part, str(count), pct(count, total_metric)])
    if not wildcard_part_rows:
        wildcard_part_rows.append(["(none)", "0", "0.0%"])

    wildcard_rule_rows: list[list[str]] = []
    for rule_type in METRIC_RULE_TYPES:
        count = wildcard_only_by_rule_type.get(rule_type, 0)
        wildcard_rule_rows.append([rule_type, str(count), pct(count, total_metric)])

    match_quality_rows: list[list[str]] = []
    for strength in TEST_MATCH_STRENGTH_ORDER:
        count = match_strength_counter.get(strength, 0)
        match_quality_rows.append([strength, str(count), pct(count, total_metric)])

    suspicious_any_not_implemented = [
        row for row in metric_rows if row.test_covered_any and not row.code_implemented
    ]
    suspicious_wildcard_any = [
        row for row in metric_rows if row.test_covered_any and row.test_match_strength == "wildcard_assertion"
    ]

    def suspicious_rows_table(group: list[SpecRuleRow]) -> list[list[str]]:
        sample = sorted(group, key=lambda r: r.sort_key())[:10]
        rows_out: list[list[str]] = []
        for row in sample:
            rows_out.append(
                [
                    row.rule_id,
                    row.identifier_family,
                    row.rule_type,
                    short_notes(row),
                ]
            )
        if not rows_out:
            rows_out.append(["(none)", "-", "-", "-"])
        return rows_out

    exact_signature_count = tested_match_counter.get("exact_signature", 0)
    exact_assertion_count = tested_match_counter.get("exact_assertion", 0)
    family_assertion_count = tested_match_counter.get("family_assertion", 0)
    wildcard_assertion_count = tested_match_counter.get("wildcard_assertion", 0)
    arity_rows = [r for r in metric_rows if r.rule_type == "arity"]
    arity_tested_strict = sum(1 for r in arity_rows if r.test_covered_strict)
    arity_tested_any = sum(1 for r in arity_rows if r.test_covered_any)

    lines: list[str] = []
    lines.append("# SPEC Coverage Report")
    lines.append("")
    lines.append("## How to run")
    lines.append("")
    lines.append("```bash")
    lines.append("python tools/spec_coverage/generate_spec_coverage.py")
    lines.append("# Fallback in environments without `python` alias:")
    lines.append("python3 tools/spec_coverage/generate_spec_coverage.py")
    lines.append("```")
    lines.append("")
    lines.append("## Overall coverage")
    lines.append("")
    lines.append(f"- Total spec rules extracted: **{total}**")
    lines.append(
        f"- Structural rules (control-position rules like `POS 1-4 width 4`): **{len(structural_rows_list)}**"
    )
    lines.append(f"- Documentation rules count (excluded): **{len(documentation_rows_list)}**")
    lines.append(f"- Metric-eligible rules (excluding `unknown`): **{total_metric}**")
    lines.append(f"- Unknown/noisy rows excluded from %: **{unknown_excluded}**")
    lines.append(f"- Rules implemented in code: **{implemented}** ({pct(implemented, total_metric)})")
    lines.append(f"- Progress KPI (`tested_strict`): **{strict_count}** ({pct(strict_count, total_metric)})")
    lines.append(
        f"- Weak coverage (`tested_any`, includes wildcard): **{tested_any}** ({pct(tested_any, total_metric)})"
    )
    lines.append(
        f"- tested_any from non-wild matches only: **{any_non_wild_count}** ({pct(any_non_wild_count, total_metric)})"
    )
    lines.append(
        f"- Wildcard-only tested_any (not counted toward progress): **{wildcard_only_count}** ({pct(wildcard_only_count, total_metric)})"
    )
    lines.append("- Coverage progress is measured with `tested_strict` only.")
    lines.append("- `test_covered` in CSV mirrors `test_covered_any` for backward compatibility.")
    lines.append("")
    lines.append("## Top 50 real gaps (strict)")
    lines.append("")
    lines.append(
        "Strict gaps are metric spec-rule rows where `code_implemented=FALSE` or `test_covered_strict=FALSE`."
    )
    lines.append(
        "Rows with `identifier=UNSPECIFIED` or `synthetic_unmapped` notes are excluded from this actionable list."
    )
    lines.append("")
    lines.append(
        format_table(
            [
                "rank",
                "spec_part",
                "identifier",
                "rule_type",
                "enforcement_layer",
                "implemented",
                "test_strict",
                "test_any",
                "match_strength",
                "notes",
            ],
            ranked_real_gap_table_rows(top_50_real_gaps),
        )
    )
    lines.append("")
    lines.append("### Implementation gaps (strict): Not implemented + not tested_strict")
    lines.append("")
    lines.append(
        format_table(
            [
                "rank",
                "spec_part",
                "identifier",
                "rule_type",
                "enforcement_layer",
                "implemented",
                "test_strict",
                "test_any",
                "match_strength",
                "notes",
            ],
            ranked_real_gap_table_rows(implementation_gaps_top_25),
        )
    )
    lines.append("")
    lines.append("### Missing tests (strict): Implemented + not tested_strict")
    lines.append("")
    lines.append(
        format_table(
            [
                "rank",
                "spec_part",
                "identifier",
                "rule_type",
                "enforcement_layer",
                "implemented",
                "test_strict",
                "test_any",
                "match_strength",
                "notes",
            ],
            ranked_real_gap_table_rows(missing_tests_top_25),
        )
    )
    lines.append("")
    lines.append("## Rule Identity & Provenance")
    lines.append("")
    lines.append(
        "- `rule_id` format for spec rows: "
        "`{spec_file}::{stable_id}::{identifier}::{rule_type}::{payload_hash}`."
    )
    lines.append(
        "- `stable_id` is derived from normalized rule text plus canonical payload data, so line-only shifts do not churn IDs."
    )
    lines.append(
        "- Provenance remains in `spec_line_start`/`spec_line_end`, which point to global lines in `isd-format-document.deterministic.md`."
    )
    lines.append("")
    lines.append("## Enforcement layer breakdown")
    lines.append("")
    for layer in ["constants_only", "cleaning_only", "both", "neither"]:
        count = layer_counter.get(layer, 0)
        lines.append(f"- {layer}: **{count}** ({pct(count, total_metric)})")
    lines.append("")
    lines.append("## Confidence breakdown")
    lines.append("")
    lines.append(
        f"- Cleaning-implemented metric rules: **{len(cleaning_implemented_rows)}** ({pct(len(cleaning_implemented_rows), total_metric)})"
    )
    for confidence in ["high", "medium", "low"]:
        count = cleaning_confidence_counter.get(confidence, 0)
        lines.append(f"- {confidence}: **{count}** ({pct(count, len(cleaning_implemented_rows))})")
    lines.append("")
    lines.append("## Match quality")
    lines.append("")
    lines.append(
        format_table(
            ["Match strength", "Count", "% of metric rules"],
            match_quality_rows,
        )
    )
    lines.append("")
    lines.append("## Precision warnings")
    lines.append("")
    lines.append("- Wildcard policy: `wildcard_assertion` counts as tested-any only; it never counts as strict.")
    lines.append(
        f"- Tested-any rows matched by `exact_signature`: **{exact_signature_count}** ({pct(exact_signature_count, len(tested_any_rows))})"
    )
    lines.append(
        f"- Tested-any rows matched by `exact_assertion`: **{exact_assertion_count}** ({pct(exact_assertion_count, len(tested_any_rows))})"
    )
    lines.append(
        f"- Tested-any rows matched by `family_assertion`: **{family_assertion_count}** ({pct(family_assertion_count, len(tested_any_rows))})"
    )
    lines.append(
        f"- Tested-any rows matched by `wildcard_assertion`: **{wildcard_assertion_count}** ({pct(wildcard_assertion_count, len(tested_any_rows))})"
    )
    lines.append(f"- Unknown rule rows excluded from percentages: **{unknown_excluded}**")
    lines.append(
        f"- Arity rules tested (strict): **{arity_tested_strict}/{len(arity_rows)}** ({pct(arity_tested_strict, len(arity_rows))})"
    )
    lines.append(
        f"- Arity rules tested (any): **{arity_tested_any}/{len(arity_rows)}** ({pct(arity_tested_any, len(arity_rows))})"
    )
    lines.append(f"- Arity tests detected in `tests/test_cleaning.py`: **{'YES' if arity_tests_detected else 'NO'}**")
    if not arity_tests_detected:
        lines.append("- Arity tests not detected; arity tested% may be 0.")
    lines.append("")
    lines.append("## Suspicious coverage")
    lines.append("")
    lines.append(
        f"- tested_any=TRUE and code_implemented=FALSE: **{len(suspicious_any_not_implemented)}** ({pct(len(suspicious_any_not_implemented), total_metric)})"
    )
    lines.append(
        format_table(
            ["Rule ID", "Identifier family", "Rule type", "Notes"],
            suspicious_rows_table(suspicious_any_not_implemented),
        )
    )
    lines.append("")
    lines.append(
        f"- tested_any=TRUE and match_strength=`wildcard_assertion`: **{len(suspicious_wildcard_any)}** ({pct(len(suspicious_wildcard_any), total_metric)})"
    )
    lines.append(
        format_table(
            ["Rule ID", "Identifier family", "Rule type", "Notes"],
            suspicious_rows_table(suspicious_wildcard_any),
        )
    )
    lines.append("")
    lines.append("## Breakdown by ISD part")
    lines.append("")
    lines.append(
        format_table(
            [
                "Part",
                "Rules",
                "Metric rules",
                "Implemented",
                "Tested strict",
                "Tested any (weak)",
                "Implemented %",
                "Tested strict %",
                "Tested any (weak) %",
            ],
            part_rows,
        )
    )
    lines.append("")
    lines.append("## Breakdown by identifier family")
    lines.append("")
    lines.append(
        format_table(
            [
                "Identifier family",
                "Rules",
                "Metric rules",
                "Implemented",
                "Tested strict",
                "Tested any (weak)",
                "Implemented %",
                "Tested strict %",
                "Tested any (weak) %",
            ],
            family_rows,
        )
    )
    lines.append("")
    lines.append("## Breakdown by rule type")
    lines.append("")
    lines.append(
        format_table(
            [
                "Rule type",
                "Rules",
                "Implemented",
                "Tested strict",
                "Tested any (weak)",
                "Implemented %",
                "Tested strict %",
                "Tested any (weak) %",
            ],
            type_rows,
        )
    )
    lines.append("")
    lines.append("## Wildcard-only coverage (not counted toward progress)")
    lines.append("")
    lines.append(
        f"- Wildcard-only rows (`test_covered_any=TRUE` and `test_covered_strict=FALSE`): **{wildcard_only_count}** ({pct(wildcard_only_count, total_metric)})"
    )
    lines.append("")
    lines.append(
        format_table(
            ["Part", "Wildcard-only rows", "% of metric rules"],
            wildcard_part_rows,
        )
    )
    lines.append("")
    lines.append(
        format_table(
            ["Rule type", "Wildcard-only rows", "% of metric rules"],
            wildcard_rule_rows,
        )
    )
    lines.append("")
    lines.append("## How to extend")
    lines.append("")
    lines.append("- Add or tweak regexes in `parse_spec_doc()` for new rule text patterns.")
    lines.append("- Update `SPEC_PART_ANCHORS` and `segment_spec_doc_lines()` if the deterministic source layout changes.")
    lines.append("- Extend `infer_rule_types_from_text()` if new rule classes appear.")
    lines.append("- Extend `coverage_in_constants_for_row()` and `coverage_in_cleaning_for_row()` for new enforcement metadata.")
    lines.append("- Extend `parse_tests_evidence()` value-token and assertion-intent hooks for new test styles.")
    lines.append("- Keep deterministic ordering by preserving `sort_key()` and fixed table order.")

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]

    spec_path = repo_root / "spec_sources" / "isd-format-document-parts" / SPEC_DOC_NAME
    constants_path = repo_root / "src" / "noaa_spec" / "constants.py"
    cleaning_path = repo_root / "src" / "noaa_spec" / "cleaning.py"
    tests_path = repo_root / "tests" / "test_cleaning.py"

    csv_output = repo_root / "spec_coverage.csv"
    report_output = repo_root / "docs" / "reports" / "SPEC_COVERAGE_REPORT.md"

    constants_ast = parse_constants_ast(constants_path)
    cleaning_index = parse_cleaning_index(cleaning_path)
    constants_module = load_constants_module(repo_root)

    known_identifiers: set[str] = set(getattr(constants_module, "KNOWN_IDENTIFIERS", set()))
    known_families: set[str] = {identifier_family(v) for v in known_identifiers}
    known_families.update({"DATE", "TIME", "LATITUDE", "LONGITUDE", "ELEVATION", "CALL_SIGN", "REPORT_TYPE", "QC_PROCESS"})
    known_identifiers.update(known_families)

    rows = parse_spec_doc(spec_path, known_identifiers, known_families)
    rows = filter_known_spec_extraction_errors(rows, constants_module)
    rows = classify_extracted_row_kinds(rows)

    rows = normalize_and_assign_rule_ids(rows)
    rows = merge_duplicate_rows(rows)

    test_known_identifiers, test_known_families = augment_known_test_identifiers(
        known_identifiers,
        known_families,
        rows,
    )
    test_index = parse_tests_evidence(tests_path, test_known_identifiers, test_known_families)
    rows = apply_coverage(rows, constants_module, constants_ast, cleaning_index, test_index)

    rows = sorted(rows, key=lambda r: r.sort_key())

    write_csv(csv_output, rows)
    report_output.parent.mkdir(parents=True, exist_ok=True)

    build_report(rows, report_output, test_index.arity_tests_detected)

    total = sum(1 for r in rows if r.row_kind in EXTRACTED_ROW_KINDS)
    metric_rows = [r for r in rows if r.row_kind in METRIC_ROW_KINDS and r.rule_type in METRIC_RULE_TYPES]
    metric_total = len(metric_rows)
    impl = sum(1 for r in metric_rows if r.code_implemented)
    tested_strict = sum(1 for r in metric_rows if r.test_covered_strict)
    tested_any = sum(1 for r in metric_rows if r.test_covered_any)
    gaps = [r for r in metric_rows if (not r.code_implemented or not r.test_covered_strict)]
    sorted_gaps = sorted(gaps, key=lambda r: (-row_gap_score(r), r.sort_key()))
    top_gaps: list[SpecRuleRow] = []
    seen_gap_keys: set[tuple[str, str, str]] = set()
    for row in sorted_gaps:
        key = (row.spec_part, row.identifier, row.rule_type)
        if key in seen_gap_keys:
            continue
        if "synthetic_unmapped" in row.notes or row.identifier == "UNSPECIFIED":
            continue
        seen_gap_keys.add(key)
        top_gaps.append(row)
        if len(top_gaps) >= 10:
            break
    if len(top_gaps) < 10:
        for row in sorted_gaps:
            key = (row.spec_part, row.identifier, row.rule_type)
            if key in seen_gap_keys:
                continue
            seen_gap_keys.add(key)
            top_gaps.append(row)
            if len(top_gaps) >= 10:
                break

    print(f"Generated {csv_output.relative_to(repo_root)} and {report_output.relative_to(repo_root)}")
    print(f"total_rules={total}")
    print(f"metric_rules={metric_total}")
    print(f"implemented_rules={impl} ({pct(impl, metric_total)})")
    print(f"tested_rules_strict={tested_strict} ({pct(tested_strict, metric_total)})")
    print(f"tested_rules_any={tested_any} ({pct(tested_any, metric_total)})")
    print("top_gap_sample=")
    for row in top_gaps:
        print(
            f"  part={row.spec_part} id={row.identifier} type={row.rule_type} "
            f"code={row.code_implemented} test_strict={row.test_covered_strict} "
            f"test_any={row.test_covered_any} match={row.test_match_strength} "
            f"notes={';'.join(sorted(row.notes))}"
        )


if __name__ == "__main__":
    main()
