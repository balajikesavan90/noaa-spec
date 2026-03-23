# Pre-Freeze Submission Hardening Report

Date: 2026-03-22

## Scope

This pass addressed the non-build, non-freeze hardening items from the deep publication readiness audit. It did not freeze the repository, regenerate the 100-station evidence package, or create archival submission artifacts.

## What changed

### 1. Rewrote the JOSS paper to be software-first

Changed:

- rewrote `paper/paper.md` to center NOAA-Spec as the software contribution,
- removed the AI-first framing and the architecture-first "Verification Triangle" language from the manuscript,
- compressed research-style results language into software-validation and artifact-language,
- added a limitations and rule-provenance section that explicitly distinguishes documented rules, inferred rules, engineering guards, and stricter behaviors still under review,
- kept AI assistance only as a brief acknowledgement-level disclosure.

Why:

- the prior manuscript framed development method and conceptual architecture more strongly than the public software interface,
- the new text better matches a JOSS software paper and the repository's current provenance posture.

### 2. Reduced terminology drift and overclaim risk

Changed:

- updated `README.md` to emphasize contracts, manifests, checksums, quality reports, and validation,
- removed the README's `Verification Triangle` section and replaced it with concrete software-surface language,
- replaced the active `docs/architecture/ARCHITECTURE_NEXT_STEPS.md` content with a short planning-record document that no longer functions as a stale reviewer-facing roadmap,
- updated `paper/README.md`, `docs/README.md`, `docs/examples/README.md`, and `examples/README.md` to point readers toward the active reviewer path.

Why:

- the repository's concrete public surfaces are artifact contracts and release semantics, not the old conceptual labels,
- the old architecture roadmap had become a stale reviewer trap because it preserved completed checklist history and missing-path references.

### 3. Cleaned stale reproducibility anchors and stale active docs

Changed:

- removed `reproducibility/pipeline_snapshot.json`,
- removed `reproducibility/environment.txt`,
- rewrote `reproducibility/README.md` so the sample run is the active reproducibility anchor and revision-specific snapshots are explicitly deferred to frozen submission evidence,
- cleaned the remaining active docs so they no longer rely on those stale anchors.

Why:

- both tracked artifacts had become credibility liabilities because they were revision-specific but stale,
- keeping them in the active reviewer path would imply a frozen evidence state that does not exist yet.

### 4. Added a reviewer bridge

Changed:

- created `docs/REVIEWER_GUIDE.md`,
- linked it from `README.md`, `docs/README.md`, `paper/README.md`, `docs/examples/README.md`, and `examples/README.md`.

Why:

- the repository needed one concise path connecting installation, the sample run, artifact interpretation, and the relationship between the sample path and later bounded build evidence.

### 5. Clarified omitted domain artifact semantics

Changed:

- documented empty-domain omission behavior in `docs/REVIEWER_GUIDE.md`,
- documented the same semantics in `docs/CLEANING_RUN_MODES.md`,
- added domain-presence clarification to `docs/DOMAIN_DATASET_REGISTRY.md`,
- added a concise note in `README.md`.

Why:

- reviewers should not assume every station must emit every domain dataset,
- omission is intentional when no rows survive a domain projection or no valid domain data exists after cleaning.

### 6. Fixed metadata polish issues

Changed:

- removed the placeholder DOI from `CITATION.cff`,
- added a real software abstract and repository URL to `CITATION.cff`,
- added a real public-facing project description to `pyproject.toml`.

Why:

- placeholder metadata is a public credibility problem,
- the repository metadata should describe the software accurately without inventing publication identifiers.

### 7. Narrowed CI and validation claims

Changed:

- rewrote the CI section of `docs/PIPELINE_VALIDATION_PLAN.md` to distinguish local/full validation expectations from the narrower visible GitHub Actions surface,
- removed the stale reference to `.github/workflows/python-app.yml`,
- updated `tests/test_documentation_integrity.py` so the README integrity check follows the renamed software-first section heading.

Why:

- the visible automated CI surface is thinner than the previous doc wording implied,
- aligning claims is safer than expanding infrastructure in this pass.

### 8. Removed a lingering stale quality-language phrase

Changed:

- updated `docs/ARTIFACT_BOUNDARY_POLICY.md` to describe `quality_assessment.json` as descriptive rather than threshold-advisory.

Why:

- this kept the active docs aligned with the earlier quality-artifact language cleanup.

## Files modified

- `CITATION.cff`
- `README.md`
- `docs/ARTIFACT_BOUNDARY_POLICY.md`
- `docs/CLEANING_RUN_MODES.md`
- `docs/DOMAIN_DATASET_REGISTRY.md`
- `docs/PIPELINE_VALIDATION_PLAN.md`
- `docs/README.md`
- `docs/REVIEWER_GUIDE.md`
- `docs/architecture/ARCHITECTURE_NEXT_STEPS.md`
- `docs/examples/README.md`
- `examples/README.md`
- `paper/README.md`
- `paper/paper.md`
- `pyproject.toml`
- `reproducibility/README.md`
- `reproducibility/environment.txt` removed
- `reproducibility/pipeline_snapshot.json` removed
- `tests/test_documentation_integrity.py`

## Validation run in this pass

- `poetry run pytest tests/test_documentation_integrity.py -v`
- `poetry run pytest tests/test_publication_schema_ci.py -v`
- `poetry run pytest tests/test_reproducibility_example.py -v`

Result:

- all three targeted validation slices passed after updating the README section expectation in `tests/test_documentation_integrity.py`.

## Intentionally not addressed in this pass

- no repository freeze,
- no fresh 100-station build or evidence regeneration,
- no packaging of a frozen release snapshot under `release/build_<build_id>/`,
- no Zenodo or OSF preparation,
- no attempt to align the active repo to the previously audited 100-station build revision,
- no core cleaning-behavior changes to weaken or remove stricter rules yet,
- no broad CI expansion beyond claim alignment.

These belong to the final freeze/build-evidence pass or to a separate cleaning-semantics change set.

## Remaining risks

1. The strongest bounded-build evidence is still external to the tracked repository and still needs to be paired to a frozen revision in the final submission pass.
2. Rule provenance remains mixed: the manuscript now discloses this, but the underlying stricter and weakly supported behaviors are not resolved yet.
3. The visible GitHub Actions surface is still narrower than a full release gate, even though the docs now describe that honestly.
4. Archive materials still preserve older repository stories; they are no longer in the active reviewer path, but they remain discoverable history.

## Assessment

The repository now reads more like disciplined public scientific software and less like an evolving local research narrative. It is materially better prepared for the final freeze/build-evidence pass, but that final pass is still required before submission.
