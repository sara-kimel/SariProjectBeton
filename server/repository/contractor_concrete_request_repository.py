"""
Repository להצעות בטון של קבלנים (ContractorConcreteRequest)
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from models.contractor_concrete_request import ContractorConcreteRequest
from dto.contractor_concrete_request_dto import ContractorConcreteRequestCreateDTO


class ContractorConcreteRequestRepository:
    """מחלקת גישה לנתוני הצעות בטון של קבלנים"""

    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[ContractorConcreteRequest]:
        """שליפת כל ההצעות של הקבלנים"""
        return self.db.query(ContractorConcreteRequest).all()

    def get_by_id(self, request_id: int) -> Optional[ContractorConcreteRequest]:
        """שליפת הצעה לפי מזהה"""
        return self.db.query(ContractorConcreteRequest).filter(
            ContractorConcreteRequest.request_id == request_id
        ).first()

    def get_by_contractor(self, contractor_id: int) -> List[ContractorConcreteRequest]:
        """שליפת כל ההצעות של קבלן מסויים"""
        return self.db.query(ContractorConcreteRequest).filter(
            ContractorConcreteRequest.contractor_id == contractor_id
        ).all()



    def create_for_contractor(
        self, contractor_id: int, data: ContractorConcreteRequestCreateDTO
    ) -> ContractorConcreteRequest:
        """
        יצירת פנייה עבור קבלן מחובר (שלב 2).
        contractor_id ו-status נקבעים ע"י השרת. המחיר נשמר כפי שהוזן (ללא הכפלה).
        id_customer נקבע בעת אישור (שלב 4).
        """
        new_offer = ContractorConcreteRequest(
            concrete_id=data.concrete_id,
            contractor_id=contractor_id,
            quantity=data.quantity,
            address=data.address,
            lat=data.lat,
            lng=data.lng,
            expiry_time=data.expiry_time,
            price=data.price,
            status="OPEN",
        )
        self.db.add(new_offer)
        self.db.commit()
        self.db.refresh(new_offer)
        return new_offer

    def create(self, data: ContractorConcreteRequestCreateDTO) -> ContractorConcreteRequest:
        """יצירת הצעת קבלן חדשה"""
        new_offer = ContractorConcreteRequest(
            concrete_id=data.concrete_id,
            contractor_id=data.contractor_id,
            quantity=data.quantity,
            address=data.address,
            lat=data.lat,
            lng=data.lng,
            expiry_time=data.expiry_time,
            price=data.price,
            id_customer=data.id_customer,
        )
        self.db.add(new_offer)
        self.db.commit()
        self.db.refresh(new_offer)
        return new_offer

    def update(self, request_id: int, data: ContractorConcreteRequestCreateDTO) -> Optional[ContractorConcreteRequest]:
        """עדכון הצעה קיימת"""
        existing = self.get_by_id(request_id)
        if not existing:
            return None

        # עדכון כל שדה שאינו None
        if data.concrete_id is not None:
            existing.concrete_id = data.concrete_id
        if data.contractor_id is not None:
            existing.contractor_id = data.contractor_id
        if data.quantity is not None:
            existing.quantity = data.quantity
        if data.address is not None:
            existing.address = data.address
        if data.lat is not None:
            existing.lat = data.lat
        if data.lng is not None:
            existing.lng = data.lng
        if data.expiry_time is not None:
            existing.expiry_time = data.expiry_time

        if data.price is not None:
            existing.price = data.price
        if data.id_customer is not None:
            existing.id_customer = data.id_customer
        self.db.commit()
        self.db.refresh(existing)
        return existing

    def delete(self, request_id: int) -> bool:
        """מחיקת הצעה"""
        existing = self.get_by_id(request_id)
        if not existing:
            return False
        self.db.delete(existing)
        self.db.commit()
        return True


