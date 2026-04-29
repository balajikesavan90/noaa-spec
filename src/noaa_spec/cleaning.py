"""Cleaning utilities for NOAA Global Hourly data."""

from __future__ import annotations

from dataclasses import dataclass
import json
import logging
import re
from typing import Iterable

import pandas as pd

# Module-level logger for strict parsing warnings
logger = logging.getLogger(__name__)

from .constants import (
    ADDITIONAL_DATA_PREFIXES,
    DATA_SOURCE_FLAGS,
    EQD_ELEMENT_NAMES,
    EQD_FLAG1_CODES,
    EQD_FLAG2_CODES,
    KNOWN_IDENTIFIERS,
    LEGACY_EQD_MSD_PATTERN,
    LEGACY_EQD_PARAMETER_CODES,
    CIG_PUBLIC_OUTPUT_MAX_M,
    QNN_ELEMENT_IDENTIFIERS,
    REM_TYPE_CODES,
    QUALITY_FLAGS,
    QC_PROCESS_CODES,
    QC_STATUS_VALUES,
    QC_REASON_ENUM,
    USABILITY_METRIC_INDICATORS,
    REPORT_TYPE_CODES,
    VIS_PUBLIC_OUTPUT_MAX_M,
    FieldPartRule,
    get_expected_part_count,
    get_field_registry_entry,
    get_field_rule,
    get_token_width_rules,
    is_valid_eqd_identifier,
    is_valid_repeated_identifier,
    is_valid_section_identifier_token,
    to_friendly_column,
    to_internal_column,
)


@dataclass(frozen=True)
class ParsedField:
    parts: list[str]
    raw_parts: list[str]
    values: list[float | None]
    quality: str | None


# Cleaned-column naming contract:
# - Parsed source fields retain full NOAA identifiers, including repeated suffixes
#   (e.g., "OD1__part3", "OD2__part3").
# - Per-field QC columns append "__qc_*" to those prefix-specific base columns.
# - Prefix-bound custom QC flags preserve the full source prefix in the output
#   name (e.g., "qc_calm_direction_detected_OD1", not a collapsed family key).
# - Only true singleton semantics may use non-prefixed/global flags.


def _strip_plus(value: str) -> str:
    return value[1:] if value.startswith("+") else value


def _is_missing_numeric(value: str) -> bool:
    stripped = value.replace(".", "").replace("+", "")
    if stripped.startswith("-"):
        return False
    return stripped.isdigit() and len(stripped) >= 2 and set(stripped) == {"9"}


def _normalize_missing(value: str) -> str:
    stripped = value.replace(".", "").replace("+", "")
    sign = ""
    if stripped.startswith("-"):
        sign = "-"
        stripped = stripped[1:]
    stripped = stripped.lstrip("0") or "0"
    return f"{sign}{stripped}"


def _is_missing_value(value: str, rule: FieldPartRule | None) -> bool:
    if rule and rule.missing_values is not None:
        stripped = _normalize_missing(value)
        return stripped in rule.missing_values
    return _is_missing_numeric(value)


def _is_flag_only_domain_identifier(prefix: str) -> bool:
    return prefix.startswith(("AC", "AD", "AG", "AH"))


def _is_flag_only_arity_identifier(prefix: str) -> bool:
    return prefix.startswith("AH")


def _check_domain(
    value: str,
    part_rule: FieldPartRule | None,
) -> tuple[str | None, bool, bool]:
    normalized = value.strip()
    if part_rule is None:
        return normalized, False, False

    domain_invalid = False
    pattern_mismatch = False
    if part_rule.allowed_values:
        normalized_upper = normalized.upper()
        if normalized_upper not in part_rule.allowed_values:
            domain_invalid = True
    if part_rule.allowed_pattern:
        pattern = part_rule.allowed_pattern
        if isinstance(pattern, str):
            pattern = re.compile(pattern)
        if not pattern.fullmatch(normalized):
            pattern_mismatch = True

    if domain_invalid or pattern_mismatch:
        return None, domain_invalid, pattern_mismatch
    return normalized, False, False


def enforce_domain(value: str, part_rule: FieldPartRule | None) -> str | None:
    normalized = value.strip()
    if part_rule is None:
        return normalized
    if part_rule.allowed_values:
        normalized_upper = normalized.upper()
        if normalized_upper not in part_rule.allowed_values:
            return None
    if part_rule.allowed_pattern:
        pattern = part_rule.allowed_pattern
        if isinstance(pattern, str):
            pattern = re.compile(pattern)
        if not pattern.fullmatch(normalized):
            return None
    return normalized


def _quality_for_part(prefix: str, part_index: int, parts: list[str]) -> str | None:
    rule = get_field_rule(prefix)
    if not rule:
        return None
    part_rule = rule.parts.get(part_index)
    if not part_rule or part_rule.quality_part is None:
        return None
    quality_index = part_rule.quality_part
    if quality_index > len(parts):
        return None
    return parts[quality_index - 1]


def _allowed_quality_set(prefix: str, quality_part_index: int) -> set[str]:
    rule = get_field_rule(prefix)
    if rule is None:
        return QUALITY_FLAGS
    quality_rule = rule.parts.get(quality_part_index)
    if quality_rule and quality_rule.allowed_quality:
        return quality_rule.allowed_quality
    return QUALITY_FLAGS


def _allowed_quality_for_value(prefix: str, part_index: int) -> set[str]:
    rule = get_field_rule(prefix)
    if rule is None:
        return QUALITY_FLAGS
    part_rule = rule.parts.get(part_index)
    if part_rule is None or part_rule.quality_part is None:
        return QUALITY_FLAGS
    return _allowed_quality_set(prefix, part_rule.quality_part)


def _additional_data_fixed_width(
    prefix: str, part_rule: FieldPartRule | None
) -> int | None:
    if part_rule is None or part_rule.kind != "numeric":
        return None
    prefix_key = prefix[:2]
    if prefix_key not in ADDITIONAL_DATA_PREFIXES:
        return None
    if not part_rule.missing_values:
        return None
    lengths = {
        len(value)
        for value in part_rule.missing_values
        if value.isdigit()
    }
    return next(iter(lengths)) if len(lengths) == 1 else None


def _single_quality_part(prefix: str) -> int | None:
    rule = get_field_rule(prefix)
    if not rule:
        return None
    quality_parts = {
        part.quality_part
        for part in rule.parts.values()
        if part.quality_part is not None
    }
    if len(quality_parts) == 1:
        return next(iter(quality_parts))
    return None


def _is_eqd_prefix(prefix: str) -> bool:
    return len(prefix) == 3 and prefix[0] in {"Q", "P", "R", "C", "D", "N"} and prefix[1:].isdigit()


def _is_numeric_parse_failure(
    part: str,
    value: float | None,
    part_rule: FieldPartRule | None,
) -> bool:
    if part_rule is None or part_rule.kind != "numeric":
        return False
    return part.strip() != "" and value is None and not _is_missing_value(part, part_rule)


def _should_preserve_text_token(
    prefix: str,
    idx: int,
    part_rule: FieldPartRule | None,
) -> bool:
    if part_rule is None:
        return False
    if _is_eqd_prefix(prefix) and idx == 1:
        return True
    if part_rule.kind != "categorical":
        return False
    return (
        (prefix.startswith("AT") and idx == 2)
        or (prefix.startswith("AW") and idx == 1)
        or (prefix.startswith("MV") and idx == 1)
        or (prefix.startswith("MW") and idx == 1)
    )


def _is_crn_missing_qc(
    prefix: str,
    part_rule: FieldPartRule | None,
    part_quality: str | None,
) -> bool:
    if part_rule is None or part_rule.kind != "numeric":
        return False
    return prefix[:2] in {"CB", "CF", "CG", "CH", "CI", "CN"} and part_quality == "9"


def _is_valid_eqd_parameter_code(prefix: str, value: str) -> bool:
    if prefix.startswith("N"):
        if len(value) != 6:
            return False
        element = value[:4]
        flag1 = value[4]
        flag2 = value[5]
        return (
            element in EQD_ELEMENT_NAMES
            and flag1 in EQD_FLAG1_CODES
            and flag2 in EQD_FLAG2_CODES
        )
    normalized = value.strip().upper()
    if normalized in LEGACY_EQD_PARAMETER_CODES:
        return True
    return prefix.startswith("R") and bool(LEGACY_EQD_MSD_PATTERN.fullmatch(normalized))


def _parse_remark(value: object) -> tuple[str | None, str | None]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None, None
    raw_text = str(value)
    text = raw_text.strip()
    if text in {"", "nan", "None"}:
        return None, None
    structured = _parse_structured_remark(text)
    if structured is not None:
        return structured[0], structured[1]
    return None, text


def _parse_structured_remark(
    text: str,
) -> tuple[str, str, str, str] | None:
    if len(text) < 6:
        return None
    idx = 0
    remark_types: list[str] = []
    remark_texts: list[str] = []
    while idx < len(text):
        type_end = idx + 3
        if type_end > len(text):
            return None
        remark_type = text[idx:type_end].upper()
        if remark_type not in REM_TYPE_CODES:
            return None
        idx = type_end
        length_end = idx + 3
        if length_end > len(text):
            return None
        length_token = text[idx:length_end]
        if not length_token.isdigit():
            return None
        text_length = int(length_token)
        if text_length < 1 or text_length > 999:
            return None
        idx = length_end
        text_end = idx + text_length
        if text_end > len(text):
            return None
        remark_text = text[idx:text_end]
        if not _is_ascii_text(remark_text):
            return None
        remark_types.append(remark_type)
        remark_texts.append(remark_text)
        idx = text_end
    if not remark_types:
        return None
    return (
        remark_types[0],
        remark_texts[0],
        ",".join(remark_types),
        json.dumps(remark_texts),
    )


def _skip_qnn_padding(text: str, idx: int) -> int:
    while idx < len(text) and text[idx].isspace():
        idx += 1
    return idx


def _is_qnn_token_char(char: str) -> bool:
    return char != "," and not char.isspace() and 32 <= ord(char) <= 126


def _read_qnn_token(text: str, idx: int, width: int) -> tuple[str, int] | None:
    idx = _skip_qnn_padding(text, idx)
    end = idx + width
    if end > len(text):
        return None
    token = text[idx:end]
    if any(not _is_qnn_token_char(char) for char in token):
        return None
    return token, end


def _parse_qnn_blocks(
    payload: str,
    block_count: int,
) -> tuple[list[str], list[str], int] | None:
    idx = 0
    element_ids: list[str] = []
    source_flags: list[str] = []
    for _ in range(block_count):
        element_token = _read_qnn_token(payload, idx, 1)
        if element_token is None:
            return None
        element, idx = element_token
        if element not in QNN_ELEMENT_IDENTIFIERS:
            return None
        flag_token = _read_qnn_token(payload, idx, 4)
        if flag_token is None:
            return None
        flags, idx = flag_token
        element_ids.append(element)
        source_flags.append(flags)
    return element_ids, source_flags, idx


def _parse_qnn_data_values(payload: str, idx: int, count: int) -> list[str] | None:
    data_values: list[str] = []
    for _ in range(count):
        data_token = _read_qnn_token(payload, idx, 6)
        if data_token is None:
            return None
        data_value, idx = data_token
        data_values.append(data_value)
    if _skip_qnn_padding(payload, idx) != len(payload):
        return None
    return data_values


def _parse_qnn(value: object) -> tuple[str | None, str | None, str | None]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None, None, None
    text = str(value).strip()
    if text in {"", "nan", "None"}:
        return None, None, None
    if text[:3].upper() != "QNN":
        return None, None, None
    payload = text[3:]
    if payload.strip() == "":
        return None, None, None
    block_count = 1
    while True:
        parsed_blocks = _parse_qnn_blocks(payload, block_count)
        if parsed_blocks is None:
            return None, None, None
        element_ids, source_flags, idx = parsed_blocks
        data_values = _parse_qnn_data_values(payload, idx, block_count)
        if data_values is not None:
            return ",".join(element_ids), ",".join(source_flags), ",".join(data_values)
        block_count += 1


def _to_float(value: str) -> float | None:
    value = value.strip()
    if value == "":
        return None
    value = _strip_plus(value)
    try:
        return float(value)
    except ValueError:
        return None


def _split_field(raw: str) -> list[str]:
    return raw.split(",")


def parse_field(raw: str) -> ParsedField:
    raw_parts = _split_field(raw)
    parts = [part.strip() for part in raw_parts]
    values = [_to_float(part) for part in parts]
    quality = parts[-1] if parts and len(parts[-1]) == 1 else None
    return ParsedField(parts=parts, raw_parts=raw_parts, values=values, quality=quality)


def _expand_parsed(
    parsed: ParsedField,
    prefix: str,
    allow_quality: bool,
    strict_mode: bool = True,
    arity_mismatch: bool = False,
) -> dict[str, object]:
    """Expand multi-part parsed field into column dictionary with QC signals.

    For each numeric part, emits:
    - `{PREFIX}__partN`: Numeric or categorical value (scaled if applicable)
    - `{PREFIX}__partN__qc_pass`: Boolean - range/quality checks passed
    - `{PREFIX}__partN__qc_status`: String - "PASS" or "INVALID"
    - `{PREFIX}__partN__qc_reason`: Reason for failure (or None if PASS)

    QC signal values indicate:
    - OUT_OF_RANGE: Value outside min/max bounds from FieldPartRule
    - SENTINEL_MISSING: Value matched missing sentinel pattern
    - BAD_QUALITY_CODE: Quality flag outside allowed set
    - MALFORMED_TOKEN: Token width or format validation failed

    Args:
        parsed: ParsedField with parts, values, and quality
        prefix: Field identifier (e.g., "WND", "MA1", "GE1")
        allow_quality: Whether to include quality column if present
        strict_mode: If True, enforce token width validation (A4) and log rejections

    Returns:
        Dict mapping output column names to values
    """
    payload: dict[str, object] = {}
    malformed_parts: set[int] = set()
    missing_by_quality_parts: set[int] = set()
    is_variable_direction = (
        prefix == "WND"
        and len(parsed.parts) >= 3
        and parsed.parts[0].strip() == "999"
        and parsed.parts[2].strip().upper() == "V"
    )
    if prefix == "WND":
        payload["WND__direction_variable"] = is_variable_direction
    is_od_calm = (
        prefix.startswith("OD")
        and len(parsed.parts) >= 4
        and parsed.parts[2].strip() == "999"
        and parsed.parts[3].strip() == "0000"
    )
    is_wnd_calm = (
        prefix == "WND"
        and len(parsed.parts) >= 4
        and parsed.parts[2].strip() == "9"
        and parsed.parts[3].strip() == "0000"
    )
    is_oe_calm = (
        prefix.startswith("OE")
        and len(parsed.parts) >= 4
        and parsed.parts[2].strip() == "00000"
        and parsed.parts[3].strip() == "999"
    )
    is_eqd = _is_eqd_prefix(prefix)
    flag_only_domain = _is_flag_only_domain_identifier(prefix)
    flag_only_arity = _is_flag_only_arity_identifier(prefix)
    if flag_only_domain:
        payload[f"qc_domain_invalid_{prefix}"] = False
        payload[f"qc_pattern_mismatch_{prefix}"] = False
    if flag_only_arity:
        payload[f"qc_arity_mismatch_{prefix}"] = bool(arity_mismatch)
    if prefix == "WND":
        payload["qc_calm_wind_detected"] = False
    if prefix.startswith("OD"):
        payload[f"qc_calm_direction_detected_{prefix}"] = False
    if prefix.startswith("OE"):
        payload[f"qc_calm_speed_detected_{prefix}"] = False
    field_rule = get_field_rule(prefix)
    quality_value = None
    if allow_quality:
        quality_part_index = _single_quality_part(prefix)
        if quality_part_index is not None and quality_part_index <= len(parsed.parts):
            quality_value = parsed.parts[quality_part_index - 1].strip()
            if quality_value == "":
                quality_value = None
    allowed_quality = QUALITY_FLAGS
    if allow_quality and quality_part_index is not None:
        allowed_quality = _allowed_quality_set(prefix, quality_part_index)
    invalid_quality = (
        allow_quality
        and quality_value is not None
        and quality_value not in allowed_quality
    )
    for idx, (part, value) in enumerate(zip(parsed.parts, parsed.values), start=1):
        entry = get_field_registry_entry(prefix, idx, suffix="part")
        key = entry.internal_name if entry else f"{prefix}__part{idx}"
        part_rule = field_rule.parts.get(idx) if field_rule else None
        if is_variable_direction and idx == 1:
            payload[key] = None
            continue
        if is_wnd_calm and idx == 3:
            payload["qc_calm_wind_detected"] = True
            if _is_missing_value(part, part_rule):
                payload[key] = None
            else:
                payload[key] = value if value is not None else part.strip()
            continue
        if is_od_calm and idx == 3:
            payload[f"qc_calm_direction_detected_{prefix}"] = True
            if _is_missing_value(part, part_rule):
                payload[key] = None
            else:
                payload[key] = value if value is not None else part.strip()
            continue
        if is_oe_calm and idx == 4:
            payload[f"qc_calm_speed_detected_{prefix}"] = True
            if _is_missing_value(part, part_rule):
                payload[key] = None
            else:
                payload[key] = value if value is not None else part.strip()
            continue
        part_quality = _quality_for_part(prefix, idx, parsed.parts) if allow_quality else None
        allowed_for_part = _allowed_quality_for_value(prefix, idx)
        if part_quality is not None and part_quality not in allowed_for_part:
            payload[key] = None
            continue
        if invalid_quality and idx == 1 and part_quality is None:
            payload[key] = None
            continue
        # Check field-specific sentinels first — raw parts like "009999"
        # may parse numerically but still be declared missing.
        if _is_missing_value(part, part_rule):
            payload[key] = None
            continue
        
        # A4: Strict mode token width/format validation
        if strict_mode:
            width_rules = get_token_width_rules(prefix, idx)
            if width_rules:
                part_stripped = part.strip()
                raw_part = parsed.raw_parts[idx - 1] if idx - 1 < len(parsed.raw_parts) else part
                # Check token width
                if 'width' in width_rules:
                    expected_width = width_rules['width']
                    if part_rule and part_rule.kind == "numeric":
                        # Reject space-padded numeric tokens in strict mode.
                        if raw_part != raw_part.strip():
                            logger.warning(
                                f"[PARSE_STRICT] Rejected {prefix} part {idx}: "
                                "token contains leading/trailing whitespace"
                            )
                            malformed_parts.add(idx)
                            payload[key] = None
                            continue
                        # Handle signed numeric values (e.g., temperature).
                        test_value = part_stripped.lstrip('+-')
                    else:
                        # Preserve raw token width for fixed-width categorical/quality tokens.
                        test_value = raw_part
                    if len(test_value) != expected_width:
                        logger.warning(
                            f"[PARSE_STRICT] Rejected {prefix} part {idx}: "
                            f"token width {len(test_value)}, expected {expected_width}"
                        )
                        malformed_parts.add(idx)
                        payload[key] = None
                        continue
                # Check token pattern
                if 'pattern' in width_rules:
                    pattern = width_rules['pattern']
                    if not pattern.fullmatch(part_stripped):
                        logger.warning(
                            f"[PARSE_STRICT] Rejected {prefix} part {idx}: "
                            f"token format mismatch (pattern validation failed)"
                        )
                        malformed_parts.add(idx)
                        payload[key] = None
                        continue
        
        if part_rule and part_rule.kind == "quality" and part_rule.allowed_quality:
            if part.strip().upper() not in part_rule.allowed_quality:
                payload[key] = None
                continue
        fixed_width = _additional_data_fixed_width(prefix, part_rule)
        if fixed_width is not None:
            normalized = part.strip()
            if not normalized.isdigit() or len(normalized) != fixed_width:
                payload[key] = None
                continue
        domain_value, domain_invalid, pattern_mismatch = _check_domain(part, part_rule)
        if flag_only_domain:
            if domain_invalid:
                payload[f"qc_domain_invalid_{prefix}"] = True
            if pattern_mismatch:
                payload[f"qc_pattern_mismatch_{prefix}"] = True
        if domain_value is None:
            if flag_only_domain and (domain_invalid or pattern_mismatch):
                if _should_preserve_text_token(prefix, idx, part_rule):
                    payload[key] = part.strip()
                elif value is not None:
                    scale = part_rule.scale if part_rule else None
                    payload[key] = value * scale if scale is not None else value
                else:
                    payload[key] = part.strip()
                continue
            if _is_numeric_parse_failure(part, value, part_rule):
                malformed_parts.add(idx)
            payload[key] = None
            continue
        if _should_preserve_text_token(prefix, idx, part_rule):
            payload[key] = domain_value
            continue
        if is_eqd and idx == 3:
            param_code = domain_value
            if param_code != "" and not _is_valid_eqd_parameter_code(prefix, param_code):
                payload[key] = None
                continue
        if _is_numeric_parse_failure(part, value, part_rule):
            malformed_parts.add(idx)
            payload[key] = None
            continue
        if _is_crn_missing_qc(prefix, part_rule, part_quality):
            missing_by_quality_parts.add(idx)
            payload[key] = None
            continue
        if value is None:
            payload[key] = domain_value
            continue
        if part_rule and value is not None:
            if part_rule.min_value is not None and value < part_rule.min_value:
                payload[key] = None
                continue
            if part_rule.max_value is not None and value > part_rule.max_value:
                payload[key] = None
                continue
        scale = part_rule.scale if part_rule else None
        scaled = value * scale if scale is not None else value
        if prefix == "CIG" and idx == 1 and scaled is not None and scaled > CIG_PUBLIC_OUTPUT_MAX_M:
            scaled = CIG_PUBLIC_OUTPUT_MAX_M
        if prefix == "VIS" and idx == 1 and scaled is not None and scaled > VIS_PUBLIC_OUTPUT_MAX_M:
            scaled = VIS_PUBLIC_OUTPUT_MAX_M
        payload[key] = scaled
    
    # Add QC signals for numeric parts in multi-part fields
    for idx, (part, value) in enumerate(zip(parsed.parts, parsed.values), start=1):
        part_rule = field_rule.parts.get(idx) if field_rule else None
        if part_rule is None or part_rule.kind != "numeric":
            continue
        entry = get_field_registry_entry(prefix, idx, suffix="part")
        key = entry.internal_name if entry else f"{prefix}__part{idx}"
        if key not in payload:
            continue
        
        # Determine QC signals based on the current state
        is_sentinel = _is_missing_value(part, part_rule) or idx in missing_by_quality_parts
        
        # Check quality for this part
        part_quality = _quality_for_part(prefix, idx, parsed.parts) if allow_quality else None
        allowed_for_part = _allowed_quality_for_value(prefix, idx)
        bad_quality = part_quality is not None and part_quality not in allowed_for_part
        
        # Check range (value is pre-scale)
        out_of_range = False
        if value is not None:
            if part_rule.min_value is not None and value < part_rule.min_value:
                out_of_range = True
            elif part_rule.max_value is not None and value > part_rule.max_value:
                out_of_range = True
        
        qc_pass, qc_status, qc_reason = _compute_qc_signals(
            is_sentinel=is_sentinel,
            bad_quality=bad_quality,
            out_of_range=out_of_range,
            malformed_token=idx in malformed_parts,
        )
        
        payload[f"{key}__qc_pass"] = qc_pass
        payload[f"{key}__qc_status"] = qc_status
        payload[f"{key}__qc_reason"] = qc_reason
    
    if allow_quality and quality_value is not None:
        payload[f"{prefix}__quality"] = quality_value
    return payload


def _is_value_quality_field(prefix: str, part_count: int) -> bool:
    if part_count != 2:
        return False
    rule = get_field_rule(prefix)
    if rule is None:
        return False
    part_rule = rule.parts.get(1)
    if part_rule is None or part_rule.quality_part is None:
        return False
    return len(rule.parts) == 1


def _compute_qc_signals(
    is_sentinel: bool, bad_quality: bool, out_of_range: bool, malformed_token: bool
) -> tuple[bool, str, str | None]:
    """Compute QC signals based on validation checks.

    Maps validation failure reasons to standardized QC status and reason codes,
    following the pattern defined by QC_STATUS_VALUES and QC_REASON_ENUM in constants:
    - BAD_QUALITY_CODE: Quality flag outside allowed_quality set (per FieldPartRule)
    - SENTINEL_MISSING: Value matched missing sentinel pattern (e.g., 9999 for OC1)
    - OUT_OF_RANGE: Numeric value outside min/max bounds from FieldPartRule
    - All checks pass → PASS status with None reason

    Priority order: malformed_token > bad_quality > is_sentinel > out_of_range.

    Args:
        is_sentinel: Value was a missing sentinel (pre-scale)
        bad_quality: Quality code failed validation against allowed_quality
        out_of_range: Numeric value outside min/max bounds (pre-scale)
        malformed_token: Token width or format validation failed (A4)

    Returns:
        Tuple of (qc_pass: bool, qc_status: str, qc_reason: str | None)
            qc_pass: True if all checks pass, False otherwise
            qc_status: "PASS" or "INVALID" (values from QC_STATUS_VALUES)
            qc_reason: string from QC_REASON_ENUM, or None if qc_pass is True

    Example:
        >>> _compute_qc_signals(False, False, False, False)  # All checks passed
        (True, 'PASS', None)
        >>> _compute_qc_signals(False, False, True, False)   # Out of range
        (False, 'INVALID', 'OUT_OF_RANGE')
        >>> _compute_qc_signals(True, False, False, False)   # Sentinel value
        (False, 'MISSING', 'SENTINEL_MISSING')
    """
    if malformed_token:
        return False, "INVALID", "MALFORMED_TOKEN"
    if bad_quality:
        return False, "INVALID", "BAD_QUALITY_CODE"
    if is_sentinel:
        return False, "MISSING", "SENTINEL_MISSING"
    if out_of_range:
        return False, "INVALID", "OUT_OF_RANGE"
    return True, "PASS", None


def clean_value_quality(raw: str, prefix: str, strict_mode: bool = True) -> dict[str, object]:
    """Parse and validate a comma-encoded 2-part NOAA value/quality field.

    Applies range validation (pre-scale), quality code checking, and sentinel detection
    to emit QC signals per _compute_qc_signals(). Raw value is preserved in __value unless
    QC check fails (out_of_range, bad_quality, sentinel, malformed), in which case
    __value is None.

    For 2-part value/quality fields, emits:
    - {PREFIX}__value: Numeric value (scaled per FieldPartRule, None if invalid)
    - {PREFIX}__quality: Quality code string  
    - {PREFIX}__qc_pass: Boolean - all checks passed
    - {PREFIX}__qc_status: String - "PASS" or "INVALID" (from QC_STATUS_VALUES)
    - {PREFIX}__qc_reason: String from QC_REASON_ENUM, or None if PASS

    Validation order (pre-scale):
    1. Quality code against allowed_quality set (per FieldPartRule)
    2. Sentinel detection against missing_values set
    3. Range check: min_value ≤ numeric ≤ max_value

    Args:
        raw: Raw comma-separated field value (e.g., "0500,1" for OC1 wind gust)
        prefix: Field identifier used to look up FieldPartRule (e.g., "OC1", "MA1")
        strict_mode: If True, enforce validation rules (A2-A4) with [PARSE_STRICT] logging.
                     If False, use permissive parsing (legacy mode).

    Returns:
        Dict with keys like {PREFIX}__value, {PREFIX}__quality, {PREFIX}__qc_*
        Returns empty dict {} if EQD/repeated identifier validation fails in strict mode.

    Examples:
        >>> clean_value_quality("0500,1", "OC1")
        {'OC1__value': 50.0, 'OC1__quality': '1', 'OC1__qc_pass': True, ...}
        >>> clean_value_quality("1101,1", "OC1")  # 1101 > max 1100
        {'OC1__value': None, 'OC1__qc_pass': False, 'OC1__qc_reason': 'OUT_OF_RANGE', ...}
    """
    field_rule = get_field_rule(prefix)
    if strict_mode:
        section_identifier_valid = is_valid_section_identifier_token(prefix)
        if section_identifier_valid is False:
            logger.warning(
                f"[PARSE_STRICT] Rejected {prefix}: malformed section identifier token (expected 3 upper-case alphanumeric chars)"
            )
            return {}
    if field_rule is None:
        eqd_valid = is_valid_eqd_identifier(prefix)
        if eqd_valid is False:
            if strict_mode:
                logger.warning(f"[PARSE_STRICT] Rejected {prefix}: invalid EQD identifier format")
            return {}
        repeated_valid = is_valid_repeated_identifier(prefix)
        if repeated_valid is False:
            if strict_mode:
                logger.warning(f"[PARSE_STRICT] Rejected {prefix}: invalid repeated identifier format")
            return {}
    parsed = parse_field(raw)
    arity_mismatch = False
    
    # A3: Strict mode arity validation - check expected vs actual part count
    # Skip validation for value/quality fields (they have special 2-part handling)
    if strict_mode and not _is_value_quality_field(prefix, len(parsed.parts)):
        expected_parts = get_expected_part_count(prefix)
        if expected_parts is not None and len(parsed.parts) != expected_parts:
            if len(parsed.parts) < expected_parts:
                logger.warning(
                    f"[PARSE_STRICT] Rejected {prefix}: truncated payload - "
                    f"expected {expected_parts} parts, got {len(parsed.parts)}"
                )
            else:
                logger.warning(
                    f"[PARSE_STRICT] Rejected {prefix}: extra payload - "
                    f"expected {expected_parts} parts, got {len(parsed.parts)}"
                )
            if _is_flag_only_arity_identifier(prefix):
                arity_mismatch = True
            else:
                return {}
    
    if len(parsed.parts) != 2:
        return _expand_parsed(
            parsed,
            prefix,
            allow_quality=True,
            strict_mode=strict_mode,
            arity_mismatch=arity_mismatch,
        )
    if not _is_value_quality_field(prefix, len(parsed.parts)):
        return _expand_parsed(
            parsed,
            prefix,
            allow_quality=True,
            strict_mode=strict_mode,
            arity_mismatch=arity_mismatch,
        )
    part_rule = field_rule.parts.get(1) if field_rule else None
    entry = get_field_registry_entry(prefix, 1, suffix="value")
    value_key = entry.internal_name if entry else f"{prefix}__value"
    quality = parsed.quality
    quality_index = part_rule.quality_part if part_rule else None
    if quality_index is not None and quality_index <= len(parsed.parts):
        quality = parsed.parts[quality_index - 1].strip() or None
    allowed_quality = (
        _allowed_quality_set(prefix, quality_index)
        if quality_index is not None
        else QUALITY_FLAGS
    )
    if (
        quality_index is not None
        and allowed_quality == QUALITY_FLAGS
        and part_rule
        and part_rule.allowed_quality
    ):
        allowed_quality = part_rule.allowed_quality
    
    # A4: Token width validation for value/quality fields
    if strict_mode:
        width_rules = get_token_width_rules(prefix, 1)
        if width_rules:
            part_stripped = parsed.parts[0].strip()
            # Check token width (handling signed values)
            if 'width' in width_rules:
                expected_width = width_rules['width']
                raw_part = parsed.raw_parts[0] if parsed.raw_parts else parsed.parts[0]
                if raw_part != raw_part.strip():
                    logger.warning(
                        f"[PARSE_STRICT] Rejected {prefix} part 1: "
                        "token contains leading/trailing whitespace"
                    )
                    qc_pass, qc_status, qc_reason = _compute_qc_signals(
                        is_sentinel=False,
                        bad_quality=False,
                        out_of_range=False,
                        malformed_token=True,
                    )
                    return {
                        value_key: None,
                        f"{prefix}__quality": quality,
                        f"{prefix}__qc_pass": qc_pass,
                        f"{prefix}__qc_status": qc_status,
                        f"{prefix}__qc_reason": qc_reason,
                    }
                test_value = part_stripped.lstrip('+-')
                if len(test_value) != expected_width:
                    logger.warning(
                        f"[PARSE_STRICT] Rejected {prefix} part 1: "
                        f"token width {len(test_value)}, expected {expected_width}"
                    )
                    qc_pass, qc_status, qc_reason = _compute_qc_signals(
                        is_sentinel=False,
                        bad_quality=False,
                        out_of_range=False,
                        malformed_token=True,
                    )
                    return {
                        value_key: None,
                        f"{prefix}__quality": quality,
                        f"{prefix}__qc_pass": qc_pass,
                        f"{prefix}__qc_status": qc_status,
                        f"{prefix}__qc_reason": qc_reason,
                    }
            # Check token pattern
            if 'pattern' in width_rules:
                pattern = width_rules['pattern']
                if not pattern.fullmatch(part_stripped):
                    logger.warning(
                        f"[PARSE_STRICT] Rejected {prefix} part 1: "
                        f"token format mismatch (pattern validation failed)"
                    )
                    qc_pass, qc_status, qc_reason = _compute_qc_signals(
                        is_sentinel=False,
                        bad_quality=False,
                        out_of_range=False,
                        malformed_token=True,
                    )
                    return {
                        value_key: None,
                        f"{prefix}__quality": quality,
                        f"{prefix}__qc_pass": qc_pass,
                        f"{prefix}__qc_status": qc_status,
                        f"{prefix}__qc_reason": qc_reason,
                    }
    
    value: float | None
    raw_part = parsed.parts[0]
    malformed_token = False
    
    # Check if it's a sentinel/missing value
    is_sentinel = part_rule and _is_missing_value(raw_part, part_rule)
    
    if is_sentinel:
        value = None
    elif _is_numeric_parse_failure(raw_part, parsed.values[0], part_rule):
        value = None
        malformed_token = True
    else:
        domain_value = enforce_domain(raw_part, part_rule)
        if domain_value is None:
            value = None
        else:
            value = parsed.values[0]
    
    # Check if quality is bad
    bad_quality = quality is not None and quality not in allowed_quality
    if bad_quality:
        value = None
    
    # Check if value is out of range
    out_of_range = False
    if value is not None and part_rule and part_rule.kind == "numeric":
        if part_rule.min_value is not None and value < part_rule.min_value:
            value = None
            out_of_range = True
        elif part_rule.max_value is not None and value > part_rule.max_value:
            value = None
            out_of_range = True
    
    if value is not None and part_rule and part_rule.scale is not None:
        value = value * part_rule.scale
    
    # Compute QC signals
    qc_pass, qc_status, qc_reason = _compute_qc_signals(
        is_sentinel=bool(is_sentinel),
        bad_quality=bad_quality,
        out_of_range=out_of_range,
        malformed_token=malformed_token,
    )
    
    return {
        value_key: value,
        f"{prefix}__quality": quality,
        f"{prefix}__qc_pass": qc_pass,
        f"{prefix}__qc_status": qc_status,
        f"{prefix}__qc_reason": qc_reason,
    }


def _should_parse_column(values: Iterable[str]) -> bool:
    for value in values:
        if isinstance(value, str) and "," in value:
            return True
    return False


def _part_rule_for_parsed_column(column: str) -> FieldPartRule | None:
    internal = to_internal_column(column)
    if "__" not in internal:
        return None
    prefix, suffix = internal.split("__", 1)
    rule = get_field_rule(prefix)
    if rule is None:
        return None
    if suffix == "value":
        return rule.parts.get(1)
    if not suffix.startswith("part"):
        return None
    part_idx = suffix[4:]
    if not part_idx.isdigit():
        return None
    return rule.parts.get(int(part_idx))


def _cleanup_rule_missing_text(value: object, column: str) -> object:
    if not isinstance(value, str):
        return value
    part_rule = _part_rule_for_parsed_column(column)
    if part_rule is None or part_rule.missing_values is None:
        return value
    if _is_missing_value(value, part_rule):
        return None
    return value


def _cleanup_rule_missing_text_for_part_rule(
    value: object,
    part_rule: FieldPartRule,
) -> object:
    if not isinstance(value, str):
        return value
    if _is_missing_value(value, part_rule):
        return None
    return value


def _columns_requiring_missing_text_cleanup(columns: Iterable[str]) -> dict[str, FieldPartRule]:
    cleanup_columns: dict[str, FieldPartRule] = {}
    for column in columns:
        part_rule = _part_rule_for_parsed_column(column)
        if part_rule is None or part_rule.missing_values is None:
            continue
        cleanup_columns[column] = part_rule
    return cleanup_columns


def _record_structure_error(raw_line: object) -> str | None:
    """Validate fixed record structure and overall record/block size limits."""
    if raw_line is None or (isinstance(raw_line, float) and pd.isna(raw_line)):
        return None
    text = str(raw_line).rstrip("\r\n")
    actual_length = len(text)
    if actual_length > 8192:
        return "block_length_exceeds_max"
    if actual_length > 2844:
        return "record_length_exceeds_max"
    if actual_length < 105:
        return "mandatory_section_short"
    if actual_length < 4:
        return "record_length_mismatch"
    try:
        total_variable_characters = int(text[0:4])
    except ValueError:
        return "record_length_mismatch"
    expected_length = 105 + total_variable_characters
    if actual_length != expected_length:
        return "record_length_mismatch"
    return None


def _is_ascii_text(value: str) -> bool:
    try:
        value.encode("ascii")
    except UnicodeEncodeError:
        return False
    return True


def _all_nines(value: str) -> bool:
    token = value.lstrip("+-")
    return token != "" and set(token) == {"9"}


def _validate_control_header(raw_line: object) -> str | None:
    """Validate Part 02 control header fields from fixed raw-line positions."""
    if raw_line is None or (isinstance(raw_line, float) and pd.isna(raw_line)):
        return None

    text = str(raw_line).rstrip("\r\n")
    if len(text) < 60:
        return "control_header_short"

    total_variable_characters = text[0:4]
    usaf = text[4:10]
    wban = text[10:15]
    date = text[15:23]
    time = text[23:27]
    source_flag = text[27:28]
    latitude = text[28:34]
    longitude = text[34:41]
    elevation = text[41:46]
    report_type = text[46:51]
    call_sign = text[51:56]
    qc_process = text[56:60]

    fields = (
        (total_variable_characters, 4),
        (usaf, 6),
        (wban, 5),
        (date, 8),
        (time, 4),
        (source_flag, 1),
        (latitude, 6),
        (longitude, 7),
        (elevation, 5),
        (report_type, 5),
        (call_sign, 5),
        (qc_process, 4),
    )
    if any(len(value) != width for value, width in fields):
        return "control_header_invalid_width"

    if not total_variable_characters.isdigit():
        return "control_header_invalid_width"

    if not wban.isdigit():
        return "control_header_invalid_width"

    if not date.isdigit() or not time.isdigit():
        return "control_header_invalid_width"

    if not re.fullmatch(r"[+-]\d{5}", latitude):
        if _all_nines(latitude) and latitude != "+99999":
            return "control_header_invalid_sentinel"
        return "control_header_invalid_width"

    if not re.fullmatch(r"[+-]\d{6}", longitude):
        if _all_nines(longitude) and longitude != "+999999":
            return "control_header_invalid_sentinel"
        return "control_header_invalid_width"

    if not re.fullmatch(r"[+-]\d{4}", elevation):
        if _all_nines(elevation) and elevation != "+9999":
            return "control_header_invalid_sentinel"
        return "control_header_invalid_width"

    if _all_nines(latitude) and latitude != "+99999":
        return "control_header_invalid_sentinel"
    if _all_nines(longitude) and longitude != "+999999":
        return "control_header_invalid_sentinel"
    if _all_nines(elevation) and elevation != "+9999":
        return "control_header_invalid_sentinel"

    if source_flag not in DATA_SOURCE_FLAGS:
        return "control_header_invalid_domain"

    if report_type != "99999" and report_type not in REPORT_TYPE_CODES:
        return "control_header_invalid_domain"

    if not _is_ascii_text(call_sign):
        return "control_header_invalid_domain"

    if qc_process != "9999" and qc_process not in {"V01 ", "V02 ", "V03 "}:
        return "control_header_invalid_domain"

    total_value = int(total_variable_characters)
    if not (0 <= total_value <= 9999):
        return "control_header_invalid_domain"

    date_year = int(date[0:4])
    date_month = int(date[4:6])
    date_day = int(date[6:8])
    if not (0 <= date_year <= 9999 and 1 <= date_month <= 12 and 1 <= date_day <= 31):
        return "control_header_invalid_domain"
    month_lengths = {
        1: 31,
        2: 29 if (date_year % 4 == 0 and (date_year % 100 != 0 or date_year % 400 == 0)) else 28,
        3: 31,
        4: 30,
        5: 31,
        6: 30,
        7: 31,
        8: 31,
        9: 30,
        10: 31,
        11: 30,
        12: 31,
    }
    if date_day > month_lengths[date_month]:
        return "control_header_invalid_domain"

    time_hour = int(time[0:2])
    time_minute = int(time[2:4])
    if not (0 <= time_hour <= 23 and 0 <= time_minute <= 59):
        return "control_header_invalid_domain"

    lat_value = int(latitude)
    if latitude != "+99999" and not (-90000 <= lat_value <= 90000):
        return "control_header_invalid_domain"

    lon_value = int(longitude)
    if longitude != "+999999" and not (-179999 <= lon_value <= 180000):
        return "control_header_invalid_domain"

    elev_value = int(elevation)
    if elevation != "+9999" and not (-400 <= elev_value <= 8850):
        return "control_header_invalid_domain"

    return None


def _normalize_control_fields(df: pd.DataFrame) -> pd.DataFrame:
    work = df.copy()

    def _normalize_text(series: pd.Series) -> pd.Series:
        text = series.astype(str).str.strip()
        return text.where(~text.isin({"", "nan", "None"}))

    def _normalize_numeric_with_fixed_width(
        series: pd.Series,
        *,
        width: int,
        scale: float,
        min_value: float,
        max_value: float,
        missing_tokens: set[str],
    ) -> pd.Series:
        text = _normalize_text(series)
        text = text.where(~text.isin(missing_tokens))
        signed = text.str.startswith(("+", "-"), na=False)
        unsigned = text.str.replace(r"^[+-]", "", regex=True)
        integer_mask = text.str.fullmatch(r"[+-]?\d+", na=False)
        fixed_width_mask = integer_mask & (
            (signed & unsigned.str.len().eq(width - 1))
            | (~signed & unsigned.str.len().eq(width))
        )
        fixed_width_values = pd.to_numeric(text.where(fixed_width_mask), errors="coerce") / scale
        decimal_mask = text.str.contains(r"\.", regex=True, na=False)
        decimal_values = pd.to_numeric(text.where(decimal_mask), errors="coerce")
        normalized = fixed_width_values.where(fixed_width_values.notna(), decimal_values)
        return normalized.where(normalized.between(min_value, max_value))

    def _normalize_fixed_width_text(
        series: pd.Series,
        *,
        width: int,
        upper: bool = False,
        allowed_values: set[str] | None = None,
        missing_tokens: set[str] | None = None,
    ) -> pd.Series:
        text = _normalize_text(series)
        if upper:
            text = text.str.upper()
        text = text.where(text.str.len().eq(width))
        if missing_tokens:
            text = text.where(~text.isin(missing_tokens))
        if allowed_values is not None:
            text = text.where(text.isin(allowed_values))
        return text

    def _normalize_fixed_width_ascii_text(
        series: pd.Series,
        *,
        width: int,
        missing_tokens: set[str] | None = None,
    ) -> pd.Series:
        text = series.astype("string")
        text = text.where(~text.isin({"", "nan", "None", "<NA>"}))
        text = text.where(text.str.len().eq(width))
        text = text.where(text.str.fullmatch(rf"[\x20-\x7E]{{{width}}}", na=False))
        if missing_tokens:
            text = text.where(~text.isin(missing_tokens))
        normalized = text.str.rstrip()
        return normalized.where(normalized.notna() & normalized.ne(""))

    def _normalize_date(series: pd.Series) -> pd.Series:
        text = _normalize_text(series)
        match = text.str.fullmatch(r"\d{8}")
        year = pd.to_numeric(text.str.slice(0, 4), errors="coerce")
        month = pd.to_numeric(text.str.slice(4, 6), errors="coerce")
        day = pd.to_numeric(text.str.slice(6, 8), errors="coerce")

        in_spec_range = (
            match
            & year.between(0, 9999)
            & month.between(1, 12)
            & day.between(1, 31)
        )

        month_lengths = pd.Series(
            [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31],
            index=range(1, 13),
            dtype="int64",
        )
        max_day = month.map(month_lengths)
        leap_year = (year % 4 == 0) & ((year % 100 != 0) | (year % 400 == 0))
        feb_leap = (month == 2) & leap_year
        max_day = max_day.where(~feb_leap, 29)

        valid_calendar = in_spec_range & (day <= max_day)
        return text.where(valid_calendar)

    def _normalize_time(series: pd.Series) -> pd.Series:
        text = _normalize_text(series)
        match = text.str.fullmatch(r"\d{4}")
        hour = pd.to_numeric(text.str.slice(0, 2), errors="coerce")
        minute = pd.to_numeric(text.str.slice(2, 4), errors="coerce")
        valid = match & hour.between(0, 23) & minute.between(0, 59)
        return text.where(valid)

    if "LATITUDE" in work.columns:
        work["LATITUDE"] = _normalize_numeric_with_fixed_width(
            work["LATITUDE"],
            width=6,
            scale=1000.0,
            min_value=-90.0,
            max_value=90.0,
            missing_tokens={"99999"},
        )

    if "LONGITUDE" in work.columns:
        work["LONGITUDE"] = _normalize_numeric_with_fixed_width(
            work["LONGITUDE"],
            width=7,
            scale=1000.0,
            min_value=-179.999,
            max_value=180.0,
            missing_tokens={"999999"},
        )

    if "DATE" in work.columns:
        work["DATE"] = _normalize_date(work["DATE"])

    if "TIME" in work.columns:
        work["TIME"] = _normalize_time(work["TIME"])

    if "ELEVATION" in work.columns:
        work["ELEVATION"] = _normalize_numeric_with_fixed_width(
            work["ELEVATION"],
            width=5,
            scale=1.0,
            min_value=-400.0,
            max_value=8850.0,
            missing_tokens={"9999"},
        )

    if "CALL_SIGN" in work.columns:
        work["CALL_SIGN"] = _normalize_fixed_width_ascii_text(
            work["CALL_SIGN"],
            width=5,
            missing_tokens={"99999"},
        )

    if "SOURCE" in work.columns:
        series = work["SOURCE"].astype(str).str.strip().str.upper()
        series = series.where(series.isin(DATA_SOURCE_FLAGS))
        series = series.where(series != "9")
        work["SOURCE"] = series.where(series.notna())

    if "REPORT_TYPE" in work.columns:
        work["REPORT_TYPE"] = _normalize_fixed_width_text(
            work["REPORT_TYPE"],
            width=5,
            upper=True,
            allowed_values=REPORT_TYPE_CODES,
            missing_tokens={"99999"},
        )

    if "QUALITY_CONTROL" in work.columns:
        series = work["QUALITY_CONTROL"].astype(str).str.strip().str.upper()
        normalized = series.where(series.isin(QC_PROCESS_CODES))
        work["QUALITY_CONTROL"] = normalized.where(normalized.notna())

    return work


def _annotate_control_field_qc_flags(df: pd.DataFrame) -> pd.DataFrame:
    """Add deterministic control-field QC flags without rewriting source values."""
    work = df.copy()
    control_columns = [
        "LATITUDE",
        "LONGITUDE",
        "DATE",
        "TIME",
        "ELEVATION",
        "CALL_SIGN",
        "SOURCE",
        "REPORT_TYPE",
        "QUALITY_CONTROL",
    ]
    present = [column for column in control_columns if column in work.columns]
    if not present:
        return work

    normalized = _normalize_control_fields(work)
    any_invalid = pd.Series(False, index=work.index)
    for column in present:
        flag_column = f"qc_control_invalid_{column.lower()}"
        invalid_mask = work[column].notna() & normalized[column].isna()
        work[flag_column] = invalid_mask.fillna(False)
        any_invalid = any_invalid | work[flag_column]

    work["qc_domain_invalid_CONTROL"] = any_invalid.fillna(False)
    return work


def _find_duplicate_column_names(columns: Iterable[object]) -> list[str]:
    index = pd.Index(list(columns))
    duplicates = index[index.duplicated()].unique().tolist()
    return sorted(str(name) for name in duplicates)


def _rename_collisions_by_target(
    source_columns: Iterable[str],
    rename_map: dict[str, str],
) -> dict[str, list[str]]:
    by_target: dict[str, list[str]] = {}
    for source in source_columns:
        target = rename_map.get(source, source)
        internal_source = to_internal_column(source)
        by_target.setdefault(target, []).append(internal_source)

    collisions: dict[str, list[str]] = {}
    for target, internal_sources in by_target.items():
        unique_sources = sorted(set(internal_sources))
        if len(unique_sources) > 1:
            collisions[str(target)] = unique_sources
    return collisions


def _assert_unique_cleaned_columns(
    *,
    columns: Iterable[object],
    stage: str,
    rename_collisions: dict[str, list[str]] | None = None,
) -> None:
    duplicate_names = _find_duplicate_column_names(columns)
    if not duplicate_names:
        return

    message = (
        f"Duplicate cleaned column names detected (stage={stage}): "
        + ", ".join(duplicate_names)
    )
    if rename_collisions:
        relevant = {
            name: rename_collisions[name]
            for name in duplicate_names
            if name in rename_collisions
        }
        if relevant:
            details = "; ".join(
                f"{name} <- [{', '.join(sources)}]"
                for name, sources in sorted(relevant.items())
            )
            message += f". rename_collisions={details}"
    raise ValueError(message)


def clean_noaa_dataframe(
    df: pd.DataFrame,
    keep_raw: bool = True,
    strict_mode: bool = True,
) -> pd.DataFrame:
    """Expand NOAA comma-encoded fields into parsed numeric columns with QC signals.

    For fields with the pattern value,quality this will create:
    - `<column>__value`: Numeric value (scaled, None if invalid)
    - `<column>__quality`: NOAA quality code
    - `<column>__qc_pass`: Boolean - all validations passed
    - `<column>__qc_status`: String - "PASS" or "INVALID"
    - `<column>__qc_reason`: String - reason for failure (or None if PASS)

    For multi-part fields, creates:
    - `<column>__partN`: Component values
    - `<column>__partN__qc_*`: QC signals for numeric parts

    Row-level usability summary (if any QC columns exist):
    - `row_has_any_usable_metric`: Boolean - at least one metric passed QC
    - `usable_metric_count`: Integer - count of passed metrics
    - `usable_metric_fraction`: Float [0, 1] - fraction of metrics that passed

    Naming contract:
    - Distinct source identifiers remain distinct in cleaned names (`XX1` != `XX2`).
    - Per-field QC columns are attached to those prefix-specific columns.
    - Prefix-specific custom QC flags always include the full source prefix.
    - Duplicate output columns are hard-failed with stage diagnostics.

    Args:
        df: Input DataFrame with NOAA Global Hourly data
        keep_raw: If True, keep original raw columns alongside expanded ones
        strict_mode: If True, only expand known NOAA identifiers and enforce
                     validation rules (A1-A4). If False, use legacy permissive
                     parsing. Rejections are logged with [PARSE_STRICT] prefix.

    Returns:
        DataFrame with expanded, cleaned, and QC columns
    """
    cleaned = df.copy()
    rejected_mask = pd.Series(False, index=cleaned.index)
    raw_line_col = "raw_line" if "raw_line" in cleaned.columns else ("RAW_LINE" if "RAW_LINE" in cleaned.columns else None)
    if raw_line_col is not None:
        cleaned["__parse_error"] = pd.Series(pd.NA, index=cleaned.index, dtype="object")

        control_error = cleaned[raw_line_col].apply(_validate_control_header)
        control_error_mask = control_error.notna()
        if control_error_mask.any():
            rejected_mask = rejected_mask | control_error_mask
            cleaned.loc[control_error_mask, "__parse_error"] = control_error[control_error_mask]
            for error_name, error_count in control_error[control_error_mask].value_counts().items():
                logger.warning(
                    f"[PARSE_STRICT] Rejected {int(error_count)} record(s): {error_name}"
                )

        structure_error = cleaned[raw_line_col].apply(_record_structure_error)
        structure_error_mask = structure_error.notna()
        if structure_error_mask.any():
            rejected_mask = rejected_mask | structure_error_mask
            no_prior_error = structure_error_mask & cleaned["__parse_error"].isna()
            cleaned.loc[no_prior_error, "__parse_error"] = structure_error[no_prior_error]
            for error_name, error_count in structure_error[no_prior_error].value_counts().items():
                logger.warning(
                    f"[PARSE_STRICT] Rejected {int(error_count)} record(s): {error_name}"
                )

    if "ADD" in cleaned.columns:
        add_series = cleaned["ADD"].astype(str).str.strip().str.upper()
        add_mask = add_series.replace("", pd.NA).dropna().eq("ADD")
        if add_mask.empty or add_mask.all():
            cleaned = cleaned.drop(columns=["ADD"])

    source_columns = list(cleaned.columns)

    # Priority parsing: handle REM before generic expansion to preserve typed parsing (step 2)
    processed_columns = set()
    if "REM" in cleaned.columns:
        remark_types = []
        remark_texts = []
        remark_type_lists = []
        remark_text_lists = []
        for value in cleaned["REM"]:
            structured = None
            if value is not None and not (isinstance(value, float) and pd.isna(value)):
                text = str(value).strip()
                if text not in {"", "nan", "None"}:
                    structured = _parse_structured_remark(text)
            if structured is None:
                remark_type, remark_text = _parse_remark(value)
                remark_types.append(remark_type)
                remark_texts.append(remark_text)
                remark_type_lists.append(None)
                remark_text_lists.append(None)
                continue
            remark_type, remark_text, remark_types_csv, remark_texts_json = structured
            remark_types.append(remark_type)
            remark_texts.append(remark_text)
            remark_type_lists.append(remark_types_csv)
            remark_text_lists.append(remark_texts_json)
        cleaned["REM__type"] = remark_types
        cleaned["REM__text"] = remark_texts
        cleaned["REM__types"] = remark_type_lists
        cleaned["REM__texts_json"] = remark_text_lists
        processed_columns.update(
            {"REM", "REM__type", "REM__text", "REM__types", "REM__texts_json"}
        )
    if "QNN" in cleaned.columns:
        processed_columns.add("QNN")

    expansion_frames: list[pd.DataFrame] = []

    for column in source_columns:
        # Skip columns already processed by priority parsing
        if column in processed_columns:
            continue

        series = cleaned[column]
        if not pd.api.types.is_object_dtype(series) and not pd.api.types.is_string_dtype(series):
            continue
        sample = series.dropna().astype(str).head(200)
        if sample.empty or not _should_parse_column(sample):
            continue

        # A1: Strict mode allowlist gate - only expand known NOAA identifiers.
        # Evaluate this only for columns that actually look parseable so metadata
        # columns like STATION/DATE do not emit reviewer-facing noise.
        if strict_mode:
            section_identifier_valid = is_valid_section_identifier_token(column)
            if section_identifier_valid is False:
                logger.warning(
                    f"[PARSE_STRICT] Skipping malformed section identifier token: {column}"
                )
                continue

            known_identifier = (
                column in KNOWN_IDENTIFIERS
                or is_valid_eqd_identifier(column) is True
                or is_valid_repeated_identifier(column) is True
            )
            if not known_identifier:
                # Skip expansion for unknown identifiers, keep raw column.
                logger.warning(f"[PARSE_STRICT] Skipping unknown identifier: {column}")
                continue

        parsed_rows = []
        normalized_values = series.fillna("").astype(str)
        for is_rejected, value in zip(rejected_mask.to_numpy(dtype=bool), normalized_values, strict=False):
            if is_rejected:
                parsed_rows.append({})
                continue
            if value == "":
                parsed_rows.append({})
                continue
            payload = clean_value_quality(value, column, strict_mode=strict_mode)
            parsed_rows.append(payload)

        expanded = pd.DataFrame(parsed_rows, index=cleaned.index)
        expansion_frames.append(expanded)
        if not keep_raw:
            cleaned = cleaned.drop(columns=[column])

    if expansion_frames:
        cleaned = pd.concat([cleaned] + expansion_frames, axis=1)

    # QNN parsing (REM already handled in priority parsing above)
    if "QNN" in cleaned.columns:
        qnn_elements = []
        qnn_flags = []
        qnn_values = []
        for value in cleaned["QNN"]:
            element_ids, source_flags, data_values = _parse_qnn(value)
            qnn_elements.append(element_ids)
            qnn_flags.append(source_flags)
            qnn_values.append(data_values)
        cleaned["QNN__elements"] = qnn_elements
        cleaned["QNN__source_flags"] = qnn_flags
        cleaned["QNN__data_values"] = qnn_values

    cleanup_columns = _columns_requiring_missing_text_cleanup(cleaned.columns)
    for column, part_rule in cleanup_columns.items():
        series = cleaned[column]
        if not pd.api.types.is_object_dtype(series) and not pd.api.types.is_string_dtype(series):
            continue
        cleaned[column] = series.apply(
            lambda value, column_part_rule=part_rule: _cleanup_rule_missing_text_for_part_rule(
                value,
                column_part_rule,
            )
        )

    cleaned = _annotate_control_field_qc_flags(cleaned)
    _assert_unique_cleaned_columns(columns=cleaned.columns, stage="pre_rename")

    rename_map = {col: to_friendly_column(col) for col in cleaned.columns}
    rename_collisions = _rename_collisions_by_target(cleaned.columns, rename_map)
    _assert_unique_cleaned_columns(
        columns=[rename_map.get(col, col) for col in cleaned.columns],
        stage="post_rename",
        rename_collisions=rename_collisions,
    )
    if any(key != value for key, value in rename_map.items()):
        cleaned = cleaned.rename(columns=rename_map)

    # Add row-level usability metrics based on QC columns
    qc_pass_columns = [col for col in cleaned.columns if col.endswith("__qc_pass")]
    if qc_pass_columns:
        # Create row summaries
        cleaned["row_has_any_usable_metric"] = cleaned[qc_pass_columns].any(axis=1)
        cleaned["usable_metric_count"] = cleaned[qc_pass_columns].sum(axis=1)
        total_metrics = len(qc_pass_columns)
        cleaned["usable_metric_fraction"] = (
            cleaned["usable_metric_count"] / total_metrics
            if total_metrics > 0
            else 0.0
        )

    _assert_unique_cleaned_columns(columns=cleaned.columns, stage="final")

    return cleaned
