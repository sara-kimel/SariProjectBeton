"""
מודל לטבלת Reliant (סומך הבטון)
טבלת lookup לרמות סומך שונות של בטון
"""

from sqlalchemy import Column, Integer, String
from database import Base


class Reliant(Base):
    """
    מחלקת מודל לסומך בטון
    הטבלה ב-DB: Reliant
    תפקיד: רשימת רמות סומך אפשריות (קשיחות הבטון)
    """

    __tablename__ = "Reliant"

    # מפתח ראשי - מתחיל מ-1200
    id = Column(Integer, primary_key=True, autoincrement=True)

    # תיאור הסומך (עד 50 תווים)
    # שם העמודה הוא Reliant - אותו שם כמו הטבלה
    Reliant = Column("Reliant", String(50), nullable=True)
