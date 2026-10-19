from unittest.mock import patch, MagicMock
from app.services.video_metadata import (
    fetch_video_metadata,
    clean_video_title
)
from app.services.config_service import domain_config_manager
from app.domain.capture import CaptureEngine
from app.db.database import init_db


def test_clean_video_title():
    assert clean_video_title("Rick Astley - Never Gonna Give You Up - YouTube") == "Rick Astley - Never Gonna Give You Up"
    assert clean_video_title("איך מכינים מרק ירקות קל ב-10 דקות - YouTube") == "איך מכינים מרק ירקות קל ב-10 דקות"


def test_analyze_text_for_video_domain():
    res_soup = domain_config_manager.analyze_text_with_config("איך להכין מרק כתום וירקות מוקפצים")
    assert res_soup["primary_domain"] == "culinary"
    assert "soups" in res_soup["sub_topics"]

    res_hair = domain_config_manager.analyze_text_with_config("טיפול טבעי בנשירת שיער ושיפור עור הפנים")
    assert res_hair["primary_domain"] == "health"
    assert "hair" in res_hair["sub_topics"]


@patch("app.services.video_metadata.httpx.get")
def test_fetch_video_metadata_mocked(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "title": "מתכון למרק ירקות עשיר ומשביע - YouTube",
        "author_name": "השף הפשוט",
        "thumbnail_url": "https://img.youtube.com/vi/test/hqdefault.jpg"
    }
    mock_get.return_value = mock_resp

    meta = fetch_video_metadata("https://www.youtube.com/watch?v=mock123")
    assert meta["title"] == "מתכון למרק ירקות עשיר ומשביע"
    assert meta["primary_domain"] == "culinary"
    assert "soups" in meta["sub_topics"]
    assert meta["primary_domain_he"] == "קולינריה"


def test_capture_dual_media_and_obsidian_sync(tmp_path):
    init_db()
    capture_engine = CaptureEngine()

    record = capture_engine.capture_text_or_url(
        title="מדריך תזונה משולב",
        content_text="סרטון הדרכה עם אינפוגרפיקה מפורטת",
        source_url='["https://www.youtube.com/watch?v=dQw4w9WgXcQ", "/data/uploads/chart1.png"]',
        original_media_url="/data/uploads/chart1.png",
        primary_domain="health",
        workspace_id="test_ws",
        owner_id="test_user"
    )

    assert record.id is not None
    assert "https://www.youtube.com/watch?v=dQw4w9WgXcQ" in record.source_url
    assert "/data/uploads/chart1.png" in record.source_url

    # Test Obsidian Export with Dual Media
    from app.domain.obsidian_sync import ObsidianSyncEngine
    from app.config import settings
    settings.VAULT_DIR = tmp_path
    sync_engine = ObsidianSyncEngine()
    filepath = sync_engine.export_record_to_markdown(record)
    assert filepath.exists()

    content = filepath.read_text(encoding="utf-8")
    assert "## 🎥 סרטון ומקור (Video & Source)" in content
    assert "https://www.youtube.com/watch?v=dQw4w9WgXcQ" in content
    assert "## 🖼️ אינפוגרפיקות ותמונות (Infographics)" in content
    assert "/data/uploads/chart1.png" in content
    assert "has_video: true" in content
    assert "has_infographics: true" in content
