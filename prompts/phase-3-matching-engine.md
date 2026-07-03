# שלב 3 — מנוע ההתאמה המלא (Matching Engine)

> פרומפט עצמאי לצ'אט חדש. **לפני שמתחילים:** קרא/י את `SPEC.md` (סעיף 5 כולו — כולל 5.6, סעיף 6, סעיף 7.2 OfferMatches) ואת `prompts/README.md`. ודא ששלבים 0–2 הושלמו.

## מטרת השלב
להפוך את המנוע ל**מלא ופעיל דו-כיוונית**: פניית קבלן מפעילה חיפוש בקשות; בקשת לקוח מפעילה חיפוש פניות. יצירת רשומות **OfferMatches** לכל התאמה, סינון **מטרה→מפרט** (OD-2), ושמירת הפנייה ב-`/send/` (כיום לא נשמרת!). ההתראות והאישור עצמם — שלב 4 (כאן ניצור את רשומות ה-Match; שליחת ההתראה בפועל תיושם/תחובר בשלב 4, אבל אפשר ליצור כבר רשומות Notifications בסיסיות).

## היקף
**נכלל:** טבלת OfferMatches · סינון מטרה→מפרט + חוזק≥ · שמירת פנייה ב-/send/ · יצירת Matches · טריגר הפוך על יצירת בקשה · lazy skip של פניות שפגו · endpoint לצפייה בהתאמות.
**לא נכלל:** אישור/דחייה טרנזקציוני ומרכז ההתראות המלא (שלב 4).

## משימות

### DB
1. מיגרציה `db/migrations/003_matches.sql` — טבלת **OfferMatches** לפי SPEC §7.2:
   `id PK, offer_id FK→ContractorConcreteRequests, request_id FK→ConcreteRequests, customer_id FK→Customers, score DECIMAL, distance_m DECIMAL, status NVARCHAR(20) (NOTIFIED/ACCEPTED/DECLINED/SUPERSEDED/EXPIRED), created_at, responded_at NULL, UNIQUE(offer_id, request_id)`. עדכן `schema.sql`. (טבלת Notifications תיווצר בשלב 4 — או צור אותה כאן אם נוח, לפי SPEC §7.2.)

### שרת — המנוע
2. **סינון מטרה→מפרט (OD-2)** ב-`service/matching_engine_service.py`:
   - במקום `request.purpose_id == offer.concrete_type.Purpose_id` בלבד — גזור מ-`request.purpose` את המפרט הנדרש (`Purpose.req_strength_id/req_reliant_id/req_stone_size_id`).
   - שמור פנייה אם: `offer.concrete_type.strength.sort_order ≥ req_strength.sort_order` (אם הוגדר), וסומך/גודל אבן שווים אם המטרה מגדירה אותם.
   - **נפילה חיננית:** אם למטרה אין מיפוי `req_*` → התאמה לפי מטרה בלבד (התנהגות קיימת).
3. **שלב טעינה:** ב-`load_data()` סנן `status = 'OPEN'` כבר בשאילתה (לא בלולאה). קרא פרמטרים (רדיוס/משקלים/יחס כמות) מ-`config.py` (OD-9).
4. **מודולריזציה:** הפוך את הצינור לפונקציה נקייה `match_requests_for_offer(db, offer_dict) -> [candidates]` ופונקציה סימטרית `match_offers_for_request(db, request_dict) -> [offers]` (טריגר הפוך, SPEC §5.6): פניות `status='OPEN'` ושלא פג `expiry_time`, אותו סינון מטרה→מפרט, וכמות `request.qty ∈ [0.9×offer.qty, offer.qty]`.

### שרת — חיווט ל-endpoints
5. **`POST /contractor-offers/send/`** (שכתוב מלא): בטרנזקציה — (א) שמור את הפנייה (status=OPEN), (ב) הרץ `match_requests_for_offer`, (ג) צור רשומת `OfferMatches` (NOTIFIED) לכל מועמד, (ד) החזר לקבלן סיכום {offer_id, מספר מותאמים, רשימה מדורגת}. שילוב עם `POST /contractor-offers/` — החלט: או ש-`/` שומר בלבד ו-`/send/` שומר+מתאים, או שאיחוד. תעד בבירור.
6. **טריגר הפוך:** ב-`POST /concrete-requests/` — לאחר שמירת הבקשה, הרץ `match_offers_for_request`, צור `OfferMatches` (NOTIFIED) והחזר ללקוח את הפניות התואמות (אם יש).
7. **צפייה בהתאמות (endpoints ➕):**
   - `GET /matches/request/{request_id}` — ההתאמות של בקשה (לבעלים).
   - `GET /matches/offer/{offer_id}` — ההתאמות של פנייה (לבעלים).
   - `GET /contractor-offers/{id}` — כלול את מספר/רשימת המותאמים.
8. **Lazy expiry (חלקי, OD-11):** בכל שליפה של פנייה/מועמדים — התעלם/סמן EXPIRED פניות שעבר `expiry_time` שלהן (הסימון המלא + Matches→EXPIRED יושלם בשלב 4/5; לפחות אל תתאים פניות שפגו).

### לקוח
9. **קבלן — תוצאות התאמה:** לאחר יצירת פנייה (`/send/`), הצג את רשימת הלקוחות שהותאמו (מדורגת: מרחק/ותק/ניקוד) ב-`OfferDetailPage` / מסך תוצאות.
10. **לקוח — בפרטי הבקשה:** הצג את הפניות שהותאמו (אם יש) — placeholder לכפתור "אשר" (הפעולה עצמה בשלב 4).

## בדיקת מקצה-לקצה (E2E)
**שרת (`tests/test_matching.py`, `tests/e2e/test_phase3_flow.py`):**
1. **התאמה קדימה:** קיימת בקשת לקוח OPEN (מטרה=יסודות, כמות=3, מיקום א'). קבלן יוצר פנייה תואמת (concrete_type עם חוזק≥הנדרש, כמות=3.2, מיקום קרוב) → נוצרת רשומת OfferMatches (NOTIFIED), והפנייה **נשמרה** ב-DB.
2. **סינון מטרה→מפרט:** פנייה עם חוזק **נמוך** מהנדרש למטרה → **לא** מותאמת. פנייה עם חוזק גבוה יותר → כן.
3. **סינון כמות:** בקשה שצריכה 1 מ"ק מול פנייה של 8 מ"ק (1 < 0.9×8) → לא מותאמת. בקשה של 7.5 מול 8 → מותאמת.
4. **סינון גיאוגרפי:** בקשה מחוץ ל-10 ק"מ → לא מותאמת.
5. **טריגר הפוך:** קיימת פנייה OPEN; לקוח יוצר בקשה תואמת → מקבל בתגובה את הפנייה, ונוצרת OfferMatches.
6. **פנייה שפגה** (`expiry_time` בעבר) → לא מותאמת בשום כיוון.
7. `GET /matches/request/{id}` ו-`/matches/offer/{id}` מחזירים את ההתאמות.

**לקוח (ידני + build):** `npm run build`; קבלן יוצר פנייה ורואה רשימת מותאמים מדורגת; לקוח רואה בפרטי הבקשה שיש פניות מתאימות.

## הגדרת סיום
- המנוע שומר פנייה, יוצר Matches, מתאים מטרה→מפרט, ופועל בשני הכיוונים; פניות שפגו לא מותאמות.
- כל הבדיקות עוברות + build.
- עדכן `SPEC.md` §15 (שלב 3 ✅) ואת הזיכרון (OfferMatches קיים, המנוע דו-כיווני חי, החלטה על /send/ מול /).
- סכם למשתמש.

## הערות/מלכודות
- `filter_by_quantity`/`filter_requests_by_concrete` הקיימים ב-`matching_engine_service.py` הם הבסיס — הרחב אותם, אל תשכתב מאפס.
- `waiting_days` מבוסס על `date` (רזולוציית יום) — תקין.
- ודא אטומיות: יצירת פנייה + Matches בטרנזקציה אחת (אם ה-Match נכשל, הפנייה לא תישמר חלקית).
