"""
מודל לטבלת Concrete_type (סוג בטון)
מחבר בין כל המאפיינים של הבטון - חוזק, סומך, גודל אבן, מטרה
"""

from sqlalchemy import Column, Integer, ForeignKey
from database import Base


class ConcreteType(Base):
    """
    מחלקת מודל לסוג בטון מורכב
    הטבלה ב-DB: Concrete_type
    תפקיד: שילוב של מאפיינים שיוצרים סוג בטון ספציפי
    """

    __tablename__ = "Concrete_type"

    # מפתח ראשי - מתחיל מ-2000
    id = Column(Integer, primary_key=True, autoincrement=True)

    # קישור לחוזק
    strength_id = Column(Integer, ForeignKey("Strength.id"), nullable=True)

    # קישור לסומך
    Reliant_id = Column(Integer, ForeignKey("Reliant.id"), nullable=True)

    # קישור לגודל אבן
    Stone_size_id = Column(Integer, ForeignKey("Stone_size.id"), nullable=True)

    # קישור למטרה
    Purpose_id = Column(Integer, ForeignKey("Purpose.id"), nullable=True)
