import os
from pathlib import Path

class Settings:
    PROJECT_NAME: str = "Domain Content Manager"
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    VAULT_DIR: Path = BASE_DIR / "vault"
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'data' / 'domain_content.db'}")
    DEFAULT_WORKSPACE: str = os.getenv("DEFAULT_WORKSPACE", "default_ws")
    DEFAULT_OWNER: str = os.getenv("DEFAULT_OWNER", "default_owner")

    def __init__(self):
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.VAULT_DIR.mkdir(parents=True, exist_ok=True)

settings = Settings()
