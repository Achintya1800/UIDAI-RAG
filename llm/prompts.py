from __future__ import annotations
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import List, Dict

IST = ZoneInfo("Asia/Kolkata")

SYSTEM_BASE = (
    "You are a precise assistant for a legal-information chatbot focused on UIDAI. "
    "Answer concisely (2–5 sentences) using only the provided document list and snippets. "
    "If the context is insufficient, say so and point the user to the listed documents. "
    "Do not hallucinate dates or titles. The current timezone is Asia/Kolkata."
)

TEMPLATE = """
## Response
{response_paragraph}

## Most Relevant Documents
{ranked_items}

## Information Source Website
UIDAI (uidai.gov.in)
"""


def format_ranked_items(items: List[Dict]) -> str:
    lines = []
    for i, d in enumerate(items, start=1):
        date_str = d.get("published_date").isoformat() if d.get("published_date") else ""
        size = d.get("file_size_bytes")
        size_str = f"{size} bytes" if size else ""
        meta = ", ".join([s for s in [date_str, d.get("file_type"), size_str] if s])
        url = d.get("doc_url") or d.get("download_url") or d.get("page_url")
        lines.append(f"{i}. {d.get('title','').strip()} — {meta} — {url}")
    return "\n".join(lines)


def build_messages(query: str, items: List[Dict], snippets: List[str]) -> list[dict]:
    today = datetime.now(IST).strftime("%Y-%m-%d")
    ranked_items_block = format_ranked_items(items)

    # Build a compact context string (titles + snippets)
    snippet_block = []
    for i, (d, snip) in enumerate(zip(items, snippets), start=1):
        if not snip:
            continue
        snippet_block.append(f"[{i}] {d.get('title','')}\n{snip.strip()}")
    snippet_text = "\n\n".join(snippet_block)

    user_content = (
        f"Date (IST): {today}\n"
        f"User query: {query}\n\n"
        f"Documents (ranked):\n{ranked_items_block}\n\n"
        f"Snippets (optional):\n{snippet_text}\n\n"
        "Write a 2–5 sentence Response that addresses the query, citing document titles in natural language where helpful. "
        "Then reproduce the exact three-section format as specified."
    )

    return [
        {"role": "system", "content": SYSTEM_BASE},
        {"role": "user", "content": user_content},
    ]


def render_output(response_paragraph: str, items: List[Dict]) -> str:
    return TEMPLATE.format(
        response_paragraph=response_paragraph.strip(),
        ranked_items=format_ranked_items(items),
    )