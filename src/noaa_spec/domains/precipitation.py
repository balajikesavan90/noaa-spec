"""Contract for the precipitation publication domain dataset."""

DOMAIN_NAME = "precipitation"

INPUT_FIELDS = (
    "station_id",
    "DATE",
    "precip_amount_1",
    "precip_period_hours_1",
    "snow_accum_depth_cm_1",
    "AA1__part2__qc_pass",
)

OUTPUT_SCHEMA = (
    ("station_id", "string"),
    ("DATE", "string"),
    ("precip_amount_1", "float64"),
    ("precip_period_hours_1", "float64"),
    ("snow_accum_depth_cm_1", "float64"),
    ("AA1__part2__qc_pass", "boolean"),
)

JOIN_KEYS = ("station_id", "DATE")

QUALITY_RULES = (
    "precip_qc_pass_preserved",
    "precip_amount_no_sentinel",
    "precip_period_hours_domain_validated",
)
