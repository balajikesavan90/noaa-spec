---
title: "NOAA-Spec: A Deterministic Canonical Interpretation Layer for NOAA Integrated Surface Database Observations"
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

NOAA-Spec is open-source software for deterministic interpretation of NOAA Integrated Surface Database (ISD) / Global Hourly observations. It standardizes sentinel handling, preserves NOAA quality-control semantics in dedicated columns, and emits a stable observation-level CSV so the same raw input always yields the same canonical output. The result is a reusable interpretation layer that downstream analyses can share instead of reimplementing NOAA decoding logic independently.

# Summary

NOAA ISD is widely used in weather and climate research, but its raw rows are not directly comparable without interpretation [@smith2011isd; @noaa_isd_docs]. Users must decode packed field encodings, sentinel values, and field-specific quality codes from technical documentation before they can produce comparable derived tables. In practice, that interpretation step is often reimplemented locally in scripts and notebooks. NOAA-Spec packages those repeated decoding and cleaning decisions into one reusable Python library and CLI.

Existing tools help users obtain NOAA records or parse ISD structures, and many projects maintain project-local preprocessing scripts. NOAA-Spec addresses the recurring step after parsing: turning raw NOAA rows into a stable interpreted representation for sentinels, QC semantics, and packed measurement fields before downstream analysis begins.

# Statement of Need

Preprocessing NOAA ISD is not only a file-reading task. Raw observations contain compact tokens such as `TMP=+9999,9`, where the numeric segment and quality code must be interpreted together [@noaa_isd_docs]. A token like `+9999,9` does not mean a very large temperature; it is a sentinel-coded missing value. When projects reimplement that interpretation locally, sentinel handling and QC preservation can drift, and derived tables stop being directly comparable.

Researchers comparing temperature and visibility across stations and years need the same interpretation of missingness, QC state, and packed field semantics each time an analysis is rerun. NOAA-Spec makes that layer explicit and reusable: it converts sentinel-coded measurements into nulls, preserves NOAA quality codes in dedicated columns, and emits a stable observation-level schema.

For example, the raw token `TMP=+9999,9` does not mean a very large temperature — it is a sentinel-coded missing value. NOAA-Spec emits `temperature_c=null` with `temperature_quality_code=9` and `TMP__qc_reason=SENTINEL_MISSING`, so the sentinel interpretation and QC context are preserved explicitly rather than discarded or silently reimplemented. Two downstream users can start from the same canonical subset — `STATION`, `DATE`, `temperature_c`, `temperature_quality_code`, `visibility_m`, `TMP__qc_reason` — and apply different later filters without reimplementing NOAA decoding. The canonical representation is intentionally wide because it is the source layer; users can begin from a subset of fields or from narrower derived views such as `metadata`, `wind`, `precipitation`, `clouds_visibility`, `pressure_temperature`, or `remarks`.

# Why This Matters In Practice

NOAA-Spec matters when multiple projects need the same interpreted NOAA input. A careful local preprocessing script can clean one dataset for one study, but the interpretation rules remain local and difficult to compare across projects.

An ad hoc workflow typically discards the QC context that explains why a value is missing. NOAA-Spec preserves that context deterministically — sentinel-coded missingness is distinguished from later quality-based exclusion — so downstream users start from the same decoded interpretation instead of silently diverging. The canonical dataset defines the reproducible interpretation contract, and optional derived views are usability projections from that canonical table.

# Comparison With Existing Tools

Existing NOAA tools help users obtain or parse ISD data, but they do not by themselves define a shared reusable interpretation contract for downstream analysis.

The closest comparators are project-local preprocessing scripts, parsing-oriented tools such as the R package `isdparser`, and Python packages such as `isd`. These tools help users read NOAA data structures or fetch source records. NOAA-Spec targets the next step: a reusable interpretation layer that fixes sentinel handling, preserves QC semantics in a stable schema, and gives different analyses the same canonical observation-level output contract.

An ad hoc pandas workflow can clean one dataset for one project, but it does not establish a shared interpretation contract that another project can rerun and compare against. NOAA-Spec's contribution is that reusable canonicalization layer.

| Capability | Ad hoc / local scripts | Parsing tools (`isdparser`, `isd`) | NOAA-Spec |
| --- | --- | --- | --- |
| Primary role | Project-specific preprocessing | Parsing or access | Canonical interpretation layer |
| Deterministic canonical CSV | Usually project-specific | Not the primary focus | Yes |
| Sentinel normalization + QC preservation | Varies, often implicit | Left to downstream workflows | Yes |
| Checksum-backed reproducibility fixture | Rare | Not the primary focus | Yes |

NOAA-Spec is aimed at that layer. Its contribution is deterministic NOAA-ISD-specific infrastructure that sits between raw parsed rows and downstream scientific analysis.

# Software Design

NOAA-Spec exposes a small public surface:

1. read raw NOAA ISD / Global Hourly rows,
2. apply deterministic field interpretation based on NOAA semantics,
3. write a canonical observation-level CSV with stable column names and preserved QC fields.

The public CLI is the `noaa-spec clean` command. The reviewer-visible example is intentionally bounded to the tracked reproducibility fixture so the JOSS claim matches the software surface that users and reviewers can run. The CLI also exposes optional derived views (`metadata`, `wind`, `precipitation`, `clouds_visibility`, `pressure_temperature`, `remarks`) as narrower projections from the canonical table.

# Reproducibility

The repository includes a tracked raw input, tracked expected canonical output, and checksum-backed verification under `reproducibility/`. For independent reviewer verification, the authoritative path is the Docker workflow documented in the repository. Reviewers can rerun the example and confirm that the emitted CSV matches the expected checksum. The included fixture is intentionally minimal (5 rows) and serves as a deterministic reproducibility proof; larger-scale processing is supported but not bundled in-repo. This supports the main software claim: NOAA-Spec makes NOAA-specific interpretation behavior deterministic and inspectable at the observation level.

# Limitations

NOAA-Spec is NOAA-specific software. The current contribution is the reusable canonical interpretation layer and its stable output contract.

# Acknowledgements

The author acknowledges NOAA National Centers for Environmental Information (NCEI) for maintaining the ISD dataset and documentation. Some development work used large language models as drafting assistance, but the software contribution described here is the committed implementation, tests, and documentation in the repository.

# References
All references cited in this manuscript are provided in `paper.bib` [@smith2011isd; @noaa_isd_docs].
