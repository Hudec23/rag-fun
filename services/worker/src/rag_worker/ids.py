"""IDs and time. Every id is a UUIDv7 string; every timestamp is UTC with millisecond precision."""

from collections.abc import Callable
from datetime import UTC, datetime

import uuid_utils

# Tests replace this (fixture `frozen_now`); code always calls utcnow().
_clock: Callable[[], datetime] = lambda: datetime.now(UTC)  # noqa: E731


def new_id() -> str:
    return str(uuid_utils.uuid7())


def utcnow() -> datetime:
    """Current UTC time truncated to milliseconds."""
    now = _clock()
    return now.replace(microsecond=(now.microsecond // 1000) * 1000)


def to_iso(dt: datetime) -> str:
    """'2026-11-01T18:22:05.123Z'."""
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"
