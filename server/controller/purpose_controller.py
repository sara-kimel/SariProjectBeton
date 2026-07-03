"""
Controller למטרה / קטגוריה (Purpose)
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from dto.purpose_dto import PurposeCreateDTO, PurposeResponseDTO, PurposeMappingDTO
from repository.purpose_repository import PurposeRepository
from service.security import get_current_admin
from service.lookup_guard import guarded_delete


router = APIRouter(prefix="/purposes", tags=["Purpose"])


@router.get("/", response_model=List[PurposeResponseDTO])
def get_all(db: Session = Depends(get_db)):
    """שליפת כל המטרות (ציבורי — לטפסים)"""
    return PurposeRepository(db).get_all()


@router.get("/{purpose_id}", response_model=PurposeResponseDTO)
def get_one(purpose_id: int, db: Session = Depends(get_db)):
    """שליפת מטרה לפי מזהה"""
    item = PurposeRepository(db).get_by_id(purpose_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"מטרה {purpose_id} לא נמצאה")
    return item


@router.post("/", response_model=PurposeResponseDTO, status_code=201)
def create(data: PurposeCreateDTO, _admin=Depends(get_current_admin), db: Session = Depends(get_db)):
    """יצירת מטרה חדשה (מנהל בלבד)"""
    return PurposeRepository(db).create(data)


@router.put("/{purpose_id}", response_model=PurposeResponseDTO)
def update(
    purpose_id: int, data: PurposeCreateDTO,
    _admin=Depends(get_current_admin), db: Session = Depends(get_db),
):
    """עדכון מטרה (מנהל בלבד)"""
    updated = PurposeRepository(db).update(purpose_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail=f"מטרה {purpose_id} לא נמצאה")
    return updated


@router.put("/{purpose_id}/mapping", response_model=PurposeResponseDTO)
def update_mapping(
    purpose_id: int, data: PurposeMappingDTO,
    _admin=Depends(get_current_admin), db: Session = Depends(get_db),
):
    """עדכון מיפוי מטרה->מפרט (חוזק/סומך/גודל-אבן) — מזין את סינון OD-2 במנוע. מנהל בלבד."""
    updated = PurposeRepository(db).update_mapping(purpose_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail=f"מטרה {purpose_id} לא נמצאה")
    return updated


@router.delete("/{purpose_id}", status_code=204)
def delete(purpose_id: int, _admin=Depends(get_current_admin), db: Session = Depends(get_db)):
    """מחיקת מטרה (מנהל בלבד; חסום אם בשימוש → 409)"""
    return guarded_delete(db, PurposeRepository(db), purpose_id, f"מטרה {purpose_id} לא נמצאה")
