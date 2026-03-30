# INTERNAL DEVELOPMENT RECORD — NOT REVIEWER EVIDENCE

# Checksum Finalization Integrity Fix

## Root Cause

The failure mode was a finalization-ordering bug, not a cleaning-content bug.

Before this change:

- finalized station and quality artifacts were already on disk
- `release_manifest.csv` was written from one checksum snapshot
- `quality_assessment.json` was written next
- `file_manifest.csv` was written once without the gate row
- `publication_readiness_gate.json` was then built from that intermediate file manifest
- `file_manifest.csv` was rewritten again to add publication-gate coverage

That allowed three integrity defects:

- the embedded gate could describe an older manifest snapshot
- the same physical artifact path could acquire different checksums across manifests if the file changed between checksum passes
- there was no explicit guard preventing post-registration rewrites

## Lifecycle Before vs After

### Before

1. write finalized artifacts
2. compute release-manifest checksums
3. write `release_manifest.csv`
4. write `quality_assessment.json`
5. compute/write `file_manifest.csv`
6. compute/write `publication_readiness_gate.json`
7. rewrite `file_manifest.csv`

### After

1. write finalized station/quality artifacts
2. register checksums from finalized on-disk paths into a single checksum registry
3. build and write `release_manifest.csv` from that registry
4. write and register `quality_assessment.json`
5. precompute the publication-gate checksum from the final manifest snapshot
6. build and write `file_manifest.csv` once, using the same registry plus the precomputed gate checksum
7. build `publication_readiness_gate.json` from the final manifest frames
8. write the gate last
9. generate `manifests/post_run_audit.md` from the finished build state

## Invariants Now Enforced

- finalized artifact checksums come from one registry, not multiple timing-dependent passes
- `release_manifest.csv` and `file_manifest.csv` must agree on checksum for the same artifact path
- once a finalized path is checksum-registered, writing that path again raises an error
- the publication gate is generated from the final manifest snapshot
- a completed run emits a post-run audit snapshot automatically
- if the final gate payload changes after `file_manifest.csv` is built, finalization fails loudly

## Why This Fixes The Audit Failure Mode

The audit failure was driven by drift between checksum capture, manifest writing, and gate generation. The new flow removes the second `file_manifest.csv` write, makes manifest checksums depend on a single registered artifact state, and forces the gate to be the last integrity artifact written.

That closes the stale-gate and cross-manifest checksum divergence class without weakening any integrity check.
