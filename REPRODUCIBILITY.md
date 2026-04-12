# Reproducibility

This document describes the tracked reproducibility checks for the JOSS-facing NOAA-Spec claim: deterministic canonical CSV output from the public `noaa-spec clean` CLI.

## Docker Verification

```bash
docker build -f Dockerfile -t noaa-spec-review .
docker run --rm noaa-spec-review bash scripts/verify_reproducibility.sh
```

Expected result:

```text
PASS: reproducibility verification succeeded.
SHA256: b48aba1b8a304451dc3874b963d76275bf79ad68c6f28d9190e0e636f2887597
```

The verification script runs:

```bash
python3 -m noaa_spec.cli clean reproducibility/minimal/station_raw.csv /tmp/noaa-spec-sample.csv
```

It then compares the generated CSV checksum to the tracked expected output.

After verification, reviewers should inspect the raw fixture and expected cleaned output side by side:

- `reproducibility/minimal/station_raw.csv`
- `reproducibility/minimal/station_cleaned_expected.csv`
- `docs/schema.md`
- `docs/rule_provenance.md`

The cleaned CSV is wider than a single analysis table because NOAA-Spec preserves decoded measurements, NOAA quality codes, validation sidecars, and row-level usability summaries. Width depends on which optional NOAA encoded fields are present in the input.

## Primary Fixture

Tracked files:

- Raw input: `reproducibility/minimal/station_raw.csv`
- Raw input SHA256: `50e8bfb9ffae8278652bb7410cfbc9683a48711c35cfcf9e9dd3c38bbc403d47`
- Expected output: `reproducibility/minimal/station_cleaned_expected.csv`
- Expected output SHA256: `b48aba1b8a304451dc3874b963d76275bf79ad68c6f28d9190e0e636f2887597`

Local verification:

```bash
python -m pip install -e .
noaa-spec clean reproducibility/minimal/station_raw.csv /tmp/noaa-spec-sample.csv
sha256sum /tmp/noaa-spec-sample.csv
```

Expected checksum:

```text
b48aba1b8a304451dc3874b963d76275bf79ad68c6f28d9190e0e636f2887597
```

## Secondary Fixture

The second tracked fixture gives broader field coverage while remaining small enough for direct review.

Tracked files:

- Raw input: `reproducibility/minimal_second/station_raw.csv`
- Raw input SHA256: `7b77a6b636baaf00f465c747d541e237417757d518e13e6e286045b53d6fe685`
- Expected output: `reproducibility/minimal_second/station_cleaned_expected.csv`
- Expected output SHA256: `223efb068df6d605646a1288feedf6621fa55b4c9074c027f6347cbe7ca2f30e`

Run and verify:

```bash
noaa-spec clean reproducibility/minimal_second/station_raw.csv /tmp/noaa-spec-second.csv
sha256sum /tmp/noaa-spec-second.csv
```

Expected checksum:

```text
223efb068df6d605646a1288feedf6621fa55b4c9074c027f6347cbe7ca2f30e
```

## Fixture Coverage Note

The primary fixture contains 5 raw rows. The secondary fixture contains 8 raw rows and includes additional NOAA field structures including precipitation (`AA1`-`AA4`), multiple cloud layers (`GA1`-`GA5`), past weather (`AY1`/`AY2`), extreme temperature (`KA1`/`KA2`), and present weather (`MW1`-`MW3`).

These fixtures are reproducibility checks, not a claim of exhaustive NOAA coverage. The automated tests exercise additional encoded cases for sentinel handling, QC preservation, deterministic output, CLI behavior, and field parsing.
