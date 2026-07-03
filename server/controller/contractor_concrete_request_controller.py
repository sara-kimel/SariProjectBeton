"""
Controller לפניות של קבלנים (ContractorConcreteRequest).
POST /       — שמירה בלבד (contractor_id של המשתמש המחובר, status='OPEN',
               מחיר כפי שהוזן ללא הכפלה — SPEC §14, expiry_time עתידי).
POST /send/  — שלב 3: שומר פנייה + מריץ מנוע ההתאמה + יוצר OfferMatches (NOTIFIED)
               בטרנזקציה אחת, ומחזיר סיכום מדורג של הלקוחות שהותאמו.
החלטה (OD/§8.3): "/" שומר בלבד; "/send/" שומר+מתאים. לקוח יוצר פנייה דרך /send/
כדי לקבל מיד את המותאמים; העריכה הפשוטה (PUT) והשמירה ללא מנוע נשארות ב-"/".
"""

from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from dto.contractor_concrete_request_dto import (
    ContractorConcreteRequestCreateDTO,
    ContractorConcreteRequestResponseDTO,
)
from dto.match_response_dto import OfferSendResultDTO
from repository.contractor_concrete_request_repository import ContractorConcreteRequestRepository
from repository.concrete_type_repository import ConcreteTypeRepository
from service.match_service import MatchService
from service.expiry_service import expire_stale_offers
from service.security import get_current_user

router = APIRouter(
    prefix="/contractor-offers",
    tags=["Contractor Offers"],
    dependencies=[Depends(get_current_user)],
)


def _owns_or_admin(current: dict, contractor_id) -> bool:
    if current["role"] == "admin":
        return True
    return current["role"] == "contractor" and current["id"] == contractor_id


def _is_open(offer) -> bool:
    return (offer.status or "OPEN").strip().upper() == "OPEN"


def _is_future(dt: datetime) -> bool:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt > datetime.now(timezone.utc)


def _naive_utc(dt: datetime) -> datetime:
    """המרה ל-datetime נאיבי ב-UTC לאחסון בעמודת DATETIME (ללא אזור זמן)."""
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def _validate_offer_payload(data: ContractorConcreteRequestCreateDTO, db: Session) -> None:
    """ולידציית פנייה משותפת ל-POST / ול-POST /send/. מנרמל expiry ל-UTC נאיבי."""
    if data.quantity is None or float(data.quantity) <= 0:
        raise HTTPException(status_code=422, detail="כמות הבטון חייבת להיות גדולה מ-0")
    if data.lat is None or data.lng is None:
        raise HTTPException(status_code=422, detail="חובה לבחור מיקום על המפה")
    if data.concrete_id is None or ConcreteTypeRepository(db).get_by_id(data.concrete_id) is None:
        raise HTTPException(status_code=422, detail="סוג הבטון שנבחר אינו קיים")
    if data.expiry_time is None:
        raise HTTPException(status_code=422, detail="יש להזין זמן תפוגה")
    if not _is_future(data.expiry_time):
        raise HTTPException(status_code=422, detail="זמן התפוגה חייב להיות עתידי")
    data.expiry_time = _naive_utc(data.expiry_time)


@router.get("/", response_model=List[ContractorConcreteRequestResponseDTO])
def get_all_offers(current: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """כל הפניות — מנהל בלבד."""
    if current["role"] != "admin":
        raise HTTPException(status_code=403, detail="אין הרשאה")
    expire_stale_offers(db)  # תפוגה עצלה (OD-11)
    return ContractorConcreteRequestRepository(db).get_all()


@router.get("/contractor/{contractor_id}", response_model=List[ContractorConcreteRequestResponseDTO])
def get_offers_by_contractor(
    contractor_id: int,
    current: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """הפניות של קבלן מסוים — לבעלים או למנהל בלבד."""
    if not _owns_or_admin(current, contractor_id):
        raise HTTPException(status_code=403, detail="אין הרשאה לצפות בפניות של קבלן אחר")
    expire_stale_offers(db)  # תפוגה עצלה (OD-11)
    return ContractorConcreteRequestRepository(db).get_by_contractor(contractor_id)


@router.get("/{request_id}", response_model=ContractorConcreteRequestResponseDTO)
def get_offer(
    request_id: int,
    current: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repo = ContractorConcreteRequestRepository(db)
    offer = repo.get_by_id(request_id)
    if not offer:
        raise HTTPException(status_code=404, detail=f"פנייה {request_id} לא נמצאה")
    if not _owns_or_admin(current, offer.contractor_id):
        raise HTTPException(status_code=403, detail="אין הרשאה לצפות בפנייה זו")
    # תפוגה עצלה (OD-11): אם הפנייה פגה — מסמנים ומחזירים את המצב המעודכן
    expire_stale_offers(db)
    return repo.get_by_id(request_id)


@router.post("/", response_model=ContractorConcreteRequestResponseDTO, status_code=201)
def create_offer(
    data: ContractorConcreteRequestCreateDTO,
    current: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    יצירת פנייה חדשה (שמירה בלבד — המנוע לא רץ בשלב 2).
    contractor_id נלקח מהמשתמש המחובר; status='OPEN'.
    """
    if current["role"] != "contractor":
        raise HTTPException(status_code=403, detail="רק קבלן יכול לפתוח פנייה")

    _validate_offer_payload(data, db)
    return ContractorConcreteRequestRepository(db).create_for_contractor(current["id"], data)


@router.put("/{request_id}", response_model=ContractorConcreteRequestResponseDTO)
def update_offer(
    request_id: int,
    data: ContractorConcreteRequestCreateDTO,
    current: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repo = ContractorConcreteRequestRepository(db)
    offer = repo.get_by_id(request_id)
    if not offer:
        raise HTTPException(status_code=404, detail=f"פנייה {request_id} לא נמצאה")
    if not _owns_or_admin(current, offer.contractor_id):
        raise HTTPException(status_code=403, detail="אין הרשאה לערוך פנייה זו")
    if not _is_open(offer):
        raise HTTPException(status_code=409, detail="לא ניתן לערוך פנייה שאינה פתוחה")
    if data.expiry_time is not None:
        if not _is_future(data.expiry_time):
            raise HTTPException(status_code=422, detail="זמן התפוגה חייב להיות עתידי")
        data.expiry_time = _naive_utc(data.expiry_time)
    return repo.update(request_id, data)


@router.delete("/{request_id}", status_code=204)
def delete_offer(
    request_id: int,
    current: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repo = ContractorConcreteRequestRepository(db)
    offer = repo.get_by_id(request_id)
    if not offer:
        raise HTTPException(status_code=404, detail=f"פנייה {request_id} לא נמצאה")
    if not _owns_or_admin(current, offer.contractor_id):
        raise HTTPException(status_code=403, detail="אין הרשאה למחוק פנייה זו")
    if not _is_open(offer):
        raise HTTPException(status_code=409, detail="לא ניתן למחוק פנייה שאינה פתוחה")
    repo.delete(request_id)
    return None


@router.post("/send/", response_model=OfferSendResultDTO)
def send_offer(
    data: ContractorConcreteRequestCreateDTO,
    current: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    שלב 3 — שומר את הפנייה (status=OPEN), מריץ את מנוע ההתאמה קדימה,
    יוצר רשומות OfferMatches (NOTIFIED) לכל לקוח שהותאם — הכול בטרנזקציה אחת —
    ומחזיר סיכום מדורג {offer_id, matched_count, matches}.
    """
    if current["role"] != "contractor":
        raise HTTPException(status_code=403, detail="רק קבלן יכול להריץ התאמה")

    _validate_offer_payload(data, db)
    return MatchService(db).create_offer_and_match(current["id"], data)
