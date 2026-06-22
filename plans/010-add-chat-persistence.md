# Plan 010: Add chat persistence via localStorage

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 093c952..HEAD -- templates/chat.html`

## Status

- **Priority**: P3
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: direction
- **Planned at**: commit `093c952`, 2026-06-22

## Why this matters

Chat conversation is stored in a JS array (`conversation = []`). On page
refresh, all history is lost. Users lose context and must re-ask questions.
localStorage persistence costs ~15 lines and survives refresh.

## Current state

- `templates/chat.html` — chat JS:
  ```javascript
  let isStreaming = false;
  const conversation = [];
  ```
  - `sendChat()` pushes to `conversation` and sends full array to backend.
  - `clearChat()` does `conversation.length = 0`.
  - No persistence.

## Commands you will need

| Purpose   | Command                | Expected on success |
|-----------|------------------------|---------------------|
| None      | (frontend-only change) | visual verification |

## Scope

**In scope**:
- `templates/chat.html` — add localStorage save/load

**Out of scope**:
- Server-side chat persistence (SQLite).
- Cross-device sync.
- Conversation encryption.

## Git workflow

- Branch: `advisor/010-chat-persistence`
- Commit message: `feat: persist chat history in localStorage`
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Add localStorage load on page init

After `const conversation = [];`, add:

```javascript
// Load saved conversation from localStorage
try {
    const saved = localStorage.getItem('law_chat_history');
    if (saved) {
        conversation.push(...JSON.parse(saved));
    }
} catch (e) {
    // Corrupted data — start fresh
    localStorage.removeItem('law_chat_history');
}
```

### Step 2: Save after each successful exchange

In `sendChat()`, after `conversation.push({role: 'assistant', content: data.content})`,
add:

```javascript
// Save to localStorage
try {
    localStorage.setItem('law_chat_history', JSON.stringify(conversation));
} catch (e) {
    // Quota exceeded — remove oldest entries
    conversation.splice(0, conversation.length - 6);
    localStorage.setItem('law_chat_history', JSON.stringify(conversation));
}
```

### Step 3: Re-render saved messages on load

After loading from localStorage, re-render the conversation:

```javascript
// Re-render saved messages
if (conversation.length > 0) {
    // Clear the bot welcome message
    document.getElementById('chatMessages').innerHTML = '';
    for (const msg of conversation) {
        const content = msg.role === 'user'
            ? escapeHtml(msg.content)
            : renderMarkdown(msg.content);
        addMessage(msg.role, content);
    }
}
```

Place this after the localStorage load block, before the closing `}`.

### Step 4: Clear localStorage in clearChat()

In `clearChat()`, add:

```javascript
localStorage.removeItem('law_chat_history');
```

After `conversation.length = 0;`.

## Test plan

No automated tests (frontend-only). Verify manually:
1. Open chat page, send a message, get a response.
2. Refresh the page — conversation should be restored.
3. Click "پاک کردن" (clear) — conversation should be gone.
4. Refresh again — no conversation.

## Done criteria

- [ ] Chat messages survive page refresh
- [ ] `clearChat()` removes localStorage data
- [ ] Corrupted localStorage data doesn't crash the page (try/catch)
- [ ] No files outside the in-scope list are modified
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back if:

- `templates/chat.html` has changed significantly since the excerpts above.
- The project uses a framework (React, Vue) instead of vanilla JS — the plan
  assumes vanilla JS (it does).

## Maintenance notes

- localStorage has ~5MB quota. For very long conversations, the quota fallback
  keeps last 6 messages. Consider a cap (e.g., max 50 messages) if this becomes
  an issue.
- For server-side persistence, replace localStorage with a `POST /api/chat-history`
  endpoint storing to SQLite.
