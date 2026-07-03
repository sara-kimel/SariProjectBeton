"""
DTO לסומך (Reliant)
"""

from typing import Optional
from pydantic import BaseModel, Field


class ReliantCreateDTO(BaseModel):
    """DTO ליצירת רשומת סומך חדשה"""

    Reliant: Optional[str] = Field(None, max_length=50, description="תיאור הסומך")


class ReliantResponseDTO(BaseModel):
    """DTO להחזרת רשומת סומך"""

    id: int
    Reliant: Optional[str] = None

    class Config:
        from_attributes = True
