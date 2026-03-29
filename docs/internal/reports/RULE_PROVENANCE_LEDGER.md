# INTERNAL DEVELOPMENT RECORD — NOT REVIEWER EVIDENCE

# RULE_PROVENANCE_LEDGER Summary

- Total enforced rules inventoried: **4926**

## Counts by `source_class`
- `defensive_sanity_check`: 7
- `documented_exact`: 971
- `documented_inferred`: 3937
- `implementation_only`: 7
- `legacy_behavior`: 4

## Counts by `doc_support_status`
- `supported_exact`: 971
- `supported_partial`: 1969
- `unknown`: 1986

## Counts by `strictness_vs_doc`
- `equal`: 2384
- `looser`: 155
- `not_comparable`: 2208
- `stricter`: 179
- `needs_manual_review` rows: 3886

## Top Contributing Files
- `src/noaa_spec/cleaning.py`: 4924
- `src/noaa_spec/constants.py`: 2

## Top Contributing Functions
- `_expand_parsed`: 4060
- `clean_value_quality`: 845
- `clean_noaa_dataframe`: 4
- `_record_structure_error`: 4
- `_validate_control_header`: 2
- `_is_valid_eqd_parameter_code`: 2
- `get_field_rule`: 2
- `_annotate_control_field_qc_flags`: 1
- `_is_crn_missing_qc`: 1
- `_normalize_missing`: 1
- `_cleanup_rule_missing_text`: 1
- `_is_missing_numeric`: 1

## Highest-Risk Unsupported / Strictness-Divergent Rules
- `RPL::AA3::domain::90ae3db04dce74` | `AA3` | `domain` | doc=`supported_partial` strictness=`looser` | AA3 part 3 allowed domain values are enumerated.
- `RPL::AA4::domain::a261955541ccc2` | `AA4` | `domain` | doc=`supported_partial` strictness=`looser` | AA4 part 3 allowed domain values are enumerated.
- `RPL::AB::allowed_quality::b9ab519e3c873b` | `AB` | `allowed_quality` | doc=`supported_partial` strictness=`looser` | AB part 3 quality codes constrained to allowed set.
- `RPL::AC::allowed_quality::c62ff3d33aa2ec` | `AC` | `allowed_quality` | doc=`supported_partial` strictness=`looser` | AC part 3 quality codes constrained to allowed set.
- `RPL::AC::domain::e4c89058e53c5e` | `AC` | `domain` | doc=`supported_partial` strictness=`stricter` | AC part 1 allowed domain values are enumerated.
- `RPL::AC::domain::f726571e77bfb0` | `AC` | `domain` | doc=`supported_partial` strictness=`stricter` | AC part 2 allowed domain values are enumerated.
- `RPL::AD::arity::e1d7a9e3a1ba40` | `AD` | `arity` | doc=`supported_partial` strictness=`looser` | AD requires 6 parsed part(s) in strict mode.
- `RPL::AG::domain::1630645888e088` | `AG` | `domain` | doc=`supported_partial` strictness=`stricter` | AG part 1 allowed domain values are enumerated.
- `RPL::AH1::arity::799a30c16a6521` | `AH1` | `arity` | doc=`supported_partial` strictness=`stricter` | AH1 requires 5 parsed part(s) in strict mode.
- `RPL::AH1::domain::826068387e6335` | `AH1` | `domain` | doc=`supported_partial` strictness=`stricter` | AH1 part 3 allowed domain values are enumerated.
- `RPL::AH2::arity::9c665daa777001` | `AH2` | `arity` | doc=`supported_partial` strictness=`stricter` | AH2 requires 5 parsed part(s) in strict mode.
- `RPL::AH2::domain::194dce27177333` | `AH2` | `domain` | doc=`supported_partial` strictness=`stricter` | AH2 part 3 allowed domain values are enumerated.
- `RPL::AH3::arity::a3cb693da01c01` | `AH3` | `arity` | doc=`supported_partial` strictness=`stricter` | AH3 requires 5 parsed part(s) in strict mode.
- `RPL::AH3::domain::6ed80d9a4782e1` | `AH3` | `domain` | doc=`supported_partial` strictness=`stricter` | AH3 part 3 allowed domain values are enumerated.
- `RPL::AH4::arity::93e133fe1ed763` | `AH4` | `arity` | doc=`supported_partial` strictness=`stricter` | AH4 requires 5 parsed part(s) in strict mode.
- `RPL::AH4::domain::554ed89bb6cf64` | `AH4` | `domain` | doc=`supported_partial` strictness=`stricter` | AH4 part 3 allowed domain values are enumerated.
- `RPL::AH5::arity::f7aece8b15067f` | `AH5` | `arity` | doc=`supported_partial` strictness=`stricter` | AH5 requires 5 parsed part(s) in strict mode.
- `RPL::AH5::domain::f3da158abbd4ca` | `AH5` | `domain` | doc=`supported_partial` strictness=`stricter` | AH5 part 3 allowed domain values are enumerated.
- `RPL::AH6::arity::6b6962d4cc8372` | `AH6` | `arity` | doc=`supported_partial` strictness=`stricter` | AH6 requires 5 parsed part(s) in strict mode.
- `RPL::AH6::domain::a0d4caee2b53be` | `AH6` | `domain` | doc=`supported_partial` strictness=`stricter` | AH6 part 3 allowed domain values are enumerated.
- `RPL::AI1::arity::37bcd9e25334a4` | `AI1` | `arity` | doc=`supported_partial` strictness=`stricter` | AI1 requires 5 parsed part(s) in strict mode.
- `RPL::AI1::domain::db9a2cb1a37892` | `AI1` | `domain` | doc=`supported_partial` strictness=`stricter` | AI1 part 3 allowed domain values are enumerated.
- `RPL::AI2::arity::f08c44dcd33e7f` | `AI2` | `arity` | doc=`supported_partial` strictness=`stricter` | AI2 requires 5 parsed part(s) in strict mode.
- `RPL::AI2::domain::39163de9175045` | `AI2` | `domain` | doc=`supported_partial` strictness=`stricter` | AI2 part 3 allowed domain values are enumerated.
- `RPL::AI3::arity::60f801168e7503` | `AI3` | `arity` | doc=`supported_partial` strictness=`stricter` | AI3 requires 5 parsed part(s) in strict mode.

## Ambiguous / Manual Review Rows
- `RPL::AA1::domain::115299be0bdd3d` | `AA1` | `domain` | match=`isd-format-document.deterministic.md::d89a89cba42d::AA1::domain::7049972093` | Matched isd-format-document.deterministic.md::d89a89cba42d::AA1::domain::7049972093, but multiple comparable spec rows exist.
- `RPL::AA1::width::305fab57b19c6f` | `AA1` | `width` | match=`isd-format-document.deterministic.md::238bebc52bad::AA1::width::da8bf6c4d0` | Matched isd-format-document.deterministic.md::238bebc52bad::AA1::width::da8bf6c4d0, but multiple comparable spec rows exist.
- `RPL::AA1::width::9dddf16a7ffa2b` | `AA1` | `width` | match=`isd-format-document.deterministic.md::238bebc52bad::AA1::width::da8bf6c4d0` | Matched isd-format-document.deterministic.md::238bebc52bad::AA1::width::da8bf6c4d0, but multiple comparable spec rows exist.
- `RPL::AA2::domain::8ed2b7280c47b1` | `AA2` | `domain` | match=`isd-format-document.deterministic.md::f9f36ae5289f::AA2::domain::7049972093` | Matched isd-format-document.deterministic.md::f9f36ae5289f::AA2::domain::7049972093, but multiple comparable spec rows exist.
- `RPL::AA2::width::458f8ff1ee45bd` | `AA2` | `width` | match=`isd-format-document.deterministic.md::987237c9860f::AA2::width::da8bf6c4d0` | Matched isd-format-document.deterministic.md::987237c9860f::AA2::width::da8bf6c4d0, but multiple comparable spec rows exist.
- `RPL::AA2::width::a8d873b3f632f2` | `AA2` | `width` | match=`isd-format-document.deterministic.md::987237c9860f::AA2::width::da8bf6c4d0` | Matched isd-format-document.deterministic.md::987237c9860f::AA2::width::da8bf6c4d0, but multiple comparable spec rows exist.
- `RPL::AA3::domain::90ae3db04dce74` | `AA3` | `domain` | match=`isd-format-document.deterministic.md::e024d400d19c::AA3::domain::8df6c39aa4` | Matched isd-format-document.deterministic.md::e024d400d19c::AA3::domain::8df6c39aa4, but multiple comparable spec rows exist.
- `RPL::AA3::width::e362c5a4d4ee75` | `AA3` | `width` | match=`isd-format-document.deterministic.md::73b50b27725a::AA3::width::da8bf6c4d0` | Matched isd-format-document.deterministic.md::73b50b27725a::AA3::width::da8bf6c4d0, but multiple comparable spec rows exist.
- `RPL::AA3::width::e6d1b5842366c2` | `AA3` | `width` | match=`isd-format-document.deterministic.md::73b50b27725a::AA3::width::da8bf6c4d0` | Matched isd-format-document.deterministic.md::73b50b27725a::AA3::width::da8bf6c4d0, but multiple comparable spec rows exist.
- `RPL::AA4::domain::a261955541ccc2` | `AA4` | `domain` | match=`isd-format-document.deterministic.md::a131f8635371::AA4::domain::8df6c39aa4` | Matched isd-format-document.deterministic.md::a131f8635371::AA4::domain::8df6c39aa4, but multiple comparable spec rows exist.
- `RPL::AA4::width::a5256c8d7e378e` | `AA4` | `width` | match=`isd-format-document.deterministic.md::d41be2e45334::AA4::width::da8bf6c4d0` | Matched isd-format-document.deterministic.md::d41be2e45334::AA4::width::da8bf6c4d0, but multiple comparable spec rows exist.
- `RPL::AA4::width::a5d50c96a607ca` | `AA4` | `width` | match=`isd-format-document.deterministic.md::d41be2e45334::AA4::width::da8bf6c4d0` | Matched isd-format-document.deterministic.md::d41be2e45334::AA4::width::da8bf6c4d0, but multiple comparable spec rows exist.
- `RPL::AB::width::2a11fabaf17675` | `AB` | `width` | match=`isd-format-document.deterministic.md::57cddaba913b::AB1::width::da8bf6c4d0` | Matched isd-format-document.deterministic.md::57cddaba913b::AB1::width::da8bf6c4d0, but multiple comparable spec rows exist.
- `RPL::AB::width::dbf822b03d0152` | `AB` | `width` | match=`isd-format-document.deterministic.md::57cddaba913b::AB1::width::da8bf6c4d0` | Matched isd-format-document.deterministic.md::57cddaba913b::AB1::width::da8bf6c4d0, but multiple comparable spec rows exist.
- `RPL::AC::sentinel::03f2a69bd7ec54` | `AC` | `sentinel` | match=`isd-format-document.deterministic.md::40d41993158c::AC1::sentinel::0006a4e09e` | Matched isd-format-document.deterministic.md::40d41993158c::AC1::sentinel::0006a4e09e, but multiple comparable spec rows exist.
- `RPL::AC::sentinel::5adbbc139f1bd2` | `AC` | `sentinel` | match=`isd-format-document.deterministic.md::40d41993158c::AC1::sentinel::0006a4e09e` | Matched isd-format-document.deterministic.md::40d41993158c::AC1::sentinel::0006a4e09e, but multiple comparable spec rows exist.
- `RPL::AC::width::457d88ceb08287` | `AC` | `width` | match=`isd-format-document.deterministic.md::d6f2f667cb53::AC1::width::da8bf6c4d0` | Matched isd-format-document.deterministic.md::d6f2f667cb53::AC1::width::da8bf6c4d0, but multiple comparable spec rows exist.
- `RPL::AC::width::d7e64193b888e4` | `AC` | `width` | match=`isd-format-document.deterministic.md::d6f2f667cb53::AC1::width::da8bf6c4d0` | Matched isd-format-document.deterministic.md::d6f2f667cb53::AC1::width::da8bf6c4d0, but multiple comparable spec rows exist.
- `RPL::AC::width::f7c3baa5ed9762` | `AC` | `width` | match=`isd-format-document.deterministic.md::d6f2f667cb53::AC1::width::da8bf6c4d0` | Matched isd-format-document.deterministic.md::d6f2f667cb53::AC1::width::da8bf6c4d0, but multiple comparable spec rows exist.
- `RPL::AD::range::165dc2fdcfd09b` | `AD` | `range` | match=`isd-format-document.deterministic.md::062e56a36495::AD1::range::507ee23397` | Matched isd-format-document.deterministic.md::062e56a36495::AD1::range::507ee23397, but multiple comparable spec rows exist.
- `RPL::AD::range::296e08750bab5a` | `AD` | `range` | match=`isd-format-document.deterministic.md::062e56a36495::AD1::range::507ee23397` | Matched isd-format-document.deterministic.md::062e56a36495::AD1::range::507ee23397, but multiple comparable spec rows exist.
- `RPL::AD::range::ae4596a4589277` | `AD` | `range` | match=`isd-format-document.deterministic.md::062e56a36495::AD1::range::507ee23397` | Matched isd-format-document.deterministic.md::062e56a36495::AD1::range::507ee23397, but multiple comparable spec rows exist.
- `RPL::AD::sentinel::034abcd412f133` | `AD` | `sentinel` | match=`isd-format-document.deterministic.md::ee4943d6d370::AD1::sentinel::c5dbf82cfb` | Matched isd-format-document.deterministic.md::ee4943d6d370::AD1::sentinel::c5dbf82cfb, but multiple comparable spec rows exist.
- `RPL::AD::sentinel::3e791d130ed3be` | `AD` | `sentinel` | match=`isd-format-document.deterministic.md::ee4943d6d370::AD1::sentinel::c5dbf82cfb` | Matched isd-format-document.deterministic.md::ee4943d6d370::AD1::sentinel::c5dbf82cfb, but multiple comparable spec rows exist.
- `RPL::AD::sentinel::f2e661d4e05b6f` | `AD` | `sentinel` | match=`isd-format-document.deterministic.md::ee4943d6d370::AD1::sentinel::c5dbf82cfb` | Matched isd-format-document.deterministic.md::ee4943d6d370::AD1::sentinel::c5dbf82cfb, but multiple comparable spec rows exist.
- `RPL::AD::width::314b30714f4308` | `AD` | `width` | match=`isd-format-document.deterministic.md::2ee7a1381258::AD1::width::8c9caffdfb` | Matched isd-format-document.deterministic.md::2ee7a1381258::AD1::width::8c9caffdfb, but multiple comparable spec rows exist.
- `RPL::AD::width::40d20b1ca4bbed` | `AD` | `width` | match=`isd-format-document.deterministic.md::2ee7a1381258::AD1::width::8c9caffdfb` | Matched isd-format-document.deterministic.md::2ee7a1381258::AD1::width::8c9caffdfb, but multiple comparable spec rows exist.
- `RPL::AD::width::ce897888913709` | `AD` | `width` | match=`isd-format-document.deterministic.md::2ee7a1381258::AD1::width::8c9caffdfb` | Matched isd-format-document.deterministic.md::2ee7a1381258::AD1::width::8c9caffdfb, but multiple comparable spec rows exist.
- `RPL::AD::width::dd520a2a62932d` | `AD` | `width` | match=`isd-format-document.deterministic.md::fafa47807a44::AD1::width::da8bf6c4d0` | Matched isd-format-document.deterministic.md::fafa47807a44::AD1::width::da8bf6c4d0, but multiple comparable spec rows exist.
- `RPL::AD::width::f5ef8906130fda` | `AD` | `width` | match=`isd-format-document.deterministic.md::fafa47807a44::AD1::width::da8bf6c4d0` | Matched isd-format-document.deterministic.md::fafa47807a44::AD1::width::da8bf6c4d0, but multiple comparable spec rows exist.

## Extraction Limitations
- Rule extraction is static: runtime branches dependent on unseen data payloads may not surface additional behavior.
- Spec matching relies on `spec_coverage.csv` normalization; ambiguous rows are intentionally marked for manual review.
- `normalization` and some structural guards are implementation-centric and may map only partially (or not at all) to deterministic spec rows.
- `keep_decision` is intentionally left blank unless objectively obvious from current code.
