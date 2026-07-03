"""
מנוע ההתאמה — לב המערכת (SPEC §5).

הצינור (Pipeline), לפי SPEC §5.2:
  שלב 0  טעינת מועמדים  — נטענים רק פריטים בסטטוס OPEN (סינון כבר בשאילתה).
  שלב 1  סינון גיאוגרפי — R-tree (lng,lat) + Haversine, רדיוס מ-config (OD-9).
  שלב 2  מטרה->מפרט     — נגזר ממטרת הבקשה (Purpose.req_*), חוזק>= / סומך== / גודל-אבן==,
                          נפילה חיננית להתאמה-לפי-מטרה אם למטרה אין מיפוי (OD-2).
  שלב 3  כמות           — request.qty בטווח [ratio*offer.qty, offer.qty] (OD-4).
  שלב 4  דירוג          — score = w1*waiting_days - w2*travel_minutes (OD-9).

המנוע דו-כיווני (OD-6):
  match_requests_for_offer(db, offer_dict)   — טריגר A: פניית קבלן -> בקשות לקוחות.
  match_offers_for_request(db, request_dict) — טריגר B: בקשת לקוח  -> פניות קבלנים.
שני הכיוונים חולקים את שלבי הסינון ואת פונקציות העזר.
"""

from sqlalchemy import text
from rtree import index
from datetime import datetime
import math

from type_safety import safe_int, safe_float
from config import settings


# =========================================================================
# שירות המועמדים הגיאוגרפי (R-tree + Haversine + ניקוד)
# טוען פריטים (בקשות או פניות) בסטטוס OPEN בלבד, ומחזיר מועמדים ממוינים.
# =========================================================================
class GeoCandidateService:

    def __init__(self, db):
        self.db = db
        self.rtree = index.Index()
        self.store = {}

    # ---------------------------------------------------------------------
    # טעינת בקשות לקוחות פתוחות (טריגר A) — הסינון status='OPEN' בשאילתה (SPEC §5.2 שלב 0)
    # ---------------------------------------------------------------------
    def load_data(self):
        self.rtree = index.Index()
        self.store = {}

        result = self.db.execute(text("""
            SELECT
                request_id,
                customer_id,
                purpose_id,
                quantity,
                address,
                lat,
                lng,
                [date],
                [status]
            FROM [dbo].[ConcreteRequests]
            WHERE [status] = 'OPEN'
        """))

        self._index_rows(result)

    # ---------------------------------------------------------------------
    # טעינת פניות קבלנים פתוחות ושלא פגו (טריגר B) — כולל מפרט ה-Concrete_type
    # ומיזוג sort_order של החוזק, כדי לאפשר סינון מטרה->מפרט לכל פנייה.
    # Lazy expiry (OD-11): פניות שעבר expiry_time שלהן מסוננות כבר בשאילתה.
    # ---------------------------------------------------------------------
    def load_open_offers(self):
        self.rtree = index.Index()
        self.store = {}

        result = self.db.execute(text("""
            SELECT
                o.request_id,
                o.contractor_id,
                o.concrete_id,
                o.quantity,
                o.address,
                o.lat,
                o.lng,
                o.price,
                o.expiry_time,
                o.created_at AS [date],
                o.[status],
                ct.strength_id,
                ct.Reliant_id,
                ct.Stone_size_id,
                ct.Purpose_id,
                s.sort_order AS strength_sort
            FROM [dbo].[ContractorConcreteRequests] o
            LEFT JOIN [dbo].[Concrete_type] ct ON ct.id = o.concrete_id
            LEFT JOIN [dbo].[Strength] s        ON s.id = ct.strength_id
            WHERE o.[status] = 'OPEN'
              AND (o.expiry_time IS NULL OR o.expiry_time > SYSUTCDATETIME())
        """))

        self._index_rows(result)

    def _index_rows(self, result):
        """מוסיף שורות תוצאה ל-R-tree ול-store לפי (lng, lat). דורש request_id + lat/lng."""
        for row in result:
            item = dict(row._mapping)

            lat = item.get("lat")
            lng = item.get("lng")
            if lat is None or lng is None:
                continue

            lat = float(lat)
            lng = float(lng)
            rid = int(item["request_id"])

            item["lat"] = lat
            item["lng"] = lng

            self.rtree.insert(rid, (lng, lat, lng, lat))
            self.store[rid] = item

    # =========================
    # חישוב מרחק (Haversine)
    # =========================
    def haversine(self, lat1, lng1, lat2, lng2):

        R = 6371000

        lat1 = float(lat1)
        lng1 = float(lng1)
        lat2 = float(lat2)
        lng2 = float(lng2)

        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)

        a = (
            math.sin(dlat / 2) ** 2 +
            math.cos(math.radians(lat1)) *
            math.cos(math.radians(lat2)) *
            math.sin(dlng / 2) ** 2
        )

        return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # =========================
    # חישוב זמן המתנה (ימים)
    # =========================
    def calculate_waiting_days(self, created_date):

        if created_date is None:
            return 0

        if isinstance(created_date, datetime):
            dt = created_date
        else:
            try:
                dt = datetime.strptime(str(created_date), "%Y-%m-%d")
            except ValueError:
                try:
                    dt = datetime.fromisoformat(str(created_date))
                except Exception:
                    return 0

        return (datetime.now() - dt).days

    # =========================
    # שלב 1 + שלב 4: גיאו + ניקוד
    # =========================
    def get_candidates(self, lat, lng, radius_meters=None,
                       w1=None, w2=None):

        # פרמטרי המנוע מרוכזים ב-config.py (OD-9); None => ברירת המחדל מהקונפיג
        if radius_meters is None:
            radius_meters = settings.MATCH_RADIUS_METERS
        if w1 is None:
            w1 = settings.MATCH_SCORE_W1_WAITING
        if w2 is None:
            w2 = settings.MATCH_SCORE_W2_TRAVEL

        lat = float(lat)
        lng = float(lng)

        # תיבת חיפוש (bounding box) ל-R-tree. מעלת רוחב ≈ 111 ק"מ בכל מקום,
        # אך מעלת אורך מתכווצת ב-cos(lat) — לכן delta נפרד לציר האורך (FIX-6).
        # בלי התיקון התיבה צרה מדי מזרח-מערב ומשמיטה מועמדים תקפים בתוך הרדיוס
        # עוד לפני בדיקת ה-Haversine (בישראל ~32°: cos≈0.85 → ~8.5 ק"מ במקום 10).
        delta_lat = radius_meters / 111000
        cos_lat = math.cos(math.radians(lat))
        # הגנה מפני קטבים (cos≈0): לא מחלקים באפס — נשתמש ברוחב-אורך מלא.
        delta_lng = radius_meters / (111000 * cos_lat) if abs(cos_lat) > 1e-6 else 180.0

        min_lat = lat - delta_lat
        max_lat = lat + delta_lat
        min_lng = lng - delta_lng
        max_lng = lng + delta_lng

        candidate_ids = list(
            self.rtree.intersection((min_lng, min_lat, max_lng, max_lat))
        )

        results = []

        for cid in candidate_ids:

            item = self.store.get(cid)
            if not item:
                continue

            # פריט זמין כאשר status='OPEN' (סונן כבר בשאילתה; הגנה כפולה).
            status = item.get("status")
            if status is not None and str(status).strip().upper() != "OPEN":
                continue

            dist = self.haversine(lat, lng, item["lat"], item["lng"])
            if dist > radius_meters:
                continue

            # זמן המתנה (ותק) — לבקשות לפי date, לפניות לפי created_at (aliased ל-date)
            waiting_days = self.calculate_waiting_days(item.get("date"))

            # ניקוד חכם (SPEC §5.2 שלב 4)
            travel_minutes = (dist / 1000) * 2  # הערכה גסה: 2 דק' לק"מ

            score = (w1 * waiting_days) - (w2 * travel_minutes)

            results.append({
                **item,
                "distance_m": dist,
                "waiting_days": waiting_days,
                "travel_minutes": travel_minutes,
                "score": score,
            })

        # מיון יורד לפי ניקוד
        results.sort(key=lambda x: x["score"], reverse=True)

        return results


# =========================================================================
# שלב 2 — סינון מטרה->מפרט (OD-2)
# =========================================================================

def _load_offer_spec(db, concrete_id):
    """מפרט הבטון של פנייה מתוך Concrete_type (+ sort_order של החוזק). None אם לא נמצא."""
    if concrete_id is None:
        return None
    row = db.execute(
        text("""
            SELECT ct.Purpose_id, ct.Reliant_id, ct.Stone_size_id,
                   ct.strength_id, s.sort_order AS strength_sort
            FROM [dbo].[Concrete_type] ct
            LEFT JOIN [dbo].[Strength] s ON s.id = ct.strength_id
            WHERE ct.id = :cid
        """),
        {"cid": int(concrete_id)},
    ).first()
    if row is None:
        return None
    m = dict(row._mapping)
    return {
        "purpose_id": safe_int(m.get("Purpose_id")),
        "reliant_id": safe_int(m.get("Reliant_id")),
        "stone_size_id": safe_int(m.get("Stone_size_id")),
        "strength_sort": safe_int(m.get("strength_sort")),
    }


def _load_purpose_specs(db):
    """מיפוי purpose_id -> המפרט הנדרש (req_*). כולל sort_order של חוזק הדרישה."""
    rows = db.execute(text("""
        SELECT p.id, p.req_strength_id, p.req_reliant_id, p.req_stone_size_id,
               s.sort_order AS req_strength_sort
        FROM [dbo].[Purpose] p
        LEFT JOIN [dbo].[Strength] s ON s.id = p.req_strength_id
    """))
    specs = {}
    for row in rows:
        m = dict(row._mapping)
        pid = safe_int(m.get("id"))
        if pid is None:
            continue
        req_strength_id = safe_int(m.get("req_strength_id"))
        req_reliant_id = safe_int(m.get("req_reliant_id"))
        req_stone_size_id = safe_int(m.get("req_stone_size_id"))
        specs[pid] = {
            "purpose_id": pid,
            "req_strength_id": req_strength_id,
            "req_strength_sort": safe_int(m.get("req_strength_sort")),
            "req_reliant_id": req_reliant_id,
            "req_stone_size_id": req_stone_size_id,
            # "יש מיפוי" = לפחות אחד משדות ה-req_* מוגדר
            "has_mapping": any(
                x is not None for x in (req_strength_id, req_reliant_id, req_stone_size_id)
            ),
        }
    return specs


def _offer_meets_purpose(offer_spec, purpose_spec):
    """
    האם מפרט הפנייה עומד במפרט הנגזר ממטרת הבקשה (SPEC §5.2 שלב 2)?
    - אם למטרה אין מיפוי req_* -> נפילה חיננית: התאמה לפי מטרה בלבד
      (offer.concrete_type.Purpose_id == request.purpose_id).
    - אחרת: חוזק >= (לפי sort_order), וסומך/גודל-אבן שווים אם המטרה מגדירה אותם.
    """
    if purpose_spec is None:
        return False

    if not purpose_spec["has_mapping"]:
        offer_purpose = offer_spec.get("purpose_id")
        return offer_purpose is not None and offer_purpose == purpose_spec["purpose_id"]

    # חוזק: offer.sort_order >= req.sort_order (אם החוזק מוגדר וניתן להשוואה)
    req_strength_sort = purpose_spec["req_strength_sort"]
    if purpose_spec["req_strength_id"] is not None and req_strength_sort is not None:
        offer_sort = offer_spec.get("strength_sort")
        if offer_sort is None or offer_sort < req_strength_sort:
            return False

    # סומך: שוויון אם המטרה מגדירה
    req_reliant = purpose_spec["req_reliant_id"]
    if req_reliant is not None and offer_spec.get("reliant_id") != req_reliant:
        return False

    # גודל אבן: שוויון אם המטרה מגדירה
    req_stone = purpose_spec["req_stone_size_id"]
    if req_stone is not None and offer_spec.get("stone_size_id") != req_stone:
        return False

    return True


def filter_requests_by_concrete(concrete_id, db, candidates):
    """
    שלב 2 (OD-2) עבור טריגר A: בהינתן concrete_id של הקבלן, משאיר רק בקשות
    שמפרט הפנייה עומד במפרט הנגזר ממטרתן. מרחיב את הגרסה הישנה (שוויון מטרה בלבד)
    לסינון מטרה->מפרט המלא, עם נפילה חיננית להתנהגות הישנה כשלמטרה אין מיפוי.
    """
    offer_spec = _load_offer_spec(db, concrete_id)
    if offer_spec is None:
        return []

    purpose_specs = _load_purpose_specs(db)

    filtered = []
    for req in candidates:
        purpose_spec = purpose_specs.get(safe_int(req.get("purpose_id")))
        if _offer_meets_purpose(offer_spec, purpose_spec):
            filtered.append(req)
    return filtered


# =========================================================================
# שלב 3 — סינון כמות (OD-4): request.qty בטווח [ratio*offer.qty, offer.qty]
# =========================================================================
def filter_by_quantity(required_quantity, candidates, min_ratio=None):

    # יחס הכמות המינימלי מרוכז ב-config.py (OD-9)
    if min_ratio is None:
        min_ratio = settings.MATCH_QUANTITY_MIN_RATIO

    required_quantity = float(required_quantity)

    min_qty = required_quantity * min_ratio   # גבול תחתון: ratio מכמות הפנייה
    max_qty = required_quantity               # גבול עליון: כמות הפנייה

    filtered = []
    for c in candidates:
        qty = safe_float(c.get("quantity"))
        if qty is None:
            continue
        if min_qty <= qty <= max_qty:
            filtered.append(c)

    return filtered


# =========================================================================
# צינור מלא — דו-כיווני (OD-6)
# =========================================================================

def match_requests_for_offer(db, offer_dict):
    """
    טריגר A: פניית קבלן -> בקשות לקוחות תואמות (ממוין לפי ניקוד יורד).
    offer_dict דורש: lat, lng, concrete_id, quantity.
    """
    concrete_id = offer_dict.get("concrete_id")
    if concrete_id is None or offer_dict.get("lat") is None or offer_dict.get("lng") is None:
        return []
    if offer_dict.get("quantity") is None:
        return []

    geo = GeoCandidateService(db)
    geo.load_data()  # בקשות OPEN בלבד

    candidates = geo.get_candidates(
        lat=float(offer_dict["lat"]),
        lng=float(offer_dict["lng"]),
    )
    candidates = filter_requests_by_concrete(concrete_id, db, candidates)   # שלב 2 (OD-2)
    candidates = filter_by_quantity(offer_dict["quantity"], candidates)     # שלב 3
    return candidates


def match_offers_for_request(db, request_dict):
    """
    טריגר B (הפוך, SPEC §5.6): בקשת לקוח -> פניות קבלנים פתוחות ותואמות
    (סטטוס OPEN + לא פגו). request_dict דורש: lat, lng, purpose_id, quantity.
    """
    purpose_id = safe_int(request_dict.get("purpose_id"))
    req_qty = safe_float(request_dict.get("quantity"))
    if purpose_id is None or req_qty is None:
        return []
    if request_dict.get("lat") is None or request_dict.get("lng") is None:
        return []

    purpose_spec = _load_purpose_specs(db).get(purpose_id)

    geo = GeoCandidateService(db)
    geo.load_open_offers()  # פניות OPEN שלא פגו

    candidates = geo.get_candidates(
        lat=float(request_dict["lat"]),
        lng=float(request_dict["lng"]),
    )

    min_ratio = settings.MATCH_QUANTITY_MIN_RATIO
    matched = []
    for offer in candidates:
        offer_spec = {
            "purpose_id": safe_int(offer.get("Purpose_id")),
            "reliant_id": safe_int(offer.get("Reliant_id")),
            "stone_size_id": safe_int(offer.get("Stone_size_id")),
            "strength_sort": safe_int(offer.get("strength_sort")),
        }
        # שלב 2 (OD-2): הפנייה עומדת במפרט הנגזר ממטרת הבקשה
        if not _offer_meets_purpose(offer_spec, purpose_spec):
            continue
        # שלב 3: request.qty בטווח [ratio*offer.qty, offer.qty]
        offer_qty = safe_float(offer.get("quantity"))
        if offer_qty is None:
            continue
        if offer_qty * min_ratio <= req_qty <= offer_qty:
            matched.append(offer)

    return matched
