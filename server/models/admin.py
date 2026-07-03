"""
מודל לטבלת Admins (מנהלים) — שלב 1.
משתמש מנהל: תפקיד יחיד, טבלה נפרדת (OD-8).
"""

from sqlalchemy import Column, Integer, String, DateTime, text
from database import Base


class Admin(Base):
    __tablename__ = "Admins"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # שם משתמש ייחודי לכניסה
    user_name = Column(String(50), nullable=False, unique=True)

    # סיסמה מוצפנת (bcrypt) — חובה
    password_hash = Column(String(255), nullable=False)

    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)

    created_at = Column(DateTime, nullable=False, server_default=text("SYSDATETIME()"))
