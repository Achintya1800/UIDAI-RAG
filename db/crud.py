from __future__ import annotations
import hashlib
from typing import Iterable, List, Dict, Any
from datetime import date

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .session import SessionLocal, engine
from .models import Base, Document


def create_all():
    Base.metadata.create_all(bind=engine)


def _compute_hash(item: Dict[str, Any]) -> str:
    # Hash the fields that matter for change detection
    s = "|".join([
        str(item.get("title") or ""),
        str(item.get("doc_url") or ""),
        str(item.get("download_url") or ""),
        str(item.get("file_size_bytes") or ""),
        str(item.get("published_date") or ""),
        str(item.get("updated_date") or ""),
    ])
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def upsert_documents(items: Iterable[Dict[str, Any]]) -> int:
    count = 0
    with SessionLocal() as db:
        for raw in items:
            content_hash = _compute_hash(raw)
            title = (raw.get("title") or "").strip()
            doc_url = (raw.get("doc_url") or "").strip() or None

            # Try to find existing
            stmt = select(Document).where(Document.title == title, Document.doc_url == doc_url)
            existing = db.execute(stmt).scalars().first()

            if existing:
                if existing.content_hash != content_hash:
                    existing.category = raw.get("category")
                    existing.serial_no = raw.get("serial_no")
                    existing.page_url = raw.get("page_url")
                    existing.download_url = raw.get("download_url")
                    existing.file_type = raw.get("file_type")
                    existing.file_size_bytes = raw.get("file_size_bytes")
                    existing.published_date = _to_date(raw.get("published_date"))
                    existing.updated_date = _to_date(raw.get("updated_date"))
                    existing.content_hash = content_hash
                    db.add(existing)
            else:
                doc = Document(
                    category=raw.get("category"),
                    serial_no=raw.get("serial_no"),
                    title=title,
                    page_url=raw.get("page_url"),
                    doc_url=doc_url,
                    download_url=raw.get("download_url"),
                    file_type=raw.get("file_type"),
                    file_size_bytes=raw.get("file_size_bytes"),
                    published_date=_to_date(raw.get("published_date")),
                    updated_date=_to_date(raw.get("updated_date")),
                    content_hash=content_hash,
                )
                db.add(doc)
                count += 1
        db.commit()
    return count


def _to_date(s):
    if not s:
        return None
    try:
        # accept YYYY-MM-DD strings
        return date.fromisoformat(str(s))
    except Exception:
        return None
    
    # --- Phase 2 additions ---
from typing import Optional, Sequence
from sqlalchemy import and_, or_
from datetime import date


def fetch_documents(
    categories: Optional[Sequence[str]] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    limit: Optional[int] = None,
):
    """Load candidate documents for search with optional filters.
    Returns a list[dict] with primitive fields for ranking.
    """
    results = []
    with SessionLocal() as db:
        stmt = select(Document)
        conds = []
        if categories:
            conds.append(Document.category.in_(list(categories)))
        if date_from:
            conds.append(Document.published_date >= date_from)
        if date_to:
            conds.append(Document.published_date <= date_to)
        if conds:
            stmt = stmt.where(and_(*conds))
        if limit:
            stmt = stmt.limit(limit)
        for row in db.execute(stmt).scalars():
            results.append(
                {
                    "id": row.id,
                    "category": row.category,
                    "serial_no": row.serial_no,
                    "title": row.title,
                    "page_url": row.page_url,
                    "doc_url": row.doc_url,
                    "download_url": row.download_url,
                    "file_type": row.file_type,
                    "file_size_bytes": row.file_size_bytes,
                    "published_date": row.published_date,  # date or None
                    "updated_date": row.updated_date,
                }
            )
    return results