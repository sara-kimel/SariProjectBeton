# שלב 5 — מנהל ותפוגות (Admin + Lazy Expiry)

> פרומפט עצמאי לצ'אט חדש. **לפני שמתחילים:** קרא/י את `SPEC.md` (סעיפים 8.6, 12.5, 6.2, 11) ואת `prompts/README.md`. ודא ששלבים 0–4 הושלמו (הזרימה המרכזית עובדת).

## מטרת השלב
לתת ל**מנהל** לנהל את תוכן המערכת (טבלאות עזר + מיפוי מטרה→מפרט + סוגי בטון + משתמשים), ולהשלים את מנגנון **התפוגה העצל (lazy)** של פניות (OD-11) כך שהמערכת עקבית לאורך זמן.

## היקף
**נכלל:** CRUD מנהל ל-lookups + concrete-types + מיפוי `req_*` בטבלת Purpose · רשימת משתמשים + reset-password (מ-שלב 1) · מסכי מנהל · lazy expiry מלא (סימון EXPIRED + Matches) · לוח בקרה עם KPI בסיסי.
**לא נכלל:** הקשחה/מובייל/בדיקות מקיפות (שלב 6).

## משימות

### שרת — ניהול (admin בלבד)
1. **Lookups CRUD:** ודא `POST/PUT/DELETE` לכל אחד מ-`/purposes/ /strengths/ /reliants/ /stone-sizes/ /concrete-types/` (הוסף היכן שחסר), מוגן ב-`require_role('admin')`. מנע מחיקה של ערך שבשימוש (FK) → 409 עם הודעה ברורה.
2. **מיפוי מטרה→מפרט:** endpoints לעדכון `Purpose.req_strength_id/req_reliant_id/req_stone_size_id` (העמודות נוספו בשלב 0). זה מה שמזין את סינון OD-2 במנוע.
3. **`Strength.sort_order`:** אפשר עריכה (חשוב להשוואת `≥`).
4. **משתמשים:** `GET /admin/users` (לקוחות+קבלנים, בלי hash), ו-`POST /admin/users/{id}/reset-password` (כבר משלב 1 — ודא עובד ומוגן).
5. **סטטיסטיקות:** `GET /admin/stats` — מונים: בקשות OPEN, פניות OPEN, עסקאות CLOSED, אחוז התאמה.

### שרת — תפוגה עצלה (OD-11)
6. **פונקציית עזר** `expire_offer_if_needed(db, offer)` / שכבת שירות: כשפנייה נטענת (בכל `GET`/במנוע) ועבר `expiry_time` והיא עדיין OPEN → סמן `status='EXPIRED'` ו-Matches שלה (NOTIFIED) → EXPIRED, בטרנזקציה. ודא שהמנוע (שני הכיוונים) לעולם לא מתאים פנייה שפגה.
7. אין job רקע ואין התראת תפוגה יזומה (הוכרע). תעד זאת.

### לקוח — מסכי מנהל (`role=admin`)
8. `pages/admin/AdminDashboard.tsx` (`/admin`) — KPI מ-`/admin/stats`.
9. `pages/admin/LookupsPage.tsx` (`/admin/lookups`) — ניהול מטרות/חוזק (עם sort_order)/סומך/גודל אבן + **עריכת מיפוי `req_*` למטרה**.
10. `pages/admin/ConcreteTypesPage.tsx` (`/admin/concrete-types`) — הרכבת סוג בטון מצירוף ערכי lookup.
11. `pages/admin/UsersPage.tsx` (`/admin/users`) — רשימה + כפתור reset-password.
12. ניווט admin ב-Layout; הכל תחת `RoleRoute('admin')`.

## בדיקת מקצה-לקצה (E2E)
**שרת (`tests/test_admin.py`, `tests/test_expiry.py`):**
1. מנהל יוצר מטרה חדשה + מיפוי `req_strength`, ואז המנוע משתמש בו (פנייה חלשה מהנדרש לא מותאמת). לקוח/קבלן מנסים לגשת ל-admin endpoint → 403.
2. מחיקת ערך lookup בשימוש → 409.
3. reset-password ע"י מנהל → המשתמש מתחבר בסיסמה הזמנית.
4. `/admin/stats` מחזיר מונים נכונים.
5. **תפוגה:** צור פנייה עם `expiry_time` שעבר → בקריאת `GET`/הפעלת מנוע היא מסומנת EXPIRED וה-Matches שלה EXPIRED; היא לא מותאמת.

**לקוח (ידני + build):** `npm run build`; מנהל נכנס, מנהל lookups + מיפוי, מריץ התאמה ורואה השפעה; פנייה שפגה מוצגת EXPIRED.

## הגדרת סיום
- מנהל יכול לנהל את כל התוכן; מיפוי מטרה→מפרט משפיע על המנוע; תפוגה עצלה עקבית.
- בדיקות עוברות + build.
- עדכן `SPEC.md` §15 (שלב 5 ✅) ואת הזיכרון.
- סכם למשתמש.

## הערות/מלכודות
- lazy expiry רץ בכל נתיב שנוגע בפניות — רכז אותו במקום אחד כדי לא לשכוח נתיב.
- מחיקת lookups: העדף חסימה (409) על מחיקה מדורגת, לשמירת שלמות היסטוריה.
