import json
from typing import Optional, List, Union
from sqlmodel import Session
from app.db.database import engine
from app.db.models import ContentRecord
from app.services.llm_service import llm_service
from app.services.stt_service import stt_service
from app.services.video_metadata import fetch_video_metadata, extract_video_url_from_text

class CaptureEngine:
    def capture_text_or_url(
        self,
        title: str = None,
        content_text: str = None,
        source_url: Union[str, List[str]] = None,
        source_type: str = "note",
        workspace_id: str = "default_ws",
        owner_id: str = "default_owner",
        primary_domain: str = "general",
        domains: list = None,
        sub_topics: list = None,
        custom_tags: list = None,
        original_media_url: str = None
    ) -> ContentRecord:
        # 1. Parse and normalize source URLs (could be single string, list, or JSON list)
        all_urls = []
        if isinstance(source_url, list):
            all_urls = [u for u in source_url if u]
        elif source_url:
            try:
                parsed = json.loads(source_url)
                if isinstance(parsed, list):
                    all_urls = [u for u in parsed if u]
                else:
                    all_urls = [source_url.strip()]
            except Exception:
                all_urls = [source_url.strip()]

        if original_media_url and original_media_url not in all_urls:
            all_urls.append(original_media_url)

        # 2. Check for video URL in source_url or content_text
        video_url = None
        for u in all_urls:
            extracted = extract_video_url_from_text(u)
            if extracted:
                video_url = extracted
                break
        if not video_url and content_text:
            video_url = extract_video_url_from_text(content_text)
            if video_url and video_url not in all_urls:
                all_urls.insert(0, video_url)

        # 3. If video detected and title is missing or generic, auto-fetch from video metadata
        video_meta = {}
        if video_url:
            raw_title_clean = (title or "").strip()
            # If no title or title is just the URL itself
            if not raw_title_clean or raw_title_clean in all_urls or raw_title_clean == video_url:
                video_meta = fetch_video_metadata(video_url)
                if video_meta.get("title"):
                    title = video_meta["title"]
                    # If domain / sub-topics weren't specified, adopt the ones inferred from video title
                    if not domains or domains == ["general"]:
                        domains = video_meta.get("domains", [])
                    if not sub_topics:
                        sub_topics = video_meta.get("sub_topics", [])
                    if primary_domain == "general":
                        primary_domain = video_meta.get("primary_domain", "general")

        text_to_analyze = (title or "") + " " + (content_text or "")
        analysis = llm_service.analyze_content(text_to_analyze, source_url=video_url or (all_urls[0] if all_urls else None))

        # 4. Resolve source_type and dual media
        has_video = bool(video_url or analysis.get("is_video"))
        has_image = any(
            (isinstance(u, str) and (u.startswith("/data/uploads/") or any(u.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp", ".gif"])))
            for u in all_urls
        ) or bool(original_media_url)

        final_source_type = source_type
        if has_video and has_image:
            final_source_type = "video"
        elif has_video:
            final_source_type = "video"
        elif has_image and source_type in ["note", "article"]:
            final_source_type = "infographic"

        # 5. Format final source_url
        if len(all_urls) > 1:
            final_source_url = json.dumps(all_urls, ensure_ascii=False)
        elif len(all_urls) == 1:
            final_source_url = all_urls[0]
        else:
            final_source_url = None

        record_title = title or (video_url if video_url else (text_to_analyze[:40] if text_to_analyze.strip() else "רשומה חדשה"))

        final_domains = domains if domains else analysis["domains"]
        final_sub_topics = sub_topics if sub_topics is not None else analysis.get("sub_topics", [])
        final_custom_tags = custom_tags if custom_tags is not None else []
        final_primary = primary_domain if primary_domain != "general" else (final_domains[0] if final_domains else analysis["primary_domain"])

        if final_primary not in final_domains:
            final_domains.insert(0, final_primary)

        # Primary media url for quick preview
        first_img = next((u for u in all_urls if isinstance(u, str) and (u.startswith("/data/uploads/") or any(u.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp", ".gif"]))), None)
        final_media_url = original_media_url or first_img or (video_meta.get("thumbnail_url") if video_meta else None)

        record = ContentRecord(
            workspace_id=workspace_id,
            owner_id=owner_id,
            title=record_title,
            source_url=final_source_url,
            original_media_url=final_media_url,
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
