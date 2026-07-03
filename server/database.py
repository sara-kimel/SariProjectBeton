"""
קובץ ניהול החיבור לבסיס הנתונים
מטרה: ליצור Engine ו-Session של SQLAlchemy שישמשו את כל הפרויקט
הקובץ הזה מספק את הפונקציה get_db שמשמשת ליצירת חיבור חדש לכל בקשה
"""

from sqlalchemy import create_engine                  # פונקציה ליצירת מנוע חיבור
from sqlalchemy.orm import sessionmaker, declarative_base, Session  # כלי ORM
from config import settings                           # הגדרות הפרויקט


# יצירת מנוע חיבור (Engine) לבסיס הנתונים
# echo=True יציג בלוג את כל ה-SQL שמתבצע - שימושי לפיתוח
engine = create_engine(
    settings.database_url,
    echo=False,           # שינוי ל-True יציג את כל פקודות ה-SQL בקונסולה
    pool_pre_ping=True,   # בדיקה שהחיבור עדיין חי לפני שמשתמשים בו
)

# יצירת מחלקת Session - כל בקשה תקבל סשן חדש שמתחבר ל-DB
SessionLocal = sessionmaker(
    autocommit=False,     # לא לשמור אוטומטית - אנחנו נחליט מתי לשמור
    autoflush=False,      # לא לשלוח שאילתות אוטומטית
    bind=engine           # קישור לאותו מנוע שהגדרנו למעלה
)

# מחלקת בסיס לכל המודלים שלנו - כל מודל יורש ממנה
Base = declarative_base()


def get_db():
    """
    פונקציית עזר ליצירת חיבור חדש לבסיס הנתונים
    משמשת כ-Dependency ב-FastAPI - מבטיחה שהחיבור ייסגר בסוף הבקשה
    זה Generator - הוא מחזיר את ה-DB ואחר כך סוגר אותו ב-finally
    """
    db = SessionLocal()       # יצירת סשן חדש
    try:
        yield db              # החזרת הסשן למי שצריך
    finally:
        db.close()            # סגירת הסשן בכל מקרה (גם אם הייתה שגיאה)
