"""
שירות התראות בתוך-אפליקציה (In-app) — שלב 4.
מחליף את השלד הישן (שהעלה NotImplementedError). כותב רשומות Notifications
ומספק פונקציות-אירוע טיפוסיות. ה-create מבצע flush בלבד — ה-commit באחריות
השירות שמנהל את הטרנזקציה (למשל אישור עסקה או יצירת התאמות), כדי שההתראה
תהיה אטומית יחד עם האירוע.

אירועים (SPEC §11):
  MATCH_FOUND       -> ללקוח: "נמצאה שארית/פנייה מתאימה"
  CUSTOMER_ACCEPTED -> לקבלן: "לקוח אישר את הפנייה" + טלפון הלקוח
  OFFER_TAKEN       -> ללקוחות שהותאמו: "ההצעה כבר נתפסה"
"""

from typing import Optional
from sqlalchemy.orm import Session

from repository.notification_repository import NotificationRepository


class NotificationService:
    def __init__(self, db: Session):
        self.repo = NotificationRepository(db)

    def create_notification(
        self,
        user_id: int,
        user_role: str,
        type: str,
        title: str,
        body: str,
        related_offer_id: Optional[int] = None,
        related_request_id: Optional[int] = None,
    ):
        return self.repo.create(
            user_id=user_id,
            user_role=user_role,
            type=type,
            title=title,
            body=body,
            related_offer_id=related_offer_id,
            related_request_id=related_request_id,
        )

    # ---- אירועים טיפוסיים ----

    def notify_match_found_for_customer(
        self, customer_id: int, offer_id: int, request_id: int,
        price: Optional[str] = None, distance_m: Optional[float] = None,
    ):
        parts = ["נמצאה שארית בטון מתאימה לבקשתך!"]
        if price:
            parts.append(f"מחיר: {price}")
        if distance_m is not None:
            parts.append(f"מרחק: {distance_m / 1000:.1f} ק\"מ")
        parts.append("היכנס/י לאישור.")
        return self.create_notification(
            user_id=customer_id, user_role="customer", type="MATCH_FOUND",
            title="נמצאה התאמה", body=" ".join(parts),
            related_offer_id=offer_id, related_request_id=request_id,
        )

    def notify_customer_accepted_to_contractor(
        self, contractor_id: int, offer_id: int, request_id: int, customer_phone: Optional[str],
    ):
        phone = customer_phone or "לא זמין"
        return self.create_notification(
            user_id=contractor_id, user_role="contractor", type="CUSTOMER_ACCEPTED",
            title="לקוח אישר את הפנייה",
            body=f"לקוח אישר את הפנייה שלך. ליצירת קשר — טלפון: {phone}",
            related_offer_id=offer_id, related_request_id=request_id,
        )

    def notify_offer_taken_to_customer(self, customer_id: int, offer_id: int, request_id: int):
        return self.create_notification(
            user_id=customer_id, user_role="customer", type="OFFER_TAKEN",
            title="ההצעה כבר נתפסה",
            body="לקוח אחר אישר את ההצעה לפניך. נודיע לך על שאריות מתאימות נוספות.",
            related_offer_id=offer_id, related_request_id=request_id,
        )
