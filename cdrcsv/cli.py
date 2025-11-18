"""Command line interface for the validator."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable, Mapping
from pathlib import Path

from .config import (
    HeaderExpectation,
    HTTPRequestConfig,
    HTTPResponseExpectations,
    TLSRequirements,
    ValidatorProfile,
)
from .logging import LOG_LEVELS, configure_logging
from .profiles import BUILTIN_PROFILES, load_profiles_from_file
from .report import ValidationReport
from .validator import CDRValidator


def parse_header_overrides(values: Iterable[str]) -> list[HeaderExpectation]:
    expectations = []
    for item in values:
        if "=" not in item:
            raise argparse.ArgumentTypeError("header overrides must use name=regex syntax")
        name, pattern = item.split("=", 1)
        expectations.append(HeaderExpectation(name=name.strip(), pattern=pattern.strip()))
    return expectations


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profile",
        default="accc",
        help="Name of the validation profile to run",
    )
    parser.add_argument(
        "--profile-file",
        action="append",
        default=[],
        metavar="PATH",
        help="Load additional profiles from a JSON or TOML file (repeatable)",
    )
    parser.add_argument(
        "--list-profiles",
        action="store_true",
        help="List available profiles and exit",
    )
    parser.add_argument("--base-url", help="Override the base URL for the target data holder")
    parser.add_argument("--endpoint", help="Override the endpoint path")
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="HTTP request timeout in seconds",
    )
    parser.add_argument(
        "--header",
        action="append",
        default=[],
        metavar="name=regex",
        help="Extra required response headers expressed as regex patterns",
    )
    parser.add_argument("--min-tls", default=None, help="Minimum TLS version (e.g. TLSv1.2)")
    parser.add_argument(
        "--status",
        dest="status_codes",
        action="append",
        type=int,
        metavar="CODE",
        help="Allowable HTTP status codes (repeatable)",
    )
    parser.add_argument(
        "--content-type",
        dest="content_types",
        action="append",
        metavar="MIME",
        help="Required Content-Type prefixes (repeatable)",
    )
    parser.add_argument(
        "--max-latency",
        dest="max_latency",
        type=float,
        default=None,
        help="Maximum acceptable response latency in seconds",
    )
    parser.add_argument("--json", action="store_true", help="Emit the report as JSON")
    parser.add_argument("--verbose", action="store_true", help="Print verbose human readable output")
    parser.add_argument(
        "--log-level",
        default="WARNING",
        choices=LOG_LEVELS,
        help="Logging verbosity for diagnostics",
    )
    return parser


def discover_profiles(profile_files: Iterable[str]) -> dict[str, ValidatorProfile]:
    """Return built-in profiles plus any supplied via JSON/TOML files."""

    catalog = dict(BUILTIN_PROFILES)
    for path_str in profile_files:
        file_profiles = load_profiles_from_file(Path(path_str))
        duplicate_keys = set(file_profiles) & set(catalog)
        catalog.update(file_profiles)
        if duplicate_keys:
            duplicates = ", ".join(sorted(duplicate_keys))
            print(
                f"Warning: overriding existing profiles with entries from {path_str}: {duplicates}",
                file=sys.stderr,
            )
    return catalog


def configure_profile(args: argparse.Namespace, *, profiles: Mapping[str, ValidatorProfile]) -> ValidatorProfile:
    try:
        base_profile = profiles[args.profile]
    except KeyError as exc:  # pragma: no cover - defensive guard
        raise SystemExit(f"Unknown profile '{args.profile}'") from exc

    base_request = base_profile.request
    request_overrides = {
        "base_url": args.base_url or base_request.base_url,
        "endpoint": args.endpoint or base_request.endpoint,
        "timeout": args.timeout if args.timeout is not None else base_request.timeout,
    }
    request = HTTPRequestConfig(
        method=base_request.method,
        base_url=request_overrides["base_url"],
        endpoint=request_overrides["endpoint"],
        headers=base_request.headers,
        timeout=request_overrides["timeout"],
    )

    expected_headers = list(base_profile.expected_headers)
    if args.header:
        expected_headers.extend(parse_header_overrides(args.header))

    tls_req = base_profile.tls
    if args.min_tls:
        tls_req = TLSRequirements(
            min_version=args.min_tls,
            allowed_cipher_substrings=tls_req.allowed_cipher_substrings,
        )

    response_expectations = base_profile.response_expectations
    status_codes = (
        tuple(args.status_codes)
        if args.status_codes
        else response_expectations.status_codes
    )
    content_types = (
        tuple(args.content_types)
        if args.content_types
        else response_expectations.content_type_prefixes
    )
    max_latency = (
        args.max_latency
        if args.max_latency is not None
        else response_expectations.max_latency_seconds
    )
    response_expectations = HTTPResponseExpectations(
        status_codes=status_codes,
        content_type_prefixes=content_types,
        max_latency_seconds=max_latency,
    )

    return ValidatorProfile(
        name=base_profile.name,
        request=request,
        expected_headers=expected_headers,
        response_expectations=response_expectations,
        tls=tls_req,
    )


def format_profile_listing(profiles: Mapping[str, ValidatorProfile]) -> str:
    lines = ["Available profiles:"]
    for name in sorted(profiles):
        profile = profiles[name]
        lines.append(f"- {name}: {profile.request.url()} (timeout {profile.request.timeout}s)")
    return "\n".join(lines)


def format_report(report: ValidationReport, verbose: bool = False) -> str:
    lines = [f"Target: {report.target_url}"]
    if verbose:
        lines.append("")
    for result in report.check_results:
        symbol = "✔" if result.passed else "✖"
        lines.append(f"{symbol} {result.name} - {result.details}")
    lines.append("")
    lines.append("Overall: PASS" if report.passed else "Overall: FAIL")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    configure_logging(args.log_level)
    profiles = discover_profiles(args.profile_file)

    if args.list_profiles:
        print(format_profile_listing(profiles))
        return 0

    profile = configure_profile(args, profiles=profiles)
    validator = CDRValidator(profile)
    report = validator.run()

    if args.json:
        print(json.dumps(report.as_dict(), indent=2))
    else:
        print(format_report(report, verbose=args.verbose))

    return 0 if report.passed else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

