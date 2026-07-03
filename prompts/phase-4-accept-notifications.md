# שלב 4 — אישור עסקה והתראות (Accept + Notifications)

> פרומפט עצמאי לצ'אט חדש. **לפני שמתחילים:** קרא/י את `SPEC.md` (סעיפים 4, 6, 8.4, 8.5, 11, 13.3) ואת `prompts/README.md`. ודא ששלבים 0–3 הושלמו (המנוע יוצר OfferMatches).

## מטרת השלב
לסגור את **הזרימה המרכזית**: לקוח מותאם מקבל התראה, מאשר/דוחה, ו**הראשון שמאשר זוכה** (broadcast + first-wins, OD-5) — הכול אטומי; ואז שני הצדדים רואים את פרטי הקשר. + **מרכז התראות** בתוך-האפליקציה (OD-13).

## היקף
**נכלל:** טבלת Notifications · `/matches/accept` + `/decline` טרנזקציוני אטומי · עדכון סטטוסים (Offer/Request/Matches) · חשיפת פרטי קשר לאחר סגירה · endpoints התראות + polling בלקוח · מסכי אישור ומרכז התראות.
**לא נכלל:** מסכי מנהל, תפוגה יזומה (שלב 5), Web Push (הוכרע: לא ב-MVP).

## משימות

### DB
1. אם טרם נוצרה בשלב 3 — מיגרציה `db/migrations/004_notifications.sql` לטבלת **Notifications** (SPEC §7.2):
   `id PK, user_id, user_role NVARCHAR(20), type NVARCHAR(40), title, body, related_offer_id NULL, related_request_id NULL, is_read BIT DEFAULT 0, created_at`. עדכן `schema.sql`.

### שרת — אישור אטומי (הליבה)
2. **שירות** `service/deal_service.py` עם `accept_match(db, match_id, current_customer)` — **בטרנזקציה אחת**:
   - ודא שה-Match שייך ל-`current_customer` וסטטוסו NOTIFIED; אחרת 403/409.
   - ודא שהפנייה עדיין `OPEN` **ולא פגה** (`expiry_time`); אחרת 409/410 "ההצעה כבר נתפסה/פגה".
   - **עדכון אטומי (first-wins):** `UPDATE ContractorConcreteRequests SET status='CLOSED', accepted_request_id=? WHERE request_id=? AND status='OPEN'` — אם 0 שורות הושפעו → הפסד המרוץ → 409.
   - עדכן: `Request.status='CLOSED'`, ה-Match → ACCEPTED (+`responded_at`), שאר ה-Matches של אותה פנייה → SUPERSEDED, שאר ה-Matches הפעילות של אותה בקשה → מבוטלות.
   - צור התראות: לקבלן ("לקוח אישר" + טלפון הלקוח), ולמותאמים האחרים ("ההצעה כבר נתפסה").
   - הערה: השדה `id_customer` הקיים ב-`ContractorConcreteRequests` הוא ה-FK לבקשה — לשמו המומלץ `accepted_request_id` (SPEC §7.1).
3. **`decline_match`** — Match → DECLINED (+responded_at); לא משנה את הפנייה.
4. **Controller** `controller/match_controller.py` (או הרחבת קיים): `POST /matches/{id}/accept`, `POST /matches/{id}/decline`. אכיפת בעלות.
5. **חשיפת פרטי קשר:** רק לאחר סגירה — לקוח רואה טלפון הקבלן, קבלן רואה טלפון הלקוח. לפני כן לא לחשוף (SPEC §17.1).

### שרת — התראות
6. **NotificationService אמיתי** (החלף את `notification_service.py`/`mounday154.py` שהיו stubs): `create_notification(...)` כותב לטבלה. חבר אותו לכל האירועים: נמצאה התאמה (מהמנוע, שלב 3 — חבר כאן), לקוח אישר, הצעה נתפסה.
7. **Controller** `controller/notification_controller.py`: `GET /notifications/` (של המחובר), `GET /notifications/unread-count`, `POST /notifications/{id}/read`.

### לקוח
8. **api/matches.ts, api/notifications.ts.**
9. **מרכז התראות** `pages/NotificationsPage.tsx` (`/notifications`) + `NotificationBell` ב-Layout (מונה לא-נקראו, **polling** כל 15–30 שנ'). לחיצה על התראת התאמה → פרטי הבקשה עם כפתור אישור.
10. **אישור לקוח:** ב-`RequestDetailPage` — רשימת הפניות שהותאמו עם **אשר/דחה**. אישור מוצלח → הצגת פרטי הקבלן (טלפון). אם "כבר נתפסה" → הודעה מתאימה + רענון.
11. **צד קבלן:** ב-`OfferDetailPage` — כשנסגר, הצג את הלקוח שאישר + טלפון. התראה נכנסת מעדכנת.
12. מצבי טעינה/ריק/שגיאה + Toast לכל פעולה.

## בדיקת מקצה-לקצה (E2E)
**שרת (`tests/test_accept.py`, `tests/e2e/test_happy_path.py`):**
1. **מסלול מלא:** לקוח יוצר בקשה → קבלן יוצר פנייה תואמת → נוצר Match + התראה ללקוח → הלקוח מאשר → Offer=CLOSED, Request=CLOSED, Match=ACCEPTED, נוצרות התראות (לקבלן + "נתפסה" לאחרים) → הלקוח רואה טלפון הקבלן והקבלן רואה טלפון הלקוח.
2. **מרוץ (קריטי):** שתי בקשות מותאמות לאותה פנייה; שני אישורים כמעט-בו-זמנית → **בדיוק אחד** מצליח (200), השני 409. הפנייה CLOSED פעם אחת, אין כפילות. (בדיקה עם שני threads/קריאות מקבילות.)
3. אישור פנייה שכבר CLOSED → 409. אישור פנייה שפגה → 409/410.
4. לקוח מנסה לאשר Match של לקוח אחר → 403.
5. `GET /notifications/` מחזיר את ההתראות הנכונות; `unread-count` יורד אחרי `read`.

**לקוח (ידני + build):** `npm run build`; זרימה מלאה בשני חלונות (לקוח + קבלן): פנייה → פעמון מתעדכן אצל הלקוח → אישור → שני הצדדים רואים טלפון.

## הגדרת סיום
- הזרימה המרכזית עובדת קצה-לקצה; המרוץ בטוח (אטומי); התראות זורמות; פרטי קשר נחשפים רק אחרי סגירה.
- כל הבדיקות עוברות (כולל בדיקת המרוץ) + build.
- עדכן `SPEC.md` §15 (שלב 4 ✅ — MVP הליבה מוכן!) ואת הזיכרון.
- סכם למשתמש שה-MVP הפונקציונלי הושלם.

## הערות/מלכודות
- **אטומיות זו הנקודה הקריטית** — השתמש ב-`UPDATE ... WHERE status='OPEN'` המותנה ובדוק rowcount; אל תסתמך על קריאה-ואז-כתיבה.
- polling פשוט מספיק ל-MVP; WebSocket הוא שלב 6/עתידי.
- ודא שכל עדכוני הסטטוס + ההתראות באותה טרנזקציה של האישור.
