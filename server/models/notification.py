"""
מודל לטבלת Notifications (מרכז התראות בתוך-אפליקציה) — שלב 4.
כל אירוע (נמצאה התאמה / לקוח אישר / ההצעה נתפסה) כותב רשומה למשתמש הרלוונטי.
user_id/user_role לוגיים (המשתמש עשוי להיות לקוח/קבלן/מנהל) — ללא FK קשיח.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, text
from database import Base


class Notification(Base):
    __tablename__ = "Notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # נמען ההתראה
    user_id = Column(Integer, nullable=False)
    user_role = Column(String(20), nullable=False)          # customer / contractor / admin

    # סוג האירוע: MATCH_FOUND / CUSTOMER_ACCEPTED / OFFER_TAKEN ...
    type = Column(String(40), nullable=False)

    title = Column(String(200), nullable=True)
    body = Column(String(1000), nullable=True)

    # קישור לישות רלוונטית (לניווט מהמרכז)
    related_offer_id = Column(Integer, nullable=True)
    related_request_id = Column(Integer, nullable=True)

    is_read = Column(Boolean, nullable=False, server_default=text("0"))
    created_at = Column(DateTime, nullable=False, server_default=text("SYSDATETIME()"))
