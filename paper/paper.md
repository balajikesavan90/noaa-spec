---
title: "NOAA-Spec: A Deterministic Canonicalization Layer for NOAA Integrated Surface Database Observations"
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

NOAA-Spec is open-source software for deterministic canonicalization of NOAA Integrated Surface Database (ISD) / Global Hourly observations. Its public `noaa-spec clean` command converts raw NOAA-style CSV rows into a stable observation-level CSV with sentinel-coded measurements normalized to nulls, NOAA quality-control codes preserved in explicit columns, and deterministic serialization. The contribution is a reusable NOAA-specific interpretation layer that downstream analyses can share instead of reimplementing the same cleaning decisions in project-local scripts.

# Summary

NOAA ISD is widely used in weather and climate research, but raw rows require NOAA-specific interpretation before they can be compared across studies [@smith2011isd; @noaa_isd_docs]. Packed measurement fields combine values and quality codes; sentinel values encode missingness; and many fields have documented widths, scales, ranges, and quality semantics. NOAA-Spec packages those interpretation decisions into one Python library and CLI centered on the `noaa-spec clean` workflow.

The submitted software surface is intentionally narrow. NOAA-Spec reads raw NOAA ISD / Global Hourly CSV rows, applies deterministic canonicalization rules, and writes a canonical CSV whose schema and serialization are stable for a given input.

# Statement of Need

Preprocessing NOAA ISD is not just a matter of loading a CSV into pandas. A token such as `TMP=+9999,9` contains both a numeric segment and a quality code [@noaa_isd_docs]. The numeric segment is not a large temperature; it is a sentinel-coded missing value. A naive parser can therefore leak sentinel values into analysis, while an overly simple cleaner can drop the quality code that explains the state of the measurement.

Project-local cleaning scripts also tend to diverge in small but consequential ways: one script may convert `+9999` to `NaN` but discard the associated QC flag, another may rename columns differently, and another may serialize rows in an order that is hard to checksum. These differences make downstream tables difficult to compare even when the same NOAA source rows were used.

NOAA-Spec addresses this specific gap. For `TMP=+9999,9`, it emits a null `temperature_c`, preserves `temperature_quality_code=9`, and records `TMP__qc_reason=SENTINEL_MISSING`. The output remains observation-level, so downstream researchers can apply their own scientific filters after starting from the same canonical interpretation.

# Comparison With Existing Tools

Existing NOAA tools help users obtain or parse ISD data, but they do not by themselves define a shared canonical cleaned CSV for downstream analysis.

The closest comparators are project-local preprocessing scripts, parsing-oriented tools such as the R package `isdparser` [@chamberlain_isdparser], and Python packages such as `isd` [@isd_python]. These tools help users read NOAA structures or fetch source records. NOAA-Spec targets the next step: deterministic canonicalization with sentinel normalization, QC preservation, stable schema behavior, and checksum-backed reproducibility.

| Capability | Ad hoc / local scripts | Parsing tools (`isdparser` [@chamberlain_isdparser], `isd` [@isd_python]) | NOAA-Spec |
| --- | --- | --- | --- |
| Primary role | Project-specific preprocessing | Parsing or access | Canonicalization layer |
| Sentinel normalization | Varies | Left to downstream workflows | Yes |
| QC preservation in stable columns | Varies, often implicit | Left to downstream workflows | Yes |
| Deterministic canonical CSV | Usually project-specific | Not the primary focus | Yes |
| Checksum-backed reproducibility fixture | Rare | Not the primary focus | Yes |

# Software Design

NOAA-Spec exposes a small public workflow:

1. read a raw NOAA ISD / Global Hourly CSV,
2. apply field-specific interpretation rules for sentinels, scales, domains, ranges, and quality codes,
3. write a canonical observation-level CSV with stable column names and deterministic serialization.

The public CLI is:

```bash
noaa-spec clean INPUT.csv OUTPUT.csv
```

The implementation separates the canonicalization logic (`cleaning.py` and `constants.py`) from deterministic CSV writing (`deterministic_io.py`) and the command-line entry point (`cli.py`). The canonical output is intentionally wide because it preserves decoded measurement fields and QC context rather than projecting a single analysis-ready subset.

# Reproducibility

The repository includes tracked raw inputs, tracked expected canonical outputs, and checksum-backed verification under `reproducibility/`. The primary reviewer path runs the public CLI against `reproducibility/minimal/station_raw.csv` and verifies that the emitted CSV matches the expected SHA256 checksum. A second small fixture exercises additional field structures including precipitation, clouds, past weather, extreme temperature, and present weather.

The fixtures are deliberately small and reviewer-checkable. They demonstrate deterministic behavior for committed input/output pairs; the automated tests provide broader regression coverage for sentinel handling, quality-code preservation, deterministic output, CLI behavior, and encoded field parsing. The paper does not claim that the fixtures are exhaustive NOAA coverage.

# Limitations

NOAA-Spec is NOAA-specific software. This JOSS submission covers the deterministic canonicalization layer and the `noaa-spec clean` CLI. It does not claim to be a data-download system, multi-station orchestration framework, or statistical analysis package.

# Acknowledgements

The author acknowledges NOAA National Centers for Environmental Information (NCEI) for maintaining the ISD dataset and documentation. Some development work used large language models as drafting assistance, but the software contribution described here is the committed implementation, tests, and documentation in the repository.

# References
