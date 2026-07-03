"""
Repository לסוג בטון (ConcreteType) - שילוב מאפיינים
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from models.concrete_type import ConcreteType
from dto.concrete_type_dto import ConcreteTypeCreateDTO


class ConcreteTypeRepository:
    """מחלקת גישה לנתוני סוגי בטון"""

    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[ConcreteType]:
        """שליפת כל סוגי הבטון"""
        return self.db.query(ConcreteType).all()

    def get_by_id(self, type_id: int) -> Optional[ConcreteType]:
        """שליפת סוג בטון לפי מזהה"""
        return self.db.query(ConcreteType).filter(ConcreteType.id == type_id).first()

    def create(self, data: ConcreteTypeCreateDTO) -> ConcreteType:
        """יצירת סוג בטון חדש"""
        new_item = ConcreteType(
            strength_id=data.strength_id,
            Reliant_id=data.Reliant_id,
            Stone_size_id=data.Stone_size_id,
            Purpose_id=data.Purpose_id,
        )
        self.db.add(new_item)
        self.db.commit()
        self.db.refresh(new_item)
        return new_item

    def update(self, type_id: int, data: ConcreteTypeCreateDTO) -> Optional[ConcreteType]:
        """עדכון סוג בטון"""
        existing = self.get_by_id(type_id)
        if not existing:
            return None

        if data.strength_id is not None:
            existing.strength_id = data.strength_id
        if data.Reliant_id is not None:
            existing.Reliant_id = data.Reliant_id
        if data.Stone_size_id is not None:
            existing.Stone_size_id = data.Stone_size_id
        if data.Purpose_id is not None:
            existing.Purpose_id = data.Purpose_id

        self.db.commit()
        self.db.refresh(existing)
        return existing

    def delete(self, type_id: int) -> bool:
        """מחיקת סוג בטון"""
        existing = self.get_by_id(type_id)
        if not existing:
            return False
        self.db.delete(existing)
        self.db.commit()
        return True
