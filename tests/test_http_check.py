import datetime as dt
from types import SimpleNamespace

from cdrcsv.checks.http import HTTPResponseCheck
from cdrcsv.config import HTTPResponseExpectations


def _response(status: int, content_type: str | None, latency: float | None = None) -> SimpleNamespace:
    headers = {}
    if content_type is not None:
        headers["Content-Type"] = content_type
    elapsed = dt.timedelta(seconds=latency) if latency is not None else None
    return SimpleNamespace(status_code=status, headers=headers, elapsed=elapsed)


def test_http_response_check_validates_status_codes():
    check = HTTPResponseCheck(HTTPResponseExpectations(status_codes=(200, 201)))
    results = {result.name: result for result in check.run(response=_response(500, "application/json"))}
    assert results["http:status"].passed is False


def test_http_response_check_validates_content_type():
    check = HTTPResponseCheck(
        HTTPResponseExpectations(content_type_prefixes=("application/json",))
    )
    results = {result.name: result for result in check.run(response=_response(200, "text/plain"))}
    assert results["http:content-type"].passed is False


def test_http_response_check_validates_latency():
    check = HTTPResponseCheck(
        HTTPResponseExpectations(max_latency_seconds=0.2)
    )
    results = {result.name: result for result in check.run(response=_response(200, "application/json", latency=0.5))}
    assert results["http:latency"].passed is False

