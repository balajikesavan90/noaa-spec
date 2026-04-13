# NOAA-Spec

NOAA-Spec provides deterministic, specification-constrained cleaning of NOAA
Integrated Surface Database (ISD) / Global Hourly CSV observations by
normalizing documented sentinel values, preserving NOAA quality-code context,
and producing checksum-stable output for a defined supported field set. Its
public JOSS-facing workflow is:

```bash
noaa-spec clean INPUT.csv OUTPUT.csv
```

The command writes an observation-level cleaned CSV with documented NOAA
sentinels normalized to empty null cells, NOAA quality codes preserved in
explicit columns, and deterministic row/order serialization. The value is not
parsing alone; it is making a bounded set of NOAA cleaning decisions explicit,
testable, provenance-aware, and checksum-stable so downstream researchers can
start from the same documented interpretation rather than divergent local
scripts. NOAA-Spec does not download NOAA data, orchestrate station batches,
produce releases, or run analyses.

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

The Dockerfile uses the floating `python:3.12-slim` base image and upgrades bootstrap packaging tools during build. Treat it as a tested reviewer environment, not an immutable archived runtime. `requirements-review.txt` pins the Docker/reviewer path only; it is not required for standard local installation.

## Traceable Example

The only upstream-traceable provenance example is:

- Raw input: `reproducibility/real_provenance_example/station_raw.csv`
- Expected cleaned output: `reproducibility/real_provenance_example/station_cleaned_expected.csv`
- Checksums: `reproducibility/checksums.sha256`
- Provenance note: `reproducibility/REAL_PROVENANCE_EXAMPLE.md`

It uses the first 20 data rows from the NOAA/NCEI Global Hourly CSV for station
`78724099999`. This demonstrates one traceable source slice; it is not a claim
of broad NOAA coverage.

```text
https://www.ncei.noaa.gov/data/global-hourly/access/2001/78724099999.csv
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

Analysis-view snapshot from the tracked expected output:

| STATION | DATE | temperature_c | temperature_quality_code | visibility_m | visibility_quality_code | wind_speed_ms | wind_type_code | precip_amount_1 | precip_quality_code_1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 78724099999 | 2001-01-01T00:00:00 | 30.0 | 1 | 11265.0 | 1.0 | 8.7 | N |  |  |
| 78724099999 | 2001-01-01T15:00:00 | 29.3 | 1 | 28000.0 | 1.0 | 8.2 | N | 0.0 | 1.0 |

### How to read one row

For `2001-01-01T15:00:00`, read the decoded measurement columns first and ignore `__qc_*` sidecars on the first pass. `temperature_c=29.3` is the decoded air temperature and `temperature_quality_code=1` is the NOAA QC flag. `visibility_m=28000.0` is decoded visibility and `visibility_quality_code=1.0` is its QC flag. `wind_speed_ms=8.2` is decoded wind speed and `wind_speed_quality_code=1.0` is its QC flag. `precip_amount_1=0.0` is decoded precipitation for the first `AA1` precipitation group.

| column | meaning |
| --- | --- |
| `temperature_c` | decoded temperature |
| `temperature_quality_code` | NOAA QC flag for temperature |
| `visibility_m` | decoded visibility |
| `wind_speed_ms` | decoded wind speed |
| `precip_amount_1` | decoded precipitation amount |

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

## Why Not Pandas?

Pandas can load the CSV, but it does not know NOAA sentinel semantics. A raw visibility token such as:

```text
VIS=999999,9,N,1
```

can be naively split into a numeric value of `999999`, which is not a real visibility distance. NOAA-Spec emits an empty `visibility_m`, preserves `visibility_quality_code=9`, and records the parser reason in `VIS__part1__qc_reason`.

Run the minimal comparison:

```bash
python examples/pandas_vs_noaa_spec.py
```

For a compact reviewer-facing table of selected real-row edge cases, see [docs/reviewer_cleaning_examples.md](docs/reviewer_cleaning_examples.md). For the full curated mined-example artifact, see [artifacts/curated_examples/curated_examples.md](artifacts/curated_examples/curated_examples.md); for claim-to-evidence mapping, see [docs/evidence_matrix.md](docs/evidence_matrix.md).

## Why Not Existing NOAA Parsers?

Existing NOAA parsers are useful for exposing NOAA records and parsed structures. NOAA-Spec does not claim those tools produce incorrect values. Its narrower contribution is an explicit cleaned-output policy for the documented fields this release supports: documented sentinels become nulls, NOAA QC codes stay in explicit columns, and decoded column names plus CSV serialization are deterministic for the same committed input.

## Local Install (Convenience Path)

The Docker commands above are the primary reviewer path. For local use, Python
3.11 or 3.12 is required.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e .
```

Use `python3.11` instead of `python3.12` if that is your supported local interpreter.

If the console script is not on `PATH`, use:

```bash
python -m noaa_spec.cli clean INPUT.csv OUTPUT.csv
```

The positional output path is the canonical form. `noaa-spec clean INPUT.csv --out OUTPUT.csv` remains supported as a legacy alternate, but reviewer documentation uses `noaa-spec clean INPUT.csv OUTPUT.csv`.

## Reproducibility Fixtures

The tracked fixtures are small by design:

- `reproducibility/real_provenance_example/`: 20 rows from a recorded NOAA/NCEI Global Hourly source URL; this is the only upstream-traceable provenance example.
- `reproducibility/minimal/`: five raw rows for the compact reviewer fixture.
- `reproducibility/minimal_second/`: eight raw rows covering additional encoded fields.
- `reproducibility/station_03041099999_aonach_mor/`, `reproducibility/station_01116099999_stokka/`, and `reproducibility/station_94368099999_hamilton_island/`: four-row curated station slices. Their exact upstream retrieval metadata was not retained.

These fixtures verify deterministic behavior for committed input/output pairs:
`clean(committed_input) = committed_output`, verified by checksums. Only
`reproducibility/real_provenance_example/` additionally records the upstream NOAA
URL, retrieval date, and observed upstream checksum. The other curated fixtures
do not replay upstream NOAA acquisition and do not claim exhaustive NOAA
coverage. Broader field behavior is supported by tests, not by a claim that the
small fixtures exercise every NOAA field. See [REPRODUCIBILITY.md](REPRODUCIBILITY.md),
[reproducibility/FIXTURE_PROVENANCE.md](reproducibility/FIXTURE_PROVENANCE.md),
and [docs/evidence_matrix.md](docs/evidence_matrix.md).

## Optional, Outside JOSS Core

Reviewer evaluation should focus on `noaa-spec clean`. The CLI still includes
`noaa-spec split-domains` as a non-core convenience utility for splitting an
already-cleaned CSV into derived CSV views. It is not part of the JOSS
contribution, reviewer checksum workflow, or primary reproducibility claim.

## Run Tests

```bash
python -m pip install -e .
python -m pip install pytest
python -m pytest tests -v
```
