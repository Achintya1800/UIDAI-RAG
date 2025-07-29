from __future__ import annotations
import re
from dataclasses import dataclass
from datetime import date
from dateutil import parser as dateparser
from typing import List, Optional, Set

CATEGORY_SYNONYMS = {
    "rules": "Rules",
    "rule": "Rules",
    "regulation": "Regulations",
    "regulations": "Regulations",
    "notification": "Notifications",
    "notifications": "Notifications",
    "circular": "Circulars",
    "circulars": "Circulars",
}

DATE_TOKEN = re.compile(
    r"(?P<op>after|since|from|before|until|till|in)?\s*(?P<val>(?:\d{1,2}[\-/]\d{1,2}[\-/]\d{2,4})|(?:\d{4})|(?:\w+\s+\d{4}))",
    re.IGNORECASE,
)

LATEST_TOKENS = {"latest", "newest", "recent"}
UPDATED_TOKENS = {"updated", "amended", "revision", "revised"}


@dataclass
class ParsedQuery:
    raw: str
    keywords: List[str]
    categories: Set[str]
    date_from: Optional[date]
    date_to: Optional[date]
    want_latest: bool
    want_updated: bool


def _try_parse_date(val: str) -> Optional[date]:
    try:
        return dateparser.parse(val, dayfirst=True, default=None).date()
    except Exception:
        return None


def parse_query(q: str) -> ParsedQuery:
    text = q.strip()
    lowered = text.lower()

    categories: Set[str] = set()
    tokens = re.split(r"\W+", lowered)

    for t in tokens:
        if t in CATEGORY_SYNONYMS:
            categories.add(CATEGORY_SYNONYMS[t])

    want_latest = any(t in LATEST_TOKENS for t in tokens)
    want_updated = any(t in UPDATED_TOKENS for t in tokens)

    # Date windows
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    for m in DATE_TOKEN.finditer(lowered):
        op = (m.group("op") or "").lower()
        val = m.group("val")
        d = _try_parse_date(val)
        if not d and re.fullmatch(r"\d{4}", val):
            d = date(int(val), 1, 1)
            # If "in 2023" treat as year window
            if op == "in":
                date_from = d
                date_to = date(int(val), 12, 31)
                continue
        if not d:
            continue
        if op in ("after", "since", "from"):
            date_from = d
        elif op in ("before", "until", "till"):
            date_to = d
        elif op == "in":
            date_from = d
            date_to = d
        else:
            # standalone date -> assume "since"
            date_from = d

    # Keywords = remaining words that are not control tokens
    control = set(CATEGORY_SYNONYMS.keys()) | LATEST_TOKENS | UPDATED_TOKENS
    keywords = [t for t in tokens if t and t not in control and not re.fullmatch(r"\d{4}", t)]

    return ParsedQuery(
        raw=text,
        keywords=keywords,
        categories=categories,
        date_from=date_from,
        date_to=date_to,
        want_latest=want_latest,
        want_updated=want_updated,
    )