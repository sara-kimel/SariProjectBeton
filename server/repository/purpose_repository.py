"""
Repository למטרה / קטגוריה (Purpose) - טבלת lookup
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from models.purpose import Purpose
from dto.purpose_dto import PurposeCreateDTO, PurposeMappingDTO


class PurposeRepository:
    """מחלקת גישה לנתוני מטרות / קטגוריות"""

    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[Purpose]:
        """שליפת כל המטרות"""
        return self.db.query(Purpose).all()

    def get_by_id(self, purpose_id: int) -> Optional[Purpose]:
        """שליפת מטרה לפי מזהה"""
        return self.db.query(Purpose).filter(Purpose.id == purpose_id).first()

    def create(self, data: PurposeCreateDTO) -> Purpose:
        """יצירת מטרה חדשה (כולל מיפוי req_* אם סופק)"""
        new_item = Purpose(
            Purpose=data.Purpose,
            req_strength_id=data.req_strength_id,
            req_reliant_id=data.req_reliant_id,
            req_stone_size_id=data.req_stone_size_id,
        )
        self.db.add(new_item)
        self.db.commit()
        self.db.refresh(new_item)
        return new_item

    def update(self, purpose_id: int, data: PurposeCreateDTO) -> Optional[Purpose]:
        """עדכון מטרה — מעדכן רק שדות שנשלחו במפורש (כולל אפשרות לנקות מיפוי ל-None)"""
        existing = self.get_by_id(purpose_id)
        if not existing:
            return None
        fields = data.model_fields_set
        if "Purpose" in fields:
            existing.Purpose = data.Purpose
        if "req_strength_id" in fields:
            existing.req_strength_id = data.req_strength_id
        if "req_reliant_id" in fields:
            existing.req_reliant_id = data.req_reliant_id
        if "req_stone_size_id" in fields:
            existing.req_stone_size_id = data.req_stone_size_id
        self.db.commit()
        self.db.refresh(existing)
        return existing

    def update_mapping(self, purpose_id: int, mapping: PurposeMappingDTO) -> Optional[Purpose]:
        """עדכון ייעודי של מיפוי מטרה->מפרט (מזין את סינון OD-2 במנוע)."""
        existing = self.get_by_id(purpose_id)
        if not existing:
            return None
        existing.req_strength_id = mapping.req_strength_id
        existing.req_reliant_id = mapping.req_reliant_id
        existing.req_stone_size_id = mapping.req_stone_size_id
        self.db.commit()
        self.db.refresh(existing)
        return existing

    def delete(self, purpose_id: int) -> bool:
        """מחיקת מטרה"""
        existing = self.get_by_id(purpose_id)
        if not existing:
            return False
        self.db.delete(existing)
        self.db.commit()
        return True
