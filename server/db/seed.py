# -*- coding: utf-8 -*-
"""
זריעת נתונים ל-Beton (שלב 0) — בפייתון, בטוח ל-Unicode (עברית).

מדוע פייתון ולא sqlcmd:
    sqlcmd קורא קובצי .sql בקוד-פייג' של מערכת ההפעלה (כאן cp1255) ולכן
    משבש טקסט עברי בעת ה-INSERT. הרצה דרך SQLAlchemy/pyodbc שומרת על ה-Unicode
    כראוי (נבדק). לכן זהו קובץ ה-seed הרשמי (במקום db/seed.sql).

מה עושה:
    איפוס מלא של טבלאות ה-lookup ונתוני הדמו, ואז זריעה מחדש נקייה
    (אידמפוטנטי — אפשר להריץ שוב ושוב).

*** ערכי הדומיין (חוזקים/סומך/גודל-אבן/מיפוי מטרה->מפרט) הם הצעה סבירה
    לאימות מול המשתמש — ראו סיכום שלב 0. ***

הרצה (מתוך server/, בתוך ה-venv):
    python db/seed.py
"""

import os
import sys

# הוספת server/ ל-sys.path כדי לייבא את database/config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text          # noqa: E402
from database import engine          # noqa: E402
from service.auth_service import hash_password  # noqa: E402

# סיסמאות דמו (שלב 1) — נשמרות מוצפנות (bcrypt). לתיעוד/בדיקות בלבד.
DEMO_PASSWORD = "demo123"
# מנהל ראשוני: (user_name, סיסמה זמנית, first_name, last_name)
ADMIN_SEED = ("admin", "Admin!2026", "מנהל", "ראשי")


# --- ערכי lookup ---
STRENGTHS = [("ב-20", 1), ("ב-30", 2), ("ב-40", 3), ("ב-50", 4)]
RELIANTS = ["S1", "S2", "S3", "S4", "S5"]
STONES = ['אגרגט 9.5 מ"מ', 'אגרגט 19 מ"מ', 'אגרגט 25 מ"מ']

# מטרה -> מפרט נדרש (חוזק / סומך / גודל-אבן)
# הערה (שלב 3, OD-2): 'רצפה' מוגדרת עם גודל-אבן שונה מ'יסודות' (25 מ"מ מול 19 מ"מ)
# כדי שהמטרות יהיו נבדלות במפרט — כך מנוע ההתאמה (מטרה->מפרט) מסנן ביניהן לפי
# מפרט פיזי ולא לפי שוויון מזהה-מטרה.
PURPOSES = [
    ("יסודות",   "ב-30", "S3", 'אגרגט 19 מ"מ'),
    ("רצפה",     "ב-30", "S3", 'אגרגט 25 מ"מ'),
    ("גדר",      "ב-20", "S2", 'אגרגט 19 מ"מ'),
    ("שביל",     "ב-20", "S2", 'אגרגט 9.5 מ"מ'),
    ("קיר תומך", "ב-40", "S3", 'אגרגט 19 מ"מ'),
    ("עמודים",   "ב-40", "S4", 'אגרגט 9.5 מ"מ'),
]

# צירופי בטון (אחד לכל מטרה) — הצעת קבלן מפנה ל-Concrete_type.id.
# תואם למפרט המטרה כך שמוצר של מטרה מסוימת עומד במפרט אותה מטרה.
CONCRETE_TYPES = [
    ("יסודות", "ב-30", "S3", 'אגרגט 19 מ"מ'),
    ("רצפה",   "ב-30", "S3", 'אגרגט 25 מ"מ'),
    ("גדר",    "ב-20", "S2", 'אגרגט 19 מ"מ'),
]

CUSTOMERS = [
    ("דנה",  "לוי",    "dana",  "demo123", "050-1111111"),
    ("יוסי", "כהן",    "yossi", "demo123", "050-2222222"),
    ("מור",  "ישראלי", "mor",   "demo123", "050-3333333"),
]

CONTRACTORS = [
    ("אבי", "בנאי", "avi_con", "demo123", "052-9999999"),
]

# בקשות דמו (status=OPEN). תרחיש בדיקה למנוע:
#   הצעת קבלן: ת"א (~32.0853, 34.7818), כמות 5.0 מ"ק, מטרה=יסודות
#     DEMO-A יסודות 4.80 ת"א  ~1ק"מ  -> מתאים
#     DEMO-B יסודות 4.70 ת"א  ~2ק"מ  -> מתאים
#     DEMO-C יסודות 2.00 ת"א         -> נופל בכמות (<4.5)
#     DEMO-D רצפה   4.80 ת"א         -> נופל במטרה
#     DEMO-E יסודות 4.80 חיפה ~80ק"מ -> נופל בגיאו
# שדות: user_name, purpose, qty, address, lat, lng, days_ago
REQUESTS = [
    ("dana",  "יסודות", 4.80, "DEMO-A דיזנגוף 100, תל אביב", 32.090000, 34.790000, 3),
    ("yossi", "יסודות", 4.70, "DEMO-B אלנבי 50, תל אביב",    32.070000, 34.770000, 1),
    ("mor",   "יסודות", 2.00, "DEMO-C הרצל 10, תל אביב",      32.085000, 34.782000, 0),
    ("dana",  "רצפה",   4.80, "DEMO-D רוטשילד 1, תל אביב",    32.086000, 34.781000, 0),
    ("yossi", "יסודות", 4.80, "DEMO-E הנמל 5, חיפה",          32.794000, 34.989600, 0),
]

# סדר מחיקה בטוח מבחינת מפתחות זרים (בנים -> הורים).
# OfferMatches (שלב 3) ו-Notifications (שלב 4) נמחקות ראשונות — OfferMatches
# מפנה ב-FK ל-ContractorConcreteRequests/ConcreteRequests/Customers.
WIPE_ORDER = [
    "OfferMatches",
    "Notifications",
    "ContractorConcreteRequests",
    "ConcreteRequests",
    "Concrete_type",
    "Purpose",
    "Strength",
    "Reliant",
    "Stone_size",
    "Contractors",
    "Customers",
    "Admins",
]


def main():
    with engine.begin() as c:
        # --- איפוס ---
        for tbl in WIPE_ORDER:
            c.execute(text(f"DELETE FROM dbo.[{tbl}]"))

        # --- lookups ---
        s_id, r_id, st_id = {}, {}, {}
        for name, order in STRENGTHS:
            s_id[name] = c.execute(
                text("INSERT INTO Strength (strength, sort_order) OUTPUT INSERTED.id VALUES (:s, :o)"),
                {"s": name, "o": order},
            ).scalar()
        for name in RELIANTS:
            r_id[name] = c.execute(
                text("INSERT INTO Reliant (Reliant) OUTPUT INSERTED.id VALUES (:v)"),
                {"v": name},
            ).scalar()
        for name in STONES:
            st_id[name] = c.execute(
                text("INSERT INTO Stone_size (Stone_size) OUTPUT INSERTED.id VALUES (:v)"),
                {"v": name},
            ).scalar()

        # --- purposes + מיפוי מפרט ---
        p_id = {}
        for pu, sname, rname, stname in PURPOSES:
            p_id[pu] = c.execute(
                text(
                    "INSERT INTO Purpose (Purpose, req_strength_id, req_reliant_id, req_stone_size_id) "
                    "OUTPUT INSERTED.id VALUES (:p, :s, :r, :st)"
                ),
                {"p": pu, "s": s_id[sname], "r": r_id[rname], "st": st_id[stname]},
            ).scalar()

        # --- concrete types ---
        for pu, sname, rname, stname in CONCRETE_TYPES:
            c.execute(
                text(
                    "INSERT INTO Concrete_type (strength_id, Reliant_id, Stone_size_id, Purpose_id) "
                    "VALUES (:s, :r, :st, :p)"
                ),
                {"s": s_id[sname], "r": r_id[rname], "st": st_id[stname], "p": p_id[pu]},
            )

        # --- admin (מנהל ראשוני) ---
        admin_un, admin_pw, admin_fn, admin_ln = ADMIN_SEED
        c.execute(
            text(
                "INSERT INTO Admins (user_name, password_hash, first_name, last_name) "
                "VALUES (:un, :ph, :fn, :ln)"
            ),
            {"un": admin_un, "ph": hash_password(admin_pw), "fn": admin_fn, "ln": admin_ln},
        )

        # --- customers (סיסמה מוצפנת = DEMO_PASSWORD) ---
        demo_hash = hash_password(DEMO_PASSWORD)
        cust_id = {}
        for fn, ln, un, _pw, ph in CUSTOMERS:
            cust_id[un] = c.execute(
                text(
                    "INSERT INTO Customers (first_name, last_name, user_name, password_hash, phone) "
                    "OUTPUT INSERTED.id VALUES (:fn, :ln, :un, :hash, :ph)"
                ),
                {"fn": fn, "ln": ln, "un": un, "hash": demo_hash, "ph": ph},
            ).scalar()

        # --- contractors (סיסמה מוצפנת = DEMO_PASSWORD) ---
        for fn, ln, un, _pw, ph in CONTRACTORS:
            c.execute(
                text(
                    "INSERT INTO Contractors (first_name, last_name, user_name, password_hash, phone) "
                    "OUTPUT INSERTED.id VALUES (:fn, :ln, :un, :hash, :ph)"
                ),
                {"fn": fn, "ln": ln, "un": un, "hash": demo_hash, "ph": ph},
            ).scalar()

        # --- requests (status=OPEN) ---
        for un, pu, qty, addr, lat, lng, days_ago in REQUESTS:
            c.execute(
                text(
                    "INSERT INTO ConcreteRequests "
                    "(customer_id, purpose_id, quantity, address, lat, lng, [date], [status]) "
                    "VALUES (:cid, :pid, :q, :addr, :lat, :lng, "
                    "CAST(DATEADD(day, :d, GETDATE()) AS DATE), 'OPEN')"
                ),
                {
                    "cid": cust_id[un],
                    "pid": p_id[pu],
                    "q": qty,
                    "addr": addr,
                    "lat": lat,
                    "lng": lng,
                    "d": -int(days_ago),
                },
            )

    print("Seed complete (Unicode-safe): "
          f"{len(STRENGTHS)} strengths, {len(RELIANTS)} reliants, {len(STONES)} stones, "
          f"{len(PURPOSES)} purposes, {len(CONCRETE_TYPES)} concrete-types, "
          f"1 admin, {len(CUSTOMERS)} customers, {len(CONTRACTORS)} contractors, "
          f"{len(REQUESTS)} requests.")
    print(f"  admin login: user='{ADMIN_SEED[0]}' password='{ADMIN_SEED[1]}' (temporary)")
    print(f"  demo customers/contractors password: '{DEMO_PASSWORD}'")


if __name__ == "__main__":
    main()
