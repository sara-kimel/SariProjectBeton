"""
DTO לבקשת בטון של לקוח (ConcreteRequest)
"""

from typing import Optional
from datetime import date as DateType
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator


class ConcreteRequestCreateDTO(BaseModel):
    """
    DTO ליצירת/עדכון בקשת בטון של לקוח.
    הערה: customer_id ו-status אינם נלקחים מהגוף ביצירה — השרת קובע אותם
    לפי המשתמש המחובר (שלב 2). הם נשמרים כאן לתאימות/עדכון פנימי בלבד.
    """

    # מזהה הלקוח — מתעלמים ממנו ב-POST (נקבע מהמשתמש המחובר)
    customer_id: Optional[int] = Field(None, description="מזהה הלקוח (מתעלמים ב-POST)")

    # מזהה המטרה / קטגוריה
    purpose_id: Optional[int] = Field(None, description="מזהה המטרה")

    # כמות הבטון הרצויה (במ"ק)
    quantity: Optional[Decimal] = Field(None, description="כמות בטון במ\"ק")

    # הכתובת לאספקה
    address: Optional[str] = Field(None, max_length=255, description="כתובת אספקה")

    # קו רוחב גיאוגרפי (חובה)
    lat: Decimal = Field(..., description="קו רוחב")

    # קו אורך גיאוגרפי (חובה)
    lng: Decimal = Field(..., description="קו אורך")
    status: Optional[str] = Field(None, max_length=20, description="status (מתעלמים ב-POST)")

    @field_validator("lat")
    @classmethod
    def _valid_lat(cls, v: Decimal) -> Decimal:
        if v < -90 or v > 90:
            raise ValueError("קו רוחב חייב להיות בטווח [-90, 90]")
        return v

    @field_validator("lng")
    @classmethod
    def _valid_lng(cls, v: Decimal) -> Decimal:
        if v < -180 or v > 180:
            raise ValueError("קו אורך חייב להיות בטווח [-180, 180]")
        return v

    @field_validator("quantity")
    @classmethod
    def _positive_qty(cls, v):
        if v is not None and v <= 0:
            raise ValueError("כמות הבטון חייבת להיות גדולה מ-0")
        if v is not None and v > 9999.99:  # תחום DECIMAL(6,2)
            raise ValueError("כמות הבטון חורגת מהתחום המותר")
        return v



class ConcreteRequestResponseDTO(BaseModel):
    """
    DTO להחזרת בקשת בטון מהשרת
    כולל את כל השדות + מזהה ותאריך
    """

    request_id: int                       # מזהה הבקשה שנוצר ב-DB
    customer_id: Optional[int] = None
    purpose_id: Optional[int] = None
    quantity: Optional[Decimal] = None
    address: Optional[str] = None
    lat: Decimal
    lng: Decimal
    date: DateType                        # תאריך הבקשה
    status: Optional[str] = None
    class Config:
        from_attributes = True
