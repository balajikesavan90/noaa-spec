# Reproducibility

This document describes the tracked reproducibility checks for the JOSS-facing NOAA-Spec claim: deterministic cleaned CSV output from the public `noaa-spec clean` CLI.

The boundary is deliberately precise:

- Reproducible from the repository alone: `clean(committed_input) = committed_output` for tracked raw fixtures, verified against `reproducibility/checksums.sha256`.
- Additionally traceable to upstream NOAA retrieval: `reproducibility/real_provenance_example/`, `reproducibility/traceable_peru_il_2014_aa1_qc/`, and `reproducibility/traceable_albion_ne_2014_calm_aa1/` record NOAA/NCEI source URLs, retrieval dates, and observed upstream checksums.
- Not claimed: full upstream NOAA retrieval reproducibility for every curated fixture, NOAA downloading, multi-station orchestration, or exhaustive NOAA coverage.

## Docker Verification

Docker is the repository-provided reproducibility path.

```bash
docker build -f Dockerfile -t noaa-spec-review .
docker run --rm noaa-spec-review bash scripts/verify_reproducibility.sh
```

Expected result: one `PASS` line for each tracked `station_cleaned_expected.csv`
entry in `reproducibility/checksums.sha256`, followed by:

```text
PASS: reproducibility verification succeeded.
Output directory: /tmp/noaa-spec-reproducibility
```

The verification script runs each tracked raw fixture through the public CLI. The primary fixture command is:

```bash
python3 -m noaa_spec.cli clean reproducibility/minimal/station_raw.csv /tmp/noaa-spec-sample.csv
```

It then compares each generated CSV checksum to the tracked expected output
hashes in `reproducibility/checksums.sha256`. That file is the canonical
checksum manifest for tracked reproducibility artifacts.

The Dockerfile defines a tested reproducibility container and pins the `python:3.12-slim` base image by digest. It is still not a fully immutable archived runtime because it refreshes Debian package metadata and upgrades bootstrap packaging tools during the image build.

After verification, a useful first inspection is the core raw fixture and expected cleaned output side by side:

- `reproducibility/minimal/station_raw.csv`
- `reproducibility/minimal/station_cleaned_expected.csv`
- `docs/supported_fields.md`
- `docs/schema.md`
- `docs/rule_provenance.md`
- `reproducibility/checksums.sha256`
- `docs/evidence_matrix.md`

The cleaned CSV is wider than a single analysis table because NOAA-Spec preserves decoded measurements, NOAA quality codes, validation sidecars, and row-level usability summaries. Width depends on which optional NOAA encoded fields are present in the input. Start with `docs/first_output_guide.md` for a compact first view before reading the full CSV.

The static curated examples under `artifacts/curated_examples/` are optional appendix material only. They are not part of this checksum-backed reproducibility contract, not required by the Docker reproducibility path, and not part of the core validation path.

## Primary Fixture

Tracked files:

- Raw input: `reproducibility/minimal/station_raw.csv`
- Expected output: `reproducibility/minimal/station_cleaned_expected.csv`
- Checksums: `reproducibility/checksums.sha256`

Local verification:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
noaa-spec clean reproducibility/minimal/station_raw.csv /tmp/noaa-spec-sample.csv
sha256sum /tmp/noaa-spec-sample.csv
```

Python 3.11 and 3.12 are supported by project metadata; use `python3.11` in the virtual-environment command if that is the supported interpreter available on your system. After activation, `python` refers to the virtual-environment interpreter.

Compare the generated checksum with the matching
`reproducibility/minimal/station_cleaned_expected.csv` entry in
`reproducibility/checksums.sha256`.

## Secondary Fixture

The second tracked fixture gives broader field coverage while remaining small enough for direct review.

Tracked files:

- Raw input: `reproducibility/minimal_second/station_raw.csv`
- Expected output: `reproducibility/minimal_second/station_cleaned_expected.csv`
- Checksums: `reproducibility/checksums.sha256`

Run and verify:

```bash
noaa-spec clean reproducibility/minimal_second/station_raw.csv /tmp/noaa-spec-second.csv
sha256sum /tmp/noaa-spec-second.csv
```

Compare the generated checksum with the matching
`reproducibility/minimal_second/station_cleaned_expected.csv` entry in
`reproducibility/checksums.sha256`.

## Traceable Fixtures

These are the fixtures with upstream NOAA retrieval traceability in the repository. They are still small and directly inspectable, but unlike the older curated station slices they record NOAA/NCEI source URLs, retrieval dates, observed upstream checksums, and exact extraction commands.

Tracked fixtures:

| Fixture | Station / year | Rows | Coverage note |
| --- | --- | --- | --- |
| `real_provenance_example/` | `78724099999` / 2001 | 20 | Core mandatory fields plus incidental additional fields where present. |
| `traceable_peru_il_2014_aa1_qc/` | `72214904899` / 2014 | 1 | One promoted edge-case row; secondary fields remain outside the primary JOSS claim. |
| `traceable_albion_ne_2014_calm_aa1/` | `72344154921` / 2014 | 1 | One promoted edge-case row; secondary fields remain outside the primary JOSS claim. |

Checksums are recorded in `reproducibility/checksums.sha256`, including observed upstream source CSV checksums. See [reproducibility/TRACEABLE_FIXTURES.md](reproducibility/TRACEABLE_FIXTURES.md) for NOAA URLs, retrieval dates, row selection, and extraction commands. The older curated station fixtures remain deterministic committed input/output checks, not upstream replay artifacts.

Run and verify one traceable fixture manually:

```bash
noaa-spec clean reproducibility/real_provenance_example/station_raw.csv /tmp/noaa-spec-real-provenance.csv
sha256sum /tmp/noaa-spec-real-provenance.csv
```

Compare the generated checksum with the matching
`reproducibility/real_provenance_example/station_cleaned_expected.csv` entry in
`reproducibility/checksums.sha256`.

## Additional Station Fixtures

These 4-row fixtures are committed real-station slices that broaden deterministic input/output checks without changing the core contribution boundary. Their expected outputs were generated with the same `noaa-spec clean` CLI. The exact upstream retrieval dates and original NOAA URL/year-file metadata were not retained when these slices were curated; see [reproducibility/FIXTURE_PROVENANCE.md](reproducibility/FIXTURE_PROVENANCE.md).

| Fixture | Station | Coverage note |
| --- | --- | --- |
| `station_03041099999_aonach_mor/` | Aonach Mor, UK | Additional deterministic input/output check; not upstream replay evidence. |
| `station_01116099999_stokka/` | Stokka, Norway | Additional deterministic input/output check; not upstream replay evidence. |
| `station_94368099999_hamilton_island/` | Hamilton Island Airport, Australia | Additional deterministic input/output check; not upstream replay evidence. |

Checksums for these files are in `reproducibility/checksums.sha256`.

Run and verify one station fixture manually:

```bash
noaa-spec clean reproducibility/station_03041099999_aonach_mor/station_raw.csv /tmp/noaa-spec-aonach-mor.csv
sha256sum /tmp/noaa-spec-aonach-mor.csv
```

Compare the generated checksum with the matching
`reproducibility/station_03041099999_aonach_mor/station_cleaned_expected.csv`
entry in `reproducibility/checksums.sha256`.

## Fixture Coverage Note

The primary fixture contains 5 raw rows. The traceable fixtures contain 22 raw rows total: the original 20-row source slice plus two one-row source slices. The secondary fixture and additional station fixtures include some additional NOAA field structures, but those fields are secondary implementation coverage, not the primary JOSS evidence. The three additional station fixtures each contain 4 raw rows.

These fixtures are reproducibility checks, not a claim of exhaustive NOAA coverage. The three traceable fixture directories record complete source URLs, retrieval dates, and observed upstream checksums; the older curated station slices do not replay upstream acquisition. The automated tests exercise additional encoded cases for sentinel handling, QC preservation, deterministic output, CLI behavior, and field parsing.

For a concise claim-to-evidence map, including which claims are fixture-backed, upstream-traceable fixture-backed, unit-test-backed, or documentation-only, see [docs/evidence_matrix.md](docs/evidence_matrix.md).
