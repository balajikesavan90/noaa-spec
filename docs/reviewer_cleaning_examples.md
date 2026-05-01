# Cleaning Examples

This note summarizes selected NOAA ISD / Global Hourly edge cases used to show why `noaa-spec clean` is a specification-constrained cleaning step, not just CSV parsing. The examples are intentionally small and compact; the executable reproducibility claim remains the tracked raw/expected fixture workflow under `reproducibility/`.

These examples illustrate the cleaning policy. They do not claim that other NOAA tools fail on these rows; they show the documented interpretation NOAA-Spec makes explicit, testable, and checksum-stable for the supported fields in this release.

| Row | Station / timestamp | Raw token | Cleaning issue | NOAA-Spec interpretation |
| --- | --- | --- | --- | --- |
| R04 | `72547299999` / `1997-02-25T04:53:00` | `TMP=+9999,9` | `+9999` is a documented missing sentinel, not `+999.9 C`. | `temperature_c` is null, `temperature_quality_code=9` is preserved, and the parser reason is `SENTINEL_MISSING`. |
| R01 | `63250099999` / `1978-08-18T06:00:00` | `VIS=999999,9,N,9` | `999999` is a visibility sentinel, not a real 999999 m distance. | `visibility_m` is null while the visibility quality and variability fields remain explicit. |
| R06 | `72547299999` / `1997-02-01T11:40:00` | `WND=999,1,C,0000,1` | Direction `999` with type code `C` means calm wind, not missing wind. | Wind direction is null, type code `C` is retained, and `wind_speed_ms=0.0` is preserved as valid. |
| R03 | `63250099999` / `1978-11-02T15:00:00` | `WND=999,1,V,0031,1` | Direction `999` with type code `V` means variable wind direction, not automatically missing wind. | Wind direction is null, type code `V` is retained, and the valid wind speed is preserved. |

The same edge-case classes are exercised by tracked fixture outputs and regression tests where the corresponding fields appear. The point is the boundary of the core contribution: for the core mandatory families, `noaa-spec clean` turns documented field semantics into deterministic cleaned CSV output instead of leaving each downstream script to rediscover those decisions. Broader additional-family coverage remains implemented and tested, but secondary to the core JOSS-facing surface and not uniformly upstream-traceable.

The broader 18-row curated example appendix remains available under
`artifacts/curated_examples/` as optional context only. It is not part of the
Docker reviewer workflow, the checksum-backed reproducibility contract, or the
core validation path.
