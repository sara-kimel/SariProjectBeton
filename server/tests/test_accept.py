# -*- coding: utf-8 -*-
"""
בדיקות אישור/דחיית עסקה (שלב 4) + המרוץ הקריטי (first-wins).
נבנה תרחיש מבוקר ישירות ב-DB (מסומן PYTEST4/pytest4) וקוראים ל-DealService
(ללא HTTP) — כדי לבדוק אטומיות ברמת ה-DB עם שני סשנים מקבילים.
דורש: DB beton.
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from sqlalchemy import text

from database import SessionLocal
from service.deal_service import DealService
from repository.notification_repository import NotificationRepository


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _scalar(db, sql, **p):
    return db.execute(text(sql), p).scalar()


def _wipe(db):
    db.execute(text(
        "DELETE FROM Notifications WHERE user_id IN "
        "(SELECT id FROM Customers WHERE user_name LIKE 'pytest4%') "
        "OR user_id IN (SELECT id FROM Contractors WHERE user_name LIKE 'pytest4%')"
    ))
    db.execute(text("DELETE FROM OfferMatches WHERE offer_id IN "
                    "(SELECT request_id FROM ContractorConcreteRequests WHERE address LIKE 'PYTEST4-%')"))
    db.execute(text("DELETE FROM ContractorConcreteRequests WHERE address LIKE 'PYTEST4-%'"))
    db.execute(text("DELETE FROM ConcreteRequests WHERE address LIKE 'PYTEST4-%'"))
    db.execute(text("DELETE FROM Contractors WHERE user_name LIKE 'pytest4%'"))
    db.execute(text("DELETE FROM Customers WHERE user_name LIKE 'pytest4%'"))
    db.commit()


def _mk_customer(db, un, phone):
    return _scalar(
        db, "INSERT INTO Customers (user_name, password_hash, phone) OUTPUT INSERTED.id VALUES (:u,'x',:p)",
        u=un, p=phone,
    )


def _mk_contractor(db, un, phone):
    return _scalar(
        db, "INSERT INTO Contractors (user_name, password_hash, phone) OUTPUT INSERTED.id VALUES (:u,'x',:p)",
        u=un, p=phone,
    )


def _mk_offer(db, contractor_id, tag, expiry):
    return _scalar(
        db,
        "INSERT INTO ContractorConcreteRequests (contractor_id, quantity, address, lat, lng, expiry_time, [status]) "
        "OUTPUT INSERTED.request_id VALUES (:c, 5.0, :a, 32.08, 34.78, :exp, 'OPEN')",
        c=contractor_id, a=f"PYTEST4-{tag}", exp=expiry,
    )


def _mk_request(db, customer_id, tag):
    return _scalar(
        db,
        "INSERT INTO ConcreteRequests (customer_id, quantity, address, lat, lng, [status]) "
        "OUTPUT INSERTED.request_id VALUES (:c, 4.8, :a, 32.08, 34.78, 'OPEN')",
        c=customer_id, a=f"PYTEST4-{tag}",
    )


def _mk_match(db, offer_id, request_id, customer_id):
    return _scalar(
        db,
        "INSERT INTO OfferMatches (offer_id, request_id, customer_id, score, distance_m, [status]) "
        "OUTPUT INSERTED.id VALUES (:o,:r,:c, 10, 500, 'NOTIFIED')",
        o=offer_id, r=request_id, c=customer_id,
    )


@pytest.fixture()
def scene(db):
    """קבלן + פנייה + שני לקוחות + שתי בקשות + שתי התאמות NOTIFIED לאותה פנייה."""
    _wipe(db)
    con = _mk_contractor(db, "pytest4_con", "052-1000000")
    c1 = _mk_customer(db, "pytest4_c1", "050-1111111")
    c2 = _mk_customer(db, "pytest4_c2", "050-2222222")
    offer = _mk_offer(db, con, "OFFER", _now() + timedelta(hours=5))
    r1 = _mk_request(db, c1, "R1")
    r2 = _mk_request(db, c2, "R2")
    m1 = _mk_match(db, offer, r1, c1)
    m2 = _mk_match(db, offer, r2, c2)
    db.commit()
    data = dict(con=con, c1=c1, c2=c2, offer=offer, r1=r1, r2=r2, m1=m1, m2=m2)
    yield db, data
    _wipe(db)


def test_accept_happy_path(scene):
    db, d = scene
    result = DealService(db).accept_match(d["m1"], d["c1"])

    assert result["match_status"] == "ACCEPTED"
    assert result["offer_status"] == "CLOSED"
    assert result["contact_phone"] == "052-1000000"   # טלפון הקבלן נחשף ללקוח

    db.commit()  # לסיים כל טרנזקציה מרומזת לפני קריאה
    assert _scalar(db, "SELECT [status] FROM ContractorConcreteRequests WHERE request_id=:o", o=d["offer"]) == "CLOSED"
    assert _scalar(db, "SELECT id_customer FROM ContractorConcreteRequests WHERE request_id=:o", o=d["offer"]) == d["r1"]
    assert _scalar(db, "SELECT [status] FROM ConcreteRequests WHERE request_id=:r", r=d["r1"]) == "CLOSED"
    assert _scalar(db, "SELECT [status] FROM OfferMatches WHERE id=:m", m=d["m1"]) == "ACCEPTED"
    assert _scalar(db, "SELECT [status] FROM OfferMatches WHERE id=:m", m=d["m2"]) == "SUPERSEDED"

    # התראות: לקבלן (אישר) + ללקוח האחר (נתפסה)
    con_notes = NotificationRepository(db).get_for_user(d["con"], "contractor")
    assert any(n.type == "CUSTOMER_ACCEPTED" for n in con_notes)
    c2_notes = NotificationRepository(db).get_for_user(d["c2"], "customer")
    assert any(n.type == "OFFER_TAKEN" for n in c2_notes)


def test_accept_already_closed_returns_409(scene):
    db, d = scene
    DealService(db).accept_match(d["m1"], d["c1"])  # זוכה
    db.commit()
    with pytest.raises(HTTPException) as ei:
        DealService(db).accept_match(d["m2"], d["c2"])  # הפנייה כבר CLOSED
    assert ei.value.status_code == 409


def test_accept_wrong_customer_forbidden(scene):
    db, d = scene
    with pytest.raises(HTTPException) as ei:
        DealService(db).accept_match(d["m1"], d["c2"])  # m1 שייך ל-c1
    assert ei.value.status_code == 403


def test_accept_expired_offer(db):
    _wipe(db)
    con = _mk_contractor(db, "pytest4_conE", "052-9")
    cust = _mk_customer(db, "pytest4_cE", "050-9")
    offer = _mk_offer(db, con, "EXP", _now() - timedelta(hours=1))  # פגה
    req = _mk_request(db, cust, "RE")
    m = _mk_match(db, offer, req, cust)
    db.commit()
    try:
        with pytest.raises(HTTPException) as ei:
            DealService(db).accept_match(m, cust)
        assert ei.value.status_code == 410
        db.commit()
        assert _scalar(db, "SELECT [status] FROM ContractorConcreteRequests WHERE request_id=:o", o=offer) == "EXPIRED"
        assert _scalar(db, "SELECT [status] FROM OfferMatches WHERE id=:m", m=m) == "EXPIRED"
    finally:
        _wipe(db)


def test_decline(scene):
    db, d = scene
    result = DealService(db).decline_match(d["m1"], d["c1"])
    assert result["match_status"] == "DECLINED"
    db.commit()
    assert _scalar(db, "SELECT [status] FROM OfferMatches WHERE id=:m", m=d["m1"]) == "DECLINED"
    # הפנייה לא הושפעה
    assert _scalar(db, "SELECT [status] FROM ContractorConcreteRequests WHERE request_id=:o", o=d["offer"]) == "OPEN"


def test_concurrent_accept_first_wins(scene):
    """המרוץ הקריטי: שני אישורים כמעט-בו-זמנית לאותה פנייה → בדיוק אחד מצליח."""
    db, d = scene

    def worker(match_id, customer_id):
        s = SessionLocal()
        try:
            DealService(s).accept_match(match_id, customer_id)
            return "ok"
        except HTTPException as e:
            return e.status_code
        finally:
            s.close()

    with ThreadPoolExecutor(max_workers=2) as ex:
        f1 = ex.submit(worker, d["m1"], d["c1"])
        f2 = ex.submit(worker, d["m2"], d["c2"])
        results = [f1.result(), f2.result()]

    assert results.count("ok") == 1, f"בדיוק אחד היה אמור להצליח, קיבלנו {results}"
    assert 409 in results, f"המפסיד היה אמור לקבל 409, קיבלנו {results}"

    db.commit()
    # הפנייה CLOSED פעם אחת, ובדיוק התאמה אחת ACCEPTED
    assert _scalar(db, "SELECT [status] FROM ContractorConcreteRequests WHERE request_id=:o", o=d["offer"]) == "CLOSED"
    accepted = _scalar(db, "SELECT COUNT(*) FROM OfferMatches WHERE offer_id=:o AND [status]='ACCEPTED'", o=d["offer"])
    assert accepted == 1


# =========================================================================
# FIX-2 — מרוץ double-booking: לקוח יחיד + בקשה אחת שהותאמה לשתי פניות שונות.
# בלי שער אטומי על הבקשה, שני אישורים במקביל היו סוגרים את שתי הפניות ושני
# קבלנים היו מקבלים את פרטי הלקוח.
# =========================================================================
def test_concurrent_double_booking_prevented(db):
    _wipe(db)
    con = _mk_contractor(db, "pytest4_conDB", "052-3000000")
    cust = _mk_customer(db, "pytest4_cDB", "050-3333333")
    o1 = _mk_offer(db, con, "DB1", _now() + timedelta(hours=5))
    o2 = _mk_offer(db, con, "DB2", _now() + timedelta(hours=5))
    req = _mk_request(db, cust, "RDB")
    m1 = _mk_match(db, o1, req, cust)
    m2 = _mk_match(db, o2, req, cust)
    db.commit()

    def worker(match_id):
        s = SessionLocal()
        try:
            DealService(s).accept_match(match_id, cust)
            return "ok"
        except HTTPException as e:
            return e.status_code
        finally:
            s.close()

    try:
        with ThreadPoolExecutor(max_workers=2) as ex:
            f1 = ex.submit(worker, m1)
            f2 = ex.submit(worker, m2)
            results = [f1.result(), f2.result()]

        assert results.count("ok") == 1, f"בדיוק אישור אחד היה אמור להצליח, קיבלנו {results}"
        assert 409 in results, f"המפסיד היה אמור לקבל 409, קיבלנו {results}"

        db.commit()
        # הבקשה נסגרה; בדיוק פנייה אחת CLOSED (השנייה נשארה OPEN) — לא double-booking
        assert _scalar(db, "SELECT [status] FROM ConcreteRequests WHERE request_id=:r", r=req) == "CLOSED"
        closed_offers = _scalar(
            db,
            "SELECT COUNT(*) FROM ContractorConcreteRequests "
            "WHERE request_id IN (:o1,:o2) AND [status]='CLOSED'",
            o1=o1, o2=o2,
        )
        assert closed_offers == 1, "בדיוק פנייה אחת אמורה להיסגר (מניעת double-booking)"
        accepted = _scalar(db, "SELECT COUNT(*) FROM OfferMatches WHERE request_id=:r AND [status]='ACCEPTED'", r=req)
        assert accepted == 1
    finally:
        _wipe(db)


# =========================================================================
# FIX-3 — ביטול (soft) של פנייה/בקשה שיש להן התאמות: בעבר מחיקה פיזית נכשלה
# על FK של OfferMatches (500). כעת: status→CANCELLED, ההתאמות→SUPERSEDED,
# והלקוח מקבל התראה על ביטול הפנייה.
# =========================================================================
def test_cancel_offer_with_matches_soft(db):
    _wipe(db)
    con = _mk_contractor(db, "pytest4_conCXO", "052-7000000")
    cust = _mk_customer(db, "pytest4_cCXO", "050-7777777")
    offer = _mk_offer(db, con, "CXO", _now() + timedelta(hours=5))
    req = _mk_request(db, cust, "CXR")
    m = _mk_match(db, offer, req, cust)
    db.commit()
    try:
        DealService(db).cancel_offer(offer)  # בעבר: FK 547 -> 500
        db.commit()
        assert _scalar(db, "SELECT [status] FROM ContractorConcreteRequests WHERE request_id=:o", o=offer) == "CANCELLED"
        assert _scalar(db, "SELECT [status] FROM OfferMatches WHERE id=:m", m=m) == "SUPERSEDED"
        notes = NotificationRepository(db).get_for_user(cust, "customer")
        assert any(n.type == "OFFER_CANCELLED" for n in notes)
    finally:
        _wipe(db)


def test_cancel_request_with_matches_soft(db):
    _wipe(db)
    con = _mk_contractor(db, "pytest4_conCRQ", "052-8000000")
    cust = _mk_customer(db, "pytest4_cCRQ", "050-8888888")
    offer = _mk_offer(db, con, "CR2O", _now() + timedelta(hours=5))
    req = _mk_request(db, cust, "CR2R")
    m = _mk_match(db, offer, req, cust)
    db.commit()
    try:
        DealService(db).cancel_request(req)  # בעבר: FK 547 -> 500
        db.commit()
        assert _scalar(db, "SELECT [status] FROM ConcreteRequests WHERE request_id=:r", r=req) == "CANCELLED"
        assert _scalar(db, "SELECT [status] FROM OfferMatches WHERE id=:m", m=m) == "SUPERSEDED"
    finally:
        _wipe(db)
