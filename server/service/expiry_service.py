"""
תפוגה עצלה (Lazy Expiry, OD-11) — שלב 5, מרוכז במקום אחד.
פנייה שעבר `expiry_time` שלה ועדיין OPEN מסומנת EXPIRED, וכל ההתאמות שלה
שב-NOTIFIED מסומנות EXPIRED — בזמן שנוגעים בפניות (GET / הרצת מנוע).
אין job רקע ואין התראת תפוגה יזומה (הוכרע, SPEC §11/§6.2).

זהו הנתיב היחיד לסימון תפוגה — לקרוא לו מכל מקום שקורא/מתאים פניות.
"""

from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session


def _now_naive_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def expire_stale_offers(db: Session) -> int:
    """
    מסמן EXPIRED את כל הפניות שפגו ועדיין OPEN (וההתאמות NOTIFIED שלהן).
    מבצע commit. מחזיר את מספר הפניות שסומנו.
    """
    now = _now_naive_utc()

    # קודם ההתאמות (בעוד הפניות עדיין OPEN), ואז הפניות עצמן
    db.execute(
        text("""
            UPDATE OfferMatches SET [status]='EXPIRED'
            WHERE [status]='NOTIFIED' AND offer_id IN (
                SELECT request_id FROM ContractorConcreteRequests
                WHERE [status]='OPEN' AND expiry_time IS NOT NULL AND expiry_time <= :now
            )
        """),
        {"now": now},
    )
    res = db.execute(
        text("""
            UPDATE ContractorConcreteRequests SET [status]='EXPIRED'
            WHERE [status]='OPEN' AND expiry_time IS NOT NULL AND expiry_time <= :now
        """),
        {"now": now},
    )
    db.commit()
    return res.rowcount or 0
