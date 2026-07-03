"""
שירות סגירת עסקה (Accept/Decline) — שלב 4, לב הזרימה המרכזית.

אישור אטומי (OD-5, SPEC §13.3): broadcast לכל המותאמים + הראשון שמאשר זוכה.
הנקודה הקריטית = עדכון מותנה `UPDATE ... WHERE status='OPEN'` ובדיקת rowcount:
רק מי שה-UPDATE שלו השפיע על שורה זוכה; היתר מקבלים 409 "כבר נתפסה".
כל עדכוני הסטטוס + ההתראות באותה טרנזקציה של האישור.
"""

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from service.notification_service import NotificationService
from type_safety import safe_int


def _now_naive_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class DealService:
    def __init__(self, db: Session):
        self.db = db
        self.notifier = NotificationService(db)

    # -------------------------------------------------------------------
    # אישור עסקה — אטומי (first-wins)
    # -------------------------------------------------------------------
    def accept_match(self, match_id: int, customer_id: int) -> dict:
        db = self.db
        try:
            match = db.execute(
                text("SELECT id, offer_id, request_id, customer_id, [status] "
                     "FROM OfferMatches WHERE id = :mid"),
                {"mid": match_id},
            ).mappings().first()
            if match is None:
                raise HTTPException(status_code=404, detail="התאמה לא נמצאה")
            if safe_int(match["customer_id"]) != int(customer_id):
                raise HTTPException(status_code=403, detail="אין הרשאה לאשר התאמה זו")
            if (match["status"] or "").upper() != "NOTIFIED":
                raise HTTPException(status_code=409, detail="לא ניתן לאשר התאמה שאינה פעילה")

            offer_id = int(match["offer_id"])
            request_id = int(match["request_id"])

            offer = db.execute(
                text("SELECT request_id, contractor_id, [status], expiry_time "
                     "FROM ContractorConcreteRequests WHERE request_id = :oid"),
                {"oid": offer_id},
            ).mappings().first()
            if offer is None:
                raise HTTPException(status_code=404, detail="הפנייה לא נמצאה")

            # תפוגה עצלה (OD-11): אם הפנייה פגה — סמן EXPIRED (+ ההתאמות שלה) והחזר 410
            expiry = offer["expiry_time"]
            if expiry is not None and expiry <= _now_naive_utc():
                db.execute(
                    text("UPDATE ContractorConcreteRequests SET [status]='EXPIRED' "
                         "WHERE request_id=:oid AND [status]='OPEN'"),
                    {"oid": offer_id},
                )
                db.execute(
                    text("UPDATE OfferMatches SET [status]='EXPIRED' "
                         "WHERE offer_id=:oid AND [status]='NOTIFIED'"),
                    {"oid": offer_id},
                )
                db.commit()
                raise HTTPException(status_code=410, detail="ההצעה פגה")

            if (offer["status"] or "").upper() != "OPEN":
                raise HTTPException(status_code=409, detail="ההצעה כבר נתפסה")

            # ==== שער אטומי (first-wins) — כאן מוכרע המרוץ ====
            gate = db.execute(
                text("UPDATE ContractorConcreteRequests "
                     "SET [status]='CLOSED', id_customer=:rid "
                     "WHERE request_id=:oid AND [status]='OPEN'"),
                {"rid": request_id, "oid": offer_id},
            )
            if gate.rowcount == 0:
                db.rollback()
                raise HTTPException(status_code=409, detail="ההצעה כבר נתפסה")

            # סגירת הבקשה של הלקוח המאשר
            db.execute(
                text("UPDATE ConcreteRequests SET [status]='CLOSED' WHERE request_id=:rid"),
                {"rid": request_id},
            )

            # ההתאמה הזו -> ACCEPTED
            db.execute(
                text("UPDATE OfferMatches SET [status]='ACCEPTED', responded_at=SYSDATETIME() "
                     "WHERE id=:mid"),
                {"mid": match_id},
            )

            # איסוף שאר המותאמים של אותה פנייה (להתראת "נתפסה") ואז SUPERSEDED
            others = db.execute(
                text("SELECT id, customer_id, request_id FROM OfferMatches "
                     "WHERE offer_id=:oid AND id<>:mid AND [status]='NOTIFIED'"),
                {"oid": offer_id, "mid": match_id},
            ).mappings().all()
            db.execute(
                text("UPDATE OfferMatches SET [status]='SUPERSEDED' "
                     "WHERE offer_id=:oid AND id<>:mid AND [status]='NOTIFIED'"),
                {"oid": offer_id, "mid": match_id},
            )

            # שאר ההתאמות הפעילות של אותה בקשה (בחרה פנייה אחרת) -> SUPERSEDED
            db.execute(
                text("UPDATE OfferMatches SET [status]='SUPERSEDED' "
                     "WHERE request_id=:rid AND id<>:mid AND [status]='NOTIFIED'"),
                {"rid": request_id, "mid": match_id},
            )

            # פרטי קשר
            customer_phone = db.execute(
                text("SELECT phone FROM Customers WHERE id=:cid"), {"cid": customer_id}
            ).scalar()
            contractor = db.execute(
                text("SELECT first_name, last_name, phone FROM Contractors WHERE id=:cid"),
                {"cid": offer["contractor_id"]},
            ).mappings().first()

            # התראות (באותה טרנזקציה)
            self.notifier.notify_customer_accepted_to_contractor(
                contractor_id=int(offer["contractor_id"]),
                offer_id=offer_id, request_id=request_id, customer_phone=customer_phone,
            )
            for row in others:
                oc = safe_int(row["customer_id"])
                if oc is not None:
                    self.notifier.notify_offer_taken_to_customer(oc, offer_id, safe_int(row["request_id"]))

            db.commit()

            contact_name = None
            contact_phone = None
            if contractor:
                contact_name = (
                    " ".join(p for p in [contractor.get("first_name"), contractor.get("last_name")] if p)
                    or None
                )
                contact_phone = contractor.get("phone")

            return {
                "match_id": match_id,
                "offer_id": offer_id,
                "request_id": request_id,
                "match_status": "ACCEPTED",
                "offer_status": "CLOSED",
                "request_status": "CLOSED",
                "contact_name": contact_name,
                "contact_phone": contact_phone,
                "message": "אישרת את הפנייה! פרטי הקבלן ליצירת קשר מוצגים כעת.",
            }
        except HTTPException:
            db.rollback()
            raise
        except Exception:
            db.rollback()
            raise

    # -------------------------------------------------------------------
    # דחיית התאמה — לא נוגעת בפנייה
    # -------------------------------------------------------------------
    def decline_match(self, match_id: int, customer_id: int) -> dict:
        db = self.db
        try:
            match = db.execute(
                text("SELECT id, offer_id, request_id, customer_id, [status] "
                     "FROM OfferMatches WHERE id = :mid"),
                {"mid": match_id},
            ).mappings().first()
            if match is None:
                raise HTTPException(status_code=404, detail="התאמה לא נמצאה")
            if safe_int(match["customer_id"]) != int(customer_id):
                raise HTTPException(status_code=403, detail="אין הרשאה לדחות התאמה זו")
            if (match["status"] or "").upper() != "NOTIFIED":
                raise HTTPException(status_code=409, detail="לא ניתן לדחות התאמה שאינה פעילה")

            db.execute(
                text("UPDATE OfferMatches SET [status]='DECLINED', responded_at=SYSDATETIME() "
                     "WHERE id=:mid"),
                {"mid": match_id},
            )
            db.commit()
            return {
                "match_id": match_id,
                "offer_id": int(match["offer_id"]),
                "request_id": int(match["request_id"]),
                "match_status": "DECLINED",
                "offer_status": None,
                "request_status": None,
                "contact_name": None,
                "contact_phone": None,
                "message": "דחית את הפנייה.",
            }
        except HTTPException:
            db.rollback()
            raise
        except Exception:
            db.rollback()
            raise
