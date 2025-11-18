"""HTTP response validation."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import timedelta

from requests import Response

from ..config import HTTPResponseExpectations
from .base import CheckResult


class HTTPResponseCheck:
    """Ensure the HTTP response matches the configured expectations."""

    name = "HTTP response"

    def __init__(self, expectations: HTTPResponseExpectations):
        self.expectations = expectations

    def run(self, *, response: Response) -> list[CheckResult]:
        return [
            self._check_status(response.status_code),
            self._check_content_type(response.headers.get("Content-Type")),
            self._check_latency(getattr(response, "elapsed", None)),
        ]

    def _check_status(self, status: int) -> CheckResult:
        allowed = self.expectations.status_codes
        passed = self.expectations.allows_status(status)
        detail_suffix = "" if allowed else " (no explicit requirements)"
        details = f"Status code {status}{detail_suffix}"
        if not passed and allowed:
            allowed_str = ", ".join(str(code) for code in allowed)
            details = f"Status code {status} is not in allowed set ({allowed_str})"

        return CheckResult(
            name="http:status",
            passed=passed,
            details=details,
            evidence={"status_code": status, "allowed": list(allowed)},
        )

    def _check_content_type(self, header_value: str | None) -> CheckResult:
        prefixes: Sequence[str] = self.expectations.content_type_prefixes
        passed = self.expectations.allows_content_type(header_value)

        if not prefixes:
            details = "No Content-Type requirement configured"
        elif header_value is None:
            details = "Content-Type header is missing"
        else:
            details = f"Content-Type is '{header_value}'"

        if prefixes and header_value:
            allowed = ", ".join(prefixes)
            details += f" (required prefixes: {allowed})"

        return CheckResult(
            name="http:content-type",
            passed=passed,
            details=details,
            evidence={
                "content_type": header_value,
                "required_prefixes": list(prefixes),
            },
        )

    def _check_latency(self, elapsed: timedelta | None) -> CheckResult:
        observed = elapsed.total_seconds() if isinstance(elapsed, timedelta) else None
        max_latency = self.expectations.max_latency_seconds
        passed = self.expectations.allows_latency(observed)

        if max_latency is None:
            details = "No latency requirement configured"
        elif observed is None:
            details = "Latency measurement unavailable"
        else:
            details = f"Latency {observed:.3f}s (max {max_latency:.3f}s)"

        return CheckResult(
            name="http:latency",
            passed=passed,
            details=details,
            evidence={"latency_seconds": observed, "max_latency_seconds": max_latency},
        )

