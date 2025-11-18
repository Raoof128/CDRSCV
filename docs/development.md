# Development playbook

This document expands on `CONTRIBUTING.md` with day-to-day commands and test
strategies.

## Tooling

* **Python** – 3.11 or newer.
* **Dependencies** – install via `pip install -e .[dev]`.
* **Linters** – `ruff` enforces formatting and import rules; configuration lives
  in `ruff.toml`.
* **Type checking** – `mypy` is configured via `mypy.ini` to catch regressions.

## Common commands

| Command | Purpose |
| ------- | ------- |
| `make install` | Install project plus dev extras into the active venv |
| `make lint` | Run `ruff` (style) and `mypy` (types) |
| `make test` | Execute `pytest` with coverage output |

All commands are idempotent and can be run locally or in CI.

## Writing new checks

1. Add a class under `cdrcsv/checks/` that subclasses `Check` and returns
   `CheckResult` objects.
2. Reference the new check from `CDRValidator` (if global) or from a profile
   configuration.
3. Capture the expected behaviour in `tests/` with fixtures that do not require
   live network access.

## Custom profiles

Custom JSON/TOML files can be loaded via the CLI:

```bash
python -m cdrcsv --profile-file profiles/bank.json --profile bank-prod
```

Each profile entry is keyed by name and contains the same structure as the
built-in ACCC profile. See `examples/accc-profile.json` for a template.
