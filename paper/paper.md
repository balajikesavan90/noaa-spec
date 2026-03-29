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

NOAA-Spec is open-source software for deterministic interpretation of NOAA Integrated Surface Database (ISD) / Global Hourly observations. Its contribution is deliberately narrow: it provides a specification-constrained canonical contract for raw NOAA rows, rather than a general validation framework or workflow bundle. The software standardizes sentinel handling, preserves NOAA quality-control semantics in dedicated fields, emits a stable schema, and serializes a deterministic canonical representation so the same raw input yields the same observation-level CSV.

# Summary

NOAA ISD is widely used in weather and climate research, but its raw rows are not directly comparable without interpretation [@smith2011isd; @noaa_isd_docs]. Users must interpret field encodings, sentinel values, and field-specific quality codes from technical documentation before they can produce comparable derived tables. NOAA-Spec packages those interpretation decisions into one reusable Python library and CLI.

Existing tools help users obtain NOAA records or parse ISD structures, and many projects also maintain local preprocessing scripts. NOAA-Spec addresses a narrower recurring problem: once NOAA rows have been fetched or parsed, projects still need a stable interpretation layer for sentinels, QC semantics, and packed measurement fields before downstream analysis begins.

# Statement of Need

Preprocessing NOAA ISD is not only a file-reading task. Raw observations contain compact tokens such as `TMP=+9999,9`, where the numeric segment and quality code must be interpreted together [@noaa_isd_docs]. A token like `+9999,9` does not mean a very large temperature; it is a sentinel-coded missing value. If one project treats that token as missing and another project leaves it numeric or drops the quality code context, the resulting derived tables are no longer directly comparable.

Consider a researcher comparing temperature and visibility across stations and years. The researcher does not only need raw values read into a dataframe; they need the same interpretation of missingness, QC state, and packed field semantics each time the analysis is rerun. A project-local parser plus one-off cleaning script can produce a usable dataset once, but that interpretation layer often remains undocumented and difficult to compare across studies. NOAA-Spec addresses that narrower recurring problem by making the interpretation explicit and reusable. It converts sentinel-coded measurements into nulls, preserves NOAA quality codes in dedicated columns, and emits a stable observation-level schema. The result is a canonical, loss-preserving normalized representation intended to serve as a stable intermediate contract for downstream analyses.

In the tracked reproducibility fixture included with the repository, raw `TMP` values such as `+0180,1` become `temperature_c=18.0`, while `TMP=+9999,9` becomes `temperature_c=null` with `temperature_quality_code=9` and `TMP__qc_reason=SENTINEL_MISSING`. The practical benefit is comparability at the interpretation layer. When the same raw input yields the same canonical observation-level output, downstream analyses become easier to audit, compare, and reproduce because a key preprocessing step is no longer hidden inside project-local scripts. Most users will work with a subset of fields or a downstream domain-specific projection derived from the canonical representation. The contribution is the deterministic shared interpretation layer, not a claim that the full canonical table is the final analysis table for every use case.

# Reproducible Cross-Project Interpretation Scenario

Consider two researchers studying visibility and temperature over the same station set. Both begin from the same ISD raw rows, but one keeps sentinel-coded values in the table until late-stage filtering while the other converts them to nulls during import and drops the original QC context. Even if both use pandas correctly, their preprocessing rules are local and difficult to compare. Their downstream station-year tables may differ because missingness and quality semantics were handled differently before analysis began.

With NOAA-Spec, both researchers can start from the same canonical representation. Sentinel normalization is identical, temperature and visibility fields are emitted into the same stable columns, and NOAA QC semantics remain preserved in dedicated sidecar fields rather than disappearing inside notebook code. The resulting cleaned tables are reproducible at the interpretation layer and directly comparable before any project-specific modeling or aggregation begins.

For example, a station-year comparison workflow can begin from the subset `STATION`, `DATE`, `temperature_c`, `temperature_quality_code`, `visibility_m`, and `TMP__qc_reason`. One study may keep all non-null `temperature_c` rows, while another may additionally require `temperature_quality_code=1` before aggregation. NOAA-Spec does not remove that downstream choice; it ensures both studies start from the same deterministic interpretation of the raw NOAA rows and can make the stricter or looser filter explicitly.

# Comparison With Existing Tools

Existing NOAA tools help users obtain or parse ISD data, but they do not by themselves define a shared reusable interpretation contract for downstream analysis.

The closest comparators are project-local preprocessing scripts, parsing-oriented tools such as the R package `isdparser`, and Python packages such as `isd`. These tools help users read NOAA data structures or fetch source records, which is valuable. The gap NOAA-Spec targets is the next step: a reusable deterministic interpretation layer that fixes sentinel handling, preserves QC semantics in a stable schema, and gives different analyses the same canonical observation-level output contract.

| Capability / role | Ad hoc pandas or local preprocessing | `isdparser` / `isd` style parsing tools | NOAA-Spec |
| --- | --- | --- | --- |
| Primary role | Project-specific preprocessing | Parsing or access to NOAA structures | Canonical interpretation layer |
| Deterministic serialized canonical CSV | Usually project-specific | Not the primary focus | Yes |
| Explicit sentinel normalization policy | Usually local and implicit | Often left to project-specific workflows after parsing | Yes |
| Preservation of QC semantics in stable sidecar columns | Varies by project | Not the primary focus | Yes |
| Documented shared cleaning/interpretation contract | Usually local to one project | Not documented as the main contribution | Yes |
| Checksum-backed reproducibility fixture in-repo | Rare | Not the primary focus | Yes |
| Intended role as stable intermediate representation | Varies by project | Usually parsing-oriented input to later workflows | Yes |

NOAA-Spec is aimed at that layer. It does not claim novelty in generic validation, schema tooling, or workflow orchestration. Its contribution is deterministic NOAA-ISD-specific infrastructure that sits between raw parsed rows and downstream scientific analysis.

This is why NOAA-Spec is more than a disciplined local preprocessing script. A local script can clean one project's input once. NOAA-Spec instead fixes a shared, specification-constrained interpretation contract that multiple projects can reuse, rerun, audit, and compare. The software value is reusable, deterministic infrastructure for a recurring NOAA-ISD data-preparation problem, not a claim of novelty in generic validation or workflow orchestration.

# Software Design

NOAA-Spec exposes a small public surface:

1. read raw NOAA ISD / Global Hourly rows,
2. apply deterministic field interpretation based on NOAA semantics,
3. write a canonical observation-level CSV with stable column names and preserved QC fields.

The public CLI is the `noaa-spec clean` command. The reviewer-visible example is intentionally bounded to the tracked reproducibility fixture in the repository. This keeps the JOSS claim aligned with the software surface that users and reviewers can actually run. The canonical CSV is the reproducible source representation and stable intermediate contract; users will often work with selected columns from it or with downstream domain-specific projections derived from it.

# Reproducibility

The repository includes a tracked raw input, tracked expected canonical output, and checksum-backed verification under `reproducibility/`. Reviewers can rerun the example and confirm that the emitted CSV matches the expected checksum. This supports the main software claim: NOAA-Spec makes NOAA-specific interpretation behavior deterministic and inspectable at the observation level.

# Limitations

NOAA-Spec is NOAA-specific software, not a general-purpose data framework. The current contribution is the reusable canonical interpretation layer and its stable output contract. Broader batch orchestration, release architecture, and maintainer-only reporting code may exist in the repository, but those are outside the scoped JOSS claim of this submission.

# Acknowledgements

The author acknowledges NOAA National Centers for Environmental Information (NCEI) for maintaining the ISD dataset and documentation. Some development work used large language models as drafting assistance, but the software contribution described here is the committed implementation, tests, and documentation in the repository.

# References
All references cited in this manuscript are provided in `paper.bib` [@smith2011isd; @noaa_isd_docs].
