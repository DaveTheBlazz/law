# ⚖️ پایگاه نظریات حقوقی — Law Opinions Search

A web application for searching and exploring the Iranian Judiciary's legal opinions database (`opinions.csv`).

## Features

| Feature | Description |
|---|---|
| 🔤 **Keyword Search** | Fast substring search across questions and rulings |
| 🧠 **Semantic Search** | AI-powered search using embeddings — finds related opinions even without exact keyword matches |
| 💬 **Chatbot** | Ask legal questions in Persian; the bot searches relevant opinions and answers with citations |
| 📱 **Responsive UI** | RTL Persian interface, works on desktop and mobile |

## Quick Start

```bash
# 1. Activate virtual environment
.venv\Scripts\activate

# 2. (Optional) Configure AI — copy and edit
copy .env.example .env

# 3. Run
python main.py
```

Then open **http://localhost:8000** in your browser.

## Configuration (`.env`)

Copy `.env.example` to `.env` and edit:

```ini
# AI Model (OpenAI-compatible API)
AI_BASE_URL=https://api.openai.com/v1
AI_API_KEY=sk-your-key-here
AI_MODEL=gpt-4o-mini

# Embedding Model (for semantic search)
AI_EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536

# App
APP_HOST=0.0.0.0
APP_PORT=8000

# Data
CSV_PATH=opinions.csv
DB_PATH=law.db
SEMANTIC_TOP_K=20
```

## Project Structure

```
law/
├── app.py              # FastAPI application (routes + API)
├── config.py           # Environment config loader
├── database.py         # SQLite DB layer (CSV import, search, embeddings)
├── main.py             # Entry point / startup script
├── requirements.txt    # Python dependencies
├── .env.example        # Configuration template
├── templates/          # Jinja2 HTML templates
│   ├── base.html       # Base layout (nav, CSS, RTL)
│   ├── index.html      # Home page with hero search
│   ├── search.html     # Keyword + semantic search UI
│   └── chat.html       # Chatbot interface
├── static/             # Static assets
├── opinions.csv        # Source data (12,239 opinions)
├── law.db              # Auto-created SQLite database
└── .venv/              # Python virtual environment
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/search?q=طلاق&limit=50` | Keyword search |
| POST | `/api/semantic-search` | Semantic search (`{"query": "...", "top_k": 20}`) |
| POST | `/api/chat-with-search` | Chat with auto-retrieval (streaming SSE) |
| POST | `/api/embed-all` | Compute embeddings for all opinions |
| GET | `/api/stats` | Database statistics |

## Without AI

The app works without AI configuration — keyword search is fully functional. Semantic search and the chatbot require an OpenAI-compatible API key.
