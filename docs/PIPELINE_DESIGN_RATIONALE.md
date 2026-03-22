# Pipeline Design Rationale: NOAA ISD Specification-Constrained Cleaning

## Problem Statement

NOAA's Integrated Surface Database (ISD) Global Hourly Archive publishes raw observation data in conformance with the ISD format specification — a dense technical document (30+ parts) defining fixed-width field layouts, sentinel values, quality codes, domain constraints, and numeric scaling rules across dozens of weather variables. Three properties make end-to-end specification compliance exceptionally difficult:

1. **Fixed-width + comma-encoding complexity**: The ISD format combines fixed-position control fields with comma-delimited additional-data blocks. Each block may contain multiple comma-separated parts (e.g., wind = direction, quality, type, speed quality) with field-specific sentinel values (wind direction = 999 missing; temperature = +9999 missing). Generic CSV expansion collapses semantic structure and falsely creates missing-value conflicts.

2. **Sentinel and scale heterogeneity**: Sentinels are not uniform across the specification. Wind direction uses 3-digit codes (999), temperature uses 5-digit signed tokens (+9999), visibility uses 6-digit values (999999). Signed sentinels (e.g., +9999 for temperature exclusive of valid negatives down to -9999) must be distinguished from unsigned ones. Scale factors (÷10 for many temperature/pressure/wind fields) apply selectively. Zero coverage of these rules causes silent data corruption — missing values leak into numeric summaries and scale misalignment skews all derived metrics.

3. **Multi-identifier families and partial specification**: The format defines ~867 field identifiers grouped into families (control, mandatory, additional meteorological, present weather, network metadata, equipment QC, etc.). The working specification source is now a single deterministic markdown export of the NOAA PDF, but the cleaning and coverage systems still need to derive the historical Part 01-30 grouping from ordered section anchors. Implementation requires tracing rule implications across those derived parts and governing quality-code domains, missing-value sentinels, numeric ranges, and cardinality constraints per identifier. Spec gaps and ambiguities (fields mentioned in summaries but absent from detailed tables; repeated-identifier bounds inconsistently documented) necessitate judgement calls backed by evidence.

The primary objective is to **transform raw ISD CSV rows into a deterministically cleaned dataset where every field conforms to its specification rules**: sentinels nullified, scale factors applied, quality codes enforced, and domain values validated — all trackable through an auditable rule inventory tied to specification line ranges and evidence of code/test coverage.

---

## Architecture Overview

The cleaning pipeline is organized into **specification-driven rule extraction**, **implementation enforcement** across two layers (constants + cleaning logic), and **coverage measurement** to track which specification rules are implemented and tested. Three components interact:

### 1. Specification Parsing & Rule Extraction (`tools/spec_coverage/generate_spec_coverage.py`)

The spec coverage generator parses the deterministic NOAA markdown source at `isd-format-document-parts/isd-format-document.deterministic.md` and extracts a structured **rule inventory** with deterministic identifiers and provenance. A segmentation pass first derives the legacy Part 02-30 slices from exact anchor lines in document order, then the extractor applies rule heuristics within those slices. Extraction recognizes four rule types — **range** (min/max numeric bounds), **sentinel** (missing-value indicators), **domain** (allowed code sets), and **width** (fixed-field length) — plus two quality-specific types, **allowed_quality** and **arity** (expected comma-separated part count).

Each extracted rule becomes a `SpecRuleRow` with:
- **rule_id**: Deterministic identifier formed from `spec_file::stable_id::identifier::rule_type::payload_hash`, where `stable_id` is content-based and does not depend on line positions.
- **identifier**: 2–6 character field code (e.g., TMP, WND, GE1, OA1).
- **identifier_family**: Inferred from identifier prefix (e.g., O→wind, G→solar, K→temperature extremes).
- **spec_part**: Part number (01–30).
- **spec_line_start / spec_line_end**: Global text line range in `isd-format-document.deterministic.md` where rule is evidenced.
- **rule_type**: One of `range`, `sentinel`, `domain`, `allowed_quality`, `width`, `arity`, `cardinality`.
- **payload fields**: `min_value`, `max_value`, `sentinel_values`, `allowed_values_or_codes` — normalized numeric tokens or code sets.

Regex extractors target patterns like `MIN: 999`, `Missing = +9999`, `Allowed: 0-9, 99`, `POS: 1-5`, and `up to 6 parts`. Since the spec is human-authored and irregular, extraction tolerates whitespace variance and numeric-token normalization (stripping leading zeros, normalizing sign placement). An **identifier frequency heuristic** distinguishes genuine field codes from incidental numbers.

### 2. Rule Enforcement Layers (`src/noaa_spec/constants.py` and `src/noaa_spec/cleaning.py`)

Rules are **operationalized across two separation-of-concerns layers**:

#### **Constants Layer** (`src/noaa_spec/constants.py`)
Declarative specification of field metadata via `FieldRule` and `FieldPartRule` dataclasses. Each field rule encodes:
- Cardinality (expected comma-part count for multi-part fields).
- Per-part metadata: `allowed_values`, `allowed_pattern`, `missing_values`, `scale_factor`, `token_width`, `kind` (numeric vs. categorical).
- Quality-code domain per field (e.g., WND restrictive quality ∈ {0–7, 9}; generic fallback ∈ {0–7, 9, A, C, I, M, P, R, U}).

The constants layer is **machine-readable provenance**: every entry maps to a spec location and can be traced back to a rule_id. Constants enforcement is deterministic and side-effect-free, making it ideal for testing and for building the rule index.

#### **Cleaning Layer** (`src/noaa_spec/cleaning.py`)
Imperative logic that applies field rules **during data transformation**:
1. **Parse field** — expand comma-delimited payloads into parts and detect/apply scale factors.
2. **Validate domain** — reject non-enumerated codes.
3. **Detect sentinels** — apply per-field missing-value rules and null matching tokens.
4. **Quality gate** — null values whose quality code signals invalidity.
5. **Emit outputs** — structured columns: `<field>__value`, `<field>__quality`, `<field>__partN`.

**Enforcement layers** in the rule inventory track where rules are applied:
- **constants_only**: Rule enforced purely via constants metadata (e.g., quality-code domain tables).
- **cleaning_only**: Logic checks are embedded in cleaning functions; constants are shallow or absent.
- **both**: Rule is codified in constants AND checked in cleaning functions.
- **neither**: Rule extracted from spec but not yet operationalized (gap).

### 3. Coverage Measurement (`spec_coverage.csv` and `SPEC_COVERAGE_REPORT.md`)

After extraction and implementation indexing, the generator runs **test evidence matching**: for each rule, it scans test files for evidence of validation. Three **match strengths** identify test coverage:

- **exact_signature**: Test contains the exact field+rule_type+payload parameters.
- **exact_assertion**: Test checks the specific field+rule_type but with generic/wildcard values.
- **family_assertion**: Test validates the identifier family (e.g., all temperature fields) for the rule_type.
- **wildcard_assertion**: Test covers the rule_type (e.g., all range checks) regardless of identifier.
- **none**: No test evidence detected.

Two **coverage KPIs**:
- **test_covered_strict**: Sum of exact_signature + exact_assertion + family_assertion. Reflects high-confidence test-to-rule binding.
- **test_covered_any**: Sum of all non-none strengths, including wildcard. Permits coarser coverage but allows weak-match visibility.

The **progress KPI** is **test_covered_strict** only; wildcard-only tests do not count toward the published coverage percentage. This is intentional: wildcard tests validate structure (e.g., "all field ranges are numeric") but do not prove identifier-specific rule correctness.

---

## Data Flow & Boundaries

```
Deterministic spec markdown (isd-format-document-parts/isd-format-document.deterministic.md)
    ↓ [Fail-fast segmentation by exact section anchors]
Derived Part 02-30 slices with global line provenance
    ↓ [Regex extraction + heuristic identifier detection]
Extracted rules (SpecRuleRow list, ~3,500+ rows)
    ↓ [Rule deduplication via rule_id]
Deduplicated rule inventory with provenance
    ↓ [AST scanning of constants.py + cleaning.py]
Evidence index (field rules, cleaning function calls, AST hints)
    ↓ [Merge rule rows with evidence]
Hybrid rows (spec + implementation + enforcement layer)
    ↓ [Test file scanning + signature matching]
Final rows with test coverage metadata
    ↓ [CSV write + markdown report generation]
spec_coverage.csv | SPEC_COVERAGE_REPORT.md
```

**Process boundaries:**
- **Spec → Rules**: Extraction is deterministic (same input → same output) but heuristic (regex-based, no semantic parsing). Extraction errors (missed rules, false positives) propagate downstream.
- **Rules → Implementation Evidence**: AST scanning of constants and cleaning functions is deterministic but imperfect. Heuristics detect calls to `get_field_rule()`, pattern matches in function names, and hard-coded sentinel literals. Evidence is conservative: a rule without code evidence is flagged as "neither" layer, even if cleaning functions have ad-hoc logic.
- **Implementation → Tests**: Test scanning uses method-signature matching and assertion-text parsing. A test like `assert _is_missing_value("+9999", rule)` matches rule_id={identifier=TMP, rule_type=sentinel, sentinel_values=+9999} with strength exact_signature. Weakly-written tests (that don't pass field or rule_type context) match as wildcard_assertion and do not count toward strict coverage.
- **Output**: CSV schema is stable (OUTPUT_COLUMNS list, 30 columns). Rows are sortable by (spec_file, spec_line_start, identifier, rule_type, rule_id).

---

## Key Design Choices & Rationale

### 1. Deterministic Rule Extraction vs. LLM-Only Parsing

**Choice**: Extract rules via **handcrafted regex patterns** applied to spec markdown, with deduplication by rule_id, rather than prompting an LLM to "understand" the entire spec and generate field metadata.

**Rationale**:
- **Auditability**: Every extracted rule is tied to a global line range in `isd-format-document.deterministic.md`. A user can open the deterministic markdown and verify the exact source snippet directly.
- **Stability**: Regex extraction is deterministic. Running the generator twice on the same spec produces identical output (same rule_id hash, same deduplication).
- **Evolutionary**: As the spec document is updated or clarified, extraction rules can be refined incrementally. Versioned spec → versioned rule inventory is explicit and auditable.
- **Limitation**: Heuristic regex-based extraction will miss rules phrased unexpectedly or misinterpret ambiguous text. Extraction quality depends on spec document consistency and regex coverage (see Limitations).

**Alternative (rejected)**: Use a language model to generate field metadata from spec. Pros: Could handle varied phrasing; might infer implicit constraints. Cons: Non-deterministic (LLM output varies by temperature, version); expensive (API calls per run); opaque provenance (impossible to map back to spec text for validation); high false-positive/false-negative rates on numeric bounds and sentinel codes. For a specification-compliance tool, auditability and stability outweigh inference capability.

### 2. Spec Coverage as a Measurable Target

**Choice**: Generate a CSV rule inventory with coverage metrics (implemented_in_code, test_covered_strict, enforcement_layer) and publish a report. Use **test_covered_strict** as the progress KPI, not implementation alone.

**Rationale**:
- **Transparency**: Gaps between specification and implementation are visible. Every rule has a status (implemented? tested? both?). Report ranks gaps by rule_type and identifier family, making prioritization data-driven.
- **Enforcement**: Without oversight, implementation diverges from spec. A developer might implement wind-speed validation but forget its arity constraint (speed should always be paired with quality). Tracking coverage surfaces omissions.
- **Coordination**: The rule_id uniquely identifies a specification rule. When a developer fixes a gap, they reference the rule_id, linking code to spec intent. Test and implementation changes are connected.
- **Metric stability**: test_covered_strict counts only high-confidence test-to-rule bindings (exact_signature, exact_assertion, family_assertion). This prevents misleading inflation from wildcard tests (e.g., one generic "all fields are numeric" test falsely claiming coverage of 100+ numeric-range rules).

**Limitation**: Coverage metrics do not measure *implementation correctness at scale*. A rule can be test-covered but implemented incorrectly (e.g., a sentinel-detection test that uses the wrong sentinel value). Integration tests (Limitation 4) mitigate this.

### 3. test_covered_strict vs. test_covered_any (Wildcard Policy)

**Choice**: Distinguish `test_covered_strict` (exact, family, or exact_assertion matches) from `test_covered_any` (includes wildcard), and report progress only on strict. Wildcard matches remain visible in reports but do not count toward the KPI.

**Rationale**:
- **Precision**: A test that checks `"for all fields in ['TMP', 'DEW', 'SLP'], if rule_type=='range', assert min ≤ value ≤ max"` validates structural correctness but does not prove that TMP's specific range (−999 to +500, ÷10) is correct. Only an exact_signature or family_assertion match confirms identifier-specific correctness.
- **Encouragement**: Wildcard tests are useful during early-stage development (quick validation that all fields parse without crashing). But they mask gaps. By excluding them from the progress KPI, we incentivize developers to write targeted tests for repeated-identifier families (e.g., OA1–OA3, MV1–MV7) and identifier-specific sentinel handling.
- **Audit trail**: The `test_match_strength` column in the CSV makes wildcard coverage visible. Users can filter for `wildcard_assertion` rows to find tests that need tightening.

**Alternative (rejected)**: Count all test matches toward progress. Risk: Developers rely on cheap wildcard tests and never write family-level tests. Rule inventory becomes high-coverage-percentage but shallow-validation. Specification compliance requires depth.

### 4. Constants vs. Cleaning Separation & Enforcement Layers

**Choice**: Separate **declarative metadata** (rules, bounds, code sets in `constants.py` dataclasses) from **imperative logic** (parsing, validation, nulling in `cleaning.py` functions). Track whether each rule is enforced via constants_only, cleaning_only, both, or neither.

**Rationale**:
- **Discoverability**: A field rule in constants is a single data structure:  
  ```python
  FieldRule(
      identifier='TMP',
      parts={
          1: FieldPartRule(kind='numeric', scale_factor=0.1, missing_values={'+9999', '+99999'}, min_value=-999, max_value=500)
      }
  )
  ```
  A developer can inspect this without reading 200 lines of cleaning code. Tests can reuse FieldRule directly.

- **Composition**: Constants can be composed (e.g., a base FieldRule for temperature, inherited/extended for subfields like KA extreme temperature, CB CRN temperature). Cleaning logic can reference the same rule object multiple times (different callers all enforce the same domain).

- **Auditability**: Constants encode specification intent in source form (not hidden in control flow). A code review can compare constants against the spec markdown side-by-side. Diff history shows when rules were added or changed.

- **Generalization**: Cleaning logic can be written once for all range rules, all domain rules, etc., reading their parameters from constants. New fields can be added without modifying cleaning logic.

**Limitation**: Separation introduces complexity. A developer must know whether a rule belongs in constants (declarative) or cleaning (imperative). For most rules (ranges, sentinels, domains), constants suffice. For a few (e.g., cardinality validation for variable-length repeated-identifiers, Part 30 EQD legacy parameter-code handling), cleaning_only logic is warranted. The enforcement_layer field in the coverage report documents these decisions.

### 5. Rule_id Format: Content-Based Identity + Separate Provenance

**Choice**: Generate rule_id as `{spec_file}::{stable_id}::{identifier}::{rule_type}::{payload_hash}` for spec-sourced rules, where `stable_id` is derived from normalized rule text, identifier, rule_type, and canonical payload JSON.

**Rationale**:
- **Determinism**: The same extracted rule always gets the same rule_id across runs. Deduplication is stable.
- **Line-shift resilience**: Edits that only move the rule within the deterministic markdown do not churn the rule_id.
- **Provenance**: The source lines remain available in `spec_line_start` and `spec_line_end`, so traceability is preserved without making line position part of identity.
- **Payload hashing**: The rule_id distinguishes `{TMP, range, min=−999, max=500}` from `{TMP, range, min=−1000, max=500}` so overlapping or corrected rules do not collide.

**Limitation**: Content-based identity still changes if the normalized rule text or canonical payload changes. If a rule_id is cited in external tooling or documentation, the citation can still break after a real spec edit. Mitigation: Use git history (`git log --grep="rule_id"`) to track rule evolution. Avoid hardcoding rule_ids in external systems; instead, reference the `(spec_part, identifier, rule_type)` tuple plus provenance lines when needed.

---

## Implementation Gaps & Limitations

### 1. False Positives in Regex Extraction

**Problem**: Regex extractors may match incidental numbers or text fragments as rules.  
**Example**: Part-title text like "Part 15: Cloud Data — Ranges: 0 to 99" might trigger a `range` rule extraction for an unrelated identifier.  
**Impact**: Extracted rule inventory includes spurious rows. Deduplication (rule_id hashing) reduces impact, but human manual review of the top 50 gaps in SPEC_COVERAGE_REPORT.md is necessary before declaring a rule "truly unimplemented."  
**Mitigation**: Identifier frequency heuristic (IDENTIFIER_RE pattern, requiring 2–6 uppercase alphanumeric characters) filters junk. Extractors target specific context patterns (e.g., "MIN/MAX" adjacent to numeric tokens, not isolated numbers). High-confidence patterns (POS regex matching position ranges) are prioritized.

### 2. False Negatives in Extraction

**Problem**: Spec rules phrased unusually or stored in tables instead of prose are missed.  
**Example**: A rule stated as "Wind direction is [001–360] or [999]" may not match the MIN_MAX_INLINE_RE pattern if brackets are used instead of "MIN/MAX" keywords.  
**Impact**: Rule inventory is incomplete. A developer implements the rule in code, but the coverage report shows it as "not extracted" and thus "never tested" (since test evidence is matched only to extracted rules).  
**Mitigation**: Iteratively improve extractors after reviewing gaps. Add new regex patterns for newly-discovered phrasing patterns and update the segmentation anchor table if NOAA changes the source document structure.

### 3. Weak Test Evidence Matching

**Problem**: Test-to-rule matching via method signature and assertion text is imperfect.  
**Example**: A test function `def test_wind_validation():` with assertion `assert validate_wind(data) is not None`, provides no structured hint about which rule_type it tests. The matcher may classify it as `wildcard_assertion` (rule_type only) instead of `exact_assertion` (field + rule_type).  
**Impact**: Coverage metrics underestimate true testing. Developers may not realize a rule is already tested and write redundant tests.  
**Mitigation**: Establish test-naming and assertion-structure conventions. E.g., test names follow `test_{identifier}_{rule_type}_{variant}` (e.g., `test_tmp_sentinel_positive_9999`). Assertions use assertion helper functions that include rule context (e.g., `assert_sentinel(field='TMP', sentinel='+9999', value='+9999')`). Refactor test files to improve structure; see test_cleaning.py for examples.

### 4. Coverage Misalignment: Tests Exist Without Code Implementation

**Problem**: A test may exist for a rule that is not yet implemented in constants or cleaning functions.  
**Example**: test_cleaning.py contains a test for OA supplementary-wind speed range (0000–2000, 9999 missing) but the Constants-layer field rule for OA1/OA2 does not encode this range, and cleaning.py does not validate it.  
**Impact**: test_covered_strict is inflated; implementation_confidence is misleading; tests pass against a stub but would reveal gaps if run against live data.  
**Mitigation**: Coverage report includes a dedicated `implementation_gaps` section listing rules where `test_covered_strict=TRUE` but `code_implemented=FALSE`. Developers should implement rules before or in parallel with tests, not after.

### 5. Arity Rule Type Under-Tested

**Problem**: Arity (expected comma-part count) rules are extracted from spec but rarely have exact_signature test matches due to the difficulty of writing generic arity tests.  
**Example**: Rule: WND has arity=5 (direction, quality, type, speed, speed_quality). A test validating arity must pass a malformed `WND=1,2,3` (only 3 parts) and assert it fails. Tests in test_cleaning.py do this for TMP/WND, but not for all identifiers.  
**Current status**: test_covered_strict for arity rules is ~30%; most arity rules are marked `none` or `family_assertion`.  
**Planned**: Expand arity test coverage via parameterized tests and a dedicated arity validation test suite.

### 6. Width Rule Extraction Incomplete

**Problem**: Spec defines fixed-width token formats for many fields (e.g., WND part4 = 4 digits, TMP part1 = 5 tokens including sign), but width rules are irregularly phrased in the spec.  
**Example**: "POS: 1–5" means field starts at position 1, width 5. Extractors find this; but width rules are often inferred from position ranges (POS 1–5 → width 5) rather than explicit "FLD LEN" keywords.  
**Current status**: ~200 width rules extracted; ~50 test_covered (mostly WND, TMP). Remaining width rules are marked `neither`.  
**Impact**: Truncated or padded tokens may pass cleaning when they should be rejected. An example: `WND=1,1,N,50,1` (speed token "50" instead of 4-digit "0050") silently accepts the token instead of flagging it as malformed.  
**Planned**: Expand width rule coverage and write parameterized width-validation tests for mandatory-section and additional-section field families.

### 7. EQD (Equipment QC / Part 30) Complex Structure

**Problem**: Part 30 original-observation blocks (QNN) encode nested structure (header + repeated element blocks) with legacy parameter codes and format nuances. Specification of EQD handling is complex and scattered across 30-language code tables.  
**Current status**: QNN parsing is partially implemented; part-30 rule coverage is ~40% strict.  
**Limitations**: 
  - Repeated-identifier bounds (e.g., Q00–Q99, P00–P99, R00–R99, etc.) are inferred from context; exact cardinality is not always specified.
  - Legacy parameter codes (e.g., `APC3`, `PRSWA1`) use inconsistent formatting; validation patterns are heuristic.
  - ASCII payload preservation (Part 30 specifies 6-character ASCII token fields) conflicts with blanket nulling of all-9 values, which can erase valid data payloads.
  
**Planned**: Fully specify EQD arity, parameter-code domain, and payload normalization rules; write targeted tests for the 50+ EQD identifiers.

---

## How to Reproduce

### Prerequisites
- Python ≥ 3.12
- Poetry
- Repository structure: `tools/spec_coverage/`, `src/noaa_spec/`, `tests/`, `isd-format-document-parts/`

### Generate the Rule Inventory & Coverage Report

```bash
# From workspace root
cd /path/to/noaa-climate-data

# Generate spec_coverage.csv and SPEC_COVERAGE_REPORT.md
python tools/spec_coverage/generate_spec_coverage.py
```

Outputs:
- `spec_coverage.csv` — Full rule inventory with 30 columns (rule_id, identifier, rule_type, enforcement_layer, implementation_confidence, test_coverage).
- `SPEC_COVERAGE_REPORT.md` — Markdown summary with overall coverage %, top gaps, and distribution by rule_type.

### Run Tests

```bash
# All tests
poetry run pytest tests/ -v

# Cleaning tests (rule enforcement validation)
poetry run pytest tests/test_cleaning.py -v

# Aggregation tests (output column classification)
poetry run pytest tests/test_aggregation.py -v

# Integration tests (end-to-end cleanup on 11 real stations)
poetry run pytest tests/test_integration.py -v

# Spec coverage generator tests (rule extraction and indexing)
poetry run pytest tests/test_spec_coverage_generator.py -v
```

### Inspect Coverage Gaps

Open `SPEC_COVERAGE_REPORT.md` and review the top-50 `real_gaps` table. Each row shows:
- `spec_part`: Which ISD specification part (01–30).
- `identifier`: Field code (e.g., TMP, WND, OA1).
- `rule_type`: One of range, sentinel, domain, width, arity.
- `enforcement_layer`: constants_only, cleaning_only, both, or neither.
- `implemented`: Boolean; whether code enforces the rule.
- `test_strict`: Boolean; whether test_covered_strict is TRUE.
- `notes`: Coverage annotations emitted by the generator (for example `coverage_reason_cleaning=none`).

Filter by `implemented=FALSE` to find unimplemented rules. Filter by `enforcement_layer=neither` to find rules with zero enforcement.

### Trace a Rule to Source Spec

Extract the `rule_id` from the CSV, e.g., `isd-format-document.deterministic.md::4c2d8e1f0a6b::WND::range::abc123def4`.

1. Open `isd-format-document-parts/isd-format-document.deterministic.md`.
2. Navigate to the row's `spec_line_start` and `spec_line_end` values.
3. Confirm that the rule text matches the rule_id's assertion.

Example spec excerpt (Part 3, Mandatory Data Section):
```
WND — Wind-observation
  POS: 25-30
  FLD LEN: 6
  Mandatory; variable-byte-delimited field.
  Part 1 (3 bytes): Direction angle in DDDDD format (001-360 or 999 missing).
  Part 2 (1 byte): Quality code (0-7 or 9).
  Parts 3-5: Type code, speed, speed-quality.
  ...
```

### Edit Constants and Re-Run Tests

To implement a rule (e.g., OA1 speed range):

1. Edit `src/noaa_spec/constants.py`, add/update FieldRule for OA1:
   ```python
   "OA1": FieldRule(
       identifier="OA1",
       parts={
           1: FieldPartRule(kind='numeric', min_value=0, max_value=2000, missing_values={'9999'}),
           ...
       }
   )
   ```

2. Re-run the spec coverage generator:
   ```bash
   python tools/spec_coverage/generate_spec_coverage.py
   ```

3. Check the updated CSV for OA1 range rule:
   ```bash
   grep "OA1.*range" spec_coverage.csv
   ```
   Column `implemented_in_constants` should now be `TRUE`.

4. Write a test in `tests/test_cleaning.py`:
   ```python
   def test_oa1_speed_range():
       rule = get_field_rule("OA1").parts[1]
       assert rule.min_value == 0
       assert rule.max_value == 2000
       # Test actual enforcement
       field = parse_field("OA1", "1500,1,2")  # valid speed
       assert field.values[0] == 1500
       
       field = parse_field("OA1", "2500,1,2")  # speed > max
       assert field.values[0] is None  # should be nulled
   ```

5. Run the test:
   ```bash
   poetry run pytest tests/test_cleaning.py::test_oa1_speed_range -v
   ```

6. Re-run spec coverage to confirm test is matched:
   ```bash
   python tools/spec_coverage/generate_spec_coverage.py
   grep "OA1.*range" spec_coverage.csv | grep "test_covered_strict"
   ```

---

## Summary

This pipeline embodies a specification-driven approach to data cleaning: extract rules from authoritative documentation, implement them declaratively (constants) and imperatively (logic), and measure compliance through a rule inventory tied to specification provenance and test evidence. Gaps are visible, ranked by impact, and tied to spec locations for resolution. The design trades complexity (a rule extractor + coverage index) for transparency and auditability — essential properties for compliance-critical data workflows.
