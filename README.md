# NOAA-Spec

NOAA-Spec provides deterministic, specification-constrained cleaning of NOAA
Integrated Surface Database (ISD) / Global Hourly CSV observations by
normalizing documented sentinel values, preserving NOAA quality-code context,
and producing checksum-stable output for a defined supported field set. Its
public JOSS-facing workflow is the single command:

```bash
noaa-spec clean INPUT.csv OUTPUT.csv
```

The command writes an observation-level cleaned CSV with documented NOAA
sentinels normalized to empty null cells, NOAA quality codes preserved in
explicit columns, and deterministic row/order serialization. If the input CSV
includes a `raw_line` or `RAW_LINE` column, the cleaner also performs raw
record/header structural validation on that column. The value is not parsing
alone; it is making a bounded set of NOAA cleaning decisions explicit,
testable, provenance-aware, and checksum-stable so downstream researchers can
start from the same documented interpretation rather than divergent local
scripts. NOAA-Spec does not download NOAA data, orchestrate station batches,
split datasets into analysis domains, produce releases, or run analyses.

## Reviewer Path

Use the repository-defined, tested Docker reviewer environment. This is the
primary reviewer path; local installation below is a convenience path for users
who do not want Docker.

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

The canonical checksum list is `reproducibility/checksums.sha256`.

The Dockerfile pins the `python:3.12-slim` base image by digest, but it still refreshes Debian package metadata and upgrades bootstrap packaging tools during build. Treat it as a tested reviewer environment, not an immutable archived runtime. `requirements-review.txt` pins the Docker/reviewer Python dependency path only; it is not required for standard local installation.

## Traceable Fixtures

The upstream-traceable reproducibility fixtures are:

- `reproducibility/real_provenance_example/`: 20 rows from station `78724099999` in 2001.
- `reproducibility/traceable_peru_il_2014_aa1_qc/`: one row from station `72214904899` in 2014.
- `reproducibility/traceable_albion_ne_2014_calm_aa1/`: one row from station `72344154921` in 2014.
- Checksums: `reproducibility/checksums.sha256`
- Provenance note: `reproducibility/TRACEABLE_FIXTURES.md`

These demonstrate selected traceable NOAA source slices; they are not a claim
of broad NOAA coverage. Reviewer evaluation should focus on the core families:
`WND`, `CIG`, `VIS`, `TMP`, `DEW`, and `SLP`.

```text
https://www.ncei.noaa.gov/data/global-hourly/access/2001/78724099999.csv
https://www.ncei.noaa.gov/data/global-hourly/access/2014/72214904899.csv
https://www.ncei.noaa.gov/data/global-hourly/access/2014/72344154921.csv
```

After Docker or local install, run:

```bash
noaa-spec clean \
  reproducibility/real_provenance_example/station_raw.csv \
  /tmp/noaa-spec-real-provenance.csv
sha256sum /tmp/noaa-spec-real-provenance.csv
```

Compare the generated checksum with the matching
`reproducibility/real_provenance_example/station_cleaned_expected.csv` entry in
`reproducibility/checksums.sha256`.

Core-field snapshot from the tracked expected output:

| STATION | DATE | temperature_c | temperature_quality_code | visibility_m | visibility_quality_code | wind_speed_ms | wind_type_code | sea_level_pressure_hpa |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 78724099999 | 2001-01-01T15:00:00 | 29.3 | 1 | 28000.0 | 1.0 | 8.2 | N | 1013.8 |
| 78724099999 | 2001-01-01T18:00:00 | 32.7 | 1 | 28000.0 | 1.0 | 10.8 | N | 1011.9 |

### Raw Row Walkthrough

From the tracked primary fixture, this raw row snippet:

```text
STATION=40435099999
DATE=2000-03-17T09:00:00
TMP=+9999,9
VIS=999999,9,N,1
WND=999,9,9,9999,9
SLP=99999,9
```

becomes the following compact cleaned view. This is not the full schema; it is
the first-pass interpretation a reviewer should inspect.

| Output column | Meaning | Result |
| --- | --- | --- |
| `STATION` | Source station | `40435099999` |
| `DATE` | Observation timestamp | `2000-03-17T09:00:00` |
| `temperature_c` | Decoded air temperature | empty null |
| `temperature_quality_code` | NOAA QC flag from `TMP` | `9` |
| `TMP__qc_reason` | Why temperature is null | `SENTINEL_MISSING` |
| `visibility_m` | Decoded visibility distance | empty null |
| `visibility_quality_code` | NOAA QC flag from `VIS` | `9.0` |
| `VIS__part1__qc_reason` | Why visibility is null | `SENTINEL_MISSING` |
| `wind_speed_ms` | Decoded wind speed | empty null |
| `wind_speed_quality_code` | NOAA QC flag from `WND` | `9.0` |
| `sea_level_pressure_hpa` | Decoded sea-level pressure | empty null |

The useful behavior is explicit: sentinel-coded measurements become null while
the NOAA quality-code context remains visible.

## First Output: What To Look At

The full cleaned CSV is intentionally wide because it preserves decoded
measurements, NOAA quality codes, parser sidecars, and row-level usability
signals. For a first pass, start with decoded measurement columns and their NOAA
quality-code columns. Ignore `__qc_*` sidecars unless a decoded value is empty or
surprising.

| Column | What to check |
| --- | --- |
| `STATION`, `DATE` | Source station and observation timestamp. |
| `temperature_c` | Decoded air temperature; sentinels become null. |
| `temperature_quality_code` | NOAA QC code preserved from `TMP`. |
| `dew_point_c` | Decoded dew point temperature. |
| `visibility_m` | Decoded visibility; `999999` becomes null. |
| `visibility_quality_code` | NOAA QC code preserved from `VIS`. |
| `wind_speed_ms` | Decoded wind speed from `WND`. |
| `wind_speed_quality_code` | NOAA QC code preserved for wind speed. |
| `sea_level_pressure_hpa` | Decoded sea-level pressure; `99999` becomes null. |

Compact excerpt from the tracked primary fixture:

| STATION | DATE | temperature_c | temperature_quality_code | visibility_m | visibility_quality_code | wind_speed_ms | wind_type_code | TMP__qc_reason | VIS__part1__qc_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 40435099999 | 2000-01-10T06:00:00 | 18.0 | 1 | 10000.0 | 1.0 | 0.0 | C |  |  |
| 40435099999 | 2000-03-17T09:00:00 |  | 9 |  | 9.0 |  |  | SENTINEL_MISSING | SENTINEL_MISSING |

For a slightly longer guide, see [docs/first_output_guide.md](docs/first_output_guide.md). For the supported field registry, see [docs/supported_fields.md](docs/supported_fields.md).

## Core Reviewed Contribution vs Extended Coverage

Reviewer evaluation should center on the core JOSS contribution:
`noaa-spec clean`, deterministic cleaned CSV generation, documented
sentinel-to-null normalization, explicit NOAA QC preservation, stable decoded
column names, and checksum-backed reproduction of tracked fixtures. The core
field families are the retained source/control columns plus `WND`, `CIG`,
`VIS`, `TMP`, `DEW`, and `SLP`.

Additional NOAA families remain implemented, but they are not part of the
primary JOSS-reviewed claim. Treat them as secondary implementation inventory:
documented and tested, but not all backed by equal upstream-traceable real-data
fixtures. Use [docs/evidence_matrix.md](docs/evidence_matrix.md) and
[docs/supported_fields.md](docs/supported_fields.md) for the evidence boundary.

## Why A Shared Cleaning Tool?

A careful project-local script can reproduce the core cleaning mechanics for
one study. NOAA-Spec is useful when that interpretation needs to be shared: it
publishes stable decoded column names, explicit QC preservation,
checksum-backed regression behavior, and deterministic CSV serialization as a
versioned contract across users and studies instead of leaving each study to
carry a private preprocessing policy.

As a concrete illustration, a raw visibility token such as:

```text
VIS=999999,9,N,1
```

can be naively split into a numeric value of `999999`, which is not a real visibility distance. NOAA-Spec emits an empty `visibility_m`, preserves `visibility_quality_code=9`, and records the parser reason in `VIS__part1__qc_reason`.

Run the minimal comparison:

```bash
python3 examples/pandas_vs_noaa_spec.py
```

For a compact reviewer-facing table of selected real-row edge cases, see [docs/reviewer_cleaning_examples.md](docs/reviewer_cleaning_examples.md). For claim-to-evidence mapping, see [docs/evidence_matrix.md](docs/evidence_matrix.md).

## Relationship to Existing NOAA Tools

Existing NOAA parsers are useful for exposing NOAA records and parsed structures. NOAA-Spec does not claim those tools produce incorrect values. Its narrower contribution is an explicit cleaned-output policy for the documented fields this release supports: documented sentinels become nulls, NOAA QC codes stay in explicit columns, and decoded column names plus CSV serialization are deterministic for the same committed input.

## Local Install (Convenience Path)

The Docker commands above are the primary reviewer path. The local convenience
path works on macOS, Linux, and Windows, but the virtual-environment commands
are platform-specific. Python 3.11 or 3.12 is required.

macOS or Linux:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e .
```

Use `python3.11` instead of `python3.12` if that is your supported local
interpreter.

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e .
```

Use `py -3.11` instead of `py -3.12` if that is your supported local
interpreter. After activation, `python` refers to the virtual-environment
interpreter.

If the console script is not on `PATH`, use:

```bash
python -m noaa_spec.cli clean INPUT.csv OUTPUT.csv
```

## Reproducibility Fixtures

The tracked fixtures are small by design:

- `reproducibility/real_provenance_example/`: 20 rows from a recorded NOAA/NCEI Global Hourly source URL.
- `reproducibility/traceable_peru_il_2014_aa1_qc/`: one upstream-traceable row promoted from an edge-case example.
- `reproducibility/traceable_albion_ne_2014_calm_aa1/`: one upstream-traceable row promoted from an edge-case example.
- `reproducibility/minimal/`: five raw rows for the compact reviewer fixture.
- `reproducibility/minimal_second/`: eight raw rows covering additional encoded fields.
- `reproducibility/station_03041099999_aonach_mor/`, `reproducibility/station_01116099999_stokka/`, and `reproducibility/station_94368099999_hamilton_island/`: four-row curated station slices. Their exact upstream retrieval metadata was not retained.

These fixtures verify deterministic behavior for committed input/output pairs:
`clean(committed_input) = committed_output`, verified by checksums. The
`real_provenance_example/`, `traceable_peru_il_2014_aa1_qc/`, and
`traceable_albion_ne_2014_calm_aa1/` fixtures additionally record upstream NOAA
URLs, retrieval dates, and observed upstream checksums. The older curated
station fixtures do not replay upstream NOAA acquisition and do not claim
exhaustive NOAA coverage. Broader field behavior is supported by tests, not by a
claim that the small fixtures exercise every NOAA field. See [REPRODUCIBILITY.md](REPRODUCIBILITY.md),
[reproducibility/TRACEABLE_FIXTURES.md](reproducibility/TRACEABLE_FIXTURES.md),
[reproducibility/FIXTURE_PROVENANCE.md](reproducibility/FIXTURE_PROVENANCE.md),
and [docs/evidence_matrix.md](docs/evidence_matrix.md).

To run a bundled fixture manually after Docker or local install, use:

```bash
noaa-spec clean \
  reproducibility/minimal/station_raw.csv \
  /tmp/noaa-spec-minimal.csv
diff -u \
  reproducibility/minimal/station_cleaned_expected.csv \
  /tmp/noaa-spec-minimal.csv
sha256sum /tmp/noaa-spec-minimal.csv
```

For any other bundled fixture, replace `minimal` with the fixture directory
name, for example `minimal_second` or `real_provenance_example`. The `diff`
command should produce no output. The checksum should match the corresponding
`station_cleaned_expected.csv` entry in `reproducibility/checksums.sha256`.

## Run Tests

```bash
source .venv/bin/activate
python -m pip install -e .
python -m pip install pytest
python -m pytest tests -v
```
