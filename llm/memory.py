from __future__ import annotations
import os
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Dict, Any, Optional

import numpy as np
import faiss

from .gemini_client import embed_text, embed_texts

DATA_DIR = os.getenv("DATA_DIR", "data")
INDEX_PATH = os.path.join(DATA_DIR, "answers.faiss")
META_PATH = os.path.join(DATA_DIR, "answers_meta.jsonl")


def _l2_normalize(vecs: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-12
    return vecs / norms


@dataclass
class AnswerMeta:
    idx: int
    question: str
    answer: str
    doc_ids: List[int]
    created_at: str


class AnswerMemory:
    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        self.index: Optional[faiss.IndexFlatIP] = None
        self.dim: Optional[int] = None
        self.next_idx: int = 0
        self.meta: Dict[int, AnswerMeta] = {}
        self._load()

    def _load(self):
        # Load meta
        if os.path.exists(META_PATH):
            with open(META_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    obj = json.loads(line)
                    m = AnswerMeta(**obj)
                    self.meta[m.idx] = m
                    self.next_idx = max(self.next_idx, m.idx + 1)
        # Load FAISS index if present
        if os.path.exists(INDEX_PATH):
            self.index = faiss.read_index(INDEX_PATH)  # cosine via IP with normalized vectors
            self.dim = self.index.d

    def _ensure_index(self, dim: int):
        if self.index is None:
            self.index = faiss.IndexFlatIP(dim)  # inner product
            self.dim = dim

    def add_answer(self, question: str, answer: str, doc_ids: List[int]):
        # Embed only the answer (persisted). Query embedding will be computed on the fly later.
        emb = np.array([embed_text(answer)], dtype="float32")
        emb = _l2_normalize(emb)
        self._ensure_index(emb.shape[1])
        idx = self.next_idx
        self.index.add(emb)
        meta = AnswerMeta(
            idx=idx,
            question=question,
            answer=answer,
            doc_ids=doc_ids,
            created_at=datetime.utcnow().isoformat() + "Z",
        )
        self.meta[idx] = meta
        self.next_idx += 1
        # Persist
        faiss.write_index(self.index, INDEX_PATH)
        with open(META_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(meta), ensure_ascii=False) + "\n")

    def search_similar(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        if self.index is None or self.index.ntotal == 0:
            return []
        q = np.array([embed_text(query)], dtype="float32")
        q = _l2_normalize(q)
        scores, ids = self.index.search(q, k)
        out: List[Dict[str, Any]] = []
        for score, idx in zip(scores[0], ids[0]):
            if idx == -1:
                continue
            m = self.meta.get(int(idx))
            if not m:
                continue
            out.append({"score": float(score), **asdict(m)})
        return out