"""NOAA-Spec package.

Public API surface (JOSS-reviewed):
    cleaning        — canonical interpretation logic
    constants       — field rules, sentinels, QC definitions
    deterministic_io — checksummable CSV writer
    cli             — ``noaa-spec clean`` entry point
    domains/        — view definitions for domain-specific datasets

Other modules (pipeline, cleaning_runner, internal/, research_reports,
noaa_client) support maintainer batch workflows and are not part of
the public API.
"""

__all__ = [
    "constants",
    "cleaning",
]

__version__ = "1.0.0"
