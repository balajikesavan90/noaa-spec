# Real Provenance Example

This is the strongest real-world provenance example in the repository. It is still intentionally small: it exists to give reviewers one traceable NOAA source example for `noaa-spec clean`, not to expand NOAA-Spec into a downloader or station-processing workflow.

## Source

| Field | Value |
| --- | --- |
| Station ID | `03041099999` |
| Station name | Aonach Mor, UK |
| Dataset | NOAA Integrated Surface Database (ISD) / Global Hourly |
| NOAA source URL | `https://www.ncei.noaa.gov/data/global-hourly/access/2024/03041099999.csv` |
| Retrieval date | 2026-04-12 |
| HTTP `Last-Modified` observed | 2025-02-27 22:27:07 GMT |
| Extracted fixture path | `reproducibility/real_provenance_example/station_raw.csv` |
| Cleaned expected output path | `reproducibility/real_provenance_example/station_cleaned_expected.csv` |
| Checksum manifest | `reproducibility/checksums.sha256` |

## Row Selection

The fixture contains the CSV header and the first five data rows from the NOAA source file:

```bash
curl -s https://www.ncei.noaa.gov/data/global-hourly/access/2024/03041099999.csv | head -n 6
```

This selection is deliberately mechanical and small. It avoids hand-picking unusual rows while keeping the reviewer fixture inspectable.

## Cleaning Command

```bash
noaa-spec clean \
  reproducibility/real_provenance_example/station_raw.csv \
  reproducibility/real_provenance_example/station_cleaned_expected.csv
```

The same fixture is included in `scripts/verify_reproducibility.sh`, which regenerates the cleaned output in a temporary directory and checks it against `reproducibility/checksums.sha256`.

## Limitations

- NOAA-Spec does not download NOAA data; the source URL and observed upstream checksum are recorded so reviewers can independently inspect the source used for this example.
- The upstream NOAA URL is an external service. The recorded upstream checksum is evidence for the file as observed on 2026-04-12, not a guarantee that NOAA will never revise or move the file.
- This example demonstrates one traceable real-world source slice. It does not claim exhaustive NOAA field coverage.
