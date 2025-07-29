from __future__ import annotations
import os
import time
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DEFAULT_TIMEOUT = float(os.getenv("HTTP_TIMEOUT_SECONDS", "20"))
MAX_RETRIES = int(os.getenv("HTTP_MAX_RETRIES", "3"))
BACKOFF_FACTOR = float(os.getenv("HTTP_BACKOFF_FACTOR", "0.5"))
REQUEST_DELAY = float(os.getenv("SCRAPER_REQUEST_DELAY_SECONDS", "0.5"))
USER_AGENT = os.getenv("HTTP_USER_AGENT", "uidai-rag-scraper/1.0")

class TimeoutHTTPAdapter(HTTPAdapter):
    def __init__(self, *args, **kwargs):
        self.timeout = kwargs.pop("timeout", DEFAULT_TIMEOUT)
        super().__init__(*args, **kwargs)

    def send(self, request, **kwargs):
        kwargs.setdefault("timeout", self.timeout)
        return super().send(request, **kwargs)


def make_session() -> requests.Session:
    session = requests.Session()
    retries = Retry(
        total=MAX_RETRIES,
        backoff_factor=BACKOFF_FACTOR,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET"]),
        raise_on_status=False,
    )
    adapter = TimeoutHTTPAdapter(max_retries=retries, timeout=DEFAULT_TIMEOUT)
    session.headers.update({"User-Agent": USER_AGENT})
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def polite_get(session: requests.Session, url: str) -> Optional[requests.Response]:
    time.sleep(REQUEST_DELAY)
    resp = session.get(url)
    if resp.status_code >= 400:
        return None
    return resp