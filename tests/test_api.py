import pytest
from fastapi.testclient import TestClient
from app.db.database import init_db
from app.api.main import app

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

client = TestClient(app)

def test_api_root():
    res = client.get("/")
    assert res.status_code == 200
    assert "Domain Content Manager" in res.text

def test_api_root_contains_cook_pilot_ui():
    res = client.get("/cook-pilot")
    assert res.status_code == 200
    html = res.text
    assert "Cook Pilot" in html
    assert "Shared Obsidian backbone only" in html
    assert "buildRequest" in html
    assert "validateRequest" in html
    assert "setBusy" in html
    assert "timerSummary" in html
    assert "riskSummary" in html
    assert "sourceSummary" in html
    assert "printableSummary" in html
    assert "renderPlan" in html
    assert "planCook" in html
    assert "saveSession" in html
    assert "saveDraft" in html
    assert "restoreDraft" in html

def test_api_capture_and_search():
    cap_res = client.post("/api/v1/capture", json={
        "title": "פוסט בדיקת API",
        "content_text": "תוכן עבור בדיקת שרשרת API",
        "primary_domain": "health"
    })
    assert cap_res.status_code == 200
    data = cap_res.json()
    assert data["status"] == "CAPTURED"

    search_res = client.get("/api/v1/search?domain=health")
    assert search_res.status_code == 200
    s_data = search_res.json()
    assert s_data["count"] >= 1

def test_api_upload_multiple_files():
    files = [
        ('files', ('test1.jpg', b'image data 1', 'image/jpeg')),
        ('files', ('test2.jpg', b'image data 2', 'image/jpeg')),
        ('files', ('test3.jpg', b'image data 3', 'image/jpeg')),
    ]
    data = {
        'title': 'אינפוגרפיקות מרובות לבדיקה',
        'primary_domain': 'health',
        'source_type': 'infographic'
    }
    res = client.post("/api/v1/capture/upload", files=files, data=data)
    assert res.status_code == 200
    res_data = res.json()
    assert res_data["status"] == "UPLOADED_AND_CAPTURED"
    assert res_data["files_count"] == 3
    assert len(res_data["file_urls"]) == 3

def test_api_delete_record():
    # 1. Capture a temporary record
    cap_res = client.post("/api/v1/capture", json={
        "title": "פריט למחיקה",
        "content_text": "תוכן שמיועד למחיקה מיידית",
        "primary_domain": "general"
    })
    assert cap_res.status_code == 200
    rec_id = cap_res.json()["record_id"]

    # 2. Delete it
    del_res = client.delete(f"/api/v1/records/{rec_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "DELETED"

    # 3. Verify it is gone
    del_again = client.delete(f"/api/v1/records/{rec_id}")
    assert del_again.status_code == 404

def test_api_update_record():
    # 1. Capture a record
    cap_res = client.post("/api/v1/capture", json={
        "title": "כותרת ישנה",
        "content_text": "תוכן ישן",
        "primary_domain": "health"
    })
    assert cap_res.status_code == 200
    rec_id = cap_res.json()["record_id"]

    # 2. Update it
    put_res = client.put(f"/api/v1/records/{rec_id}", json={
        "title": "כותרת מעודכנת חדשה",
        "summary": "תקציר מעודכן",
        "transcript": "תוכן חדש ומפורט"
    })
    assert put_res.status_code == 200
    assert put_res.json()["status"] == "UPDATED"

    # 3. Check search returns new title
    search_res = client.get("/api/v1/search?domain=health")
    assert search_res.status_code == 200
    titles = [r["title"] for r in search_res.json()["results"]]
    assert "כותרת מעודכנת חדשה" in titles



