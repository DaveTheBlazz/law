# Plan 003: Remove dead embedding code from database.py

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 093c952..HEAD -- database.py app.py`
> If in-scope files changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: tech-debt
- **Planned at**: commit `093c952`, 2026-06-22

## Why this matters

`database.py` contains ~70 lines of embedding functions (`_embedding_to_blob`,
`_blob_to_embedding`, `_cosine_similarity`, `get_embedding`, `compute_and_store_embedding`,
`embed_all_missing`, `semantic_search`) and an unused `numpy` import. The
project's AI provider doesn't support embeddings (returns 501), so this code
has never run and will confuse future maintainers.

## Current state

- `database.py:5` — `import numpy as np` (unused after removal)
- `database.py:35` — `import math` (unused)
- `database.py:127-218` — embedding section, functions:
  - `_embedding_to_blob(vec)` — line ~127
  - `_blob_to_embedding(blob)` — line ~131
  - `_cosine_similarity(a, b)` — line ~135
  - `get_embedding(text)` — async, line ~144
  - `compute_and_store_embedding(opinion_id, text)` — async, line ~162
  - `embed_all_missing()` — async, line ~175
  - `semantic_search(query, top_k)` — async, line ~201
- `app.py` — no imports of these functions (confirmed by grep)
- `pyproject.toml` lists `numpy` as dependency — can be removed after code cleanup

**Code to remove** (the entire "Embedding helpers" section in database.py):

```python
# ---------------------------------------------------------------------------
# Embedding helpers
# ---------------------------------------------------------------------------

def _embedding_to_blob(vec: list[float]) -> bytes:
    return np.array(vec, dtype=np.float32).tobytes()


def _blob_to_embedding(blob: bytes) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float32)


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    ...


async def get_embedding(text: str) -> Optional[list[float]]:
    ...


async def compute_and_store_embedding(opinion_id: int, text: str) -> Optional[list[float]]:
    ...


async def embed_all_missing() -> int:
    ...


async def semantic_search(query: str, top_k: int = None) -> list[dict]:
    ...
```

## Commands you will need

| Purpose   | Command                          | Expected on success |
|-----------|----------------------------------|---------------------|
| Syntax    | `.venv/Scripts/python.exe -m py_compile database.py` | no output |
| Import    | `.venv/Scripts/python.exe -c "import database; print('ok')"` | prints `ok` |

## Scope

**In scope**:
- `database.py` — remove embedding functions and unused imports
- `pyproject.toml` — remove `numpy` dependency

**Out of scope**:
- `database.py` embeddings TABLE schema — leave the CREATE TABLE in
  `initialize_db()`. It costs nothing to keep and allows embeddings if a
  different provider is used later.
- `requirements.txt` — it duplicates `pyproject.toml`; don't touch it unless
  asked. The `pyproject.toml` is the source of truth (uv is the package manager).
- `app.py` — no changes needed.

## Git workflow

- Branch: `advisor/003-clean-embedding-code`
- Commit message: `refactor: remove dead embedding code and numpy dependency`
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Remove embedding functions from database.py

Delete the entire "Embedding helpers" section (from the comment block through
the end of `semantic_search`). This is approximately lines 125–218.

Keep everything before it (keyword search, helpers) and after it
(`get_opinion_by_id`, `get_total_count`, `get_embedding_count`).

**Verify**: `grep -n "embedding" database.py` → only matches in `initialize_db`
(table creation) and `get_embedding_count`, not function definitions.

### Step 2: Remove unused imports from database.py

Remove these lines from the top of `database.py`:
- `import numpy as np`
- `import math`
- `import json` (unused)

Keep: `csv`, `os`, `sqlite3`, `from typing import Optional`, `import config`

**Verify**: `.venv/Scripts/python.exe -m py_compile database.py` → no output

### Step 3: Verify no other file imports the removed functions

```bash
grep -rn "get_embedding\|semantic_search\|embed_all_missing\|compute_and_store_embedding" --include="*.py" .
```

Expected: only `get_embedding_count` matches (different function). If any
embedding function is imported elsewhere, STOP.

### Step 4: Remove numpy from pyproject.toml

Remove `"numpy>=2.0.0",` from the dependencies list.

**Verify**: `grep "numpy" pyproject.toml` → no output (exit 1)

## Test plan

No new tests needed. Verify by:
- `py_compile` succeeds on `database.py`
- Import test succeeds: `python -c "import database; print('ok')"`

## Done criteria

- [ ] `grep -n "def.*embedding\|def semantic_search\|def embed_all" database.py` returns no function definitions (only the table schema reference)
- [ ] `grep "numpy" pyproject.toml` returns no matches
- [ ] `py_compile database.py` succeeds (exit 0)
- [ ] No files outside the in-scope list are modified
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back if:

- Any file imports `get_embedding`, `semantic_search`, or `embed_all_missing`
  from `database`.
- `numpy` is used for something other than embeddings in `database.py`.
- `database.py` has changed significantly since the excerpts above.

## Maintenance notes

- The `embeddings` table in SQLite is left in place. If embeddings are needed
  with a different provider, only the functions need to be added back.
- If the project adopts a provider that supports embeddings, `numpy` can be
  re-added with `uv add numpy`.
