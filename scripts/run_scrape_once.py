from __future__ import annotations
from crawler.pipeline import run_scrape

if __name__ == "__main__":
    total = run_scrape()
    print(f"[OK] Scrape finished. Upserted: {total}")