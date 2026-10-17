import json
import re
from pathlib import Path
from typing import List
from sqlmodel import Session, select
from app.config import settings
from app.db.database import engine
from app.db.models import ContentRecord, ContentRelation

class ObsidianSyncEngine:
    def sanitize_filename(self, name: str) -> str:
        clean = re.sub(r'[\\/*?:"<>|]', "", name)
        return clean.strip().replace(" ", "_")

    def export_record_to_markdown(self, record: ContentRecord) -> Path:
        vault_dir = settings.VAULT_DIR

        # Subdirectory routing
        if record.status == "inbox":
            target_subfolder = vault_dir / "00 Inbox"
        elif record.primary_domain:
            target_subfolder = vault_dir / "02 By Domain" / record.primary_domain.capitalize()
        else:
            target_subfolder = vault_dir / "01 Tagged"

        target_subfolder.mkdir(parents=True, exist_ok=True)

        filename = f"{self.sanitize_filename(record.title)}_{record.id[:8]}.md"
        filepath = target_subfolder / filename

        # Fetch relations
        related_links: List[str] = []
        with Session(engine) as session:
            relations = session.exec(select(ContentRelation).where(ContentRelation.source_id == record.id)).all()
            for rel in relations:
                target_rec = session.get(ContentRecord, rel.target_id)
                if target_rec:
                    target_filename = self.sanitize_filename(target_rec.title)
                    related_links.append(f"- [[{target_filename}]] ({rel.relation_type})")

        keywords = json.loads(record.keywords_json) if record.keywords_json else []
        domains = json.loads(record.domains_json) if record.domains_json else []
        sub_topics = json.loads(record.sub_topics_json) if getattr(record, "sub_topics_json", None) else []
        custom_tags = json.loads(record.custom_tags_json) if getattr(record, "custom_tags_json", None) else []

        # Media / Infographics embedding
        media_embeds: List[str] = []
        if record.source_url:
            try:
                urls = json.loads(record.source_url)
                if not isinstance(urls, list):
                    urls = [record.source_url]
            except Exception:
                urls = [record.source_url]

            for u in urls:
                if u and (record.source_type == "infographic" or u.startswith("/data/uploads/") or any(u.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp", ".gif"])):
                    media_embeds.append(f"![{record.title}]({u})")

        media_section = "\n".join(media_embeds) if media_embeds else ""

        yaml_frontmatter = f"""---
id: "{record.id}"
title: "{record.title}"
workspace_id: "{record.workspace_id}"
owner_id: "{record.owner_id}"
primary_domain: "{record.primary_domain}"
domains: {json.dumps(domains, ensure_ascii=False)}
sub_topics: {json.dumps(sub_topics, ensure_ascii=False)}
custom_tags: {json.dumps(custom_tags, ensure_ascii=False)}
source_type: "{record.source_type}"
source_url: "{record.source_url or ''}"
status: "{record.status}"
reliability_layer: "{record.reliability_layer}"
risk_level: "{record.risk_level}"
seasonality: "{record.seasonality or ''}"
created_at: "{record.created_at}"
---

# {record.title}

## 📌 תקציר (Summary)
{record.summary or 'אין תקציר עדיין.'}

## 🖼️ אינפוגרפיקות ותמונות (Infographics)
{media_section if media_section else 'אין קבצי תמונה מצורפים'}

## 🏷️ מילות מפתח שנשאבו (Mined Keywords)
{', '.join([f'#{k}' for k in keywords]) if keywords else 'אין מילות מפתח'}

## 🔖 תגים אישיים (Custom Tags)
{', '.join([f'#{t}' for t in custom_tags]) if custom_tags else 'אין תגים אישיים'}

## 📌 תתי-נושאים (Sub-Topics)
{', '.join(sub_topics) if sub_topics else 'אין תתי-נושאים'}

## 🔗 קשרים (Bidirectional Links)
{chr(10).join(related_links) if related_links else 'אין קשרים מוגדרים.'}

## 📝 תוכן מלא (Transcript / Notes)
{record.transcript or 'אין תוכן טקסטואלי.'}
"""

        filepath.write_text(yaml_frontmatter, encoding="utf-8")
        return filepath

    def delete_record_markdown(self, record: ContentRecord) -> bool:
        vault_dir = settings.VAULT_DIR
        pattern = f"*_{record.id[:8]}.md"
        deleted = False
        for file in vault_dir.rglob(pattern):
            try:
                file.unlink(missing_ok=True)
                deleted = True
            except Exception:
                pass
        return deleted

    def sync_all(self) -> int:
        with Session(engine) as session:
            records = session.exec(select(ContentRecord)).all()
            count = 0
            for rec in records:
                self.export_record_to_markdown(rec)
                count += 1
            return count

obsidian_sync_engine = ObsidianSyncEngine()
