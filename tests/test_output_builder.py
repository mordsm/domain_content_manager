import pytest
from app.db.database import init_db
from app.domain.capture import capture_engine
from app.domain.output_builder import output_builder_engine

@pytest.fixture(autouse=True)
def setup_database():
    init_db()

def test_output_assembly():
    rec1 = capture_engine.capture_text_or_url(title="מקור 1: מרק גזר", content_text="מרק גזר עשיר בוויטמין A", primary_domain="culinary")
    rec2 = capture_engine.capture_text_or_url(title="מקור 2: שילוב תבלינים", content_text="שילוב ג'ינג'ר וכורכום", primary_domain="culinary")

    res = output_builder_engine.assemble_output(
        record_ids=[rec1.id, rec2.id],
        output_type="guide",
        target_title="מדריך מרקי חורף"
    )

    assert res["sources_count"] == 2
    assert "מדריך מרקי חורף" in res["title"]
    assert "מקריא בקול" in res["voice_script"]
