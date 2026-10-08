from typing import Optional, List
from pydantic import BaseModel

class VoiceCaptureRequest(BaseModel):
    audio_path_or_url: Optional[str] = None
    voice_note_text: Optional[str] = None  # Direct voice text transcription input
    workspace_id: str = "default_ws"
    owner_id: str = "default_owner"

class VoiceIntentResponse(BaseModel):
    intent: str  # CAPTURE_AND_TAG, RETRIEVE, GENERATE_OUTPUT, ASK_QUESTION
    transcription: str
    suggested_domain: str
    suggested_keywords: List[str]
    suggested_title: str
    response_voice_script: str
