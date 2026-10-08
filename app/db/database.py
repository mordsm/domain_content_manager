import os
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import StaticPool
from app.config import settings

def get_engine():
    if os.getenv("TESTING", "").lower() == "true":
        return create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )
    return create_engine(
        settings.DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False}
    )

engine = get_engine()

def init_db(test_engine=None):
    target_engine = test_engine or engine
    SQLModel.metadata.create_all(target_engine)

def get_session():
    with Session(engine) as session:
        yield session
