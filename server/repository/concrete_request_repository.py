"""
Repository לבקשות בטון של לקוחות (ConcreteRequest)
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from models.concrete_request import ConcreteRequest
from dto.concrete_request_dto import ConcreteRequestCreateDTO


class ConcreteRequestRepository:
    """מחלקת גישה לנתוני בקשות בטון של לקוחות"""

    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[ConcreteRequest]:
        """שליפת כל בקשות הלקוחות"""
        return self.db.query(ConcreteRequest).all()

    def get_by_id(self, request_id: int) -> Optional[ConcreteRequest]:
        """שליפת בקשה לפי מזהה"""
        return self.db.query(ConcreteRequest).filter(
            ConcreteRequest.request_id == request_id
        ).first()

    def get_by_customer(self, customer_id: int) -> List[ConcreteRequest]:
        """שליפת כל הבקשות של לקוח מסויים"""
        return self.db.query(ConcreteRequest).filter(
            ConcreteRequest.customer_id == customer_id
        ).all()



    def create_for_customer(self, customer_id: int, data: ConcreteRequestCreateDTO) -> ConcreteRequest:
        """
        יצירת בקשה עבור לקוח מחובר (שלב 2).
        customer_id ו-status נקבעים ע"י השרת (מתעלמים מהגוף) — מניעת IDOR.
        """
        new_request = ConcreteRequest(
            customer_id=customer_id,
            purpose_id=data.purpose_id,
            quantity=data.quantity,
            address=data.address,
            lat=data.lat,
            lng=data.lng,
            status="OPEN",
        )
        self.db.add(new_request)
        self.db.commit()
        self.db.refresh(new_request)
        return new_request

    def create(self, data: ConcreteRequestCreateDTO) -> ConcreteRequest:
        """יצירת בקשת בטון חדשה"""
        # יצירת אובייקט מהנתונים שב-DTO
        new_request = ConcreteRequest(
            customer_id=data.customer_id,
            purpose_id=data.purpose_id,
            quantity=data.quantity,
            address=data.address,
            lat=data.lat,
            lng=data.lng,
            # הסטטוס עקבי כעת (NOT NULL); בקשה חדשה נכנסת כ-OPEN אלא אם צוין אחרת
            status=(data.status or "OPEN"),
        )
        self.db.add(new_request)
        self.db.commit()
        self.db.refresh(new_request)
        return new_request

    def update(self, request_id: int, data: ConcreteRequestCreateDTO) -> Optional[ConcreteRequest]:
        """עדכון בקשה קיימת"""
        existing = self.get_by_id(request_id)
        if not existing:
            return None

        # עדכון של כל שדה שלא None ב-DTO
        if data.customer_id is not None:
            existing.customer_id = data.customer_id
        if data.purpose_id is not None:
            existing.purpose_id = data.purpose_id
        if data.quantity is not None:
            existing.quantity = data.quantity
        if data.address is not None:
            existing.address = data.address
        if data.lat is not None:
            existing.lat = data.lat
        if data.lng is not None:
            existing.lng = data.lng
        if data.status is not None:
            existing.status = data.status


        self.db.commit()
        self.db.refresh(existing)
        return existing

    def delete(self, request_id: int) -> bool:
        """מחיקת בקשה"""
        existing = self.get_by_id(request_id)
        if not existing:
            return False
        self.db.delete(existing)
        self.db.commit()
        return True
