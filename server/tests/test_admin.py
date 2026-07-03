# -*- coding: utf-8 -*-
"""
בדיקות ניהול (שלב 5): הרשאות admin ל-lookups, מיפוי מטרה->מפרט שמזין את המנוע,
חסימת מחיקה של ערך בשימוש (409), reset-password, ו-/admin/stats + /admin/users.
דורש: DB beton עם seed.
"""

import pytest
from sqlalchemy import text

from service.auth_service import hash_password
from service.matching_engine_service import match_requests_for_offer

TA = (32.0853, 34.7818)


def _scalar(db, sql, **p):
    return db.execute(text(sql), p).scalar()


def _wipe(db):
    db.execute(text("DELETE FROM ConcreteRequests WHERE address LIKE 'PYTEST5-%'"))
    db.execute(text("DELETE FROM Concrete_type WHERE Purpose_id IN (SELECT id FROM Purpose WHERE Purpose LIKE 'PYTEST5%')"))
    db.execute(text("DELETE FROM Purpose WHERE Purpose LIKE 'PYTEST5%'"))
    db.execute(text("DELETE FROM Admins WHERE user_name LIKE 'pytest5%'"))
    db.execute(text("DELETE FROM Customers WHERE user_name LIKE 'pytest5%'"))
    db.execute(text("DELETE FROM Contractors WHERE user_name LIKE 'pytest5%'"))
    db.commit()


@pytest.fixture()
def admin_token(client, db):
    _wipe(db)
    db.execute(
        text("INSERT INTO Admins (user_name, password_hash) VALUES (:u, :h)"),
        {"u": "pytest5_admin", "h": hash_password("adminpw")},
    )
    db.commit()
    tok = client.post("/auth/login", json={"user_name": "pytest5_admin", "password": "adminpw"}).json()["access_token"]
    yield tok
    _wipe(db)


def _auth(tok):
    return {"Authorization": f"Bearer {tok}"}


def test_lookup_crud_requires_admin(client, db, admin_token):
    # קבלן רגיל → 403
    con = client.post("/auth/register/contractor", json={"user_name": "pytest5_con", "password": "x123456"}).json()
    forbidden = client.post("/purposes/", json={"Purpose": "PYTEST5_X"}, headers=_auth(con["access_token"]))
    assert forbidden.status_code == 403
    # ללא טוקן → 401
    assert client.post("/purposes/", json={"Purpose": "PYTEST5_X"}).status_code == 401
    # מנהל → 201
    ok = client.post("/purposes/", json={"Purpose": "PYTEST5_X"}, headers=_auth(admin_token))
    assert ok.status_code == 201


def test_admin_mapping_feeds_engine(client, db, admin_token):
    b30 = _scalar(db, "SELECT id FROM Strength WHERE strength='ב-30'")
    b40 = _scalar(db, "SELECT id FROM Strength WHERE strength='ב-40'")

    # מנהל יוצר מטרה עם דרישת חוזק ב-40 (sort גבוה)
    purpose = client.post(
        "/purposes/",
        json={"Purpose": "PYTEST5_מטרה", "req_strength_id": b40},
        headers=_auth(admin_token),
    ).json()
    pid = purpose["id"]
    assert purpose["req_strength_id"] == b40

    # שני סוגי בטון: חלש (ב-30) וחזק (ב-40)
    weak = client.post("/concrete-types/", json={"strength_id": b30, "Purpose_id": pid}, headers=_auth(admin_token)).json()
    strong = client.post("/concrete-types/", json={"strength_id": b40, "Purpose_id": pid}, headers=_auth(admin_token)).json()

    # בקשת לקוח עם המטרה החדשה
    cust = _scalar(db, "INSERT INTO Customers (user_name, password_hash) OUTPUT INSERTED.id VALUES ('pytest5_cust','x')")
    _scalar(
        db,
        "INSERT INTO ConcreteRequests (customer_id, purpose_id, quantity, address, lat, lng, [status]) "
        "OUTPUT INSERTED.request_id VALUES (:c,:p,5.0,'PYTEST5-req',:lat,:lng,'OPEN')",
        c=cust, p=pid, lat=TA[0], lng=TA[1],
    )
    db.commit()

    def matched(concrete_id):
        res = match_requests_for_offer(db, {"lat": TA[0], "lng": TA[1], "concrete_id": concrete_id, "quantity": 5.0})
        return any(str(r.get("address") or "").startswith("PYTEST5-req") for r in res)

    assert matched(weak["id"]) is False, "פנייה חלשה מהמיפוי לא אמורה להתאים"
    assert matched(strong["id"]) is True, "פנייה בחוזק הנדרש אמורה להתאים"


def test_delete_in_use_lookup_returns_409(client, db, admin_token):
    # ב-30 בשימוש (seed: יסודות/concrete_types) → מחיקה חסומה
    b30 = _scalar(db, "SELECT id FROM Strength WHERE strength='ב-30'")
    r = client.delete(f"/strengths/{b30}", headers=_auth(admin_token))
    assert r.status_code == 409


def test_admin_reset_password(client, db, admin_token):
    cust = client.post("/auth/register/customer", json={"user_name": "pytest5_rp", "password": "orig123"}).json()
    rp = client.post(
        f"/admin/users/{cust['user_id']}/reset-password",
        json={"role": "customer", "new_password": "Temp!456"},
        headers=_auth(admin_token),
    )
    assert rp.status_code == 200
    # התחברות בסיסמה הזמנית מצליחה
    login = client.post("/auth/login", json={"user_name": "pytest5_rp", "password": "Temp!456"})
    assert login.status_code == 200


def test_admin_stats_and_users(client, db, admin_token):
    client.post("/auth/register/customer", json={"user_name": "pytest5_u", "password": "x123456"})

    stats = client.get("/admin/stats", headers=_auth(admin_token))
    assert stats.status_code == 200
    body = stats.json()
    for k in ("open_requests", "open_offers", "closed_deals", "total_matches", "accepted_matches", "match_rate"):
        assert k in body
    assert body["open_requests"] >= 0

    users = client.get("/admin/users", headers=_auth(admin_token))
    assert users.status_code == 200
    assert any(u["user_name"] == "pytest5_u" and u["role"] == "customer" for u in users.json())

    # לקוח לא רשאי לגשת ל-/admin/stats
    cust_tok = client.post("/auth/login", json={"user_name": "pytest5_u", "password": "x123456"}).json()["access_token"]
    assert client.get("/admin/stats", headers=_auth(cust_tok)).status_code == 403
