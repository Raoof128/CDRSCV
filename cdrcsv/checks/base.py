"""Common validation primitives."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class CheckResult:
    """Outcome of a single validation step."""

    name: str
    passed: bool
    details: str
    evidence: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        payload = {
            "name": self.name,
            "passed": self.passed,
            "details": self.details,
        }
        if self.evidence is not None:
            payload["evidence"] = self.evidence
        return payload


class Check:
    """Base class for validator checks."""

    name = "unnamed"

    def run(self, **kwargs: Any) -> CheckResult:  # pragma: no cover - interface
        raise NotImplementedError

