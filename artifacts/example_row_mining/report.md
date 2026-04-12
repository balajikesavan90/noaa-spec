# NOAA ISD Example Row Mining Report

**Corpus root:** `/media/balaji-kesavan/LaCie/NOAA_Data`
**Output directory:** `/home/balaji-kesavan/Documents/AI_Projects/noaa-spec/artifacts/example_row_mining`
**Max per pattern:** 25

---

## Scan Statistics

| Metric | Value |
|--------|-------|
| Total files scanned | 500 |
| Total rows scanned | 72,968,685 |
| Skipped / bad files | 0 |

---

## Matches Per Pattern

| Pattern | Raw matches found | Rows in output (after diversity capping) |
|---------|:-----------------:|:-----------------------------------------:|
| `tmp_missing_sentinel` | 1,000 | 25 |
| `tmp_negative_sentinel` | 0 | 0 |
| `vis_missing_sentinel` | 1,000 | 25 |
| `wnd_calm_valid` | 0 | 0 |
| `wnd_missing_dir_valid_spd` | 1,000 | 25 |
| `wnd_fully_missing` | 1,000 | 25 |
| `aa1_valid_precip` | 1,000 | 25 |
| `aa1_missing_sentinel` | 1,000 | 25 |
| `mixed_validity` | 1,000 | 25 |
| `multi_family_informative` | 1,000 | 25 |

---

## Top Candidate Stations / Files Per Pattern

### `tmp_missing_sentinel`
- `72547299999`
- `63250099999`

### `tmp_negative_sentinel`
- *(no matches)*

### `vis_missing_sentinel`
- `72547299999`
- `63250099999`
- `72214904899`

### `wnd_calm_valid`
- *(no matches)*

### `wnd_missing_dir_valid_spd`
- `72547299999`
- `63250099999`

### `wnd_fully_missing`
- `72547299999`
- `63250099999`

### `aa1_valid_precip`
- `63250099999`

### `aa1_missing_sentinel`
- `55696099999`
- `72344154921`
- `72214904899`
- `46737399999`
- `72547299999`
- `63250099999`

### `mixed_validity`
- `72547299999`
- `63250099999`

### `multi_family_informative`
- `63250099999`

---

## Malformed / Skipped Files

- *(none)*

---

## Suggested Next Steps

1. **Review `summary.csv`** — check which patterns found matches.
2. **Open `all_matches.csv`** — sort by `pattern_name` or `station_id` to spot useful candidates.
3. **Use per-pattern CSVs** — each `pattern_<name>.csv` has already been diversity-sampled to ≤ `max_per_pattern` rows.
4. **Manually curate a reviewer fixture** — pick ~15–25 rows that collectively illustrate several distinct patterns.  Keep the fixture small and traceable (preserve `source_file_path` and `line_number` columns).
5. **Validate with the cleaner** — run curated rows through `noaa_spec.cleaning.clean_noaa_dataframe()` to confirm expected cleaning behaviour before committing them as fixtures.
