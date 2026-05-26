from __future__ import annotations

from datetime import datetime, tzinfo
from zoneinfo import ZoneInfo


LOCAL_TIMEZONE_ALIASES = {"", "auto", "local", "system"}


def is_local_timezone(timezone_name: str | None) -> bool:
    return (timezone_name or "").strip().lower() in LOCAL_TIMEZONE_ALIASES


def resolve_timezone(timezone_name: str | None) -> tzinfo:
    if is_local_timezone(timezone_name):
        return datetime.now().astimezone().tzinfo or ZoneInfo("UTC")
    return ZoneInfo(str(timezone_name))


def timezone_label(timezone_name: str | None) -> str:
    if is_local_timezone(timezone_name):
        current = datetime.now().astimezone()
        name = current.tzname() or current.strftime("%z")
        return f"local system timezone ({name})"
    return str(timezone_name)
