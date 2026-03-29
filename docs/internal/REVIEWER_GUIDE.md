# Reviewer Guide

Use [reproducibility/README.md](../../reproducibility/README.md) for the complete reviewer workflow. The root [README.md](../../README.md) documents ordinary CLI usage, not the clean-environment reviewer path.

That supported path requires a working Docker installation with daemon access; the `docker` CLI alone is not sufficient.

Python 3.12+ applies only to optional local development, not to the supported reviewer workflow.

The canonical reviewer example is under `reproducibility/minimal/`.

This submission validates the bounded, checksum-backed canonical cleaning example included in-repo.

The software contribution under review is the narrow public cleaning surface: the `noaa-spec clean` CLI, the deterministic observation-level cleaning contract, and the bundled reproducibility fixture.

The failure mode it addresses is silent divergence in preprocessing: different local scripts can interpret sentinel values, field encodings, or quality-code semantics differently while starting from the same raw ISD records.

The reviewer task is intentionally narrow:

1. Build the Docker image.
2. Run the reproducibility verification script.
3. Confirm that the produced CSV matches the tracked expected output and checksum.

That bounded example is enough to evaluate the public claim: the same raw NOAA input produces the same cleaned observation-level output with stable handling of sentinels and preserved QC semantics.

Broader publication artifacts, domain outputs, manifests, tests beyond this path, and maintainer-facing quality reports are not part of the primary reviewer proof for this submission.

NOAA-Spec should therefore be evaluated here as a deterministic NOAA-specific cleaning layer with a bounded reproducibility example, not as a fully reviewer-reproduced end-to-end release workflow.
