import sys
import os
import pytest

# Add root folder to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal, engine
from app.models import Base
from scripts.seed import seed


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Ensure database schema is created and seed database with demo data before tests run."""
    # 1. Ensure all tables are created
    Base.metadata.create_all(bind=engine)
    
    # 2. Seed database
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()
