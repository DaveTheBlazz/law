# Plan 012: Handle opinions.csv — add to .gitignore and document bootstrap

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 093c952..HEAD -- .gitignore README.md`

## Status

- **Priority**: P3
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: dx
- **Planned at**: commit `093c952`, 2026-06-22

## Why this matters

`opinions.csv` is referenced by `config.py` (`CSV_PATH=opinions.csv`) but is
not in the repo and not in `.gitignore`. A fresh clone has no data source —
`initialize_db()` silently creates an empty table. The CSV should either be
distributed (LFS or release asset) or documented as required.

## Current state

- `config.py:20`: `CSV_PATH = os.getenv("CSV_PATH", "opinions.csv")`
- `database.py:55`: `if count == 0 and os.path.exists(csv_path):` — skips
  import if CSV doesn't exist.
- `.gitignore` does not mention `*.csv` or `opinions.csv`.
- `README.md` mentions `opinions.csv` in the structure but not how to obtain it.

## Commands you will need

| Purpose   | Command                | Expected on success |
|-----------|------------------------|---------------------|
| Check     | `git status`           | clean or known state|

## Scope

**In scope**:
- `.gitignore` — add `opinions.csv`
- `README.md` — document how to obtain the CSV

**Out of scope**:
- Adding `opinions.csv` to the repo (likely large, possibly copyrighted).
- Setting up Git LFS (requires pushing, beyond this plan's scope).

## Git workflow

- Branch: `advisor/012-document-csv`
- Commit message: `docs: add opinions.csv to .gitignore and document bootstrap`
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Add opinions.csv to .gitignore

Append to `.gitignore`:
```
# Data files (generated or external)
opinions.csv
```

**Verify**: `grep "opinions.csv" .gitignore` → outputs the line.

### Step 2: Update README.md Quick Start

Add a step between "Activate virtual environment" and "Run":

In the Quick Start section, after the venv activation step, add:

```markdown
# 1.5 (Required) Place opinions.csv in the project root
# Download from: [source URL or instructions]
# The app will import it into law.db on first run.
```

Since the source URL is the Iranian Judiciary's law opinion extractor skill
(`edarehoququqy.eadl.ir`), document it generically:

```markdown
# 2. Place opinions.csv in the project root
# (Exported from edarehoququqy.eadl.ir or provided as a data file)
```

**Verify**: `grep "opinions.csv" README.md` → outputs the new documentation line.

## Test plan

No automated tests. Verify by reading the updated files.

## Done criteria

- [ ] `opinions.csv` appears in `.gitignore`
- [ ] `README.md` documents where to obtain `opinions.csv`
- [ ] No files outside the in-scope list are modified
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back if:

- `opinions.csv` IS in the repo (check `git ls-files | grep opinions`).
- The README already documents CSV acquisition.

## Maintenance notes

- If the CSV is small enough (<50MB) and publicly distributable, consider
  adding it to the repo with `git lfs track opinions.csv`.
- Consider adding a startup check that prints a helpful error when the CSV is
  missing and the DB is empty.
