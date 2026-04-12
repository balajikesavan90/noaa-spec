# Reproducibility

This document describes the tracked reproducibility checks for the JOSS-facing NOAA-Spec claim: deterministic cleaned CSV output from the public `noaa-spec clean` CLI.

## Docker Verification

Docker is the repository-provided reviewer path.

```bash
docker build -f Dockerfile -t noaa-spec-review .
docker run --rm noaa-spec-review bash scripts/verify_reproducibility.sh
```

Expected result:

```text
PASS: minimal 20e571805ad6eafd0d538b57f64e94ddc6aebe78280e3c10c48095f375f49850
PASS: minimal_second e6f8ae6ca75c10bdbbc1714cc61f49d0afcbe7ad6767da58551fc73742dab934
PASS: real_provenance_example e7db5076bc211e1a2a738de5ed83e42ba8543d0b1ce7a686f4cd06f399164e53
PASS: station_03041099999_aonach_mor 8a38e712e4fcb81bc26860b5a575c05951b3d6761fc04511a6237acfe454abe2
PASS: station_01116099999_stokka a13415c7916371aecdfe0b6e8d5c81eae63207ef7a46606e45b98f0e59b7ae6c
PASS: station_94368099999_hamilton_island 1d741b69938780663c88d8f4b982f1d01fc6a8212fe4b4fa0878040e222f1f4e
PASS: reproducibility verification succeeded.
Output directory: /tmp/noaa-spec-reproducibility
```

The verification script runs each tracked raw fixture through the public CLI. The primary fixture command is:

```bash
python3 -m noaa_spec.cli clean reproducibility/minimal/station_raw.csv /tmp/noaa-spec-sample.csv
```

It then compares each generated CSV checksum to the tracked expected output.

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

The cleaned CSV is wider than a single analysis table because NOAA-Spec preserves decoded measurements, NOAA quality codes, validation sidecars, and row-level usability summaries. Width depends on which optional NOAA encoded fields are present in the input.

## Primary Fixture

Tracked files:

- Raw input: `reproducibility/minimal/station_raw.csv`
- Raw input SHA256: `50e8bfb9ffae8278652bb7410cfbc9683a48711c35cfcf9e9dd3c38bbc403d47`
- Expected output: `reproducibility/minimal/station_cleaned_expected.csv`
- Expected output SHA256: `20e571805ad6eafd0d538b57f64e94ddc6aebe78280e3c10c48095f375f49850`

Local verification:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
noaa-spec clean reproducibility/minimal/station_raw.csv /tmp/noaa-spec-sample.csv
sha256sum /tmp/noaa-spec-sample.csv
```

Python 3.11 and 3.12 are supported by project metadata; use `python3.11` in the virtual-environment command if that is the supported interpreter available on your system.

Expected checksum:

```text
20e571805ad6eafd0d538b57f64e94ddc6aebe78280e3c10c48095f375f49850
```

## Secondary Fixture

The second tracked fixture gives broader field coverage while remaining small enough for direct review.

Tracked files:

- Raw input: `reproducibility/minimal_second/station_raw.csv`
- Raw input SHA256: `7b77a6b636baaf00f465c747d541e237417757d518e13e6e286045b53d6fe685`
- Expected output: `reproducibility/minimal_second/station_cleaned_expected.csv`
- Expected output SHA256: `e6f8ae6ca75c10bdbbc1714cc61f49d0afcbe7ad6767da58551fc73742dab934`

Run and verify:

```bash
noaa-spec clean reproducibility/minimal_second/station_raw.csv /tmp/noaa-spec-second.csv
sha256sum /tmp/noaa-spec-second.csv
```

Expected checksum:

```text
e6f8ae6ca75c10bdbbc1714cc61f49d0afcbe7ad6767da58551fc73742dab934
```

## Fully Traceable Example

This is the strongest real-world provenance case in the repository. It is still small and reviewer-checkable, but unlike the older curated station slices it records the upstream NOAA/NCEI source URL and observed upstream checksum.

Tracked files:

- Raw input: `reproducibility/real_provenance_example/station_raw.csv`
- Raw input SHA256: `2e91752f732f81e2e20e539b738bd9c46afa4d6cba24bdb4e0c0b972194083fc`
- Expected output: `reproducibility/real_provenance_example/station_cleaned_expected.csv`
- Expected output SHA256: `e7db5076bc211e1a2a738de5ed83e42ba8543d0b1ce7a686f4cd06f399164e53`
- Upstream source URL: `https://www.ncei.noaa.gov/data/global-hourly/access/2024/03041099999.csv`
- Upstream full CSV SHA256 observed on 2026-04-12: `853a03a7108aef0d080cdafc2c30537ce9992841bb2b0f780aa0a6461c311169`

The fixture contains the header and first five data rows from the upstream source file. See [reproducibility/REAL_PROVENANCE_EXAMPLE.md](reproducibility/REAL_PROVENANCE_EXAMPLE.md) for the full provenance boundary.

Run and verify:

```bash
noaa-spec clean reproducibility/real_provenance_example/station_raw.csv /tmp/noaa-spec-real-provenance.csv
sha256sum /tmp/noaa-spec-real-provenance.csv
```

Expected checksum:

```text
e7db5076bc211e1a2a738de5ed83e42ba8543d0b1ce7a686f4cd06f399164e53
```

## Additional Station Fixtures

These 4-row fixtures were selected from local real-station examples to broaden reviewer evidence across geography and reporting characteristics without adding large datasets. Their expected outputs were generated with the same `noaa-spec clean` CLI. The exact upstream retrieval dates and original NOAA URL/year-file metadata were not retained when these slices were curated; see [reproducibility/FIXTURE_PROVENANCE.md](reproducibility/FIXTURE_PROVENANCE.md).

| Fixture | Station | Raw input SHA256 | Expected output SHA256 | Coverage note |
| --- | --- | --- | --- | --- |
| `station_03041099999_aonach_mor/` | Aonach Mor, UK | `30f7edbcd4dcc475727ee2c66187a251a6bf35d91bfc7f700aadd39d27cdbcf1` | `8a38e712e4fcb81bc26860b5a575c05951b3d6761fc04511a6237acfe454abe2` | High-elevation UK station with mandatory fields, sentinel-heavy pressure/visibility cases, supplemental wind, and wave/sea side fields. |
| `station_01116099999_stokka/` | Stokka, Norway | `cc08ee8aeafe1494b4c8ab73a386a0f425c81db995b66ee0fe9284050fddfc17` | `a13415c7916371aecdfe0b6e8d5c81eae63207ef7a46606e45b98f0e59b7ae6c` | Norwegian station with multiple cloud layers, present/past weather, runway/weather-extension fields, and station pressure. |
| `station_94368099999_hamilton_island/` | Hamilton Island Airport, Australia | `ccef9c7c69f8a11e4896277bc5aebb41e44570cf46028c3c567991d10d680851` | `1d741b69938780663c88d8f4b982f1d01fc6a8212fe4b4fa0878040e222f1f4e` | Australian airport station with precipitation, past/present weather, sea-level pressure, and additional weather-code fields. |

Run and verify one station fixture manually:

```bash
noaa-spec clean reproducibility/station_03041099999_aonach_mor/station_raw.csv /tmp/noaa-spec-aonach-mor.csv
sha256sum /tmp/noaa-spec-aonach-mor.csv
```

Expected checksum:

```text
8a38e712e4fcb81bc26860b5a575c05951b3d6761fc04511a6237acfe454abe2
```

## Fixture Coverage Note

The primary fixture contains 5 raw rows. The secondary fixture contains 8 raw rows and includes additional NOAA field structures including precipitation (`AA1`-`AA4`), multiple cloud layers (`GA1`-`GA5`), past weather (`AY1`/`AY2`), extreme temperature (`KA1`/`KA2`), and present weather (`MW1`-`MW3`). The three additional station fixtures each contain 4 raw rows.

These fixtures are reproducibility checks, not a claim of exhaustive NOAA coverage. Only `real_provenance_example/` records a complete source URL and observed upstream checksum; the curated station slices do not replay upstream acquisition. The automated tests exercise additional encoded cases for sentinel handling, QC preservation, deterministic output, CLI behavior, and field parsing.
