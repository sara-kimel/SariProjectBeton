# -*- coding: utf-8 -*-
"""
בדיקות CRUD ובעלות לפניות של קבלנים (שלב 2).
דורש: DB beton עם seed (עבור מזהה Concrete_type תקין).
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

PW = "secret123"


@pytest.fixture(autouse=True)
def _clean(db):
    def wipe():
        db.execute(
            text(
                "DELETE FROM OfferMatches WHERE offer_id IN "
                "(SELECT request_id FROM ContractorConcreteRequests WHERE contractor_id IN "
                " (SELECT id FROM Contractors WHERE user_name LIKE 'pytest%'))"
            )
        )
        db.execute(
            text(
                "DELETE FROM ContractorConcreteRequests WHERE contractor_id IN "
                "(SELECT id FROM Contractors WHERE user_name LIKE 'pytest%')"
            )
        )
        db.execute(text("DELETE FROM Contractors WHERE user_name LIKE 'pytest%'"))
        db.execute(text("DELETE FROM Customers WHERE user_name LIKE 'pytest%'"))
        db.commit()

    wipe()
    yield
    wipe()


def _reg(client, role, user):
    return client.post(f"/auth/register/{role}", json={"user_name": user, "password": PW}).json()


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _concrete_id(db):
    return db.execute(text("SELECT TOP 1 id FROM Concrete_type ORDER BY id")).scalar()


def _future_iso(hours=5):
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()


def _past_iso(hours=5):
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()


def test_create_offer_open_future_and_owner(client, db):
    cid = _concrete_id(db)
    a = _reg(client, "contractor", "pytest_offA")
    body = {
        "concrete_id": cid, "quantity": 5.0, "address": "אתר בנייה",
        "lat": 32.08, "lng": 34.78, "price": "600",
        "expiry_time": _future_iso(), "contractor_id": 999999,
    }
    r = client.post("/contractor-offers/", json=body, headers=_auth(a["access_token"]))
    assert r.status_code == 201, r.text
    j = r.json()
    assert j["status"] == "OPEN"
    assert j["contractor_id"] == a["user_id"]  # לא 999999
    assert j["price"] == "600"  # ללא הכפלה


def test_expiry_in_past_rejected(client, db):
    cid = _concrete_id(db)
    a = _reg(client, "contractor", "pytest_offA")
    r = client.post(
        "/contractor-offers/",
        json={"concrete_id": cid, "quantity": 5.0, "lat": 32.08, "lng": 34.78, "expiry_time": _past_iso()},
        headers=_auth(a["access_token"]),
    )
    assert r.status_code == 422


def test_offers_by_contractor_scoped(client, db):
    cid = _concrete_id(db)
    a = _reg(client, "contractor", "pytest_offA")
    b = _reg(client, "contractor", "pytest_offB")
    client.post(
        "/contractor-offers/",
        json={"concrete_id": cid, "quantity": 5.0, "lat": 32.08, "lng": 34.78, "expiry_time": _future_iso()},
        headers=_auth(a["access_token"]),
    )
    la = client.get(f"/contractor-offers/contractor/{a['user_id']}", headers=_auth(a["access_token"]))
    assert la.status_code == 200 and len(la.json()) == 1
    # קבלן ב' אינו רשאי לראות את הרשימה של א'
    assert client.get(
        f"/contractor-offers/contractor/{a['user_id']}", headers=_auth(b["access_token"])
    ).status_code == 403


def test_customer_cannot_create_offer(client, db):
    cid = _concrete_id(db)
    cust = _reg(client, "customer", "pytest_offCust")
    r = client.post(
        "/contractor-offers/",
        json={"concrete_id": cid, "quantity": 5.0, "lat": 32.08, "lng": 34.78, "expiry_time": _future_iso()},
        headers=_auth(cust["access_token"]),
    )
    assert r.status_code == 403
