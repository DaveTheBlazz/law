"""SQLite database layer - imports CSV and provides keyword search."""

import csv
import os
import sqlite3
from typing import Optional

import config


def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\u200c", "").replace("\u200b", "")
    text = text.replace("ي", "ی").replace("ك", "ک")
    return text.strip()


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def initialize_db(csv_path: Optional[str] = None) -> None:
    """Create tables and import CSV if not already done."""
    csv_path = csv_path or config.CSV_PATH
    conn = _get_conn()
    try:
        c = conn.cursor()

        # Main table
        c.execute("""
            CREATE TABLE IF NOT EXISTS opinions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT,
                nezariye_number TEXT,
                parvandeh_number TEXT,
                date TEXT,
                estelam TEXT,
                nezariye TEXT,
                combined TEXT
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_date ON opinions(date)")

        # Embedding table
        c.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                opinion_id INTEGER PRIMARY KEY,
                embedding BLOB,
                FOREIGN KEY (opinion_id) REFERENCES opinions(id)
            )
        """)

        # Check if already imported
        count = c.execute("SELECT COUNT(*) FROM opinions").fetchone()[0]
        if count == 0 and os.path.exists(csv_path):
            print(f"[DB] Importing {csv_path} ...")
            rows = []
            with open(csv_path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    clean = {}
                    for k, v in row.items():
                        clean[k.strip().lstrip("\ufeff")] = v
                    combined = normalize_text(clean.get("estelam", "") + " " + clean.get("nezariye", ""))
                    rows.append((
                        clean.get("url", ""),
                        clean.get("nezariye_number", ""),
                        clean.get("parvandeh_number", ""),
                        clean.get("date", ""),
                        clean.get("estelam", ""),
                        clean.get("nezariye", ""),
                        combined,
                    ))
            c.executemany(
                "INSERT INTO opinions (url, nezariye_number, parvandeh_number, date, estelam, nezariye, combined) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                rows,
            )
            print(f"[DB] Imported {len(rows)} opinions.")
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Keyword search
# ---------------------------------------------------------------------------

def _word_in_text(term: str, text: str) -> bool:
    """Check if term appears as a whole word (not substring) in text."""
    if not term:
        return True
    import re
    words = re.split(r'[\s.,؛:!؟\-()\/\[\]<>(){}؛،?!\u200c\u200b]+', text)
    return term in words


def keyword_search(query: str, columns: list[str] = None, limit: int = 50) -> list[dict]:
    """Search opinions by keyword using SQL LIKE queries."""
    if columns is None:
        columns = ["estelam", "nezariye"]
    terms = [normalize_text(t) for t in query.strip().split() if normalize_text(t)]  # strip + filter empty

    if not terms:
        return []

    conn = _get_conn()
    try:
        # Use SQL LIKE for first term to narrow candidates, then filter in-memory
        first_term = terms[0]
        # Build LIKE clauses for target columns
        like_clauses = [f"{col} LIKE ?" for col in columns if col in ["estelam", "nezariye"]]
        like_pattern = f"%{first_term}%"

        where = " OR ".join(like_clauses)
        params = [like_pattern] * len(like_clauses)

        sql = f"SELECT id, url, nezariye_number, parvandeh_number, date, estelam, nezariye " \
              f"FROM opinions WHERE ({where}) LIMIT 500"
        rows = conn.execute(sql, params).fetchall()

        # Filter with whole-word matching in memory
        results = []
        for r in rows:
            rd = dict(r)  # Convert sqlite3.Row to dict
            text = " ".join(normalize_text(rd.get(col, "")) for col in columns)
            if all(_word_in_text(term, text) for term in terms):
                results.append({
                    "id": rd["id"],
                    "url": rd["url"],
                    "nezariye_number": rd["nezariye_number"],
                    "parvandeh_number": rd["parvandeh_number"],
                    "date": rd["date"],
                    "estelam": rd["estelam"],
                    "nezariye": rd["nezariye"],
                })
                if len(results) >= limit:
                    break
        return results
    finally:
        conn.close()


def get_opinion_by_id(opinion_id: int) -> Optional[dict]:
    """Fetch a single opinion by ID."""
    conn = _get_conn()
    try:
        r = conn.execute("SELECT * FROM opinions WHERE id=?", (opinion_id,)).fetchone()
        if r:
            return dict(r)
        return None
    finally:
        conn.close()


def get_total_count() -> int:
    conn = _get_conn()
    try:
        return conn.execute("SELECT COUNT(*) FROM opinions").fetchone()[0]
    finally:
        conn.close()


def get_embedding_count() -> int:
    conn = _get_conn()
    try:
        return conn.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]
    finally:
        conn.close()
