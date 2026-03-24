# Deep Publication Readiness Audit

Local-path note: references in this archival review use placeholders such as `<EXTERNAL_STORAGE>` and document a machine-local audited build. Those paths are not required for reproduction from this repository.

## Executive summary

### Overall verdict

This repository is stronger as software than as a JOSS submission narrative. The implementation, contract checks, and the audited 100-station build are materially credible. The main remaining gaps are not random code polish issues. They are story-discipline, evidence-packaging, and revision-alignment problems that could cause a reviewer to distrust the submission even though the pipeline itself looks serious.

### Top 5 remaining gaps

1. The JOSS paper is still too AI-first and architecture-first, and not software/user-first enough.
   Evidence: `paper/paper.md`.
2. The paper and README imply specification-grounded confidence more strongly than the repository's own provenance/risk reports justify.
   Evidence: `paper/paper.md`, `docs/reports/RULE_PROVENANCE_LEDGER.md`, `docs/reports/UNDOCUMENTED_RULES_REVIEW.md`.
3. The strongest empirical evidence, `build_20260322T070910Z`, is external to the repository and was produced from a different code revision than the current checkout.
   Evidence: `<EXTERNAL_STORAGE>/NOAA_CLEANED_DATA/build_20260322T070910Z/manifests/build_metadata.json`, `git rev-parse HEAD`.
4. Reviewer-facing reproducibility materials are stale or split across multiple revision anchors.
   Evidence: `reproducibility/pipeline_snapshot.json`, `reproducibility/environment.txt`, `README.md`, `reproducibility/README.md`.
5. The public documentation surface still contains stale or contradictory traces of prior repository states.
   Evidence: `docs/archive/REPO_FOLDER_STRUCTURE_REPORT.md`, `docs/architecture/ARCHITECTURE_NEXT_STEPS.md`, references to missing `noaa_file_index/20260207/README.md`.

### Top 5 strengths

1. The 100-station build is internally coherent and integrity-clean.
   Evidence: `<EXTERNAL_STORAGE>/NOAA_CLEANED_DATA/build_20260322T070910Z/manifests/post_run_audit.md`, `<EXTERNAL_STORAGE>/NOAA_CLEANED_DATA/build_20260322T070910Z/manifests/publication_readiness_gate.json`.
2. Publication contracts and deterministic artifact semantics are explicit.
   Evidence: `src/noaa_spec/contracts.py`, `src/noaa_spec/contract_schemas/v1/`, `docs/ARTIFACT_BOUNDARY_POLICY.md`, `docs/CLEANING_RUN_MODES.md`.
3. The publication-surface tests are real and currently passing locally.
   Evidence: `tests/test_publication_schema_ci.py`, `tests/test_documentation_integrity.py`, local run on 2026-03-22: `25 passed`.
4. Artifact integrity logic is more mature than typical research-pipeline repos.
   Evidence: `src/noaa_spec/cleaning_runner.py`, `src/noaa_spec/build_audit.py`.
5. The build outputs do support the broad descriptive claims about sparsity, sentinel prevalence, and heterogeneous exclusion.
   Evidence: `<EXTERNAL_STORAGE>/NOAA_CLEANED_DATA/build_20260322T070910Z/quality_reports/*.csv`, `<EXTERNAL_STORAGE>/NOAA_CLEANED_DATA/build_20260322T070910Z/quality_reports/quality_reports_summary.md`.

### Readiness assessment

Nearly ready.

More precisely: not "submit now", but also not a major rebuild. This looks like a submission that should go in after a focused hardening pass on manuscript framing, evidence packaging, and stale-surface cleanup.

## What I inspected

- Root metadata and entrypoints: `README.md`, `pyproject.toml`, `CITATION.cff`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `CHANGELOG.md`, `.gitignore`
- Manuscript: `paper/paper.md`, `paper/paper.bib`, `paper/README.md`
- Core implementation: `src/noaa_spec/cli.py`, `src/noaa_spec/cleaning_runner.py`, `src/noaa_spec/build_audit.py`, `src/noaa_spec/contracts.py`, `src/noaa_spec/contract_validation.py`, `src/noaa_spec/deterministic_io.py`
- Tests: `tests/test_publication_schema_ci.py`, `tests/test_documentation_integrity.py`, `tests/test_reproducibility_example.py`, `tests/test_integration.py`, `tests/test_cleaning_runner.py`, `tests/test_artifact_contracts.py`
- Active docs: `docs/README.md`, `docs/ARTIFACT_BOUNDARY_POLICY.md`, `docs/CLEANING_RUN_MODES.md`, `docs/DOMAIN_DATASET_REGISTRY.md`, `docs/PIPELINE_VALIDATION_PLAN.md`
- Reports and archival state docs: `docs/reports/*.md`, `docs/archive/*.md`, `docs/architecture/ARCHITECTURE_NEXT_STEPS.md`
- Examples and reproducibility: `examples/README.md`, `docs/examples/README.md`, `reproducibility/README.md`, `reproducibility/pipeline_snapshot.json`, `reproducibility/environment.txt`
- External audited build: `<EXTERNAL_STORAGE>/NOAA_CLEANED_DATA/build_20260322T070910Z`

## JOSS paper audit

### Supported claims

- The claim that NOAA-Spec produces deterministic canonical datasets, domain datasets, quality artifacts, and release manifests is supported by the implementation and the 100-station build.
  Evidence: `paper/paper.md`, `src/noaa_spec/cleaning_runner.py`, `<EXTERNAL_STORAGE>/NOAA_CLEANED_DATA/build_20260322T070910Z/manifests/post_run_audit.md`.
- The descriptive results claims about sentinel prevalence, sparse completeness, and heterogeneous quality-code exclusions are broadly supported.
  Evidence: `paper/paper.md:71-83`, `<EXTERNAL_STORAGE>/NOAA_CLEANED_DATA/build_20260322T070910Z/quality_reports/sentinel_frequency.csv`, `<EXTERNAL_STORAGE>/NOAA_CLEANED_DATA/build_20260322T070910Z/quality_reports/field_completeness.csv`, `<EXTERNAL_STORAGE>/NOAA_CLEANED_DATA/build_20260322T070910Z/quality_reports/quality_code_exclusions.csv`, `<EXTERNAL_STORAGE>/NOAA_CLEANED_DATA/build_20260322T070910Z/quality_reports/quality_reports_summary.md:22-35`.
- The claim that quality diagnostics are separated from publication integrity is supported.
  Evidence: `paper/paper.md`, `docs/CLEANING_RUN_MODES.md:138-183`, `<EXTERNAL_STORAGE>/NOAA_CLEANED_DATA/build_20260322T070910Z/manifests/publication_readiness_gate.json`, `<EXTERNAL_STORAGE>/NOAA_CLEANED_DATA/build_20260322T070910Z/quality_reports/quality_assessment.json`.

### Weak claims

- "Treating the NOAA specification as an executable contract" is directionally true, but the repo's own provenance materials show a much messier rule-support story than the paper signals.
  Evidence: `paper/paper.md:45`, `docs/reports/RULE_PROVENANCE_LEDGER.md:12-22`, `docs/reports/UNDOCUMENTED_RULES_REVIEW.md:5-16`.
- "Correctness guarantees" is too strong as written.
  Evidence: `paper/paper.md:65`; counterweight: `docs/reports/RULE_PROVENANCE_LEDGER.md:15-22`, `docs/reports/UNDOCUMENTED_RULES_REVIEW.md:16-16`.
- The paper says empirical evaluation "demonstrates" structural properties across 100 stations, but it does not cite or point readers to a concrete release artifact set or archived build package.
  Evidence: `paper/paper.md:25`, `paper/paper.md:67-83`.

### Overclaims

- The manuscript foregrounds AI-assisted development as if it is part of the core software contribution. For JOSS, that is likely to hurt more than help.
  Evidence: `paper/paper.md:8`, `paper/paper.md:21-27`, `paper/paper.md:33`, `paper/paper.md:57-65`, `paper/paper.md:89`.
- The "Results" section reads more like a research paper result narrative than a software paper justification.
  Evidence: `paper/paper.md:67-83`.
- The paper suggests strong documentation-implementation-test alignment, but the repo still carries 1986 `unknown` support rows, 179 `stricter` rows, and 3886 manual-review rows in the provenance ledger summary.
  Evidence: `paper/paper.md:23`, `paper/paper.md:53`, `docs/reports/RULE_PROVENANCE_LEDGER.md:12-22`.

### Missing context

- The paper does not clearly state that the 100-station evidence currently lives in an external build root rather than in a versioned in-repo release snapshot.
  Evidence: `paper/paper.md`; actual location: `<EXTERNAL_STORAGE>/NOAA_CLEANED_DATA/build_20260322T070910Z`.
- The paper does not disclose that the audited build was produced from revision `173f3dc9...`, while the current inspected checkout is `ce4cf3ff...`.
  Evidence: `<EXTERNAL_STORAGE>/NOAA_CLEANED_DATA/build_20260322T070910Z/manifests/build_metadata.json:2-5`, `git rev-parse HEAD`.
- The paper does not acknowledge that some enforced rules are currently judged by the repo itself as better handled as engineering guards or flag-only behavior.
  Evidence: `docs/reports/UNDOCUMENTED_RULES_REVIEW.md:18-76`.

### Terminology/story mismatches

- The paper uses "Verification Triangle", "Specification Rule Graph", and "Implementation Alignment Map", but those are not prominent public runtime objects in the codebase. They read more like conceptual scaffolding than software interfaces.
  Evidence: `paper/paper.md:23`, `paper/paper.md:57-61`; compare with active repo entrypoints in `README.md`, `docs/README.md`, `src/noaa_spec/cli.py`.
- The repository more concretely speaks in terms of release manifests, file manifests, quality reports, contracts, and checksums.
  Evidence: `docs/ARTIFACT_BOUNDARY_POLICY.md`, `docs/CLEANING_RUN_MODES.md`, `src/noaa_spec/contracts.py`, `src/noaa_spec/build_audit.py`.

### Limitations and disclosure gaps

- The paper should explicitly disclose that some rules are inferred, some are engineering guards, and some current cleaning behavior may be stricter than the NOAA documentation warrants.
  Evidence: `docs/reports/RULE_PROVENANCE_LEDGER.md:5-22`, `docs/reports/UNDOCUMENTED_RULES_REVIEW.md:5-16`.
- The paper should disclose that the 100-station build is a bounded batch, not evidence of whole-dataset publication at repository scale.
  Evidence: `<EXTERNAL_STORAGE>/NOAA_CLEANED_DATA/build_20260322T070910Z/manifests/build_metadata.json:110-113`.

## Repo and documentation audit

### Structure strengths

- The core package layout is coherent: `src/`, `tests/`, `docs/`, `paper/`, `examples/`, `reproducibility/`.
- Publication contracts are separated from runtime roots in policy docs.
  Evidence: `docs/ARTIFACT_BOUNDARY_POLICY.md:5-87`.
- The README is concise and reviewer-usable for the minimal sample path.
  Evidence: `README.md:3-89`.

### Structure weaknesses

- The repository still tells multiple stories depending on whether the reader opens active docs, archive docs, or cleanup audits.
  Evidence: `docs/README.md:3-11`, `docs/archive/CURRENT_PROJECT_STATE.md`, `docs/architecture/ARCHITECTURE_NEXT_STEPS.md`.
- The docs surface is light on bridging material. There is no single reviewer guide that says: "start here, run this, inspect this build, here is what the evidence means."
  Evidence: `README.md`, `docs/README.md`, `reproducibility/README.md`, `docs/examples/README.md`.
- The build and release contract are documented as `release/build_<build_id>/...` inside the repository, but the audited submission-strength build is external.
  Evidence: `docs/ARTIFACT_BOUNDARY_POLICY.md:7-23`, `docs/CLEANING_RUN_MODES.md:65-68`, actual build root `<EXTERNAL_STORAGE>/NOAA_CLEANED_DATA/build_20260322T070910Z`.

### Hygiene problems

- `CITATION.cff` still contains a placeholder DOI.
  Evidence: `CITATION.cff:1-10`.
- `pyproject.toml` still has an empty project description.
  Evidence: `pyproject.toml:1-17`.
- CI is thin relative to the claims in the validation plan. Only one workflow is present, and it does not run the full suite.
  Evidence: `.github/workflows/suspicious_coverage.yml:1-155`, `docs/PIPELINE_VALIDATION_PLAN.md:24-61`.
- The archive contains stale reports about files and layouts that no longer exist, which is acceptable as archive history but still risky when linked or encountered by reviewers.
  Evidence: `docs/archive/REPO_FOLDER_STRUCTURE_REPORT.md`, `docs/architecture/ARCHITECTURE_NEXT_STEPS.md:129-148`.

### Reviewer confusion risks

- `docs/examples/README.md` and `examples/README.md` describe different "examples" surfaces without a unifying explanation.
  Evidence: `docs/examples/README.md:1-8`, `examples/README.md:1-9`.
- `paper/README.md` only explains rendering, not how the manuscript claims map to repository evidence.
  Evidence: `paper/README.md:1-18`.
- The public CLI still exposes many commands, including deprecated and placeholder-feeling ones, which makes the project look broader and less focused than the JOSS narrative.
  Evidence: `src/noaa_spec/cli.py`, CLI help output from `poetry run noaa-spec --help`.

## Build artifact audit: build_20260322T070910Z

### What the artifacts convincingly prove

- The run completed successfully for 100 stations with finalization.
  Evidence: `<EXTERNAL_STORAGE>/NOAA_CLEANED_DATA/build_20260322T070910Z/manifests/run_state.json:2-18`.
- The build has coherent manifest coverage and passed recomputed checksum validation.
  Evidence: `<EXTERNAL_STORAGE>/NOAA_CLEANED_DATA/build_20260322T070910Z/manifests/post_run_audit.md:19-57`.
- The release artifact set is substantial and nontrivial: 100 raw sources, 100 canonical datasets, 588 domain datasets, and 5 run-level quality reports.
  Evidence: `<EXTERNAL_STORAGE>/NOAA_CLEANED_DATA/build_20260322T070910Z/manifests/release_manifest.csv`.
- The broad descriptive claims in the paper are supported by the measured outputs.
  Computed from:
  - `<EXTERNAL_STORAGE>/NOAA_CLEANED_DATA/build_20260322T070910Z/quality_reports/sentinel_frequency.csv`: mean sentinel row rate `0.9969`, min `0.8467`, max `1.0`
  - `<EXTERNAL_STORAGE>/NOAA_CLEANED_DATA/build_20260322T070910Z/quality_reports/field_completeness.csv`: median completeness `0.000567...`
  - `<EXTERNAL_STORAGE>/NOAA_CLEANED_DATA/build_20260322T070910Z/quality_reports/quality_code_exclusions.csv`: max exclusion rate `0.9313`

### What they do not prove

- They do not prove reproducibility from the current repository checkout.
  Evidence: build revision `173f3dc9...` in `<EXTERNAL_STORAGE>/.../build_metadata.json:2-5` versus current checkout `ce4cf3ff...`.
- They do not prove external reviewer reproducibility, because the raw input staging root is external and machine-local.
  Evidence: `<EXTERNAL_STORAGE>/.../build_metadata.json:6-120`, `<EXTERNAL_STORAGE>/.../run_config.json:1-25`.
- They do not prove whole-dataset or production-at-scale coverage beyond this bounded 100-station run.

### Integrity/traceability assessment

- Strong on internal integrity.
- Strong on path-level lineage inside the run.
- Moderate on external reproducibility.

The biggest limitation is not manifest integrity. It is the fact that the best build evidence is local to `<EXTERNAL_STORAGE>/...` and not packaged into a reviewer-portable release exemplar.

### Reviewer-facing weaknesses

- The build is highly machine-readable but only moderately reviewer-readable.
  Evidence: manifests are strong; reviewer summary is mostly `quality_reports_summary.md` and `post_run_audit.md`.
- `run_config.json` and `build_metadata.json` expose local absolute paths, which are useful for provenance but not reviewer-friendly.
  Evidence: `<EXTERNAL_STORAGE>/.../run_config.json:1-25`, `<EXTERNAL_STORAGE>/.../build_metadata.json:2-120`.
- The build contains 588 domain datasets rather than the naive expected 600, because 12 stations have no `precipitation` artifact. That may be legitimate, but it is not explained anywhere reviewer-facing.
  Evidence: `<EXTERNAL_STORAGE>/.../release_manifest.csv`; computed missing domain set from that file.

## Cross-file consistency audit

### Contradictions

- The repo policy says the canonical publication surface is `release/build_<build_id>/...`, but the audited build is external and no `release/build_20260322T070910Z` snapshot exists in-repo.
  Evidence: `docs/ARTIFACT_BOUNDARY_POLICY.md:7-23`, `docs/CLEANING_RUN_MODES.md:65-68`, repository `release/` contents.
- `reproducibility/pipeline_snapshot.json` points to old coverage counts and an old commit, while current spec coverage says 3536/3536 and HEAD is different.
  Evidence: `reproducibility/pipeline_snapshot.json:2-14`, `docs/reports/SPEC_COVERAGE_REPORT.md:9-18`, `git rev-parse HEAD`.
- `docs/architecture/ARCHITECTURE_NEXT_STEPS.md` records completed actions against files that no longer exist in those paths, especially `noaa_file_index/20260207/README.md`.
  Evidence: `docs/architecture/ARCHITECTURE_NEXT_STEPS.md:129-148`, missing `noaa_file_index/20260207/README.md`.

### Stale docs

- `docs/archive/REPO_FOLDER_STRUCTURE_REPORT.md` still shows a prior tree with `paper-preview.html`, root-level cleanup docs, old examples layout, and other surfaces no longer matching the current repository.
  Evidence: `docs/archive/REPO_FOLDER_STRUCTURE_REPORT.md`.
- `docs/archive/CURRENT_PROJECT_STATE.md` still centers the older 11-station contract-check narrative rather than the newer 100-station build.
  Evidence: `docs/archive/CURRENT_PROJECT_STATE.md:38-108`.
- `reproducibility/pipeline_snapshot.json` is clearly stale.
  Evidence: `reproducibility/pipeline_snapshot.json:2-14`.

### Inconsistent terminology

- The project alternates among "publication-ready", "publishability", "publication readiness", "reproducibility", "verification triangle", and "verification-first architecture" without one plain reviewer-facing explanation.
- `docs/ARTIFACT_BOUNDARY_POLICY.md` still says "`quality_assessment.json` ... advisory threshold findings" even though the later cleanup says threshold/scoring language was removed.
  Evidence: `docs/ARTIFACT_BOUNDARY_POLICY.md:36-38`, `docs/reports/quality_artifact_language_cleanup_20260320.md:10-39`.

### Mismatched semantics

- The gate and audit use the label `station_year_usable_row_rate`, but the actual CSV column is `usable_row_rate`.
  Evidence: `src/noaa_spec/cleaning_runner.py:3840-3864`, `<EXTERNAL_STORAGE>/.../manifests/publication_readiness_gate.json:9-30`, `<EXTERNAL_STORAGE>/.../quality_reports/station_year_quality.csv`.
- The validation plan says "full repository test suite" is required, but the visible CI workflow does not run it.
  Evidence: `docs/PIPELINE_VALIDATION_PLAN.md:24-61`, `.github/workflows/suspicious_coverage.yml:49-147`.

## Reproducibility and reviewer experience

### What is clear

- How to install the project minimally.
  Evidence: `README.md:13-39`.
- How to run the bounded deterministic sample example.
  Evidence: `README.md:41-57`, `reproducibility/README.md:5-29`, `examples/README.md:3-9`.
- What a completed build should contain.
  Evidence: `docs/ARTIFACT_BOUNDARY_POLICY.md`, `docs/CLEANING_RUN_MODES.md`.

### What is unclear

- How a reviewer should move from the sample example to validating the 100-station claim set.
- Which exact code revision should be paired with the 100-station build.
- Whether the 100-station build is intended as a submission artifact, a local validation artifact, or just supporting evidence.

### What is missing

- A single reviewer guide mapping:
  raw input -> staged batch selection -> cleaning-run -> manifests -> quality evidence -> manuscript claims.
- A release note or submission note explicitly tying the manuscript to one commit and one archived build.
- A human-readable explanation of why some stations legitimately lack some domain artifacts.

## Highest-risk issues before JOSS submission

### Critical

- Paper overemphasizes AI-assisted development and underemphasizes the actual software contribution.
  Why it matters: JOSS reviewers evaluate software utility, design, installability, and community value. The current paper invites "this is a methods/results paper about AI workflow" criticism.
  Exact evidence/files: `paper/paper.md:21-27`, `paper/paper.md:33`, `paper/paper.md:57-65`, `paper/paper.md:85-89`, tag `ai-assisted-development` at `paper/paper.md:3-8`.
  Recommended fix: Rewrite the abstract, summary, software design, and impact statement so NOAA-Spec itself is the contribution; demote AI workflow to one short disclosure paragraph or remove it entirely from the main framing.
  Must-fix before submission: Yes.

- The manuscript's confidence language outruns the repository's own provenance-risk evidence.
  Why it matters: a reviewer who opens the provenance docs will see a less settled story than the paper presents.
  Exact evidence/files: `paper/paper.md:45-65`; `docs/reports/RULE_PROVENANCE_LEDGER.md:12-22`; `docs/reports/UNDOCUMENTED_RULES_REVIEW.md:5-16`.
  Recommended fix: Add a limitations/disclosure paragraph explaining documented_exact vs documented_inferred vs engineering-guard behavior, and state clearly that some stricter behaviors remain under active review.
  Must-fix before submission: Yes.

### High

- The strongest 100-station evidence is not packaged as reviewer-portable submission evidence.
  Why it matters: reviewers can distrust claims if the decisive artifact lives only on a local external drive.
  Exact evidence/files: `<EXTERNAL_STORAGE>/.../build_20260322T070910Z/*`; no matching tracked `release/build_20260322T070910Z` snapshot.
  Recommended fix: archive a sanitized release exemplar or publish a Zenodo/OSF-style snapshot and cite it from the paper and README.
  Must-fix before submission: Yes.

- The audited build does not match the current checkout revision.
  Why it matters: this weakens exact reproducibility and claim alignment.
  Exact evidence/files: `<EXTERNAL_STORAGE>/.../build_metadata.json:2-5` shows `173f3dc9...`; current checkout is `ce4cf3ff...`; `reproducibility/pipeline_snapshot.json:13-14` points to yet another commit.
  Recommended fix: either rebuild from the submission commit or state exactly which commit the build corresponds to and freeze that pairing in submission materials.
  Must-fix before submission: Yes.

- Reproducibility materials are stale.
  Why it matters: stale reproducibility artifacts are a credibility hit because they suggest the public story is lagging behind the software.
  Exact evidence/files: `reproducibility/pipeline_snapshot.json:2-14`, `reproducibility/environment.txt`, `docs/archive/CURRENT_PROJECT_STATE.md:17-23`.
  Recommended fix: regenerate or remove stale reproducibility snapshots, and replace them with one current submission-grade provenance note.
  Must-fix before submission: Yes.

- Archive/history docs still leak into the active reviewer narrative.
  Why it matters: reviewers will encounter multiple repository "states" and may not know which is canonical.
  Exact evidence/files: `docs/archive/REPO_FOLDER_STRUCTURE_REPORT.md`, `docs/architecture/ARCHITECTURE_NEXT_STEPS.md:129-148`, references to missing `noaa_file_index/20260207/README.md`.
  Recommended fix: prune or clearly label obsolete archive docs; remove stale references from active docs.
  Must-fix before submission: Yes.

### Medium

- The paper includes a results-style section that is stronger than needed for JOSS and could distract from the software contribution.
  Why it matters: reviewers may ask why this is a software paper rather than a research paper.
  Exact evidence/files: `paper/paper.md:67-83`.
  Recommended fix: compress results into a brief validation/evidence paragraph tied directly to software outputs and release artifacts.
  Must-fix before submission: Probably.

- CI surface is thinner than the documentation implies.
  Why it matters: the repo claims strong validation discipline, but visible automation is narrower.
  Exact evidence/files: `docs/PIPELINE_VALIDATION_PLAN.md:24-61`, `.github/workflows/suspicious_coverage.yml:49-147`.
  Recommended fix: either add fuller CI or soften the public claim so it matches visible automation.
  Must-fix before submission: Probably.

- Reviewer path from quickstart to publication artifact validation is not explicit.
  Why it matters: this reduces accessibility even if the software is technically strong.
  Exact evidence/files: `README.md`, `docs/README.md`, `reproducibility/README.md`, `docs/examples/README.md`.
  Recommended fix: add one short reviewer guide or submission walkthrough.
  Must-fix before submission: Probably.

- Some public metadata surfaces still look unfinished.
  Why it matters: small issues can create "local project" optics.
  Exact evidence/files: `CITATION.cff:9-10`, `pyproject.toml:1-17`.
  Recommended fix: replace placeholder DOI or remove it, add a real project description.
  Must-fix before submission: Nice-to-have if time is tight; DOI placeholder is the one worth fixing.

- The build contains 12 stations without `precipitation` domain artifacts, but the absence is undocumented.
  Why it matters: this can look like incompleteness to a reviewer.
  Exact evidence/files: `<EXTERNAL_STORAGE>/.../release_manifest.csv`; derived count from manifest shows 588 domain datasets and 12 stations missing `precipitation`.
  Recommended fix: document that empty domains may be omitted when no rows survive projection, if that is the intended semantics.
  Must-fix before submission: Nice-to-have.

### Low

- Terminology around quality diagnostics still has minor residue from older "advisory threshold" language.
  Why it matters: not a blocker, but it weakens semantic crispness.
  Exact evidence/files: `docs/ARTIFACT_BOUNDARY_POLICY.md:36-38`, `docs/reports/quality_artifact_language_cleanup_20260320.md:10-39`.
  Recommended fix: normalize wording to "descriptive diagnostics" everywhere.
  Must-fix before submission: Nice-to-have.

- `tests/test_integration.py` is fixture-optional and can skip entirely.
  Why it matters: not fatal, but reviewers may overestimate how much integration coverage is always exercised.
  Exact evidence/files: `tests/test_integration.py:36-69`.
  Recommended fix: document this explicitly or add a small tracked fixture set if feasible.
  Must-fix before submission: Safe to leave if clearly disclosed elsewhere.

## Recommended action plan

### Must fix before submission

- Rewrite the paper to center the software, not the AI workflow.
- Add a limitations/disclosure paragraph about inferred and engineering-guard rules.
- Tie the manuscript to one exact code revision and one archived build snapshot.
- Replace or remove stale reproducibility artifacts, especially `reproducibility/pipeline_snapshot.json`.
- Remove or quarantine stale references to absent or superseded docs from active surfaces.
- Fix `CITATION.cff` placeholder DOI.

### Should fix if time permits

- Add one reviewer-facing walkthrough from sample install to release evidence.
- Clarify in docs why some domain datasets may be absent for some stations.
- Tighten wording drift around quality diagnostics and gate semantics.
- Expand visible CI or narrow the claims made about automated validation.

### Safe to ignore for JOSS

- Broad repository archive history, as long as it is clearly marked and no longer linked from active docs.
- Minor metadata polish beyond the placeholder DOI and empty package description.

## Bottom line

Submit only after a focused hardening pass.

The core software and the 100-station build are strong enough that this should not be treated as a major rework. But the current submission package still leaves avoidable reviewer attack surfaces: AI-centric framing, stale evidence anchors, and insufficiently packaged empirical support. Fix those, and the repository should read as a disciplined scientific software artifact rather than an impressive local research build with an unstable public story.
