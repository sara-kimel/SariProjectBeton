"""
Repository למנהלים (Admin) — שלב 1.
"""

from typing import Optional
from sqlalchemy.orm import Session
from models.admin import Admin


class AdminRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, admin_id: int) -> Optional[Admin]:
        return self.db.query(Admin).filter(Admin.id == admin_id).first()

    def get_by_username(self, user_name: str) -> Optional[Admin]:
        return self.db.query(Admin).filter(Admin.user_name == user_name).first()

    def create(self, user_name, password_hash, first_name=None, last_name=None) -> Admin:
        new_admin = Admin(
            user_name=user_name,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
        )
        self.db.add(new_admin)
        self.db.commit()
        self.db.refresh(new_admin)
        return new_admin

    def set_password_hash(self, admin: Admin, password_hash: str) -> Admin:
        admin.password_hash = password_hash
        self.db.commit()
        self.db.refresh(admin)
        return admin
