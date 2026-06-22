# Plan 001: Rotate API key leaked in summary.md

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 093c952..HEAD -- summary.md`
> If summary.md changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: security
- **Planned at**: commit `093c952`, 2026-06-22

## Why this matters

An API key (`aplserghsoleirhg35366`) is committed in `summary.md:30`. Once a
credential is in git history, it is burned — even if deleted, it remains in
every clone's history. The key must be rotated on the provider side and removed
from the repo.

## Current state

- `summary.md` — project notes; contains the key at line ~30:
  ```
  | Key | `aplserghsoleirhg35366` |
  ```
- `.gitignore` currently:
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

## Commands you will need

| Purpose   | Command                  | Expected on success |
|-----------|--------------------------|---------------------|
| Check git | `git status`             | clean or known state|

## Scope

**In scope** (the only files you should modify):
- `summary.md`
- `.gitignore`

**Out of scope**:
- `app.py`, `config.py`, `database.py` — the key is not hardcoded there (it
  comes from `.env` at runtime).
- `.env` — not tracked in git, not relevant.

## Git workflow

- Branch: `advisor/001-rotate-api-key`
- Commit message style: `fix: remove leaked API key from summary.md`
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Remove the API key value from summary.md

Replace the key value in the table row with `REDACTED — rotate this key`.
Do not leave the old value anywhere in the file.

**Verify**: `grep -n "aplserghsoleirhg35366" summary.md` → no output (exit 1)

### Step 2: Add `summary.md` to a "sensitive project notes" warning (optional)

If `summary.md` will be kept in the repo going forward, add a comment at the
top: `<!-- Do not put real credentials in this file. Use .env only. -->`

### Step 3: Warn user to rotate the key on the provider side

Add a `ponytail:` comment or note in the commit message that the key at
`telsaco.ir` must be rotated manually — code changes alone don't invalidate it.

**Verify**: `git diff -- summary.md` shows only the key replacement, no other
changes.

## Test plan

No tests needed — this is a file cleanup. Verify by grep.

## Done criteria

- [ ] `grep -rn "aplserghsoleirhg35366" .` returns no matches (outside .git)
- [ ] `summary.md` still provides useful project context without the key
- [ ] No files outside the in-scope list are modified (`git status`)
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- `summary.md` has changed significantly since the excerpt above.
- The key value appears in other tracked files (`grep -rn "aplserghsoleirhg35366" . --exclude-dir=.git`).

## Maintenance notes

- If `summary.md` is intended to be a living document, consider renaming it to
  `SUMMARY.md` or moving it to `docs/` and adding a CONTRIBUTING note about
  not committing credentials.
- Any future `.env` values should never be copied into markdown files.
