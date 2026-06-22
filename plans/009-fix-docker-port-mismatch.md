# Plan 009: Fix Docker port mismatch between docker-compose and .env.example

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 093c952..HEAD -- docker-compose.yml .env.example Dockerfile`

## Status

- **Priority**: P3
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: dx
- **Planned at**: commit `093c952`, 2026-06-22

## Why this matters

`docker-compose.yml` maps port 8080, `Dockerfile` exposes 8080, but
`.env.example` defaults to `APP_PORT=8000`. A new developer copying
`.env.example` to `.env` and running Docker gets a mismatch — the app listens
on 8000 inside the container but compose maps 8080→8080, so nothing is reachable.

## Current state

- `docker-compose.yml`:
  ```yaml
  ports:
    - "8080:8080"
  ```
- `Dockerfile`:
  ```dockerfile
  EXPOSE 8080
  ```
- `.env.example`:
  ```ini
  APP_PORT=8000
  ```

The app reads `APP_PORT` from env. In Docker, compose sets port mapping to 8080
but `.env` (loaded into container) sets `APP_PORT=8000`. The app listens on
8000, compose maps 8080→8080 — unreachable.

## Commands you will need

| Purpose   | Command                | Expected on success |
|-----------|------------------------|---------------------|
| Check     | `git status`           | clean or known state|

## Scope

**In scope**:
- `.env.example` — change default port

**Out of scope**:
- `docker-compose.yml` — the compose mapping is fine (8080 is the convention).
- `Dockerfile` — EXPOSE 8080 is correct.
- `config.py` — the port loader is fine.

## Git workflow

- Branch: `advisor/009-fix-docker-port`
- Commit message: `fix: align .env.example APP_PORT with Docker port 8080`
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Change APP_PORT default in .env.example

In `.env.example`, change:
```ini
APP_PORT=8000
```
to:
```ini
APP_PORT=8080
```

**Verify**: `grep "APP_PORT" .env.example` → `APP_PORT=8080`

## Test plan

No new tests needed. Verify by reading the file.

## Done criteria

- [ ] `.env.example` has `APP_PORT=8080`
- [ ] Port matches `docker-compose.yml` mapping (8080:8080)
- [ ] Port matches `Dockerfile` EXPOSE (8080)
- [ ] No files outside the in-scope list are modified
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back if:

- `docker-compose.yml` or `Dockerfile` have changed to use a different port.
- There is a documented reason for port 8000 (e.g., summary.md mentions port
  conflicts — it does: "Port 8000 blocked on this machine"). If so, change
  docker-compose.yml instead of .env.example.

## Maintenance notes

- summary.md notes "Port 8000 blocked on this machine; using 8080". If 8000 is
  globally blocked on the dev machine, 8080 is the right default everywhere.
- Consider documenting the port in README.md Quick Start for Docker users.
