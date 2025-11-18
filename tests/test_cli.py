import json

from cdrcsv.checks.base import CheckResult
from cdrcsv.cli import (
    configure_profile,
    discover_profiles,
    format_profile_listing,
    format_report,
    parse_header_overrides,
)
from cdrcsv.report import ValidationReport


def test_parse_header_overrides_supports_multiple_entries():
    overrides = parse_header_overrides(["x-demo=^foo$", "x-bar=^.+$"])
    assert len(overrides) == 2
    assert overrides[0].name == "x-demo"


def test_configure_profile_applies_overrides():
    parser_args = type(
        "Args",
        (),
        {
            "profile": "accc",
            "base_url": "https://example.com",
            "endpoint": "/foo",
            "timeout": 30.0,
            "header": ["x-extra=^bar$"]
            ,
            "min_tls": "TLSv1.3",
            "status_codes": [201],
            "content_types": ["application/json"],
            "max_latency": 0.5,
        },
    )
    profile = configure_profile(parser_args, profiles=discover_profiles([]))
    assert profile.request.base_url == "https://example.com"
    assert profile.request.endpoint == "/foo"
    assert profile.request.timeout == 30.0
    assert any(h.name == "x-extra" for h in profile.expected_headers)
    assert profile.tls.min_version == "TLSv1.3"
    assert profile.response_expectations.status_codes == (201,)
    assert profile.response_expectations.content_type_prefixes == ("application/json",)
    assert profile.response_expectations.max_latency_seconds == 0.5


def test_format_report_contains_symbols():
    report = ValidationReport(target_url="https://example.com")
    report.add_results(
        [
            CheckResult(name="demo", passed=True, details="ok"),
            CheckResult(name="demo2", passed=False, details="bad"),
        ]
    )
    text = format_report(report, verbose=True)
    assert "✔ demo" in text
    assert "✖ demo2" in text


def test_discover_profiles_loads_external_files(tmp_path):
    profile_file = tmp_path / "custom.json"
    profile_file.write_text(
        json.dumps(
            {
                "custom": {
                    "request": {"base_url": "https://example.com", "endpoint": "/foo"},
                    "expected_headers": [],
                    "response_expectations": {"status_codes": [200]},
                    "tls": {"min_version": "TLSv1.2", "allowed_cipher_substrings": ["AES"]},
                }
            }
        )
    )
    profiles = discover_profiles([str(profile_file)])
    assert "custom" in profiles


def test_format_profile_listing_lists_profiles():
    text = format_profile_listing(discover_profiles([]))
    assert "Available profiles:" in text
    assert "- accc:" in text

