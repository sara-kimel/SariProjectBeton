# -*- coding: utf-8 -*-
"""
בדיקת מקצה-לקצה חוצת-מערכת לשלב 2 (מול אפליקציית ה-FastAPI):
הרשמת לקוח+קבלן -> לקוח יוצר בקשה -> קבלן יוצר פנייה -> כל אחד רואה את שלו.
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
                "DELETE FROM OfferMatches WHERE request_id IN "
                "(SELECT request_id FROM ConcreteRequests WHERE customer_id IN "
                " (SELECT id FROM Customers WHERE user_name LIKE 'pytest%')) "
                "OR offer_id IN (SELECT request_id FROM ContractorConcreteRequests WHERE contractor_id IN "
                " (SELECT id FROM Contractors WHERE user_name LIKE 'pytest%'))"
            )
        )
        db.execute(
            text(
                "DELETE FROM ConcreteRequests WHERE customer_id IN "
                "(SELECT id FROM Customers WHERE user_name LIKE 'pytest%')"
            )
        )
        db.execute(
            text(
                "DELETE FROM ContractorConcreteRequests WHERE contractor_id IN "
                "(SELECT id FROM Contractors WHERE user_name LIKE 'pytest%')"
            )
        )
        db.execute(text("DELETE FROM Customers WHERE user_name LIKE 'pytest%'"))
        db.execute(text("DELETE FROM Contractors WHERE user_name LIKE 'pytest%'"))
        db.commit()

    wipe()
    yield
    wipe()


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_phase2_full_flow(client, db):
    pid = db.execute(text("SELECT TOP 1 id FROM Purpose ORDER BY id")).scalar()
    cid = db.execute(text("SELECT TOP 1 id FROM Concrete_type ORDER BY id")).scalar()
    future = (datetime.now(timezone.utc) + timedelta(hours=6)).isoformat()

    cust = client.post("/auth/register/customer", json={"user_name": "pytest_flowC", "password": PW}).json()
    con = client.post("/auth/register/contractor", json={"user_name": "pytest_flowK", "password": PW}).json()

    # לקוח יוצר בקשה
    r = client.post(
        "/concrete-requests/",
        json={"purpose_id": pid, "quantity": 3.5, "lat": 32.08, "lng": 34.78, "address": "תל אביב"},
        headers=_auth(cust["access_token"]),
    )
    assert r.status_code == 201, r.text

    # קבלן יוצר פנייה
    o = client.post(
        "/contractor-offers/",
        json={"concrete_id": cid, "quantity": 5.0, "lat": 32.08, "lng": 34.78, "price": "550", "expiry_time": future},
        headers=_auth(con["access_token"]),
    )
    assert o.status_code == 201, o.text

    # כל אחד רואה את שלו
    my_reqs = client.get(
        f"/concrete-requests/customer/{cust['user_id']}", headers=_auth(cust["access_token"])
    ).json()
    assert len(my_reqs) == 1 and my_reqs[0]["status"] == "OPEN"

    my_offers = client.get(
        f"/contractor-offers/contractor/{con['user_id']}", headers=_auth(con["access_token"])
    ).json()
    assert len(my_offers) == 1 and my_offers[0]["status"] == "OPEN"
    assert my_offers[0]["price"] == "550"
