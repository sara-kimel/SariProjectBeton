"""
DTO לקבלן (Contractor)
מגדיר את מבנה הנתונים של קבלן בבקשות וב-תגובות API
"""

from typing import Optional
from pydantic import BaseModel, Field


class ContractorCreateDTO(BaseModel):
    """
    DTO ליצירת קבלן חדש
    מכיל את הנתונים שהלקוח שולח לשרת
    """

    # שם הקבלן - עד 15 תווים
    first_name: Optional[str] = Field(None, max_length=15, description="שם פרטי הקבלן")


    # שם הקבלן - עד 15 תווים
    last_name: Optional[str] = Field(None, max_length=15, description="שם משפחה הקבלן")

    # שם משתמש של הקבלן - עד 50 תווים
    user_name: Optional[str] = Field(None, max_length=50, description="שם משתמש של הקבלן")

    # מספר טלפון של הקבלן - עד 15 תווים
    phone: Optional[str] = Field(None, max_length=15, description="מספר טלפון")

    # הערה: הסיסמה אינה חלק מ-DTO זה. הרשמה עם אישורים דרך /auth/register (שלב 1).


class ContractorResponseDTO(BaseModel):
    """
    DTO להחזרת קבלן מהשרת
    כולל את המזהה (id) שנוצר ב-DB
    """

    id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    user_name: Optional[str] = None
    phone: Optional[str] = None

    class Config:
        # מאפשר ל-Pydantic לקרוא ממודלים של SQLAlchemy
        from_attributes = True
