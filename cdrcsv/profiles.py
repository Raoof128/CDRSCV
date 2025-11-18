"""Built-in validation profiles for common CDR targets."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

try:  # pragma: no cover - tomllib is always available on 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None  # type: ignore[assignment]

from .config import (
    HeaderExpectation,
    HTTPRequestConfig,
    HTTPResponseExpectations,
    TLSRequirements,
    ValidatorProfile,
)


def _cdr_default_headers() -> list[HeaderExpectation]:
    return [
        HeaderExpectation(
            name="x-v",
            pattern=r"^\d+$",
            description="CDR version requested by the client",
        ),
        HeaderExpectation(
            name="x-min-v",
            pattern=r"^\d+$",
            description="Minimum acceptable version",
        ),
        HeaderExpectation(
            name="x-fapi-interaction-id",
            pattern=r"^[0-9a-fA-F-]{8,}$",
            required=False,
            description="Unique request identifier propagated by the data holder",
        ),
        HeaderExpectation(
            name="x-fapi-customer-ip-address",
            pattern=r"^.+$",
            required=False,
            description="Customer IP address echo",
        ),
        HeaderExpectation(
            name="cache-control",
            pattern=r"^.+$",
            description="Response must be explicit about caching",
        ),
        HeaderExpectation(
            name="strict-transport-security",
            pattern=r"^max-age=\d+.*$",
            required=False,
            description="Enforce HTTPS",
        ),
    ]


BUILTIN_PROFILES: dict[str, ValidatorProfile] = {
    "accc": ValidatorProfile(
        name="accc",
        request=HTTPRequestConfig(),
        expected_headers=_cdr_default_headers(),
        response_expectations=HTTPResponseExpectations(
            status_codes=(200,),
            content_type_prefixes=("application/json",),
            max_latency_seconds=2.0,
        ),
        tls=TLSRequirements(
            min_version="TLSv1.2",
            allowed_cipher_substrings=("ECDHE", "AES", "GCM"),
        ),
    )
}


def _load_mapping_from_file(path: Path) -> Mapping[str, object]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return json.loads(path.read_text())
    if suffix == ".toml":
        if tomllib is None:  # pragma: no cover - fallback for older versions
            raise RuntimeError("tomllib is required to parse TOML profile files")
        with path.open("rb") as handle:
            return tomllib.load(handle)
    raise ValueError(f"Unsupported profile file format: {path.suffix}")


def load_profiles_from_file(path: Path) -> dict[str, ValidatorProfile]:
    """Load ValidatorProfile objects from a JSON or TOML file."""

    if not path.exists():
        raise FileNotFoundError(f"Profile file '{path}' does not exist")

    raw_mapping = _load_mapping_from_file(path)
    if not isinstance(raw_mapping, Mapping):
        raise ValueError("Profile file must define a mapping of profiles")

    profiles: dict[str, ValidatorProfile] = {}
    for name, payload in raw_mapping.items():
        if not isinstance(payload, Mapping):
            raise ValueError(f"Profile '{name}' must be a mapping of sections")
        profiles[name] = ValidatorProfile.from_dict(name, payload)
    return profiles


__all__ = ["BUILTIN_PROFILES", "load_profiles_from_file"]

