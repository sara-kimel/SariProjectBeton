# -*- coding: utf-8 -*-
"""
בדיקות תפוגה עצלה (OD-11, שלב 5): פנייה שעבר expiry_time שלה מסומנת EXPIRED
(וההתאמות NOTIFIED שלה) בעת קריאה/הרצת מנוע, והמנוע לעולם לא מתאים אותה.
דורש: DB beton.
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from service.expiry_service import expire_stale_offers
from service.matching_engine_service import match_offers_for_request

TA = (32.0853, 34.7818)


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _scalar(db, sql, **p):
    return db.execute(text(sql), p).scalar()


def _wipe(db):
    db.execute(text("DELETE FROM OfferMatches WHERE offer_id IN "
                    "(SELECT request_id FROM ContractorConcreteRequests WHERE address LIKE 'PYTEST5E-%')"))
    db.execute(text("DELETE FROM ContractorConcreteRequests WHERE address LIKE 'PYTEST5E-%'"))
    db.execute(text("DELETE FROM ConcreteRequests WHERE address LIKE 'PYTEST5E-%'"))
    db.execute(text("DELETE FROM Concrete_type WHERE Purpose_id IN (SELECT id FROM Purpose WHERE Purpose LIKE 'PYTEST5E%')"))
    db.execute(text("DELETE FROM Purpose WHERE Purpose LIKE 'PYTEST5E%'"))
    db.execute(text("DELETE FROM Contractors WHERE user_name LIKE 'pytest5e%'"))
    db.execute(text("DELETE FROM Customers WHERE user_name LIKE 'pytest5e%'"))
    db.commit()


@pytest.fixture()
def env(db):
    _wipe(db)
    con = _scalar(db, "INSERT INTO Contractors (user_name, password_hash) OUTPUT INSERTED.id VALUES ('pytest5e_con','x')")
    cust = _scalar(db, "INSERT INTO Customers (user_name, password_hash) OUTPUT INSERTED.id VALUES ('pytest5e_cust','x')")
    db.commit()
    yield db, con, cust
    _wipe(db)


def _mk_offer(db, con, tag, expiry, status="OPEN"):
    return _scalar(
        db,
        "INSERT INTO ContractorConcreteRequests (contractor_id, quantity, address, lat, lng, expiry_time, [status]) "
        "OUTPUT INSERTED.request_id VALUES (:c, 5.0, :a, :lat, :lng, :exp, :st)",
        c=con, a=f"PYTEST5E-{tag}", lat=TA[0], lng=TA[1], exp=expiry, st=status,
    )


def test_expire_marks_offer_and_matches(env):
    db, con, cust = env
    offer = _mk_offer(db, con, "PAST", _now() - timedelta(hours=1))
    req = _scalar(
        db,
        "INSERT INTO ConcreteRequests (customer_id, quantity, address, lat, lng, [status]) "
        "OUTPUT INSERTED.request_id VALUES (:c, 4.8, 'PYTEST5E-req', :lat, :lng, 'OPEN')",
        c=cust, lat=TA[0], lng=TA[1],
    )
    match = _scalar(
        db,
        "INSERT INTO OfferMatches (offer_id, request_id, customer_id, [status]) "
        "OUTPUT INSERTED.id VALUES (:o,:r,:c,'NOTIFIED')",
        o=offer, r=req, c=cust,
    )
    db.commit()

    n = expire_stale_offers(db)
    assert n >= 1
    assert _scalar(db, "SELECT [status] FROM ContractorConcreteRequests WHERE request_id=:o", o=offer) == "EXPIRED"
    assert _scalar(db, "SELECT [status] FROM OfferMatches WHERE id=:m", m=match) == "EXPIRED"


def test_engine_never_matches_expired_offer(env):
    db, con, cust = env
    # מטרה ללא מיפוי req_* -> נפילה חיננית: התאמה לפי שוויון מטרה בלבד
    pid = _scalar(db, "INSERT INTO Purpose (Purpose) OUTPUT INSERTED.id VALUES ('PYTEST5E_מטרה')")
    ct = _scalar(
        db,
        "INSERT INTO Concrete_type (Purpose_id) OUTPUT INSERTED.id VALUES (:p)", p=pid,
    )
    db.commit()

    # פנייה שפגה + פנייה תקפה, שתיהן עם אותו סוג-בטון (אותה מטרה)
    _scalar(
        db,
        "INSERT INTO ContractorConcreteRequests (contractor_id, concrete_id, quantity, address, lat, lng, expiry_time, [status]) "
        "OUTPUT INSERTED.request_id VALUES (:c,:ct,5.0,'PYTEST5E-EXP',:lat,:lng,:exp,'OPEN')",
        c=con, ct=ct, lat=TA[0], lng=TA[1], exp=_now() - timedelta(hours=2),
    )
    _scalar(
        db,
        "INSERT INTO ContractorConcreteRequests (contractor_id, concrete_id, quantity, address, lat, lng, expiry_time, [status]) "
        "OUTPUT INSERTED.request_id VALUES (:c,:ct,5.0,'PYTEST5E-OK',:lat,:lng,:exp,'OPEN')",
        c=con, ct=ct, lat=TA[0], lng=TA[1], exp=_now() + timedelta(hours=5),
    )
    db.commit()

    request_dict = {"lat": TA[0], "lng": TA[1], "purpose_id": pid, "quantity": 4.8}
    res = match_offers_for_request(db, request_dict)
    addrs = [str(r.get("address") or "") for r in res]
    assert any(a.startswith("PYTEST5E-OK") for a in addrs), "פנייה תקפה ותואמת אמורה להימצא"
    assert not any(a.startswith("PYTEST5E-EXP") for a in addrs), "פנייה שפגה לא אמורה להיות מותאמת"


def test_future_offer_not_expired(env):
    db, con, cust = env
    offer = _mk_offer(db, con, "FUT", _now() + timedelta(hours=5))
    db.commit()
    expire_stale_offers(db)
    assert _scalar(db, "SELECT [status] FROM ContractorConcreteRequests WHERE request_id=:o", o=offer) == "OPEN"
