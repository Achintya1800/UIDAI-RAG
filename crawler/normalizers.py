from __future__ import annotations
import re
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional

from dateutil import parser as dateparser

IST = ZoneInfo("Asia/Kolkata")

_SIZE_RE = re.compile(r"(?P<value>\d+(?:[.,]\d+)?)\s*(?P<unit>KB|MB|GB|B)\b", re.IGNORECASE)
_FILETYPE_RE = re.compile(r"\.([A-Za-z0-9]{1,6})$")
_DATE_CLEAN_RE = re.compile(r"\s+")


def parse_date_to_iso(s: str | None) -> Optional[str]:
    if not s:
        return None
    s = _DATE_CLEAN_RE.sub(" ", s.strip())
    try:
        dt = dateparser.parse(s, dayfirst=True)
        if not dt:
            return None
        # Ensure timezone is IST and drop time
        dt = dt.astimezone(IST) if dt.tzinfo else dt.replace(tzinfo=IST)
        return dt.date().isoformat()
    except Exception:
        return None


def parse_size_to_bytes(s: str | None) -> Optional[int]:
    if not s:
        return None
    m = _SIZE_RE.search(s)
    if not m:
        return None
    value = float(m.group("value").replace(",", "."))
    unit = m.group("unit").upper()
    if unit == "B":
        mult = 1
    elif unit == "KB":
        mult = 1024
    elif unit == "MB":
        mult = 1024 ** 2
    elif unit == "GB":
        mult = 1024 ** 3
    else:
        mult = 1
    return int(value * mult)


def detect_filetype_from_url(url: str | None) -> Optional[str]:
    if not url:
        return None
    m = _FILETYPE_RE.search(url)
    if not m:
        return None
    return m.group(1).lower()