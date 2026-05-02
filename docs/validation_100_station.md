# 100-Station Operational Validation

The repository contains the code to reproduce a reviewer-facing 100-station operational validation artifact. The repository keeps small upstream-traceable fixtures for semantic verification, while the larger 100-station validation bundle is intended for external archival rather than in-repo tracking.

Small upstream-traceable fixtures verify semantic correctness. The 100-station validation artifact demonstrates that the same repository-controlled workflow runs successfully across a broader stratified operational sample.

## A. Quick semantic verification

This is the normal reviewer quick path.

- Uses the small tracked fixtures already committed in the repository.
- No external data is required.
- The fixture-backed path verifies semantic behavior and checksum-stable output for the public cleaning workflow.

See `REPRODUCIBILITY.md`, `reproducibility/checksums.sha256`, and the tracked fixture directories for the in-repo verification path.

## B. Inspect archived 100-station validation bundle

This is the intended reviewer path for broader operational evidence beyond the small fixtures.

- Uses an externally archived validation artifact rather than local NOAA downloads.
- Allows inspection of selected station inputs or archived source snapshots, canonical cleaned outputs, manifests, checksums, and `summary.md`.
- Does not require the reviewer to already have 100 downloaded station files locally.

## Archived validation bundle

Status: pending DOI before submission.

DOI: TO_BE_ADDED_BEFORE_JOSS_SUBMISSION

Planned contents:

- selected 100 station input files or archived source snapshots
- `station_selection_manifest.csv`
- `run_manifest.json`
- `station_results.csv`
- `canonical_cleaned/`
- `quality_reports/`
- `summary.md`
- `checksums.txt`

The generated validation artifact can include 100 cleaned station outputs, per-station quality JSON files, manifests, and checksums. That is useful reviewer evidence, but it is not appropriate to commit into the source repository because it would materially increase repository size. The repository therefore keeps the workflow and small semantic fixtures, while the larger validation bundle is meant to be archived externally with a DOI.

## C. Reproduce the 100-station validation locally

This path is optional.

- It is for maintainers or reviewers who want to reproduce the archived validation artifact.
- It requires either downloaded station files or the archived input bundle.
- It uses `noaa-spec build-validation-bundle`.

Provide a directory of station files that this repository can read as `.csv`, `.csv.gz`, or `.parquet` inputs, or point the workflow at an unpacked archived input bundle. Then run:

```bash
noaa-spec build-validation-bundle \
  --source-root /path/to/downloaded/stations \
  --output-root artifacts/validation_100_station/build_20260430 \
  --count 100 \
  --strategy size-stratified \
  --seed 20260430
```

The workflow fails if fewer than the requested number of viable station files are available. By default it also fails if any selected station run fails. Use `--continue-on-error` only when diagnostic partial output is more important than strict pass/fail behavior.

## Generated artifacts

The output directory contains:

- `raw_inputs/`
- `station_selection_manifest.csv`
- `run_manifest.json`
- `station_results.csv`
- `canonical_cleaned/`
- `quality_reports/`
- `summary.md`
- `checksums.txt`
- `archive_manifest.json`

The selection manifest records the auditable deterministic sample and the copied raw-input provenance. The run manifest records environment metadata and the reproducibility boundary. The results table records per-station status, row counts, runtime, raw checksums, and output checksums. The checksum file covers the key generated artifacts so the validation package can be archived externally.

## Relationship to the tracked fixtures

The repository’s small tracked fixtures remain the semantic verification layer and the normal quick reviewer path. The archived 100-station workflow complements them by showing that the same cleaning code path executes successfully across a broader stratified operational sample without turning this repository into a downloader or claiming NOAA-wide exhaustiveness.

## External archival

For JOSS or later archival packaging, generate the output locally, review `summary.md` and `checksums.txt`, and archive the resulting artifact bundle in an external repository or data archive that can mint a DOI. Reviewers should be able to inspect that archived bundle without rerunning the workflow. Local rerun is optional and requires either the archived input bundle or local station downloads. The source repository remains small and focused while the larger validation bundle can be cited separately.
