"""
Repository לגודל אבן (StoneSize) - טבלת lookup
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from models.stone_size import StoneSize
from dto.stone_size_dto import StoneSizeCreateDTO


class StoneSizeRepository:
    """מחלקת גישה לנתוני גודל אבן"""

    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[StoneSize]:
        """שליפת כל גדלי האבן"""
        return self.db.query(StoneSize).all()

    def get_by_id(self, stone_size_id: int) -> Optional[StoneSize]:
        """שליפת גודל אבן לפי מזהה"""
        return self.db.query(StoneSize).filter(StoneSize.id == stone_size_id).first()

    def create(self, data: StoneSizeCreateDTO) -> StoneSize:
        """יצירת רשומת גודל אבן חדשה"""
        new_item = StoneSize(Stone_size=data.Stone_size)
        self.db.add(new_item)
        self.db.commit()
        self.db.refresh(new_item)
        return new_item

    def update(self, stone_size_id: int, data: StoneSizeCreateDTO) -> Optional[StoneSize]:
        """עדכון רשומת גודל אבן"""
        existing = self.get_by_id(stone_size_id)
        if not existing:
            return None
        if data.Stone_size is not None:
            existing.Stone_size = data.Stone_size
        self.db.commit()
        self.db.refresh(existing)
        return existing

    def delete(self, stone_size_id: int) -> bool:
        """מחיקת רשומת גודל אבן"""
        existing = self.get_by_id(stone_size_id)
        if not existing:
            return False
        self.db.delete(existing)
        self.db.commit()
        return True
