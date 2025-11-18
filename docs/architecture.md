# Architecture overview

The Consumer Data Right Security Conformance Validator is intentionally small
and modular so that individual checks can be reused in bank or energy company
pipelines.

## High-level flow

1. The CLI parses arguments and builds a `ValidatorProfile` by combining a base
   profile with any operator overrides.
2. `CDRValidator` orchestrates the run: it instantiates a `CDRClient`, issues a
   single HTTP request, and then fans the response out to each check.
3. Checks report results as `CheckResult` objects. These results are aggregated
   into a `ValidationReport` that can be rendered to text or JSON.

## Package layout

| Module | Responsibility |
| ------ | -------------- |
| `cdrcsv.cli` | Argument parsing, profile discovery, report formatting |
| `cdrcsv.client` | Thin HTTP wrapper around `requests` with sane defaults |
| `cdrcsv.checks.http` | Response hygiene (status codes, `Content-Type`, latency) |
| `cdrcsv.checks.headers` | FAPI/CDR header enforcement |
| `cdrcsv.checks.tls` | TLS handshake inspection and certificate validation |
| `cdrcsv.profiles` | Built-in profiles plus helpers to load custom JSON/TOML files |
| `cdrcsv.validator` | Orchestration and result collation |

## Profiles

Profiles define the full runtime configuration for a validation run. They are
serialized as dictionaries with four sections:

* `request` – HTTP method, base URL, endpoint, default headers, timeout.
* `expected_headers` – list of header name/regex pairs and optional descriptions.
* `response_expectations` – status codes, `Content-Type` prefixes, and latency
  budgets.
* `tls` – minimum protocol version and cipher fragments that must appear in the
  negotiated suite.

Profiles can be bundled with the package (see `cdrcsv.profiles.BUILTIN_PROFILES`)
or loaded from JSON/TOML files at runtime via the `--profile-file` CLI option.

## Extensibility

* New validations can subclass `cdrcsv.checks.base.Check` and be wired into a
  profile.
* The `CDRValidator` accepts any profile, so bespoke checks and TLS policies can
  be layered without modifying the CLI.
* The CLI exposes overrides for timeouts, headers, status codes, content types,
  latency budgets, TLS minimums, and profile sources. This makes it possible to
  integrate with CI pipelines or run bespoke scenarios without code changes.
