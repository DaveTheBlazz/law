# Plan 006: Disable uvicorn reload in production

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 093c952..HEAD -- main.py`

## Status

- **Priority**: P3
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: dx
- **Planned at**: commit `093c952`, 2026-06-22

## Why this matters

`main.py` hardcodes `reload=True` in `uvicorn.run()`. The reloader spawns a
second process, doubles memory usage, and can mask import-time errors in
production. It should be off by default and opt-in for development.

## Current state

- `main.py` (full file):
  ```python
  #!/usr/bin/env python3
  """Run the law opinions web app.

  Usage:
      python main.py
  """

  import uvicorn
  import config

  def main():
      print(f"Starting {config.APP_TITLE} on http://{config.APP_HOST}:{config.APP_PORT}")
      uvicorn.run(
          "app:app",
          host=config.APP_HOST,
          port=config.APP_PORT,
          reload=True,
      )

  if __name__ == "__main__":
      main()
  ```

## Commands you will need

| Purpose   | Command                          | Expected on success |
|-----------|----------------------------------|---------------------|
| Syntax    | `.venv/Scripts/python.exe -m py_compile main.py` | no output |

## Scope

**In scope**:
- `main.py`

**Out of scope**:
- `Dockerfile` / `docker-compose.yml` — they use `python main.py` as CMD;
  production reload behavior is controlled here.
- `config.py` — don't add a config flag; use a command-line flag.

## Git workflow

- Branch: `advisor/006-disable-reload-production`
- Commit message: `fix: disable uvicorn reload by default (opt-in via --reload)`
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Accept reload from command line, default False

Replace `main.py` with:

```python
#!/usr/bin/env python3
"""Run the law opinions web app.

Usage:
    python main.py          # production (no reload)
    python main.py --reload # development (auto-reload)
"""

import argparse
import uvicorn
import config

def main():
    parser = argparse.ArgumentParser(description=config.APP_TITLE)
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload (development)")
    args = parser.parse_args()

    print(f"Starting {config.APP_TITLE} on http://{config.APP_HOST}:{config.APP_PORT}")
    uvicorn.run(
        "app:app",
        host=config.APP_HOST,
        port=config.APP_PORT,
        reload=args.reload,
    )

if __name__ == "__main__":
    main()
```

**Verify**: `py_compile main.py` exits 0

### Step 2: Verify --help works

```bash
.venv/Scripts/python.exe main.py --help
```

**Verify**: Output includes `--reload` option.

### Step 3: Verify default (no reload) starts without error

```bash
timeout 5 .venv/Scripts/python.exe main.py 2>&1 || true
```

**Verify**: Prints startup message, does NOT show "watchfiles" or "reload"
messages (those indicate the reloader is active).

## Test plan

No new tests needed. Verify by running `--help` and checking default behavior.

## Done criteria

- [ ] `py_compile main.py` exits 0
- [ ] `python main.py` runs with `reload=False` (no reloader messages)
- [ ] `python main.py --reload` runs with `reload=True`
- [ ] No files outside the in-scope list are modified
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back if:

- `main.py` has changed significantly since the excerpt above.
- `uvicorn` version doesn't support `reload` parameter (it does for all
  versions ≥ 0.1).

## Maintenance notes

- Document `python main.py --reload` in README.md Quick Start section if the
  team wants dev-mode instructions explicit.
