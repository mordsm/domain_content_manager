import sys
import os
import re
import time
import json
import uuid
import logging
from datetime import datetime
from pathlib import Path
import httpx

from app.config import settings
from app.domain.capture import capture_engine
from app.domain.obsidian_sync import obsidian_sync_engine

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("telegram_bot")

TELEGRAM_API_BASE = "https://api.telegram.org/bot"

# LLM Wiki Path Resolution
WORKSPACE_DIR = Path("C:/workspace")
LLM_WIKI_DIR = WORKSPACE_DIR / "llm_wiki"
LLM_WIKI_API_BASE = "http://localhost:8050/api/v1"


def sanitize_filename(name: str) -> str:
    clean = re.sub(r'[\\/*?:"<>|]', "", name)
    return clean.strip().replace(" ", "-").lower()


def send_telegram_message(bot_token: str, chat_id: int | str, text: str, reply_to_message_id: int = None):
    """
    Sends message to Telegram chat. Automatically falls back to plain text
    if Markdown parsing errors occur, and chunks messages over 4000 characters.
    """
    chunks = []
    while len(text) > 3900:
        split_idx = text.rfind("\n", 0, 3900)
        if split_idx == -1:
            split_idx = 3900
        chunks.append(text[:split_idx])
        text = text[split_idx:].strip()
    if text:
        chunks.append(text)

    for chunk in chunks:
        payload = {
            "chat_id": chat_id,
            "text": chunk,
            "parse_mode": "Markdown"
        }
        if reply_to_message_id:
            payload["reply_to_message_id"] = reply_to_message_id

        try:
            resp = httpx.post(f"{TELEGRAM_API_BASE}{bot_token}/sendMessage", json=payload, timeout=15)
            if resp.status_code != 200:
                # Fallback to plain text without Markdown
                payload.pop("parse_mode", None)
                httpx.post(f"{TELEGRAM_API_BASE}{bot_token}/sendMessage", json=payload, timeout=15)
        except Exception as e:
            logger.error(f"Error sending telegram message: {e}")


def append_to_llm_wiki_daily_log(entry: str, category: str = "notes"):
    """
    Appends an event, note, or decision into the canonical LLM Wiki daily log
    under wiki/daily/YYYY-MM-DD.md.
    """
    if not LLM_WIKI_DIR.exists():
        return

    daily_dir = LLM_WIKI_DIR / "wiki" / "daily"
    daily_dir.mkdir(parents=True, exist_ok=True)
    today_str = datetime.now().strftime("%Y-%m-%d")
    now_time = datetime.now().strftime("%H:%M")
    daily_file = daily_dir / f"{today_str}.md"

    if not daily_file.exists():
        initial_content = f"""# Daily Memory Log: {today_str}

**Status**: Active • Auto-tracked via Telegram & LLM Wiki

## Quick Notes & Events
- [{now_time}] יומן נפתח אוטומטית.

## Key Decisions Recorded

## Research Questions & Topics
"""
        daily_file.write_text(initial_content, encoding="utf-8")

    content = daily_file.read_text(encoding="utf-8")

    if category == "decisions":
        marker = "## Key Decisions Recorded"
        new_line = f"- ⚖️ **[{now_time}]** {entry}\n"
    elif category == "research":
        marker = "## Research Questions & Topics"
        new_line = f"- 🔬 **[{now_time}]** {entry}\n"
    else:
        marker = "## Quick Notes & Events"
        new_line = f"- 📝 **[{now_time}]** {entry}\n"

    if marker in content:
        parts = content.split(marker, 1)
        updated = parts[0] + marker + "\n" + new_line + parts[1].lstrip("\n")
    else:
        updated = content + f"\n\n{marker}\n{new_line}"

    daily_file.write_text(updated, encoding="utf-8")
    logger.info(f"Appended entry to LLM Wiki daily log {daily_file.name} [{category}]")


def create_llm_wiki_decision(title: str, decision: str, reason: str, alternatives: str, tradeoffs: str) -> dict:
    """
    Creates a canonical first-class decision in 40_Decisions/ and syncs with daily log.
    """
    today_str = datetime.now().strftime("%Y-%m-%d")
    slug = sanitize_filename(title)[:40] or "new-decision"
    file_id = f"{today_str}-{slug}"

    if LLM_WIKI_DIR.exists():
        dec_dir = LLM_WIKI_DIR / "40_Decisions"
        dec_dir.mkdir(parents=True, exist_ok=True)
        target = dec_dir / f"{file_id}.md"

        content = f"""---
confidence: high
created: '{today_str}'
domain:
- llm_wiki
id: {file_id}
resolved_by: Telegram / Moshe
status: active
title: {title}
type: decision
---

# Decision: {title}

**Project / Domain**: llm_wiki

## Decision
{decision}

## Rationale & Reason
{reason}

## Alternatives Considered
{alternatives or "None recorded"}

## Tradeoffs
{tradeoffs or "None recorded"}

## Resolved By
Telegram / Moshe
"""
        target.write_text(content, encoding="utf-8")

        # Append to daily log
        append_to_llm_wiki_daily_log(f"[[{file_id}|{title}]]: {decision}", category="decisions")

        # Try triggering MOC rebuild on running server
        try:
            httpx.post(f"{LLM_WIKI_API_BASE}/wiki/mocs/rebuild", timeout=5)
        except Exception:
            pass

        return {"file_id": file_id, "path": str(target), "status": "success"}

    return {"file_id": file_id, "status": "fallback"}


def create_llm_wiki_research(topic: str, context: str = "") -> dict:
    """
    Creates an open research question entry under 20_Research/ and records it in daily log.
    """
    today_str = datetime.now().strftime("%Y-%m-%d")
    slug = sanitize_filename(topic)[:40] or "new-research"
    folder_id = f"{today_str}-{slug}"

    if LLM_WIKI_DIR.exists():
        res_dir = LLM_WIKI_DIR / "20_Research" / folder_id
        res_dir.mkdir(parents=True, exist_ok=True)
        target = res_dir / "overview.md"

        content = f"""---
created: '{today_str}'
id: research-{slug}
status: proposed
tags:
- research
- telegram_intake
title: {topic}
type: research_question
---

# שאלת מחקר: {topic}

## שאלת המחקר וההקשר
{context or topic}

## ערוץ קליטה
תועד דרך Content Manager Telegram Bot בתאריך {today_str} בשעה {datetime.now().strftime("%H:%M")}

## שלב במחזור החיים
ממתין לסריקת ספרות וביקורת מדעית (Investigate This Topic).
"""
        target.write_text(content, encoding="utf-8")
        append_to_llm_wiki_daily_log(f"שאלת מחקר חדשה: [[{folder_id}|{topic}]]", category="research")
        return {"folder_id": folder_id, "status": "success"}

    return {"folder_id": folder_id, "status": "fallback"}


def query_llm_wiki_rag(question: str) -> dict:
    """
    Queries LLM Wiki's live Hybrid RAG server via HTTP API.
    """
    try:
        resp = httpx.post(
            f"{LLM_WIKI_API_BASE}/query",
            data={"query": question, "domain": "all", "mode": "hybrid"},
            timeout=45
        )
        if resp.status_code == 200:
            return resp.json()
        else:
            return {"error": f"HTTP {resp.status_code}: {resp.text}"}
    except Exception as e:
        return {"error": f"LLM Wiki Server unreachable (http://localhost:8050): {e}"}


def get_help_message() -> str:
    return """🤖 *Content Manager & LLM Wiki Telegram Bot*
אני מחבר את טלגרם ישירות למערכת המודיעין והכספת שלך!

📋 *פקודות ייעודיות לניתוב המידע:*

⚖️ */decision* או */החלטה*
תיעוד החלטה רשמית מחייבת ב-`40_Decisions/`:
פורמט עם קווים מפרידים:
`/decision כותרת | ההחלטה שהתקבלה | נימוק ורציונל | חלופות ופשרות`
או מקוצר:
`/decision שימוש ב-Obsidian לשמירת זיכרון`

📝 */note* או */פתק* או */אירוע*
הוספת אירוע/מחשבה ישירות ליומן היומי (`daily log`) ולכספת:
`/note שיחה מצוינת על שיפור הדיאלוג הקולי`

🔬 */research* או */מחקר* או */investigate*
רישום שאלת מחקר חדשה ב-`20_Research/`:
`/research מה ההשפעה של צום לסירוגין על שלמות רירית המעי?`

💬 */ask* או */שאלה* או */q*
שאל שאלה את ה-LLM Wiki וקבל תשובה סמנטית מבוססת Hybrid RAG ישירות בטלגרם:
`/ask מה ההחלטות שלנו בנוגע לארכיטקטורת זיכרון?`

🍳 */cook* או */מתכון*
שמירת מתכון ישירות ל-Cook Pilot תחת `02 By Domain/Culinary/`:
`/cook מרק ארטישוק ירושלמי עם שמן כמהין ופטריות`

🌿 */health* או */בריאות*
שמירת מידע בריאותי/פרוטוקול/תוסף תחת `02 By Domain/Health/`:
`/health מגנזיום גליצינאט 400 מ"ג לפני שינה לשיפור שנת REM`

👤 */personal* או */אישי*
שמירה לתחום האישי ב-Wiki (`wiki/personal/`)

💼 */business* או */עסקי*
שמירה לתחום העסקי ב-Wiki (`wiki/business/`)

📸 *שליחת תמונה / מסמך / קישור (ללא פקודה):*
יישמר אוטומטית כאינפוגרפיקה, וידאו או מאמר ב-Inbox עם ניתוח תוכן מלא!
"""


def process_telegram_update(bot_token: str, update: dict):
    message = update.get("message") or update.get("channel_post")
    if not message:
        return

    chat_id = message["chat"]["id"]
    message_id = message.get("message_id")
    raw_text = (message.get("text") or message.get("caption") or "").strip()
    photos = message.get("photo")
    documents = message.get("document")

    uploads_dir = settings.DATA_DIR / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    saved_urls = []
    source_type = "note"

    # --- 1. HANDLE PHOTO UPLOADS ---
    if photos:
        source_type = "infographic"
        best_photo = photos[-1]
        file_id = best_photo["file_id"]
        try:
            file_resp = httpx.get(f"{TELEGRAM_API_BASE}{bot_token}/getFile?file_id={file_id}", timeout=15).json()
            if file_resp.get("ok"):
                file_path = file_resp["result"]["file_path"]
                download_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
                ext = Path(file_path).suffix or ".jpg"
                local_filename = f"tg_{uuid.uuid4().hex[:10]}{ext}"
                dest_path = uploads_dir / local_filename

                img_data = httpx.get(download_url, timeout=30).content
                with open(dest_path, "wb") as f:
                    f.write(img_data)
                saved_urls.append(f"/data/uploads/{local_filename}")
        except Exception as e:
            logger.error(f"Failed to download telegram photo: {e}")

    # --- 2. HANDLE DOCUMENT UPLOADS ---
    elif documents:
        mime = documents.get("mime_type", "")
        if mime.startswith("image/"):
            source_type = "infographic"
            file_id = documents["file_id"]
            try:
                file_resp = httpx.get(f"{TELEGRAM_API_BASE}{bot_token}/getFile?file_id={file_id}", timeout=15).json()
                if file_resp.get("ok"):
                    file_path = file_resp["result"]["file_path"]
                    download_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
                    ext = Path(file_path).suffix or ".png"
                    local_filename = f"tg_{uuid.uuid4().hex[:10]}{ext}"
                    dest_path = uploads_dir / local_filename

                    img_data = httpx.get(download_url, timeout=30).content
                    with open(dest_path, "wb") as f:
                        f.write(img_data)
                    saved_urls.append(f"/data/uploads/{local_filename}")
            except Exception as e:
                logger.error(f"Failed to download telegram document: {e}")

    # --- 3. HANDLE COMMANDS (/decision, /note, /research, /ask, etc.) ---
    if raw_text.startswith("/"):
        parts = raw_text.split(maxsplit=1)
        command = parts[0].lower().split("@")[0]  # strip @bot_username if present
        args = parts[1].strip() if len(parts) > 1 else ""

        # A. HELP & START
        if command in ["/start", "/help", "/עזרה", "/פקודות"]:
            send_telegram_message(bot_token, chat_id, get_help_message(), reply_to_message_id=message_id)
            return

        # B. DECISIONS (/decision, /החלטה, /decide)
        elif command in ["/decision", "/החלטה", "/decide"]:
            if not args:
                send_telegram_message(
                    bot_token, chat_id,
                    "⚠️ אנא הזן את פרטי ההחלטה.\n*דוגמה:*\n`/decision בחירת מודל זיכרון | שימוש ב-Obsidian | פשטות ושקיפות | חוסר ב-SQL`",
                    reply_to_message_id=message_id
                )
                return

            pipe_parts = [p.strip() for p in args.split("|")]
            if len(pipe_parts) == 1:
                title = pipe_parts[0]
                decision_stmt = pipe_parts[0]
                reason = "תועד באופן מהיר דרך Telegram Bot"
                alts = "לא נרשמו חלופות"
                tradeoffs = "לא נרשמו פשרות"
            elif len(pipe_parts) == 2:
                title, decision_stmt = pipe_parts[0], pipe_parts[1]
                reason = "תועד דרך Telegram Bot"
                alts = "לא נרשמו חלופות"
                tradeoffs = "לא נרשמו פשרות"
            elif len(pipe_parts) == 3:
                title, decision_stmt, reason = pipe_parts[0], pipe_parts[1], pipe_parts[2]
                alts = "לא נרשמו חלופות"
                tradeoffs = "לא נרשמו פשרות"
            else:
                title, decision_stmt, reason = pipe_parts[0], pipe_parts[1], pipe_parts[2]
                alts = pipe_parts[3]
                tradeoffs = pipe_parts[4] if len(pipe_parts) > 4 else "נלקח בחשבון בתכנון"

            res = create_llm_wiki_decision(title, decision_stmt, reason, alts, tradeoffs)

            # Also register in DCM DB for unified search
            record = capture_engine.capture_text_or_url(
                title=f"החלטה: {title}",
                content_text=f"## החלטה\n{decision_stmt}\n\n## רציונל\n{reason}\n\n## חלופות\n{alts}\n\n## פשרות\n{tradeoffs}",
                primary_domain="general",
                custom_tags=["decision", "architecture"]
            )
            obsidian_sync_engine.export_record_to_markdown(record)

            reply = f"""⚖️ *ההחלטה נרשמה בהצלחה בכספת!*
📁 *קובץ:* `40_Decisions/{res['file_id']}.md`
📌 *כותרת:* {title}
💡 *החלטה:* {decision_stmt}
🔍 *נימוק:* {reason}
🔄 *סונכרן:* ליומן היומי, למפות התוכן ול-LLM Wiki."""
            send_telegram_message(bot_token, chat_id, reply, reply_to_message_id=message_id)
            return

        # C. NOTE / EVENT (/note, /פתק, /event, /אירוע, /זיכרון, /memo)
        elif command in ["/note", "/פתק", "/event", "/אירוע", "/זיכרון", "/memo"]:
            if not args and not saved_urls:
                send_telegram_message(bot_token, chat_id, "⚠️ אנא הזן תוכן לפתק או אירוע.\n*דוגמה:* `/note שוחחתי עם שרון על התקדמות הפרויקט`", reply_to_message_id=message_id)
                return

            note_text = args or (f"תמונה מטלגרם: {saved_urls[0]}" if saved_urls else "פתק ללא תוכן")
            title = args.split("\n")[0][:60] if args else "פתק מהיר מטלגרם"

            # 1. Append to LLM Wiki Daily Log
            append_to_llm_wiki_daily_log(note_text, category="notes")

            # 2. Capture into DCM
            record = capture_engine.capture_text_or_url(
                title=title,
                content_text=note_text,
                source_url=saved_urls[0] if saved_urls else None,
                source_type="infographic" if saved_urls else "note",
                primary_domain="general",
                custom_tags=["quick_note", "telegram"]
            )
            obsidian_sync_engine.export_record_to_markdown(record)

            reply = f"""📝 *הפתק תועד בהצלחה!*
📅 נרשם ביומן היומי של ה-Wiki (`daily/{datetime.now().strftime('%Y-%m-%d')}.md`)
📂 נשמר בכספת תחת `00 Inbox/`
📌 *כותרת:* {title}"""
            send_telegram_message(bot_token, chat_id, reply, reply_to_message_id=message_id)
            return

        # D. RESEARCH (/research, /מחקר, /investigate, /חקירה)
        elif command in ["/research", "/מחקר", "/investigate", "/חקירה"]:
            if not args:
                send_telegram_message(bot_token, chat_id, "⚠️ אנא הזן שאלת מחקר או נושא לחקירה.\n*דוגמה:* `/research מה ההשפעה של בוטיראט על רירית המעי?`", reply_to_message_id=message_id)
                return

            res = create_llm_wiki_research(topic=args, context=args)

            # Record in DCM
            record = capture_engine.capture_text_or_url(
                title=f"שאלת מחקר: {args[:50]}",
                content_text=args,
                primary_domain="health" if any(w in args for w in ["מעי", "תזונה", "בריאות", "בוטיראט", "סוכרת"]) else "general",
                custom_tags=["research_question", "pipeline"]
            )
            obsidian_sync_engine.export_record_to_markdown(record)

            reply = f"""🔬 *שאלת המחקר נקלטה בהצלחה ב-Wiki!*
📁 *תיקיית מעקב:* `20_Research/{res['folder_id']}/`
📌 *נושא:* {args}
🚀 *הצעד הבא:* הנושא זמין לחקירה מדעית מלאה (Investigate This Topic) בממשק ה-Web."""
            send_telegram_message(bot_token, chat_id, reply, reply_to_message_id=message_id)
            return

        # E. ASK LLM WIKI (/ask, /שאלה, /q)
        elif command in ["/ask", "/שאלה", "/q"]:
            if not args:
                send_telegram_message(bot_token, chat_id, "⚠️ אנא הזן שאלה לחיפוש ב-Wiki.\n*דוגמה:* `/ask מה ההחלטות שלנו בנוגע לארכיטקטורת זיכרון?`", reply_to_message_id=message_id)
                return

            send_telegram_message(bot_token, chat_id, f"🔎 *בודק ב-LLM Wiki...*\n\"{args}\"", reply_to_message_id=message_id)

            res = query_llm_wiki_rag(args)
            if "error" in res:
                send_telegram_message(bot_token, chat_id, f"⚠️ לא ניתן לתשאל את ה-Wiki כרגע:\n{res['error']}", reply_to_message_id=message_id)
                return

            ans = res.get("answer", "לא נמצאה תשובה.")
            conf = res.get("confidence", 92)
            sources = res.get("citations", []) or res.get("sources", [])

            sources_text = ""
            if sources:
                sources_text = "\n\n📚 *מקורות שצוטטו:*\n" + "\n".join([f"• `{s}`" for s in sources[:4]])

            reply = f"""💡 *תשובה מה-LLM Wiki:*

{ans}
{sources_text}

🎯 *ציון ביטחון:* {conf}%"""
            send_telegram_message(bot_token, chat_id, reply, reply_to_message_id=message_id)
            return

        # F. COOKING / CULINARY (/cook, /מתכון, /culinary, /בישול)
        elif command in ["/cook", "/מתכון", "/culinary", "/בישול"]:
            content = args or (f"מתכון מתמונה: {saved_urls[0]}" if saved_urls else "מתכון חדש")
            title = args.split("\n")[0][:60] if args else "מתכון מטלגרם"

            record = capture_engine.capture_text_or_url(
                title=title,
                content_text=content,
                source_url=saved_urls[0] if saved_urls else None,
                source_type="infographic" if saved_urls else "recipe",
                primary_domain="culinary",
                custom_tags=["recipe", "cook_pilot", "telegram"]
            )
            obsidian_sync_engine.export_record_to_markdown(record)
            append_to_llm_wiki_daily_log(f"🍳 מתכון חדש ב-Cook Pilot: {title}")

            reply = f"""🍳 *המתכון נשמר ב-Cook Pilot ובכספת!*
📂 *מיקום:* `02 By Domain/Culinary/` (זמין גם ב-LLM Wiki)
📌 *כותרת:* {record.title}
🏷️ *תגיות:* recipe, cook_pilot"""
            send_telegram_message(bot_token, chat_id, reply, reply_to_message_id=message_id)
            return

        # G. HEALTH (/health, /בריאות)
        elif command in ["/health", "/בריאות"]:
            content = args or (f"מידע בריאותי מתמונה: {saved_urls[0]}" if saved_urls else "פריט בריאות")
            title = args.split("\n")[0][:60] if args else "מידע בריאות מטלגרם"

            record = capture_engine.capture_text_or_url(
                title=title,
                content_text=content,
                source_url=saved_urls[0] if saved_urls else None,
                source_type="infographic" if saved_urls else "note",
                primary_domain="health",
                custom_tags=["health", "nutrition", "telegram"]
            )
            obsidian_sync_engine.export_record_to_markdown(record)
            append_to_llm_wiki_daily_log(f"🌿 פריט בריאות חדש: {title}")

            reply = f"""🌿 *פריט הבריאות נשמר בהצלחה!*
📂 *מיקום:* `02 By Domain/Health/` (מסונכרן עם Wiki Personal)
📌 *כותרת:* {record.title}"""
            send_telegram_message(bot_token, chat_id, reply, reply_to_message_id=message_id)
            return

        # H. PERSONAL (/personal, /אישי)
        elif command in ["/personal", "/אישי"]:
            content = args or "פתק אישי מטלגרם"
            title = args.split("\n")[0][:60] if args else "פתק אישי"

            record = capture_engine.capture_text_or_url(
                title=title,
                content_text=content,
                source_url=saved_urls[0] if saved_urls else None,
                source_type="note",
                primary_domain="personal",
                custom_tags=["personal", "telegram"]
            )
            obsidian_sync_engine.export_record_to_markdown(record)
            append_to_llm_wiki_daily_log(f"👤 פתק אישי: {title}")

            reply = f"""👤 *נשמר בתחום האישי (`wiki/personal/`)!*
📌 *כותרת:* {record.title}"""
            send_telegram_message(bot_token, chat_id, reply, reply_to_message_id=message_id)
            return

        # I. BUSINESS (/business, /עסקי)
        elif command in ["/business", "/עסקי"]:
            content = args or "פתק עסקי מטלגרם"
            title = args.split("\n")[0][:60] if args else "פתק עסקי"

            record = capture_engine.capture_text_or_url(
                title=title,
                content_text=content,
                source_url=saved_urls[0] if saved_urls else None,
                source_type="note",
                primary_domain="business",
                custom_tags=["business", "strategy", "telegram"]
            )
            obsidian_sync_engine.export_record_to_markdown(record)
            append_to_llm_wiki_daily_log(f"💼 פתק עסקי: {title}")

            reply = f"""💼 *נשמר בתחום העסקי (`wiki/business/`)!*
📌 *כותרת:* {record.title}"""
            send_telegram_message(bot_token, chat_id, reply, reply_to_message_id=message_id)
            return

        else:
            send_telegram_message(
                bot_token, chat_id,
                f"❓ הפקודה `{command}` אינה מוכרת.\nשלח */help* לצפייה בכל הפקודות הנתמכות.",
                reply_to_message_id=message_id
            )
            return

    # --- 4. DEFAULT FALLBACK: UNPREFIXED MESSAGES / MEDIA ---
    source_url = None
    if saved_urls:
        source_url = saved_urls[0] if len(saved_urls) == 1 else json.dumps(saved_urls, ensure_ascii=False)
    elif raw_text.startswith("http://") or raw_text.startswith("https://"):
        source_url = raw_text.split()[0]
        if any(v in source_url for v in ["youtube.com", "youtu.be", "vimeo.com"]):
            source_type = "video"
        elif any(p in source_url for p in ["podcast", "spotify.com"]):
            source_type = "podcast"
        else:
            source_type = "article"

    title_text = raw_text.strip().split("\n")[0] if raw_text else "פריט חדש מטלגרם"
    if len(title_text) > 80:
        title_text = title_text[:77] + "..."

    if not title_text and saved_urls:
        title_text = f"תמונה מטלגרם ({len(saved_urls)} קבצים)"

    # Capture record into DB & Vault
    record = capture_engine.capture_text_or_url(
        title=title_text,
        content_text=raw_text or "נלכד דרך Telegram Bot",
        source_url=source_url,
        source_type=source_type,
        workspace_id=os.getenv("DEFAULT_WORKSPACE", "default_ws"),
        owner_id=os.getenv("DEFAULT_OWNER", "default_owner"),
        primary_domain="general",
        custom_tags=["telegram_capture"]
    )
    obsidian_sync_engine.export_record_to_markdown(record)

    # Also log in daily log
    append_to_llm_wiki_daily_log(f"נלכד פריט מטלגרם: [[{record.title}]] ({record.source_type})")

    reply_text = f"""✅ *הפריט נשמר בהצלחה בכספת!*
📌 *כותרת:* {record.title}
📂 *תחום:* {record.primary_domain}
🏷️ *סוג:* {record.source_type}

💡 _טיפ: ניתן לנתב פריטים באמצעות פקודות: /decision, /note, /research, /ask, /cook ועוד. שלח /help לפירוט._"""
    send_telegram_message(bot_token, chat_id, reply_text, reply_to_message_id=message_id)
    logger.info(f"Captured Telegram item ID {record.id}: {record.title}")


def start_telegram_bot():
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not bot_token or "YOUR_" in bot_token or bot_token == "7891234567:AAFn_xXyZ12345abcDEfgHIJKlmNoPQRsTU":
        print("\n⚠️ TELEGRAM_BOT_TOKEN עדיין לא מוגדר בקובץ .env!")
        print("👉 כדי להפעיל את הבוט, היכנס לקובץ .env והחלף את TELEGRAM_BOT_TOKEN בטוקן שקיבלת מ-BotFather בטלגרם.\n")
        return

    # Fetch Bot info from Telegram API
    bot_username = ""
    bot_name = ""
    try:
        me_resp = httpx.get(f"{TELEGRAM_API_BASE}{bot_token}/getMe", timeout=10).json()
        if me_resp.get("ok"):
            result = me_resp["result"]
            bot_name = result.get("first_name", "Bot")
            bot_username = result.get("username", "")
            print("\n==================================================")
            print("✅ Telegram Bot מחובר בהצלחה ומקשיב להודעות!")
            print(f"🤖 שם הבוט: {bot_name}")
            print(f"🔍 שם משתמש בטלגרם: @{bot_username}")
            print("==================================================\n")
    except Exception as e:
        logger.warning(f"Could not fetch bot details: {e}")

    logger.info(f"🤖 starting Telegram Bot long polling for @{bot_username}...")
    offset = 0
    while True:
        try:
            url = f"{TELEGRAM_API_BASE}{bot_token}/getUpdates?offset={offset}&timeout=20"
            resp = httpx.get(url, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok"):
                    for update in data.get("result", []):
                        offset = update["update_id"] + 1
                        process_telegram_update(bot_token, update)
            elif resp.status_code == 401:
                print("\n❌ שגיאה 401: ה-TELEGRAM_BOT_TOKEN בקובץ .env אינו תקין (Unauthorized).")
                print("אנא ודא שהעתקת את הטוקן המדויק שקיבלת מ-BotFather לתוך קובץ .env.\n")
                time.sleep(10)
            else:
                logger.warning(f"Telegram API status {resp.status_code}: {resp.text}")
                time.sleep(5)
        except Exception as e:
            logger.error(f"Telegram polling error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    start_telegram_bot()
