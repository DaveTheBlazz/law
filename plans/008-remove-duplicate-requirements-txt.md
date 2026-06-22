# Plan 008: Remove duplicate requirements.txt (pyproject.toml is source of truth)

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 093c952..HEAD -- requirements.txt pyproject.toml Dockerfile`

## Status

- **Priority**: P3
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: tech-debt
- **Planned at**: commit `093c952`, 2026-06-22

## Why this matters

The project maintains both `requirements.txt` and `pyproject.toml` with the
same 7 dependencies. `pyproject.toml` + `uv.lock` is the source of truth
(uv is the package manager). `requirements.txt` is stale risk — whoever updates
one will likely forget the other.

## Current state

- `requirements.txt` (7 deps, duplicates pyproject.toml exactly):
  ```
  fastapi>=0.115.0
  uvicorn[standard]>=0.32.0
  jinja2>=3.1.4
  python-dotenv>=1.0.1
  aiohttp>=3.11.0
  numpy>=2.0.0
  openai>=2.43.0
  ```
- `pyproject.toml` dependencies (same 7):
  ```toml
  dependencies = [
      "aiohttp>=3.11.0",
      "fastapi>=0.115.0",
      "jinja2>=3.1.4",
      "numpy>=2.0.0",
      "openai>=2.43.0",
      "python-dotenv>=1.0.1",
      "uvicorn[standard]>=0.32.0",
  ]
  ```
- `Dockerfile` uses `requirements.txt`:
  ```dockerfile
  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt
  ```

## Commands you will need

| Purpose   | Command                | Expected on success |
|-----------|------------------------|---------------------|
| Check     | `git status`           | clean or known state|

## Scope

**In scope**:
- `requirements.txt` — delete
- `Dockerfile` — switch to `uv` or `pip install .`

**Out of scope**:
- `pyproject.toml` — no changes.
- `uv.lock` — no changes.

## Git workflow

- Branch: `advisor/008-remove-requirements-txt`
- Commit message: `chore: remove requirements.txt, use pyproject.toml in Dockerfile`
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Update Dockerfile to use pip install from pyproject.toml

Replace the dependency installation in `Dockerfile`:

**Before**:
```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

**After**:
```dockerfile
COPY pyproject.toml uv.lock .
RUN pip install --no-cache-dir .
```

This installs from `pyproject.toml` directly. No need for uv in the container —
`pip install .` reads pyproject.toml.

**Verify**: `grep "requirements.txt" Dockerfile` → no output (exit 1)

### Step 2: Delete requirements.txt

```bash
git rm requirements.txt
```

**Verify**: `git status` shows `requirements.txt` as deleted.

### Step 3: Verify Dockerfile still references valid files

```bash
grep -E "COPY|RUN pip" Dockerfile
```

Expected: `COPY pyproject.toml uv.lock .` and `RUN pip install --no-cache-dir .`

## Test plan

No new tests needed. Verify by reading Dockerfile.

A full Docker build would be the definitive test but requires Docker runtime.
If available: `docker build -t law-test .` → exit 0.

## Done criteria

- [ ] `requirements.txt` is deleted (`git status` shows it)
- [ ] `Dockerfile` installs from `pyproject.toml` (not requirements.txt)
- [ ] `grep "requirements.txt" Dockerfile` returns no matches
- [ ] No files outside the in-scope list are modified
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back if:

- `Dockerfile` has changed significantly (e.g., already switched to uv).
- `requirements.txt` contains dependencies NOT in `pyproject.toml` (diff them
  first; if there are extras, add them to pyproject.toml before deleting).

## Maintenance notes

- Future dependency changes: `uv add <package>` (updates pyproject.toml + uv.lock).
- Never generate `requirements.txt` from uv — it defeats the purpose of having
  a single source of truth.
