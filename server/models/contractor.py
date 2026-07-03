"""
מודל לטבלת Contractors (קבלנים)
מייצג קבלן שנשארו לו שאריות בטון להציע
"""

from sqlalchemy import Column, Integer, String, DateTime, text   # סוגי עמודות
from database import Base                        # מחלקת בסיס למודלים


class Contractor(Base):
    """
    מחלקת מודל לקבלן
    הטבלה ב-DB: Contractors
    תפקיד: קבלנים שיש להם שאריות בטון להציע ללקוחות
    """

    __tablename__ = "Contractors"   # שם הטבלה כפי שהוגדרה ב-SQL

    # מפתח ראשי - מתחיל מ-300 ועולה ב-1 בכל הוספה
    id = Column(Integer, primary_key=True, autoincrement=True)


    # שם פרטי הקבלן (עד 15 תווים)
    first_name = Column(String(15), nullable=True)

    # שם  משפחה הקבלן (עד 15 תווים)
    last_name = Column(String(15), nullable=True)

    # שם משתמש של הקבלן — ייחודי, חובה (מיגרציה 002)
    user_name = Column(String(50), nullable=False, unique=True)

    # סיסמה מוצפנת (bcrypt) — שלב 1. לעולם לא בטקסט גלוי, לא מוחזר ב-DTO.
    password_hash = Column(String(255), nullable=True)

    # מספר טלפון של הקבלן (עד 15 תווים)
    phone = Column(String(15), nullable=True)

    # חותמת יצירה (מיגרציה 002)
    created_at = Column(DateTime, nullable=False, server_default=text("SYSDATETIME()"))
