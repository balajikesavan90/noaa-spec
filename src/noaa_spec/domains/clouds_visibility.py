"""Contract for the clouds_visibility publication domain dataset."""

DOMAIN_NAME = "clouds_visibility"

INPUT_FIELDS = (
    "station_id",
    "DATE",
    "visibility_m",
    "ceiling_height_m",
    "cloud_total_coverage",
    "VIS__part1__qc_pass",
    "CIG__part1__qc_pass",
)

OUTPUT_SCHEMA = (
    ("station_id", "string"),
    ("DATE", "string"),
    ("visibility_m", "float64"),
    ("ceiling_height_m", "float64"),
    ("cloud_total_coverage", "float64"),
    ("VIS__part1__qc_pass", "boolean"),
    ("CIG__part1__qc_pass", "boolean"),
)

JOIN_KEYS = ("station_id", "DATE")

QUALITY_RULES = (
    "visibility_qc_pass_preserved",
    "ceiling_qc_pass_preserved",
    "cloud_fraction_domain_validated",
)
