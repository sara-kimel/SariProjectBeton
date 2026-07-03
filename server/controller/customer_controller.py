"""
Controller ללקוחות (Customer)
מטפל בכל בקשות ה-HTTP שקשורות ללקוחות
מגדיר את ה-endpoints של ה-API
"""

from typing import List                              # סוג לרשימה
from fastapi import APIRouter, Depends, HTTPException, status  # כלי FastAPI
from sqlalchemy.orm import Session                   # סוג של DB session
from database import get_db                          # פונקציית עזר לקבלת DB
from dto.customer_dto import CustomerCreateDTO, CustomerResponseDTO
from repository.customer_repository import CustomerRepository
from service.security import get_current_user


# יצירת ראוטר עם prefix משותף לכל ה-endpoints של לקוחות
# שלב 1: כל הנתיבים דורשים משתמש מחובר (RBAC מלא לפי בעלות — בשלבים הבאים).
router = APIRouter(
    prefix="/customers",      # כל ה-routes יתחילו ב-/customers
    tags=["Customers"],       # תיוג עבור התיעוד האוטומטי של Swagger
    dependencies=[Depends(get_current_user)],
)


@router.get("/", response_model=List[CustomerResponseDTO])
def get_all_customers(db: Session = Depends(get_db)):
    """
    שליפת כל הלקוחות
    GET /customers/
    """
    repo = CustomerRepository(db)        # יצירת Repository עם הסשן
    return repo.get_all()                 # החזרת רשימת לקוחות


@router.get("/{customer_id}", response_model=CustomerResponseDTO)
def get_customer_by_id(customer_id: int, db: Session = Depends(get_db)):
    """
    שליפת לקוח לפי מזהה
    GET /customers/{customer_id}
    """
    repo = CustomerRepository(db)
    customer = repo.get_by_id(customer_id)

    # אם לא נמצא - מחזירים שגיאה 404
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"לקוח עם מזהה {customer_id} לא נמצא"
        )
    return customer


@router.post("/", response_model=CustomerResponseDTO, status_code=status.HTTP_201_CREATED)
def create_customer(customer: CustomerCreateDTO, db: Session = Depends(get_db)):
    """
    יצירת לקוח חדש
    POST /customers/
    גוף הבקשה: CustomerCreateDTO (name, phone)
    """
    repo = CustomerRepository(db)
    return repo.create(customer)


@router.put("/{customer_id}", response_model=CustomerResponseDTO)
def update_customer(
    customer_id: int,
    customer: CustomerCreateDTO,
    db: Session = Depends(get_db)
):
    """
    עדכון לקוח קיים
    PUT /customers/{customer_id}
    """
    repo = CustomerRepository(db)
    updated = repo.update(customer_id, customer)

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"לקוח עם מזהה {customer_id} לא נמצא"
        )
    return updated


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    """
    מחיקת לקוח
    DELETE /customers/{customer_id}
    """
    repo = CustomerRepository(db)
    if not repo.delete(customer_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"לקוח עם מזהה {customer_id} לא נמצא"
        )
    return None
