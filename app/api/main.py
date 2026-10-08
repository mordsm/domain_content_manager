from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.db.database import init_db
from app.api.routes import router
from app.config import settings

app = FastAPI(title="Domain Content Manager API", version="0.1.0")

# Allow every origin, method, and header (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

# Mount vault and data directories to serve any file path over HTTP
if settings.VAULT_DIR.exists():
    app.mount("/vault", StaticFiles(directory=str(settings.VAULT_DIR)), name="vault")

if settings.DATA_DIR.exists():
    app.mount("/data", StaticFiles(directory=str(settings.DATA_DIR)), name="data")

app.include_router(router)

@app.get("/manifest.json")
def get_manifest():
    return {
        "name": "Domain Content Manager",
        "short_name": "ContentMgr",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#090d16",
        "theme_color": "#0f172a",
        "share_target": {
            "action": "/",
            "method": "GET",
            "params": {
                "title": "title",
                "text": "text",
                "url": "url"
            }
        }
    }

@app.get("/", response_class=HTMLResponse)
def root():
    template_path = Path(__file__).parent.parent / "templates" / "index.html"
    if template_path.exists():
        return HTMLResponse(content=template_path.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>Domain Content Manager API</h1>")
