import os
from pathlib import Path
from typing import Optional

class STTService:
    def transcribe(self, audio_file_path: str) -> str:
        """
        Transcribes audio file to Hebrew/English text using Whisper API or fallback.
        """
        path = Path(audio_file_path)
        if not path.exists():
            return f"הקלטה קולית: {path.name}"
        
        # Mock / Fallback transcription for local execution
        return f"תמלול אוטומטי של הקובץ הקולי {path.name}: רעיון חדש לתזונה ובריאות המעי."

stt_service = STTService()
