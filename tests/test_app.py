import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def test_index_page(db_config):
    """Home page loads."""
    response = client.get("/")
    assert response.status_code == 200


def test_search_page(db_config):
    """Search page loads."""
    response = client.get("/search")
    assert response.status_code == 200


def test_api_stats(db_config):
    """Stats endpoint returns JSON."""
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_opinions" in data
    assert "ai_available" in data


def test_api_keyword_search(db_config):
    """Keyword search returns results or empty list."""
    response = client.get("/api/search?q=test")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert isinstance(data["results"], list)


def test_api_keyword_search_min_length(db_config):
    """Empty query rejected."""
    response = client.get("/api/search?q=")
    assert response.status_code == 422  # FastAPI validation error


def test_chat_page_requires_ai(db_config, monkeypatch):
    """Chat page returns 400 when AI not configured."""
    import config as cfg
    monkeypatch.setattr(cfg, "ai_available", lambda: False)
    # Patch the reference in the app module too
    import app as app_mod
    monkeypatch.setattr(app_mod, "config", cfg)
    response = client.get("/chat")
    assert response.status_code == 400
