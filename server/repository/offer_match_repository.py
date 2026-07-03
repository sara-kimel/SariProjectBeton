"""
Repository להתאמות (OfferMatches) — שלב 3.

- create_notified: יוצר רשומת התאמה (status=NOTIFIED). מוסיף ל-session ומבצע
  flush בלבד (ללא commit) — כדי שהיוצר (שירות התזמור) יסגור את הטרנזקציה
  יחד עם שמירת הפנייה/הבקשה (אטומיות, ראה SPEC §5.4).
- exists: מונע כפילויות (UNIQUE(offer_id, request_id)) בין הטריגר הישיר להפוך.
- get_view_for_offer / get_view_for_request: שליפה מועשרת (JOIN) להצגה —
  התאמה + פרטי הבקשה + פרטי הפנייה, ממוינת לפי ניקוד יורד.
"""

from typing import List, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

from models.offer_match import OfferMatch


# שאילתת בסיס מועשרת: התאמה + צד-הבקשה (לקוח) + צד-הפנייה (קבלן).
_VIEW_SQL = """
    SELECT
        m.id, m.offer_id, m.request_id, m.customer_id,
        m.score, m.distance_m, m.status, m.created_at, m.responded_at,
        r.quantity   AS request_quantity,
        r.address    AS request_address,
        r.purpose_id AS request_purpose_id,
        r.[date]     AS request_date,
        r.[status]   AS request_status,
        o.quantity     AS offer_quantity,
        o.price        AS offer_price,
        o.address      AS offer_address,
        o.expiry_time  AS offer_expiry_time,
        o.[status]     AS offer_status,
        o.contractor_id AS contractor_id,
        -- פרטי קשר גולמיים; מוסתרים בשכבת ה-controller עד סגירת העסקה (status=ACCEPTED)
        LTRIM(RTRIM(CONCAT(cust.first_name, ' ', cust.last_name))) AS customer_name,
        cust.phone AS customer_phone,
        LTRIM(RTRIM(CONCAT(con.first_name, ' ', con.last_name)))   AS contractor_name,
        con.phone AS contractor_phone
    FROM dbo.OfferMatches m
    LEFT JOIN dbo.ConcreteRequests r           ON r.request_id = m.request_id
    LEFT JOIN dbo.ContractorConcreteRequests o ON o.request_id = m.offer_id
    LEFT JOIN dbo.Customers cust               ON cust.id = m.customer_id
    LEFT JOIN dbo.Contractors con              ON con.id = o.contractor_id
"""


class OfferMatchRepository:
    """מחלקת גישה לנתוני התאמות."""

    def __init__(self, db: Session):
        self.db = db

    def exists(self, offer_id: int, request_id: int) -> bool:
        """האם כבר קיימת התאמה לזוג (offer_id, request_id)."""
        return (
            self.db.query(OfferMatch)
            .filter(OfferMatch.offer_id == offer_id, OfferMatch.request_id == request_id)
            .first()
            is not None
        )

    def create_notified(
        self,
        offer_id: int,
        request_id: int,
        customer_id: Optional[int],
        score: Optional[float],
        distance_m: Optional[float],
    ) -> Optional[OfferMatch]:
        """
        יוצר רשומת התאמה חדשה במצב NOTIFIED (אם אינה קיימת כבר).
        מבצע flush בלבד — ה-commit באחריות שירות התזמור (אטומיות).
        """
        if self.exists(offer_id, request_id):
            return None
        match = OfferMatch(
            offer_id=offer_id,
            request_id=request_id,
            customer_id=customer_id,
            score=score,
            distance_m=distance_m,
            status="NOTIFIED",
        )
        self.db.add(match)
        self.db.flush()
        return match

    def get_view_for_offer(self, offer_id: int) -> List[dict]:
        """כל ההתאמות של פנייה (עבור הקבלן), ממוינות לפי ניקוד יורד."""
        rows = self.db.execute(
            text(_VIEW_SQL + " WHERE m.offer_id = :oid ORDER BY m.score DESC, m.created_at ASC"),
            {"oid": offer_id},
        )
        return [dict(r._mapping) for r in rows]

    def get_view_for_request(self, request_id: int) -> List[dict]:
        """כל ההתאמות של בקשה (עבור הלקוח), ממוינות לפי ניקוד יורד."""
        rows = self.db.execute(
            text(_VIEW_SQL + " WHERE m.request_id = :rid ORDER BY m.score DESC, m.created_at ASC"),
            {"rid": request_id},
        )
        return [dict(r._mapping) for r in rows]
