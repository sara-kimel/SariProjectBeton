"""
Repository ללקוחות (Customer)
שכבה זו אחראית על כל הגישה ל-DB בנושא לקוחות
פעולות CRUD בסיסיות: יצירה, קריאה, עדכון, מחיקה
"""

from typing import List, Optional                    # סוגים לתיאור החזרות
from sqlalchemy.orm import Session                   # סוג של סשן ל-DB
from models.customer import Customer                 # המודל של לקוח
from dto.customer_dto import CustomerCreateDTO       # ה-DTO ליצירה


class CustomerRepository:
    """
    מחלקה לגישה לנתוני לקוחות בבסיס הנתונים
    מקבלת בקונסטרוקטור סשן של SQLAlchemy
    """

    def __init__(self, db: Session):
        """אתחול עם סשן של DB"""
        self.db = db   # שמירת הסשן לשימוש בכל הפונקציות

    def get_all(self) -> List[Customer]:
        """
        שליפת כל הלקוחות מה-DB
        החזרה: רשימה של אובייקטי Customer
        """
        return self.db.query(Customer).all()

    def get_by_id(self, customer_id: int) -> Optional[Customer]:
        """
        שליפת לקוח לפי מזהה
        החזרה: אובייקט Customer או None אם לא נמצא
        """
        return self.db.query(Customer).filter(Customer.id == customer_id).first()

    def get_by_username(self, user_name: str) -> Optional[Customer]:
        """שליפת לקוח לפי שם משתמש (לאימות/הרשמה)."""
        return self.db.query(Customer).filter(Customer.user_name == user_name).first()

    def create_with_credentials(
        self, first_name, last_name, user_name, phone, password_hash
    ) -> Customer:
        """יצירת לקוח עם סיסמה מוצפנת (זרימת /auth/register)."""
        new_customer = Customer(
            first_name=first_name,
            last_name=last_name,
            user_name=user_name,
            phone=phone,
            password_hash=password_hash,
        )
        self.db.add(new_customer)
        self.db.commit()
        self.db.refresh(new_customer)
        return new_customer

    def set_password_hash(self, customer: Customer, password_hash: str) -> Customer:
        """עדכון סיסמה מוצפנת (שינוי סיסמה / איפוס ע"י מנהל)."""
        customer.password_hash = password_hash
        self.db.commit()
        self.db.refresh(customer)
        return customer

    def create(self, customer_data: CustomerCreateDTO) -> Customer:
        """
        יצירת לקוח חדש (פרופיל ללא אישורים — ניהול/תאימות).
        הרשמה עם סיסמה נעשית דרך create_with_credentials מזרימת /auth/register.
        """
        new_customer = Customer(
            first_name=customer_data.first_name,
            last_name=customer_data.last_name,
            user_name=customer_data.user_name,
            phone=customer_data.phone,
        )
        self.db.add(new_customer)
        self.db.commit()
        self.db.refresh(new_customer)   # רענון כדי לקבל את ה-id שנוצר
        return new_customer

    def update(self, customer_id: int, customer_data: CustomerCreateDTO) -> Optional[Customer]:
        """
        עדכון לקוח קיים
        מחפש לפי id ומעדכן את השדות
        """
        # מציאת הלקוח הקיים
        existing = self.get_by_id(customer_id)
        if not existing:
            return None      # לא נמצא - מחזירים None

        # עדכון השדות
        if customer_data.first_name is not None:
            existing.first_name = customer_data.first_name
        if customer_data.last_name is not None:
            existing.last_name = customer_data.last_name
        if customer_data.user_name is not None:
            existing.user_name = customer_data.user_name
        if customer_data.phone is not None:
            existing.phone = customer_data.phone

        self.db.commit()
        self.db.refresh(existing)
        return existing

    def delete(self, customer_id: int) -> bool:
        """
        מחיקת לקוח לפי מזהה
        החזרה: True אם נמחק, False אם לא נמצא
        """
        existing = self.get_by_id(customer_id)
        if not existing:
            return False

        self.db.delete(existing)
        self.db.commit()
        return True
