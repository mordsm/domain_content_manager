import json
from sqlmodel import Session
from app.db.database import engine
from app.db.models import ContentRecord
from app.services.llm_service import llm_service
from app.services.stt_service import stt_service

class CaptureEngine:
    def capture_text_or_url(
        self,
        title: str = None,
        content_text: str = None,
        source_url: str = None,
        source_type: str = "note",
        workspace_id: str = "default_ws",
        owner_id: str = "default_owner",
        primary_domain: str = "general",
        domains: list = None,
        sub_topics: list = None,
        custom_tags: list = None
    ) -> ContentRecord:
        text_to_analyze = content_text or title or source_url or ""
        analysis = llm_service.analyze_content(text_to_analyze, source_url=source_url)

        final_source_url = source_url or analysis.get("detected_video_url")
        final_source_type = source_type
        if source_type == "note" and analysis.get("is_video"):
            final_source_type = "video"

        record_title = title or (final_source_url if final_source_url else text_to_analyze[:30]) or "רשומה חדשה"

        final_domains = domains if domains else analysis["domains"]
        final_sub_topics = sub_topics if sub_topics is not None else analysis.get("sub_topics", [])
        final_custom_tags = custom_tags if custom_tags is not None else []
        final_primary = primary_domain if primary_domain != "general" else (final_domains[0] if final_domains else analysis["primary_domain"])
        
        # Ensure final_primary is in final_domains
        if final_primary not in final_domains:
            final_domains.insert(0, final_primary)

        record = ContentRecord(
            workspace_id=workspace_id,
            owner_id=owner_id,
            title=record_title,
            source_url=final_source_url,
            source_type=final_source_type,
            transcript=content_text,
            summary=analysis["summary"],
            keywords_json=json.dumps(analysis["keywords"], ensure_ascii=False),
            primary_domain=final_primary,
            domains_json=json.dumps(final_domains, ensure_ascii=False),
            sub_topics_json=json.dumps(final_sub_topics, ensure_ascii=False),
            custom_tags_json=json.dumps(final_custom_tags, ensure_ascii=False),
            is_cross_domain=len(final_domains) > 1,
            risk_level=analysis["risk_level"],
            reliability_layer=analysis["reliability_layer"],
            status="inbox"
        )

        with Session(engine) as session:
            session.add(record)
            session.commit()
            session.refresh(record)

        return record

    def capture_voice(
        self,
        audio_path: str = None,
        voice_text: str = None,
        workspace_id: str = "default_ws",
        owner_id: str = "default_owner"
    ) -> ContentRecord:
        transcript = voice_text or (stt_service.transcribe(audio_path) if audio_path else "הודעה קולית")
        intent_res = llm_service.parse_voice_intent(transcript)

        return self.capture_text_or_url(
            title=intent_res["suggested_title"],
            content_text=transcript,
            source_type="voice",
            workspace_id=workspace_id,
            owner_id=owner_id,
            primary_domain=intent_res["suggested_domain"]
        )

capture_engine = CaptureEngine()
