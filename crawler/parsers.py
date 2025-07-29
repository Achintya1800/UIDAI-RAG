from __future__ import annotations
from bs4 import BeautifulSoup
from typing import Iterable, Optional, Dict, Any, List
import re

from .normalizers import parse_date_to_iso, parse_size_to_bytes, detect_filetype_from_url

# Given UIDAI lists are fairly uniform: a serial/number, a title link, a download link/button,
# a size and a date. This parser aims to be resilient by searching for anchors and nearby
# metadata rather than brittle classnames.

_ITEM_SELECTORS = [
    "li",              # ordered/unordered lists
    ".list-group-item",
    "tr",              # table rows
    ".views-row",      # drupal-like listing rows
    ".item, .document, .doc-item",
]

_SIZE_PAT = re.compile(r"\b(\d+(?:[.,]\d+)?)\s*(KB|MB|GB|B)\b", re.I)
_DATE_PAT = re.compile(r"\b(\d{1,2}[\-/ ]\w{3,9}[\-/ ]\d{2,4}|\d{1,2}[\-/ ]\d{1,2}[\-/ ]\d{2,4}|\w+\s+\d{1,2},\s*\d{4})\b")
_SERIAL_PAT = re.compile(r"^\s*(\d+)[).\-]\s*")


class ParsedItem(dict):
    """A normalized parsed item from a listing page."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setdefault("serial_no", None)
        self.setdefault("title", None)
        self.setdefault("doc_url", None)
        self.setdefault("download_url", None)
        self.setdefault("file_size_bytes", None)
        self.setdefault("file_type", None)
        self.setdefault("published_date", None)
        self.setdefault("updated_date", None)


def _extract_anchor_and_title(el) -> tuple[Optional[str], Optional[str]]:
    # Prefer anchors that look like document links (pdf/doc)
    anchors = el.select("a[href]")
    if not anchors:
        return None, None
    # Choose the longest text anchor as title heuristic
    best = max(anchors, key=lambda a: len(a.get_text(strip=True) or ""))
    href = best.get("href")
    title = best.get_text(strip=True)
    return href, title


def _extract_download_url(el) -> Optional[str]:
    # Sometimes there is an explicit download button/link separate from title
    a_tags = el.select('a[href*="download"], a[download], a[href$=".pdf"], a[href$=".doc"], a[href$=".docx"]')
    if a_tags:
        # Choose the one with "download" semantics or ending with known ext
        return a_tags[0].get("href")
    return None


def _extract_size(el) -> Optional[int]:
    text = el.get_text(" ", strip=True)
    m = _SIZE_PAT.search(text)
    if not m:
        return None
    return parse_size_to_bytes(m.group(0))


def _extract_date(el) -> Optional[str]:
    text = el.get_text(" ", strip=True)
    m = _DATE_PAT.search(text)
    if not m:
        return None
    return parse_date_to_iso(m.group(0))


def _extract_serial(el) -> Optional[str]:
    # Try the first text node or leading number patterns
    text = el.get_text(" ", strip=True)
    m = _serial_from_text(text)
    if m:
        return m
    # Check for cells (table layouts)
    first_cell = el.find(["td", "th"])
    if first_cell:
        return _serial_from_text(first_cell.get_text(" ", strip=True))
    return None


def _serial_from_text(text: str) -> Optional[str]:
    m = _SERIAL_PAT.search(text)
    if m:
        return m.group(1)
    return None


def parse_listing(html: str) -> List[ParsedItem]:
    soup = BeautifulSoup(html, "lxml")
    container_candidates = soup.select(", ".join(_ITEM_SELECTORS))
    items: List[ParsedItem] = []
    for el in container_candidates:
        # Heuristic: consider elements that contain at least one link
        if not el.select("a[href]"):
            continue
        doc_url, title = _extract_anchor_and_title(el)
        if not (doc_url and title):
            continue
        download_url = _extract_download_url(el) or doc_url
        file_size = _extract_size(el)
        date_iso = _extract_date(el)
        serial = _extract_serial(el)
        ftype = detect_filetype_from_url(download_url or doc_url)
        items.append(
            ParsedItem(
                serial_no=serial,
                title=title,
                doc_url=doc_url,
                download_url=download_url,
                file_size_bytes=file_size,
                file_type=ftype,
                published_date=date_iso,
                updated_date=None,
            )
        )
    # De-duplicate by (title, doc_url)
    uniq = {}
    for it in items:
        key = (it.get("title"), it.get("doc_url"))
        if key not in uniq:
            uniq[key] = it
    return list(uniq.values())