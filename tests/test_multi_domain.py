import pytest
from app.db.database import init_db
from app.domain.capture import capture_engine
from app.domain.retrieval import retrieval_engine
from app.services.llm_service import llm_service

@pytest.fixture(autouse=True)
def setup_database():
    init_db()

def test_mental_and_financial_classification():
    text_mental = "פרוטוקול מדיטציה ומיינדפולנס להפחתת מתח וחרדה"
    res_m = llm_service.analyze_content(text_mental)
    assert "mental" in res_m["domains"]

    text_financial = "מדריך פיננסי: ניהול תקציב משפחתי והשקעה במניות"
    res_f = llm_service.analyze_content(text_financial)
    assert "financial" in res_f["domains"]

def test_multi_domain_capture_and_retrieval():
    rec = capture_engine.capture_text_or_url(
        title="תוסף תזונה לבריאות המעי ולפוקוס מנטלי",
        content_text="מתכון לשייק ירוק עם פרוביוטיקה להורדת סטרס ולשיפור הבריאות",
        primary_domain="health",
        domains=["health", "mental", "culinary"]
    )
    assert rec.is_cross_domain is True
    assert "mental" in rec.domains_json
    assert "health" in rec.domains_json

    # Test that searching for 'mental' returns this record even though its primary_domain is 'health'
    res_mental = retrieval_engine.search(domain="mental")
    assert any(r.id == rec.id for r in res_mental)

    # Test that searching for 'health' also returns this record
    res_health = retrieval_engine.search(domain="health")
    assert any(r.id == rec.id for r in res_health)

def test_yaml_config_and_sub_topics():
    from app.services.config_service import domain_config_manager
    cfg = domain_config_manager.get_domains_dict()
    assert "mental" in cfg
    assert "financial" in cfg
    assert "mindfulness_meditation" in cfg["mental"]["sub_topics"]

    # Test sub-topic auto detection from text
    res = llm_service.analyze_content("אימון מדיטציה ונשימות להרגעת סטרס")
    assert "mental" in res["domains"]
    assert "mindfulness_meditation" in res["sub_topics"]

def test_sub_topic_search_filter():
    rec = capture_engine.capture_text_or_url(
        title="פרוטוקול חיסכון פנסיוני",
        content_text="תכנון פנסיה וריבית דריבית לעצמאות כלכלית",
        primary_domain="financial",
        sub_topics=["pension_fire"]
    )
    assert "pension_fire" in rec.sub_topics_json

    res = retrieval_engine.search(sub_topic="pension_fire")
    assert any(r.id == rec.id for r in res)

