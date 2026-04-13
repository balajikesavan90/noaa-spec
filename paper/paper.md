---
title: "NOAA-Spec: A Deterministic Cleaning Tool for NOAA Integrated Surface Database Observations"
tags:
  - climate
  - meteorology
  - data-cleaning
  - reproducibility
  - scientific-software
authors:
  - name: Balaji Kesavan
    affiliation: 1
    orcid: 0009-0002-7714-518X
affiliations:
  - name: Independent Researcher
    index: 1
date: 2026-03-29
bibliography: paper.bib
---

# Abstract

NOAA-Spec is open-source software for deterministic, specification-constrained cleaning of NOAA Integrated Surface Database (ISD) / Global Hourly CSV observations. Its public `noaa-spec clean` command converts raw NOAA-style CSV rows into a deterministic observation-level CSV by normalizing documented sentinel values, preserving NOAA quality-code context, and producing checksum-stable output for a defined supported field set. The contribution is not parsing alone: it is a documented and test-backed NOAA-specific cleaning layer that makes a bounded set of cleaning decisions explicit, provenance-aware, and reproducible for downstream use.

# Summary

NOAA ISD is widely used in weather and climate research, but raw rows require NOAA-specific interpretation before cleaned observation tables can be compared across studies [@smith2011isd; @noaa_isd_docs]. Packed measurement fields combine values and quality codes; sentinel values encode missingness; and many fields have documented widths, scales, ranges, and quality semantics. NOAA-Spec packages a defined set of those interpretation decisions into one Python library and CLI centered on the `noaa-spec clean` workflow.

The submitted software surface is intentionally narrow. NOAA-Spec reads raw NOAA ISD / Global Hourly CSV rows, applies deterministic field-interpretation rules for recognized fields, and writes a cleaned CSV whose serialization and emitted columns are stable for a given input.

The executable evidence in the repository is also bounded: tracked fixtures demonstrate deterministic input/output reproduction, three small fixtures record upstream NOAA provenance, and tests exercise broader parser behavior. The paper does not assert exhaustive NOAA coverage or a single authoritative schema for all possible NOAA data.

# Statement of Need

Preprocessing NOAA ISD is not just a matter of loading a CSV into pandas. A token such as `TMP=+9999,9` contains both a numeric segment and a quality code [@noaa_isd_docs]. The numeric segment is not a large temperature; it is a sentinel-coded missing value. A naive parser can therefore leak sentinel values into analysis, while an overly simple cleaner can drop the quality code that explains the state of the measurement.

Project-local cleaning scripts also tend to diverge in small but consequential ways: one script may convert `+9999` to `NaN` but discard the associated QC flag, another may handle composite fields such as `VIS=010000,1,N,1` differently, and another may serialize rows in an order that is hard to checksum. These differences make downstream tables difficult to compare even when the same NOAA source rows were used, which works against reproducible data preparation practice in computational science [@peng2011reproducible].

NOAA-Spec addresses this gap by making these cleaning choices explicit and testable for the public CLI output. The output remains observation-level, so downstream researchers can apply their own scientific filters after starting from the same documented interpretation for the fields supported in this release.

The public claim centers on the core cleaned-output policy and the mandatory field families directly exercised by the reviewer workflow (`WND`, `CIG`, `VIS`, `TMP`, `DEW`, and `SLP`, with source/control columns retained). Additional implemented field families are included in the package and covered by tests and selected fixtures, but they are not presented as having identical upstream-traceable real-data support.

# Demonstrated Cleaning Cases

A compact reviewer-facing evidence set in `docs/reviewer_cleaning_examples.md`
summarizes selected NOAA ISD / Global Hourly edge cases. The executable
reproducibility claim remains the tracked fixture workflow in `reproducibility/`;
these examples explain why specification-aware cleaning matters and avoid making
claims about failures in other NOAA tools.

| NOAA token | Naive risk | NOAA-Spec cleaned-output behavior |
| --- | --- | --- |
| `TMP=+9999,9` | Treating `+9999` as `+999.9 C` or dropping the QC flag. | Emits null `temperature_c`, preserves `temperature_quality_code=9`, and records `TMP__qc_reason=SENTINEL_MISSING`. |
| `VIS=999999,9,N,9` | Treating `999999` as a real visibility distance. | Emits null `visibility_m` while preserving visibility QC and variability context. |
| `WND=999,1,C,0000,1` | Treating all `999` wind directions as missing observations. | Preserves calm wind context with type code `C` and valid `wind_speed_ms=0.0`. |
| `WND=999,1,V,0031,1` | Treating variable wind direction as ordinary missing wind. | Preserves type code `V` and the valid wind speed while leaving direction null. |
| `AA1=24,9999,1,9` | Nullifying or retaining the whole precipitation group as one undifferentiated value. | Preserves the period/QC context while nullifying only the sentinel amount. |

# Comparison With Existing Tools

Existing NOAA tools help users obtain or parse ISD data. NOAA-Spec makes a narrower policy choice: for supported fields it defines a deterministic cleaned-output layer with sentinel-to-null handling, QC preservation, documented decoded columns, and checksum-friendly output for the public `noaa-spec clean` workflow. The closest comparators are project-local preprocessing scripts and parsing-oriented tools such as the R package `isdparser` [@chamberlain_isdparser] and Python packages such as `isd` [@isd_python]. This comparison describes scope and output policy; it does not assert that those tools produce incorrect values.

| Criterion | Naive pandas/raw CSV loading | Parsing-oriented tools (`isdparser` [@chamberlain_isdparser], `isd` [@isd_python]) | NOAA-Spec |
| --- | --- | --- | --- |
| Sentinel normalization for `TMP=+9999,9` | Must be implemented by the local workflow after loading | Parsed structure can be exposed; downstream workflow chooses missing-value handling | Emits null `temperature_c`, preserves `temperature_quality_code=9`, and records `TMP__qc_reason=SENTINEL_MISSING` |
| Packed visibility `VIS=999999,9,N,1` | Must be implemented by the local workflow after loading | Parsed structure can be exposed; downstream workflow chooses cleaning policy | Emits null `visibility_m`, preserves visibility QC, and keeps variability fields explicit |
| Stable decoded column names | Requires project-specific naming | Parsed names and analysis tables depend on the downstream workflow | Uses documented release names such as `temperature_c`, `precip_amount_1`, and `cloud_layer_base_height_m_1` for supported fields |
| QC preservation as output | Easy to drop while extracting measurement values | Available if retained by downstream code | Preserved in explicit columns such as `temperature_quality_code` and `precip_quality_code_1`, with `__qc_*` sidecars for parser decisions |
| Reproducible cleaned CSV | Requires project-specific serialization and checksums | Downstream workflow chooses serialization policy | Writes deterministic CSV output and includes checksum-backed fixtures and regression tests |

# Software Design

NOAA-Spec exposes a small public workflow:

1. read a raw NOAA ISD / Global Hourly CSV,
2. apply field-specific interpretation rules for recognized sentinels, scales, domains, ranges, and quality codes,
3. write a cleaned observation-level CSV with stable column names and deterministic serialization.

The public CLI is:

```bash
noaa-spec clean INPUT.csv OUTPUT.csv
```

The implementation separates NOAA field interpretation (`cleaning.py` and `constants.py`) from deterministic CSV writing (`deterministic_io.py`) and the command-line entry point (`cli.py`). The cleaned output is intentionally wide because it preserves decoded measurement fields, NOAA quality codes, validation sidecars, and row-level usability summaries rather than projecting a single analysis-ready subset. This is a tradeoff for explicit QC retention and deterministic field exposure; `docs/first_output_guide.md` provides the recommended compact first view. Optional domain-specific CSV views can be derived from the cleaned output, but they are outside the core JOSS contribution and are not part of the primary reproducibility claim. The repository includes a supported-field registry in `docs/supported_fields.md`, an interpretation guide in `docs/schema.md`, and a rule-family provenance inventory in `docs/rule_provenance.md`.

# Reproducibility

The repository includes tracked raw inputs, tracked expected cleaned outputs, and checksum-backed verification under `reproducibility/`. The primary reviewer claim is reproducible from the repository alone: for committed fixtures, `clean(committed_input) = committed_output`, and the emitted CSVs are verified against tracked SHA256 checksums. This is a deterministic cleaning claim for committed input/output pairs, not a claim that every fixture can replay upstream NOAA retrieval.

Three upstream-traceable fixtures additionally record NOAA/NCEI source URLs, retrieval dates, observed upstream checksums, and exact extraction commands: the original 20-row source slice for station `78724099999` in 2001 and two one-row 2014 slices promoted from reviewer edge cases. Those traceable slices include the mandatory families plus selected precipitation, cloud, pressure, temperature-summary, wind-gust, remarks, and EQD fields where present in the source rows. Older curated station fixtures exercise additional field structures while keeping the tracked data reviewer-checkable; their exact upstream retrieval metadata was not retained. The traceable source fixtures are documented in `reproducibility/TRACEABLE_FIXTURES.md`, and the older curated station slices are documented in `reproducibility/FIXTURE_PROVENANCE.md`. The paper does not claim exhaustive NOAA coverage or a general NOAA download workflow.

# Limitations

NOAA-Spec is NOAA-specific software. This JOSS submission covers the deterministic cleaning behavior exposed by the `noaa-spec clean` CLI for the documented fields supported in this release. It does not claim to be a data downloader, multi-station orchestration framework, release platform, domain dataset publishing system, or statistical analysis package.

# Acknowledgements

The author acknowledges NOAA National Centers for Environmental Information (NCEI) for maintaining the ISD dataset and documentation. Some development work used large language models as drafting assistance, but the software contribution described here is the committed implementation, tests, and documentation in the repository.

# References
