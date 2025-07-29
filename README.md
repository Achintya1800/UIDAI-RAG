# UIDAI-RAG Chatbot 🤖📚

Retrieval-Augmented-Generation system that answers questions about **UIDAI**
(Unique Identification Authority of India) legal documents—rules, regulations,
notifications, circulars, etc.—with cited sources and a concise summary.

*Built with Python 3.11, FastAPI, SQLite, FAISS, BM25 and **Google Gemini**.*

---

## 📑 Table of Contents
1. [Motivation](#motivation)
2. [Key Features](#key-features)
3. [Architecture Overview](#architecture-overview)
4. [Tech Stack](#tech-stack)
5. [Data Flow](#data-flow)
6. [Getting Started](#getting-started)
7. [Environment Variables](#environment-variables)
8. [CLI & Scripts](#cli--scripts)
9. [API Reference](#api-reference)
10. [Streamlit UI](#streamlit-ui)
11. [Development Workflow](#development-workflow)
12. [Testing](#testing)
13. [Deployment Options](#deployment-options)
14. [Troubleshooting / FAQ](#troubleshooting--faq)
15. [Project Roadmap](#project-roadmap)
16. [Contributing](#contributing)
17. [License](#license)

---

## Motivation
UIDAI publishes dozens of legal artefacts across several sections.  
Manually searching PDF tables or website lists is slow & error-prone.
**UIDAI-RAG** automatically:

* Scrapes & normalises all legal docs.
* Ranks most relevant items (lexical + recency).
* Generates an _answer + citations_ with Gemini.
* Stores answers in FAISS for fast recall.

---

## Key Features
| Layer        | Details                                                                                   |
|--------------|-------------------------------------------------------------------------------------------|
| **Scraper**  | Resilient (timeout, retries, polite delay) — harvests 800 + docs across 8 UIDAI pages     |
| **Database** | Normalised SQLite (docs, hashes, dates, bytes, category)                                  |
| **Ranker**   | BM25Okapi (`rank-bm25`) + exponential date boost                                          |
| **LLM**      | Google Gemini *gemini-pro* (`generate_content`)                                           |
| **Embeds**   | Gemini *embedding-001* (1536-D) → FAISS FlatIP                                            |
| **RAG**      | Stores every Q→A vector to avoid re-generating identical questions                        |
| **API**      | FastAPI 3-endpoint backend (`/scrape`, `/search`, `/answer`)                              |
| **UI**       | Streamlit front-end renders: **Answer ∙ Top Docs ∙ Source site**                          |
| **Scheduler**| Optional cron / GH Actions for nightly scrape + weekly re-index                           |

---

## Architecture Overview

```text
┌──────────────┐  scrape   ┌───────────────┐  rank  ┌────────────────┐
│ UIDAI Site   │──────────▶│  SQLite DB    │──────▶│  BM25 + Date   │
└──────────────┘           │  (documents)  │       │  Fusion        │
        ▲                  └──────┬────────┘       └──────┬─────────┘
        │                         │ upsert                │ top-k docs
        │                         ▼                       │
┌───────┴────────┐   embed   ┌──────────────┐ generate  ┌────────────┐
│  FAISS Index   │◀──────────│  Gemini LLM  │──────────▶│  3-Block   │
│  (answers)     │           └──────────────┘           │  Answer    │
└────────────────┘                                       └────────────┘
