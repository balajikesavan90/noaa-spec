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
affiliations:
  - name: Independent Researcher
    index: 1
date: 2026
bibliography: paper.bib
---

# Abstract

NOAA-Spec is open-source software for deterministic cleaning of NOAA Integrated Surface Database (ISD) / Global Hourly observations. Its public `noaa-spec clean` command converts raw NOAA-style CSV rows into a reproducible observation-level CSV with sentinel-coded measurements normalized to nulls, NOAA quality-control codes preserved in explicit columns, and deterministic serialization. The contribution is a documented and test-backed NOAA-specific cleaning contract for supported NOAA field families, reducing sentinel leakage, quality-code loss, inconsistent packed-field interpretation, and nondeterministic cleaned CSVs in project-local preprocessing.

# Summary

NOAA ISD is widely used in weather and climate research, but raw rows require NOAA-specific interpretation before they can be compared across studies [@smith2011isd; @noaa_isd_docs]. Packed measurement fields combine values and quality codes; sentinel values encode missingness; and many fields have documented widths, scales, ranges, and quality semantics. NOAA-Spec packages those interpretation decisions into one Python library and CLI centered on the `noaa-spec clean` workflow.

The submitted software surface is intentionally narrow. NOAA-Spec reads raw NOAA ISD / Global Hourly CSV rows, applies deterministic field-interpretation rules for recognized fields, and writes a cleaned CSV whose serialization and column set are stable for a given input.

This tool provides a consistent and reproducible interpretation for the supported NOAA ISD CSV field families in this release, rather than asserting a single authoritative schema for all possible NOAA data.

# Statement of Need

Preprocessing NOAA ISD is not just a matter of loading a CSV into pandas. A token such as `TMP=+9999,9` contains both a numeric segment and a quality code [@noaa_isd_docs]. The numeric segment is not a large temperature; it is a sentinel-coded missing value. A naive parser can therefore leak sentinel values into analysis, while an overly simple cleaner can drop the quality code that explains the state of the measurement.

Project-local cleaning scripts also tend to diverge in small but consequential ways: one script may convert `+9999` to `NaN` but discard the associated QC flag, another may handle composite fields such as `VIS=010000,1,N,1` differently, and another may serialize rows in an order that is hard to checksum. These differences make downstream tables difficult to compare even when the same NOAA source rows were used, which works against reproducible data preparation practice in computational science [@peng2011reproducible].

NOAA-Spec addresses this specific gap by making these cleaning choices explicit and testable for the public CLI output. For `TMP=+9999,9`, it emits a null `temperature_c`, preserves `temperature_quality_code=9`, and records `TMP__qc_reason=SENTINEL_MISSING`. The output remains observation-level, so downstream researchers can apply their own scientific filters after starting from the same documented interpretation for supported fields.

# Why Not a Simple Script?

A naive script can parse `TMP=+9999,9` as numeric and produce `999.9` or `9999`. The problem is that a documented sentinel is interpreted as a real temperature, the quality code can be lost, and the missingness meaning is destroyed. NOAA-Spec emits a null `temperature_c`, preserves `temperature_quality_code=9`, and emits `TMP__qc_reason=SENTINEL_MISSING`.

A second common case is `VIS=999999,9,N,1`. Treating it as ordinary comma-separated text can turn the visibility sentinel into a real 999999 m distance, drop the distance quality code, or separate variability fields from the measurement they qualify. NOAA-Spec emits a null `visibility_m`, preserves `visibility_quality_code=9`, and keeps the visibility variability and variability-quality fields in explicit columns.

# Comparison With Existing Tools

Existing NOAA tools help users obtain or parse ISD data, but they do not by themselves define the specific cleaned-output decisions targeted here. The closest comparators are project-local preprocessing scripts, parsing-oriented tools such as the R package `isdparser` [@chamberlain_isdparser], and Python packages such as `isd` [@isd_python]. These tools are useful in their intended roles; NOAA-Spec is narrower than a general access or parsing package and focuses on one deterministic cleaning layer, documented decoded columns, and checksum-friendly output for the public `noaa-spec clean` workflow.

| Criterion | Naive pandas/raw CSV loading | Parsing-oriented tools (`isdparser` [@chamberlain_isdparser], `isd` [@isd_python]) | NOAA-Spec |
| --- | --- | --- | --- |
| Sentinel normalization for `TMP=+9999,9` | May remain a string token or be split into a numeric sentinel and suffix without NOAA semantics | Parsed structure can be exposed; downstream workflow chooses missing-value handling | Emits null `temperature_c`, preserves `temperature_quality_code=9`, and records `TMP__qc_reason=SENTINEL_MISSING` |
| Packed visibility `VIS=999999,9,N,1` | May treat `999999` as an ordinary distance or detach variability fields from the distance they qualify | Parsed structure can be exposed; downstream workflow chooses cleaning policy | Emits null `visibility_m`, preserves visibility QC, and keeps variability fields explicit |
| Stable decoded column names | Requires project-specific naming | Naming and analysis tables remain workflow-specific | Uses documented release names such as `temperature_c`, `precip_amount_1`, and `cloud_layer_base_height_m_1` for supported fields |
| QC preservation as output | Easy to drop while extracting measurement values | Available if retained by downstream code | Preserved in explicit columns such as `temperature_quality_code` and `precip_quality_code_1`, with `__qc_*` sidecars for parser decisions |
| Reproducible cleaned CSV | Requires project-specific serialization and checksums | Not the primary focus of parsing/access packages | Writes deterministic CSV output and includes checksum-backed fixtures and regression tests |

# Software Design

NOAA-Spec exposes a small public workflow:

1. read a raw NOAA ISD / Global Hourly CSV,
2. apply field-specific interpretation rules for recognized sentinels, scales, domains, ranges, and quality codes,
3. write a cleaned observation-level CSV with stable column names and deterministic serialization.

The public CLI is:

```bash
noaa-spec clean INPUT.csv OUTPUT.csv
```

The implementation separates the NOAA field-interpretation logic (`cleaning.py` and `constants.py`) from deterministic CSV writing (`deterministic_io.py`) and the command-line entry point (`cli.py`). The cleaned output is intentionally wide because it preserves decoded measurement fields, NOAA quality codes, validation sidecars, and row-level usability summaries rather than projecting a single analysis-ready subset. Optional domain-specific CSV views can be derived from the cleaned output for interpretation, but they are outside the core JOSS contribution and are not part of the primary reproducibility claim. The repository includes a versioned supported-field registry in `docs/supported_fields.md`, an interpretation guide in `docs/schema.md`, a first-output guide in `docs/first_output_guide.md`, and a rule-family provenance inventory in `docs/rule_provenance.md`.

# Reproducibility

The repository includes tracked raw inputs, tracked expected cleaned outputs, and checksum-backed verification under `reproducibility/`. The primary reviewer path runs the public CLI against tracked fixtures and verifies that each emitted CSV matches the expected SHA256 checksum. The strongest provenance example uses the first five data rows from the recorded NOAA/NCEI Global Hourly source URL for station `03041099999` in 2024 and records the observed upstream checksum. Smaller curated fixtures exercise additional field structures including precipitation, clouds, past weather, extreme temperature, and present weather while keeping the tracked data reviewer-checkable.

The fixtures are deliberately small and reviewer-checkable. They demonstrate deterministic behavior for committed input/output pairs; the automated tests provide broader regression coverage for sentinel handling, quality-code preservation, deterministic output, CLI behavior, and encoded field parsing. The fully traceable source example is documented in `reproducibility/REAL_PROVENANCE_EXAMPLE.md`; the older curated station slices are documented in `reproducibility/FIXTURE_PROVENANCE.md`. The paper does not claim exhaustive NOAA coverage or a general NOAA download workflow.

# Limitations

NOAA-Spec is NOAA-specific software. This JOSS submission covers the deterministic cleaning behavior exposed by the `noaa-spec clean` CLI for the supported field surface documented in the repository. It does not claim to be a data downloader, multi-station orchestration framework, release platform, or statistical analysis package.

# Acknowledgements

The author acknowledges NOAA National Centers for Environmental Information (NCEI) for maintaining the ISD dataset and documentation. Some development work used large language models as drafting assistance, but the software contribution described here is the committed implementation, tests, and documentation in the repository.

# References
