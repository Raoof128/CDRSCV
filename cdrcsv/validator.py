"""Validator orchestration logic."""

from __future__ import annotations

import logging

from .checks.base import CheckResult
from .checks.headers import HeaderCheck
from .checks.http import HTTPResponseCheck
from .checks.tls import TLSCheck
from .client import CDRClient
from .config import ValidatorProfile
from .report import ValidationReport


class CDRValidator:
    """Coordinates the HTTP call, header checks and TLS evaluation."""

    def __init__(self, profile: ValidatorProfile):
        self.profile = profile
        self.client = CDRClient(profile.request)
        self.response_check = HTTPResponseCheck(profile.response_expectations)
        self.header_check = HeaderCheck(profile.expected_headers)
        self.tls_check = TLSCheck(requirements=profile.tls)
        self.logger = logging.getLogger(self.__class__.__name__)

    def run(self) -> ValidationReport:
        url = self.profile.request.url()
        report = ValidationReport(target_url=url)
        self.logger.info("Validating %s", url)

        response = None
        try:
            response = self.client.send()
        except Exception as exc:  # pragma: no cover - network failure path
            self.logger.exception("HTTP request to %s failed", url)
            report.add_results(
                [
                    CheckResult(
                        name="http:request",
                        passed=False,
                        details=f"HTTP request failed: {exc}",
                    )
                ]
            )
            return report

        report.add_results(self.response_check.run(response=response))
        report.add_results(self.header_check.run(headers=response.headers))
        report.add_results(self.tls_check.run(url=url))
        self.logger.info("Validation finished with %s", "PASS" if report.passed else "FAIL")
        return report

