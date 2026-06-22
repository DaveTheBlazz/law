# Plan 002: Remove 79MB law.db from git tracking

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 093c952..HEAD -- .gitignore`
> If `.gitignore` changed since this plan was written, compare against live
> code before proceeding; on a mismatch, treat it as a STOP condition.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: tech-debt
- **Planned at**: commit `093c952`, 2026-06-22

## Why this matters

`law.db` (79 MB) is tracked in git. It is a derived artifact — recreated from
`opinions.csv` by `initialize_db()`. Tracking it bloats clones, slows CI, and
risks stale data. The DB should be regenerated on startup.

## Current state

- `.gitignore` (full contents):
  ```
  .env
  .venv/
  __pycache__/
  *.pyc
  *.pyo
  *.pyd
  *.sqlite
  *.sqlite3
  nul
  .DS_Store
  ```
  Note: `*.sqlite` and `*.sqlite3` are excluded, but `*.db` is NOT.
- `database.py:53-57` — `initialize_db()` creates the DB from CSV on startup:
  ```python
  count = c.execute("SELECT COUNT(*) FROM opinions").fetchone()[0]
  if count == 0 and os.path.exists(csv_path):
  ```
  The DB auto-regenerates if empty, so removing it is safe.

## Commands you will need

| Purpose   | Command                  | Expected on success |
|-----------|--------------------------|---------------------|
| Check git | `git status`             | clean or known state|
| Untrack   | `git rm --cached law.db` | file removed from index |

## Scope

**In scope**:
- `.gitignore`
- `law.db` (git untrack only — do not delete the working copy)

**Out of scope**:
- `database.py` — the auto-regenerate logic already handles missing DB.
- `Dockerfile` / `docker-compose.yml` — they mount a volume for the DB already.

## Git workflow

- Branch: `advisor/002-remove-db-from-git`
- Commit message: `fix: untrack law.db from git (79MB derived artifact)`
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Add `*.db` to `.gitignore`

Append `*.db` to `.gitignore` after the existing `*.sqlite3` line:

```
*.sqlite3
*.db
```

**Verify**: `grep "*.db" .gitignore` → outputs `*.db`

### Step 2: Remove law.db from git index (keep working copy)

```bash
git rm --cached law.db
```

**Verify**: `git status` shows `law.db` as untracked, not deleted.

### Step 3: Confirm DB regenerates

Verify that `database.py:initialize_db()` will recreate the DB:
```python
# Read the function to confirm
grep -A5 "count == 0 and os.path.exists" database.py
```

Expected: the function imports from CSV when table is empty.

**Verify**: The grep output shows the import logic (it does, per current state).

## Test plan

No new tests needed. Verify the DB auto-creates by reading `initialize_db()`.

## Done criteria

- [ ] `*.db` appears in `.gitignore`
- [ ] `git status` shows `law.db` as untracked
- [ ] `law.db` file still exists on disk (not deleted)
- [ ] No files outside the in-scope list are modified
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back if:

- `law.db` is referenced as a required asset in documentation (it isn't —
  `README.md` says "Auto-created SQLite database").
- `initialize_db()` does not recreate the DB from CSV when empty.

## Maintenance notes

- If the team wants a seed database in the future, distribute it as a release
  asset or via a script, not in git.
- Consider adding `DB_PATH` to `.gitignore` explicitly (not just `*.db`) to
  catch non-standard DB filenames.
