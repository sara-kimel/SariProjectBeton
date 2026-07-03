"""
conftest ברמת השורש של server/.
מטרה יחידה: להוסיף את תיקיית server/ ל-sys.path כדי שהבדיקות תוכלנה
לייבא את מודולי האפליקציה בייבוא מוחלט (from app import app, from database ...),
בדיוק כפי שהשרת רץ כשמריצים אותו מתוך server/.
"""

import os
import sys

# כיבוי rate limiting בבדיקות (הסוויטה מריצה הרבה login/register מאותו "IP").
# חייב לקרות לפני ייבוא app/config. הייצור משאיר את ברירת המחדל (מופעל).
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")

_SERVER_DIR = os.path.dirname(os.path.abspath(__file__))
if _SERVER_DIR not in sys.path:
    sys.path.insert(0, _SERVER_DIR)
