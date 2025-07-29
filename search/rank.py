from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo
from math import exp
from typing import Any, Dict, List

from .query_parser import parse_query, ParsedQuery
from .filters import categories_for_query
from .bm25 import BM25
from db.crud import fetch_documents

IST = ZoneInfo("Asia/Kolkata")

@dataclass
class RankedDoc:
    score: float
    doc: Dict[str, Any]


def _tokenize(text: str) -> List[str]:
    return [t.lower() for t in (text or "").split() if t]


def _normalize_scores(scores: List[float]) -> List[float]:
    if not scores:
        return []
    mx = max(scores) or 1.0
    return [s / mx for s in scores]


def _recency_score(d) -> float:
    if not d:
        return 0.1  # small baseline if no date known
    today = datetime.now(IST).date()
    age_days = (today - d).days
    if age_days < 0:
        age_days = 0
    half_life = 180.0  # ~6 months
    return exp(-age_days / half_life)


def rank_documents(q: ParsedQuery, candidates: List[Dict[str, Any]], top_k: int = 10):
    # Build BM25 corpus from title + category
    corpus = [
        _tokenize(f"{c.get('title','')} {c.get('category','')}") for c in candidates
    ]
    bm25 = BM25(corpus)
    query_tokens = q.keywords or _tokenize(q.raw)
    bm25_scores = _normalize_scores(bm25.get_scores(query_tokens))

    # Recency component
    rec_scores = [_recency_score(c.get("published_date")) for c in candidates]

    # Weighting: favor recency when "latest" is requested
    alpha = 0.4 if q.want_latest else 0.7
    combined = [alpha * b + (1 - alpha) * r for b, r in zip(bm25_scores, rec_scores)]

    ranked = sorted(zip(combined, candidates), key=lambda x: x[0], reverse=True)
    return [
        {**c, "score": round(s, 6)} for s, c in ranked[: top_k]
    ]


def search_ranked_documents(query_text: str, top_k: int = 10):
    q = parse_query(query_text)
    cats = categories_for_query(q)
    candidates = fetch_documents(categories=cats, date_from=q.date_from, date_to=q.date_to, limit=None)
    return rank_documents(q, candidates, top_k=top_k)