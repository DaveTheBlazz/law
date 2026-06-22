# Plan 004: Fix database connection leaks on exceptions

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 093c952..HEAD -- app.py database.py`

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: bug
- **Planned at**: commit `093c952`, 2026-06-22

## Why this matters

Every function that calls `_get_conn()` opens a SQLite connection but does not
wrap the usage in try/finally. If an exception occurs between `_get_conn()` and
`conn.close()`, the connection leaks. Under concurrent load (uvicorn workers),
SQLite can run out of file handles or hit locking issues.

## Current state

Pattern in `database.py` (example — `get_total_count`):
```python
def get_total_count() -> int:
    conn = _get_conn()
    c = conn.execute("SELECT COUNT(*) FROM opinions").fetchone()[0]
    conn.close()
    return c
```

Same pattern in: `get_embedding_count()`, `keyword_search()`, `get_opinion_by_id()`.

Pattern in `app.py` (`api_all_opinions`):
```python
@app.get("/api/all-opinions")
async def api_all_opinions():
    conn = _get_conn()
    rows = conn.execute("SELECT ...").fetchall()
    conn.close()
    return {"count": len(rows), "results": [dict(r) for r in rows]}
```

The fix: use `try/finally` to guarantee `conn.close()`.

**Repo convention**: No context managers or dependency injection. Functions are
procedural. Match this style — add try/finally, don't refactor to `with`
statements unless the whole module adopts it.

## Commands you will need

| Purpose   | Command                          | Expected on success |
|-----------|----------------------------------|---------------------|
| Syntax    | `.venv/Scripts/python.exe -m py_compile database.py` | no output |
| Syntax    | `.venv/Scripts/python.exe -m py_compile app.py` | no output |

## Scope

**In scope**:
- `database.py` — all functions that call `_get_conn()`
- `app.py` — `api_all_opinions` function

**Out of scope**:
- `initialize_db()` — already has `conn.commit()` and `conn.close()` in a
  controlled flow; add try/finally only if it has early returns.
- Connection pooling — not needed for SQLite at this scale.

## Git workflow

- Branch: `advisor/004-fix-db-connection-leaks`
- Commit message: `fix: ensure DB connections are closed on exception`
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Fix database.py functions

For each function that uses `_get_conn()`, wrap in try/finally:

**Before** (example — `get_total_count`):
```python
def get_total_count() -> int:
    conn = _get_conn()
    c = conn.execute("SELECT COUNT(*) FROM opinions").fetchone()[0]
    conn.close()
    return c
```

**After**:
```python
def get_total_count() -> int:
    conn = _get_conn()
    try:
        return conn.execute("SELECT COUNT(*) FROM opinions").fetchone()[0]
    finally:
        conn.close()
```

Apply this pattern to ALL functions in `database.py` that call `_get_conn()`:
- `initialize_db` — add try/finally around the body
- `keyword_search` — add try/finally
- `get_opinion_by_id` — add try/finally
- `get_total_count` — add try/finally
- `get_embedding_count` — add try/finally

**Verify**: `grep -n "conn.close()" database.py` — every `close()` should be
inside a `finally` block.

### Step 2: Fix app.py — api_all_opinions

Same pattern:

**Before**:
```python
async def api_all_opinions():
    conn = _get_conn()
    rows = conn.execute("SELECT ...").fetchall()
    conn.close()
    return ...
```

**After**:
```python
async def api_all_opinions():
    conn = _get_conn()
    try:
        rows = conn.execute("SELECT ...").fetchall()
        return {"count": len(rows), "results": [dict(r) for r in rows]}
    finally:
        conn.close()
```

**Verify**: `grep -n "conn.close()" app.py` — inside `finally`.

### Step 3: Verify syntax

```bash
.venv/Scripts/python.exe -m py_compile database.py
.venv/Scripts/python.exe -m py_compile app.py
```

**Verify**: Both exit 0, no output.

## Test plan

No new tests needed. The change is mechanical (try/finally wrapper) and verified
by syntax check + code review.

## Done criteria

- [ ] Every `conn.close()` in `database.py` and `app.py` is inside a `finally` block
- [ ] `py_compile database.py` exits 0
- [ ] `py_compile app.py` exits 0
- [ ] No files outside the in-scope list are modified
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back if:

- `database.py` or `app.py` have changed significantly since the excerpts above.
- You discover a context-manager pattern (`with _get_conn() as conn`) already
  in use — if so, adopt that pattern instead of try/finally.

## Maintenance notes

- For a more robust solution, consider making `_get_conn()` a context manager:
  ```python
  @contextlib.contextmanager
  def _get_conn():
      conn = sqlite3.connect(config.DB_PATH)
      try:
          yield conn
      finally:
          conn.close()
  ```
  This is a larger refactor — not in this plan's scope.
