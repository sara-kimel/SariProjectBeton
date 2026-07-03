"""
DTOs לניהול (Admin) — שלב 5.
"""

from typing import Optional
from pydantic import BaseModel


class AdminUserDTO(BaseModel):
    """שורת משתמש ברשימת הניהול (ללא hash סיסמה)."""

    id: int
    role: str
    user_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None


class AdminStatsDTO(BaseModel):
    """מוני לוח הבקרה של המנהל."""

    open_requests: int
    open_offers: int
    closed_deals: int
    total_matches: int
    accepted_matches: int
    match_rate: float   # אחוז ההתאמות שהבשילו לאישור (accepted / total)
