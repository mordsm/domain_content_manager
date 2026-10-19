import re
import urllib.parse
from typing import Dict, Any, Optional
import httpx

from app.services.config_service import domain_config_manager
from app.services.llm_service import llm_service

VIDEO_REGEX = re.compile(
    r'https?://(?:www\.)?(?:youtube\.com/(?:[^\s/]+/|(?:v|e(?:mbed)?|shorts)/|.*[?&]v=)|youtu\.be/|vimeo\.com/|tiktok\.com/@[^/]+/video/|instagram\.com/reel/|[\w\.-]+/(?:[^\s]+\.(?:mp4|mov|webm|avi|mkv)))[^\s]*',
    re.IGNORECASE
)

def extract_video_url_from_text(text: str) -> Optional[str]:
    if not text:
        return None
    match = VIDEO_REGEX.search(text)
    return match.group(0) if match else None

def clean_video_title(raw_title: str) -> str:
    if not raw_title:
        return ""
    title = raw_title.strip()
    # Strip common site suffixes like " - YouTube", "| YouTube", " - Vimeo", etc.
    title = re.sub(r'\s*[-|–—]\s*(?:YouTube|Vimeo|TikTok|Instagram).*$', '', title, flags=re.IGNORECASE).strip()
    # Replace excessive whitespace
    title = re.sub(r'\s+', ' ', title)
    return title

def fetch_video_metadata(url: str) -> Dict[str, Any]:
    """
    Fetches real video title, author, and thumbnail via oEmbed or OpenGraph/HTML.
    Then performs automatic domain and sub-topic classification using domains.yaml.
    """
    clean_url = url.strip() if url else ""
    if not clean_url:
        return {}

    fetched_title = ""
    author = ""
    thumbnail_url = ""
    provider = "unknown"

    # 1. YouTube oEmbed (Free, public, ultra-fast, no API key required)
    if any(d in clean_url.lower() for d in ["youtube.com", "youtu.be"]):
        provider = "youtube"
        try:
            oembed_url = f"https://www.youtube.com/oembed?url={urllib.parse.quote(clean_url)}&format=json"
            resp = httpx.get(oembed_url, timeout=6.0, follow_redirects=True)
            if resp.status_code == 200:
                data = resp.json()
                fetched_title = data.get("title", "").strip()
                author = data.get("author_name", "").strip()
                thumbnail_url = data.get("thumbnail_url", "")
        except Exception:
            pass

    # 2. Vimeo oEmbed
    elif "vimeo.com" in clean_url.lower():
        provider = "vimeo"
        try:
            oembed_url = f"https://vimeo.com/api/oembed.json?url={urllib.parse.quote(clean_url)}"
            resp = httpx.get(oembed_url, timeout=6.0, follow_redirects=True)
            if resp.status_code == 200:
                data = resp.json()
                fetched_title = data.get("title", "").strip()
                author = data.get("author_name", "").strip()
                thumbnail_url = data.get("thumbnail_url", "")
        except Exception:
            pass

    # 3. Fallback: Generic OpenGraph / HTML Title
    if not fetched_title:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            resp = httpx.get(clean_url, headers=headers, timeout=6.0, follow_redirects=True)
            if resp.status_code == 200:
                text = resp.text
                og_match = re.search(r'<meta\s+property=["\']og:title["\']\s+content=["\'](.*?)["\']', text, re.IGNORECASE)
                if not og_match:
                    og_match = re.search(r'<meta\s+content=["\'](.*?)["\']\s+property=["\']og:title["\']', text, re.IGNORECASE)
                if og_match:
                    fetched_title = og_match.group(1).strip()
                else:
                    title_match = re.search(r'<title>(.*?)</title>', text, re.IGNORECASE | re.DOTALL)
                    if title_match:
                        fetched_title = title_match.group(1).strip()
        except Exception:
            pass

    # If title still empty and it's a direct video file, extract clean filename
    if not fetched_title and any(clean_url.lower().endswith(ext) for ext in [".mp4", ".mov", ".webm", ".avi", ".mkv"]):
        path_stem = clean_url.split("/")[-1].split("?")[0]
        fetched_title = re.sub(r'\.(mp4|mov|webm|avi|mkv)$', '', path_stem, flags=re.IGNORECASE).replace("_", " ").replace("-", " ").title()

    final_title = clean_video_title(fetched_title)

    # Auto-classify domain and sub-topic based on the detected video title
    analysis = domain_config_manager.analyze_text_with_config(final_title or clean_url)
    keywords = llm_service.extract_keywords_from_text(final_title, max_keywords=8) if final_title else []

    # Get human-readable Hebrew domain label
    config = domain_config_manager.load_config()
    domain_info = config.get(analysis["primary_domain"], {})
    domain_he = domain_info.get("label_he", analysis["primary_domain"])

    sub_topics_he = []
    available_sub_topics = domain_info.get("sub_topics", {})
    for st in analysis.get("sub_topics", []):
        st_label = available_sub_topics.get(st, {}).get("label_he", st)
        sub_topics_he.append(st_label)

    return {
        "title": final_title,
        "author": author,
        "thumbnail_url": thumbnail_url,
        "provider": provider,
        "source_url": clean_url,
        "primary_domain": analysis["primary_domain"],
        "primary_domain_he": domain_he,
        "domains": analysis["domains"],
        "sub_topics": analysis.get("sub_topics", []),
        "sub_topics_he": sub_topics_he,
        "keywords": keywords,
        "is_video": True
    }
