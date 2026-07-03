"""
DTO למטרה / קטגוריה (Purpose) — כולל מיפוי מטרה->מפרט (שלב 5, OD-2).
"""

from typing import Optional
from pydantic import BaseModel, Field


class PurposeCreateDTO(BaseModel):
    """DTO ליצירת/עדכון-שם רשומת מטרה (+ אפשרות להגדיר מיפוי כבר ביצירה)."""

    Purpose: Optional[str] = Field(None, max_length=50, description="תיאור המטרה")
    req_strength_id: Optional[int] = Field(None, description="חוזק נדרש (מיפוי OD-2)")
    req_reliant_id: Optional[int] = Field(None, description="סומך נדרש (מיפוי OD-2)")
    req_stone_size_id: Optional[int] = Field(None, description="גודל-אבן נדרש (מיפוי OD-2)")


class PurposeMappingDTO(BaseModel):
    """
    עדכון ייעודי של מיפוי מטרה->מפרט. שולח את שלושת השדות (None => ניקוי הדרישה)
    — זה מה שמזין את סינון OD-2 במנוע.
    """

    req_strength_id: Optional[int] = None
    req_reliant_id: Optional[int] = None
    req_stone_size_id: Optional[int] = None


class PurposeResponseDTO(BaseModel):
    """DTO להחזרת רשומת מטרה כולל המיפוי הנוכחי."""

    id: int
    Purpose: Optional[str] = None
    req_strength_id: Optional[int] = None
    req_reliant_id: Optional[int] = None
    req_stone_size_id: Optional[int] = None

    class Config:
        from_attributes = True
