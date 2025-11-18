"""HTTP header validation."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping

from ..config import HeaderExpectation
from .base import Check, CheckResult


class HeaderCheck(Check):
    """Ensure that required CDR/FAPI headers are present and well-formed."""

    name = "HTTP headers"

    def __init__(self, expectations: Iterable[HeaderExpectation]):
        self.expectations = list(expectations)

    def run(self, *, headers: Mapping[str, str]) -> list[CheckResult]:
        normalized = {k.lower(): v for k, v in headers.items()}
        results: list[CheckResult] = []

        for expectation in self.expectations:
            key = expectation.normalized_name()
            value = normalized.get(key)
            evidence = {"header": expectation.name, "expected_pattern": expectation.pattern}

            if value is None:
                if expectation.required:
                    results.append(
                        CheckResult(
                            name=f"header:{expectation.name}",
                            passed=False,
                            details=f"Missing required header '{expectation.name}'",
                            evidence=evidence,
                        )
                    )
                else:
                    results.append(
                        CheckResult(
                            name=f"header:{expectation.name}",
                            passed=True,
                            details=f"Optional header '{expectation.name}' absent",
                            evidence=evidence,
                        )
                    )
                continue

            if not re.match(expectation.pattern, value):
                results.append(
                    CheckResult(
                        name=f"header:{expectation.name}",
                        passed=False,
                        details=(
                            f"Header '{expectation.name}' value '{value}' does not match pattern "
                            f"{expectation.pattern!r}"
                        ),
                        evidence={**evidence, "value": value},
                    )
                )
                continue

            details = f"Header '{expectation.name}' present"
            if expectation.description:
                details += f" ({expectation.description})"

            results.append(
                CheckResult(
                    name=f"header:{expectation.name}",
                    passed=True,
                    details=details,
                    evidence={**evidence, "value": value},
                )
            )

        return results

