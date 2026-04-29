# Contributing

## Development setup

Use the same Python 3.12 virtual-environment flow documented in the README:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e .
```

If `python3 -m venv` is unavailable on Ubuntu/Debian, install `python3-venv` first.

Install test tooling if needed:

```bash
python3 -m pip install pytest pytest-cov
```

## Running tests

Run the full suite:

```bash
python3 -m pytest -q
```

Run CLI smoke checks:

```bash
python3 -m noaa_spec.cli --help
noaa-spec --help
```

## Adding or updating rules

- Treat NOAA documentation as the authoritative source.
- Keep rule provenance explicit in code and tests.
- Prefer adding or tightening validation through declarative rules and deterministic checks.
- If a rule is stricter than the source documentation, record that rationale clearly and avoid silent data loss.

## Coding standards

- Preserve deterministic outputs and stable schema contracts.
- Keep production code under `src/noaa_spec/`.
- Keep reproducibility helper scripts minimal and reproducibility-oriented.
- Update tests and documentation in the same change whenever paths, commands, or contracts change.
