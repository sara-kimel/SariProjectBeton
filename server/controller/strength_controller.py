"""
Controller לחוזק בטון (Strength)
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from dto.strength_dto import StrengthCreateDTO, StrengthResponseDTO
from repository.strength_repository import StrengthRepository
from service.security import get_current_admin
from service.lookup_guard import guarded_delete


router = APIRouter(prefix="/strengths", tags=["Strength"])


@router.get("/", response_model=List[StrengthResponseDTO])
def get_all(db: Session = Depends(get_db)):
    """שליפת כל סוגי החוזק (ציבורי — לטפסים)"""
    return StrengthRepository(db).get_all()


@router.get("/{strength_id}", response_model=StrengthResponseDTO)
def get_one(strength_id: int, db: Session = Depends(get_db)):
    """שליפת חוזק לפי מזהה"""
    item = StrengthRepository(db).get_by_id(strength_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"חוזק {strength_id} לא נמצא")
    return item


@router.post("/", response_model=StrengthResponseDTO, status_code=201)
def create(data: StrengthCreateDTO, _admin=Depends(get_current_admin), db: Session = Depends(get_db)):
    """יצירת רשומת חוזק חדשה (מנהל בלבד)"""
    return StrengthRepository(db).create(data)


@router.put("/{strength_id}", response_model=StrengthResponseDTO)
def update(
    strength_id: int, data: StrengthCreateDTO,
    _admin=Depends(get_current_admin), db: Session = Depends(get_db),
):
    """עדכון רשומת חוזק (כולל sort_order; מנהל בלבד)"""
    updated = StrengthRepository(db).update(strength_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail=f"חוזק {strength_id} לא נמצא")
    return updated


@router.delete("/{strength_id}", status_code=204)
def delete(strength_id: int, _admin=Depends(get_current_admin), db: Session = Depends(get_db)):
    """מחיקת רשומת חוזק (מנהל בלבד; חסום אם בשימוש → 409)"""
    return guarded_delete(db, StrengthRepository(db), strength_id, f"חוזק {strength_id} לא נמצא")
