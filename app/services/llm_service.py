import json
import re
from typing import Dict, Any, List
from app.services.config_service import domain_config_manager

HEBREW_STOPWORDS = {
    "את", "של", "על", "עם", "כי", "מה", "גם", "זה", "אשר", "היה", "הם", "היא", "הוא",
    "לפי", "תוך", "כדי", "ללא", "אשר", "אחר", "שלא", "אלא", "שבו", "כמה", "כל", "שכל",
    "כך", "אשר", "איך", "יומי", "למ משך", "מאוד", "כמו", "דרך", "בגלל", "אפילו", "רק",
    "the", "and", "that", "this", "with", "from", "for", "have", "been", "was", "were"
}

VIDEO_URL_PATTERN = re.compile(
    r'https?://(?:www\.)?(?:youtube\.com/watch\?v=[\w-]+|youtu\.be/[\w-]+|vimeo\.com/\d+|tiktok\.com/@[^/]+/video/\d+|instagram\.com/reel/[\w-]+|[\w\.-]+/(?:[^\s]+\.(?:mp4|mov|webm|avi|mkv)))[^\s]*',
    re.IGNORECASE
)

class LLMService:
    def extract_keywords_from_text(self, text: str, max_keywords: int = 8) -> List[str]:
        """
        Mines keywords and key phrases (bigrams) automatically from audio/video transcripts, articles, or notes.
        """
        if not text:
            return []

        # Clean punctuation and split into tokens
        words = [w.strip() for w in re.findall(r'[\u0590-\u05FFa-zA-Z0-9_-]+', text)]
        
        # Filter single words
        meaningful_words = []
        for w in words:
            w_clean = w
            # Strip common Hebrew prefix if long enough
            if len(w_clean) > 4 and w_clean[0] in ['ב', 'ל', 'מ', 'כ', 'ו', 'ה']:
                w_clean = w_clean[1:]
            
            if len(w_clean) >= 3 and w_clean.lower() not in HEBREW_STOPWORDS and not w_clean.isdigit():
                meaningful_words.append(w_clean)

        # Extract 2-word keyphrases (bigrams)
        bigrams = []
        for i in range(len(words) - 1):
            w1 = words[i].lower()
            w2 = words[i+1].lower()
            if (len(w1) >= 3 and len(w2) >= 3 and
                w1 not in HEBREW_STOPWORDS and w2 not in HEBREW_STOPWORDS and
                not w1.isdigit() and not w2.isdigit()):
                bigrams.append(f"{words[i]}_{words[i+1]}")

        # Frequency count
        freq: Dict[str, int] = {}
        for bg in bigrams:
            freq[bg] = freq.get(bg, 0) + 2  # Boost keyphrases
        for w in meaningful_words:
            freq[w] = freq.get(w, 0) + 1

        # Sort by frequency and return top keywords
        sorted_terms = sorted(freq.keys(), key=lambda t: freq[t], reverse=True)
        return sorted_terms[:max_keywords]

    def analyze_content(self, text: str, source_url: str = None) -> Dict[str, Any]:
        """
        Extracts domain, sub_topics, mined keywords, summary, video URLs, and risk level from text using domains.yaml configuration.
        """
        text_lower = text.lower()
        
        # Auto-detect video URL if not provided
        detected_video_url = source_url
        if not detected_video_url:
            match = VIDEO_URL_PATTERN.search(text)
            if match:
                detected_video_url = match.group(0)

        is_video = bool(detected_video_url or any(w in text_lower for w in ["youtube.com", "youtu.be", "vimeo.com", "סרטון", "וידאו", "יוטיוב"]))
        
        # Dynamic domain and sub-topic detection from YAML config
        config_analysis = domain_config_manager.analyze_text_with_config(text)
        primary_domain = config_analysis["primary_domain"]
        detected_domains = config_analysis["domains"]
        detected_sub_topics = config_analysis["sub_topics"]

        # Risk assessment
        risk_level = "none"
        if any(d in ["foraging", "health"] for d in detected_domains) and any(w in text_lower for w in ["רעיל", "סכנה", "מינון", "תופעות לוואי"]):
            risk_level = "high"
        elif any(d in ["health", "diet", "financial"] for d in detected_domains):
            risk_level = "medium"

        # Mined keywords extraction
        keywords = self.extract_keywords_from_text(text, max_keywords=8)

        # Summary generation
        summary = text[:150] + ("..." if len(text) > 150 else "")

        return {
            "primary_domain": primary_domain,
            "domains": detected_domains,
            "sub_topics": detected_sub_topics,
            "keywords": keywords,
            "summary": summary,
            "risk_level": risk_level,
            "reliability_layer": "personal" if "ניסיון" in text_lower else "research",
            "detected_video_url": detected_video_url,
            "is_video": is_video
        }

    def parse_voice_intent(self, transcript: str) -> Dict[str, Any]:
        """
        Parses user voice intent from transcript.
        """
        analysis = self.analyze_content(transcript)
        title = transcript.split('.')[0][:40] if transcript else "הקלטה קולית חדשה"
        
        return {
            "intent": "CAPTURE_AND_TAG",
            "transcription": transcript,
            "suggested_domain": analysis["primary_domain"],
            "suggested_keywords": analysis["keywords"],
            "suggested_title": f"קליטה קולית: {title}",
            "response_voice_script": f"נקלט בהצלחה ותויג תחת {analysis['primary_domain']}. הרשומה מוכנה ב-Obsidian."
        }

llm_service = LLMService()
