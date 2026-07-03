"""
Controller לניהול (Admin) — שלב 5.
- GET /admin/users — רשימת לקוחות + קבלנים (ללא hash), למנהל בלבד.
- GET /admin/stats — מוני לוח בקרה (בקשות/פניות פתוחות, עסקאות סגורות, אחוז התאמה).
(reset-password נמצא ב-auth_controller: POST /admin/users/{id}/reset-password.)
"""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from dto.admin_dto import AdminUserDTO, AdminStatsDTO
from models.customer import Customer
from models.contractor import Contractor
from service.security import get_current_admin

router = APIRouter(prefix="/admin", tags=["Admin"], dependencies=[Depends(get_current_admin)])


@router.get("/users", response_model=List[AdminUserDTO])
def list_users(db: Session = Depends(get_db)):
    """לקוחות + קבלנים (ללא סיסמאות/hash)."""
    users: List[AdminUserDTO] = []
    for c in db.query(Customer).all():
        users.append(AdminUserDTO(
            id=c.id, role="customer", user_name=c.user_name,
            first_name=c.first_name, last_name=c.last_name, phone=c.phone,
        ))
    for k in db.query(Contractor).all():
        users.append(AdminUserDTO(
            id=k.id, role="contractor", user_name=k.user_name,
            first_name=k.first_name, last_name=k.last_name, phone=k.phone,
        ))
    return users


@router.get("/stats", response_model=AdminStatsDTO)
def stats(db: Session = Depends(get_db)):
    """מוני לוח הבקרה. אחוז התאמה = התאמות שאושרו / סך ההתאמות."""
    open_requests = db.execute(
        text("SELECT COUNT(*) FROM ConcreteRequests WHERE [status]='OPEN'")
    ).scalar() or 0
    open_offers = db.execute(
        text("SELECT COUNT(*) FROM ContractorConcreteRequests WHERE [status]='OPEN'")
    ).scalar() or 0
    closed_deals = db.execute(
        text("SELECT COUNT(*) FROM ContractorConcreteRequests WHERE [status]='CLOSED'")
    ).scalar() or 0
    total_matches = db.execute(text("SELECT COUNT(*) FROM OfferMatches")).scalar() or 0
    accepted_matches = db.execute(
        text("SELECT COUNT(*) FROM OfferMatches WHERE [status]='ACCEPTED'")
    ).scalar() or 0

    match_rate = round(100.0 * accepted_matches / total_matches, 1) if total_matches else 0.0

    return AdminStatsDTO(
        open_requests=open_requests,
        open_offers=open_offers,
        closed_deals=closed_deals,
        total_matches=total_matches,
        accepted_matches=accepted_matches,
        match_rate=match_rate,
    )
