# Plan 007: Establish test suite baseline

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 093c952..HEAD -- app.py database.py config.py pyproject.toml`

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: LOW
- **Depends on**: none
- **Category**: tests
- **Planned at**: commit `093c952`, 2026-06-22

## Why this matters

The codebase has zero tests. Any refactor, dependency upgrade, or bug fix has
no safety net. This plan establishes a minimal but meaningful test baseline
covering the critical paths: DB initialization, keyword search, and API routes.

## Current state

- No test directory, no test framework installed.
- Package manager: **uv** (pyproject.toml + uv.lock). Use `uv add --dev pytest httpx`.
- Key modules to test:
  - `database.py` — `initialize_db()`, `keyword_search()`, `get_total_count()`
  - `app.py` — FastAPI routes (use `TestClient`)
- `config.py` reads from `.env`; tests need isolated config (use a temp DB path).

## Commands you will need

| Purpose   | Command                                    | Expected on success |
|-----------|--------------------------------------------|---------------------|
| Add deps  | `uv add --dev pytest httpx`               | packages added      |
| Run tests | `uv run pytest`                            | all pass            |
| Run tests | `uv run pytest tests/ -v`                  | verbose output      |

## Scope

**In scope**:
- `pyproject.toml` — add dev dependencies
- `tests/` directory (create) — test files
- `tests/conftest.py` — shared fixtures
- `tests/test_database.py` — DB layer tests
- `tests/test_app.py` — API route tests

**Out of scope**:
- Integration tests against real AI API (requires credentials, slow).
- E2E browser tests.
- Mocking AI calls in app tests — skip AI-requiring routes, test only
  keyword search and static pages.

## Git workflow

- Branch: `advisor/007-add-test-baseline`
- Commit message style: Conventional commits, e.g. `test: add keyword search tests`
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Add test dependencies

```bash
uv add --dev pytest httpx
```

`httpx` is needed for FastAPI's `TestClient`.

**Verify**: `grep -A2 "pytest" pyproject.toml` shows pytest in dev dependencies
(or `dependency-groups`).

### Step 2: Create tests/conftest.py

Create a shared fixture that points DB operations to a temp file:

```python
import os
import tempfile
import pytest
from unittest.mock import patch

@pytest.fixture(autouse=True)
def test_db(monkeytmp_path, monkeypatch):
    """Redirect all DB operations to a temporary file."""
    db_file = tmp_path / "test.db"
    with patch("config.DB_PATH", str(db_file)):
        with patch("config.CSV_PATH", ""):  # no CSV import in tests
            yield str(db_file)
```

Wait — `monkeytmp_path` is a typo, fix to use `tmp_path`:

```python
import tempfile
import pytest
from unittest.mock import patch

@pytest.fixture
def test_db_path(tmp_path):
    """Return a temp DB path for tests."""
    return str(tmp_path / "test.db")

@pytest.fixture
def db_config(test_db_path, monkeypatch):
    """Patch config to use temp DB and no CSV."""
    monkeypatch.setattr("config.DB_PATH", test_db_path)
    monkeypatch.setattr("config.CSV_PATH", "")
    yield test_db_path
```

### Step 3: Create tests/test_database.py

Test the database layer functions:

```python
import pytest
from database import initialize_db, keyword_search, get_total_count, normalize_text

def test_normalize_text(db_config):
    assert normalize_text("  hello  ") == "hello"
    assert normalize_text("\u200c") == ""  # zero-width non-joiner removed
    assert normalize_text("ي") == "ی"  # Arabic Ya → Persian Ya
    assert normalize_text("") == ""

def test_initialize_db_creates_table(db_config):
    initialize_db()  # with no CSV, creates empty table
    assert get_total_count() == 0

def test_keyword_search_empty(db_config):
    initialize_db()
    results = keyword_search("nonexistent")
    assert results == []

def test_keyword_search_with_data(db_config, tmp_path):
    # Create a minimal CSV for testing
    csv_file = tmp_path / "test.csv"
    csv_file.write_text(
        "url,nezariye_number,parvandeh_number,date,estelam,nezariye\n"
        "http://example.com,123,456,1402/01/01,سوال درباره طلاق,نظر درباره طلاق\n"
        "http://example.com,124,457,1402/01/02,سوال درباره مهریه,نظر درباره مهریه\n"
    )
    import config
    config.CSV_PATH = str(csv_file)
    initialize_db()
    assert get_total_count() == 2

    results = keyword_search("طلاق")
    assert len(results) == 1
    assert results[0]["nezariye_number"] == "123"

    results = keyword_search("مهریه")
    assert len(results) == 1
    assert results[0]["nezariye_number"] == "124"

    # Multi-term search (both terms must match)
    results = keyword_search("طلاق مهریه")
    assert len(results) == 0  # no single row has both
```

**Verify**: `uv run pytest tests/test_database.py -v` → all pass

### Step 4: Create tests/test_app.py

Test API routes:

```python
import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_index_page(db_config):
    """Home page loads."""
    response = client.get("/")
    assert response.status_code == 200

def test_search_page(db_config):
    """Search page loads."""
    response = client.get("/search")
    assert response.status_code == 200

def test_api_stats(db_config):
    """Stats endpoint returns JSON."""
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_opinions" in data
    assert "ai_available" in data

def test_api_keyword_search(db_config):
    """Keyword search returns results or empty list."""
    response = client.get("/api/search?q=test")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert isinstance(data["results"], list)

def test_api_keyword_search_min_length(db_config):
    """Empty query rejected."""
    response = client.get("/api/search?q=")
    assert response.status_code == 422  # FastAPI validation error

def test_chat_page_requires_ai(db_config):
    """Chat page returns 400 when AI not configured."""
    response = client.get("/chat")
    assert response.status_code == 400
```

**Verify**: `uv run pytest tests/test_app.py -v` → all pass

### Step 5: Run full test suite

```bash
uv run pytest tests/ -v
```

**Verify**: All tests pass, exit 0.

### Step 6: Add test script to pyproject.toml

Add to `[project.scripts]` or `[tool.uv]` section (match repo convention —
the repo currently has no test script):

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
```

## Test plan

The tests ARE the test plan. They cover:
- Text normalization (Persian-specific)
- DB initialization (empty + with data)
- Keyword search (single term, multi-term, no match)
- API routes (pages load, stats, search, validation)

## Done criteria

- [ ] `uv run pytest tests/ -v` exits 0, all tests pass
- [ ] At least 10 tests exist across test_database.py and test_app.py
- [ ] Tests use temp DB (no pollution of law.db)
- [ ] No files outside the in-scope list are modified
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back if:

- `uv` is not available in the environment (fall back to `pip install --dev`).
- FastAPI's `TestClient` requires a different import path in the installed
  version.
- `database.py` or `app.py` have changed significantly since the excerpts above.

## Maintenance notes

- When AI tests are needed, mock `config.ai_available()` to return True and
  patch `app.ai_client` with a fixture.
- Consider adding `pytest-asyncio` if async route tests are added later.
- CI should run `uv run pytest` as a gate.
