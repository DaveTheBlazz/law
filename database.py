"""SQLite database layer - imports CSV and provides search + embedding storage."""

import csv
import os
import sqlite3
import json
import math
from typing import Optional

import numpy as np

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
    conn = _get_conn()

    if not terms:
        conn.close()
        return []

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
    conn.close()

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


# ---------------------------------------------------------------------------
# Embedding helpers
# ---------------------------------------------------------------------------

def _embedding_to_blob(vec: list[float]) -> bytes:
    return np.array(vec, dtype=np.float32).tobytes()


def _blob_to_embedding(blob: bytes) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float32)


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


async def get_embedding(text: str) -> Optional[list[float]]:
    """Get embedding vector from AI API (OpenAI-compatible)."""
    if not config.ai_available():
        return None
    import aiohttp
    url = config.AI_BASE_URL.rstrip("/") + "/embeddings"
    payload = {
        "model": config.AI_EMBEDDING_MODEL,
        "input": text,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=payload,
                headers={"Authorization": f"Bearer {config.AI_API_KEY}"},
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["data"][0]["embedding"]
    except Exception as e:
        print(f"[Embedding error] {e}")
    return None


async def compute_and_store_embedding(opinion_id: int, text: str) -> Optional[list[float]]:
    """Compute embedding for an opinion and store it."""
    vec = await get_embedding(text)
    if vec:
        conn = _get_conn()
        conn.execute(
            "INSERT OR REPLACE INTO embeddings (opinion_id, embedding) VALUES (?, ?)",
            (opinion_id, _embedding_to_blob(vec)),
        )
        conn.commit()
        conn.close()
    return vec


async def embed_all_missing() -> int:
    """Compute embeddings for all opinions that don't have one yet."""
    conn = _get_conn()
    ids = conn.execute("SELECT id FROM opinions").fetchall()
    conn.close()
    total = len(ids)
    embedded = 0
    for row in ids:
        oid = row["id"]
        conn2 = _get_conn()
        existing = conn2.execute("SELECT embedding FROM embeddings WHERE opinion_id=?", (oid,)).fetchone()
        if existing is None:
            r = conn2.execute("SELECT estelam, nezariye FROM opinions WHERE id=?", (oid,)).fetchone()
            conn2.close()
            if r:
                text = r["estelam"] + " " + r["nezariye"]
                vec = await get_embedding(text)
                if vec:
                    conn3 = _get_conn()
                    conn3.execute(
                        "INSERT INTO embeddings (opinion_id, embedding) VALUES (?, ?)",
                        (oid, _embedding_to_blob(vec)),
                    )
                    conn3.commit()
                    conn3.close()
                    embedded += 1
        else:
            conn2.close()
        if (embedded + 1) % 100 == 0:
            print(f"[Embed] {embedded}/{total} opinions embedded...")
    return embedded


async def semantic_search(query: str, top_k: int = None) -> list[dict]:
    """Search opinions by semantic similarity using stored embeddings."""
    if top_k is None:
        top_k = config.SEMANTIC_TOP_K

    query_vec = await get_embedding(query)
    if query_vec is None:
        return []

    q_arr = np.array(query_vec, dtype=np.float32)

    conn = _get_conn()
    rows = conn.execute(
        "SELECT o.id, o.url, o.nezariye_number, o.parvandeh_number, o.date, "
        "o.estelam, o.nezariye, e.embedding "
        "FROM opinions o JOIN embeddings e ON o.id = e.opinion_id"
    ).fetchall()
    conn.close()

    scored = []
    for r in rows:
        emb = _blob_to_embedding(r["embedding"])
        sim = _cosine_similarity(q_arr, emb)
        scored.append((sim, {
            "id": r["id"],
            "url": r["url"],
            "nezariye_number": r["nezariye_number"],
            "parvandeh_number": r["parvandeh_number"],
            "date": r["date"],
            "estelam": r["estelam"],
            "nezariye": r["nezariye"],
            "similarity": round(sim, 4),
        }))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:top_k]]


def get_opinion_by_id(opinion_id: int) -> Optional[dict]:
    """Fetch a single opinion by ID."""
    conn = _get_conn()
    r = conn.execute("SELECT * FROM opinions WHERE id=?", (opinion_id,)).fetchone()
    conn.close()
    if r:
        return dict(r)
    return None


def get_total_count() -> int:
    conn = _get_conn()
    c = conn.execute("SELECT COUNT(*) FROM opinions").fetchone()[0]
    conn.close()
    return c


def get_embedding_count() -> int:
    conn = _get_conn()
    c = conn.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]
    conn.close()
    return c
