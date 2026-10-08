import json
from typing import List, Dict, Any
from sqlmodel import Session, select
from app.db.database import engine
from app.db.models import ContentRecord, ContentRelation

class EnrichmentEngine:
    def enrich_record(
        self,
        record_id: str,
        primary_domain: str,
        domains: List[str] = None,
        sub_topics: List[str] = None,
        custom_tags: List[str] = None,
        keywords: List[str] = None,
        summary: str = None,
        why_saved: str = None,
        personal_rating: int = None,
        reliability_layer: str = "personal",
        risk_level: str = "none",
        seasonality: str = None,
        domain_specific_data: Dict[str, Any] = None,
        related_record_ids: List[str] = None,
        relation_type: str = "related"
    ) -> ContentRecord:
        with Session(engine) as session:
            record = session.get(ContentRecord, record_id)
            if not record:
                raise ValueError(f"ContentRecord {record_id} not found")

            record.primary_domain = primary_domain
            if domains:
                record.domains_json = json.dumps(domains, ensure_ascii=False)
                record.is_cross_domain = len(domains) > 1
            if sub_topics is not None:
                record.sub_topics_json = json.dumps(sub_topics, ensure_ascii=False)
            if custom_tags is not None:
                record.custom_tags_json = json.dumps(custom_tags, ensure_ascii=False)
            if keywords:
                record.keywords_json = json.dumps(keywords, ensure_ascii=False)
            if summary:
                record.summary = summary
            if why_saved:
                record.why_saved = why_saved
            if personal_rating is not None:
                record.personal_rating = personal_rating
            record.reliability_layer = reliability_layer
            record.risk_level = risk_level
            record.seasonality = seasonality
            if domain_specific_data:
                record.domain_data_json = json.dumps(domain_specific_data, ensure_ascii=False)

            record.status = "tagged"
            session.add(record)
            session.commit()

            # Create bidirectional relation links if provided
            if related_record_ids:
                for target_id in related_record_ids:
                    rel1 = ContentRelation(
                        source_id=record_id,
                        target_id=target_id,
                        relation_type=relation_type
                    )
                    # Inverse bidirectional relation type
                    inv_type = "summary_of" if relation_type == "derived_from" else relation_type
                    rel2 = ContentRelation(
                        source_id=target_id,
                        target_id=record_id,
                        relation_type=inv_type
                    )
                    session.add(rel1)
                    session.add(rel2)
                session.commit()

            session.refresh(record)

        return record

enrichment_engine = EnrichmentEngine()
