"""
Repository לחוזק בטון (Strength) - טבלת lookup
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from models.strength import Strength
from dto.strength_dto import StrengthCreateDTO


class StrengthRepository:
    """מחלקת גישה לנתוני חוזק בטון"""

    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[Strength]:
        """שליפת כל סוגי החוזק"""
        return self.db.query(Strength).all()

    def get_by_id(self, strength_id: int) -> Optional[Strength]:
        """שליפת חוזק לפי מזהה"""
        return self.db.query(Strength).filter(Strength.id == strength_id).first()

    def create(self, data: StrengthCreateDTO) -> Strength:
        """יצירת רשומת חוזק חדשה (כולל sort_order אם סופק)"""
        new_strength = Strength(strength=data.strength, sort_order=data.sort_order)
        self.db.add(new_strength)
        self.db.commit()
        self.db.refresh(new_strength)
        return new_strength

    def update(self, strength_id: int, data: StrengthCreateDTO) -> Optional[Strength]:
        """עדכון רשומת חוזק (שם ו/או sort_order — רק שדות שנשלחו)"""
        existing = self.get_by_id(strength_id)
        if not existing:
            return None
        fields = data.model_fields_set
        if "strength" in fields:
            existing.strength = data.strength
        if "sort_order" in fields:
            existing.sort_order = data.sort_order
        self.db.commit()
        self.db.refresh(existing)
        return existing

    def delete(self, strength_id: int) -> bool:
        """מחיקת רשומת חוזק"""
        existing = self.get_by_id(strength_id)
        if not existing:
            return False
        self.db.delete(existing)
        self.db.commit()
        return True
