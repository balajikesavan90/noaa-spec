"""Contract for the remarks publication domain dataset."""

DOMAIN_NAME = "remarks"

INPUT_FIELDS = (
    "station_id",
    "DATE",
    "remarks_text",
)

OUTPUT_SCHEMA = (
    ("station_id", "string"),
    ("DATE", "string"),
    ("remarks_text", "string"),
)

JOIN_KEYS = ("station_id", "DATE")

QUALITY_RULES = (
    "remarks_preserved_raw_semantics",
    "remarks_nullable",
)
