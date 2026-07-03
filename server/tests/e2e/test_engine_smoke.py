# -*- coding: utf-8 -*-
"""
בדיקת עשן (smoke) למנוע ההתאמה — זו הבדיקה שמוכיחה שהבסיס חי.
מריצה את הצינור המלא של המנוע על נתוני ה-seed:
    גיאו (R-tree + Haversine) -> סינון מטרה (purpose) -> סינון כמות.

תרחיש (ראו db/seed.py):
  הצעת קבלן: תל אביב (~32.0853, 34.7818), כמות 5.0 מ"ק, מטרה = 'יסודות'
             (מפרט הבטון: ב-30 / S3 / אגרגט 19 מ"מ).
  צפי (שלב 3, סינון מטרה->מפרט OD-2):
    DEMO-A (יסודות, 4.80, ת"א)  -> מתאים
    DEMO-B (יסודות, 4.70, ת"א)  -> מתאים
    DEMO-C (יסודות, 2.00)       -> נפסל בכמות (<4.5)
    DEMO-D (רצפה,   4.80)       -> נפסל במפרט (רצפה דורשת אגרגט 25 מ"מ; הפנייה 19 מ"מ)
    DEMO-E (יסודות, 4.80, חיפה) -> נפסל בגיאו (>10 ק"מ)

דורש: DB beton עם seed טעון (python db/seed.py).
"""

from sqlalchemy import text

# מיובא כמודול (ולא `from ... import TestService`) כדי ש-pytest לא ינסה
# לאסוף את המחלקה TestService (שם שמתחיל ב-Test) כמחלקת בדיקות.
import service.contractor_matching_controller as matching_pipeline


def _addr_prefixes(results):
    return [str(r.get("address") or "") for r in results]


def test_engine_returns_reasonable_candidates(db):
    # מזהי מטרה + סוג-בטון עבור 'יסודות' (מזהים דינמיים -> נשלפים מה-DB)
    purpose_id = db.execute(
        text("SELECT id FROM Purpose WHERE Purpose = :p"), {"p": "יסודות"}
    ).scalar()
    assert purpose_id is not None, "seed חסר: מטרת 'יסודות' לא נמצאה"

    concrete_id = db.execute(
        text("SELECT TOP 1 id FROM Concrete_type WHERE Purpose_id = :pid"),
        {"pid": purpose_id},
    ).scalar()
    assert concrete_id is not None, "seed חסר: אין Concrete_type למטרת 'יסודות'"

    offer = {
        "lat": 32.0853,
        "lng": 34.7818,
        "concrete_id": concrete_id,
        "quantity": 5.0,
    }

    results = matching_pipeline.TestService(db).run_pipeline(offer)

    # --- מבנה התוצאה ---
    assert isinstance(results, list)
    assert len(results) >= 2, f"ציפינו ל->=2 מועמדים, קיבלנו {len(results)}"

    addrs = _addr_prefixes(results)

    # --- מי אמור לעבור ---
    assert any(a.startswith("DEMO-A") for a in addrs), "DEMO-A היה אמור להתאים"
    assert any(a.startswith("DEMO-B") for a in addrs), "DEMO-B היה אמור להתאים"

    # --- מי אמור להיפסל ---
    assert not any(a.startswith("DEMO-C") for a in addrs), "DEMO-C היה אמור להיפסל בכמות"
    assert not any(a.startswith("DEMO-D") for a in addrs), "DEMO-D היה אמור להיפסל במפרט (גודל אבן)"
    assert not any(a.startswith("DEMO-E") for a in addrs), "DEMO-E היה אמור להיפסל בגיאו"

    # --- תכונות כל מועמד ---
    for r in results:
        assert int(r["purpose_id"]) == int(purpose_id)
        assert 4.5 <= float(r["quantity"]) <= 5.0
        assert "score" in r and "distance_m" in r
        assert float(r["distance_m"]) <= 10000  # בתוך הרדיוס
