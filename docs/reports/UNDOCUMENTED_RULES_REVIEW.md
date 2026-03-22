# Undocumented Rules Review

## Executive summary

- Total reviewed rules: **2481**
- Count by `recommended_action`:
  - `keep_as_documented`: 0
  - `keep_as_engineering_guard`: 1229
  - `weaken_to_flag_only`: 842
  - `remove_from_cleaning`: 0
  - `needs_manual_review`: 410
- Count by `scientific_risk`:
  - `low`: 4
  - `medium`: 1635
  - `high`: 842
- Interpretation: The cleaning code is materially stricter/less documented than extracted NOAA support: 179 stricter rules and 1986 rules with unknown/unsupported support are present in the reviewed set.

## Highest-priority findings

- `RPL::AC::domain::e4c89058e53c5e` (`AC` / `domain`): `weaken_to_flag_only`. Why it matters: doc=supported_partial, strictness=stricter behavior=null Current enforcement nulls/excludes values under weak NOAA support; safer as quality evidence. Code: `src/noaa_spec/constants.py:1931::FIELD_RULE_PREFIXES['AC'].parts[1].allowed_values`. Spec reference: `isd-format-document.deterministic.md::257338eb5c89::AC1::domain::0242b6a5ca`.
- `RPL::AC::domain::f726571e77bfb0` (`AC` / `domain`): `weaken_to_flag_only`. Why it matters: doc=supported_partial, strictness=stricter behavior=null Current enforcement nulls/excludes values under weak NOAA support; safer as quality evidence. Code: `src/noaa_spec/constants.py:1939::FIELD_RULE_PREFIXES['AC'].parts[2].allowed_values`. Spec reference: `isd-format-document.deterministic.md::870d94da3ef2::AC1::domain::5159408515`.
- `RPL::AD::domain::33eaf82266262c` (`AD` / `domain`): `weaken_to_flag_only`. Why it matters: doc=unknown, strictness=not_comparable behavior=null Current enforcement nulls/excludes values under weak NOAA support; safer as quality evidence. Code: `src/noaa_spec/constants.py:1981::FIELD_RULE_PREFIXES['AD'].parts[4].allowed_pattern`. Spec reference: `no matched spec rule id in ledger`.
- `RPL::AD::domain::677ed5dfddd256` (`AD` / `domain`): `weaken_to_flag_only`. Why it matters: doc=unknown, strictness=not_comparable behavior=null Current enforcement nulls/excludes values under weak NOAA support; safer as quality evidence. Code: `src/noaa_spec/constants.py:1972::FIELD_RULE_PREFIXES['AD'].parts[3].allowed_pattern`. Spec reference: `no matched spec rule id in ledger`.
- `RPL::AD::domain::b69bd19c301354` (`AD` / `domain`): `weaken_to_flag_only`. Why it matters: doc=unknown, strictness=not_comparable behavior=null Current enforcement nulls/excludes values under weak NOAA support; safer as quality evidence. Code: `src/noaa_spec/constants.py:1990::FIELD_RULE_PREFIXES['AD'].parts[5].allowed_pattern`. Spec reference: `no matched spec rule id in ledger`.
- `RPL::AG::domain::1630645888e088` (`AG` / `domain`): `weaken_to_flag_only`. Why it matters: doc=supported_partial, strictness=stricter behavior=null Current enforcement nulls/excludes values under weak NOAA support; safer as quality evidence. Code: `src/noaa_spec/constants.py:2067::FIELD_RULE_PREFIXES['AG'].parts[1].allowed_values`. Spec reference: `isd-format-document.deterministic.md::f56d87fca13f::AG1::domain::34aa592680`.
- `RPL::AH1::arity::799a30c16a6521` (`AH1` / `arity`): `weaken_to_flag_only`. Why it matters: doc=supported_partial, strictness=stricter behavior=exclude Current enforcement nulls/excludes values under weak NOAA support; safer as quality evidence. Code: `src/noaa_spec/cleaning.py:744::get_expected_part_count(AH1)`. Spec reference: `isd-format-document.deterministic.md::f2f3fd21464b::AH1::arity::c1097aca2d`.
- `RPL::AH1::domain::826068387e6335` (`AH1` / `domain`): `weaken_to_flag_only`. Why it matters: doc=supported_partial, strictness=stricter behavior=null Current enforcement nulls/excludes values under weak NOAA support; safer as quality evidence. Code: `src/noaa_spec/constants.py:2100::FIELD_RULE_PREFIXES['AH'].parts[3].allowed_values`. Spec reference: `isd-format-document.deterministic.md::1838e0c276b4::AH1::domain::af31ab33c8`.
- `RPL::AH2::arity::9c665daa777001` (`AH2` / `arity`): `weaken_to_flag_only`. Why it matters: doc=supported_partial, strictness=stricter behavior=exclude Current enforcement nulls/excludes values under weak NOAA support; safer as quality evidence. Code: `src/noaa_spec/cleaning.py:744::get_expected_part_count(AH2)`. Spec reference: `isd-format-document.deterministic.md::96faed91300f::AH2::arity::c1097aca2d`.
- `RPL::AH2::domain::194dce27177333` (`AH2` / `domain`): `weaken_to_flag_only`. Why it matters: doc=supported_partial, strictness=stricter behavior=null Current enforcement nulls/excludes values under weak NOAA support; safer as quality evidence. Code: `src/noaa_spec/constants.py:2100::FIELD_RULE_PREFIXES['AH'].parts[3].allowed_values`. Spec reference: `isd-format-document.deterministic.md::87cbb9dab657::AH2::domain::af31ab33c8`.
- `RPL::AH3::arity::a3cb693da01c01` (`AH3` / `arity`): `weaken_to_flag_only`. Why it matters: doc=supported_partial, strictness=stricter behavior=exclude Current enforcement nulls/excludes values under weak NOAA support; safer as quality evidence. Code: `src/noaa_spec/cleaning.py:744::get_expected_part_count(AH3)`. Spec reference: `isd-format-document.deterministic.md::2e055911df4e::AH3::arity::c1097aca2d`.
- `RPL::AH3::domain::6ed80d9a4782e1` (`AH3` / `domain`): `weaken_to_flag_only`. Why it matters: doc=supported_partial, strictness=stricter behavior=null Current enforcement nulls/excludes values under weak NOAA support; safer as quality evidence. Code: `src/noaa_spec/constants.py:2100::FIELD_RULE_PREFIXES['AH'].parts[3].allowed_values`. Spec reference: `isd-format-document.deterministic.md::6ea27b6b1c27::AH3::domain::af31ab33c8`.

## Rules likely safe to keep

These are parser/schema determinism guards and publication-contract protections with low semantic distortion risk.

- `RPL::AD::arity::e1d7a9e3a1ba40`: Payload expansion returns empty object for arity mismatch in strict mode. Code: `src/noaa_spec/cleaning.py:744::get_expected_part_count(AD)`. Spec: `isd-format-document.deterministic.md::b2f054c23ac5::AD1::arity::b2cff35beb`.
- `RPL::ADD::exclusion::10f9b7ae7a0260`: Structural marker column is removed from cleaned output. Code: `src/noaa_spec/cleaning.py:1441::ADD marker drop`. Spec: `no matched spec rule id in ledger`.
- `RPL::AM::arity::86c7c182a07ca2`: Payload expansion returns empty object for arity mismatch in strict mode. Code: `src/noaa_spec/cleaning.py:744::get_expected_part_count(AM)`. Spec: `isd-format-document.deterministic.md::78286bada3b4::AM1::arity::b2cff35beb`.
- `RPL::AP::arity::e6524876aad01e`: Payload expansion returns empty object for arity mismatch in strict mode. Code: `src/noaa_spec/cleaning.py:744::get_expected_part_count(AP)`. Spec: `no matched spec rule id in ledger`.
- `RPL::AT1::arity::30d1518ae07ef7`: Payload expansion returns empty object for arity mismatch in strict mode. Code: `src/noaa_spec/cleaning.py:744::get_expected_part_count(AT1)`. Spec: `isd-format-document.deterministic.md::88e0ba6703cd::AT1::arity::d077ed6f7f`.
- `RPL::AT2::arity::7ce620356f411c`: Payload expansion returns empty object for arity mismatch in strict mode. Code: `src/noaa_spec/cleaning.py:744::get_expected_part_count(AT2)`. Spec: `isd-format-document.deterministic.md::bf7e54f70af5::AT2::arity::d077ed6f7f`.
- `RPL::AT3::arity::4c67a2556ee1d2`: Payload expansion returns empty object for arity mismatch in strict mode. Code: `src/noaa_spec/cleaning.py:744::get_expected_part_count(AT3)`. Spec: `isd-format-document.deterministic.md::826492d15194::AT3::arity::d077ed6f7f`.
- `RPL::AT4::arity::5e22712b015c3e`: Payload expansion returns empty object for arity mismatch in strict mode. Code: `src/noaa_spec/cleaning.py:744::get_expected_part_count(AT4)`. Spec: `isd-format-document.deterministic.md::82a944aa69b9::AT4::arity::d077ed6f7f`.
- `RPL::AT5::arity::ee4bac6d137544`: Payload expansion returns empty object for arity mismatch in strict mode. Code: `src/noaa_spec/cleaning.py:744::get_expected_part_count(AT5)`. Spec: `isd-format-document.deterministic.md::fa97441e0eaf::AT5::arity::d077ed6f7f`.
- `RPL::AT6::arity::ccf65070edaaf2`: Payload expansion returns empty object for arity mismatch in strict mode. Code: `src/noaa_spec/cleaning.py:744::get_expected_part_count(AT6)`. Spec: `isd-format-document.deterministic.md::92601873b18c::AT6::arity::d077ed6f7f`.
- `RPL::AT7::arity::753fcd572bc928`: Payload expansion returns empty object for arity mismatch in strict mode. Code: `src/noaa_spec/cleaning.py:744::get_expected_part_count(AT7)`. Spec: `isd-format-document.deterministic.md::f65511a14edf::AT7::arity::d077ed6f7f`.
- `RPL::AT8::arity::c2190817aab7ae`: Payload expansion returns empty object for arity mismatch in strict mode. Code: `src/noaa_spec/cleaning.py:744::get_expected_part_count(AT8)`. Spec: `isd-format-document.deterministic.md::259371302a94::AT8::arity::d077ed6f7f`.

## Rules that should probably be downgraded to quality evidence

These mostly nullify/exclude observations under unknown or stricter-than-doc support; preserving values with flags is safer.

- `RPL::AC::domain::e4c89058e53c5e`: Tokens outside allowed domain are nullified. Code: `src/noaa_spec/constants.py:1931::FIELD_RULE_PREFIXES['AC'].parts[1].allowed_values`. Spec: `isd-format-document.deterministic.md::257338eb5c89::AC1::domain::0242b6a5ca`.
- `RPL::AC::domain::f726571e77bfb0`: Tokens outside allowed domain are nullified. Code: `src/noaa_spec/constants.py:1939::FIELD_RULE_PREFIXES['AC'].parts[2].allowed_values`. Spec: `isd-format-document.deterministic.md::870d94da3ef2::AC1::domain::5159408515`.
- `RPL::AD::domain::33eaf82266262c`: Pattern mismatch values are nullified. Code: `src/noaa_spec/constants.py:1981::FIELD_RULE_PREFIXES['AD'].parts[4].allowed_pattern`. Spec: `no matched spec rule id in ledger`.
- `RPL::AD::domain::677ed5dfddd256`: Pattern mismatch values are nullified. Code: `src/noaa_spec/constants.py:1972::FIELD_RULE_PREFIXES['AD'].parts[3].allowed_pattern`. Spec: `no matched spec rule id in ledger`.
- `RPL::AD::domain::b69bd19c301354`: Pattern mismatch values are nullified. Code: `src/noaa_spec/constants.py:1990::FIELD_RULE_PREFIXES['AD'].parts[5].allowed_pattern`. Spec: `no matched spec rule id in ledger`.
- `RPL::AG::domain::1630645888e088`: Tokens outside allowed domain are nullified. Code: `src/noaa_spec/constants.py:2067::FIELD_RULE_PREFIXES['AG'].parts[1].allowed_values`. Spec: `isd-format-document.deterministic.md::f56d87fca13f::AG1::domain::34aa592680`.
- `RPL::AH1::arity::799a30c16a6521`: Payload expansion returns empty object for arity mismatch in strict mode. Code: `src/noaa_spec/cleaning.py:744::get_expected_part_count(AH1)`. Spec: `isd-format-document.deterministic.md::f2f3fd21464b::AH1::arity::c1097aca2d`.
- `RPL::AH1::domain::826068387e6335`: Tokens outside allowed domain are nullified. Code: `src/noaa_spec/constants.py:2100::FIELD_RULE_PREFIXES['AH'].parts[3].allowed_values`. Spec: `isd-format-document.deterministic.md::1838e0c276b4::AH1::domain::af31ab33c8`.
- `RPL::AH2::arity::9c665daa777001`: Payload expansion returns empty object for arity mismatch in strict mode. Code: `src/noaa_spec/cleaning.py:744::get_expected_part_count(AH2)`. Spec: `isd-format-document.deterministic.md::96faed91300f::AH2::arity::c1097aca2d`.
- `RPL::AH2::domain::194dce27177333`: Tokens outside allowed domain are nullified. Code: `src/noaa_spec/constants.py:2100::FIELD_RULE_PREFIXES['AH'].parts[3].allowed_values`. Spec: `isd-format-document.deterministic.md::87cbb9dab657::AH2::domain::af31ab33c8`.
- `RPL::AH3::arity::a3cb693da01c01`: Payload expansion returns empty object for arity mismatch in strict mode. Code: `src/noaa_spec/cleaning.py:744::get_expected_part_count(AH3)`. Spec: `isd-format-document.deterministic.md::2e055911df4e::AH3::arity::c1097aca2d`.
- `RPL::AH3::domain::6ed80d9a4782e1`: Tokens outside allowed domain are nullified. Code: `src/noaa_spec/constants.py:2100::FIELD_RULE_PREFIXES['AH'].parts[3].allowed_values`. Spec: `isd-format-document.deterministic.md::6ea27b6b1c27::AH3::domain::af31ab33c8`.

## Rules that should probably be removed


## Recommended cleanup sequence

1. Freeze parser-structure guards (`width`, `arity`, malformed-record exclusions) and document them as engineering guards.
2. Convert high-risk unsupported/stricter null/exclude rules to flag-only behavior behind parity tests.
3. Remove unsupported semantic rewrites from default cleaning or gate them behind optional transforms.
4. Resolve `needs_manual_review` rows by linking each to exact NOAA lines or reclassifying as engineering guard.
5. Re-run provenance generation and update this review to confirm action-count reduction in risky buckets.

## Method notes

- Inputs: `RULE_PROVENANCE_LEDGER.csv` (existing repository artifact) and embedded `code_reference` / `matched_spec_rule_id` provenance columns.
- Selection logic: all rows meeting any required criteria (`implementation_only`, `legacy_behavior`, `unsupported`, `unknown`, `stricter`) plus ambiguous `documented_inferred` rows (`needs_manual_review` and weak/uncertain match).
- Ambiguous rule definition used here: `documented_inferred` + `needs_manual_review` + (`matched_spec_rule_id` missing or `strictness_vs_doc != equal`).
