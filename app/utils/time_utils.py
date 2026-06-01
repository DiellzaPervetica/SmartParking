from __future__ import annotations

from datetime import datetime, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def floor_to_minute(dt: datetime) -> datetime:
    return dt.replace(second=0, microsecond=0)
