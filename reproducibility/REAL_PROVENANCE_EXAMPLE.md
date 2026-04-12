# Real Provenance Example

This is the only upstream-traceable real-world provenance example in the repository. It is still intentionally small: it exists to give reviewers one traceable NOAA source example for `noaa-spec clean`, not to expand NOAA-Spec into a downloader or station-processing workflow.

## Source

| Field | Value |
| --- | --- |
| Station ID | `78724099999` |
| Station name | Choluteca, Honduras |
| Dataset | NOAA Integrated Surface Database (ISD) / Global Hourly |
| NOAA source URL | `https://www.ncei.noaa.gov/data/global-hourly/access/2001/78724099999.csv` |
| Retrieval date | 2026-04-12 |
| HTTP `Last-Modified` observed | 2020-03-17 13:48:14 GMT |
| Upstream source CSV checksum observed | `18eee5a542603cd803e9ebe49de467c2f68f3e510ef1a781d427c50e86ac9214` |
| Extracted fixture path | `reproducibility/real_provenance_example/station_raw.csv` |
| Cleaned expected output path | `reproducibility/real_provenance_example/station_cleaned_expected.csv` |
| Checksum manifest | `reproducibility/checksums.sha256` |

## Row Selection

The fixture contains the CSV header and the first 20 data rows from the NOAA source file:

```bash
curl -s https://www.ncei.noaa.gov/data/global-hourly/access/2001/78724099999.csv | head -n 21
```

This selection is deliberately mechanical and small. It avoids hand-picking unusual rows while keeping the reviewer fixture inspectable. The selected rows include supported wind (`WND`), precipitation (`AA1`), cloud (`GA1`/`GF1`), present-weather (`MW1`), pressure (`MA1`/`MD1`), temperature (`TMP`/`DEW`), and remarks (`REM`) fields where present in the source slice.

## Cleaning Command

```bash
noaa-spec clean \
  reproducibility/real_provenance_example/station_raw.csv \
  reproducibility/real_provenance_example/station_cleaned_expected.csv
```

The same fixture is included in `scripts/verify_reproducibility.sh`, which regenerates the cleaned output in a temporary directory and checks it against `reproducibility/checksums.sha256`.

## Limitations

- NOAA-Spec does not download NOAA data; the source URL, retrieval date, and observed upstream checksum are recorded so reviewers can independently inspect the source used for this example.
- The upstream NOAA URL is an external service. The recorded upstream checksum is evidence for the file as observed on 2026-04-12, not a guarantee that NOAA will never revise or move the file.
- This example demonstrates one traceable real-world source slice. It does not claim exhaustive NOAA field coverage.
