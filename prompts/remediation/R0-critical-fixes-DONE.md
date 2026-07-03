# שלב R0 — תיקונים קריטיים לפני אוויר (Critical Fixes) — ✅ בוצע

> **סטטוס: בוצע ואומת (2026-07-03).** קובץ זה מתעד את מה שכבר תוקן, כדי שצ'אט חדש יכיר את המצב ולא יחזור על העבודה. אם אתה פותח שלב חדש — התחל מ-R1.

## מטרת השלב
לסגור את 6 הליקויים הקריטיים שנמצאו בסקירת הקוד (כולם עברו אימות אדוורסרי עצמאי) לפני עלייה לאוויר: חור אבטחה, שני באגי נכונות ושני באגי תצורה. ראה `SPEC.md` §18.1.

## מה בוצע
כל 6 תיקוני ה-P0 יושמו ואומתו. חבילת בדיקות השרת: **52 עוברות** (היו 49; נוספו 3 בדיקות רגרסיה). כל שורה ב-`SPEC.md` §18.1 מסומנת ✅.

## התיקונים

### FIX-1 — הרשאות `/customers` ו-`/contractors` (IDOR + דליפת PII) [קריטי]
- **הבעיה:** הראוטרים היו מוגנים רק ב-`get_current_user` — כל משתמש מאומת יכל למשוך את כל הטלפונים (`GET /`) ולערוך/למחוק כל חשבון (`PUT/DELETE /{id}`).
- **התיקון:** `server/controller/customer_controller.py` + `server/controller/contractor_controller.py` — רשימת-הכל ו-`POST` הוגבלו ל-admin בלבד; `GET/PUT/DELETE /{id}` לבעלים-או-admin (נוסף `_owns_or_admin`, כדפוס `concrete_request_controller`).

### FIX-2 — מרוץ double-booking באישור [גבוה]
- **הבעיה:** ב-`accept_match` השער האטומי הגן רק על שורת הפנייה; סגירת הבקשה וקביעת ACCEPTED לא היו מותנות → לקוח יחיד שהותאם לשתי פניות יכל לאשר את שתיהן במקביל (שני קבלנים מקבלים את פרטיו).
- **התיקון:** `server/service/deal_service.py` — שער אטומי סימטרי על הבקשה (`UPDATE ConcreteRequests SET status='CLOSED' WHERE request_id=:rid AND status='OPEN'` + `rowcount==0 → 409`), ותנאי `AND status='NOTIFIED'` על עדכון ה-ACCEPTED. סדר הנעילה פנייה→בקשה נשמר.

### FIX-3 — ביטול = מחיקה קשה ששברה FK [גבוה]
- **הבעיה:** `DELETE` על בקשה/פנייה ביצע מחיקה פיזית; ל-`OfferMatches` יש FK בלי cascade → כל ביטול של פריט עם התאמות (המצב הרגיל) זרק 500. `CANCELLED` לא מומש בקוד.
- **התיקון:** נוספו `DealService.cancel_request` / `cancel_offer` (`server/service/deal_service.py`): מעבר ל-`status='CANCELLED'` (מותנה `WHERE status='OPEN'` → 409 אחרת), ההתאמות ה-`NOTIFIED` → `SUPERSEDED`, ו(בביטול פנייה) התראת `OFFER_CANCELLED` ללקוחות המותאמים. הבקרים `concrete_request_controller.delete_request` ו-`contractor_concrete_request_controller.delete_offer` קוראים להם במקום `repo.delete`.
- **⚠️ שינוי סמנטי:** `DELETE` כעת = **ביטול רך**. הרשומה נשמרת עם `status=CANCELLED` (GET מחזיר 200, לא 404). `notification_service` קיבל `notify_offer_cancelled_to_customer` (סוג `OFFER_CANCELLED`). מתודות `repo.delete()` עדיין קיימות אך אינן נקראות מנתיבי הביטול.

### FIX-4 — מפתח JWT ברירת-מחדל לא בטוח [גבוה]
- **התיקון:** `server/config.py` — נוסף `APP_ENV` (ברירת מחדל `development`) ו-`_validate_production_settings`: מעלה `RuntimeError` אם `JWT_SECRET` ריק / שווה לברירת-המחדל / קצר מ-32 תווים כאשר `APP_ENV=production`, ומדפיס אזהרה ל-stderr בפיתוח (כך שבדיקות/dev עם המפתח הדיפולטי ממשיכות לרוץ). קבוע `_DEFAULT_JWT_SECRET` מרכז את הערך הלא-בטוח. `server/.env.example` — הערך המפורש הוסר (`JWT_SECRET=` ריק + רמז `secrets.token_urlsafe(48)`), ונוסף `APP_ENV=development`.

### FIX-5 — `DB_SERVER` מקובע [בינוני]
- **התיקון:** `server/config.py` — `DB_SERVER: str = os.getenv("DB_SERVER", "localhost")` (היה מקובע ל-`"localhost"` ומתעלם מ-`.env`).

### FIX-6 — R-tree ללא `cos(lat)` [בינוני]
- **התיקון:** `server/service/matching_engine_service.py` `get_candidates` — `delta_lng = radius_meters / (111000 * cos(radians(lat)))` נפרד מ-`delta_lat`, עם הגנת קטבים (`abs(cos)<1e-6 → 180.0`). כך תיבת ה-R-tree היא על-קבוצה אמיתית של מעגל הרדיוס, וה-Haversine מסנן במדויק. (אומת נומרית: נקודה 9 ק"מ ממזרח בקו-רוחב 32° כעת נכללת, קודם נפלה.)

## בדיקות שנוספו (`server/tests/test_accept.py`)
- `test_concurrent_double_booking_prevented` — לקוח יחיד + שתי פניות + שני אישורים במקביל → בדיוק פנייה אחת נסגרת (מוכיח FIX-2).
- `test_cancel_offer_with_matches_soft` / `test_cancel_request_with_matches_soft` — ביטול פריט שיש לו התאמות → `CANCELLED` + `SUPERSEDED` + התראה, בלי 500 (מוכיח FIX-3).
- `test_edit_and_delete_open` עודכן: אחרי `DELETE` הבקשה מוחזרת 200 עם `status=CANCELLED`, וביטול חוזר → 409.

## אימות
`cd server && PYTHONUTF8=1 ./.venv/Scripts/python.exe -m pytest -q` → **52 passed**. `npm run build` בלקוח לא הושפע (`format.ts` כבר מטפל בתווית `CANCELLED`; מודולי `api/customers.ts`+`api/contractors.ts` בלקוח מתים/לא בשימוש, ולכן הידוק ה-IDOR לא שבר שום זרימה).

## הבא בתור
המשך ל-`R1-cleanup-and-errors.md` ואילך (P1 הקשחות, ואז P2 השלמות SPEC).
