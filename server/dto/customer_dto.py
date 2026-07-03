"""
DTO ללקוח (Customer)
מגדיר את המבנה של נתוני הלקוח שעוברים בבקשות API
יש שני סוגי DTO:
1. CreateDTO - לקבלת נתונים מהלקוח (יצירה / עדכון)
2. ResponseDTO - להחזרת נתונים ללקוח (כולל ה-ID)
"""

from typing import Optional               # סוג שמאפשר ערך אופציונלי
from pydantic import BaseModel, Field     # מחלקות בסיס של Pydantic


class CustomerCreateDTO(BaseModel):
    """
    DTO ליצירת לקוח חדש
    מכיל את הנתונים שהלקוח שולח לשרת
    """

    # שם םרטי הלקוח - אופציונלי, עד 15 תווים (כפי שמוגדר ב-DB)
    first_name: Optional[str] = Field(None, max_length=15, description="שם םרטי הלקוח")

    # שם משפחה הלקוח - אופציונלי, עד 15 תווים (כפי שמוגדר ב-DB)
    last_name: Optional[str] = Field(None, max_length=15, description="שם משפחה הלקוח")

    # שם משתמש של הלקוח - עד 50 תווים
    user_name: Optional[str] = Field(None, max_length=50, description="שם משתמש של הלקוח")

    # מספר טלפון - אופציונלי, עד 20 תווים
    phone: Optional[str] = Field(None, max_length=20, description="מספר טלפון")

    # הערה: הסיסמה אינה חלק מ-DTO זה. יצירת משתמש עם אישורים נעשית דרך
    # /auth/register (שלב 1); סיסמה נשמרת מוצפנת (password_hash) ולעולם לא מוחזרת.


class CustomerResponseDTO(BaseModel):
    """
    DTO להחזרת לקוח מהשרת
    מכיל גם את המזהה (id) שנוצר בבסיס הנתונים
    """

    id: int                              # המזהה של הלקוח שנוצר ב-DB
    first_name: Optional[str] = None           # שם פרטי הלקוח
    last_name: Optional[str] = None           # שם משפחה הלקוח
    user_name: Optional[str] = None           # שם משתמש של הלקוח
    phone: Optional[str] = None          # טלפון

    class Config:
        # הגדרה שמאפשרת ל-Pydantic לקרוא ממודלים של SQLAlchemy
        from_attributes = True
