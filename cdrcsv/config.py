"""Runtime configuration models."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, cast


@dataclass(slots=True)
class HeaderExpectation:
    """Expectation for a single HTTP response header."""

    name: str
    pattern: str
    required: bool = True
    description: str | None = None

    def normalized_name(self) -> str:
        return self.name.lower()


@dataclass(slots=True)
class HTTPRequestConfig:
    """Settings for the HTTP call made against the target endpoint."""

    method: str = "GET"
    base_url: str = "https://sandbox.api.consumerdatastandards.gov.au"
    endpoint: str = "/cds-au/v1/banking/products"
    headers: Mapping[str, str] = field(default_factory=dict)
    timeout: float = 10.0

    def url(self) -> str:
        base = self.base_url.rstrip("/")
        endpoint = self.endpoint
        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint
        return f"{base}{endpoint}"


@dataclass(slots=True)
class HTTPResponseExpectations:
    """Expected properties of the HTTP response."""

    status_codes: tuple[int, ...] = (200,)
    content_type_prefixes: tuple[str, ...] = ("application/json",)
    max_latency_seconds: float | None = None

    def allows_status(self, status_code: int) -> bool:
        return not self.status_codes or status_code in self.status_codes

    def allows_content_type(self, content_type: str | None) -> bool:
        if not self.content_type_prefixes:
            return True
        if not content_type:
            return False
        lowered = content_type.lower()
        return any(lowered.startswith(prefix.lower()) for prefix in self.content_type_prefixes)

    def allows_latency(self, observed_seconds: float | None) -> bool:
        if self.max_latency_seconds is None:
            return True
        if observed_seconds is None:
            return False
        return observed_seconds <= self.max_latency_seconds


@dataclass(slots=True)
class TLSRequirements:
    """Minimum TLS posture the endpoint must satisfy."""

    min_version: str = "TLSv1.2"
    allowed_cipher_substrings: Iterable[str] = field(
        default_factory=lambda: ("ECDHE", "AES", "GCM")
    )
    require_ocsp_stapling: bool = False


@dataclass(slots=True)
class ValidatorProfile:
    """Aggregated configuration for a validation run."""

    name: str
    request: HTTPRequestConfig
    expected_headers: list[HeaderExpectation]
    response_expectations: HTTPResponseExpectations = field(
        default_factory=HTTPResponseExpectations
    )
    tls: TLSRequirements = field(default_factory=TLSRequirements)

    @classmethod
    def from_dict(cls, name: str, data: Mapping[str, object]) -> ValidatorProfile:
        request_data = cast(Mapping[str, Any], data.get("request", {}))
        headers_data = cast(Sequence[Mapping[str, Any]], data.get("expected_headers", []))
        response_data = cast(
            Mapping[str, Any], data.get("response_expectations", {})
        )
        tls_data = cast(Mapping[str, Any], data.get("tls", {}))

        request = HTTPRequestConfig(**request_data)
        header_expectations = [HeaderExpectation(**item) for item in headers_data]
        response_expectations = HTTPResponseExpectations(**response_data)
        tls_req = TLSRequirements(**tls_data)

        return cls(
            name=name,
            request=request,
            expected_headers=header_expectations,
            response_expectations=response_expectations,
            tls=tls_req,
        )


def headers_from_mapping(mapping: Mapping[str, str]) -> list[HeaderExpectation]:
    return [HeaderExpectation(name=k, pattern=v) for k, v in mapping.items()]

