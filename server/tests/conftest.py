"""
Fixtures משותפים לבדיקות.
- client: FastAPI TestClient (לבדיקות health / API בלי צורך בהרצת uvicorn).
- db: סשן SQLAlchemy אמיתי מול DB beton (לבדיקות E2E של המנוע).
"""

import pytest
from fastapi.testclient import TestClient

from app import app
from database import SessionLocal


@pytest.fixture(scope="session")
def client():
    """לקוח בדיקות שמריץ את אפליקציית ה-FastAPI בזיכרון (ללא שרת חי)."""
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def db():
    """סשן DB אמיתי; נסגר בסוף כל בדיקה."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
