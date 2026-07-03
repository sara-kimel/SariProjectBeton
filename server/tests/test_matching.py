# -*- coding: utf-8 -*-
"""
בדיקות מנוע ההתאמה (שלב 3), ברמת הפונקציות (ללא HTTP):
  - סינון מטרה->מפרט (OD-2): חוזק >= / סומך == / גודל-אבן ==.
  - נפילה חיננית: מטרה ללא מיפוי req_* -> התאמה לפי מטרה בלבד.
  - סינון כמות (OD-4): request.qty בטווח [0.9*offer.qty, offer.qty].
  - סינון גיאוגרפי (רדיוס 10 ק"מ).
  - כיוון הפוך (SPEC §5.6): בקשה מוצאת פניות פתוחות; פנייה שפגה לא נמצאת.

מכניס נתונים מבוקרים ל-DB beton (מסומנים 'PYTEST3'/'pytest3') ומנקה בסוף.
דורש: DB beton עם seed (עבור ערכי ה-lookup: חוזקים/סומך/גודל-אבן).
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from service.matching_engine_service import (
    match_requests_for_offer,
    match_offers_for_request,
)

TA = (32.0853, 34.7818)    # תל אביב
FAR = (32.7940, 34.9896)   # חיפה (~80 ק"מ מת"א)


# ---------------------------------------------------------------------------
# עזרי הכנסת נתונים
# ---------------------------------------------------------------------------
def _scalar(db, sql, **p):
    return db.execute(text(sql), p).scalar()


def _wipe(db):
    db.execute(text(
        "DELETE FROM OfferMatches WHERE offer_id IN "
        "(SELECT request_id FROM ContractorConcreteRequests WHERE address LIKE 'PYTEST3-%') "
        "OR request_id IN (SELECT request_id FROM ConcreteRequests WHERE address LIKE 'PYTEST3-%')"
    ))
    db.execute(text("DELETE FROM ContractorConcreteRequests WHERE address LIKE 'PYTEST3-%'"))
    db.execute(text("DELETE FROM ConcreteRequests WHERE address LIKE 'PYTEST3-%'"))
    db.execute(text(
        "DELETE FROM ConcreteRequests WHERE purpose_id IN "
        "(SELECT id FROM Purpose WHERE Purpose LIKE 'PYTEST3%')"
    ))
    db.execute(text("DELETE FROM Concrete_type WHERE Purpose_id IN (SELECT id FROM Purpose WHERE Purpose LIKE 'PYTEST3%')"))
    db.execute(text("DELETE FROM Purpose WHERE Purpose LIKE 'PYTEST3%'"))
    db.execute(text("DELETE FROM Contractors WHERE user_name LIKE 'pytest3%'"))
    db.execute(text("DELETE FROM Customers WHERE user_name LIKE 'pytest3%'"))
    db.commit()


@pytest.fixture()
def env(db):
    """מכין ערכי lookup + לקוח/קבלן, ומנקה נתוני-בדיקה לפני ואחרי."""
    _wipe(db)

    ids = {
        "b20": _scalar(db, "SELECT id FROM Strength WHERE strength=:s", s="ב-20"),
        "b30": _scalar(db, "SELECT id FROM Strength WHERE strength=:s", s="ב-30"),
        "b40": _scalar(db, "SELECT id FROM Strength WHERE strength=:s", s="ב-40"),
        "S2": _scalar(db, "SELECT id FROM Reliant WHERE Reliant=:s", s="S2"),
        "S3": _scalar(db, "SELECT id FROM Reliant WHERE Reliant=:s", s="S3"),
        "agg19": _scalar(db, "SELECT id FROM Stone_size WHERE Stone_size=:s", s='אגרגט 19 מ"מ'),
        "agg25": _scalar(db, "SELECT id FROM Stone_size WHERE Stone_size=:s", s='אגרגט 25 מ"מ'),
    }
    assert all(v is not None for v in ids.values()), "seed חסר ערכי lookup"

    ids["cust"] = _scalar(
        db, "INSERT INTO Customers (user_name, password_hash) OUTPUT INSERTED.id VALUES (:u,'x')",
        u="pytest3_cust",
    )
    ids["con"] = _scalar(
        db, "INSERT INTO Contractors (user_name, password_hash) OUTPUT INSERTED.id VALUES (:u,'x')",
        u="pytest3_con",
    )
    db.commit()
    yield db, ids
    _wipe(db)


def _mk_purpose(db, name, req_str=None, req_rel=None, req_stone=None):
    return _scalar(
        db,
        "INSERT INTO Purpose (Purpose, req_strength_id, req_reliant_id, req_stone_size_id) "
        "OUTPUT INSERTED.id VALUES (:p,:s,:r,:st)",
        p=name, s=req_str, r=req_rel, st=req_stone,
    )


def _mk_concrete(db, purpose_id, str_id, rel_id, stone_id):
    return _scalar(
        db,
        "INSERT INTO Concrete_type (strength_id, Reliant_id, Stone_size_id, Purpose_id) "
        "OUTPUT INSERTED.id VALUES (:s,:r,:st,:p)",
        s=str_id, r=rel_id, st=stone_id, p=purpose_id,
    )


def _mk_request(db, cust, purpose_id, qty, lat, lng, tag, days_ago=0):
    return _scalar(
        db,
        "INSERT INTO ConcreteRequests (customer_id, purpose_id, quantity, address, lat, lng, [date], [status]) "
        "OUTPUT INSERTED.request_id VALUES (:c,:p,:q,:a,:lat,:lng, CAST(DATEADD(day,:d,GETDATE()) AS DATE),'OPEN')",
        c=cust, p=purpose_id, q=qty, a=f"PYTEST3-{tag}", lat=lat, lng=lng, d=-int(days_ago),
    )


def _mk_offer(db, con, concrete_id, qty, lat, lng, tag, expiry):
    return _scalar(
        db,
        "INSERT INTO ContractorConcreteRequests (contractor_id, concrete_id, quantity, address, lat, lng, expiry_time, [status]) "
        "OUTPUT INSERTED.request_id VALUES (:c,:ct,:q,:a,:lat,:lng,:exp,'OPEN')",
        c=con, ct=concrete_id, q=qty, a=f"PYTEST3-{tag}", lat=lat, lng=lng, exp=expiry,
    )


def _addrs(results):
    return [str(r.get("address") or "") for r in results]


# ---------------------------------------------------------------------------
# OD-2 — סינון מטרה->מפרט (חוזק)
# ---------------------------------------------------------------------------
def test_od2_strength_filter(env):
    db, ids = env
    # מטרה הדורשת ב-30 (sort 2) / S3 / אגרגט 19
    pid = _mk_purpose(db, "PYTEST3_STR", ids["b30"], ids["S3"], ids["agg19"])
    req = _mk_request(db, ids["cust"], pid, 5.0, *TA, "STR")
    db.commit()

    ct_weak = _mk_concrete(db, pid, ids["b20"], ids["S3"], ids["agg19"])   # ב-20 < ב-30
    ct_ok = _mk_concrete(db, pid, ids["b30"], ids["S3"], ids["agg19"])     # ב-30 == נדרש
    ct_strong = _mk_concrete(db, pid, ids["b40"], ids["S3"], ids["agg19"]) # ב-40 > ב-30
    db.commit()

    def match(ct):
        res = match_requests_for_offer(db, {"lat": TA[0], "lng": TA[1], "concrete_id": ct, "quantity": 5.0})
        return any(a.startswith("PYTEST3-STR") for a in _addrs(res))

    assert match(ct_weak) is False, "פנייה חלשה מהנדרש לא אמורה להתאים"
    assert match(ct_ok) is True, "פנייה בחוזק הנדרש אמורה להתאים"
    assert match(ct_strong) is True, "פנייה חזקה יותר אמורה להתאים"


# ---------------------------------------------------------------------------
# OD-2 — סומך/גודל-אבן חייבים להיות שווים אם המטרה מגדירה
# ---------------------------------------------------------------------------
def test_od2_reliant_and_stone_equality(env):
    db, ids = env
    pid = _mk_purpose(db, "PYTEST3_EQ", ids["b30"], ids["S3"], ids["agg19"])
    _mk_request(db, ids["cust"], pid, 5.0, *TA, "EQ")
    db.commit()

    ct_bad_rel = _mk_concrete(db, pid, ids["b30"], ids["S2"], ids["agg19"])    # סומך שונה
    ct_bad_stone = _mk_concrete(db, pid, ids["b30"], ids["S3"], ids["agg25"])  # גודל-אבן שונה
    ct_good = _mk_concrete(db, pid, ids["b40"], ids["S3"], ids["agg19"])       # חזק יותר, אותו סומך/אבן
    db.commit()

    def match(ct):
        res = match_requests_for_offer(db, {"lat": TA[0], "lng": TA[1], "concrete_id": ct, "quantity": 5.0})
        return any(a.startswith("PYTEST3-EQ") for a in _addrs(res))

    assert match(ct_bad_rel) is False, "סומך שונה -> לא מתאים"
    assert match(ct_bad_stone) is False, "גודל-אבן שונה -> לא מתאים"
    assert match(ct_good) is True, "חוזק גבוה + סומך/אבן תואמים -> מתאים"


# ---------------------------------------------------------------------------
# נפילה חיננית — מטרה ללא מיפוי req_* -> התאמה לפי מטרה בלבד
# ---------------------------------------------------------------------------
def test_fallback_purpose_only(env):
    db, ids = env
    pid = _mk_purpose(db, "PYTEST3_NOMAP")                    # ללא req_*
    other = _mk_purpose(db, "PYTEST3_OTHER")                  # מטרה אחרת (גם ללא מיפוי)
    _mk_request(db, ids["cust"], pid, 5.0, *TA, "FB")
    db.commit()

    ct_same_purpose = _mk_concrete(db, pid, ids["b20"], ids["S2"], ids["agg25"])    # מטרה תואמת, מפרט "חלש"
    ct_other_purpose = _mk_concrete(db, other, ids["b40"], ids["S3"], ids["agg19"]) # מטרה אחרת
    db.commit()

    def match(ct):
        res = match_requests_for_offer(db, {"lat": TA[0], "lng": TA[1], "concrete_id": ct, "quantity": 5.0})
        return any(a.startswith("PYTEST3-FB") for a in _addrs(res))

    assert match(ct_same_purpose) is True, "מטרה ללא מיפוי -> התאמה לפי מטרה בלבד (זהה)"
    assert match(ct_other_purpose) is False, "מטרה שונה -> לא מתאים בנפילה החיננית"


# ---------------------------------------------------------------------------
# סינון כמות (OD-4)
# ---------------------------------------------------------------------------
def test_quantity_filter(env):
    db, ids = env
    pid = _mk_purpose(db, "PYTEST3_QTY", ids["b30"], ids["S3"], ids["agg19"])
    ct = _mk_concrete(db, pid, ids["b30"], ids["S3"], ids["agg19"])
    _mk_request(db, ids["cust"], pid, 1.0, *TA, "QTY-SMALL")   # 1.0 < 0.9*8 => נפסל
    _mk_request(db, ids["cust"], pid, 7.5, *TA, "QTY-OK")      # 7.5 בטווח [7.2,8] => עובר
    db.commit()

    res = match_requests_for_offer(db, {"lat": TA[0], "lng": TA[1], "concrete_id": ct, "quantity": 8.0})
    addrs = _addrs(res)
    assert any(a.startswith("PYTEST3-QTY-OK") for a in addrs), "בקשה 7.5 מול 8 אמורה לעבור"
    assert not any(a.startswith("PYTEST3-QTY-SMALL") for a in addrs), "בקשה 1 מול 8 אמורה להיפסל"


# ---------------------------------------------------------------------------
# סינון גיאוגרפי (10 ק"מ)
# ---------------------------------------------------------------------------
def test_geo_filter(env):
    db, ids = env
    pid = _mk_purpose(db, "PYTEST3_GEO", ids["b30"], ids["S3"], ids["agg19"])
    ct = _mk_concrete(db, pid, ids["b30"], ids["S3"], ids["agg19"])
    _mk_request(db, ids["cust"], pid, 5.0, *TA, "GEO-NEAR")
    _mk_request(db, ids["cust"], pid, 5.0, *FAR, "GEO-FAR")
    db.commit()

    res = match_requests_for_offer(db, {"lat": TA[0], "lng": TA[1], "concrete_id": ct, "quantity": 5.0})
    addrs = _addrs(res)
    assert any(a.startswith("PYTEST3-GEO-NEAR") for a in addrs)
    assert not any(a.startswith("PYTEST3-GEO-FAR") for a in addrs), "בקשה מעל 10 ק\"מ אמורה להיפסל"


# ---------------------------------------------------------------------------
# כיוון הפוך (SPEC §5.6): בקשה מוצאת פניות פתוחות; פנייה שפגה לא נמצאת.
# ---------------------------------------------------------------------------
def test_reverse_match_and_expiry(env):
    db, ids = env
    pid = _mk_purpose(db, "PYTEST3_REV", ids["b30"], ids["S3"], ids["agg19"])
    ct = _mk_concrete(db, pid, ids["b30"], ids["S3"], ids["agg19"])
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)  # נאיבי-UTC לאחסון בעמודת DATETIME
    future = now_utc + timedelta(hours=5)
    past = now_utc - timedelta(hours=5)
    _mk_offer(db, ids["con"], ct, 8.0, *TA, "REV-OPEN", future)     # פתוחה + תקפה
    _mk_offer(db, ids["con"], ct, 8.0, *TA, "REV-EXPIRED", past)    # פגה
    db.commit()

    request_dict = {"lat": TA[0], "lng": TA[1], "purpose_id": pid, "quantity": 7.5}
    res = match_offers_for_request(db, request_dict)
    addrs = _addrs(res)
    assert any(a.startswith("PYTEST3-REV-OPEN") for a in addrs), "פנייה פתוחה ותואמת אמורה להימצא"
    assert not any(a.startswith("PYTEST3-REV-EXPIRED") for a in addrs), "פנייה שפגה לא אמורה להימצא"
