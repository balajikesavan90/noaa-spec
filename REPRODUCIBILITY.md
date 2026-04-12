# Reproducibility

This document describes the tracked reproducibility checks for the JOSS-facing NOAA-Spec claim: deterministic cleaned CSV output from the public `noaa-spec clean` CLI.

## Docker Verification

Docker is the repository-provided reviewer path.

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

Optional domain split CSVs are derived convenience views from cleaned output. They are not part of this primary checksum workflow.

The Dockerfile defines a tested reviewer container, but it is not a fully immutable environment: it currently uses the `python:3.12-slim` tag rather than a digest and upgrades bootstrap packaging tools during the image build.

After verification, reviewers should inspect the raw fixture and expected cleaned output side by side:

- `reproducibility/minimal/station_raw.csv`
- `reproducibility/minimal/station_cleaned_expected.csv`
- `docs/supported_fields.md`
- `docs/schema.md`
- `docs/rule_provenance.md`
- `reproducibility/REAL_PROVENANCE_EXAMPLE.md`
- `reproducibility/FIXTURE_PROVENANCE.md`
- `reproducibility/checksums.sha256`

The cleaned CSV is wider than a single analysis table because NOAA-Spec preserves decoded measurements, NOAA quality codes, validation sidecars, and row-level usability summaries. Width depends on which optional NOAA encoded fields are present in the input.

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

Python 3.11 and 3.12 are supported by project metadata; use `python3.11` in the virtual-environment command if that is the supported interpreter available on your system.

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

## Traceable Example

This is the strongest real-world provenance case in the repository. It is still small and reviewer-checkable, but unlike the older curated station slices it records the upstream NOAA/NCEI source URL and observed upstream checksum.

Tracked files:

- Raw input: `reproducibility/real_provenance_example/station_raw.csv`
- Expected output: `reproducibility/real_provenance_example/station_cleaned_expected.csv`
- Checksums: `reproducibility/checksums.sha256`
- Upstream source URL: `https://www.ncei.noaa.gov/data/global-hourly/access/2001/78724099999.csv`
- Upstream source CSV checksum: recorded in `reproducibility/checksums.sha256`

The fixture contains the header and first 20 data rows from the upstream source file. It includes supported wind, precipitation, cloud, present-weather, pressure, temperature, and remarks fields where present in that source slice. See [reproducibility/REAL_PROVENANCE_EXAMPLE.md](reproducibility/REAL_PROVENANCE_EXAMPLE.md) for the provenance boundary.

Run and verify:

```bash
noaa-spec clean reproducibility/real_provenance_example/station_raw.csv /tmp/noaa-spec-real-provenance.csv
sha256sum /tmp/noaa-spec-real-provenance.csv
```

Compare the generated checksum with the matching
`reproducibility/real_provenance_example/station_cleaned_expected.csv` entry in
`reproducibility/checksums.sha256`.

## Additional Station Fixtures

These 4-row fixtures were selected from local real-station examples to broaden reviewer evidence across geography and reporting characteristics without adding large datasets. Their expected outputs were generated with the same `noaa-spec clean` CLI. The exact upstream retrieval dates and original NOAA URL/year-file metadata were not retained when these slices were curated; see [reproducibility/FIXTURE_PROVENANCE.md](reproducibility/FIXTURE_PROVENANCE.md).

| Fixture | Station | Coverage note |
| --- | --- | --- |
| `station_03041099999_aonach_mor/` | Aonach Mor, UK | High-elevation UK station with mandatory fields, sentinel-heavy pressure/visibility cases, supplemental wind, and wave/sea side fields. |
| `station_01116099999_stokka/` | Stokka, Norway | Norwegian station with multiple cloud layers, present/past weather, runway/weather-extension fields, and station pressure. |
| `station_94368099999_hamilton_island/` | Hamilton Island Airport, Australia | Australian airport station with precipitation, past/present weather, sea-level pressure, and additional weather-code fields. |

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

The primary fixture contains 5 raw rows. The fully traceable example contains 20 raw rows and includes supported wind, precipitation, cloud, present-weather, pressure, temperature, and remarks fields where present in its source slice. The secondary fixture contains 8 raw rows and includes additional NOAA field structures including precipitation (`AA1`-`AA4`), multiple cloud layers (`GA1`-`GA5`), past weather (`AY1`/`AY2`), extreme temperature (`KA1`/`KA2`), and present weather (`MW1`-`MW3`). The three additional station fixtures each contain 4 raw rows.

These fixtures are reproducibility checks, not a claim of exhaustive NOAA coverage. Only `real_provenance_example/` records a complete source URL and observed upstream checksum; the curated station slices do not replay upstream acquisition. The automated tests exercise additional encoded cases for sentinel handling, QC preservation, deterministic output, CLI behavior, and field parsing.
