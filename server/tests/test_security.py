# -*- coding: utf-8 -*-
"""
בדיקות אבטחה/הרשאות/ולידציה (שלב 6, SPEC §13.5): 401 ללא טוקן, IDOR (403),
כפילות שם משתמש (409), ולידציית קלט (422), והפרדת תפקידים.
דורש: DB beton עם seed.
"""

import pytest
from sqlalchemy import text

PW = "secret123"
TA_LAT, TA_LNG = 32.0853, 34.7818


@pytest.fixture(autouse=True)
def _clean(db):
    def wipe():
        db.execute(text(
            "DELETE FROM Notifications WHERE user_id IN "
            "(SELECT id FROM Customers WHERE user_name LIKE 'pytest6%') "
            "OR user_id IN (SELECT id FROM Contractors WHERE user_name LIKE 'pytest6%')"
        ))
        db.execute(text("DELETE FROM OfferMatches WHERE request_id IN "
                        "(SELECT request_id FROM ConcreteRequests WHERE customer_id IN "
                        " (SELECT id FROM Customers WHERE user_name LIKE 'pytest6%'))"))
        db.execute(text("DELETE FROM ConcreteRequests WHERE customer_id IN "
                        "(SELECT id FROM Customers WHERE user_name LIKE 'pytest6%')"))
        db.execute(text("DELETE FROM ContractorConcreteRequests WHERE contractor_id IN "
                        "(SELECT id FROM Contractors WHERE user_name LIKE 'pytest6%')"))
        db.execute(text("DELETE FROM Customers WHERE user_name LIKE 'pytest6%'"))
        db.execute(text("DELETE FROM Contractors WHERE user_name LIKE 'pytest6%'"))
        db.commit()
    wipe()
    yield
    wipe()


def _auth(tok):
    return {"Authorization": f"Bearer {tok}"}


def _reg(client, role, user):
    return client.post(f"/auth/register/{role}", json={"user_name": user, "password": PW}).json()


def _pid(db):
    return db.execute(text("SELECT TOP 1 id FROM Purpose ORDER BY id")).scalar()


def test_unauthenticated_401(client):
    assert client.get("/concrete-requests/").status_code == 401
    assert client.get("/notifications/").status_code == 401
    assert client.get("/admin/stats").status_code == 401
    # טוקן לא תקין
    assert client.get("/notifications/", headers=_auth("garbage.token")).status_code == 401


def test_duplicate_username_409(client):
    _reg(client, "customer", "pytest6_dup")
    r = client.post("/auth/register/customer", json={"user_name": "pytest6_dup", "password": PW})
    assert r.status_code == 409
    # גם חוצה-טבלאות (קבלן עם אותו שם) → 409
    r2 = client.post("/auth/register/contractor", json={"user_name": "pytest6_dup", "password": PW})
    assert r2.status_code == 409


def test_invalid_coordinates_422(client, db):
    pid = _pid(db)
    cust = _reg(client, "customer", "pytest6_coordC")
    r = client.post(
        "/concrete-requests/",
        json={"purpose_id": pid, "quantity": 3.0, "lat": 999, "lng": 34.78},
        headers=_auth(cust["access_token"]),
    )
    assert r.status_code == 422

    con = _reg(client, "contractor", "pytest6_coordK")
    cid = db.execute(text("SELECT TOP 1 id FROM Concrete_type ORDER BY id")).scalar()
    r2 = client.post(
        "/contractor-offers/",
        json={"concrete_id": cid, "quantity": 3.0, "lat": 32.0, "lng": 999},
        headers=_auth(con["access_token"]),
    )
    assert r2.status_code == 422


def test_quantity_out_of_range_422(client, db):
    pid = _pid(db)
    cust = _reg(client, "customer", "pytest6_qtyC")
    # 0 → 422
    assert client.post(
        "/concrete-requests/",
        json={"purpose_id": pid, "quantity": 0, "lat": TA_LAT, "lng": TA_LNG},
        headers=_auth(cust["access_token"]),
    ).status_code == 422
    # חורג מ-DECIMAL(6,2) → 422
    assert client.post(
        "/concrete-requests/",
        json={"purpose_id": pid, "quantity": 100000, "lat": TA_LAT, "lng": TA_LNG},
        headers=_auth(cust["access_token"]),
    ).status_code == 422


def test_idor_request_matches_forbidden(client, db):
    pid = _pid(db)
    a = _reg(client, "customer", "pytest6_A")
    b = _reg(client, "customer", "pytest6_B")
    rid = client.post(
        "/concrete-requests/",
        json={"purpose_id": pid, "quantity": 3.0, "lat": TA_LAT, "lng": TA_LNG, "address": "x"},
        headers=_auth(a["access_token"]),
    ).json()["request_id"]
    # לקוח ב' אינו רשאי לצפות בהתאמות של בקשת לקוח א'
    assert client.get(f"/matches/request/{rid}", headers=_auth(b["access_token"])).status_code == 403


def test_cross_role_forbidden(client, db):
    pid = _pid(db)
    cid = db.execute(text("SELECT TOP 1 id FROM Concrete_type ORDER BY id")).scalar()
    con = _reg(client, "contractor", "pytest6_role_K")
    cust = _reg(client, "customer", "pytest6_role_C")
    # קבלן לא יכול לפתוח בקשת לקוח
    assert client.post(
        "/concrete-requests/",
        json={"purpose_id": pid, "quantity": 3.0, "lat": TA_LAT, "lng": TA_LNG},
        headers=_auth(con["access_token"]),
    ).status_code == 403
    # לקוח לא יכול להריץ /send/ (פעולת קבלן)
    assert client.post(
        "/contractor-offers/send/",
        json={"concrete_id": cid, "quantity": 5.0, "lat": TA_LAT, "lng": TA_LNG,
              "expiry_time": "2099-01-01T00:00:00+00:00"},
        headers=_auth(cust["access_token"]),
    ).status_code == 403
