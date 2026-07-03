"""
DTOs לאימות (שלב 1). לעולם לא כוללים את ה-hash של הסיסמה בפלט.
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field


class RegisterDTO(BaseModel):
    """הרשמת לקוח/קבלן חדש."""
    first_name: Optional[str] = Field(None, max_length=50, description="שם פרטי")
    last_name: Optional[str] = Field(None, max_length=50, description="שם משפחה")
    user_name: str = Field(..., min_length=3, max_length=50, description="שם משתמש")
    phone: Optional[str] = Field(None, max_length=20, description="טלפון")
    password: str = Field(..., min_length=6, max_length=72, description="סיסמה")


class LoginDTO(BaseModel):
    user_name: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=72)


class TokenDTO(BaseModel):
    """תשובת התחברות/הרשמה — הטוקן + פרטי זיהוי בסיסיים."""
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int


class MeDTO(BaseModel):
    """פרטי המשתמש המחובר (ללא סיסמה)."""
    id: int
    role: str
    user_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None


class ChangePasswordDTO(BaseModel):
    old_password: str = Field(..., min_length=1, max_length=72)
    new_password: str = Field(..., min_length=6, max_length=72)


class AdminResetPasswordDTO(BaseModel):
    """איפוס סיסמה ע"י מנהל (OD-12). role מזהה באיזו טבלה המשתמש."""
    role: Literal["customer", "contractor"]
    new_password: str = Field(..., min_length=6, max_length=72)
