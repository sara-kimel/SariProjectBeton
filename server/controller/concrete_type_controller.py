"""
Controller לסוג בטון (ConcreteType) - שילוב מאפיינים
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from dto.concrete_type_dto import ConcreteTypeCreateDTO, ConcreteTypeResponseDTO
from repository.concrete_type_repository import ConcreteTypeRepository
from service.security import get_current_admin
from service.lookup_guard import guarded_delete


router = APIRouter(prefix="/concrete-types", tags=["Concrete Type"])


@router.get("/", response_model=List[ConcreteTypeResponseDTO])
def get_all(db: Session = Depends(get_db)):
    """שליפת כל סוגי הבטון (ציבורי — לטפסים)"""
    return ConcreteTypeRepository(db).get_all()


@router.get("/{type_id}", response_model=ConcreteTypeResponseDTO)
def get_one(type_id: int, db: Session = Depends(get_db)):
    """שליפת סוג בטון לפי מזהה"""
    item = ConcreteTypeRepository(db).get_by_id(type_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"סוג בטון {type_id} לא נמצא")
    return item


@router.post("/", response_model=ConcreteTypeResponseDTO, status_code=201)
def create(data: ConcreteTypeCreateDTO, _admin=Depends(get_current_admin), db: Session = Depends(get_db)):
    """יצירת סוג בטון חדש (מנהל בלבד)"""
    return ConcreteTypeRepository(db).create(data)


@router.put("/{type_id}", response_model=ConcreteTypeResponseDTO)
def update(
    type_id: int, data: ConcreteTypeCreateDTO,
    _admin=Depends(get_current_admin), db: Session = Depends(get_db),
):
    """עדכון סוג בטון (מנהל בלבד)"""
    updated = ConcreteTypeRepository(db).update(type_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail=f"סוג בטון {type_id} לא נמצא")
    return updated


@router.delete("/{type_id}", status_code=204)
def delete(type_id: int, _admin=Depends(get_current_admin), db: Session = Depends(get_db)):
    """מחיקת סוג בטון (מנהל בלבד; חסום אם בשימוש → 409)"""
    return guarded_delete(db, ConcreteTypeRepository(db), type_id, f"סוג בטון {type_id} לא נמצא")
