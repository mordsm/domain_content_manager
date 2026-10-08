import pytest
from app.db.database import init_db
from app.domain.capture import capture_engine

@pytest.fixture(autouse=True)
def setup_database():
    init_db()

def test_capture_text():
    rec = capture_engine.capture_text_or_url(
        title="מתכון למרק כתום",
        content_text="מתכון למרק כתום עם ג'ינג'ר וכורכום, מעולה לחיזוק מערכת החיסון בחורף.",
        primary_domain="culinary"
    )
    assert rec.id is not None
    assert rec.title == "מתכון למרק כתום"
    assert rec.primary_domain == "culinary"
    assert rec.status == "inbox"

def test_capture_voice():
    rec = capture_engine.capture_voice(
        voice_text="שמור לי טיפ לטיפוח שיער עם שמן חוחובה ורוזמרין"
    )
    assert rec.id is not None
    assert rec.source_type == "voice"
    assert rec.primary_domain in ["hair", "health", "general"]
