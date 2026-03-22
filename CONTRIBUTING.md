# Contributing

## Development setup

Install the project in editable mode:

```bash
pip install -e .
```

Install test tooling if needed:

```bash
python3 -m pip install --user --break-system-packages pytest pytest-cov
```

## Running tests

Run the full suite:

```bash
pytest -q
```

Run CLI smoke checks:

```bash
python -m noaa_spec.cli --help
noaa-spec --help
```

## Adding or updating rules

- Treat NOAA documentation as the authoritative source.
- Keep rule provenance explicit in code, tests, and generated evidence artifacts.
- Prefer adding or tightening validation through declarative rules and deterministic checks.
- If a rule is stricter than the source documentation, record that rationale clearly and avoid silent data loss.

## Coding standards

- Preserve deterministic outputs and stable schema contracts.
- Keep production code under `src/noaa_spec/`.
- Keep scripts in `scripts/` or `tools/` unless there is a real reuse benefit in moving logic into the library.
- Update tests and documentation in the same change whenever paths, commands, or contracts change.
