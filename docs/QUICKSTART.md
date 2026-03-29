# Quickstart

The canonical quickstart is the root [README.md](../README.md).

Use the public CLI:

```bash
noaa-spec clean reproducibility/minimal/station_raw.csv /tmp/station_cleaned.csv
```

This command writes the full canonical cleaned representation for the sample input. Most downstream use will inspect a subset of columns rather than the entire schema at once.

This file intentionally does not define a second workflow.
