"""
שירות אבטחה — הצפנת סיסמאות (bcrypt) וטוקני JWT (שלב 1).
עוטף את הספריות כדי שהשאר לא ייגע ישירות ב-bcrypt/jwt.
"""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from config import settings

# bcrypt מגביל את הסיסמה ל-72 בייטים — חותכים לפני הצפנה/אימות כדי למנוע חריגה.
_BCRYPT_MAX_BYTES = 72


def _to_bcrypt_bytes(plain: str) -> bytes:
    return (plain or "").encode("utf-8")[:_BCRYPT_MAX_BYTES]


def hash_password(plain: str) -> str:
    """מחזיר hash של bcrypt (מחרוזת) לאחסון ב-DB."""
    hashed = bcrypt.hashpw(_to_bcrypt_bytes(plain), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """בודק סיסמה מול ה-hash השמור. מחזיר False אם ה-hash חסר/פגום."""
    if not hashed:
        return False
    try:
        return bcrypt.checkpw(_to_bcrypt_bytes(plain), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_access_token(user_id: int, role: str) -> str:
    """יוצר JWT עם sub=מזהה, role=תפקיד, ותוקף לפי הקונפיג."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)).timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """מפענח ומאמת JWT. מעלה jwt.PyJWTError אם לא תקין/פג תוקף."""
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
