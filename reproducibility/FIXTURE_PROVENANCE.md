# Fixture Provenance

This document records provenance for the small tracked fixtures used by the JOSS-facing reproducibility checks. These files are curated, repository-committed slices. They are intended to make `noaa-spec clean` deterministic and inspectable for reviewers; they are not presented as an end-to-end replay of upstream NOAA acquisition.

NOAA Global Hourly / ISD data are public NOAA/NCEI data. The repository does not include a downloader and does not reproduce the upstream fetch step for these fixtures.

| Fixture | Station ID | Source dataset | Source/file identifier | Date accessed / retrieved | Row selection | Demonstrates | Upstream fetch reproduced in repo? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `reproducibility/minimal/` | `40435099999` | NOAA ISD / Global Hourly station CSV-style rows | Station/year source file not retained in repository metadata | Not recorded before curation | Five rows selected as the primary compact reviewer fixture | Sentinel normalization for mandatory fields, QC preservation, packed mandatory-field expansion, remarks parsing, clouds, pressure, and row usability sidecars | No |
| `reproducibility/minimal_second/` | `78724099999` | NOAA ISD / Global Hourly station CSV-style rows | Station/year source file not retained in repository metadata | Not recorded before curation | Eight rows selected to broaden encoded-field coverage while staying small | Precipitation repeats, cloud repeats, past/present weather, extreme temperature, sea-surface/marine fields, pressure, and supplemental wind | No |
| `reproducibility/station_03041099999_aonach_mor/` | `03041099999` | NOAA ISD / Global Hourly station CSV-style rows | Station `03041099999`; exact NOAA access URL/year-file metadata not retained | Not recorded before curation | Four rows curated from local real-station examples | High-elevation UK station with mandatory fields, pressure/visibility sentinel cases, supplemental wind, and marine/wave side fields | No |
| `reproducibility/station_01116099999_stokka/` | `01116099999` | NOAA ISD / Global Hourly station CSV-style rows | Station `01116099999`; exact NOAA access URL/year-file metadata not retained | Not recorded before curation | Four rows curated from local real-station examples | Norwegian station with multiple cloud layers, present/past weather, runway/weather-extension fields, station pressure, and supplemental wind | No |
| `reproducibility/station_94368099999_hamilton_island/` | `94368099999` | NOAA ISD / Global Hourly station CSV-style rows | Station `94368099999`; exact NOAA access URL/year-file metadata not retained | Not recorded before curation | Four rows curated from local real-station examples | Australian airport station with precipitation, present/past weather, sea-level pressure, and additional weather-code fields | No |

## What the Fixtures Support

- They support deterministic reproduction of committed input/output pairs through `noaa-spec clean`.
- They support reviewer inspection of representative sentinel, QC, packed-field, and serialization behavior.
- They do not establish exhaustive NOAA field coverage.
- They do not prove that an upstream NOAA fetch will reproduce byte-identical fixture files, because the upstream retrieval step and access dates were not recorded when the slices were created.
