# NOAA ISD Cleaning Pipeline Validation Plan

**Version:** 2.0  
**Last Updated:** 2026-03-08  
**Status:** Active

---

## 1. Purpose

This validation plan defines the executable checks required to keep the
specification-constrained cleaning system and publication artifacts trustworthy.

A validation run is successful only when:

1. parser/cleaner behavior remains deterministic,
2. spec-rule coverage artifacts regenerate without drift,
3. suspicious-coverage mismatch remains zero,
4. publication-facing docs reference existing commands, scripts, tests, and artifacts.

---

## 2. Authoritative Validation Artifacts

These generated artifacts are the current source of truth for rule and coverage status:

- `spec_coverage.csv`
- `docs/reports/SPEC_COVERAGE_REPORT.md`
- `RULE_PROVENANCE_LEDGER.csv`
- `docs/reports/RULE_PROVENANCE_LEDGER.md`
- `docs/reports/RULE_IMPACT_REPORT.md`
- `rule_impact_summary.csv`
- `rule_family_impact_summary.csv`
- `docs/reports/validation_artifacts/suspicious_coverage/suspicious_summary.md`

---

## 3. Required Test Tracks

Run these tests before claiming validation completion.

### 3.1 Full Repository Test Suite

```bash
poetry run pytest tests/ -v
```

### 3.2 Focused Safety Suites

```bash
poetry run pytest tests/test_cleaning.py -v
poetry run pytest tests/test_qc_comprehensive.py -v
poetry run pytest tests/test_spec_coverage_generator.py -v
poetry run pytest tests/test_suspicious_coverage_integrity.py -v
poetry run pytest tests/test_documentation_integrity.py -v
```

### 3.3 Integration and Publication-Surface Checks

```bash
poetry run pytest tests/test_integration.py -v
poetry run pytest tests/test_cleaning_runner.py -v
poetry run pytest tests/test_domain_split.py -v
```

---

## 4. Required Artifact Generation Commands

Regenerate the rule/coverage artifacts with current tooling:

```bash
poetry run python tools/spec_coverage/generate_spec_coverage.py
poetry run python tools/spec_coverage/export_suspicious_summary.py
poetry run python tools/spec_coverage/generate_rule_provenance_ledger.py
poetry run python tools/rule_impact/generate_rule_impact_report.py
```

If any generated artifact changes unexpectedly, review and explain the diff
before merge.

---

## 5. Documentation Integrity Gate

The following docs must stay executable and in-sync with repository reality:

- `README.md`
- `docs/PIPELINE_DESIGN_RATIONALE.md`
- `docs/PIPELINE_VALIDATION_PLAN.md`
- `docs/architecture/ARCHITECTURE_NEXT_STEPS.md`

Validation expectations:

1. Any script/test path referenced in these docs exists in-repo.
2. KPI claims tied to generated artifacts (for example suspicious-coverage counts)
   match current generated files.
3. Deprecated or placeholder operational instructions are removed from active
   documentation surfaces.

`tests/test_documentation_integrity.py` enforces these checks.

---

## 6. CI Baseline

Current CI-relevant validation workflows and tests:

- `.github/workflows/python-app.yml`
- `.github/workflows/suspicious_coverage.yml`
- `tests/test_suspicious_coverage_integrity.py`
- `tests/test_documentation_integrity.py`

Any new release-contract validation (schemas/manifests/lineage checks) should be
added incrementally under `tests/` and then wired into CI.

---

## 7. Completion Checklist

Use this checklist for each validation cycle:

- [ ] `pytest tests/ -v` passes.
- [ ] Spec coverage artifacts regenerate successfully.
- [ ] Suspicious coverage summary regenerates and matches `spec_coverage.csv`.
- [ ] Documentation integrity tests pass.
- [ ] Any generated-artifact diffs are reviewed and explained.

---

## 8. Scope Boundaries

This plan covers validation for parser/cleaner correctness, rule coverage
integrity, and publication-surface documentation fidelity.

It does not define downstream analytical methodology or researcher-specific
aggregation logic beyond current package behavior.
