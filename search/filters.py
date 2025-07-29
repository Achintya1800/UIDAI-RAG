from __future__ import annotations
from typing import Sequence

from .query_parser import ParsedQuery

# If "updated" is requested with a category, we also include the corresponding
# "Updated <Category>" bucket in filters (if present in our DB categories).
UPDATED_CATEGORY_MAP = {
    "Rules": "Updated Rules",
    "Regulations": "Updated Regulations",
}


def categories_for_query(q: ParsedQuery) -> Sequence[str] | None:
    if not q.categories:
        return None
    cats = set(q.categories)
    if q.want_updated:
        for c in list(q.categories):
            updated = UPDATED_CATEGORY_MAP.get(c)
            if updated:
                cats.add(updated)
    return list(cats)