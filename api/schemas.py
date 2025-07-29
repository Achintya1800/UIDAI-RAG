from __future__ import annotations
from typing import Optional, List
from datetime import date
from pydantic import BaseModel, Field

class SearchRequest(BaseModel):
    query: str = Field(..., description="User query text")
    top_k: int = Field(10, ge=1, le=50)

class SearchDocument(BaseModel):
    id: int
    category: Optional[str] = None
    serial_no: Optional[str] = None
    title: str
    page_url: Optional[str] = None
    doc_url: Optional[str] = None
    download_url: Optional[str] = None
    file_type: Optional[str] = None
    file_size_bytes: Optional[int] = None
    published_date: Optional[date] = None
    updated_date: Optional[date] = None
    score: float

class SearchResponse(BaseModel):
    query: str
    top_k: int
    results: List[SearchDocument]

# --- Phase 3 additions ---
from pydantic import BaseModel, Field
from typing import List

class AnswerRequest(BaseModel):
    query: str = Field(..., description="User query text")
    top_k: int | None = None  # optional override

class AnswerResponse(BaseModel):
    content: str  # pre-formatted 3-section text
    source_site: str
    documents: List[SearchDocument]  # reuse document shape with scores