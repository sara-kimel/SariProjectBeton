"""
Dependencies של אימות/הרשאות ל-FastAPI (שלב 1).
- get_current_user: מפענח את ה-JWT מכותרת Authorization ומזריק {id, role}.
- require_role(*roles): מחייב שהמשתמש המחובר בעל אחד התפקידים (RBAC).
- קיצורים: get_current_admin / get_current_customer / get_current_contractor.
"""

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from service.auth_service import decode_token

# auto_error=False כדי שנחזיר 401 עם הודעה בעברית (במקום 403 גנרי של starlette).
_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> dict:
    """מחזיר {'id': int, 'role': str} מתוך ה-JWT; 401 אם חסר/לא תקין/פג."""
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=401, detail="לא מאומת — נדרש טוקן")
    try:
        payload = decode_token(credentials.credentials)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="הטוקן פג תוקף — יש להתחבר מחדש")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="טוקן לא תקין")

    sub = payload.get("sub")
    role = payload.get("role")
    if sub is None or role is None:
        raise HTTPException(status_code=401, detail="טוקן חסר פרטים")

    return {"id": int(sub), "role": role}


def require_role(*roles: str):
    """מחזיר dependency שמוודא שהמשתמש בעל אחד התפקידים המותרים."""

    def checker(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] not in roles:
            raise HTTPException(status_code=403, detail="אין הרשאה לפעולה זו")
        return user

    return checker


def get_current_admin(user: dict = Depends(get_current_user)) -> dict:
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="נדרשת הרשאת מנהל")
    return user


def get_current_customer(user: dict = Depends(get_current_user)) -> dict:
    if user["role"] != "customer":
        raise HTTPException(status_code=403, detail="נדרשת הרשאת לקוח")
    return user


def get_current_contractor(user: dict = Depends(get_current_user)) -> dict:
    if user["role"] != "contractor":
        raise HTTPException(status_code=403, detail="נדרשת הרשאת קבלן")
    return user
