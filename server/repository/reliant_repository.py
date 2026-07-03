"""
Repository לסומך (Reliant) - טבלת lookup
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from models.reliant import Reliant
from dto.reliant_dto import ReliantCreateDTO


class ReliantRepository:
    """מחלקת גישה לנתוני סומך"""

    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[Reliant]:
        """שליפת כל סוגי הסומך"""
        return self.db.query(Reliant).all()

    def get_by_id(self, reliant_id: int) -> Optional[Reliant]:
        """שליפת סומך לפי מזהה"""
        return self.db.query(Reliant).filter(Reliant.id == reliant_id).first()

    def create(self, data: ReliantCreateDTO) -> Reliant:
        """יצירת רשומת סומך חדשה"""
        new_item = Reliant(Reliant=data.Reliant)
        self.db.add(new_item)
        self.db.commit()
        self.db.refresh(new_item)
        return new_item

    def update(self, reliant_id: int, data: ReliantCreateDTO) -> Optional[Reliant]:
        """עדכון רשומת סומך"""
        existing = self.get_by_id(reliant_id)
        if not existing:
            return None
        if data.Reliant is not None:
            existing.Reliant = data.Reliant
        self.db.commit()
        self.db.refresh(existing)
        return existing

    def delete(self, reliant_id: int) -> bool:
        """מחיקת רשומת סומך"""
        existing = self.get_by_id(reliant_id)
        if not existing:
            return False
        self.db.delete(existing)
        self.db.commit()
        return True
