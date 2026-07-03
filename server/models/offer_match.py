"""
מודל לטבלת OfferMatches (התאמות בין פניית קבלן לבקשת לקוח) — שלב 3.
כל רשומה מייצגת התאמה שהמנוע יצר (SPEC §7.2). היא גם הבסיס ל"מי הותאם"
ול"מי אישר" (האישור הטרנזקציוני עצמו — שלב 4).
"""

from sqlalchemy import Column, Integer, DECIMAL, String, DateTime, ForeignKey, text
from database import Base


class OfferMatch(Base):
    """
    מחלקת מודל להתאמה.
    הטבלה ב-DB: OfferMatches
    """

    __tablename__ = "OfferMatches"

    # מפתח ראשי
    id = Column(Integer, primary_key=True, autoincrement=True)

    # מזהה הפנייה (ContractorConcreteRequests.request_id)
    offer_id = Column(Integer, ForeignKey("ContractorConcreteRequests.request_id"), nullable=False)

    # מזהה הבקשה (ConcreteRequests.request_id)
    request_id = Column(Integer, ForeignKey("ConcreteRequests.request_id"), nullable=False)

    # מזהה הלקוח (דנורמליזציה לנוחות)
    customer_id = Column(Integer, ForeignKey("Customers.id"), nullable=True)

    # ניקוד ההתאמה מהמנוע
    score = Column(DECIMAL(12, 4), nullable=True)

    # מרחק במטרים בין הפנייה לבקשה
    distance_m = Column(DECIMAL(12, 2), nullable=True)

    # מצב ההתאמה: NOTIFIED / ACCEPTED / DECLINED / SUPERSEDED / EXPIRED (SPEC §6.3)
    status = Column(String(20), nullable=False, server_default=text("'NOTIFIED'"))

    # חותמת יצירה
    created_at = Column(DateTime, nullable=False, server_default=text("SYSDATETIME()"))

    # מתי הלקוח הגיב (אישר/דחה) — שלב 4
    responded_at = Column(DateTime, nullable=True)
