import pytest
from app.db.database import init_db
from app.domain.capture import capture_engine
from app.domain.obsidian_sync import obsidian_sync_engine

@pytest.fixture(autouse=True)
def setup_database():
    init_db()

def test_obsidian_export():
    rec = capture_engine.capture_text_or_url(title="בדיקת ייצוא לאובסידיאן", content_text="תוכן בדיקה עבור Obsidian Vault Export")
    path = obsidian_sync_engine.export_record_to_markdown(rec)
    
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert "id: \"" + rec.id in content
    assert "בדיקת ייצוא לאובסידיאן" in content
