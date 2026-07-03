"""
Controller לאימות והרשאות (שלב 1).
נתיבים: /auth/register/{role}, /auth/login, /auth/me, /auth/change-password,
        /admin/users/{id}/reset-password (מנהל בלבד).
טבלאות נפרדות (OD-8): login מחפש בלקוחות/קבלנים/מנהלים; שם המשתמש ייחודי
בין כל הטבלאות (נאכף גם ברמת האפליקציה).
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db
from dto.auth_dto import (
    RegisterDTO,
    LoginDTO,
    TokenDTO,
    MeDTO,
    ChangePasswordDTO,
    AdminResetPasswordDTO,
)
from repository.customer_repository import CustomerRepository
from repository.contractor_repository import ContractorRepository
from repository.admin_repository import AdminRepository
from service.auth_service import hash_password, verify_password, create_access_token
from service.security import get_current_user, get_current_admin
from service.rate_limit import rate_limit
from config import settings

router = APIRouter(tags=["Auth"])

# Rate limiting (שלב 6) — הגנת brute-force. בדיקות פטורות (ראה rate_limit).
_login_rl = rate_limit(settings.RATE_LIMIT_LOGIN_MAX, settings.RATE_LIMIT_WINDOW_SECONDS, "login")
_register_rl = rate_limit(settings.RATE_LIMIT_REGISTER_MAX, settings.RATE_LIMIT_WINDOW_SECONDS, "register")


# ------------------------------------------------------------------ helpers
def _username_taken(db: Session, user_name: str) -> bool:
    """שם משתמש תפוס אם קיים באחת משלוש הטבלאות (ייחודיות חוצת-טבלאות)."""
    return (
        CustomerRepository(db).get_by_username(user_name) is not None
        or ContractorRepository(db).get_by_username(user_name) is not None
        or AdminRepository(db).get_by_username(user_name) is not None
    )


def _get_user_record(db: Session, role: str, user_id: int):
    """מחזיר את רשומת ה-ORM של המשתמש לפי תפקיד+מזהה, או None."""
    if role == "customer":
        return CustomerRepository(db).get_by_id(user_id)
    if role == "contractor":
        return ContractorRepository(db).get_by_id(user_id)
    if role == "admin":
        return AdminRepository(db).get_by_id(user_id)
    return None


def _register(role: str, data: RegisterDTO, db: Session) -> TokenDTO:
    if _username_taken(db, data.user_name):
        raise HTTPException(status_code=409, detail="שם המשתמש כבר תפוס")

    pw_hash = hash_password(data.password)
    repo = CustomerRepository(db) if role == "customer" else ContractorRepository(db)
    try:
        user = repo.create_with_credentials(
            first_name=data.first_name,
            last_name=data.last_name,
            user_name=data.user_name,
            phone=data.phone,
            password_hash=pw_hash,
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="שם המשתמש כבר תפוס")

    token = create_access_token(user.id, role)
    return TokenDTO(access_token=token, role=role, user_id=user.id)


# ------------------------------------------------------------------ register
@router.post("/auth/register/customer", response_model=TokenDTO, status_code=201,
             dependencies=[Depends(_register_rl)])
def register_customer(data: RegisterDTO, db: Session = Depends(get_db)):
    """הרשמת לקוח חדש; שם משתמש קיים → 409. מחזיר טוקן."""
    return _register("customer", data, db)


@router.post("/auth/register/contractor", response_model=TokenDTO, status_code=201,
             dependencies=[Depends(_register_rl)])
def register_contractor(data: RegisterDTO, db: Session = Depends(get_db)):
    """הרשמת קבלן חדש; שם משתמש קיים → 409. מחזיר טוקן."""
    return _register("contractor", data, db)


# ------------------------------------------------------------------ login
@router.post("/auth/login", response_model=TokenDTO, dependencies=[Depends(_login_rl)])
def login(data: LoginDTO, db: Session = Depends(get_db)):
    """מאמת מול שלוש הטבלאות; מחזיר טוקן + תפקיד. פרטים שגויים → 401."""
    candidates = [
        ("customer", CustomerRepository(db).get_by_username(data.user_name)),
        ("contractor", ContractorRepository(db).get_by_username(data.user_name)),
        ("admin", AdminRepository(db).get_by_username(data.user_name)),
    ]
    for role, user in candidates:
        if user is not None and verify_password(data.password, user.password_hash):
            token = create_access_token(user.id, role)
            return TokenDTO(access_token=token, role=role, user_id=user.id)

    raise HTTPException(status_code=401, detail="שם משתמש או סיסמה שגויים")


# ------------------------------------------------------------------ me
@router.get("/auth/me", response_model=MeDTO)
def me(current=Depends(get_current_user), db: Session = Depends(get_db)):
    """פרטי המשתמש המחובר."""
    user = _get_user_record(db, current["role"], current["id"])
    if user is None:
        raise HTTPException(status_code=404, detail="המשתמש לא נמצא")
    return MeDTO(
        id=user.id,
        role=current["role"],
        user_name=user.user_name,
        first_name=getattr(user, "first_name", None),
        last_name=getattr(user, "last_name", None),
        phone=getattr(user, "phone", None),
    )


# ------------------------------------------------------------- change password
@router.post("/auth/change-password")
def change_password(
    data: ChangePasswordDTO,
    current=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """שינוי סיסמה ע"י המשתמש המחובר (מאמת את הסיסמה הישנה)."""
    user = _get_user_record(db, current["role"], current["id"])
    if user is None:
        raise HTTPException(status_code=404, detail="המשתמש לא נמצא")
    if not verify_password(data.old_password, user.password_hash):
        raise HTTPException(status_code=401, detail="הסיסמה הנוכחית שגויה")

    user.password_hash = hash_password(data.new_password)
    db.commit()
    return {"detail": "הסיסמה עודכנה בהצלחה"}


# ------------------------------------------------- admin reset password (OD-12)
@router.post("/admin/users/{user_id}/reset-password")
def admin_reset_password(
    user_id: int,
    data: AdminResetPasswordDTO,
    _admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """מנהל מאפס סיסמה של לקוח/קבלן לסיסמה זמנית (OD-12)."""
    user = _get_user_record(db, data.role, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="המשתמש לא נמצא")

    user.password_hash = hash_password(data.new_password)
    db.commit()
    return {"detail": "הסיסמה אופסה בהצלחה"}
