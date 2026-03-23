# Architecture Next Steps

Last reassessed: 2026-03-22

This document is retained as a planning record, not as the primary reviewer-facing description of the current software surface.

Use these documents for active evaluation instead:

- `README.md`
- `docs/REVIEWER_GUIDE.md`
- `docs/CLEANING_RUN_MODES.md`
- `docs/ARTIFACT_BOUNDARY_POLICY.md`
- `docs/DOMAIN_DATASET_REGISTRY.md`
- `docs/PIPELINE_VALIDATION_PLAN.md`

## Current direction

The repository's active public surface is organized around deterministic publication artifacts:

- canonical cleaned datasets,
- domain datasets,
- quality reports,
- release manifests with checksums and lineage.

The parser and cleaner remain the foundation, but reviewer-facing documentation should describe the concrete artifact contract rather than historical architecture framing.

## Near-term priorities

1. Keep artifact contracts and schemas stable unless a versioned change is required.
2. Preserve deterministic release behavior and manifest integrity.
3. Continue improving rule provenance and documentation alignment.
4. Prepare a frozen revision with paired larger-build evidence for final submission packaging.

## Archival note

Earlier versions of this file contained detailed milestone checklists and references to now-archived repository paths, including dated operational snapshot materials. Those historical details are intentionally removed from the active docs surface to avoid stale reviewer cues during pre-submission hardening.
