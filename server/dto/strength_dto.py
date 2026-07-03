"""
DTO לחוזק בטון (Strength) — כולל sort_order להשוואת ">=" (שלב 5).
"""

from typing import Optional
from pydantic import BaseModel, Field


class StrengthCreateDTO(BaseModel):
    """DTO ליצירת/עדכון רשומת חוזק"""

    strength: Optional[str] = Field(None, max_length=50, description="תיאור החוזק")
    sort_order: Optional[int] = Field(None, description="דירוג להשוואת חוזק (ב-20<ב-30<ב-40)")


class StrengthResponseDTO(BaseModel):
    """DTO להחזרת רשומת חוזק"""

    id: int
    strength: Optional[str] = None
    sort_order: Optional[int] = None

    class Config:
        from_attributes = True
