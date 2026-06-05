from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.config import settings

# In PostgreSQL, we don't need connect_args={"check_same_thread": False} which is SQLite specific
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True  # Helpful to detect disconnected connections
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy 2.0 declarative models"""
    pass


def get_db() -> Generator:
    """Dependency generator for database sessions"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
