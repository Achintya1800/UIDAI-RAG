from __future__ import annotations
from typing import List
from rank_bm25 import BM25Okapi


class BM25:
    def __init__(self, documents: List[List[str]]):
        # documents is a list of token lists
        self.model = BM25Okapi(documents)
        self.max_idf = max(self.model.idf.values()) if self.model.idf else 1.0

    def get_scores(self, query_tokens: List[str]) -> List[float]:
        # Raw BM25 scores (unbounded); we will normalize later
        return list(self.model.get_scores(query_tokens))