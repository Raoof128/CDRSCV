"""HTTP client helper for the validator."""

from __future__ import annotations

import logging
from collections.abc import Mapping

import requests

from .config import HTTPRequestConfig


class CDRClient:
    """Small wrapper around `requests` with defaults for the CDR sandbox."""

    def __init__(self, config: HTTPRequestConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

    def send(self) -> requests.Response:
        method = self.config.method.upper()
        url = self.config.url()
        headers: Mapping[str, str] = {
            "Accept": "application/json",
            **self.config.headers,
        }
        self.logger.debug("Sending %s request to %s", method, url)
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            timeout=self.config.timeout,
        )
        elapsed = getattr(response, "elapsed", None)
        duration = elapsed.total_seconds() if elapsed else None
        self.logger.debug(
            "Received %s response in %.3fs",
            response.status_code,
            duration if duration is not None else -1,
        )
        return response

