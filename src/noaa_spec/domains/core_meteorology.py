"""Contract for the core_meteorology publication domain dataset."""

DOMAIN_NAME = "core_meteorology"

INPUT_FIELDS = (
    "station_id",
    "DATE",
    "YEAR",
    "LATITUDE",
    "LONGITUDE",
    "ELEVATION",
    "REPORT_TYPE",
    "CALL_SIGN",
)

OUTPUT_SCHEMA = (
    ("station_id", "string"),
    ("DATE", "string"),
    ("YEAR", "int64"),
    ("LATITUDE", "float64"),
    ("LONGITUDE", "float64"),
    ("ELEVATION", "float64"),
    ("REPORT_TYPE", "string"),
    ("CALL_SIGN", "string"),
)

JOIN_KEYS = ("station_id", "DATE")

QUALITY_RULES = (
    "station_id_required",
    "date_required",
    "location_fields_nullable_not_sentinel",
)
