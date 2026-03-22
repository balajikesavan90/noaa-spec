# Repository Cleanup Audit

## Scope

- This audit is identification-only. No files were moved, edited, renamed, or deleted.
- The candidate set was built from tracked files only using `git ls-files`.
- Ignored paths were excluded from cleanup analysis per `.gitignore`, including runtime/output surfaces such as `output/`, `artifacts/test_runs/`, `artifacts/parquet_runs/`, `release/`, `noaa_file_index/state/`, and globally ignored `*.csv` / `*.parquet` files.
- Ignored paths are mentioned below only when tracked docs, tests, workflows, or tools depend on them in a way that creates a repository-readiness risk.
- Repository surface reviewed: 189 tracked files.

## Executive Summary

- The repo root is overloaded: 20 tracked root files include multiple roadmap/status documents, generated validation reports, and one-off scripts that are not primary public entrypoints.
- Three tracked root scripts — `check_station_sync.py`, `generate_audit_queue.py`, and `rerun_stations.py` — read like maintenance utilities and should likely live under `tools/` or `scripts/`. Confidence: High.
- Root-level roadmap/report docs are split across `ARCHITECTURE_NEXT_STEPS.md`, `NEXT_STEPS.md`, `P3_EXPAND_RESEARCH_VALUE.md`, `REPO_PUBLICATION_CLEANUP_AUDIT.md`, `SPEC_COVERAGE_REPORT.md`, `RULE_PROVENANCE_LEDGER.md`, `RULE_IMPACT_REPORT.md`, and `UNDOCUMENTED_RULES_REVIEW.md`. This creates a noisy public surface. Confidence: High.
- Documentation overlap is significant: `AGENTS.md` duplicates `.github/copilot-instructions.md`, and `CLEANING_RECOMMENDATIONS.md` / `QC_SIGNALS_ARCHITECTURE.md` are compatibility stubs that mostly point elsewhere. Confidence: High.
- Several tracked docs/tests depend on ignored artifacts: `docs/CURRENT_PROJECT_STATE.md` links into ignored `artifacts/test_runs/...`, `tests/test_reproducibility_example.py` expects ignored `reproducibility/*.csv`, and multiple tests/workflows depend on ignored root `spec_coverage.csv`. Confidence: High.
- `docs/PIPELINE_VALIDATION_PLAN.md` contains a stale reference to `.github/workflows/python-app.yml`, which is not present in the tracked tree. Confidence: High.
- The remaining runtime-boundary issue is mostly reference-level, not file-level: tracked examples are already under `docs/examples/`, but several tracked reports and tests still assume local ignored runtime data exists. Confidence: High.
- Public-release governance is incomplete: `CITATION.cff`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, and `CHANGELOG.md` (or equivalent) are missing. Confidence: High.

## Findings

### 1. Root-Level Clutter

| Candidate | Why it is misplaced | Suggested target | Confidence |
|---|---|---|---|
| `check_station_sync.py` | Operational helper for raw-pull state reconciliation; defaults to `/media/balaji-kesavan/LaCie/NOAA_Data`, which is machine-specific. | `tools/ops/` or `scripts/ops/` | High |
| `generate_audit_queue.py` | Specialized spec-audit utility; not a public repo entrypoint and sits outside the existing `tools/spec_coverage/` family. | `tools/spec_coverage/` | High |
| `rerun_stations.py` | One-off rerun script with a hard-coded station list and ignored `output/` assumptions. | `tools/ops/` or `scripts/maintenance/` | High |
| `ARCHITECTURE_NEXT_STEPS.md`, `NEXT_STEPS.md`, `P3_EXPAND_RESEARCH_VALUE.md` | Planning/roadmap material dominates the root instead of living under documentation. | `docs/roadmap/` and `docs/status/` | High |
| `SPEC_COVERAGE_REPORT.md`, `RULE_PROVENANCE_LEDGER.md`, `RULE_IMPACT_REPORT.md`, `UNDOCUMENTED_RULES_REVIEW.md` | Generated validation/governance reports are useful, but they are documentation artifacts, not root-level entrypoints. | `docs/validation/` or `docs/reports/` | High |
| `REPO_PUBLICATION_CLEANUP_AUDIT.md` | This is a prior audit, not a primary repo surface. Keeping audits at root will accumulate clutter. | `docs/audits/` | Medium |

### 2. Documentation Organization

**Roadmap / planning / status docs that likely belong under `docs/`:**

- `ARCHITECTURE_NEXT_STEPS.md` — architecture roadmap. Confidence: High.
- `NEXT_STEPS.md` — implementation completion log. Confidence: High.
- `P3_EXPAND_RESEARCH_VALUE.md` — backlog/workstream planning. Confidence: High.
- `docs/CURRENT_PROJECT_STATE.md` — dated status memo rather than stable public documentation. Confidence: High.
- `REPO_PUBLICATION_CLEANUP_AUDIT.md` and `docs/REPO_CLEANUP_RECOMMENDATIONS.md` — overlapping cleanup/audit artifacts. Confidence: High.

**Duplicate or overlapping docs/instructions:**

- `AGENTS.md` and `.github/copilot-instructions.md` contain the same repository operating guidance. One canonical copy is enough. Confidence: High.
- `CLEANING_RECOMMENDATIONS.md` and `QC_SIGNALS_ARCHITECTURE.md` are compatibility entrypoints that mainly redirect readers to `docs/PIPELINE_DESIGN_RATIONALE.md`, `docs/PIPELINE_VALIDATION_PLAN.md`, and `docs/PARSER_ENGINEERING_GUARDS.md`. These add indirection at the root. Confidence: High.
- Roadmap/status material overlaps across `README.md`, `ARCHITECTURE_NEXT_STEPS.md`, `NEXT_STEPS.md`, `P3_EXPAND_RESEARCH_VALUE.md`, and `docs/CURRENT_PROJECT_STATE.md`. Confidence: Medium.

**Stale or broken references:**

- `docs/PIPELINE_VALIDATION_PLAN.md` lists `.github/workflows/python-app.yml` as a current CI workflow, but that file is absent from the tracked tree. Confidence: High.
- `docs/CURRENT_PROJECT_STATE.md` links to ignored `artifacts/test_runs/...` paths. Those references will not resolve for a fresh clone and should not be treated as stable public documentation. Confidence: High.
- `docs/REPO_CLEANUP_RECOMMENDATIONS.md` is now stale relative to the current repository policy because it audits ignored runtime clutter directly, which conflicts with the narrower tracked-only/public-surface approach requested here. Confidence: Medium.

### 3. Runtime vs Tracked Boundary Issues

- `noaa_file_index/20260207/README.md` is a tracked document inside a dated operational snapshot namespace. Its content documents runtime surfaces such as `output/<station_id>/LocationData_Raw.parquet`, `noaa_file_index/state/raw_pull_state.csv`, and `release/build_<build_id>/...`, which makes it read more like archival provenance than active public docs. Suggested target: `docs/provenance/` or `docs/snapshots/`. Confidence: Medium-High.
- The spec-governance/report surface is split awkwardly between tracked Markdown summaries and ignored machine-readable inputs/companions. Examples:
  - `tools/spec_coverage/generate_spec_coverage.py` writes `spec_coverage.csv` and `SPEC_COVERAGE_REPORT.md` to the repo root.
  - `tools/spec_coverage/generate_rule_provenance_ledger.py` defaults to `RULE_PROVENANCE_LEDGER.csv` and `RULE_PROVENANCE_LEDGER.md` at the repo root.
  - `tools/rule_impact/generate_rule_impact_report.py` defaults to `RULE_IMPACT_REPORT.md`, `rule_impact_summary.csv`, and `rule_family_impact_summary.csv` at the repo root.
  Because `.gitignore` ignores `*.csv`, the human-readable reports are tracked while the machine-readable evidence is not. That weakens reproducibility for external reviewers. Confidence: High.
- `RULE_IMPACT_REPORT.md` explicitly says its sample comes from local `output/<station>/LocationData_Raw.csv`, and the generating tool says the same. Since `output/` is ignored and out of scope for the public repo, the tracked report depends on a local runtime dataset that outsiders will not have. Confidence: High.
- No tracked fixtures were found under ignored `output/`, `artifacts/test_runs/`, or `release/` roots in the current tracked set. The main remaining problem is tracked references into ignored/runtime surfaces, not tracked runtime clutter itself. Confidence: High.

### 4. Tests / Reproducibility Risks

- `tests/test_reproducibility_example.py` expects `reproducibility/sample_station_cleaned_expected.csv`, but `.gitignore` ignores `*.csv`. The same area also uses `reproducibility/sample_station_cleaned.csv` as a default output in `reproducibility/run_pipeline_example.py`, and `reproducibility/README.md` tells readers it will overwrite that file. This is a tracked-reference mismatch against ignored fixtures. Confidence: High.
- The repository has a broad dependency surface on ignored root `spec_coverage.csv`:
  - `tests/test_documentation_integrity.py`
  - `tests/test_parser_spec_guardrails.py`
  - `tests/test_suspicious_coverage_integrity.py`
  - `.github/workflows/suspicious_coverage.yml`
  - `tools/reproducibility/export_pipeline_snapshot.py`
  These consumers are legitimate, but the contract is implicit: a fresh clone needs a generation step before these checks make sense. Confidence: High.
- `tests/test_documentation_integrity.py` asserts that `.gitignore` contains release allowlist entries such as `!release/build_*/canonical_cleaned/**/*.csv`, but those entries are not present in the tracked `.gitignore`. That is a direct repo-policy/test mismatch. Confidence: High.
- `docs/CURRENT_PROJECT_STATE.md` cites ignored run artifacts as supporting evidence for current status claims. Even if locally valid, that is brittle for public review and external reproduction. Confidence: High.

### 5. Script / Tooling Placement

- `check_station_sync.py` should not live at root in a public-facing repo. It is an operational utility with machine-specific defaults and belongs in a clearly named maintenance area. Confidence: High.
- `rerun_stations.py` is an ad hoc rerun helper with a fixed station list; it should be treated as maintenance tooling, not top-level product surface. Confidence: High.
- `generate_audit_queue.py` is structurally closer to the other spec-coverage generators already stored under `tools/spec_coverage/`. Confidence: High.
- `old_r_files/FileList Creation.R`, `old_r_files/LocationID_Creation.R`, and `old_r_files/Template.R` are historical source material, but `old_r_files/` sits in the active repo surface rather than an explicit archive/legacy area. Confidence: Medium.
- `noaa_file_index/20260207/README.md` also functions like archived operational documentation and would be easier to understand if it lived under an explicit snapshot/provenance area. Confidence: Medium.

### 6. Public Repo Readiness Gaps

The following standard public-release files are missing from the tracked tree:

- `CITATION.cff` — especially important for an academic/scientific repository. Confidence: High.
- `CONTRIBUTING.md` — needed for contributor workflow, tests, and documentation expectations. Confidence: High.
- `CODE_OF_CONDUCT.md` — standard community-governance file. Confidence: High.
- `SECURITY.md` — expected disclosure path for vulnerabilities or integrity issues. Confidence: High.
- `CHANGELOG.md` or equivalent release-history file — useful for schema/release transparency. Confidence: Medium.

## Decision Table

| Candidate | Issue Type | Suggested Action | Confidence | Reason |
|---|---|---|---|---|
| `check_station_sync.py` | Root-level ops script | Move under `tools/ops/` | High | Maintenance helper with machine-specific default path |
| `generate_audit_queue.py` | Root-level tooling | Move under `tools/spec_coverage/` | High | Fits existing tool family |
| `rerun_stations.py` | Root-level one-off script | Move under `tools/ops/` or archive | High | Hard-coded station list and runtime assumptions |
| `ARCHITECTURE_NEXT_STEPS.md`, `NEXT_STEPS.md`, `P3_EXPAND_RESEARCH_VALUE.md` | Root-level planning clutter | Move under `docs/roadmap/` / `docs/status/` | High | Not primary repo entrypoints |
| `SPEC_COVERAGE_REPORT.md`, `RULE_PROVENANCE_LEDGER.md`, `RULE_IMPACT_REPORT.md`, `UNDOCUMENTED_RULES_REVIEW.md` | Root-level generated reports | Move under `docs/validation/` | High | Valuable docs, but misplaced at root |
| `AGENTS.md` | Duplicate instructions | Consolidate with `.github/copilot-instructions.md` | High | Same policy surface duplicated |
| `CLEANING_RECOMMENDATIONS.md`, `QC_SIGNALS_ARCHITECTURE.md` | Redirect/compatibility docs | Fold into a docs index or retire as stubs | Medium | Add root noise without much standalone value |
| `docs/CURRENT_PROJECT_STATE.md` | Dated status memo | Archive or move under `docs/status-history/` | High | Links to ignored run artifacts |
| `noaa_file_index/20260207/README.md` | Runtime/snapshot doc | Move under `docs/provenance/` or archive | Medium-High | Dated operational snapshot in runtime namespace |
| Reproducibility sample CSV references | Ignored-file dependency | Establish a tracked fixture policy | High | Tests/README depend on ignored `reproducibility/*.csv` |
| Root `spec_coverage.csv` dependency surface | Ignored-file dependency | Add explicit generation/bootstrap policy or sanctioned tracked snapshot | High | Tests, workflow, and tooling all depend on ignored file |
| `docs/PIPELINE_VALIDATION_PLAN.md` → `.github/workflows/python-app.yml` | Stale reference | Update the doc | High | Referenced workflow is missing |
| Missing `CITATION.cff`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `CHANGELOG.md` | Public release gap | Add files | High | Standard external-review expectations |

## Recommended Cleanup Order

1. Fix documentation integrity mismatches first:
   - remove stale references to missing files,
   - stop public docs from depending on ignored run artifacts,
   - document generation prerequisites for ignored coverage/reproducibility files.
2. Reduce root clutter by relocating roadmap/status docs and validation reports under `docs/`.
3. Move or archive root maintenance scripts into `tools/` / `scripts/` and separate legacy R assets into an explicit archive area.
4. Decide on a policy for generated validation artifacts:
   - either track a sanctioned machine-readable snapshot,
   - or keep them generated-only but document/bootstrap them explicitly and stop tests/docs from assuming they already exist.
5. Relocate or archive dated operational snapshot documentation such as `noaa_file_index/20260207/README.md`.
6. Consolidate duplicate instruction/audit surfaces (`AGENTS.md`, compatibility stubs, prior cleanup reports).
7. Add missing public-release governance files (`CITATION.cff`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `CHANGELOG.md`).

## Non-Issues / Things Intentionally Left Alone

- `README.md`, `LICENSE`, `pyproject.toml`, `poetry.lock`, `poetry.toml`, and `.gitignore` are standard root files and were not flagged.
- `src/`, `tests/`, `paper/`, `reproducibility/`, `docs/examples/`, `tests/fixtures/`, and `isd-format-document-parts/` are legitimate repository surfaces for code, manuscript, curated examples, and reproducibility support.
- `docs/examples/station_reports/` and `docs/examples/noaa_demo/` are already in a documentation/example area rather than ignored runtime roots; they should not be treated as clutter.
- No tracked files were found under ignored runtime roots such as `output/`, `artifacts/test_runs/`, or `release/`; those locations were treated as out of scope except where tracked references point into them.
- `tests/fixtures/release_manifest_v1_snapshot.csv` appears to be an intentional tracked fixture and is correctly covered by the `.gitignore` exception for `tests/fixtures/**/*.csv`.
