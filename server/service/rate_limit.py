"""
Rate limiting קל-משקל בזיכרון (שלב 6) — הגנת brute-force על login/register.
חלון מתגלגל פר-IP פר-scope. אין תלות חיצונית; per-process (מספיק ל-MVP;
לפריסה מרובת-תהליכים יש לעבור ל-Redis/reverse-proxy).

בדיקות פנימיות (Starlette TestClient, host="testclient") פטורות — כדי לא לשבור
את הסוויטה שמריצה הרבה קריאות login/register מאותו "IP".
"""

import time
from collections import defaultdict, deque

from fastapi import Request, HTTPException

from config import settings

_buckets: dict = defaultdict(deque)
_EXEMPT_HOSTS = {"testclient"}


def rate_limit(max_calls: int, window_seconds: int, scope: str):
    def dependency(request: Request):
        if not settings.RATE_LIMIT_ENABLED:   # כבוי בבדיקות/פיתוח לפי הצורך
            return
        host = request.client.host if request.client else "unknown"
        if host in _EXEMPT_HOSTS:
            return
        now = time.monotonic()
        key = f"{scope}:{host}"
        dq = _buckets[key]
        while dq and now - dq[0] > window_seconds:
            dq.popleft()
        if len(dq) >= max_calls:
            raise HTTPException(
                status_code=429,
                detail="יותר מדי ניסיונות — נסה/י שוב בעוד מספר דקות",
            )
        dq.append(now)

    return dependency
