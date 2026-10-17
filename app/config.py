import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / ".env"
if env_path.exists():
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip().strip("'").strip('"')

class Settings:
    PROJECT_NAME: str = "Domain Content Manager"
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = BASE_DIR / "data"
    VAULT_DIR: Path = BASE_DIR / "vault"
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'data' / 'domain_content.db'}")
    DEFAULT_WORKSPACE: str = os.getenv("DEFAULT_WORKSPACE", "default_ws")
    DEFAULT_OWNER: str = os.getenv("DEFAULT_OWNER", "default_owner")

    def __init__(self):
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.VAULT_DIR.mkdir(parents=True, exist_ok=True)

settings = Settings()
