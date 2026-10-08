import json
from datetime import datetime, timezone
from sqlmodel import Session, select, delete
from app.db.database import engine, init_db
from app.db.models import ContentRecord, ContentRelation
from app.domain.obsidian_sync import obsidian_sync_engine

def seed_rich_data():
    init_db()
    with Session(engine) as session:
        # Clear existing records and relations for a clean real vault
        session.exec(delete(ContentRelation))
        session.exec(delete(ContentRecord))
        session.commit()

        records_data = [
            {
                "title": "טיפול טבעי בחיזוק שורשי השיער ושיקום הקרקפת",
                "source_url": "https://youtube.com/watch?v=hair_care_1",
                "source_type": "video",
                "primary_domain": "hair",
                "domains": ["hair", "health"],
                "summary": "פרוטוקול עיסוי קרקפת יומי עם שמנים אתריים (רוזמרין 2% ושמן חוחובה כמנשא) לגירוי זרימת דם לזקיקי השיער.",
                "keywords": ["שמן_חוחובה", "רוזמרין", "חיזוק_שורשים", "קרקפת", "נשירה"],
                "transcript": "במחקרים קליניים נמצא כי שמן רוזמרין בריכוז 2% משפר את צמיחת השיער בדומה למינוקסידיל 2% ללא תופעות לוואי של גירוי. מומלץ לעסות 5 טיפות שמן רוזמרין מהולות ב-10 מ\"ל שמן חוחובה על עור הקרקפת למשך 10 דקות לפני החפיפה.",
                "reliability_layer": "research",
                "risk_level": "low",
                "seasonality": "year_round",
                "status": "tagged",
                "domain_data": {
                    "problem_type": "נשירת שיער ושיער דליל",
                    "method_name": "עיסוי קרקפת בשמנים אתריים",
                    "active_ingredients": ["שמן רוזמרין", "שמן חוחובה", "וויטמין E"]
                }
            },
            {
                "title": "מרק כתום מחזק חיסון עם ג'ינג'ר, כורכום וחלב קוקוס",
                "source_url": "https://culinary-health.com/orange-soup",
                "source_type": "article",
                "primary_domain": "culinary",
                "domains": ["culinary", "health", "diet"],
                "summary": "מתכון למרק דלעת, גזר ודלורית עשיר בבטא-קרוטן, ג'ינג'ר טרי וכורכומין לספיגה מיטבית בשילוב שומן בריא.",
                "keywords": ["מרק_כתום", "ג'ינג'ר", "כורכום", "מערכת_החיסון", "חורף"],
                "transcript": "הכנת מרק כתום עשיר: מאדים בצל ושום בשמן זית, מוסיפים גזר חתוך, דלעת ודלורית. מוסיפים 2 כפיות ג'ינג'ר מגורר טרי, כפית כורכום ומעט פלפל שחור (להגברת ספיגת הכורכומין ב-2000%). יוצקים ציר ירקות ומבשלים 30 דקות עד לריכוך. טוחנים בבלנדר מוט ומוסיפים 200 מ\"ל חלב קוקוס.",
                "reliability_layer": "personal",
                "risk_level": "none",
                "seasonality": "winter",
                "status": "tagged",
                "domain_data": {
                    "dish_type": "מרק חם",
                    "ingredients": ["גזר", "דלעת", "דלורית", "ג'ינג'ר", "כורכום", "חלב קוקוס"],
                    "technique": "אידוי, בישול איטי וטחינה"
                }
            },
            {
                "title": "אינפוגרפיק: ציר המעי-מוח וייצור סרוטונין במערכת העיכול",
                "source_url": "https://microbiome-institute.org/infographic-gut-brain",
                "source_type": "infographic",
                "primary_domain": "health",
                "domains": ["health", "diet"],
                "summary": "תרשים רפואי המציג כיצד 90% מהסרוטונין בגוף מיוצר ע\"י תאי אפיתל במעי בהשפעת חיידקים מפרישי בוטיראט.",
                "keywords": ["ציר_מעי_מוח", "סרוטונין", "מיקרוביום", "בוטיראט", "עצב_הוואגוס"],
                "transcript": "אינפוגרפיק מסכם: 1. חיידקי מעי מתסיסים סיבים תזונתיים. 2. נוצרות חומצות שומן קצרות שרשרת (SCFA). 3. אותות עצביים מועברים דרך עצב הוואגוס למוח. 4. השפעה ישירה על מצב הרוח, השינה והאנרגיה.",
                "reliability_layer": "research",
                "risk_level": "none",
                "seasonality": "year_round",
                "status": "tagged",
                "domain_data": {
                    "condition": "עייפות כרונית וחרדה",
                    "body_system": "מערכת העיכול והעצבים",
                    "evidence_level": "systematic_review"
                }
            },
            {
                "title": "מדריך ליקוט פטריות מאכל חורפיות והתגוננות מרעלים",
                "source_url": "https://foraging-israel.co.il/mushrooms-winter",
                "source_type": "article",
                "primary_domain": "foraging",
                "domains": ["foraging", "health"],
                "summary": "מדריך שדה לזיהוי אורניות, גזעניות ואוזניות כלך ביערות אורנים, כולל כללי זהירות חמורים למניעת הרעלה.",
                "keywords": ["ליקוט", "פטריות", "אורניה", "אזהרת_רעל", "חורף"],
                "transcript": "כללי ברזל בליקוט פטריות: 1. לא אוספים פטרייה שלא מזהים בוודאות של 100%. 2. נזהרים מפטריות בעלות דפים לבנים מתחת לכובע (סכנת אמנית המוות). 3. אורנייה מצויה מתאפיינת בספוג צהוב מתחת לכובע וקרום דביק.",
                "reliability_layer": "traditional",
                "risk_level": "high",
                "seasonality": "winter",
                "status": "tagged",
                "domain_data": {
                    "season": "חורף",
                    "region": "יערות הכרמל והצפון",
                    "risk_assessment": "high",
                    "usable_parts": ["כובע הפטרייה", "רגל צעירה"]
                }
            },
            {
                "title": "גידול נענע, לואיזה ומנטה בערוגות ביתיות ובאדניות",
                "source_url": "https://garden-life.co.il/herbs",
                "source_type": "note",
                "primary_domain": "garden",
                "domains": ["garden", "culinary"],
                "summary": "הנחיות להשקיה, תיחום שורשים וחשיפה לשמש עבור צמחי תה וצמחי מרפא בגינה הביתית.",
                "keywords": ["גינון", "נענע", "לואיזה", "צמחי_מרפא", "אדנית"],
                "transcript": "צמחי ממשפחת השפתיים (נענע, מנטה) נוטים להתפשט במהירות דרך שלוחות תת-קרקעיות (שלוחות). מומלץ לשתול אותם באדניות נפרדות כדי למנוע השתלטות על שאר הערוגה. השקיה סדירה וגיזום ענפים מעודדים צימוח צפוף.",
                "reliability_layer": "personal",
                "risk_level": "none",
                "seasonality": "spring",
                "status": "tagged",
                "domain_data": {
                    "plant_type": "צמחי תלישה ותה",
                    "season": "אביב וקיץ",
                    "climate_zone": "ים תיכוני"
                }
            },
            {
                "title": "פרוטוקול מדיטציה ומיינדפולנס להפחתת מתח וחרדה",
                "source_url": "https://mindfulness-institute.org/stress-reduction",
                "source_type": "article",
                "primary_domain": "mental",
                "domains": ["mental", "health"],
                "summary": "תרגול נשימות מודעות ומדיטציית סריקת גוף של 15 דקות ביום להורדת רמות קורטיזול ושיפור הריכוז.",
                "keywords": ["מדיטציה", "מיינדפולנס", "חרדה", "קורטיזול", "סטרס"],
                "transcript": "מחקרים נוירו-פסיכולוגיים מראים כי תרגול מיינדפולנס יומי של 15 דקות במשך 8 שבועות מעבה את הקורטקס הקדם-מצחי ומקטין את האמיגדלה. מומלץ להתחיל בישיבה זקופה, 4 שניות שאיפה, 4 שניות עצירה ו-6 שניות נשיפה.",
                "reliability_layer": "research",
                "risk_level": "none",
                "seasonality": "year_round",
                "status": "tagged",
                "domain_data": {
                    "practice_type": "מדיטציה ונשימות",
                    "emotional_state": "הפחתת חרדה ופוקוס",
                    "cognitive_technique": "MBSR סריקת גוף"
                }
            },
            {
                "title": "מדריך פיננסי: ניהול תקציב משפחתי והשקעה במדדי מניות",
                "source_url": "https://finance-blog.co.il/budget-index-funds",
                "source_type": "article",
                "primary_domain": "financial",
                "domains": ["financial", "general"],
                "summary": "שיטת 50/30/20 לחלוקת הכנסה והשקעה פסיבית בקרנות מחקות מדד S&P 500 לעצמאות כלכלית.",
                "keywords": ["תקציב", "השקעות", "כסף", "חיסכון", "מניות"],
                "transcript": "ניהול תקציב נכון מתחיל במעקב אחר הוצאות קבועות ומשתנות. הכלל המומלץ: 50% לצרכים חיוניים, 30% לרצונות, ו-20% לחיסכון והשקעות. השקעה עקבית במדדים רחבים לאורך זמן מנצלת את אפקט הריבית דריבית.",
                "reliability_layer": "personal",
                "risk_level": "medium",
                "seasonality": "year_round",
                "status": "tagged",
                "domain_data": {
                    "asset_class": "קרנות מחקות מדד (S&P 500)",
                    "financial_goal": "עצמאות פיננסית וחיסכון לטווח ארוך",
                    "risk_profile": "medium"
                }
            }
        ]

        created_records = []
        for d in records_data:
            text_for_sub = (d.get("transcript") or "") + " " + (d.get("title") or "")
            from app.services.llm_service import llm_service
            analysis = llm_service.analyze_content(text_for_sub)
            sub_topics = d.get("sub_topics", analysis.get("sub_topics", []))
            custom_tags = d.get("custom_tags", ["שואב_אוטומטי", "רשומה_נבחרת"] if d["primary_domain"] in ["mental", "financial"] else ["מומלץ"])

            rec = ContentRecord(
                title=d["title"],
                source_url=d["source_url"],
                source_type=d["source_type"],
                primary_domain=d["primary_domain"],
                domains_json=json.dumps(d["domains"], ensure_ascii=False),
                sub_topics_json=json.dumps(sub_topics, ensure_ascii=False),
                custom_tags_json=json.dumps(custom_tags, ensure_ascii=False),
                summary=d["summary"],
                keywords_json=json.dumps(d["keywords"], ensure_ascii=False),
                transcript=d["transcript"],
                reliability_layer=d["reliability_layer"],
                risk_level=d["risk_level"],
                seasonality=d["seasonality"],
                status=d["status"],
                domain_data_json=json.dumps(d["domain_data"], ensure_ascii=False),
                is_cross_domain=len(d["domains"]) > 1,
                capture_date=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            )
            session.add(rec)
            session.commit()
            session.refresh(rec)
            created_records.append(rec)

        # Create bidirectional relation link between Infographic and Hair care / Health
        rel1 = ContentRelation(source_id=created_records[2].id, target_id=created_records[1].id, relation_type="summary_of")
        rel2 = ContentRelation(source_id=created_records[1].id, target_id=created_records[2].id, relation_type="derived_from")
        session.add(rel1)
        session.add(rel2)
        session.commit()

        # Sync all to Obsidian Vault Markdown files
        for r in created_records:
            obsidian_sync_engine.export_record_to_markdown(r)

        print(f"Successfully seeded {len(created_records)} rich multi-domain records into database and Obsidian Vault!")

if __name__ == "__main__":
    seed_rich_data()
