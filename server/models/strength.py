"""
מודל לטבלת Strength (חוזק הבטון)
טבלת lookup לסוגי חוזק שונים של בטון
"""

from sqlalchemy import Column, Integer, String
from database import Base


class Strength(Base):
    """
    מחלקת מודל לחוזק בטון
    הטבלה ב-DB: Strength
    תפקיד: רשימת חוזקים אפשריים של בטון (למשל ב-30, ב-40 וכו')
    """

    __tablename__ = "Strength"

    # מפתח ראשי - מתחיל מ-1100
    id = Column(Integer, primary_key=True, autoincrement=True)

    # תיאור החוזק (עד 50 תווים)
    strength = Column(String(50), nullable=True)

    # דירוג סידורי לחוזק — מאפשר השוואת ">=" בין חוזקים (מיגרציה 001, שלב 0)
    sort_order = Column(Integer, nullable=True)
