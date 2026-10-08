import random
from typing import List, Optional
from sqlmodel import Session, select
from app.db.database import engine
from app.db.models import ContentRecord
from app.services.tts_service import tts_service

class RetrievalEngine:
    def search(
        self,
        query: Optional[str] = None,
        domain: Optional[str] = None,
        sub_topic: Optional[str] = None,
        risk_level: Optional[str] = None,
        seasonality: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[ContentRecord]:
        with Session(engine) as session:
            stmt = select(ContentRecord)
            if domain:
                stmt = stmt.where(
                    (ContentRecord.primary_domain == domain) |
                    (ContentRecord.domains_json.like(f'%"{domain}"%'))
                )
            if sub_topic:
                stmt = stmt.where(ContentRecord.sub_topics_json.like(f'%"{sub_topic}"%'))
            if risk_level:
                stmt = stmt.where(ContentRecord.risk_level == risk_level)
            if seasonality:
                stmt = stmt.where(ContentRecord.seasonality == seasonality)
            if status:
                stmt = stmt.where(ContentRecord.status == status)

            results = session.exec(stmt).all()

            if query:
                q_lower = query.lower()
                results = [
                    r for r in results
                    if q_lower in r.title.lower()
                    or (r.summary and q_lower in r.summary.lower())
                    or (r.transcript and q_lower in r.transcript.lower())
                    or q_lower in r.keywords_json.lower()
                    or q_lower in r.custom_tags_json.lower()
                    or q_lower in r.sub_topics_json.lower()
                ]

            return results

    def surprise_me(self, domain: Optional[str] = None) -> Optional[ContentRecord]:
        results = self.search(domain=domain)
        if not results:
            return None
        return random.choice(results)

    def speak_results_summary(self, results: List[ContentRecord]) -> dict:
        if not results:
            return tts_service.synthesize_speech("לא נמצאו תוצאות מתאימות במאגר.")
        
        count = len(results)
        titles = ", ".join([r.title for r in results[:3]])
        speech_text = f"נמצאו {count} רשומות במאגר. 3 הראשונות הן: {titles}."
        return tts_service.synthesize_speech(speech_text)

retrieval_engine = RetrievalEngine()
