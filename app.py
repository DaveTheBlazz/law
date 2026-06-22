"""FastAPI web application — search + chatbot for legal opinions."""

import re
from contextlib import asynccontextmanager

import config
from database import (
    initialize_db,
    keyword_search,
    get_total_count,
    get_embedding_count,
    _get_conn,
)
from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from openai import OpenAI

# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_db()
    yield

app = FastAPI(title=config.APP_TITLE, lifespan=lifespan)
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# OpenAI client (lazy init — avoids crash at import time when key is missing)
_ai_client = None

def get_ai_client():
    global _ai_client
    if _ai_client is None:
        _ai_client = OpenAI(
            base_url=config.AI_BASE_URL,
            api_key=config.AI_API_KEY,
        )
    return _ai_client


def call_llm(messages, max_tokens=2048):
    """Call the LLM and return content string."""
    if not config.ai_available():
        return None
    r = get_ai_client().chat.completions.create(
        model=config.AI_MODEL,
        messages=messages,
        max_tokens=max_tokens,
        extra_body={"chat_template_kwargs": {"enable_thinking": False}},
    )
    msg = r.choices[0].message
    return msg.content or "", r.usage


# ---------------------------------------------------------------------------
# Page routes
# ---------------------------------------------------------------------------

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {
        "app_title": config.APP_TITLE,
        "total": get_total_count(),
        "embedded": get_embedding_count(),
        "ai_available": config.ai_available(),
    })

@app.get("/search")
async def search_page(request: Request):
    return templates.TemplateResponse(request, "search.html", {
        "app_title": config.APP_TITLE,
        "total": get_total_count(),
        "embedded": get_embedding_count(),
        "ai_available": config.ai_available(),
    })

@app.get("/chat")
async def chat_page(request: Request):
    if not config.ai_available():
        raise HTTPException(400, "AI not configured. Set AI_API_KEY and AI_BASE_URL in .env")
    return templates.TemplateResponse(request, "chat.html", {
        "app_title": config.APP_TITLE,
        "ai_available": True,
    })

# ---------------------------------------------------------------------------
# API — All Opinions
# ---------------------------------------------------------------------------

@app.get("/api/all-opinions")
async def api_all_opinions(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    conn = _get_conn()
    try:
        total = conn.execute("SELECT COUNT(*) FROM opinions").fetchone()[0]
        rows = conn.execute(
            "SELECT id, url, nezariye_number, parvandeh_number, date, estelam, nezariye "
            "FROM opinions LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return {
            "total": total,
            "count": len(rows),
            "offset": offset,
            "limit": limit,
            "results": [dict(r) for r in rows],
        }
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# API — Keyword Search
# ---------------------------------------------------------------------------

@app.get("/api/search")
async def api_keyword_search(
    q: str = Query(..., min_length=1),
    columns: str = Query("estelam,nezariye"),
    limit: int = Query(50, ge=1, le=500),
):
    results = keyword_search(q, columns=columns.split(","), limit=limit)
    return {"query": q, "count": len(results), "results": results}


# ---------------------------------------------------------------------------
# API — Smart Search (keyword → LLM rerank)
# ---------------------------------------------------------------------------

@app.post("/api/semantic-search")
async def api_semantic_search(request: Request):
    if not config.ai_available():
        return JSONResponse(status_code=400, content={"error": "AI not configured"})

    body = await request.json()
    q = body.get("query", "")
    top_k = body.get("top_k", config.SEMANTIC_TOP_K)
    if not q:
        return JSONResponse(status_code=400, content={"error": "query required"})

    # 1. Keyword search for candidates
    candidates = keyword_search(q, limit=50)
    if not candidates:
        return {"query": q, "count": 0, "results": []}

    # 2. LLM picks most relevant
    compact = []
    for i, op in enumerate(candidates[:30], 1):
        compact.append(f"#{i} | {op['nezariye_number']} | {op['estelam'][:200]}")

    prompt = (
        f"کاربر این سوال را پرسیده: \"{q}\"\n\n"
        f"فقط شماره نظریه‌های مرتبط را از ۱ تا ۳۰ بنویس (حداکثر {min(top_k, 15)} تا)، هر شماره در یک خط:\n\n"
        + "\n".join(compact)
    )

    content, _ = call_llm([
        {"role": "system", "content": "فقط شماره نظریه‌های مرتبط را بنویس."},
        {"role": "user", "content": prompt},
    ])

    # Extract numbers
    selected_nums = set()
    for m in re.finditer(r'#?(\d+)', content or ""):
        num = int(m.group(1))
        if 1 <= num <= len(compact):
            selected_nums.add(num)

    if selected_nums:
        selected = [candidates[n - 1] for n in sorted(selected_nums) if n - 1 < len(candidates)]
        candidates = selected[:top_k]

    return {"query": q, "count": len(candidates), "results": candidates}


# ---------------------------------------------------------------------------
# API — Simple Chat (no RAG)
# ---------------------------------------------------------------------------

@app.post("/api/chat")
async def api_chat(request: Request):
    if not config.ai_available():
        return JSONResponse(status_code=400, content={"error": "AI not configured"})

    body = await request.json()
    messages = body.get("messages", [])

    content, usage = call_llm(messages)
    if content is None:
        return JSONResponse(status_code=500, content={"error": "LLM error"})

    return {"content": content, "usage": usage}


# ---------------------------------------------------------------------------
# API — Chat with Search (RAG)
# ---------------------------------------------------------------------------

@app.post("/api/chat-with-search")
async def api_chat_with_search(request: Request):
    if not config.ai_available():
        return JSONResponse(status_code=400, content={"error": "AI not configured"})

    body = await request.json()
    user_query = body.get("query", "")
    conversation = body.get("conversation", [])
    top_k = min(body.get("top_k", 5), 8)

    # 1. Keyword search
    opinions = keyword_search(user_query, limit=20)
    if not opinions:
        search_terms = user_query.split()
        for term in search_terms:
            opinions = keyword_search(term, limit=20)
            if opinions:
                break

    # 2. Build concise context
    context_parts = [f"[{op['nezariye_number']}] {op['nezariye'][:200]}" for op in opinions[:top_k]]
    context = "\n".join(context_parts) if context_parts else "نظریه مرتبطی یافت نشد."

    # 3. Messages
    messages = [
        {"role": "system", "content": config.SYSTEM_PROMPT},
    ]
    for msg in conversation[-6:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": f"نظریات:\n{context}\n\nسوال: {user_query}"})

    # 4. Call LLM
    content, usage = call_llm(messages)
    if content is None:
        return JSONResponse(status_code=500, content={"error": "LLM error"})

    sources = []
    for op in opinions[:top_k]:
        sources.append({
            "nezariye_number": op["nezariye_number"],
            "url": op["url"],
            "estelam": op["estelam"],
            "nezariye": op["nezariye"],
            "parvandeh_number": op.get("parvandeh_number", ""),
            "date": op.get("date", ""),
        })
    return {
        "content": content,
        "sources": sources,
        "opinions_count": len(opinions),
        "usage": usage,
    }


# ---------------------------------------------------------------------------
# API — Stats
# ---------------------------------------------------------------------------

@app.get("/api/stats")
async def api_stats():
    return {
        "total_opinions": get_total_count(),
        "embedded": get_embedding_count(),
        "ai_available": config.ai_available(),
    }
