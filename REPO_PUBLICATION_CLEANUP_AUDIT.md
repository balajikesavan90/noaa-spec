# Repository Cleanup Audit

Date: 2026-03-14

## Summary of findings

This audit was limited to tracked files only.

- Audited set: 192 tracked files from `git ls-files`.
- Ignore handling: no tracked files also matched current ignore rules; `git ls-files -ci --exclude-standard` returned zero paths.
- Excluded from analysis: ignored and/or untracked runtime outputs such as workspace CSVs, parquet files, logs, cache folders, and other local artifacts covered by [.gitignore](.gitignore).
- Main cleanup issues:
  - root-level documentation sprawl,
  - dated status and planning memos mixed into the public surface,
  - internal AI scaffolding tracked in public paths,
  - generated preview/snapshot artifacts committed beside source materials,
  - one-off operational scripts with local assumptions,
  - validation reports split between the repository root and [docs](docs).

### Recommended disposition summary

| Category | Recommendation count | Notes |
|---|---:|---|
| DELETE | 4 | Generated or editor-local artifacts with little publication value |
| ARCHIVE | 14 | Internal history, one-off analyses, operational helpers, and machine-specific snapshots |
| MOVE TO /docs | 5 | Useful public documentation currently cluttering the repository root |
| KEEP | Remainder | Core code, tests, spec sources, canonical docs, manuscript sources, reproducibility assets |

## Files recommended for deletion

| File path | File type | Approx. size | Short description | Why it may not belong in a public repo |
|---|---|---:|---|---|
| [CLEANING_RECOMMENDATIONS.md](CLEANING_RECOMMENDATIONS.md) | Markdown | 0.6 KB | Compatibility stub that only redirects readers to other docs. | Redundant entrypoint; update links to canonical docs directly instead of carrying a placeholder file. |
| [QC_SIGNALS_ARCHITECTURE.md](QC_SIGNALS_ARCHITECTURE.md) | Markdown | 0.6 KB | Compatibility stub pointing to parser/QC design docs. | Duplicate surface for material already covered by canonical docs in [docs](docs). |
| [paper/paper-preview.html](paper/paper-preview.html) | Generated HTML | 16.2 KB | Rendered manuscript preview generated from [paper/paper.md](paper/paper.md) and [paper/paper.bib](paper/paper.bib). | Build artifact, not source. It is reproducible from the manuscript sources and adds duplication risk. |
| [.vscode/settings.json](.vscode/settings.json) | JSON | 0.2 KB | VS Code editor preferences for Poetry environment handling. | Editor-local convenience, not part of the research or package publication surface. |

## Files recommended for archiving

| File path | File type | Approx. size | Short description | Why it may not belong in a public repo |
|---|---|---:|---|---|
| [AGENTS.md](AGENTS.md) | Markdown | 6.1 KB | AI-agent operating instructions for repository-specific automation behavior. | Internal automation guidance and substantially duplicate of [.github/copilot-instructions.md](.github/copilot-instructions.md); unnecessary at the public root. |
| [NEXT_STEPS.md](NEXT_STEPS.md) | Markdown | 33.5 KB | Large implementation checklist with dated run snapshots, blockers, and milestone notes. | Valuable history, but too operational and time-bound for the main public surface. |
| [P3_EXPAND_RESEARCH_VALUE.md](P3_EXPAND_RESEARCH_VALUE.md) | Markdown | 3.7 KB | Backlog/checklist for future research-value enhancements. | Internal planning memo rather than stable user or contributor documentation. |
| [check_station_sync.py](check_station_sync.py) | Python script | 8.4 KB | Operational utility for reconciling raw pull state with station parquet outputs. | One-off operations helper with local storage assumptions, including an external drive default path. |
| [generate_audit_queue.py](generate_audit_queue.py) | Python script | 7.2 KB | Utility for generating prioritized audit batches. | Specialist maintenance helper; better retained as internal history than exposed at the repository root. |
| [rerun_stations.py](rerun_stations.py) | Python script | 1.8 KB | Script to re-run specific stations from a hard-coded list. | Explicitly operational and ad hoc; not a stable public API or documented workflow. |
| [docs/CURRENT_PROJECT_STATE.md](docs/CURRENT_PROJECT_STATE.md) | Markdown | 14.2 KB | Dated project status memo with March 2026 run snapshots and narrative state assessment. | Strong internal context, but it will age quickly and duplicates README/roadmap material. |
| [docs/REPO_CLEANUP_RECOMMENDATIONS.md](docs/REPO_CLEANUP_RECOMMENDATIONS.md) | Markdown | 6.8 KB | Previous cleanup audit and execution notes. | Superseded by this audit and primarily useful as internal cleanup history. |
| [docs/UNSPECIFIED_RULES_ANALYSIS.md](docs/UNSPECIFIED_RULES_ANALYSIS.md) | Markdown | 11.7 KB | Deep dive into one 29-row `UNSPECIFIED` coverage bucket. | Narrow debugging/forensics document, not broad publication-facing documentation. |
| [docs/spec_coverage_unspecified_fix.md](docs/spec_coverage_unspecified_fix.md) | Markdown | 2.9 KB | Write-up of the specific fix for the `UNSPECIFIED` bucket issue. | One-off repair narrative; useful historically, but too implementation-specific for the main docs set. |
| [.github/prompts/plan-numericRangeValidationQcSignals.prompt.md](.github/prompts/plan-numericRangeValidationQcSignals.prompt.md)<br>[.github/prompts/plan-qcMissingStatusAndTests.prompt.md](.github/prompts/plan-qcMissingStatusAndTests.prompt.md)<br>[.github/prompts/plan-strictNoaaParserGateA.prompt.md](.github/prompts/plan-strictNoaaParserGateA.prompt.md) | Markdown prompts (3 files) | 22.5 KB total | AI planning prompts for specific implementation episodes. | Internal AI scaffolding; not part of the software, manuscript, or contributor contract. |
| [old_r_files/FileList Creation.R](old_r_files/FileList%20Creation.R)<br>[old_r_files/LocationID_Creation.R](old_r_files/LocationID_Creation.R)<br>[old_r_files/Template.R](old_r_files/Template.R) | R scripts (3 files) | 14.6 KB total | Legacy pre-Python scripts kept as historical material. | Historical value remains, but they should be clearly separated from the active Python publication system. |
| [noaa_file_index/20260207/README.md](noaa_file_index/20260207/README.md) | Markdown | 4.4 KB | Dated operational snapshot README for a February 2026 file-index build. | Snapshot-specific operational history; better archived or distilled into timeless provenance docs. |
| [release/build_20260314T222231Z/manifests/build_metadata.json](release/build_20260314T222231Z/manifests/build_metadata.json)<br>[release/build_20260314T222231Z/manifests/run_config.json](release/build_20260314T222231Z/manifests/run_config.json)<br>[release/build_20260314T222231Z/manifests/run_manifest.csv](release/build_20260314T222231Z/manifests/run_manifest.csv)<br>[release/build_20260314T222231Z/manifests/run_status.csv](release/build_20260314T222231Z/manifests/run_status.csv) | JSON/CSV release snapshot (4 files) | 52.1 KB total | Tracked manifest snapshot for one concrete release run. | Useful as internal provenance, but currently machine-specific and includes absolute local paths plus transient run states; not a clean public exemplar. |

## Files recommended to move into /docs

| File path | File type | Approx. size | Short description | Why it should move |
|---|---|---:|---|---|
| [ARCHITECTURE_NEXT_STEPS.md](ARCHITECTURE_NEXT_STEPS.md) | Markdown | 22.3 KB | Publication architecture roadmap and gap inventory. | Useful public documentation, but it should live under a roadmap section in [docs](docs), not the repository root. |
| [RULE_IMPACT_REPORT.md](RULE_IMPACT_REPORT.md) | Markdown | 4.1 KB | Generated summary of cleaning-rule impact on sample data. | This is validation/reporting documentation and fits better under a validation or evidence section in [docs](docs). |
| [RULE_PROVENANCE_LEDGER.md](RULE_PROVENANCE_LEDGER.md) | Markdown | 13.1 KB | Summary report for rule provenance and strictness classification. | Governance and validation material should be grouped in [docs](docs) instead of the root. |
| [SPEC_COVERAGE_REPORT.md](SPEC_COVERAGE_REPORT.md) | Markdown | 13.5 KB | Main generated specification coverage report. | Important to keep, but it is documentation/report output rather than a root-level project entrypoint. |
| [UNDOCUMENTED_RULES_REVIEW.md](UNDOCUMENTED_RULES_REVIEW.md) | Markdown | 13.1 KB | Review of undocumented rules and recommended cleanup actions. | Valuable supporting documentation that belongs in a validation/research-notes section under [docs](docs). |

## Files that should remain

| File or group | Why it should remain |
|---|---|
| [README.md](README.md), [LICENSE](LICENSE), [pyproject.toml](pyproject.toml), [poetry.lock](poetry.lock), [poetry.toml](poetry.toml), [.gitignore](.gitignore) | Core project metadata, packaging, licensing, and repository policy files. |
| [src/noaa_spec](src/noaa_spec) | Primary package implementation and public code surface. |
| [tests](tests) | Regression protection, documentation integrity checks, schema validation, and reproducibility verification. |
| [isd-format-document-parts](isd-format-document-parts) | Authoritative NOAA specification source material used to derive rule coverage and provenance. |
| [tools](tools) and [scripts](scripts) | Active tooling for reproducibility, rule coverage, and data reshaping that supports documented workflows. |
| [docs/ARTIFACT_BOUNDARY_POLICY.md](docs/ARTIFACT_BOUNDARY_POLICY.md), [docs/CLEANING_RUN_MODES.md](docs/CLEANING_RUN_MODES.md), [docs/DOMAIN_DATASET_REGISTRY.md](docs/DOMAIN_DATASET_REGISTRY.md), [docs/PARSER_ENGINEERING_GUARDS.md](docs/PARSER_ENGINEERING_GUARDS.md), [docs/PIPELINE_DESIGN_RATIONALE.md](docs/PIPELINE_DESIGN_RATIONALE.md), [docs/PIPELINE_VALIDATION_PLAN.md](docs/PIPELINE_VALIDATION_PLAN.md), [docs/validation_artifacts/suspicious_coverage/suspicious_summary.md](docs/validation_artifacts/suspicious_coverage/suspicious_summary.md) | These are the strongest canonical design, policy, and validation documents. |
| [paper/README.md](paper/README.md), [paper/paper.md](paper/paper.md), [paper/paper.bib](paper/paper.bib) | Source manuscript materials needed for academic citation and paper review. |
| [reproducibility](reproducibility) | Minimal reproducibility package and supporting environment snapshot. |
| [docs/examples/noaa_demo](docs/examples/noaa_demo) and [docs/examples/station_reports](docs/examples/station_reports) | Curated public examples are worth keeping, though they would be cleaner under a dedicated [examples](examples) top-level directory in a future reorganization. |
| [.github/workflows/suspicious_coverage.yml](.github/workflows/suspicious_coverage.yml) | Public CI logic supporting validation and publication integrity. |
| [.vscode/tasks.json](.vscode/tasks.json) | Optional contributor convenience; it exposes standard test tasks without embedding personal settings. |
| [.github/copilot-instructions.md](.github/copilot-instructions.md) | If AI-assisted maintenance is intentional, keep one canonical instruction file under [.github](.github) and avoid duplicating it elsewhere. |

## Documentation redundancies

| Topic | Overlapping files | Recommended canonical file(s) |
|---|---|---|
| AI agent instructions | [AGENTS.md](AGENTS.md) and [.github/copilot-instructions.md](.github/copilot-instructions.md) | Keep only [.github/copilot-instructions.md](.github/copilot-instructions.md) if AI instructions are desired; archive [AGENTS.md](AGENTS.md). |
| Roadmap and project-state narrative | [README.md](README.md), [ARCHITECTURE_NEXT_STEPS.md](ARCHITECTURE_NEXT_STEPS.md), [NEXT_STEPS.md](NEXT_STEPS.md), [P3_EXPAND_RESEARCH_VALUE.md](P3_EXPAND_RESEARCH_VALUE.md), [docs/CURRENT_PROJECT_STATE.md](docs/CURRENT_PROJECT_STATE.md) | Use [README.md](README.md) for public overview and a trimmed roadmap page moved from [ARCHITECTURE_NEXT_STEPS.md](ARCHITECTURE_NEXT_STEPS.md) into [docs](docs); archive the dated planning/state files. |
| Parser/QC explanation entrypoints | [CLEANING_RECOMMENDATIONS.md](CLEANING_RECOMMENDATIONS.md), [QC_SIGNALS_ARCHITECTURE.md](QC_SIGNALS_ARCHITECTURE.md), [docs/PARSER_ENGINEERING_GUARDS.md](docs/PARSER_ENGINEERING_GUARDS.md), [docs/PIPELINE_DESIGN_RATIONALE.md](docs/PIPELINE_DESIGN_RATIONALE.md) | Keep [docs/PARSER_ENGINEERING_GUARDS.md](docs/PARSER_ENGINEERING_GUARDS.md) and [docs/PIPELINE_DESIGN_RATIONALE.md](docs/PIPELINE_DESIGN_RATIONALE.md); delete the compatibility stubs. |
| Validation and rule-governance reporting | [SPEC_COVERAGE_REPORT.md](SPEC_COVERAGE_REPORT.md), [RULE_PROVENANCE_LEDGER.md](RULE_PROVENANCE_LEDGER.md), [RULE_IMPACT_REPORT.md](RULE_IMPACT_REPORT.md), [UNDOCUMENTED_RULES_REVIEW.md](UNDOCUMENTED_RULES_REVIEW.md), [docs/UNSPECIFIED_RULES_ANALYSIS.md](docs/UNSPECIFIED_RULES_ANALYSIS.md), [docs/spec_coverage_unspecified_fix.md](docs/spec_coverage_unspecified_fix.md), [docs/validation_artifacts/suspicious_coverage/suspicious_summary.md](docs/validation_artifacts/suspicious_coverage/suspicious_summary.md) | Keep [docs/PIPELINE_VALIDATION_PLAN.md](docs/PIPELINE_VALIDATION_PLAN.md) as the index and group the reusable generated reports under a validation section in [docs](docs); archive one-off forensic notes. |
| Manuscript source vs preview output | [paper/paper.md](paper/paper.md), [paper/paper.bib](paper/paper.bib), [paper/paper-preview.html](paper/paper-preview.html) | Keep the manuscript source files and delete the generated preview. |
| Release contract description vs concrete local snapshot | [docs/ARTIFACT_BOUNDARY_POLICY.md](docs/ARTIFACT_BOUNDARY_POLICY.md) and [release/build_20260314T222231Z/manifests/build_metadata.json](release/build_20260314T222231Z/manifests/build_metadata.json)<br>[release/build_20260314T222231Z/manifests/run_config.json](release/build_20260314T222231Z/manifests/run_config.json)<br>[release/build_20260314T222231Z/manifests/run_manifest.csv](release/build_20260314T222231Z/manifests/run_manifest.csv)<br>[release/build_20260314T222231Z/manifests/run_status.csv](release/build_20260314T222231Z/manifests/run_status.csv) | Keep the policy/specification doc as canonical; archive the machine-specific example until a sanitized release exemplar is prepared. |

## Missing publication files

| Missing file | Priority | Why it should be added |
|---|---|---|
| [CITATION.cff](CITATION.cff) | High | Essential for academic citation, repository metadata, and GitHub citation support. |
| [CONTRIBUTING.md](CONTRIBUTING.md) | High | Needed to define contribution workflow, test expectations, and documentation standards. |
| [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) | High | Standard open-source governance file for community behavior expectations. |
| [SECURITY.md](SECURITY.md) | High | Gives researchers and users a disclosure path for security or data-integrity concerns. |
| [SUPPORT.md](SUPPORT.md) | Medium | Clarifies where users should ask questions, report issues, or request help. |
| [CHANGELOG.md](CHANGELOG.md) or [RELEASE_NOTES.md](RELEASE_NOTES.md) | Medium | Important for tracking public releases, schema changes, and reproducibility-impacting updates. |

## Suggested final repository structure

### Root

Keep the repository root focused on public entrypoints and project metadata:

- [README.md](README.md)
- [LICENSE](LICENSE)
- [pyproject.toml](pyproject.toml)
- [poetry.lock](poetry.lock)
- [CITATION.cff](CITATION.cff)
- [CONTRIBUTING.md](CONTRIBUTING.md)
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- [SECURITY.md](SECURITY.md)
- [SUPPORT.md](SUPPORT.md)
- [CHANGELOG.md](CHANGELOG.md)
- [.github](.github)
- [src](src)
- [tests](tests)
- [tools](tools)
- [scripts](scripts)
- [docs](docs)
- [examples](examples)
- [archive](archive)
- [paper](paper)
- [reproducibility](reproducibility)
- [isd-format-document-parts](isd-format-document-parts)

### Recommended docs structure

Within [docs](docs), separate stable public docs from generated validation material:

- [docs/architecture](docs/architecture)
  - move [docs/PIPELINE_DESIGN_RATIONALE.md](docs/PIPELINE_DESIGN_RATIONALE.md)
  - move [docs/PARSER_ENGINEERING_GUARDS.md](docs/PARSER_ENGINEERING_GUARDS.md)
  - move [docs/ARTIFACT_BOUNDARY_POLICY.md](docs/ARTIFACT_BOUNDARY_POLICY.md)
  - move [docs/CLEANING_RUN_MODES.md](docs/CLEANING_RUN_MODES.md)
  - move [docs/DOMAIN_DATASET_REGISTRY.md](docs/DOMAIN_DATASET_REGISTRY.md)
- [docs/validation](docs/validation)
  - move [docs/PIPELINE_VALIDATION_PLAN.md](docs/PIPELINE_VALIDATION_PLAN.md)
  - move [SPEC_COVERAGE_REPORT.md](SPEC_COVERAGE_REPORT.md)
  - move [RULE_PROVENANCE_LEDGER.md](RULE_PROVENANCE_LEDGER.md)
  - move [RULE_IMPACT_REPORT.md](RULE_IMPACT_REPORT.md)
  - move [UNDOCUMENTED_RULES_REVIEW.md](UNDOCUMENTED_RULES_REVIEW.md)
  - keep [docs/validation_artifacts/suspicious_coverage/suspicious_summary.md](docs/validation_artifacts/suspicious_coverage/suspicious_summary.md) or fold it under the same section
- [docs/roadmap](docs/roadmap)
  - move a trimmed public roadmap derived from [ARCHITECTURE_NEXT_STEPS.md](ARCHITECTURE_NEXT_STEPS.md)
- [docs/provenance](docs/provenance)
  - only keep timeless provenance notes; archive dated snapshot memos such as [noaa_file_index/20260207/README.md](noaa_file_index/20260207/README.md)

### Examples

Create a dedicated [examples](examples) surface for curated public artifacts:

- move [docs/examples/noaa_demo](docs/examples/noaa_demo) to [examples/noaa_demo](examples/noaa_demo)
- move [docs/examples/station_reports](docs/examples/station_reports) to [examples/station_reports](examples/station_reports)
- if release examples are desired, add a sanitized [examples/release_snapshot](examples/release_snapshot) rather than keeping machine-specific files in [release](release)

### Archive

Use [archive](archive) for historical but non-canonical material:

- [archive/roadmap-history](archive/roadmap-history) for [NEXT_STEPS.md](NEXT_STEPS.md), [P3_EXPAND_RESEARCH_VALUE.md](P3_EXPAND_RESEARCH_VALUE.md), and [docs/CURRENT_PROJECT_STATE.md](docs/CURRENT_PROJECT_STATE.md)
- [archive/ai-prompts](archive/ai-prompts) for [.github/prompts](.github/prompts) and optionally [AGENTS.md](AGENTS.md)
- [archive/legacy-r](archive/legacy-r) for [old_r_files](old_r_files)
- [archive/ops](archive/ops) for [check_station_sync.py](check_station_sync.py), [generate_audit_queue.py](generate_audit_queue.py), and [rerun_stations.py](rerun_stations.py) if they are retained at all
- [archive/one-off-analysis](archive/one-off-analysis) for [docs/UNSPECIFIED_RULES_ANALYSIS.md](docs/UNSPECIFIED_RULES_ANALYSIS.md), [docs/spec_coverage_unspecified_fix.md](docs/spec_coverage_unspecified_fix.md), and [docs/REPO_CLEANUP_RECOMMENDATIONS.md](docs/REPO_CLEANUP_RECOMMENDATIONS.md)

### Paper

Keep [paper](paper) source-only:

- [paper/README.md](paper/README.md)
- [paper/paper.md](paper/paper.md)
- [paper/paper.bib](paper/paper.bib)
- do not track regenerated preview HTML by default

### Publication outcome target

A clean public release of this repository should present a small root surface, one canonical set of docs, a separate examples area, and a clearly marked historical archive. That structure would better match open-source publication norms while preserving the repository's scientific provenance and reproducibility goals.
