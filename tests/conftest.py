import os
import pytest
from pathlib import Path
from sqlmodel import SQLModel, create_engine, Session

# Enable testing mode before loading app modules
os.environ["TESTING"] = "true"

from app.db.database import init_db, engine

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)

