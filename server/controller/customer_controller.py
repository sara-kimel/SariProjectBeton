"""
Controller ללקוחות (Customer)
מטפל בכל בקשות ה-HTTP שקשורות ללקוחות ומגדיר את ה-endpoints של ה-API.

הרשאות (FIX-1, SPEC §10/§13.5): כל הנתיבים דורשים משתמש מחובר;
רשימת-הכל ויצירה — מנהל בלבד; צפייה/עדכון/מחיקה של לקוח בודד — לבעלים או למנהל
בלבד (מניעת IDOR ודליפת מספרי טלפון).
"""

from typing import List                              # סוג לרשימה
from fastapi import APIRouter, Depends, HTTPException, status  # כלי FastAPI
from sqlalchemy.orm import Session                   # סוג של DB session
from database import get_db                          # פונקציית עזר לקבלת DB
from dto.customer_dto import CustomerCreateDTO, CustomerResponseDTO
from repository.customer_repository import CustomerRepository
from service.security import get_current_user


# יצירת ראוטר עם prefix משותף לכל ה-endpoints של לקוחות (כולם דורשים אימות)
router = APIRouter(
    prefix="/customers",      # כל ה-routes יתחילו ב-/customers
    tags=["Customers"],       # תיוג עבור התיעוד האוטומטי של Swagger
    dependencies=[Depends(get_current_user)],
)


def _owns_or_admin(current: dict, customer_id) -> bool:
    """בעלים (לקוח על עצמו) או מנהל בלבד."""
    if current["role"] == "admin":
        return True
    return current["role"] == "customer" and current["id"] == customer_id


@router.get("/", response_model=List[CustomerResponseDTO])
def get_all_customers(
    current: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    שליפת כל הלקוחות — מנהל בלבד (מונע גרידת מספרי טלפון).
    GET /customers/
    """
    if current["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="אין הרשאה")
    return CustomerRepository(db).get_all()


@router.get("/{customer_id}", response_model=CustomerResponseDTO)
def get_customer_by_id(
    customer_id: int,
    current: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    שליפת לקוח לפי מזהה — לבעלים או למנהל בלבד.
    GET /customers/{customer_id}
    """
    if not _owns_or_admin(current, customer_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="אין הרשאה לצפות בלקוח אחר")
    customer = CustomerRepository(db).get_by_id(customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"לקוח עם מזהה {customer_id} לא נמצא"
        )
    return customer


@router.post("/", response_model=CustomerResponseDTO, status_code=status.HTTP_201_CREATED)
def create_customer(
    customer: CustomerCreateDTO,
    current: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    יצירת לקוח חדש — מנהל בלבד.
    POST /customers/
    (משתמשים רגילים נוצרים דרך /auth/register עם שם משתמש וסיסמה.)
    """
    if current["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="נדרשת הרשאת מנהל")
    return CustomerRepository(db).create(customer)


@router.put("/{customer_id}", response_model=CustomerResponseDTO)
def update_customer(
    customer_id: int,
    customer: CustomerCreateDTO,
    current: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    עדכון לקוח קיים — לבעלים או למנהל בלבד.
    PUT /customers/{customer_id}
    """
    if not _owns_or_admin(current, customer_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="אין הרשאה לעדכן לקוח אחר")
    updated = CustomerRepository(db).update(customer_id, customer)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"לקוח עם מזהה {customer_id} לא נמצא"
        )
    return updated


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(
    customer_id: int,
    current: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    מחיקת לקוח — לבעלים או למנהל בלבד.
    DELETE /customers/{customer_id}
    """
    if not _owns_or_admin(current, customer_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="אין הרשאה למחוק לקוח אחר")
    if not CustomerRepository(db).delete(customer_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"לקוח עם מזהה {customer_id} לא נמצא"
        )
    return None
