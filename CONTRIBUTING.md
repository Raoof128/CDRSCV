# Contributing

Thank you for helping strengthen the Consumer Data Right Security Conformance
Validator! This document summarises how to contribute fixes or new checks in a
repeatable, automation-friendly way.

## Development environment

1. Create a virtual environment and install the project in editable mode:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .[dev]
   ```

2. Run the quality gates before opening a pull request:

   ```bash
   make lint
   make test
   ```

3. If you are contributing new checks or CLI options, please update the
   documentation under `docs/` and add tests that prove the new behaviour.

## Coding guidelines

* Prefer small, well named modules. The existing checks under `cdrcsv/checks/`
  are good references for structure and docstrings.
* Keep all networking in `cdrcsv.client.CDRClient`. Checks should consume
  simple data structures instead of performing I/O themselves.
* Write deterministic unit tests that do not require live network access.
* Run `ruff` and `pytest` locally before submitting patches. Both tools are
  configured via `pyproject.toml` so CI can reproduce your environment.

## Commit messages and pull requests

* Follow the conventional _imperative mood_ style (e.g. "Add latency check")
  for commit messages.
* Include a short rationale for the change in the pull request description so
  reviewers understand the motivation.
* Link to any relevant Consumer Data Right specifications, ACCC advisories, or
  FAPI RFCs if a change implements a specific control.

## Security reporting

If you discover a vulnerability, please follow the process documented in
[`SECURITY.md`](SECURITY.md) instead of opening a public issue.
