"""Contract for the pressure_temperature publication domain dataset."""

DOMAIN_NAME = "pressure_temperature"

INPUT_FIELDS = (
    "station_id",
    "DATE",
    "temperature_c",
    "dew_point_c",
    "station_pressure_hpa",
    "sea_level_pressure_hpa",
    "altimeter_setting_hpa",
    "TMP__qc_pass",
    "SLP__qc_pass",
)

OUTPUT_SCHEMA = (
    ("station_id", "string"),
    ("DATE", "string"),
    ("temperature_c", "float64"),
    ("dew_point_c", "float64"),
    ("station_pressure_hpa", "float64"),
    ("sea_level_pressure_hpa", "float64"),
    ("altimeter_setting_hpa", "float64"),
    ("TMP__qc_pass", "boolean"),
    ("SLP__qc_pass", "boolean"),
)

JOIN_KEYS = ("station_id", "DATE")

QUALITY_RULES = (
    "temperature_qc_pass_preserved",
    "pressure_qc_pass_preserved",
    "pressure_fields_no_sentinel",
)
