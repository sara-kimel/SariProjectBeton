"""
DTO לגודל אבן (StoneSize)
"""

from typing import Optional
from pydantic import BaseModel, Field


class StoneSizeCreateDTO(BaseModel):
    """DTO ליצירת רשומת גודל אבן חדשה"""

    Stone_size: Optional[str] = Field(None, max_length=50, description="תיאור גודל האבן")


class StoneSizeResponseDTO(BaseModel):
    """DTO להחזרת רשומת גודל אבן"""

    id: int
    Stone_size: Optional[str] = None

    class Config:
        from_attributes = True
