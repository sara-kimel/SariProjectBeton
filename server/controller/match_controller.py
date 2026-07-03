"""
Controller להתאמות (OfferMatches) — שלבים 3–4.
- GET  /matches/offer/{offer_id}     — ההתאמות של פניה (לבעלים הקבלן או למנהל).
- GET  /matches/request/{request_id} — ההתאמות של בקשה (לבעלים הלקוח או למנהל).
- POST /matches/{id}/accept          — לקוח מאשר פניה (אטומי — הראשון זוכה).
- POST /matches/{id}/decline         — לקוח דוחה התאמה.
פרטי קשר (טלפון/שם) נחשפים רק לאחר סגירת העסקה (status=ACCEPTED, SPEC §17.1).
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from dto.match_response_dto import MatchViewDTO, DealResultDTO
from repository.offer_match_repository import OfferMatchRepository
from repository.contractor_concrete_request_repository import ContractorConcreteRequestRepository
from repository.concrete_request_repository import ConcreteRequestRepository
from service.deal_service import DealService
from service.security import get_current_user

router = APIRouter(
    prefix="/matches",
    tags=["Matches"],
    dependencies=[Depends(get_current_user)],
)

# שדות קשר שנחשפים רק כשההתאמה ACCEPTED
_CONTACT_FIELDS = ("customer_name", "customer_phone", "contractor_name", "contractor_phone")


def _owns_or_admin(current: dict, role: str, owner_id) -> bool:
    if current["role"] == "admin":
        return True
    return current["role"] == role and current["id"] == owner_id


def _redact_contacts(rows: List[dict]) -> List[dict]:
    """מסתיר פרטי קשר בכל התאמה שאינה סגורה (ACCEPTED) — לפני החשיפה אין ליצור קשר."""
    for r in rows:
        if (r.get("status") or "").upper() != "ACCEPTED":
            for f in _CONTACT_FIELDS:
                r[f] = None
    return rows


@router.get("/offer/{offer_id}", response_model=List[MatchViewDTO])
def get_matches_for_offer(
    offer_id: int,
    current: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """ההתאמות של פניה — לקבלן הבעלים או למנהל בלבד."""
    offer = ContractorConcreteRequestRepository(db).get_by_id(offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail=f"פניה {offer_id} לא נמצאה")
    if not _owns_or_admin(current, "contractor", offer.contractor_id):
        raise HTTPException(status_code=403, detail="אין הרשאה לצפות בהתאמות של פניה זו")
    return _redact_contacts(OfferMatchRepository(db).get_view_for_offer(offer_id))


@router.get("/request/{request_id}", response_model=List[MatchViewDTO])
def get_matches_for_request(
    request_id: int,
    current: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """ההתאמות של בקשה — ללקוח הבעלים או למנהל בלבד."""
    req = ConcreteRequestRepository(db).get_by_id(request_id)
    if not req:
        raise HTTPException(status_code=404, detail=f"בקשה {request_id} לא נמצאה")
    if not _owns_or_admin(current, "customer", req.customer_id):
        raise HTTPException(status_code=403, detail="אין הרשאה לצפות בהתאמות של בקשה זו")
    return _redact_contacts(OfferMatchRepository(db).get_view_for_request(request_id))


@router.post("/{match_id}/accept", response_model=DealResultDTO)
def accept_match(
    match_id: int,
    current: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """לקוח מאשר פניה — אטומי, הראשון זוכה (OD-5). מחזיר את פרטי הקבלן ליצירת קשר."""
    if current["role"] != "customer":
        raise HTTPException(status_code=403, detail="רק לקוח יכול לאשר פניה")
    return DealService(db).accept_match(match_id, current["id"])


@router.post("/{match_id}/decline", response_model=DealResultDTO)
def decline_match(
    match_id: int,
    current: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """לקוח דוחה התאמה (אינה משנה את הפניה)."""
    if current["role"] != "customer":
        raise HTTPException(status_code=403, detail="רק לקוח יכול לדחות התאמה")
    return DealService(db).decline_match(match_id, current["id"])
