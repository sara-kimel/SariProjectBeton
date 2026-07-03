# -*- coding: utf-8 -*-
"""
בדיקות אימות והרשאות (שלב 1).
דורש: DB beton עם seed טעון (python db/seed.py) — עבור משתמש admin הראשוני.
המשתמשים שנוצרים בבדיקות מתחילים ב-'pytest' ומנוקים לפני/אחרי כל בדיקה.
"""

import pytest
from sqlalchemy import text

CUST_USER = "pytest_cust"
CUST_PW = "secret123"

# פרטי המנהל הראשוני מה-seed (db/seed.py -> ADMIN_SEED)
ADMIN_USER = "admin"
ADMIN_PW = "Admin!2026"


@pytest.fixture(autouse=True)
def _clean_test_users(db):
    """מנקה משתמשי בדיקה (prefix 'pytest') לפני ואחרי כל בדיקה — סוויטה חוזרת."""

    def wipe():
        db.execute(text("DELETE FROM Customers WHERE user_name LIKE 'pytest%'"))
        db.execute(text("DELETE FROM Contractors WHERE user_name LIKE 'pytest%'"))
        db.commit()

    wipe()
    yield
    wipe()


def _register_customer(client, user_name=CUST_USER, password=CUST_PW):
    return client.post(
        "/auth/register/customer",
        json={"user_name": user_name, "password": password, "first_name": "בדיקה", "phone": "050-0000000"},
    )


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_register_customer_then_duplicate(client):
    r = _register_customer(client)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["role"] == "customer"
    assert body["access_token"]
    # הרשמה חוזרת עם אותו שם משתמש -> 409
    r2 = _register_customer(client)
    assert r2.status_code == 409


def test_login_success_and_wrong_password(client):
    _register_customer(client)
    ok = client.post("/auth/login", json={"user_name": CUST_USER, "password": CUST_PW})
    assert ok.status_code == 200
    assert ok.json()["role"] == "customer"
    assert ok.json()["access_token"]

    bad = client.post("/auth/login", json={"user_name": CUST_USER, "password": "wrong-pass"})
    assert bad.status_code == 401


def test_me_with_and_without_token(client):
    token = _register_customer(client).json()["access_token"]
    me = client.get("/auth/me", headers=_auth(token))
    assert me.status_code == 200
    assert me.json()["role"] == "customer"
    assert me.json()["user_name"] == CUST_USER

    assert client.get("/auth/me").status_code == 401  # ללא טוקן


def test_customer_forbidden_on_admin_endpoint(client):
    token = _register_customer(client).json()["access_token"]
    r = client.post(
        "/admin/users/100/reset-password",
        json={"role": "customer", "new_password": "whatever1"},
        headers=_auth(token),
    )
    assert r.status_code == 403


def test_change_password_then_admin_reset(client):
    reg = _register_customer(client).json()
    token, uid = reg["access_token"], reg["user_id"]

    # שינוי סיסמה ע"י המשתמש
    cp = client.post(
        "/auth/change-password",
        json={"old_password": CUST_PW, "new_password": "newpass123"},
        headers=_auth(token),
    )
    assert cp.status_code == 200
    assert client.post("/auth/login", json={"user_name": CUST_USER, "password": "newpass123"}).status_code == 200
    assert client.post("/auth/login", json={"user_name": CUST_USER, "password": CUST_PW}).status_code == 401

    # מנהל מתחבר ומאפס סיסמה
    admin_login = client.post("/auth/login", json={"user_name": ADMIN_USER, "password": ADMIN_PW})
    assert admin_login.status_code == 200, "צריך seed עם המנהל הראשוני"
    admin_token = admin_login.json()["access_token"]
    assert admin_login.json()["role"] == "admin"

    rr = client.post(
        f"/admin/users/{uid}/reset-password",
        json={"role": "customer", "new_password": "reset1234"},
        headers=_auth(admin_token),
    )
    assert rr.status_code == 200
    # המשתמש מתחבר עם הסיסמה שאופסה
    assert client.post("/auth/login", json={"user_name": CUST_USER, "password": "reset1234"}).status_code == 200


def test_password_is_stored_hashed(client, db):
    _register_customer(client)
    row = db.execute(
        text("SELECT password_hash FROM Customers WHERE user_name = :u"), {"u": CUST_USER}
    ).first()
    assert row is not None
    stored = row[0]
    assert stored, "password_hash ריק"
    assert stored != CUST_PW, "הסיסמה נשמרה בטקסט גלוי!"
    assert stored.startswith("$2"), "לא נראה כמו bcrypt hash"
