from __future__ import annotations
import os
from typing import List, Dict
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from pypdf import PdfReader

from search.rank import search_ranked_documents
from .prompts import build_messages
from .gemini_client import chat
from .memory import AnswerMemory

IST = ZoneInfo("Asia/Kolkata")
TOPK = int(os.getenv("ANSWER_TOPK", "6"))
MAX_SNIP = int(os.getenv("ANSWER_MAX_SNIPPET_CHARS", "1200"))

_session = requests.Session()


def _safe_fetch_snippet(url: str) -> str:
    try:
        r = _session.get(url, timeout=20)
        r.raise_for_status()
        if r.headers.get("content-type", "").lower().startswith("application/pdf") or url.lower().endswith(".pdf"):
            reader = PdfReader(io.BytesIO(r.content))  # type: ignore
            text = "\n".join(page.extract_text() or "" for page in reader.pages[:1])
        else:
            # fallback: naive text from bytes
            text = r.text
        return (text or "").strip()[:MAX_SNIP]
    except Exception:
        return ""


def build_answer(query: str, memory: AnswerMemory) -> Dict:
    # 1) Get top documents
    docs = search_ranked_documents(query, top_k=TOPK)

    # 2) Optional snippets (best effort, PDF-first-page or HTML text)
    snippets: List[str] = []
    for d in docs:
        url = d.get("doc_url") or d.get("download_url")
        if url:
            snippets.append("")  # disabled by default for speed; enable if required
            # snippets.append(_safe_fetch_snippet(url))
        else:
            snippets.append("")

    # 3) Build LLM prompt and get the 3-block formatted content
    messages = build_messages(query, docs, snippets)
    content = chat(messages, temperature=0.2)

    # 4) Persist answer (embeddings of answers only)
    memory.add_answer(query, content, [d["id"] for d in docs])

    return {
        "content": content,
        "documents": docs,
        "source_site": "UIDAI (uidai.gov.in)",
    }