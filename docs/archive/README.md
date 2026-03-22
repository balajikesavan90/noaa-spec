# Archive

This folder holds historical planning notes, cleanup audits, legacy materials, and archival references that are useful for provenance but are not part of the primary reviewer-facing documentation surface.

## Full station-report archive

The full tracked station-report example set is preserved locally at:

`data/archive/station_reports_full/docs/examples/station_reports/`

This archive is intentionally not tracked in git because the full set is bulky, repetitive, and unnecessary for routine review. The repository keeps a smaller curated subset under [docs/examples/stations](/home/balaji-kesavan/Documents/AI_Projects/noaa-climate-data/docs/examples/stations).

## Regenerating station reports

Full station reports can be regenerated from the pipeline by running the cleaning workflow with station-report outputs enabled, then collecting the generated station report directories under the archive path above.

## Future external archival options

If a durable external archive is needed later, the same station-report set can also be copied to an external drive, S3 bucket, or a publication archive such as Zenodo. That external publication step is optional and does not block normal repository use.
