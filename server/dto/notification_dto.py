"""
DTOs להתראות (Notifications) — שלב 4.
"""

from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class NotificationDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    user_role: str
    type: str
    title: Optional[str] = None
    body: Optional[str] = None
    related_offer_id: Optional[int] = None
    related_request_id: Optional[int] = None
    is_read: bool
    created_at: Optional[datetime] = None


class UnreadCountDTO(BaseModel):
    unread: int
