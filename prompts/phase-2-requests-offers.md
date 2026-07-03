# שלב 2 — בקשות לקוח ופניות קבלן (CRUD)

> פרומפט עצמאי לצ'אט חדש. **לפני שמתחילים:** קרא/י את `SPEC.md` (סעיפים 7, 8.2, 8.3, 12.3, 12.4) ואת `prompts/README.md`. ודא ששלבים 0–1 הושלמו (סכימה, seed, אימות).

## מטרת השלב
לאפשר ללקוח מאומת ליצור/לנהל **בקשות**, ולקבלן מאומת ליצור/לנהל **פניות** — כולל שמירה תקינה ב-DB וקשירה למשתמש המחובר. **בלי מנוע התאמה עדיין** (שלב 3) — כאן רק ישויות ה-CRUD והמסכים.

## היקף
**נכלל:** תיקון/השלמת endpoints של בקשות ופניות · קשירה ל-`current_user` · אכיפת בעלות · חיבור טפסי הלקוח (בקשה) והקבלן (פנייה) לאימות ולנתוני ה-lookup · רשימות "שלי".
**לא נכלל:** הפעלת המנוע, OfferMatches, התראות, אישור (שלב 3–4). ב-`POST` בשלב זה **לא** מריצים התאמה — רק שומרים (ההרצה תתווסף בשלב 3).

## משימות

### שרת
1. **בקשות (`concrete_request_controller` + repository):**
   - `POST /concrete-requests/` — לשמור עם `customer_id = current_user` (להתעלם מ-customer_id בגוף), `status='OPEN'`. ולידציה: lat/lng חובה ותקינים, quantity>0, purpose_id קיים.
   - `GET /concrete-requests/customer/{id}` ו-`/{id}` — רק לבעלים (או מנהל), אחרת 403/404.
   - `PUT/DELETE /{id}` — רק כשהבקשה `OPEN` ובבעלות; חסום אם CLOSED (409).
   - הסר את שדה `region` מכל ה-DTOs (OD-3); ודא שאין הפניה אליו.
2. **פניות (`contractor_concrete_request_controller` + `contractor_concrete_service`):**
   - **הפעל מחדש** `POST /contractor-offers/` — שמירת פנייה עם `contractor_id = current_user`, `status='OPEN'`, `created_at`. ולידציה: concrete_id קיים, quantity>0, lat/lng חובה, `expiry_time` **עתידי**.
   - שמור על `service/price_service.double_price_from_string` רק אם המשמעות אושרה; אחרת אל תכפיל מחיר (ראה SPEC §14 — סמן/שאל).
   - `GET /contractor-offers/contractor/{id}` ו-`/{id}` — לבעלים/מנהל.
   - `PUT/DELETE /{id}` — לבעלים כש-OPEN.
   - את `POST /contractor-offers/send/` **השאר כפי שהוא לבינתיים** (מחזיר מועמדים); הוא ישוכתב בשלב 3 לשמור+להתאים.
3. ודא DTOs עקביים (types מול DB), ותגובות 201/200/404/403/409 נכונות.

### לקוח (`client/src/`)
4. **api:** עדכן `api/requests.ts`, `api/offers.ts` שיעבדו עם הטוקן (כבר דרך ה-interceptor) ועם ה-DTOs המעודכנים. ודא `api/lookups.ts` מביא purposes/strengths/reliants/stone-sizes/concrete-types.
5. **לקוח — בקשות:**
   - עדכן `pages/NewConcreteRequestPage.tsx`: להסיר קלט `customer_id` ידני (נלקח מהמשתמש), מטרה מ-Purpose, כמות, כתובת, מיקום במפה. לאחר הצלחה → הפניה ל"הבקשות שלי".
   - `pages/customer/MyRequestsPage.tsx` (`/customer/requests`) — רשימה עם סטטוס.
   - `pages/customer/RequestDetailPage.tsx` (`/customer/requests/:id`) — פרטים + סטטוס (אזור ההתאמות/אישור יתמלא בשלב 4; כרגע placeholder).
   - לוח בקרה לקוח `/customer` — סיכום + כפתור "בקשה חדשה".
6. **קבלן — פניות:**
   - `pages/contractor/NewOfferPage.tsx` (`/contractor/offers/new`) — בחירת סוג בטון (מדורג מטרה→חוזק→סומך→גודל אבן מתוך concrete-types/lookups), כמות, מחיר, זמן תפוגה, מיקום במפה (MapPicker קיים). שליחה → `POST /contractor-offers/` (שמירה בלבד בשלב זה).
   - `pages/contractor/MyOffersPage.tsx` (`/contractor/offers`) — רשימה + סטטוס + ספירה לאחור לתפוגה.
   - `pages/contractor/OfferDetailPage.tsx` (`/contractor/offers/:id`).
   - לוח בקרה קבלן `/contractor`.
7. עדכן `App.tsx` עם המסלולים החדשים תחת RoleRoute המתאים, וניווט ב-Layout לפי תפקיד.

## בדיקת מקצה-לקצה (E2E)
**שרת (`tests/test_requests.py`, `tests/test_offers.py`):**
1. לקוח מחובר יוצר בקשה → 201, `status="OPEN"`, `customer_id` = המחובר (לא מה שנשלח בגוף).
2. לקוח א' לא רואה/לא עורך בקשה של לקוח ב' → 403/404.
3. עריכת בקשה OPEN עובדת; מחיקה עובדת.
4. קבלן מחובר יוצר פנייה → 201, `status="OPEN"`, `expiry_time` עתידי; expiry בעבר → 422/400.
5. `GET /contractor-offers/contractor/{me}` מחזיר את הפניות שלו בלבד.

**חוצה-מערכת (`tests/e2e/test_phase2_flow.py`):** רצף מלא מול השרת החי — הרשמת לקוח+קבלן, התחברות, לקוח יוצר בקשה, קבלן יוצר פנייה, כל אחד רואה את שלו.

**לקוח (ידני + build):** `npm run build` עובר; לקוח נכנס, יוצר בקשה, רואה אותה ברשימה עם OPEN; קבלן נכנס, יוצר פנייה, רואה אותה עם ספירה לאחור.

## הגדרת סיום
- בקשות ופניות נשמרות נכון ומקושרות לבעלים; בעלות נאכפת; region הוסר.
- בדיקות עוברות + `npm run build`.
- עדכן `SPEC.md` §15 (שלב 2 ✅) ואת הזיכרון (endpoints שתוקנו, price doubling — הוכרע/נשאל).
- סכם למשתמש; אם `double_price` לא הובהר — שאל מה המשמעות.

## הערות/מלכודות
- `POST /contractor-offers/` היה **מוער** — הפעל אותו מחדש נכון.
- אל תריץ את המנוע ב-POST בשלב זה (שלב 3).
- בחירת סוג בטון בלקוח: ה-`Concrete_type` הוא צירוף מזהים — ודא שהטופס מרכיב/בורר `concrete_id` תקין מתוך הנתונים שנזרעו בשלב 0.
