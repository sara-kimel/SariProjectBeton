"""
קובץ הגדרות כללי לפרויקט
מטרה: לרכז את כל הגדרות החיבור לבסיס הנתונים במקום אחד
הקובץ הזה קורא משתני סביבה מקובץ .env (אם קיים) או משתמש בברירות מחדל
"""

import os                                  # ספריה לעבודה עם משתני סביבה
from dotenv import load_dotenv             # פונקציה לטעינת קובץ .env

# טעינת משתנים מקובץ .env לתוך משתני הסביבה של התהליך
load_dotenv()

# FIX-4: ברירת-המחדל הלא-בטוחה של מפתח ה-JWT — מרוכזת כאן כדי שנוכל לזהות
# אותה ולסרב לעלות איתה בייצור (ראה _validate_production_settings בתחתית).
_DEFAULT_JWT_SECRET = "dev-insecure-secret-change-me"


class Settings:
    """
    מחלקה שמרכזת את כל ההגדרות של הפרויקט
    כל הערכים נטענים ממשתני סביבה או מערכי ברירת מחדל
    """

    # סביבת ריצה: development (ברירת מחדל) / production. משפיע על אכיפת הקשחות (FIX-4).
    APP_ENV: str = os.getenv("APP_ENV", "development")

    # כתובת השרת של SQL Server - לרוב localhost או localhost\SQLEXPRESS
    # FIX-5: נקרא ממשתנה סביבה (היה מקובע ל-"localhost" והתעלם מ-.env).
    DB_SERVER: str = os.getenv("DB_SERVER", "localhost")
    # שם בסיס הנתונים - לפי מה שיצרנו ב-SQL: "beton"
    DB_NAME: str = os.getenv("DB_NAME", "beton")

    # שם משתמש לבסיס הנתונים (במידה ולא משתמשים ב-Windows Authentication)
    DB_USER: str = os.getenv("DB_USER", "")

    # סיסמא לבסיס הנתונים
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")

    # האם להשתמש ב-Windows Authentication במקום שם משתמש וסיסמא
    USE_WINDOWS_AUTH: bool = os.getenv("USE_WINDOWS_AUTH", "True").lower() == "true"

    # ------------------------------------------------------------------
    # פרמטרי מנוע ההתאמה (OD-9)
    # מרוכזים כאן במקום קבועים מפוזרים בקוד המנוע. לא חשופים למשתמש —
    # ניתן לעקוף דרך משתני סביבה בזמן פיתוח/בדיקות בלבד.
    # ------------------------------------------------------------------
    # רדיוס החיפוש הגיאוגרפי במטרים (10 ק"מ)
    MATCH_RADIUS_METERS: int = int(os.getenv("MATCH_RADIUS_METERS", "10000"))
    # משקל זמן ההמתנה בניקוד (ככל שגבוה יותר — הותק חשוב יותר)
    MATCH_SCORE_W1_WAITING: float = float(os.getenv("MATCH_SCORE_W1_WAITING", "5"))
    # משקל זמן הנסיעה בניקוד (עונש על מרחק)
    MATCH_SCORE_W2_TRAVEL: float = float(os.getenv("MATCH_SCORE_W2_TRAVEL", "1"))
    # יחס הכמות המינימלי: request.qty בתחום [ratio*offer.qty, offer.qty]
    MATCH_QUANTITY_MIN_RATIO: float = float(os.getenv("MATCH_QUANTITY_MIN_RATIO", "0.9"))

    # ------------------------------------------------------------------
    # אימות / JWT (שלב 1)
    # JWT_SECRET חייב להיות ב-.env בייצור — לעולם לא בקוד. ברירת המחדל
    # לפיתוח בלבד ואינה בטוחה.
    # ------------------------------------------------------------------
    JWT_SECRET: str = os.getenv("JWT_SECRET", _DEFAULT_JWT_SECRET)
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))  # 24 שעות

    # ------------------------------------------------------------------
    # הקשחה (שלב 6)
    # ------------------------------------------------------------------
    # CORS: רשימת origins מותרים (מופרדת בפסיקים). ברירת מחדל = פיתוח (Vite).
    # להגדיר בייצור ל-origin של הלקוח בלבד. "*" (dev בלבד) מתיר הכל.
    CORS_ORIGINS: str = os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    )
    # Rate limiting על login/register (הגנת brute-force). ברירות מחדל שמרניות.
    # מופעל כברירת מחדל; הבדיקות מכבות אותו (conftest) למניעת תלות ב-IP משותף.
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    RATE_LIMIT_LOGIN_MAX: int = int(os.getenv("RATE_LIMIT_LOGIN_MAX", "10"))
    RATE_LIMIT_REGISTER_MAX: int = int(os.getenv("RATE_LIMIT_REGISTER_MAX", "10"))
    RATE_LIMIT_WINDOW_SECONDS: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))

    @property
    def cors_origin_list(self) -> list:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def database_url(self) -> str:
        """
        בונה את כתובת ה-URL לחיבור לבסיס הנתונים בפורמט של SQLAlchemy
        אם משתמשים ב-Windows Authentication - בונים URL בלי משתמש וסיסמא
        אחרת - בונים URL רגיל עם שם משתמש וסיסמא
        """
        # פרמטרים קבועים לחיבור (הדרייבר של SQL Server)
        driver = "ODBC+Driver+17+for+SQL+Server"

        if self.USE_WINDOWS_AUTH:
            # חיבור עם Windows Authentication
            return (
                f"mssql+pyodbc://@{self.DB_SERVER}/{self.DB_NAME}"
                f"?driver={driver}&trusted_connection=yes"
            )
        else:
            # חיבור עם שם משתמש וסיסמא
            return (
                f"mssql+pyodbc://{self.DB_USER}:{self.DB_PASSWORD}"
                f"@{self.DB_SERVER}/{self.DB_NAME}?driver={driver}"
            )


# יצירת אובייקט הגדרות גלובלי שאפשר לייבא מכל הפרויקט
settings = Settings()


def _validate_production_settings(s: "Settings") -> None:
    """
    FIX-4: בייצור (APP_ENV=production) — לא מאפשרים מפתח JWT ברירת-מחדל/ריק/קצר,
    כדי למנוע זיוף טוקן admin. בפיתוח/בדיקות מסתפקים באזהרה ל-stderr כדי לא לשבור
    הרצה מקומית (שבה אין .env והמפתח הוא ברירת המחדל).
    """
    is_prod = s.APP_ENV.strip().lower() in ("production", "prod")
    insecure = (
        not s.JWT_SECRET
        or s.JWT_SECRET == _DEFAULT_JWT_SECRET
        or len(s.JWT_SECRET) < 32
    )
    if not insecure:
        return

    msg = (
        "JWT_SECRET אינו בטוח (ריק / ברירת-מחדל / קצר מ-32 תווים). "
        "יש להגדיר JWT_SECRET אקראי וארוך במשתני הסביבה לפני עלייה לייצור."
    )
    if is_prod:
        raise RuntimeError(f"[הגדרות ייצור] {msg}")
    import sys
    print(f"[אזהרת הגדרות] {msg}", file=sys.stderr)


_validate_production_settings(settings)
