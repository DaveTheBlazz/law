# Plan 005: Add pagination to /api/all-opinions and remove unbounded endpoint

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 093c952..HEAD -- app.py`

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: MED (changes API contract)
- **Depends on**: none
- **Category**: perf
- **Planned at**: commit `093c952`, 2026-06-22

## Why this matters

`GET /api/all-opinions` returns all 12,239 opinions in a single JSON response
(~10 MB). There is no pagination, no limit, and the frontend's `doShowAll()`
loads everything into client memory. This will crash or freeze on mobile
devices. The endpoint should either be paginated or removed entirely (the
keyword search with `limit=500` already covers "show many results").

## Current state

- `app.py:97-102` — current endpoint:
  ```python
  @app.get("/api/all-opinions")
  async def api_all_opinions():
      conn = _get_conn()
      rows = conn.execute("SELECT id, url, nezariye_number, parvandeh_number, date, estelam, nezariye FROM opinions").fetchall()
      conn.close()
      return {"count": len(rows), "results": [dict(r) for r in rows]}
  ```
- `templates/search.html` — frontend calls it:
  ```javascript
  async function doShowAll() {
      const resp = await fetch('/api/all-opinions');
      const data = await resp.json();
      currentResults = data.results || [];
  ```

**Decision**: Replace the unbounded endpoint with a paginated one using
`offset` and `limit` query params. This matches the existing `/api/search`
pattern which already has `limit`.

## Commands you will need

| Purpose   | Command                          | Expected on success |
|-----------|----------------------------------|---------------------|
| Syntax    | `.venv/Scripts/python.exe -m py_compile app.py` | no output |

## Scope

**In scope**:
- `app.py` — modify `/api/all-opinions` endpoint
- `templates/search.html` — update `doShowAll()` to use paginated endpoint

**Out of scope**:
- `database.py` — no changes needed; use SQL LIMIT/OFFSET in the query.
- Other API endpoints — `/api/search` already has limit.
- Adding a separate paginated endpoint — modify the existing one in-place to
  maintain the URL.

## Git workflow

- Branch: `advisor/005-pagination-all-opinions`
- Commit message: `perf: paginate /api/all-opinions endpoint`
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Update the backend endpoint

Modify `api_all_opinions` to accept `offset` and `limit` query parameters with
defaults that return a manageable first page:

```python
@app.get("/api/all-opinions")
async def api_all_opinions(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    conn = _get_conn()
    try:
        total = conn.execute("SELECT COUNT(*) FROM opinions").fetchone()[0]
        rows = conn.execute(
            "SELECT id, url, nezariye_number, parvandeh_number, date, estelam, nezariye "
            "FROM opinions LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return {
            "total": total,
            "count": len(rows),
            "offset": offset,
            "limit": limit,
            "results": [dict(r) for r in rows],
        }
    finally:
        conn.close()
```

Note: This also applies the try/finally fix from plan 004. If plan 004 is
executed first, the code will already have try/finally — just add the LIMIT
and OFFSET.

**Verify**: `py_compile app.py` exits 0

### Step 2: Update the frontend doShowAll()

In `templates/search.html`, update `doShowAll()` to fetch the first page:

```javascript
async function doShowAll() {
    currentTab = 'keyword';
    showLoading();
    try {
        const resp = await fetch('/api/all-opinions?limit=500&offset=0');
        const data = await resp.json();
        currentResults = data.results || [];
        currentPage = 1;
        renderResults(currentResults, 'keyword');
    } catch (e) {
        showEmpty('خطا در ارتباط با سرور');
    }
}
```

**Verify**: The function still loads results and renders them (same behavior,
just limited to 500).

## Test plan

No new tests needed. Verify manually:
- `curl 'http://localhost:8080/api/all-opinions?limit=10&offset=0'` returns
  `{"total": 12239, "count": 10, ...}` with 10 results.
- `curl 'http://localhost:8080/api/all-opinions?limit=10&offset=5'` returns
  different results (next page).

## Done criteria

- [ ] `py_compile app.py` exits 0
- [ ] Endpoint accepts `offset` and `limit` query parameters
- [ ] Response includes `total` count for pagination
- [ ] `doShowAll()` fetches with `limit=500`
- [ ] No files outside the in-scope list are modified
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back if:

- `app.py` has changed significantly since the excerpts above.
- The `/api/all-opinions` endpoint is called from other places besides
  `doShowAll()` in search.html (grep for it).

## Maintenance notes

- If the frontend needs "load more" for all-opinions, add an offset-based
  fetch using `data.total` and `data.offset + data.limit`.
- Consider deprecating `/api/all-opinions` entirely in favor of keyword search
  with `limit=500` — the use case is unclear.
