"""Reporting utilities."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from .checks.base import CheckResult


@dataclass(slots=True)
class ValidationReport:
    target_url: str
    check_results: list[CheckResult] = field(default_factory=list)

    def add_results(self, results: Iterable[CheckResult]) -> None:
        self.check_results.extend(results)

    @property
    def passed(self) -> bool:
        return all(result.passed for result in self.check_results)

    def as_dict(self) -> dict:
        return {
            "target_url": self.target_url,
            "passed": self.passed,
            "results": [result.as_dict() for result in self.check_results],
        }

