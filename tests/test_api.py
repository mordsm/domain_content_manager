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

