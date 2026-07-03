# -*- coding: utf-8 -*-
"""
בדיקת מקצה-לקצה לשלב 3 (מול אפליקציית ה-FastAPI):
  A. טריגר ישיר: לקוח יוצר בקשה -> קבלן מריץ /send/ -> נוצרת OfferMatches,
     הפנייה נשמרת, והמנוע מחזיר סיכום מדורג. נקודות /matches מחזירות את ההתאמה.
  B. טריגר הפוך (SPEC §5.6): קיימת פנייה פתוחה -> לקוח יוצר בקשה תואמת ->
     נוצרת OfferMatches, ונצפית ב-/matches/request.
  C. הרשאות: משתמש זר אינו רואה התאמות של פנייה שאינה שלו.

דורש: DB beton עם seed (מטרת 'יסודות' + Concrete_type תואם).
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

PW = "secret123"
TA_LAT, TA_LNG = 32.0853, 34.7818


@pytest.fixture(autouse=True)
def _clean(db):
    def wipe():
        db.execute(text(
            "DELETE FROM Notifications WHERE user_id IN "
            "(SELECT id FROM Customers WHERE user_name LIKE 'pytest3%') "
            "OR user_id IN (SELECT id FROM Contractors WHERE user_name LIKE 'pytest3%')"
        ))
        db.execute(text(
            "DELETE FROM OfferMatches WHERE offer_id IN "
            "(SELECT request_id FROM ContractorConcreteRequests WHERE contractor_id IN "
            " (SELECT id FROM Contractors WHERE user_name LIKE 'pytest3%')) "
            "OR request_id IN (SELECT request_id FROM ConcreteRequests WHERE customer_id IN "
            " (SELECT id FROM Customers WHERE user_name LIKE 'pytest3%'))"
        ))
        db.execute(text(
            "DELETE FROM ContractorConcreteRequests WHERE contractor_id IN "
            "(SELECT id FROM Contractors WHERE user_name LIKE 'pytest3%')"
        ))
        db.execute(text(
            "DELETE FROM ConcreteRequests WHERE customer_id IN "
            "(SELECT id FROM Customers WHERE user_name LIKE 'pytest3%')"
        ))
        db.execute(text("DELETE FROM Contractors WHERE user_name LIKE 'pytest3%'"))
        db.execute(text("DELETE FROM Customers WHERE user_name LIKE 'pytest3%'"))
        db.commit()

    wipe()
    yield
    wipe()


def _auth(tok):
    return {"Authorization": f"Bearer {tok}"}


def _reg(client, role, user):
    return client.post(f"/auth/register/{role}", json={"user_name": user, "password": PW}).json()


def _future_iso(hours=5):
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()


def _foundations_ids(db):
    pid = db.execute(text("SELECT id FROM Purpose WHERE Purpose = :p"), {"p": "יסודות"}).scalar()
    cid = db.execute(
        text("SELECT TOP 1 id FROM Concrete_type WHERE Purpose_id = :pid ORDER BY id"),
        {"pid": pid},
    ).scalar()
    assert pid and cid, "seed חסר: מטרת 'יסודות' או Concrete_type תואם"
    return pid, cid


# ---------------------------------------------------------------------------
# A. טריגר ישיר — פניית קבלן מוצאת בקשה ויוצרת התאמה
# ---------------------------------------------------------------------------
def test_forward_send_creates_match(client, db):
    pid, cid = _foundations_ids(db)
    cust = _reg(client, "customer", "pytest3_fC")
    con = _reg(client, "contractor", "pytest3_fK")

    # לקוח יוצר בקשה תואמת (יסודות, 4.8 מ"ק, ת"א)
    rr = client.post(
        "/concrete-requests/",
        json={"purpose_id": pid, "quantity": 4.8, "lat": TA_LAT, "lng": TA_LNG, "address": "בקשה"},
        headers=_auth(cust["access_token"]),
    )
    assert rr.status_code == 201, rr.text
    request_id = rr.json()["request_id"]

    # קבלן מריץ /send/ (פנייה תואמת: יסודות, 5.0 מ"ק, ת"א)
    sr = client.post(
        "/contractor-offers/send/",
        json={"concrete_id": cid, "quantity": 5.0, "lat": TA_LAT, "lng": TA_LNG,
              "price": "600", "expiry_time": _future_iso()},
        headers=_auth(con["access_token"]),
    )
    assert sr.status_code == 200, sr.text
    result = sr.json()
    offer_id = result["offer_id"]

    # המנוע מצא לפחות את הבקשה שלנו
    assert result["matched_count"] >= 1
    assert request_id in [m["request_id"] for m in result["matches"]]

    # הפנייה נשמרה ב-DB (חשוב! קודם /send/ לא שמר)
    got = client.get(f"/contractor-offers/{offer_id}", headers=_auth(con["access_token"]))
    assert got.status_code == 200 and (got.json()["status"] or "").upper() == "OPEN"

    # ההתאמה נצפית משני הצדדים
    mo = client.get(f"/matches/offer/{offer_id}", headers=_auth(con["access_token"]))
    assert mo.status_code == 200
    ours = [m for m in mo.json() if m["request_id"] == request_id]
    assert len(ours) == 1 and ours[0]["status"] == "NOTIFIED"
    assert ours[0]["offer_id"] == offer_id

    mr = client.get(f"/matches/request/{request_id}", headers=_auth(cust["access_token"]))
    assert mr.status_code == 200
    assert offer_id in [m["offer_id"] for m in mr.json()]


# ---------------------------------------------------------------------------
# B. טריגר הפוך — בקשת לקוח מוצאת פנייה פתוחה קיימת
# ---------------------------------------------------------------------------
def test_reverse_request_creates_match(client, db):
    pid, cid = _foundations_ids(db)
    cust = _reg(client, "customer", "pytest3_rC")
    con = _reg(client, "contractor", "pytest3_rK")

    # קבלן יוצר פנייה בשמירה בלבד (ללא הרצת מנוע קדימה)
    oo = client.post(
        "/contractor-offers/",
        json={"concrete_id": cid, "quantity": 5.0, "lat": TA_LAT, "lng": TA_LNG,
              "price": "500", "expiry_time": _future_iso()},
        headers=_auth(con["access_token"]),
    )
    assert oo.status_code == 201, oo.text
    offer_id = oo.json()["request_id"]

    # לקוח יוצר בקשה תואמת -> טריגר הפוך יוצר התאמה מול הפנייה
    rr = client.post(
        "/concrete-requests/",
        json={"purpose_id": pid, "quantity": 4.8, "lat": TA_LAT, "lng": TA_LNG, "address": "בקשה"},
        headers=_auth(cust["access_token"]),
    )
    assert rr.status_code == 201, rr.text
    request_id = rr.json()["request_id"]

    # הלקוח רואה את הפנייה שהותאמה
    mr = client.get(f"/matches/request/{request_id}", headers=_auth(cust["access_token"]))
    assert mr.status_code == 200
    hit = [m for m in mr.json() if m["offer_id"] == offer_id]
    assert len(hit) == 1 and hit[0]["status"] == "NOTIFIED"

    # והקבלן רואה אותה מהצד שלו
    mo = client.get(f"/matches/offer/{offer_id}", headers=_auth(con["access_token"]))
    assert mo.status_code == 200
    assert request_id in [m["request_id"] for m in mo.json()]


# ---------------------------------------------------------------------------
# C. הרשאות — קבלן זר אינו רואה התאמות של פנייה שאינה שלו
# ---------------------------------------------------------------------------
def test_matches_ownership_enforced(client, db):
    pid, cid = _foundations_ids(db)
    con = _reg(client, "contractor", "pytest3_oK")
    stranger = _reg(client, "contractor", "pytest3_oX")

    sr = client.post(
        "/contractor-offers/send/",
        json={"concrete_id": cid, "quantity": 5.0, "lat": TA_LAT, "lng": TA_LNG,
              "expiry_time": _future_iso()},
        headers=_auth(con["access_token"]),
    )
    assert sr.status_code == 200, sr.text
    offer_id = sr.json()["offer_id"]

    # קבלן זר -> 403
    forbidden = client.get(f"/matches/offer/{offer_id}", headers=_auth(stranger["access_token"]))
    assert forbidden.status_code == 403
