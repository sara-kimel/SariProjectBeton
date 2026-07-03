"""
עזר משותף לניהול טבלאות ה-lookup ע"י מנהל (שלב 5).
guarded_delete: מוחק ערך lookup; אם הוא בשימוש (הפרת FK) מחזיר 409 עם הודעה
ברורה במקום להפיל 500 — משמר שלמות היסטוריה (מעדיפים חסימה על מחיקה מדורגת).
"""

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


def guarded_delete(
    db: Session,
    repo,
    entity_id: int,
    not_found_msg: str,
    in_use_msg: str = "לא ניתן למחוק — הערך נמצא בשימוש במערכת",
):
    try:
        ok = repo.delete(entity_id)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=in_use_msg)
    if not ok:
        raise HTTPException(status_code=404, detail=not_found_msg)
    return None
