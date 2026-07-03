"""
שירות תזמור ההתאמות (שלב 3) — מחבר בין שמירת הפנייה/הבקשה למנוע ההתאמה
וליצירת רשומות OfferMatches, הכול בטרנזקציה אחת (אטומיות, SPEC §5.4):
אם יצירת ההתאמות נכשלת — הפנייה/הבקשה לא נשמרת חלקית.

- create_offer_and_match  : טריגר A (פניית קבלן) — שומר פנייה + מריץ מנוע + יוצר Matches.
- create_request_and_match: טריגר B (בקשת לקוח)  — שומר בקשה + מריץ מנוע הפוך + יוצר Matches.

ההתראות בפועל ואישור טרנזקציוני — שלב 4.
"""

from sqlalchemy.orm import Session

from models.contractor_concrete_request import ContractorConcreteRequest
from models.concrete_request import ConcreteRequest
from repository.offer_match_repository import OfferMatchRepository
from service.matching_engine_service import (
    match_requests_for_offer,
    match_offers_for_request,
)
from service.notification_service import NotificationService
from service.expiry_service import expire_stale_offers
from type_safety import safe_int, safe_float


class MatchService:
    def __init__(self, db: Session):
        self.db = db
        self.notifier = NotificationService(db)

    # -------------------------------------------------------------------
    # עזר: יצירת רשומת OfferMatches (NOTIFIED) + התראת MATCH_FOUND ללקוח
    # -------------------------------------------------------------------
    def _create_match_and_notify(self, repo, offer_id, request_id, customer_id, score, distance_m, price):
        """יוצר התאמה חדשה (מדלג על כפילות) ומתריע ללקוח. מחזיר True אם נוצרה חדשה."""
        if offer_id is None or request_id is None:
            return False
        row = repo.create_notified(
            offer_id=offer_id,
            request_id=request_id,
            customer_id=customer_id,
            score=safe_float(score),
            distance_m=safe_float(distance_m),
        )
        if row is None:
            return False
        if customer_id is not None:
            self.notifier.notify_match_found_for_customer(
                customer_id=customer_id, offer_id=offer_id, request_id=request_id,
                price=price, distance_m=safe_float(distance_m),
            )
        return True

    # -------------------------------------------------------------------
    # טריגר A — פניית קבלן
    # -------------------------------------------------------------------
    def create_offer_and_match(self, contractor_id: int, data) -> dict:
        """
        שומר את הפנייה (status=OPEN), מריץ את המנוע קדימה, יוצר Matches לכל מועמד,
        ומחזיר סיכום {offer_id, matched_count, matches(מדורג)}. הכול בטרנזקציה אחת.
        """
        try:
            expire_stale_offers(self.db)  # תפוגה עצלה לפני התאמה (OD-11)
            offer = ContractorConcreteRequest(
                concrete_id=data.concrete_id,
                contractor_id=contractor_id,
                quantity=data.quantity,
                address=data.address,
                lat=data.lat,
                lng=data.lng,
                expiry_time=data.expiry_time,
                price=data.price,
                status="OPEN",
            )
            self.db.add(offer)
            self.db.flush()            # מקבלים request_id בלי לסגור טרנזקציה
            offer_id = int(offer.request_id)

            offer_dict = {
                "lat": float(offer.lat),
                "lng": float(offer.lng),
                "concrete_id": offer.concrete_id,
                "quantity": offer.quantity,
            }
            candidates = match_requests_for_offer(self.db, offer_dict)

            repo = OfferMatchRepository(self.db)
            price = data.price
            for c in candidates:
                self._create_match_and_notify(
                    repo,
                    offer_id=offer_id,
                    request_id=safe_int(c.get("request_id")),
                    customer_id=safe_int(c.get("customer_id")),
                    score=c.get("score"),
                    distance_m=c.get("distance_m"),
                    price=price,
                )

            self.db.commit()           # קומיט יחיד — הפנייה + ההתאמות + ההתראות ביחד

            matches = repo.get_view_for_offer(offer_id)
            return {"offer_id": offer_id, "matched_count": len(matches), "matches": matches}
        except Exception:
            self.db.rollback()
            raise

    # -------------------------------------------------------------------
    # טריגר B — בקשת לקוח (הפוך, SPEC §5.6)
    # -------------------------------------------------------------------
    def create_request_and_match(self, customer_id: int, data) -> ConcreteRequest:
        """
        שומר את הבקשה (status=OPEN), מריץ את המנוע ההפוך (מוצא פניות פתוחות תואמות),
        ויוצר Matches לכל פנייה. מחזיר את הבקשה שנשמרה. הכול בטרנזקציה אחת.
        ההתאמות ניתנות לצפייה ב-GET /matches/request/{id}.
        """
        try:
            expire_stale_offers(self.db)  # תפוגה עצלה — לא נתאים פניות שפגו (OD-11)
            req = ConcreteRequest(
                customer_id=customer_id,
                purpose_id=data.purpose_id,
                quantity=data.quantity,
                address=data.address,
                lat=data.lat,
                lng=data.lng,
                status="OPEN",
            )
            self.db.add(req)
            self.db.flush()
            request_id = int(req.request_id)

            request_dict = {
                "lat": float(req.lat),
                "lng": float(req.lng),
                "purpose_id": req.purpose_id,
                "quantity": req.quantity,
            }
            offers = match_offers_for_request(self.db, request_dict)

            repo = OfferMatchRepository(self.db)
            for o in offers:
                self._create_match_and_notify(
                    repo,
                    offer_id=safe_int(o.get("request_id")),   # request_id של הפנייה = offer_id
                    request_id=request_id,
                    customer_id=customer_id,
                    score=o.get("score"),
                    distance_m=o.get("distance_m"),
                    price=o.get("price"),
                )

            self.db.commit()
            self.db.refresh(req)
            return req
        except Exception:
            self.db.rollback()
            raise
