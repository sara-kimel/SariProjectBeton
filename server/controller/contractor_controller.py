"""
Controller לקבלנים (Contractor)
מגדיר את ה-endpoints לפעולות CRUD על קבלנים
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from dto.contractor_dto import ContractorCreateDTO, ContractorResponseDTO
from repository.contractor_repository import ContractorRepository
from service.security import get_current_user


# ראוטר לכל ה-endpoints של קבלנים — שלב 1: דורש משתמש מחובר.
router = APIRouter(
    prefix="/contractors",
    tags=["Contractors"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/", response_model=List[ContractorResponseDTO])
def get_all_contractors(db: Session = Depends(get_db)):
    """שליפת כל הקבלנים - GET /contractors/"""
    return ContractorRepository(db).get_all()


@router.get("/{contractor_id}", response_model=ContractorResponseDTO)
def get_contractor(contractor_id: int, db: Session = Depends(get_db)):
    """שליפת קבלן לפי מזהה - GET /contractors/{contractor_id}"""
    contractor = ContractorRepository(db).get_by_id(contractor_id)
    if not contractor:
        raise HTTPException(status_code=404, detail=f"קבלן {contractor_id} לא נמצא")
    return contractor


@router.post("/", response_model=ContractorResponseDTO, status_code=201)
def create_contractor(contractor: ContractorCreateDTO, db: Session = Depends(get_db)):
    """יצירת קבלן חדש - POST /contractors/"""
    return ContractorRepository(db).create(contractor)


@router.put("/{contractor_id}", response_model=ContractorResponseDTO)
def update_contractor(
    contractor_id: int,
    contractor: ContractorCreateDTO,
    db: Session = Depends(get_db)
):
    """עדכון קבלן - PUT /contractors/{contractor_id}"""
    updated = ContractorRepository(db).update(contractor_id, contractor)
    if not updated:
        raise HTTPException(status_code=404, detail=f"קבלן {contractor_id} לא נמצא")
    return updated


@router.delete("/{contractor_id}", status_code=204)
def delete_contractor(contractor_id: int, db: Session = Depends(get_db)):
    """מחיקת קבלן - DELETE /contractors/{contractor_id}"""
    if not ContractorRepository(db).delete(contractor_id):
        raise HTTPException(status_code=404, detail=f"קבלן {contractor_id} לא נמצא")
    return None
