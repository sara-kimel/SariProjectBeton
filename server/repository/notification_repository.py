"""
Repository להתראות (Notifications) — שלב 4.
- create: מוסיף רשומת התראה (add + flush, ללא commit — כדי שתהיה חלק מטרנזקציית
  האירוע היוצר, למשל אישור עסקה).
- get_for_user / unread_count / mark_read: שירות מרכז ההתראות.
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from models.notification import Notification


class NotificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        user_id: int,
        user_role: str,
        type: str,
        title: str,
        body: str,
        related_offer_id: Optional[int] = None,
        related_request_id: Optional[int] = None,
    ) -> Notification:
        note = Notification(
            user_id=user_id,
            user_role=user_role,
            type=type,
            title=title,
            body=body,
            related_offer_id=related_offer_id,
            related_request_id=related_request_id,
            is_read=False,
        )
        self.db.add(note)
        self.db.flush()   # ה-commit באחריות השירות שמנהל את הטרנזקציה
        return note

    def get_for_user(self, user_id: int, user_role: str, limit: int = 100) -> List[Notification]:
        return (
            self.db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.user_role == user_role)
            .order_by(Notification.created_at.desc(), Notification.id.desc())
            .limit(limit)
            .all()
        )

    def unread_count(self, user_id: int, user_role: str) -> int:
        return (
            self.db.query(Notification)
            .filter(
                Notification.user_id == user_id,
                Notification.user_role == user_role,
                Notification.is_read == False,  # noqa: E712 — ב-mssql מתקמפל ל-`is_read = 0`
            )
            .count()
        )

    def get_by_id(self, note_id: int) -> Optional[Notification]:
        return self.db.query(Notification).filter(Notification.id == note_id).first()

    def mark_read(self, note: Notification) -> Notification:
        note.is_read = True
        self.db.commit()
        self.db.refresh(note)
        return note
