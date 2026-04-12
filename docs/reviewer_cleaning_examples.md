# Reviewer Cleaning Examples

This note summarizes curated NOAA ISD / Global Hourly rows selected to show why `noaa-spec clean` is a specification-constrained cleaning step, not just CSV parsing. The mined set contains 15 examples across 6 stations and covers all 8 edge-case patterns found in the local sample used for curation.

These examples are evidence for the cleaning policy. They do not claim that other NOAA tools fail on these rows; they show the documented interpretation NOAA-Spec makes explicit, testable, and checksum-stable.

| Row | Station / timestamp | Raw token | Cleaning issue | NOAA-Spec interpretation |
| --- | --- | --- | --- | --- |
| R04 | `72547299999` / `1997-02-25T04:53:00` | `TMP=+9999,9` | `+9999` is a documented missing sentinel, not `+999.9 C`. | `temperature_c` is null, `temperature_quality_code=9` is preserved, and the parser reason is `SENTINEL_MISSING`. |
| R01 | `63250099999` / `1978-08-18T06:00:00` | `VIS=999999,9,N,9` | `999999` is a visibility sentinel, not a real 999999 m distance. | `visibility_m` is null while the visibility quality and variability fields remain explicit. |
| R06 | `72547299999` / `1997-02-01T11:40:00` | `WND=999,1,C,0000,1` | Direction `999` with type code `C` means calm wind, not missing wind. | Wind direction is null, type code `C` is retained, and `wind_speed_ms=0.0` is preserved as valid. |
| R03 | `63250099999` / `1978-11-02T15:00:00` | `WND=999,1,V,0031,1` | Direction `999` with type code `V` means variable wind direction, not automatically missing wind. | Wind direction is null, type code `V` is retained, and the valid wind speed is preserved. |
| R08 | `72214904899` / `2014-02-21T11:55:00` | `AA1=24,9999,1,9` | The precipitation period is present while the amount is the `9999` sentinel. | The period field remains available, the amount is nullified, and the amount QC code is preserved. |

The selected rows also include fully sentineled core observations, valid zero precipitation (`AA1=06,0000,9,1`), estimated-quality-code rows, and examples spanning 1975 through 2014. The point is the boundary of the core contribution: for supported NOAA field families, `noaa-spec clean` turns documented field semantics into deterministic cleaned CSV output instead of leaving each downstream script to rediscover those decisions.
