from __future__ import annotations
import os

# Load environment variables from .env
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware

from crawler.pipeline import run_scrape
from search.rank import search_ranked_documents
from llm.memory import AnswerMemory
from llm.answerer import build_answer, TOPK

from .schemas import (
    SearchRequest,
    SearchResponse,
    SearchDocument,
    AnswerRequest,
    AnswerResponse,
)

app = FastAPI(title="UIDAI RAG API", version="0.1.0")

# Allow frontend CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.post("/scrape")
async def scrape():
    total = run_scrape()
    return {"status": "ok", "upserted": total}

@app.post("/search", response_model=SearchResponse)
async def search(req: SearchRequest = Body(...)):
    ranked = search_ranked_documents(req.query, top_k=req.top_k)
    return SearchResponse(
        query=req.query,
        top_k=req.top_k,
        results=[SearchDocument(**d) for d in ranked],
    )

memory = AnswerMemory()

@app.post("/answer", response_model=AnswerResponse)
async def answer(req: AnswerRequest):
    global TOPK
    if req.top_k:
        os.environ["ANSWER_TOPK"] = str(req.top_k)
    result = build_answer(req.query, memory)
    return AnswerResponse(**result)
