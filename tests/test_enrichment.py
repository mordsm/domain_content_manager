import pytest
from app.db.database import init_db
from app.domain.capture import capture_engine
from app.domain.enrichment import enrichment_engine

@pytest.fixture(autouse=True)
def setup_database():
    init_db()

def test_enrichment_and_bidirectional_linking():
    rec1 = capture_engine.capture_text_or_url(title="מקור: סרטון על בריאות המעי", content_text="סרטון מקור מקיף על מיקרוביום המעי")
    rec2 = capture_engine.capture_text_or_url(title="אינפוגרפיק: מפת חיידקי המעי", content_text="אינפוגרפיק מסכם")

    enriched = enrichment_engine.enrich_record(
        record_id=rec2.id,
        primary_domain="health",
        domains=["health", "diet"],
        keywords=["מיקרוביום", "מעי", "בריאות"],
        summary="תמצית אינפוגרפית של חיידקי המעי",
        reliability_layer="research",
        risk_level="none",
        seasonality="year_round",
        related_record_ids=[rec1.id],
        relation_type="infographic_of"
    )

    assert enriched.status == "tagged"
    assert enriched.primary_domain == "health"
    assert enriched.is_cross_domain is True
