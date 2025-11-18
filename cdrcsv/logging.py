"""Logging helpers."""

from __future__ import annotations

import logging

LOG_LEVELS: tuple[str, ...] = ("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG")


def configure_logging(level: str = "WARNING") -> None:
    """Initialize the root logger with a consistent format."""

    normalized = level.upper()
    if normalized not in LOG_LEVELS:
        raise ValueError(f"Unsupported log level '{level}'")

    logging.basicConfig(
        level=getattr(logging, normalized),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

