from __future__ import annotations
import os
import pathlib

from db.crud import create_all

if __name__ == "__main__":
    # Ensure data directory exists for SQLite
    data_dir = pathlib.Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)

    create_all()
    print("[OK] Database initialized at data/uidai.sqlite (or DB_URL env).")