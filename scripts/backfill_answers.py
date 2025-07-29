from __future__ import annotations
# If you later change models or want to rebuild the FAISS index from meta:
# - Delete data/answers.faiss
# - Run this script to re-add all answers from answers_meta.jsonl

import json
from llm.memory import AnswerMemory, META_PATH

if __name__ == "__main__":
    mem = AnswerMemory()
    if not os.path.exists(META_PATH):
        print("No meta file; nothing to backfill.")
        raise SystemExit(0)
    with open(META_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            mem.add_answer(obj["question"], obj["answer"], obj.get("doc_ids", []))
    print("Rebuilt FAISS index from meta.")