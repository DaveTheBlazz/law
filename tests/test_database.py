import pytest
from database import initialize_db, keyword_search, get_total_count, normalize_text


def test_normalize_text(db_config):
    assert normalize_text("  hello  ") == "hello"
    assert normalize_text("\u200c") == ""  # zero-width non-joiner removed
    assert normalize_text("ي") == "ی"  # Arabic Ya → Persian Ya
    assert normalize_text("ك") == "ک"  # Arabic Kaf → Persian Kaf
    assert normalize_text("") == ""


def test_initialize_db_creates_table(db_config):
    initialize_db()  # with no CSV, creates empty table
    assert get_total_count() == 0


def test_keyword_search_empty(db_config):
    initialize_db()
    results = keyword_search("nonexistent")
    assert results == []


def test_keyword_search_with_data(db_config, tmp_path):
    # Create a minimal CSV for testing
    csv_file = tmp_path / "test.csv"
    csv_file.write_text(
        "url,nezariye_number,parvandeh_number,date,estelam,nezariye\n"
        "http://example.com,123,456,1402/01/01,سوال درباره طلاق,نظر درباره طلاق\n"
        "http://example.com,124,457,1402/01/02,سوال درباره مهریه,نظر درباره مهریه\n",
        encoding="utf-8",
    )
    import config
    config.CSV_PATH = str(csv_file)
    initialize_db()
    assert get_total_count() == 2

    results = keyword_search("طلاق")
    assert len(results) == 1
    assert results[0]["nezariye_number"] == "123"

    results = keyword_search("مهریه")
    assert len(results) == 1
    assert results[0]["nezariye_number"] == "124"

    # Multi-term search (both terms must match)
    results = keyword_search("طلاق مهریه")
    assert len(results) == 0  # no single row has both
