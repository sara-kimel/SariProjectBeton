"""
מודל לטבלת Stone_size (גודל אבן)
טבלת lookup לגדלי אבן שונים בבטון
"""

from sqlalchemy import Column, Integer, String
from database import Base


class StoneSize(Base):
    """
    מחלקת מודל לגודל אבן בבטון
    הטבלה ב-DB: Stone_size
    תפקיד: רשימת גדלי אבן אפשריים בבטון
    """

    __tablename__ = "Stone_size"

    # מפתח ראשי - מתחיל מ-1300
    id = Column(Integer, primary_key=True, autoincrement=True)

    # תיאור גודל האבן (עד 50 תווים)
    # שם העמודה ב-DB: Stone_size
    Stone_size = Column("Stone_size", String(50), nullable=True)
