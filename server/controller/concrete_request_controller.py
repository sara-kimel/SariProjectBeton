"""
Controller לבקשות בטון של לקוחות (ConcreteRequest) — שלב 2.
בעלות נאכפת: הבקשה שייכת ל-customer_id של המשתמש המחובר; רק בעלים/מנהל
צופים/עורכים. עריכה/מחיקה מותרות רק כשהבקשה OPEN.
המנוע אינו רץ כאן (שלב 3).
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from dto.concrete_request_dto import ConcreteRequestCreateDTO, ConcreteRequestResponseDTO
from repository.concrete_request_repository import ConcreteRequestRepository
from repository.purpose_repository import PurposeRepository
from service.match_service import MatchService
from service.security import get_current_user

router = APIRouter(
    prefix="/concrete-requests",
    tags=["Concrete Requests"],
    dependencies=[Depends(get_current_user)],
)


def _owns_or_admin(current: dict, customer_id) -> bool:
    if current["role"] == "admin":
        return True
    return current["role"] == "customer" and current["id"] == customer_id


def _is_open(req) -> bool:
    return (req.status or "OPEN").strip().upper() == "OPEN"


@router.get("/", response_model=List[ConcreteRequestResponseDTO])
def get_all_requests(current: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """כל הבקשות — מנהל בלבד."""
    if current["role"] != "admin":
        raise HTTPException(status_code=403, detail="אין הרשאה")
    return ConcreteRequestRepository(db).get_all()


@router.get("/customer/{customer_id}", response_model=List[ConcreteRequestResponseDTO])
def get_requests_by_customer(
    customer_id: int,
    current: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """הבקשות של לקוח מסוים — לבעלים או למנהל בלבד."""
    if not _owns_or_admin(current, customer_id):
        raise HTTPException(status_code=403, detail="אין הרשאה לצפות בבקשות של לקוח אחר")
    return ConcreteRequestRepository(db).get_by_customer(customer_id)


@router.get("/{request_id}", response_model=ConcreteRequestResponseDTO)
def get_request(
    request_id: int,
    current: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    req = ConcreteRequestRepository(db).get_by_id(request_id)
    if not req:
        raise HTTPException(status_code=404, detail=f"בקשה {request_id} לא נמצאה")
    if not _owns_or_admin(current, req.customer_id):
        raise HTTPException(status_code=403, detail="אין הרשאה לצפות בבקשה זו")
    return req


@router.post("/", response_model=ConcreteRequestResponseDTO, status_code=201)
def create_request(
    data: ConcreteRequestCreateDTO,
    current: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    יצירת בקשה. customer_id נלקח מהמשתמש המחובר; status='OPEN'.
    שלב 3 — טריגר הפוך (SPEC §5.6): לאחר השמירה רץ המנוע ההפוך, ונוצרות רשומות
    OfferMatches (NOTIFIED) לכל פנייה פתוחה ותואמת. ההתאמות נצפות ב-
    GET /matches/request/{id}. השמירה + ההתאמות בטרנזקציה אחת.
    """
    if current["role"] != "customer":
        raise HTTPException(status_code=403, detail="רק לקוח יכול לפתוח בקשה")

    if data.quantity is None or float(data.quantity) <= 0:
        raise HTTPException(status_code=422, detail="כמות הבטון חייבת להיות גדולה מ-0")
    if data.purpose_id is None:
        raise HTTPException(status_code=422, detail="יש לבחור מטרת שימוש")
    if PurposeRepository(db).get_by_id(data.purpose_id) is None:
        raise HTTPException(status_code=422, detail="מטרת השימוש שנבחרה אינה קיימת")

    return MatchService(db).create_request_and_match(current["id"], data)


@router.put("/{request_id}", response_model=ConcreteRequestResponseDTO)
def update_request(
    request_id: int,
    data: ConcreteRequestCreateDTO,
    current: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repo = ConcreteRequestRepository(db)
    req = repo.get_by_id(request_id)
    if not req:
        raise HTTPException(status_code=404, detail=f"בקשה {request_id} לא נמצאה")
    if not _owns_or_admin(current, req.customer_id):
        raise HTTPException(status_code=403, detail="אין הרשאה לערוך בקשה זו")
    if not _is_open(req):
        raise HTTPException(status_code=409, detail="לא ניתן לערוך בקשה שאינה פתוחה")
    return repo.update(request_id, data)


@router.delete("/{request_id}", status_code=204)
def delete_request(
    request_id: int,
    current: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repo = ConcreteRequestRepository(db)
    req = repo.get_by_id(request_id)
    if not req:
        raise HTTPException(status_code=404, detail=f"בקשה {request_id} לא נמצאה")
    if not _owns_or_admin(current, req.customer_id):
        raise HTTPException(status_code=403, detail="אין הרשאה למחוק בקשה זו")
    if not _is_open(req):
        raise HTTPException(status_code=409, detail="לא ניתן למחוק בקשה שאינה פתוחה")
    repo.delete(request_id)
    return None
