"""Contract for the wind publication domain dataset."""

DOMAIN_NAME = "wind"

INPUT_FIELDS = (
    "station_id",
    "DATE",
    "wind_speed_ms",
    "wind_direction_deg",
    "wind_gust_ms",
    "wind_type_code",
    "WND__part4__qc_pass",
)

OUTPUT_SCHEMA = (
    ("station_id", "string"),
    ("DATE", "string"),
    ("wind_speed_ms", "float64"),
    ("wind_direction_deg", "float64"),
    ("wind_gust_ms", "float64"),
    ("wind_type_code", "string"),
    ("WND__part4__qc_pass", "boolean"),
)

JOIN_KEYS = ("station_id", "DATE")

QUALITY_RULES = (
    "wind_qc_pass_preserved",
    "wind_direction_domain_validated",
    "wind_speed_no_sentinel",
)
