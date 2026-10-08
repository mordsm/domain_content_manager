import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field
from app.config import settings

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def now_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

class ContentRecord(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    workspace_id: str = Field(default_factory=lambda: settings.DEFAULT_WORKSPACE)
    owner_id: str = Field(default_factory=lambda: settings.DEFAULT_OWNER)

    # Layer A: Universal Metadata
    title: str
    source_url: Optional[str] = None
    source_type: str = "note"  # video, podcast, article, image, voice, note, infographic
    capture_date: str = Field(default_factory=now_str)
    status: str = "inbox"  # inbox, tagged, in_use, archived
    original_media_url: Optional[str] = None
    transcript: Optional[str] = None
    summary: Optional[str] = None
    keywords_json: str = "[]"  # JSON list string
    why_saved: Optional[str] = None
    personal_rating: Optional[int] = None
    ready_for_output: bool = False
    risk_level: str = "none"  # none, low, medium, high

    primary_domain: str = "general"  # health, hair, diet, garden, foraging, culinary, general
    domains_json: str = "[]"  # JSON list string for multi/cross domains
    sub_topics_json: str = "[]"  # JSON list string for sub-topics/sub-domains
    custom_tags_json: str = "[]"  # JSON list string for user-defined custom tags
    seasonality: Optional[str] = None  # spring, summer, autumn, winter, year_round
    reliability_layer: str = "personal"  # research, traditional, personal, doubt
    is_cross_domain: bool = False
    domain_data_json: str = "{}"  # JSON dict string for domain specific fields

    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)

class ContentRelation(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    source_id: str = Field(foreign_key="contentrecord.id")
    target_id: str = Field(foreign_key="contentrecord.id")
    relation_type: str = "related"  # summary_of, derived_from, infographic_of, related
    created_at: str = Field(default_factory=now_iso)
