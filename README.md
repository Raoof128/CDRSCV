# Consumer Data Right Security Conformance Validator

The **Consumer Data Right Security Conformance Validator (CDRSCV)** is a
lightweight Python toolkit that exercises Australian Consumer Data Right (CDR)
API endpoints and validates that they honour the Financial-grade API (FAPI)
security profile enforced by the Australian Competition and Consumer
Commission (ACCC).

The validator focuses on three key areas:

1. **HTTP response hygiene** – validates that responses return the expected
   status codes, `Content-Type` values (JSON by default) and stay within a
   configurable latency budget before any other checks are attempted. This
   guards against proxies, misrouted traffic or slow upstreams.
2. **HTTP layer security metadata** – verifies that mandatory CDR security
   headers (such as `x-v`, `x-min-v`, `x-fapi-interaction-id`) are present and
   well formed, along with common defensive headers.
3. **Transport layer posture** – inspects the TLS handshake to ensure that the
   target endpoint negotiates TLS 1.2+ with modern cipher suites and a valid
   certificate chain.

> ⚠️ **Note about networking**: the validator is designed to connect to the
> public ACCC CDR Sandbox (`https://sandbox.api.consumerdatastandards.gov.au`).
> The execution environment used for this repository has outbound network
> restrictions, so the example commands below will raise informative errors at
> runtime. They are still provided to document the expected workflow on an
> unrestricted workstation.

## Quick start

Create a virtual environment and install the project:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Now run the validator against the default ACCC sandbox banking products
endpoint:

```bash
python -m cdrcsv --profile accc --verbose
```

Example output (abridged):

```
Target: https://sandbox.api.consumerdatastandards.gov.au/cds-au/v1/banking/products

HTTP request
============
✔ x-v header present with value '3'
✔ x-min-v header present with value '1'
✖ x-fapi-customer-ip-address missing (required)

TLS posture
===========
✔ TLS version negotiated: TLSv1.3
✔ Certificate expires: 2026-02-03 12:00:00+00:00
```

Use `python -m cdrcsv --help` to explore additional options such as:

* selecting custom base URLs or endpoints,
* overriding header expectations,
* narrowing acceptable HTTP status codes or `Content-Type` prefixes,
* tuning the HTTP timeout (`--timeout`), maximum tolerated response latency (`--max-latency`),
  and log verbosity (`--log-level`),
* loading bespoke profiles from JSON/TOML via `--profile-file`,
* exporting JSON reports.

### Working with custom profiles

Profiles are simply dictionaries stored in JSON or TOML files. Each top-level
key maps to a `ValidatorProfile` definition. Add a profile file and then select
it with the CLI:

```bash
python -m cdrcsv --profile-file profiles/bank.json --profile bank-prod
```

See [`examples/accc-profile.json`](examples/accc-profile.json) for a template.

## Project layout

```
cdrcsv/
├── checks/          # Individual HTTP/TLS validations
├── cli.py           # Command line entry point
├── config.py        # Dataclasses representing runtime configuration
├── profiles.py      # Built-in validation profiles (ACCC sandbox, etc.)
├── report.py        # Aggregated report model
└── validator.py     # High level orchestration logic
```

Tests live under `tests/` and can be executed with `pytest` (or `make test`).

Additional documentation is available under `docs/`:

* [`architecture.md`](docs/architecture.md) – module-level responsibilities and
  data flow.
* [`development.md`](docs/development.md) – local tooling, commands, and profile tips.

Contribution guidelines live in [`CONTRIBUTING.md`](CONTRIBUTING.md), while
[`SECURITY.md`](SECURITY.md) and [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md)
describe reporting and community expectations.

## Extending the validator

The validator is intentionally modular. New checks can be created by deriving
from `cdrcsv.checks.base.Check` and added to a custom profile. This allows
banks, data recipients or energy retailers to codify organisation-specific
security controls while reusing the existing transport and reporting plumbing.

## Development

Use the provided `Makefile` targets for common workflows:

```bash
make install  # install project with dev extras
make lint     # run ruff + mypy
make test     # execute pytest with coverage
```

