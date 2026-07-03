# שלב 1 — אימות והרשאות (Auth)

> פרומפט עצמאי לצ'אט חדש. **לפני שמתחילים:** קרא/י את `SPEC.md` (סעיף 10 — אבטחה/אימות, סעיף 8.1, סעיף 12.2/12.6) ואת `prompts/README.md`. ודא ששלב 0 הושלם (סכימה + seed + בדיקות).

## מטרת השלב
מערכת אימות מלאה: הרשמה/התחברות בשם משתמש+סיסמה מוצפנת, JWT, והרשאות מבוססות-תפקיד (RBAC) בשרת — ובלקוח: הרשמה, התחברות, שמירת טוקן, ומסלולים מוגנים. תפקידים: לקוח/קבלן/מנהל, **תפקיד יחיד למשתמש**, טבלאות נפרדות (OD-8).

## היקף
**נכלל:** hashing, JWT, register/login/me, RBAC middleware, בעלות (IDOR), טבלת Admins, שינוי סיסמה + reset ע"י מנהל · לקוח: AuthContext, עמודי הרשמה/התחברות, ProtectedRoute/RoleRoute, interceptor לטוקן.
**לא נכלל:** לוגיקת בקשות/פניות/התאמות (שלבים 2–4). מסכי התוכן יהיו שלד ריק שמאחורי אימות.

## משימות

### DB
1. מיגרציה `db/migrations/002_auth.sql`:
   - `Customers` + `Contractors`: הוסף `password_hash NVARCHAR(255)`, ודא `user_name` **UNIQUE** (+אורך מספיק, למשל 50), `created_at DATETIME2 DEFAULT SYSDATETIME()`. את העמודה הישנה `password` להשאיר זמנית או להסיר לאחר מיגרציית ערכים (אין ערכים אמיתיים — אפשר להסיר).
   - טבלה חדשה `Admins` (id IDENTITY, user_name UNIQUE, password_hash, first_name, last_name, created_at). זרע מנהל ראשוני אחד (סיסמה זמנית, לתעד).
   - עדכן `schema.sql`.

### שרת
2. **תלויות:** הוסף `passlib[bcrypt]` (או `bcrypt`), `python-jose[cryptography]` (או `pyjwt`) ל-`requirements.txt`. הגדרות JWT ב-`config.py` (`JWT_SECRET` מ-.env, אלגוריתם HS256, תוקף).
3. **שירות אבטחה** `service/auth_service.py`: `hash_password`, `verify_password`, `create_access_token`, `decode_token`.
4. **Repository/מודל למנהל** + עדכון מודלי Customer/Contractor (password_hash).
5. **Dependencies** `service/security.py` (או `deps.py`): `get_current_user` (מפענח JWT, מזריק {id, role}), `require_role(*roles)`, `get_current_customer/contractor/admin`.
6. **Controller** `controller/auth_controller.py` + חיבור ב-`app.py`:
   - `POST /auth/register/customer`, `POST /auth/register/contractor` (יוצר משתמש עם hash; דוחה שם משתמש קיים → 409).
   - `POST /auth/login` → מאמת, מחזיר `{access_token, role, user_id}`.
   - `GET /auth/me` → פרטי המשתמש המחובר.
   - `POST /auth/change-password` (מחובר), `POST /admin/users/{id}/reset-password` (admin בלבד — OD-12).
7. **DTOs** לאימות (register/login/token) ב-`dto/auth_dto.py`. אל תחזיר לעולם את ה-hash.
8. **הגנה על endpoints קיימים:** הוסף dependency אימות ל-controllers של customers/contractors/requests/offers (קריאה = מחובר; שינוי = בעלים/מנהל). לפחות תשתית ה-guards מוכנה; אכיפה מלאה לפי הרשאות תיושם עם כל פיצ'ר.

### לקוח (`client/src/`)
9. **api/auth.ts** — register/login/me. עדכן `api/client.ts`: interceptor שמוסיף `Authorization: Bearer <token>` ומטפל ב-401 (ניתוב ל-login) ו-403.
10. **AuthContext** (`context/AuthContext.tsx`) — מצב user/token, `login`/`logout`, שמירה ב-`localStorage`, טעינה בעליית האפליקציה.
11. **עמודים:** `pages/LoginPage.tsx`, `pages/RegisterPage.tsx` (שלב בחירת תפקיד → טופס: שם, שם משתמש, טלפון, סיסמה+אימות). ולידציה בעברית.
12. **ניתוב:** `ProtectedRoute`, `RoleRoute`, `PublicRoute`; עדכן `App.tsx` עם `/login`, `/register`, ו-`/app` שמפנה לפי תפקיד. Layout מציג שם משתמש + כפתור יציאה.

## בדיקת מקצה-לקצה (E2E)
**שרת (pytest, `tests/test_auth.py`):**
1. הרשמת לקוח חדש → 201; הרשמה חוזרת עם אותו שם משתמש → 409.
2. התחברות עם סיסמה נכונה → 200 + טוקן; סיסמה שגויה → 401.
3. `GET /auth/me` עם טוקן → 200 עם התפקיד הנכון; בלי טוקן → 401.
4. גישה של לקוח ל-endpoint שמסומן admin → 403.
5. שינוי סיסמה, ואז התחברות עם החדשה עובדת; מנהל מאפס סיסמה למשתמש והוא מתחבר איתה.
6. **ודא שה-hash נשמר ב-DB ולא סיסמה גלויה.**

**לקוח (ידני + build):**
7. `npm run build` עובר.
8. הרשמה כלקוח → הפניה ל-`/app` (לוח לקוח ריק/שלד); רענון דף שומר על התחברות (טוקן ב-localStorage).
9. יציאה מנקה טוקן ומחזירה ל-login; ניסיון גישה ל-`/customer` בלי התחברות → הפניה ל-login.

## הגדרת סיום
- כל בדיקות האימות עוברות; אין סיסמאות גלויות; RBAC אוכף.
- עדכן `SPEC.md` §15 (שלב 1 ✅) ואת הזיכרון (מבנה auth, מנהל ראשוני, JWT).
- סכם למשתמש + מסור את פרטי המנהל הראשוני והיכן מוגדר `JWT_SECRET`.

## הערות/מלכודות
- CORS כרגע `*` — תקין לפיתוח; להגביל בייצור (שלב 6).
- אל תשמור `JWT_SECRET` בקוד — ב-.env בלבד.
- טבלאות נפרדות = ה-`login` צריך לחפש בשתי הטבלאות (לקוח/קבלן) + מנהלים; החזר את התפקיד בטוקן. ודא ש-`user_name` ייחודי גם בין הטבלאות (או קדד תפקיד במפתח).
