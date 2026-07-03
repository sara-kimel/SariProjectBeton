"""
DTO להצעת בטון של קבלן (ContractorConcreteRequest)
"""

from typing import Optional
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator


class ContractorConcreteRequestCreateDTO(BaseModel):
    """
    DTO ליצירת הצעת בטון חדשה מקבלן
    """

    # מזהה סוג הבטון
    concrete_id: Optional[int] = Field(None, description="מזהה סוג הבטון")

    # מזהה הקבלן שמציע
    contractor_id: Optional[int] = Field(None, description="מזהה הקבלן")

    # כמות הבטון שיש לקבלן
    quantity: Optional[Decimal] = Field(None, description="כמות בטון שנותרה")

    # כתובת היכן הבטון נמצא
    address: Optional[str] = Field(None, max_length=255, description="כתובת הקבלן")

    # קו רוחב
    lat: Optional[Decimal] = Field(None, description="קו רוחב")

    # קו אורך
    lng: Optional[Decimal] = Field(None, description="קו אורך")

    # זמן תפוגה של ההצעה
    expiry_time: Optional[datetime] = Field(None, description="זמן תפוגת ההצעה")


    # מחיר
    price: Optional[str] = Field(None, max_length=100, description="מחיר")

    #קוד לקוח
    id_customer: Optional[int] = Field(None,  description="קוד לקוח")

    # ולידציה (שלב 6) — עקבית עם בקשת הלקוח
    @field_validator("lat")
    @classmethod
    def _valid_lat(cls, v):
        if v is not None and (v < -90 or v > 90):
            raise ValueError("קו רוחב חייב להיות בטווח [-90, 90]")
        return v

    @field_validator("lng")
    @classmethod
    def _valid_lng(cls, v):
        if v is not None and (v < -180 or v > 180):
            raise ValueError("קו אורך חייב להיות בטווח [-180, 180]")
        return v

    @field_validator("quantity")
    @classmethod
    def _valid_qty(cls, v):
        if v is not None and v <= 0:
            raise ValueError("כמות הבטון חייבת להיות גדולה מ-0")
        if v is not None and v > 9999.99:  # תחום DECIMAL(6,2)
            raise ValueError("כמות הבטון חורגת מהתחום המותר")
        return v


class ContractorConcreteRequestResponseDTO(BaseModel):
    """
    DTO להחזרת הצעת קבלן מהשרת
    """

    request_id: int
    concrete_id: Optional[int] = None
    contractor_id: Optional[int] = None
    quantity: Optional[Decimal] = None
    address: Optional[str] = None
    lat: Optional[Decimal] = None
    lng: Optional[Decimal] = None
    expiry_time: Optional[datetime] = None
    price: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None
    #id_customer: Optional[int] = None

    class Config:
        from_attributes = True
