from cdrcsv.checks.headers import HeaderCheck
from cdrcsv.config import HeaderExpectation


def test_header_check_detects_missing_headers():
    expectations = [
        HeaderExpectation(name="x-v", pattern=r"^\d+$"),
        HeaderExpectation(name="cache-control", pattern=r"^.+$", required=False),
    ]
    check = HeaderCheck(expectations)

    results = check.run(headers={"X-V": "3"})

    passed = {result.name: result.passed for result in results}
    assert passed["header:x-v"] is True
    assert passed["header:cache-control"] is True  # optional header


def test_header_check_detects_invalid_pattern():
    expectations = [HeaderExpectation(name="x-min-v", pattern=r"^\d+$")]
    check = HeaderCheck(expectations)
    results = check.run(headers={"x-min-v": "abc"})
    assert results[0].passed is False

