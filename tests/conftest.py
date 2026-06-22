import pytest
from database import initialize_db


@pytest.fixture(autouse=True)
def db_config(test_db_path, monkeypatch):
    """Patch config to use temp DB, initialize tables, and provide no CSV."""
    monkeypatch.setattr("config.DB_PATH", test_db_path)
    monkeypatch.setattr("config.CSV_PATH", "")
    initialize_db()  # create tables for this temp DB
    yield test_db_path


@pytest.fixture
def test_db_path(tmp_path):
    """Return a temp DB path for tests."""
    return str(tmp_path / "test.db")
