from typing import List
from sqlmodel import Session
from app.config import settings
from app.db.database import engine
from app.db.models import ContentRecord
from app.services.tts_service import tts_service

class OutputBuilderEngine:
    def assemble_output(
        self,
        record_ids: List[str],
        output_type: str = "post",  # post, guide, protocol, lecture, infographic_summary
        target_title: str = "תוצר חדש"
    ) -> dict:
        with Session(engine) as session:
            records = [session.get(ContentRecord, rid) for rid in record_ids if session.get(ContentRecord, rid)]

        if not records:
            raise ValueError("No valid records selected for output generation")

        body_parts = []
        for i, rec in enumerate(records, 1):
            body_parts.append(f"### {i}. {rec.title} ({rec.primary_domain})\n")
            if rec.summary:
                body_parts.append(f"**תקציר:** {rec.summary}\n")
            if rec.transcript:
                body_parts.append(f"**פירוט:** {rec.transcript[:300]}...\n")
            if rec.risk_level != "none":
                body_parts.append(f"⚠️ **רמת סיכון/אזהרה:** {rec.risk_level}\n")
            body_parts.append("\n---\n")

        output_md = f"""# {target_title}
**סוג תוצר:** {output_type}
**כמות מקורות בשימוש:** {len(records)}

{"".join(body_parts)}
"""

        # Save generated output into vault/03 Outputs/
        outputs_dir = settings.VAULT_DIR / "03 Outputs"
        outputs_dir.mkdir(parents=True, exist_ok=True)
        out_path = outputs_dir / f"{target_title.replace(' ', '_')}.md"
        out_path.write_text(output_md, encoding="utf-8")

        # Synthesize voice summary of output
        tts_res = tts_service.synthesize_speech(f"הורכב תוצר חדש מסוג {output_type} בשם {target_title} מ-{len(records)} מקורות.")

        return {
            "title": target_title,
            "output_type": output_type,
            "sources_count": len(records),
            "output_path": str(out_path),
            "content": output_md,
            "voice_script": tts_res["voice_script"]
        }

output_builder_engine = OutputBuilderEngine()
