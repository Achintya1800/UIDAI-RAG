from __future__ import annotations
import os
from typing import List
from urllib.parse import urljoin

from loguru import logger

from .client import make_session, polite_get
from .constants import SEED_URLS, SOURCE_CATEGORIES
from .parsers import parse_listing
from db.crud import upsert_documents


def run_scrape() -> int:
    session = make_session()
    total_saved = 0
    for url in SEED_URLS:
        logger.info(f"Fetching: {url}")
        resp = polite_get(session, url)
        if not resp:
            logger.warning(f"Failed to fetch: {url}")
            continue
        html = resp.text
        parsed = parse_listing(html)
        # Normalize absolute URLs
        base = resp.url
        for item in parsed:
            if item.get("doc_url"):
                item["doc_url"] = urljoin(base, item["doc_url"])  # type: ignore
            if item.get("download_url"):
                item["download_url"] = urljoin(base, item["download_url"])  # type: ignore
            item["page_url"] = url
            item["category"] = SOURCE_CATEGORIES.get(url, "Unknown")
        logger.info(f"Parsed {len(parsed)} items from {url}")
        saved = upsert_documents(parsed)
        total_saved += saved
        logger.info(f"Upserted {saved} items from {url}")
    logger.success(f"Scrape complete. Upserted total: {total_saved}")
    return total_saved