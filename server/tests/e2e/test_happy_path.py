# -*- coding: utf-8 -*-
"""
מסלול מאושר מלא (שלב 4), מקצה-לקצה מול ה-FastAPI:
הרשמה → בקשה → פנייה (/send/) → נוצרת התאמה + התראת MATCH_FOUND ללקוח →
הלקוח מאשר → Offer/Request=CLOSED, Match=ACCEPTED → התראות (לקבלן + נתפסה) →
שני הצדדים רואים את פרטי הקשר (טלפון). + בדיקת מרכז ההתראות (unread/read).
דורש: DB beton עם seed (מטרת 'יסודות' + Concrete_type תואם).
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

PW = "secret123"
TA_LAT, TA_LNG = 32.0853, 34.7818
CUST_PHONE = "050-4440000"
CON_PHONE = "052-4440000"


@pytest.fixture(autouse=True)
def _clean(db):
    def wipe():
        db.execute(text(
            "DELETE FROM Notifications WHERE user_id IN "
            "(SELECT id FROM Customers WHERE user_name LIKE 'pytest4h%') "
            "OR user_id IN (SELECT id FROM Contractors WHERE user_name LIKE 'pytest4h%')"
        ))
        db.execute(text("DELETE FROM OfferMatches WHERE offer_id IN "
                        "(SELECT request_id FROM ContractorConcreteRequests WHERE address LIKE 'PYTEST4H-%') "
                        "OR request_id IN (SELECT request_id FROM ConcreteRequests WHERE address LIKE 'PYTEST4H-%')"))
        db.execute(text("DELETE FROM ContractorConcreteRequests WHERE address LIKE 'PYTEST4H-%'"))
        db.execute(text("DELETE FROM ConcreteRequests WHERE address LIKE 'PYTEST4H-%'"))
        db.execute(text("DELETE FROM Contractors WHERE user_name LIKE 'pytest4h%'"))
        db.execute(text("DELETE FROM Customers WHERE user_name LIKE 'pytest4h%'"))
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


def test_full_happy_path(client, db):
    pid = db.execute(text("SELECT id FROM Purpose WHERE Purpose='יסודות'")).scalar()
    cid = db.execute(text("SELECT TOP 1 id FROM Concrete_type WHERE Purpose_id=:p ORDER BY id"), {"p": pid}).scalar()

    cust = _reg(client, "customer", "pytest4h_C")
    con = _reg(client, "contractor", "pytest4h_K")
    # קובעים טלפונים דטרמיניסטית (לבדיקת חשיפת פרטי קשר)
    db.execute(text("UPDATE Customers SET phone=:p WHERE id=:i"), {"p": CUST_PHONE, "i": cust["user_id"]})
    db.execute(text("UPDATE Contractors SET phone=:p WHERE id=:i"), {"p": CON_PHONE, "i": con["user_id"]})
    db.commit()

    # לקוח יוצר בקשה
    rr = client.post(
        "/concrete-requests/",
        json={"purpose_id": pid, "quantity": 4.8, "lat": TA_LAT, "lng": TA_LNG, "address": "PYTEST4H-req"},
        headers=_auth(cust["access_token"]),
    )
    assert rr.status_code == 201, rr.text
    request_id = rr.json()["request_id"]

    # קבלן מריץ /send/ → נוצרת התאמה + התראה ללקוח
    sr = client.post(
        "/contractor-offers/send/",
        json={"concrete_id": cid, "quantity": 5.0, "lat": TA_LAT, "lng": TA_LNG,
              "price": "600", "address": "PYTEST4H-offer", "expiry_time": _future_iso()},
        headers=_auth(con["access_token"]),
    )
    assert sr.status_code == 200, sr.text
    offer_id = sr.json()["offer_id"]

    # ללקוח יש התראת MATCH_FOUND, unread>=1
    uc = client.get("/notifications/unread-count", headers=_auth(cust["access_token"]))
    assert uc.status_code == 200 and uc.json()["unread"] >= 1
    notes = client.get("/notifications/", headers=_auth(cust["access_token"])).json()
    assert any(n["type"] == "MATCH_FOUND" for n in notes)

    # לפני אישור — הטלפון של הקבלן מוסתר
    mr = client.get(f"/matches/request/{request_id}", headers=_auth(cust["access_token"])).json()
    ours = [m for m in mr if m["offer_id"] == offer_id]
    assert len(ours) == 1
    match_id = ours[0]["id"]
    assert ours[0]["contractor_phone"] is None  # לא נחשף לפני סגירה

    # הלקוח מאשר
    acc = client.post(f"/matches/{match_id}/accept", headers=_auth(cust["access_token"]))
    assert acc.status_code == 200, acc.text
    assert acc.json()["contact_phone"] == CON_PHONE   # טלפון הקבלן נחשף ללקוח

    # הפנייה נסגרה
    got = client.get(f"/contractor-offers/{offer_id}", headers=_auth(con["access_token"]))
    assert got.status_code == 200 and got.json()["status"] == "CLOSED"

    # הקבלן רואה את הלקוח שאישר + טלפון הלקוח (נחשף לאחר סגירה)
    mo = client.get(f"/matches/offer/{offer_id}", headers=_auth(con["access_token"])).json()
    acc_match = [m for m in mo if m["request_id"] == request_id][0]
    assert acc_match["status"] == "ACCEPTED"
    assert acc_match["customer_phone"] == CUST_PHONE

    # לקבלן נכנסה התראת CUSTOMER_ACCEPTED
    con_notes = client.get("/notifications/", headers=_auth(con["access_token"])).json()
    assert any(n["type"] == "CUSTOMER_ACCEPTED" for n in con_notes)

    # סימון התראה כנקראה מוריד את המונה
    before = client.get("/notifications/unread-count", headers=_auth(cust["access_token"])).json()["unread"]
    first_id = notes[0]["id"]
    r_read = client.post(f"/notifications/{first_id}/read", headers=_auth(cust["access_token"]))
    assert r_read.status_code == 200 and r_read.json()["is_read"] is True
    after = client.get("/notifications/unread-count", headers=_auth(cust["access_token"])).json()["unread"]
    assert after == before - 1


def test_accept_other_customers_match_forbidden(client, db):
    pid = db.execute(text("SELECT id FROM Purpose WHERE Purpose='יסודות'")).scalar()
    cid = db.execute(text("SELECT TOP 1 id FROM Concrete_type WHERE Purpose_id=:p ORDER BY id"), {"p": pid}).scalar()

    cust = _reg(client, "customer", "pytest4h_C1")
    other = _reg(client, "customer", "pytest4h_C2")
    con = _reg(client, "contractor", "pytest4h_K1")

    client.post(
        "/concrete-requests/",
        json={"purpose_id": pid, "quantity": 4.8, "lat": TA_LAT, "lng": TA_LNG, "address": "PYTEST4H-req2"},
        headers=_auth(cust["access_token"]),
    )
    sr = client.post(
        "/contractor-offers/send/",
        json={"concrete_id": cid, "quantity": 5.0, "lat": TA_LAT, "lng": TA_LNG,
              "address": "PYTEST4H-offer2", "expiry_time": _future_iso()},
        headers=_auth(con["access_token"]),
    )
    offer_id = sr.json()["offer_id"]
    match_id = client.get(f"/matches/offer/{offer_id}", headers=_auth(con["access_token"])).json()[0]["id"]

    # לקוח אחר מנסה לאשר את ההתאמה → 403
    bad = client.post(f"/matches/{match_id}/accept", headers=_auth(other["access_token"]))
    assert bad.status_code == 403
