# Law Opinions App — Summary

## Overview

FastAPI web app for searching 12,239 Persian legal opinions (`opinions.csv` from Iranian Judiciary) with keyword search, smart search (LLM reranking), and RAG chatbot.

**Running:** `http://localhost:8080`

## AI Config (`.env`)

| Setting | Value |
|---|---|
| URL | `https://chat.telsaco.ir/v1` |
| Key | `aplserghsoleirhg35366` |
| Model | `Qwen3.6-27B-Q4_K_M.gguf` |
| Thinking | Disabled: `extra_body={"chat_template_kwargs": {"enable_thinking": False}}` |
| Embeddings | **Not supported** by server |
| Library | `openai` Python package (not raw `aiohttp`) |

## Files

| File | Purpose |
|---|---|
| `app.py` | FastAPI app — all routes + API, uses `openai` library |
| `config.py` | `.env` loader, system prompt |
| `database.py` | SQLite — CSV import, keyword search (SQL LIKE), embedding storage (unused) |
| `run.py` | Startup: `python run.py` |
| `.env` | Config (port 8080, AI credentials) |
| `.env.example` | Template |
| `requirements.txt` | `fastapi uvicorn jinja2 python-dotenv aiohttp numpy openai` |
| `law.db` | Auto-created SQLite DB |
| `templates/base.html` | RTL layout, nav, CSS (Vazirmatn font) |
| `templates/index.html` | Home: hero search, popular topics, stats |
| `templates/search.html` | Tabs: keyword + smart (LLM rerank) |
| `templates/chat.html` | Chatbot: typing indicator, markdown, conversation history |

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/` | Home page |
| GET | `/search` | Search page |
| GET | `/chat` | Chat page |
| GET | `/api/search?q=...&limit=50` | Keyword search (SQL LIKE, instant) |
| POST | `/api/semantic-search` | Smart: keyword → LLM picks relevant (~10s) |
| POST | `/api/chat` | Simple chat, no RAG (~8s) |
| POST | `/api/chat-with-search` | Chat + RAG (~9s) |
| GET | `/api/stats` | DB stats |

## Architecture

```
User → FastAPI
  ├─ Keyword → SQLite LIKE query → instant
  ├─ Smart → SQLite LIKE (50) → OpenAI LLM picks top-K
  └─ Chat → SQLite LIKE (20) → OpenAI LLM with context (RAG)
```

## Key Fixes Applied

1. **Reasoning model** — outputs `reasoning_content` + `content`; must use `enable_thinking: false` or content is empty
2. **SSE streaming broken** — server streams reasoning as SSE; switched to non-streaming JSON via `openai` library
3. **No embeddings** — server returns 501; switched to keyword search + LLM reranking
4. **BOM in CSV** — first column had `\ufeff` prefix; handled with `utf-8-sig` encoding
5. **Windows console** — UTF-8 output fix for Persian text in CLI tools
6. **FastAPI TemplateResponse API change** — `TemplateResponse(request, name, context)` instead of old signature
7. **SQL optimization** — keyword search uses `LIKE` query instead of loading all rows to memory

## Performance

| Feature | Time |
|---|---|
| Keyword search | <1s |
| Chat | ~8s |
| Chat + RAG | ~9s |
| Smart search | ~10s |

## Known Issues

- Port 8000 blocked on this machine; using 8080
- Multiple stale uvicorn processes on port 8004 from earlier testing
- `database.py` has unused embedding code
- No `favicon.ico` (404 on load)
- Chat history lost on page refresh (no persistence)

## Run Command

```bash
cd C:\Users\Dave\projects\law
.venv\Scripts\python.exe -m uvicorn app:app --host 0.0.0.0 --port 8080 --reload
```

## TODO

- [ ] Kill stale uvicorn processes on port 8004
- [ ] Clean unused embedding/streaming code from `database.py`
- [ ] Add chat persistence (localStorage or SQLite)
- [ ] Add loading progress bar for slow AI calls
- [ ] Add favicon
- [ ] Optimize smart search (reduce LLM rerank candidates)
