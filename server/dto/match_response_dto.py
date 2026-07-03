"""
DTOs להתאמות (OfferMatches) — שלב 3.

- MatchViewDTO: תצוגה מועשרת של התאמה (רשומת ההתאמה + צד הבקשה + צד הפנייה),
  משמשת גם לנקודות הצפייה (/matches/...) וגם ברשימת התוצאות של /send/.
- OfferSendResultDTO: הסיכום שמוחזר לקבלן לאחר הרצת המנוע ב-/send/.
"""

from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime, date as DateType
from decimal import Decimal


class MatchViewDTO(BaseModel):
    """תצוגת התאמה מועשרת (התאמה + פרטי בקשה + פרטי פנייה)."""

    model_config = ConfigDict(from_attributes=True)

    # ליבת ההתאמה
    id: int
    offer_id: int
    request_id: int
    customer_id: Optional[int] = None
    score: Optional[float] = None
    distance_m: Optional[float] = None
    status: str
    created_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None

    # צד הבקשה (לקוח)
    request_quantity: Optional[Decimal] = None
    request_address: Optional[str] = None
    request_purpose_id: Optional[int] = None
    request_date: Optional[DateType] = None
    request_status: Optional[str] = None

    # צד הפנייה (קבלן)
    offer_quantity: Optional[Decimal] = None
    offer_price: Optional[str] = None
    offer_address: Optional[str] = None
    offer_expiry_time: Optional[datetime] = None
    offer_status: Optional[str] = None
    contractor_id: Optional[int] = None

    # פרטי קשר — נחשפים רק לאחר סגירת העסקה (status=ACCEPTED); אחרת מוסתרים (SPEC §17.1)
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    contractor_name: Optional[str] = None
    contractor_phone: Optional[str] = None


class OfferSendResultDTO(BaseModel):
    """סיכום להרצת המנוע ב-/send/: הפנייה שנשמרה + הלקוחות שהותאמו (מדורג)."""

    model_config = ConfigDict(from_attributes=True)

    offer_id: int
    matched_count: int
    matches: List[MatchViewDTO] = []


class DealResultDTO(BaseModel):
    """תוצאת אישור/דחיית עסקה (שלב 4). ב-accept נחשפים פרטי הקשר של הצד השני."""

    model_config = ConfigDict(from_attributes=True)

    match_id: int
    offer_id: int
    request_id: int
    match_status: str
    offer_status: Optional[str] = None
    request_status: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    message: str
