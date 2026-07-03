"""
DTO לסוג בטון (ConcreteType) - שילוב מאפיינים
"""

from typing import Optional
from pydantic import BaseModel, Field


class ConcreteTypeCreateDTO(BaseModel):
    """DTO ליצירת סוג בטון חדש"""

    strength_id: Optional[int] = Field(None, description="מזהה חוזק")
    Reliant_id: Optional[int] = Field(None, description="מזהה סומך")
    Stone_size_id: Optional[int] = Field(None, description="מזהה גודל אבן")
    Purpose_id: Optional[int] = Field(None, description="מזהה מטרה")


class ConcreteTypeResponseDTO(BaseModel):
    """DTO להחזרת סוג בטון"""

    id: int
    strength_id: Optional[int] = None
    Reliant_id: Optional[int] = None
    Stone_size_id: Optional[int] = None
    Purpose_id: Optional[int] = None

    class Config:
        from_attributes = True
