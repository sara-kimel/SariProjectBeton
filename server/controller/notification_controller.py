"""
Controller למרכז ההתראות (Notifications) — שלב 4.
- GET  /notifications/              — ההתראות של המשתמש המחובר.
- GET  /notifications/unread-count  — מונה לא-נקראו.
- POST /notifications/{id}/read     — סימון התראה כנקראה.
כל הנתיבים דורשים התחברות; משתמש רואה רק את ההתראות שלו.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from dto.notification_dto import NotificationDTO, UnreadCountDTO
from repository.notification_repository import NotificationRepository
from service.security import get_current_user

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/", response_model=List[NotificationDTO])
def list_notifications(
    current: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return NotificationRepository(db).get_for_user(current["id"], current["role"])


@router.get("/unread-count", response_model=UnreadCountDTO)
def unread_count(
    current: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {"unread": NotificationRepository(db).unread_count(current["id"], current["role"])}


@router.post("/{note_id}/read", response_model=NotificationDTO)
def mark_read(
    note_id: int,
    current: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repo = NotificationRepository(db)
    note = repo.get_by_id(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="התראה לא נמצאה")
    if note.user_id != current["id"] or note.user_role != current["role"]:
        raise HTTPException(status_code=403, detail="אין הרשאה להתראה זו")
    return repo.mark_read(note)
