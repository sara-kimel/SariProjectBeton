"""
מודל לטבלת ConcreteRequests (בקשות בטון של לקוחות)
מייצג בקשה של לקוח לקבל בטון בכמות מסויימת
"""

from sqlalchemy import Column, Integer, String, DECIMAL, Date, ForeignKey, text  # סוגי עמודות וקשרים
from sqlalchemy.sql import func                       # פונקציות SQL כמו GETDATE
from database import Base                             # מחלקת בסיס למודלים


class ConcreteRequest(Base):
    """
    מחלקת מודל לבקשת בטון של לקוח
    הטבלה ב-DB: ConcreteRequests
    תפקיד: שמירת בקשות של לקוחות לבטון - כמות, מטרה, מיקום
    """

    __tablename__ = "ConcreteRequests"

    # מפתח ראשי - מתחיל מ-200 ועולה ב-1
    request_id = Column(Integer, primary_key=True, autoincrement=True)

    # מזהה הלקוח - מפתח זר לטבלת Customers
    customer_id = Column(Integer, ForeignKey("Customers.id"), nullable=True)

    # מזהה המטרה (קטגוריה) - מפתח זר לטבלת Purpose
    purpose_id = Column(Integer, ForeignKey("Purpose.id"), nullable=True)

    # כמות הבטון הנדרשת במטרים מעוקבים (עד 6 ספרות, 2 אחרי הנקודה)
    quantity = Column(DECIMAL(6, 2), nullable=True)

    # כתובת הלקוח (עד 255 תווים)
    address = Column(String(255), nullable=True)

    # קו רוחב לאיתור על המפה (חובה)
    lat = Column(DECIMAL(9, 6), nullable=False)

    # קו אורך לאיתור על המפה (חובה)
    lng = Column(DECIMAL(9, 6), nullable=False)

    # תאריך הבקשה - ברירת מחדל היום הנוכחי
    date = Column(Date, nullable=False, server_default=func.getdate())

    # status: סטטוס הבקשה לאחר נורמליזציה (שלב 0) — OPEN / CLOSED / CANCELLED.
    # עמודת NVARCHAR(20) NOT NULL עם ברירת מחדל 'OPEN' בצד ה-DB.
    status = Column(String(20), nullable=False, server_default=text("'OPEN'"))


