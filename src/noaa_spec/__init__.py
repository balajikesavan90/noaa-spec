"""NOAA-Spec package.

Public API surface (JOSS-reviewed):
    cleaning        — cleaned-output interpretation logic
    constants       — field rules, sentinels, QC definitions
    deterministic_io — checksummable CSV writer
    cli             — ``noaa-spec clean`` entry point
"""

__all__ = [
    "constants",
    "cleaning",
]

__version__ = "1.0.0"
