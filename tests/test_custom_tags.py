import pytest
from app.db.database import init_db
from app.domain.capture import capture_engine
from app.domain.retrieval import retrieval_engine
from app.services.llm_service import llm_service

@pytest.fixture(autouse=True)
def setup_database():
    init_db()

def test_smart_keyword_extraction_from_transcript():
    transcript = """
    ברוכים הבאים לפודקאסט הבריאות. היום נתרגל מדיטציית סריקת גוף להורדת סטרס וחרדה.
    במחקרים קליניים נמצא כי שמן רוזמרין 2% ועיסוי קרקפת משפרים את זרימת הדם בקרקפת.
    """
    keywords = llm_service.extract_keywords_from_text(transcript)
    assert len(keywords) > 0
    # Verify mined keyphrases / terms like 'סריקת_גוף' or 'שמן_רוזמרין' or 'עיסוי_קרקפת'
    assert any("רוזמרין" in k or "מדיטציית" in k or "סטרס" in k for k in keywords)

def test_custom_user_tags_capture_and_search():
    rec = capture_engine.capture_text_or_url(
        title="פודקאסט בריאות המעי",
        content_text="תמליל פודקאסט על מיקרוביום ובוטיראט",
        primary_domain="health",
        custom_tags=["פודקאסט_מומלץ", "אביב_2026"]
    )
    assert "פודקאסט_מומלץ" in rec.custom_tags_json
    assert "אביב_2026" in rec.custom_tags_json

    # Test search by custom tag query
    res = retrieval_engine.search(query="אביב_2026")
    assert any(r.id == rec.id for r in res)

