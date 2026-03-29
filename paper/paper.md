---
title: "NOAA-Spec: A Deterministic Cleaning Layer for NOAA Integrated Surface Database Observations"
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

NOAA-Spec is open-source software for deterministic cleaning of NOAA Integrated Surface Database (ISD) / Global Hourly observations. This package provides a reusable, deterministic canonical cleaning layer for NOAA ISD / Global Hourly data, standardizing sentinel handling, QC semantics, and output schema beyond existing parsing-focused tools. Its contribution is deliberately narrow: NOAA-Spec publishes a reusable observation-level cleaning contract for raw NOAA rows, rather than a general validation framework or workflow bundle. The software turns encoded field tokens into cleaned columns with explicit null semantics, preserved quality information, and deterministic serialization so the same raw input yields the same cleaned output.

# Summary

NOAA ISD is widely used in weather and climate research, but its raw rows are not analysis-ready [@smith2011isd; @noaa_isd_docs]. Users must interpret field encodings, sentinel values, and field-specific quality codes from technical documentation before they can produce comparable cleaned datasets. NOAA-Spec packages those decisions into one reusable Python library and CLI.

We are not aware of any existing reusable NOAA ISD cleaning layer that provides a stable observation-level contract. The software claim is therefore specific: NOAA-Spec offers a deterministic cleaning layer that different projects can rerun against the same NOAA input and obtain the same cleaned observation-level output.

# Statement of Need

Preprocessing NOAA ISD is not only a file-reading task. Raw observations contain compact tokens such as `TMP=+9999,9`, where the numeric segment and quality code must be interpreted together [@noaa_isd_docs]. A token like `+9999,9` does not mean a very large temperature; it is a sentinel-coded missing value. If one project treats that token as missing and another project leaves it numeric or drops the quality code context, the resulting cleaned datasets are no longer directly comparable.

NOAA-Spec addresses that gap by making those cleaning decisions explicit and reusable. It converts sentinel-coded measurements into nulls, preserves NOAA quality codes in dedicated columns, and emits a stable observation-level schema. In the tracked reproducibility fixture included with the repository, raw `TMP` values such as `+0180,1` become `temperature_c=18.0`, while `TMP=+9999,9` becomes `temperature_c=null` with `temperature_quality_code=9` and `TMP__qc_reason=SENTINEL_MISSING`. This resolves an ambiguity that appears in routine NOAA use but is often handled in unpublished project-specific code.

# Comparison With Existing Tools

Existing NOAA tools help users obtain or parse ISD data, but they do not provide a shared reusable cleaning contract.

The closest comparators are parsing-oriented tools such as the R package `isdparser` and Python packages such as `isd`, along with project-local NOAA parsing scripts. These tools help users read NOAA data structures or fetch source records, which is valuable. The gap is downstream of parsing: there is still no standardized reusable cleaning layer that fixes sentinel handling, preserves QC semantics in a stable schema, and gives different projects the same observation-level output contract.

NOAA-Spec is aimed at that missing layer. It does not claim novelty in generic validation, schema tooling, or workflow orchestration. Its contribution is a deterministic NOAA-ISD-specific cleaning surface that sits between raw parsed rows and downstream scientific analysis.

# Software Design

NOAA-Spec exposes a small public surface:

1. read raw NOAA ISD / Global Hourly rows,
2. apply deterministic field cleaning based on NOAA semantics,
3. write a cleaned observation-level CSV with stable column names and preserved QC fields.

The public CLI is the `noaa-spec clean` command. The reviewer-visible example is intentionally bounded to the tracked reproducibility fixture in the repository. This keeps the JOSS claim aligned with the software surface that users and reviewers can actually run.

# Reproducibility

The repository includes a tracked raw input, tracked expected cleaned output, and checksum-backed verification under `reproducibility/`. Reviewers can rerun the example and confirm that the emitted CSV matches the expected checksum. This supports the main software claim: NOAA-Spec makes NOAA-specific cleaning behavior deterministic and inspectable at the observation level.

# Limitations

NOAA-Spec is NOAA-specific software, not a general-purpose data framework. The current contribution is the reusable cleaning layer and its stable output contract. Broader batch orchestration, domain projection, and report-generation code may exist in the repository for maintainer workflows, but those are outside the scoped JOSS claim of this submission.

# Acknowledgements

The author acknowledges NOAA National Centers for Environmental Information (NCEI) for maintaining the ISD dataset and documentation. Some development work used large language models as drafting assistance, but the software contribution described here is the committed implementation, tests, and documentation in the repository.

# References
All references cited in this manuscript are provided in `paper.bib` [@smith2011isd; @noaa_isd_docs].
