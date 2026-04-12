# Reproducibility

This document describes the tracked reproducibility checks for the JOSS-facing NOAA-Spec claim: deterministic cleaned CSV output from the public `noaa-spec clean` CLI.

## Docker Verification

```bash
docker build -f Dockerfile -t noaa-spec-review .
docker run --rm noaa-spec-review bash scripts/verify_reproducibility.sh
```

Expected result:

```text
PASS: minimal b48aba1b8a304451dc3874b963d76275bf79ad68c6f28d9190e0e636f2887597
PASS: minimal_second 223efb068df6d605646a1288feedf6621fa55b4c9074c027f6347cbe7ca2f30e
PASS: station_03041099999_aonach_mor 94913da579dc08b9c80a8a8f80d76cfb996ff9c28376aa2835b41161f0f7f134
PASS: station_01116099999_stokka 30e71fd2c6bed1fcecf5fd5922f96c47b11b63b4bacb4425ddbcbd078798e92d
PASS: station_94368099999_hamilton_island 9589ec020704b9d1fdd6e3675272badfd8e758302807f306ed8bbc9f91dc5a1a
PASS: reproducibility verification succeeded.
Output directory: /tmp/noaa-spec-reproducibility
```

The verification script runs each tracked raw fixture through the public CLI. The primary fixture command is:

```bash
python3 -m noaa_spec.cli clean reproducibility/minimal/station_raw.csv /tmp/noaa-spec-sample.csv
```

It then compares each generated CSV checksum to the tracked expected output.

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

## Additional Station Fixtures

These 4-row fixtures were selected from local real-station examples to broaden reviewer evidence across geography and reporting characteristics without adding large datasets. Their expected outputs were generated with the same `noaa-spec clean` CLI.

| Fixture | Station | Raw input SHA256 | Expected output SHA256 | Coverage note |
| --- | --- | --- | --- | --- |
| `station_03041099999_aonach_mor/` | Aonach Mor, UK | `30f7edbcd4dcc475727ee2c66187a251a6bf35d91bfc7f700aadd39d27cdbcf1` | `94913da579dc08b9c80a8a8f80d76cfb996ff9c28376aa2835b41161f0f7f134` | High-elevation UK station with mandatory fields, sentinel-heavy pressure/visibility cases, supplemental wind, and wave/sea side fields. |
| `station_01116099999_stokka/` | Stokka, Norway | `cc08ee8aeafe1494b4c8ab73a386a0f425c81db995b66ee0fe9284050fddfc17` | `30e71fd2c6bed1fcecf5fd5922f96c47b11b63b4bacb4425ddbcbd078798e92d` | Norwegian station with multiple cloud layers, present/past weather, runway/weather-extension fields, and station pressure. |
| `station_94368099999_hamilton_island/` | Hamilton Island Airport, Australia | `ccef9c7c69f8a11e4896277bc5aebb41e44570cf46028c3c567991d10d680851` | `9589ec020704b9d1fdd6e3675272badfd8e758302807f306ed8bbc9f91dc5a1a` | Australian airport station with precipitation, past/present weather, sea-level pressure, and additional weather-code fields. |

Run and verify one station fixture manually:

```bash
noaa-spec clean reproducibility/station_03041099999_aonach_mor/station_raw.csv /tmp/noaa-spec-aonach-mor.csv
sha256sum /tmp/noaa-spec-aonach-mor.csv
```

Expected checksum:

```text
94913da579dc08b9c80a8a8f80d76cfb996ff9c28376aa2835b41161f0f7f134
```

## Fixture Coverage Note

The primary fixture contains 5 raw rows. The secondary fixture contains 8 raw rows and includes additional NOAA field structures including precipitation (`AA1`-`AA4`), multiple cloud layers (`GA1`-`GA5`), past weather (`AY1`/`AY2`), extreme temperature (`KA1`/`KA2`), and present weather (`MW1`-`MW3`). The three additional station fixtures each contain 4 raw rows.

These fixtures are reproducibility checks, not a claim of exhaustive NOAA coverage. The automated tests exercise additional encoded cases for sentinel handling, QC preservation, deterministic output, CLI behavior, and field parsing.
