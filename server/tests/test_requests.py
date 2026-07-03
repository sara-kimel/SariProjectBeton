# -*- coding: utf-8 -*-
"""
בדיקות CRUD ובעלות לבקשות בטון של לקוחות (שלב 2).
דורש: DB beton עם seed (עבור מזהה Purpose תקין).
"""

import pytest
from sqlalchemy import text

PW = "secret123"


@pytest.fixture(autouse=True)
def _clean(db):
    def wipe():
        db.execute(
            text(
                "DELETE FROM OfferMatches WHERE request_id IN "
                "(SELECT request_id FROM ConcreteRequests WHERE customer_id IN "
                " (SELECT id FROM Customers WHERE user_name LIKE 'pytest%'))"
            )
        )
        db.execute(
            text(
                "DELETE FROM ConcreteRequests WHERE customer_id IN "
                "(SELECT id FROM Customers WHERE user_name LIKE 'pytest%')"
            )
        )
        db.execute(text("DELETE FROM Customers WHERE user_name LIKE 'pytest%'"))
        db.execute(text("DELETE FROM Contractors WHERE user_name LIKE 'pytest%'"))
        db.commit()

    wipe()
    yield
    wipe()


def _reg(client, role, user):
    return client.post(f"/auth/register/{role}", json={"user_name": user, "password": PW}).json()


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _purpose_id(db):
    return db.execute(text("SELECT TOP 1 id FROM Purpose ORDER BY id")).scalar()


def test_create_binds_current_user_and_open(client, db):
    pid = _purpose_id(db)
    a = _reg(client, "customer", "pytest_reqA")
    # גוף הבקשה מנסה לזייף customer_id ו-status — השרת מתעלם
    body = {
        "purpose_id": pid, "quantity": 3.0, "address": "רחוב טסט 1",
        "lat": 32.08, "lng": 34.78, "customer_id": 999999, "status": "CLOSED",
    }
    r = client.post("/concrete-requests/", json=body, headers=_auth(a["access_token"]))
    assert r.status_code == 201, r.text
    j = r.json()
    assert j["status"] == "OPEN"
    assert j["customer_id"] == a["user_id"]  # לא 999999


def test_cross_customer_forbidden(client, db):
    pid = _purpose_id(db)
    a = _reg(client, "customer", "pytest_reqA")
    b = _reg(client, "customer", "pytest_reqB")
    rid = client.post(
        "/concrete-requests/",
        json={"purpose_id": pid, "quantity": 3.0, "lat": 32.08, "lng": 34.78, "address": "x"},
        headers=_auth(a["access_token"]),
    ).json()["request_id"]

    hb = _auth(b["access_token"])
    assert client.get(f"/concrete-requests/{rid}", headers=hb).status_code == 403
    assert client.get(f"/concrete-requests/customer/{a['user_id']}", headers=hb).status_code == 403
    assert client.put(
        f"/concrete-requests/{rid}",
        json={"lat": 32.0, "lng": 34.0, "quantity": 2.0},
        headers=hb,
    ).status_code == 403


def test_edit_and_delete_open(client, db):
    pid = _purpose_id(db)
    a = _reg(client, "customer", "pytest_reqA")
    h = _auth(a["access_token"])
    rid = client.post(
        "/concrete-requests/",
        json={"purpose_id": pid, "quantity": 3.0, "lat": 32.08, "lng": 34.78, "address": "x"},
        headers=h,
    ).json()["request_id"]

    up = client.put(
        f"/concrete-requests/{rid}",
        json={"lat": 32.08, "lng": 34.78, "quantity": 4.5, "address": "מעודכן"},
        headers=h,
    )
    assert up.status_code == 200
    assert float(up.json()["quantity"]) == 4.5

    assert client.delete(f"/concrete-requests/{rid}", headers=h).status_code == 204
    assert client.get(f"/concrete-requests/{rid}", headers=h).status_code == 404


def test_validation_rules(client, db):
    pid = _purpose_id(db)
    a = _reg(client, "customer", "pytest_reqA")
    h = _auth(a["access_token"])
    # כמות <= 0 -> 422
    assert client.post(
        "/concrete-requests/", json={"purpose_id": pid, "quantity": 0, "lat": 32.0, "lng": 34.0}, headers=h
    ).status_code == 422
    # מטרה לא קיימת -> 422
    assert client.post(
        "/concrete-requests/", json={"purpose_id": 999999, "quantity": 3.0, "lat": 32.0, "lng": 34.0}, headers=h
    ).status_code == 422
    # קבלן לא יכול לפתוח בקשה -> 403
    c = _reg(client, "contractor", "pytest_reqC")
    assert client.post(
        "/concrete-requests/",
        json={"purpose_id": pid, "quantity": 3.0, "lat": 32.0, "lng": 34.0},
        headers=_auth(c["access_token"]),
    ).status_code == 403
