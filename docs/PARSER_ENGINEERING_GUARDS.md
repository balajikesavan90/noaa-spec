# Parser Engineering Guards

This document describes strict parser safeguards that protect data integrity and deterministic outputs without changing scientific values.

## Why These Guards Exist

The NOAA ISD payload mixes fixed-width control records and comma-encoded variable sections. Structural corruption can misalign tokens, causing downstream fields to be parsed into the wrong columns. Engineering guards prevent malformed records from silently contaminating cleaned outputs.

These safeguards are intentionally conservative:

- they reject or isolate structurally invalid records,
- they preserve deterministic parse behavior across runs,
- they prevent schema drift caused by malformed identifiers,
- they do not redefine valid observed meteorological values.

## Guard Types

## Arity and Width Guards

`_expand_parsed` enforces token-width and token-format checks in strict mode. When a token fails width/pattern checks, the token is marked malformed and its parsed value is not trusted.

`get_expected_part_count` is used by `clean_value_quality` to verify expected field arity. For strict-guarded identifiers, truncated/extra payloads are rejected or flagged before aggregation.

These checks protect parser integrity by ensuring part positions remain stable.

## Control Header Structural Guards

`_validate_control_header` validates fixed-position Part 02 control fields (lengths, signed numeric encodings, sentinel shape, source/report/QC domains, and date/time calendar validity).

`_record_structure_error` validates whole-record size/length consistency (`record_length_mismatch`, `record_length_exceeds_max`, `block_length_exceeds_max`, `mandatory_section_short`).

These checks detect corruption in raw record framing and prevent invalid control structures from being treated as valid observations.

## Identifier and Expansion Guards

Strict-mode expansion only parses known NOAA identifiers and valid repeated/EQD identifiers. Malformed or unknown identifiers are kept as raw columns and not expanded.

This behavior prevents accidental parsing of non-NOAA metadata columns and malformed identifiers into scientific metric columns.

## Guard Behavior vs Scientific Semantics

Engineering guards are not scientific filters. They do not impose additional climatological thresholds. Instead, they:

- constrain parser input shape,
- enforce deterministic null/error semantics for malformed tokens,
- preserve publication-contract stability for cleaned schemas.

Where values are structurally parseable but semantically uncertain, the pipeline now prefers QC flags over hard rewrites/nulling for selected rule families.
