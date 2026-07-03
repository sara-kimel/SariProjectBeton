"""
Repository לקבלנים (Contractor)
מטפל בכל הפעולות מול טבלת Contractors ב-DB
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from models.contractor import Contractor
from dto.contractor_dto import ContractorCreateDTO


class ContractorRepository:
    """מחלקת גישה לנתוני קבלנים"""

    def __init__(self, db: Session):
        # שמירת הסשן של DB לשימוש בפונקציות
        self.db = db

    def get_all(self) -> List[Contractor]:
        """שליפת כל הקבלנים"""
        return self.db.query(Contractor).all()

    def get_by_id(self, contractor_id: int) -> Optional[Contractor]:
        """שליפת קבלן לפי מזהה"""
        return self.db.query(Contractor).filter(Contractor.id == contractor_id).first()

    def get_by_username(self, user_name: str) -> Optional[Contractor]:
        """שליפת קבלן לפי שם משתמש (לאימות/הרשמה)."""
        return self.db.query(Contractor).filter(Contractor.user_name == user_name).first()

    def create_with_credentials(
        self, first_name, last_name, user_name, phone, password_hash
    ) -> Contractor:
        """יצירת קבלן עם סיסמה מוצפנת (זרימת /auth/register)."""
        new_contractor = Contractor(
            first_name=first_name,
            last_name=last_name,
            user_name=user_name,
            phone=phone,
            password_hash=password_hash,
        )
        self.db.add(new_contractor)
        self.db.commit()
        self.db.refresh(new_contractor)
        return new_contractor

    def set_password_hash(self, contractor: Contractor, password_hash: str) -> Contractor:
        """עדכון סיסמה מוצפנת (שינוי סיסמה / איפוס ע"י מנהל)."""
        contractor.password_hash = password_hash
        self.db.commit()
        self.db.refresh(contractor)
        return contractor

    def create(self, contractor_data: ContractorCreateDTO) -> Contractor:
        """יצירת קבלן חדש (פרופיל ללא אישורים)."""
        new_contractor = Contractor(
            first_name=contractor_data.first_name,
            last_name=contractor_data.last_name,
            user_name=contractor_data.user_name,
            phone=contractor_data.phone,
        )
        self.db.add(new_contractor)
        self.db.commit()
        self.db.refresh(new_contractor)
        return new_contractor

    def update(self, contractor_id: int, contractor_data: ContractorCreateDTO) -> Optional[Contractor]:
        """עדכון קבלן קיים"""
        existing = self.get_by_id(contractor_id)
        if not existing:
            return None

        if contractor_data.first_name is not None:
            existing.first_name = contractor_data.first_name
        if contractor_data.last_name is not None:
            existing.last_name = contractor_data.last_name
        if contractor_data.user_name is not None:
            existing.user_name = contractor_data.user_name
        if contractor_data.phone is not None:
            existing.phone = contractor_data.phone

        self.db.commit()
        self.db.refresh(existing)
        return existing

    def delete(self, contractor_id: int) -> bool:
        """מחיקת קבלן"""
        existing = self.get_by_id(contractor_id)
        if not existing:
            return False
        self.db.delete(existing)
        self.db.commit()
        return True
