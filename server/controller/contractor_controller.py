"""
Controller לקבלנים (Contractor)
מגדיר את ה-endpoints לפעולות CRUD על קבלנים.

הרשאות (FIX-1, SPEC §10/§13.5): רשימת-הכל ויצירה — מנהל בלבד;
צפייה/עדכון/מחיקה של קבלן בודד — לבעלים או למנהל בלבד (מניעת IDOR ודליפת מספרי טלפון).
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from dto.contractor_dto import ContractorCreateDTO, ContractorResponseDTO
from repository.contractor_repository import ContractorRepository
from service.security import get_current_user


# ראוטר לכל ה-endpoints של קבלנים — כולם דורשים משתמש מחובר.
router = APIRouter(
    prefix="/contractors",
    tags=["Contractors"],
    dependencies=[Depends(get_current_user)],
)


def _owns_or_admin(current: dict, contractor_id) -> bool:
    """בעלים (קבלן על עצמו) או מנהל בלבד."""
    if current["role"] == "admin":
        return True
    return current["role"] == "contractor" and current["id"] == contractor_id


@router.get("/", response_model=List[ContractorResponseDTO])
def get_all_contractors(
    current: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """שליפת כל הקבלנים — מנהל בלבד (מונע גרידת מספרי טלפון). GET /contractors/"""
    if current["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="אין הרשאה")
    return ContractorRepository(db).get_all()


@router.get("/{contractor_id}", response_model=ContractorResponseDTO)
def get_contractor(
    contractor_id: int,
    current: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """שליפת קבלן לפי מזהה — לבעלים או למנהל בלבד. GET /contractors/{contractor_id}"""
    if not _owns_or_admin(current, contractor_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="אין הרשאה לצפות בקבלן אחר")
    contractor = ContractorRepository(db).get_by_id(contractor_id)
    if not contractor:
        raise HTTPException(status_code=404, detail=f"קבלן {contractor_id} לא נמצא")
    return contractor


@router.post("/", response_model=ContractorResponseDTO, status_code=201)
def create_contractor(
    contractor: ContractorCreateDTO,
    current: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """יצירת קבלן חדש — מנהל בלבד (משתמשים נוצרים דרך /auth/register). POST /contractors/"""
    if current["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="נדרשת הרשאת מנהל")
    return ContractorRepository(db).create(contractor)


@router.put("/{contractor_id}", response_model=ContractorResponseDTO)
def update_contractor(
    contractor_id: int,
    contractor: ContractorCreateDTO,
    current: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """עדכון קבלן — לבעלים או למנהל בלבד. PUT /contractors/{contractor_id}"""
    if not _owns_or_admin(current, contractor_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="אין הרשאה לעדכן קבלן אחר")
    updated = ContractorRepository(db).update(contractor_id, contractor)
    if not updated:
        raise HTTPException(status_code=404, detail=f"קבלן {contractor_id} לא נמצא")
    return updated


@router.delete("/{contractor_id}", status_code=204)
def delete_contractor(
    contractor_id: int,
    current: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """מחיקת קבלן — לבעלים או למנהל בלבד. DELETE /contractors/{contractor_id}"""
    if not _owns_or_admin(current, contractor_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="אין הרשאה למחוק קבלן אחר")
    if not ContractorRepository(db).delete(contractor_id):
        raise HTTPException(status_code=404, detail=f"קבלן {contractor_id} לא נמצא")
    return None
