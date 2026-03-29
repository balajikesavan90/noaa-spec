# Reviewer Guide

Use the root [README.md](../README.md) line-by-line.

The supported reviewer path for this submission is the Docker workflow in the root [README.md](../README.md).

That supported path requires a working Docker installation with daemon access; the `docker` CLI alone is not sufficient.

Python 3.12+ applies only to the optional local development path, not to the supported reviewer workflow.

The canonical reviewer example is under `reproducibility/minimal/`.

This submission validates the bounded, checksum-backed canonical cleaning example included in-repo.

The software contribution under review is a reusable NOAA-specific preprocessing package that makes ISD cleaning behavior easier to inspect, compare, and rerun than common local script workflows.

Broader publication artifacts (release bundles, manifests, domain publication outputs, and quality reports) are part of the broader documented system design but are not included as reviewer-verifiable artifacts in this submission.

NOAA-Spec should therefore be evaluated here as NOAA-specific preprocessing software with a bounded reproducibility example, not as a fully reviewer-reproduced end-to-end publication release system.

No archived release bundle is linked for this revision.
