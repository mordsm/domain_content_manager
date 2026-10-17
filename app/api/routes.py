import json
import uuid
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from app.schemas.content import ContentCaptureRequest, ContentEnrichRequest, CookPilotRequest, ContentUpdateRequest
from app.schemas.voice import VoiceCaptureRequest
from app.db.database import engine
from app.db.models import ContentRecord, ContentRelation
from sqlmodel import Session, select
from app.domain.capture import capture_engine
from app.domain.enrichment import enrichment_engine
from app.domain.retrieval import retrieval_engine
from app.domain.output_builder import output_builder_engine
from app.domain.obsidian_sync import obsidian_sync_engine
from app.domain.cook_pilot import cook_pilot_engine
from app.config import settings
from app.services.config_service import domain_config_manager

router = APIRouter(prefix="/api/v1")

@router.get("/config/domains")
def get_domains_config():
    """Returns the dynamic domains and sub-topics configuration from domains.yaml."""
    return domain_config_manager.get_domains_dict()

@router.post("/capture")
def capture_content(req: ContentCaptureRequest):
    record = capture_engine.capture_text_or_url(
        title=req.title,
        content_text=req.content_text,
        source_url=req.source_url,
        source_type=req.source_type,
        workspace_id=req.workspace_id,
        owner_id=req.owner_id,
        primary_domain=req.primary_domain,
        domains=req.domains,
        sub_topics=req.sub_topics,
        custom_tags=req.custom_tags
    )
    obsidian_sync_engine.export_record_to_markdown(record)
    return {"status": "CAPTURED", "record_id": record.id, "title": record.title, "domain": record.primary_domain}

@router.post("/capture/upload")
async def upload_file_capture(
    files: List[UploadFile] = File(None),
    file: Optional[UploadFile] = File(None),
    title: Optional[str] = Form(None),
    content_text: Optional[str] = Form(None),
    source_type: str = Form("infographic"),
    primary_domain: str = Form("general"),
    domains: Optional[str] = Form(None),
    sub_topics: Optional[str] = Form(None),
    custom_tags: Optional[str] = Form(None),
    workspace_id: str = Form("default_ws"),
    owner_id: str = Form("default_owner")
):
    uploads_dir = settings.DATA_DIR / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    
    upload_list = [f for f in (files or []) if f.filename]
    if file and file.filename and file not in upload_list:
        upload_list.append(file)

    if not upload_list:
        raise HTTPException(status_code=400, detail="לא נשלח קובץ להעלאה")

    saved_urls = []
    file_names = []

    for item in upload_list:
        unique_filename = f"{uuid.uuid4().hex[:10]}_{item.filename}"
        file_path = uploads_dir / unique_filename
        
        content_bytes = await item.read()
        with open(file_path, "wb") as f:
            f.write(content_bytes)
            
        saved_urls.append(f"/data/uploads/{unique_filename}")
        file_names.append(item.filename)
        
    web_url = saved_urls[0] if len(saved_urls) == 1 else json.dumps(saved_urls, ensure_ascii=False)
    
    parsed_domains = [d.strip() for d in domains.split(",")] if domains and domains.strip() else []
    parsed_sub_topics = [st.strip() for st in sub_topics.split(",")] if sub_topics and sub_topics.strip() else []
    parsed_tags = [t.strip() for t in custom_tags.split(",")] if custom_tags and custom_tags.strip() else []
    
    count_str = f" ({len(saved_urls)} קבצים)" if len(saved_urls) > 1 else ""
    record_title = title or f"אינפוגרפיקה: {', '.join(file_names[:2])}{count_str}"
    record_text = content_text or ""
    
    record = capture_engine.capture_text_or_url(
        title=record_title,
        content_text=record_text,
        source_url=web_url,
        source_type=source_type,
        workspace_id=workspace_id,
        owner_id=owner_id,
        primary_domain=primary_domain,
        domains=parsed_domains,
        sub_topics=parsed_sub_topics,
        custom_tags=parsed_tags
    )
    obsidian_sync_engine.export_record_to_markdown(record)
    return {
        "status": "UPLOADED_AND_CAPTURED",
        "record_id": record.id,
        "title": record.title,
        "files_count": len(saved_urls),
        "file_urls": saved_urls,
        "domain": record.primary_domain
    }

@router.post("/capture/voice")
def capture_voice(req: VoiceCaptureRequest):
    record = capture_engine.capture_voice(
        audio_path=req.audio_path_or_url,
        voice_text=req.voice_note_text,
        workspace_id=req.workspace_id,
        owner_id=req.owner_id
    )
    obsidian_sync_engine.export_record_to_markdown(record)
    return {"status": "CAPTURED_VOICE", "record_id": record.id, "title": record.title, "domain": record.primary_domain}

@router.post("/enrich")
def enrich_content(req: ContentEnrichRequest):
    try:
        record = enrichment_engine.enrich_record(
            record_id=req.record_id,
            primary_domain=req.primary_domain,
            domains=req.domains,
            sub_topics=req.sub_topics,
            custom_tags=req.custom_tags,
            keywords=req.keywords,
            summary=req.summary,
            why_saved=req.why_saved,
            personal_rating=req.personal_rating,
            reliability_layer=req.reliability_layer,
            risk_level=req.risk_level,
            seasonality=req.seasonality,
            domain_specific_data=req.domain_specific_data,
            related_record_ids=req.related_record_ids,
            relation_type=req.relation_type
        )
        obsidian_sync_engine.export_record_to_markdown(record)
        return {"status": "ENRICHED", "record_id": record.id, "status_flag": record.status}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/search")
def search_content(
    query: Optional[str] = None,
    domain: Optional[str] = None,
    sub_topic: Optional[str] = None,
    risk_level: Optional[str] = None,
    seasonality: Optional[str] = None
):
    results = retrieval_engine.search(
        query=query,
        domain=domain,
        sub_topic=sub_topic,
        risk_level=risk_level,
        seasonality=seasonality
    )
    voice_res = retrieval_engine.speak_results_summary(results)
    return {
        "count": len(results),
        "results": [r.dict() for r in results],
        "voice_feedback": voice_res["voice_script"]
    }

@router.post("/obsidian/sync")
def sync_obsidian():
    count = obsidian_sync_engine.sync_all()
    return {"status": "SYNCED", "exported_count": count}

@router.post("/outputs/build")
def build_output(record_ids: List[str], output_type: str = "post", target_title: str = "תוצר חדש"):
    try:
        res = output_builder_engine.assemble_output(
            record_ids=record_ids,
            output_type=output_type,
            target_title=target_title
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/cook-pilot/plan")
def plan_cook(req: CookPilotRequest):
    return cook_pilot_engine.plan_next_cook(
        workspace_id=req.workspace_id,
        owner_id=req.owner_id,
        goal=req.goal,
        available_ingredients=req.available_ingredients,
        avoid_ingredients=req.avoid_ingredients,
        dietary_preferences=req.dietary_preferences,
        equipment=req.equipment,
        servings=req.servings,
        max_minutes=req.max_minutes,
        voice_input=req.voice_input,
        current_step=req.current_step,
        command=req.command,
        include_saved_sources=req.include_saved_sources,
    )

@router.post("/records/{record_id}/cover-image")
async def add_record_cover_image(record_id: str, file: UploadFile = File(...)):
    uploads_dir = settings.DATA_DIR / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    
    unique_filename = f"{uuid.uuid4().hex[:10]}_{file.filename}"
    file_path = uploads_dir / unique_filename
    
    content_bytes = await file.read()
    with open(file_path, "wb") as f:
        f.write(content_bytes)
        
    img_url = f"/data/uploads/{unique_filename}"
    
    with Session(engine) as session:
        record = session.get(ContentRecord, record_id)
        if not record:
            raise HTTPException(status_code=404, detail="רשומה לא נמצאה")
            
        if not record.source_url:
            record.source_url = img_url
        else:
            try:
                urls = json.loads(record.source_url)
                if isinstance(urls, list):
                    urls.append(img_url)
                    record.source_url = json.dumps(urls, ensure_ascii=False)
                else:
                    record.source_url = json.dumps([record.source_url, img_url], ensure_ascii=False)
            except Exception:
                record.source_url = json.dumps([record.source_url, img_url], ensure_ascii=False)
                
        session.add(record)
        session.commit()
        session.refresh(record)
        
        obsidian_sync_engine.export_record_to_markdown(record)
        return {"status": "COVER_IMAGE_ADDED", "record_id": record.id, "cover_url": img_url, "source_url": record.source_url}

@router.get("/records/{record_id}/markdown")
def get_record_markdown(record_id: str):
    with Session(engine) as session:
        record = session.get(ContentRecord, record_id)
        if not record:
            raise HTTPException(status_code=404, detail="רשומה לא נמצאה")
        filepath = obsidian_sync_engine.export_record_to_markdown(record)
        if filepath and filepath.exists():
            return FileResponse(filepath, media_type="text/markdown", filename=filepath.name)
        raise HTTPException(status_code=404, detail="קובץ Markdown לא נמצא")

@router.delete("/records/{record_id}")
def delete_record(record_id: str):
    with Session(engine) as session:
        record = session.get(ContentRecord, record_id)
        if not record:
            raise HTTPException(status_code=404, detail="רשומה לא נמצאה")
        
        # Delete related links
        relations = session.exec(
            select(ContentRelation).where(
                (ContentRelation.source_id == record_id) | (ContentRelation.target_id == record_id)
            )
        ).all()
        for rel in relations:
            session.delete(rel)
            
        # Delete Obsidian markdown file
        obsidian_sync_engine.delete_record_markdown(record)
        
        session.delete(record)
        session.commit()
        return {"status": "DELETED", "record_id": record_id}

@router.put("/records/{record_id}")
def update_record(record_id: str, req: ContentUpdateRequest):
    with Session(engine) as session:
        record = session.get(ContentRecord, record_id)
        if not record:
            raise HTTPException(status_code=404, detail="רשומה לא נמצאה")
        
        if req.title is not None:
            record.title = req.title
        if req.summary is not None:
            record.summary = req.summary
        if req.transcript is not None:
            record.transcript = req.transcript
        if req.primary_domain is not None:
            record.primary_domain = req.primary_domain
        if req.domains is not None:
            record.domains_json = json.dumps(req.domains, ensure_ascii=False)
        if req.sub_topics is not None:
            record.sub_topics_json = json.dumps(req.sub_topics, ensure_ascii=False)
        if req.custom_tags is not None:
            record.custom_tags_json = json.dumps(req.custom_tags, ensure_ascii=False)
        if req.source_url is not None:
            record.source_url = req.source_url
        if req.source_type is not None:
            record.source_type = req.source_type

        session.add(record)
        session.commit()
        session.refresh(record)

        obsidian_sync_engine.export_record_to_markdown(record)
        return {"status": "UPDATED", "record_id": record.id, "title": record.title}




