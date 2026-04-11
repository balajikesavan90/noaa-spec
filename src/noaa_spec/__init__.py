"""NOAA-Spec package.

Public API surface (JOSS-reviewed):
    cleaning        — canonical interpretation logic
    constants       — field rules, sentinels, QC definitions
    deterministic_io — checksummable CSV writer
    cli             — ``noaa-spec clean`` entry point
    noaa_client     — NOAA Global Hourly download helpers for single-station workflows
    domains/        — view definitions for domain-specific datasets

Modules under ``internal/`` support maintainer batch workflows and are
excluded from the installable distribution. They are not part of the
public API.
"""

__all__ = [
    "constants",
    "cleaning",
    "noaa_client",
]

__version__ = "1.0.0"
