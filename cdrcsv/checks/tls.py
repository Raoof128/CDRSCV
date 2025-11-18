"""TLS posture inspection."""

from __future__ import annotations

import datetime as dt
import socket
import ssl
from collections.abc import Mapping
from dataclasses import dataclass
from urllib.parse import urlparse

from ..config import TLSRequirements
from .base import CheckResult


@dataclass(slots=True)
class TLSInspection:
    version: str | None
    cipher: str | None
    not_before: str | None
    not_after: str | None


class TLSInspector:
    """Perform a raw TLS handshake to gather metadata."""

    def __init__(self, *, timeout: float = 5.0):
        self.timeout = timeout

    def inspect(self, url: str) -> TLSInspection:
        parsed = urlparse(url)
        host = parsed.hostname
        port = parsed.port or 443
        if not host:
            raise ValueError(f"Cannot determine host from URL '{url}'")

        context = ssl.create_default_context()
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED

        with socket.create_connection((host, port), timeout=self.timeout) as sock:
            with context.wrap_socket(sock, server_hostname=host) as secure_sock:
                version = secure_sock.version()
                cipher_info = secure_sock.cipher()
                cipher = cipher_info[0] if cipher_info else None
                cert = secure_sock.getpeercert()

        not_before: str | None = None
        not_after: str | None = None
        if isinstance(cert, Mapping):
            not_before_value = cert.get("notBefore")
            if isinstance(not_before_value, str):
                not_before = not_before_value
            not_after_value = cert.get("notAfter")
            if isinstance(not_after_value, str):
                not_after = not_after_value

        return TLSInspection(
            version=version,
            cipher=cipher,
            not_before=not_before,
            not_after=not_after,
        )


class TLSCheck:
    """Validate TLS properties against the FAPI requirements."""

    name = "TLS posture"

    def __init__(self, *, requirements: TLSRequirements, inspector: TLSInspector | None = None):
        self.requirements = requirements
        self.inspector = inspector or TLSInspector()

    def run(self, *, url: str) -> list[CheckResult]:
        results: list[CheckResult] = []

        try:
            inspection = self.inspector.inspect(url)
        except Exception as exc:  # pragma: no cover - network failure path
            results.append(
                CheckResult(
                    name="tls:handshake",
                    passed=False,
                    details=f"Failed to perform TLS handshake: {exc}",
                )
            )
            return results

        results.append(self._check_version(inspection))
        results.append(self._check_cipher(inspection))
        results.append(self._check_certificate(inspection))
        return results

    def _check_version(self, inspection: TLSInspection) -> CheckResult:
        min_version = self.requirements.min_version
        if inspection.version is None:
            return CheckResult(
                name="tls:version",
                passed=False,
                details="TLS version was not negotiated",
                evidence={"version": inspection.version, "min_version": min_version},
            )

        passed = self._version_cmp(inspection.version, min_version) >= 0
        return CheckResult(
            name="tls:version",
            passed=passed,
            details=f"TLS version negotiated: {inspection.version} (min {min_version})",
            evidence={"version": inspection.version, "min_version": min_version},
        )

    def _check_cipher(self, inspection: TLSInspection) -> CheckResult:
        allowed = self.requirements.allowed_cipher_substrings
        cipher = inspection.cipher or ""
        passed = bool(cipher) and any(part.upper() in cipher.upper() for part in allowed)
        return CheckResult(
            name="tls:cipher",
            passed=passed,
            details=f"Cipher suite: {cipher} (required fragments: {', '.join(allowed)})",
            evidence={"cipher": cipher},
        )

    def _check_certificate(self, inspection: TLSInspection) -> CheckResult:
        not_after = inspection.not_after
        passed = True
        details = "Certificate validity information unavailable"
        evidence = {"not_after": not_after, "not_before": inspection.not_before}

        if not_after:
            expires = dt.datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").replace(
                tzinfo=dt.UTC
            )
            now = dt.datetime.now(tz=dt.UTC)
            passed = expires > now
            details = f"Certificate expires {expires.isoformat()} UTC"

        return CheckResult(name="tls:certificate", passed=passed, details=details, evidence=evidence)

    @staticmethod
    def _version_cmp(actual: str, minimum: str) -> int:
        order = {"TLSv1": 1, "TLSv1.1": 2, "TLSv1.2": 3, "TLSv1.3": 4}
        return order.get(actual, 0) - order.get(minimum, 0)

