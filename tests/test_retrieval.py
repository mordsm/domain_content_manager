import pytest
from app.db.database import init_db
from app.domain.capture import capture_engine
from app.domain.retrieval import retrieval_engine

@pytest.fixture(autouse=True)
def setup_database():
    init_db()

def test_search_and_surprise_me():
    rec = capture_engine.capture_text_or_url(title="מדריך גינון ביתי", content_text="איך לשתול נענע ולואיזה בגינה", primary_domain="garden")
    results = retrieval_engine.search(query="נענע", domain="garden")
    assert len(results) >= 1
    assert results[0].primary_domain == "garden"

    surprise = retrieval_engine.surprise_me(domain="garden")
    assert surprise is not None
