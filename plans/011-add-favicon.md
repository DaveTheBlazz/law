# Plan 011: Add favicon to eliminate 404

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 093c952..HEAD -- templates/base.html`

## Status

- **Priority**: P3
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: dx
- **Planned at**: commit `093c952`, 2026-06-22

## Why this matters

Browser requests `/favicon.ico` on every page load and gets 404. This clutters
server logs and shows a broken icon in the tab. A simple SVG favicon costs
nothing and eliminates the 404.

## Current state

- `templates/base.html` — `<head>` has no `<link rel="icon">`.
- No `favicon.ico` or `favicon.svg` in the repo.

## Commands you will need

| Purpose   | Command                | Expected on success |
|-----------|------------------------|---------------------|
| None      | (static file change)   | visual verification |

## Scope

**In scope**:
- `templates/base.html` — add favicon link
- `static/favicon.svg` — create (new file, new directory)

**Out of scope**:
- Multiple favicon sizes (iOS, Android, Windows tile) — over-engineering for
  an internal tool.
- `favicon.ico` PNG — SVG suffices for all modern browsers.

## Git workflow

- Branch: `advisor/011-add-favicon`
- Commit message: `feat: add ⚖️ favicon`
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Create static/favicon.svg

Create a minimal SVG favicon using the scale emoji character:

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <text y=".9em" font-size="90">⚖️</text>
</svg>
```

### Step 2: Add favicon link in base.html

In `templates/base.html`, add after `<title>`:

```html
<link rel="icon" type="image/svg+xml" href="/static/favicon.svg">
```

**Verify**: `grep "favicon" templates/base.html` → outputs the link line.

## Test plan

No automated tests. Verify by:
1. Starting the server: `python main.py`
2. Opening browser — tab shows ⚖️ icon, no 404 in network tab.

## Done criteria

- [ ] `static/favicon.svg` exists and is valid SVG
- [ ] `templates/base.html` includes `<link rel="icon">`
- [ ] No 404 for favicon in browser network tab
- [ ] No files outside the in-scope list are modified
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back if:

- `templates/base.html` has changed significantly.
- A `static/` directory exists with conflicting files (it doesn't — not in repo).

## Maintenance notes

- If a branded favicon is desired later, replace the SVG content. Same file,
  same link.
