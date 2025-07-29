from __future__ import annotations
import os
from typing import List, Dict, Any
import google.generativeai as genai

CHAT_MODEL = os.getenv("GEMINI_CHAT_MODEL", "gemini-1.5-flash")
EMB_MODEL = os.getenv("GEMINI_EMBED_MODEL", "models/text-embedding-004")

_api_key = os.getenv("GOOGLE_API_KEY")
if not _api_key:
    raise RuntimeError("GOOGLE_API_KEY not set in env")

genai.configure(api_key=_api_key)

# --- Chat helper ----------------------------------------------------------

def chat(messages: List[Dict[str, str]], temperature: float = 0.2, max_tokens: int | None = None) -> str:
    prompt_parts = []
    for m in messages:
        role = m["role"]
        content = m["content"].strip()
        if role == "system":
            prompt_parts.append(f"System: {content}")
        elif role == "user":
            prompt_parts.append(f"User: {content}")
        else:
            prompt_parts.append(f"Assistant: {content}")
    
    full_prompt = "\n\n".join(prompt_parts)

    try:
        model = genai.GenerativeModel(CHAT_MODEL)
        response = model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens or 1024,
            )
        )
        return response.text.strip()
    except Exception as e:
        print(f"Gemini chat error: {e}")
        raise

# --- Embeddings helper ----------------------------------------------------

def embed_texts(texts: List[str]) -> List[List[float]]:
    try:
        embeddings = []
        for text in texts:
            result = genai.embed_content(
                model=EMB_MODEL,
                content=text,
                task_type="retrieval_document"
            )
            embeddings.append(result['embedding'])
        return embeddings
    except Exception as e:
        print(f"Gemini embedding error: {e}")
        raise

def embed_text(text: str) -> List[float]:
    return embed_texts([text])[0]
