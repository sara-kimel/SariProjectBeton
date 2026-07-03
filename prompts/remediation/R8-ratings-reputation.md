# שלב R8 — דירוג, מוניטין ודיווח (Ratings / Reputation / Report)

> פרומפט עצמאי לצ'אט חדש. **לפני שמתחילים:** קרא/י את SPEC.md (§18.3 + §17.1 בונוס אמון + §6 מכונות המצב + §7.2 טבלאות חדשות + §11 התראות) ואת prompts/README.md ו-prompts/remediation/README.md. ודא ש-R0 (תיקוני P0) בוצע ושחבילת הבדיקות ירוקה: מתוך `server/` הרץ `PYTHONUTF8=1 ./.venv/Scripts/python.exe -m pytest -q` → אמור להחזיר לפחות **52 passed** (דורש SQL Server מקומי + DB `beton` עם seed).

## מטרת השלב
להוסיף שכבת **אמון בין זרים** (SPEC §17.1, §18.3, שורה אחרונה): **דירוג הדדי 1–5 + הערה** לאחר עסקה שנסגרה, **מוניטין** (ממוצע דירוג המוצג לצד השני), ו**דיווח + חסימה** בסיסיים — כך שמשתמש בעייתי ניתן לדיווח, ומשתמש חסום אינו מותאם ואינו נחשף. זהו שלב **[מומלץ]/עתידי**: גם אם לא מיישמים מיד, **מתכננים את הסכימה מראש** ובונים מקצה-לקצה (DB→שרת→לקוח→E2E) כשאר השלבים.

## היקף
**נכלל:**
- טבלת **Ratings** חדשה — דירוג הדדי (מדרג/מדורג + תפקידים, ציון 1–5, הערה, קישור לעסקה הסגורה `match_id`), עם אכיפת "צד-לעסקה-סגורה בלבד, פעם אחת".
- טבלאות **UserReports** (דיווח) ו-**UserBlocks** (חסימה ברמת מנהל) + endpoints + UI מינימלי.
- **מוניטין:** endpoint שמחזיר ממוצע דירוג + מונה, והצגתו ליד פרטי הצד השני במסך העסקה הסגורה.
- **אכיפת חסימה** במנוע ההתאמה (חסום לא מותאם), בחשיפת פרטי-קשר ובהתחברות (חסום לא נכנס).
- מבנה מלא DB→models→dto→repository→service→controller→client→E2E, בסגנון phases 0-6.

**מחוץ להיקף:**
- **קאש מוניטין דנורמלי** (עמודת `avg_rating`/`ratings_count` על Customers/Contractors) — הממוצע מחושב בזמן-קריאה (`AVG`); דנורמליזציה = אופטימיזציה עתידית (ראה משימה 10, הערה).
- **חסימה הדדית משתמש-מול-משתמש** (block אישי שמסנן רק זוג נתון) — כאן החסימה היא **ברמת מנהל** (השעיה גלובלית); block אישי נשאר כהרחבה עתידית.
- תג "קבלן מאומת", תמונות לפנייה, ריבוי-שפות — כולם [עתידי] §17.1, לא בשלב זה.
- שינוי לוגיקת המנוע/אישור/הרשאות הקיימת (FIX-1..FIX-6) — לא נוגעים; רק **מוסיפים** מסנן חסימה.
- Web Push / SMS — הוכרע כנדחה (OD-13).

## משימות

### DB

1. **מיגרציה `server/db/migrations/006_ratings_reports.sql`** — סקריפט **אידמפוטנטי** בסגנון `004_notifications.sql`/`005_indexes.sql` (פתיחה `USE beton; GO`, `IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name='...')`, `PRINT` בתחילה/סוף, חלוקת `GO`). שלוש טבלאות חדשות (SPEC §7.2 — באותו קונבנציה של הטבלאות החדשות `OfferMatches`/`Notifications` שמשתמשות ב-`IDENTITY(1,1)`, כדי לא להתנגש בטווחי ה-IDENTITY הקיימים):
   - **`dbo.Ratings`** — דירוג הדדי הקשור לעסקה סגורה:
     `id INT IDENTITY(1,1) PK` · `match_id INT NOT NULL` (FK→`OfferMatches.id` — העסקה עצמה) · `request_id INT NULL` + `offer_id INT NULL` (דנורמליזציה לנוחות שליפה) · `rater_id INT NOT NULL` · `rater_role NVARCHAR(20) NOT NULL` (customer/contractor) · `ratee_id INT NOT NULL` · `ratee_role NVARCHAR(20) NOT NULL` · `score TINYINT NOT NULL` · `comment NVARCHAR(500) NULL` · `created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME()`.
     אילוצים: `CONSTRAINT FK_Ratings_match FOREIGN KEY (match_id) REFERENCES dbo.OfferMatches(id)`, `CONSTRAINT CK_Ratings_score CHECK (score BETWEEN 1 AND 5)`, ו**מפתח הייחודיות שאוכף "פעם אחת לכל כיוון"**: `CONSTRAINT UQ_Ratings_match_role UNIQUE (match_id, rater_role)` (לכל עסקה יש לקוח אחד וקבלן אחד — התפקיד מבחין בין שני הכיוונים). אינדקס לשליפת מוניטין: `IX_Ratings_ratee ON dbo.Ratings (ratee_id, ratee_role)`.
   - **`dbo.UserReports`** — דיווח על משתמש:
     `id INT IDENTITY(1,1) PK` · `reporter_id INT NOT NULL` · `reporter_role NVARCHAR(20) NOT NULL` · `reported_id INT NOT NULL` · `reported_role NVARCHAR(20) NOT NULL` · `reason NVARCHAR(1000) NOT NULL` (אי-הגעה/התנהגות/אחר — טקסט חופשי) · `related_match_id INT NULL` · `status NVARCHAR(20) NOT NULL DEFAULT 'OPEN'` · `created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME()` · `reviewed_at DATETIME2 NULL`. אילוץ enum: `CONSTRAINT CK_UserReports_status CHECK (status IN ('OPEN','REVIEWED','DISMISSED'))`. אינדקס `IX_UserReports_status ON dbo.UserReports (status, created_at)` (תור המנהל).
   - **`dbo.UserBlocks`** — חסימת משתמש ברמת מנהל (השעיה גלובלית, הפיכה):
     `id INT IDENTITY(1,1) PK` · `blocked_id INT NOT NULL` · `blocked_role NVARCHAR(20) NOT NULL` (customer/contractor) · `blocked_by INT NULL` (מזהה המנהל) · `reason NVARCHAR(500) NULL` · `is_active BIT NOT NULL DEFAULT 1` · `created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME()` · `released_at DATETIME2 NULL`. כדי למנוע כפל חסימה פעילה: **אינדקס ייחודי מסונן** `CREATE UNIQUE INDEX UX_UserBlocks_active ON dbo.UserBlocks (blocked_id, blocked_role) WHERE is_active = 1;`, ואינדקס שליפה מהיר למנוע `IX_UserBlocks_lookup ON dbo.UserBlocks (blocked_role, blocked_id, is_active)`.
2. **`server/db/schema.sql`** — הוסף את שלוש הטבלאות והאינדקסים גם ל-schema (המקור המלא של הסכימה), בסוף הקובץ, באותו סגנון כמו יתר הטבלאות (בהתאם לדפוס §18.2 "הקשחת DB — העתקת אינדקסי המיגרציה ל-schema.sql"). אל תיגע בטבלאות/עמודות הקיימות ו**אל תשנה שמות עמודות עם אותיות גדולות** (`Reliant`, `Stone_size`, `Purpose`, ...).

### שרת — מודלים ו-DTOs

3. **מודלים** — צור לפי דפוס `models/offer_match.py`/`models/notification.py` (Column + `from database import Base`, `server_default=text(...)`):
   - `server/models/rating.py` → `class Rating(Base)` (`__tablename__ = "Ratings"`), כל העמודות מהטבלה, `status` אין (אין), `score` כ-`Integer`/`SmallInteger`.
   - `server/models/user_report.py` → `class UserReport(Base)` (`__tablename__ = "UserReports"`).
   - `server/models/user_block.py` → `class UserBlock(Base)` (`__tablename__ = "UserBlocks"`).
   - רשום את שלושתם ב-`server/models/__init__.py` (כמו שם רשומים `OfferMatch`/`Notification`).
4. **DTOs** — צור לפי דפוס `dto/notification_dto.py` (`BaseModel` + `ConfigDict(from_attributes=True)`):
   - `server/dto/rating_dto.py`: `RatingCreateDTO { match_id: int, score: int (1..5, אמת עם `Field(ge=1, le=5)`), comment: Optional[str] }`; `RatingDTO` (פלט מלא); `ReputationDTO { average: Optional[float], count: int }`.
   - `server/dto/report_dto.py`: `ReportCreateDTO { reported_id: int, reported_role: str, reason: str, related_match_id: Optional[int] }`; `ReportDTO` (פלט לתור המנהל); `BlockCreateDTO { blocked_id: int, blocked_role: str, reason: Optional[str] }`; `BlockDTO`.

### שרת — repository ו-service

5. **`server/repository/rating_repository.py`** (דפוס `notification_repository.py`): `create(...)` (add+flush), `get_by_match_and_role(match_id, rater_role)` (לבדיקת קיום), `list_for_ratee(ratee_id, ratee_role)`, ו-`reputation(ratee_id, ratee_role)` → מריץ `AVG(score)` + `COUNT(*)` (החזר `average=None` כשאין דירוגים). SQL פרמטרי בלבד.
6. **`server/repository/report_repository.py`**: `create_report(...)`, `list_reports(status=None)` (לתור המנהל); `create_block(...)`, `release_block(...)` (עדכון `is_active=0`,`released_at`), `is_blocked(user_id, user_role) -> bool` (בדיקת חסימה פעילה יחידה — יישמש גם במנוע וגם בהתחברות), ו-`list_active_blocks()`.
7. **`server/service/rating_service.py`** → `class RatingService(db)` עם `create_rating(match_id, score, comment, current_user)` — **הכלל המרכזי (SPEC §17.1):**
   - שלוף את ה-`OfferMatch` לפי `match_id`; אם לא קיים → 404.
   - ודא שהעסקה **סגורה** — `OfferMatches.status == 'ACCEPTED'` (רק עסקה שנסגרה מזכה בדירוג; §6.3). אחרת → 409 "ניתן לדרג רק לאחר סגירת עסקה".
   - ודא שהמשתמש הנוכחי **צד לעסקה**: אם `current.role=='customer'` → `current.id == match.customer_id`; אם `current.role=='contractor'` → `current.id == offer.contractor_id` (שלוף `contractor_id` מ-`ContractorConcreteRequests WHERE request_id = match.offer_id`). אחרת → 403 "רק צד לעסקה יכול לדרג".
   - חשב את **המדורג** (הצד השני): אם המדרג לקוח → המדורג הוא הקבלן (`contractor_id`,role=`contractor`), ולהפך.
   - כתוב `Rating` עם `rater_id/rater_role/ratee_id/ratee_role`, `request_id=match.request_id`, `offer_id=match.offer_id`. **אכיפת "פעם אחת"**: בדוק `get_by_match_and_role(match_id, rater_role)` מראש → 409 "כבר דירגת עסקה זו", **וגם** עטוף את ה-insert ב-`try/except` על `IntegrityError` של `UQ_Ratings_match_role` (savepoint/rollback → 409), כהגנת-עומק מפני מרוץ (בדיוק כדפוס ה-savepoint על `OfferMatches` שב-§18.2).
   - **(אופציונלי, מומלץ)** צור התראת `RATING_RECEIVED` למדורג דרך `NotificationService` (הוסף מתודת-אירוע `notify_rating_received(...)` ל-`service/notification_service.py` — כמו `notify_offer_taken_to_customer`), באותה טרנזקציה. הוסף את הסוג לתיעוד ה-`type` שבראש `notification_service.py`.
   - `reputation(ratee_id, ratee_role)` — עוטף את ה-repo למוניטין.
8. **`server/service/moderation_service.py`** → `class ModerationService(db)`: `report_user(reporter, reported_id, reported_role, reason, related_match_id)` (ולידציה שהמדווח אינו מדווח על עצמו; יצירת `UserReports`); `block_user(admin, blocked_id, blocked_role, reason)` ו-`unblock_user(admin, block_id)` — **admin בלבד**; `is_blocked(user_id, role)` (מעביר ל-repo). **חשוב:** אין למחוק את המשתמש — חסימה היא `is_active` הפיך (soft, בדיוק כמו ה-soft-delete שאומץ ב-FIX-3).

### שרת — אכיפת חסימה (המסנן) והתחברות

9. **מנוע ההתאמה — סינון חסומים.** ב-`server/service/matching_engine_service.py`, במקום שבו נטענות הבקשות/הפניות הפתוחות (`load_data`, שמסננת כבר `WHERE [status]='OPEN'`, ~שורה 57) — **הוסף סינון** של בעלי חסימה פעילה: אל תכליל בקשה שלקוחה חסום ואל תכליל פנייה שקבלנה חסום. עדיף לממש כ-`AND NOT EXISTS (SELECT 1 FROM UserBlocks b WHERE b.is_active=1 AND b.blocked_role=:role AND b.blocked_id = <customer_id/contractor_id>)` בשאילתות הטעינה, כדי שהחסום **לא ייכנס למועמדים כלל** (חסום לא מותאם — דרישת המשימה). **אל תשבור** את זרימת המנוע הקיימת (§18.4 "לשמר, לא לגעת") — רק צמצם את קבוצת המקור. הוסף בדיקת רגרסיה (משימה 15) שמוודאת שהתנהגות המנוע ללא חסומים לא השתנתה.
10. **חשיפת פרטי-קשר ומוניטין.** בנקודת חשיפת הטלפון (סגירת עסקה, `service/deal_service.py`, `accept_match`) — הצג לצד המקבל גם את **המוניטין** של הצד השני (ממוצע+מונה), אם קיים. אין צורך לשנות את חוזה ה-`accept` בהכרח: אפשר להשאיר את החשיפה כפי שהיא ולתת ללקוח למשוך `GET /ratings/reputation/...` בנפרד (עדיף — פחות שינוי בליבה האטומית). ודא שמשתמש **חסום** אינו נחשף: בנקודות שמחזירות פרטי משתמש (למשל `/customers/{id}`, `/contractors/{id}` — כבר מוגנות owner-or-admin אחרי FIX-1), הוסף בדיקת `is_blocked` שמסתירה/חוסמת חשיפה של חסום למי שאינו admin. *(הערה: קאש דנורמלי של הממוצע — מחוץ להיקף; חשב בזמן-קריאה.)*
11. **התחברות.** ב-`server/service/auth_service.py` (או ב-`controller/auth_controller.py`, בנתיב ה-login) — לאחר אימות הסיסמה, אם `ModerationService(db).is_blocked(user_id, role)` → 403 "המשתמש חסום. פנה/י למנהל." כך משתמש חסום אינו מקבל טוקן. אל תשבור את בדיקות `test_auth.py` הקיימות (משתמשי-הבדיקה אינם חסומים).

### שרת — controllers ו-wiring

12. **`server/controller/rating_controller.py`** (דפוס `notification_controller.py`, `prefix="/ratings"`, `dependencies=[Depends(get_current_user)]`):
    - `POST /ratings/` — גוף `RatingCreateDTO`; קורא ל-`RatingService.create_rating(...)` עם `get_current_user`. (SPEC §8 — סגנון ה-endpoints.)
    - `GET /ratings/reputation/{role}/{user_id}` — מחזיר `ReputationDTO` (ממוצע+מונה). קריא לכל משתמש מאומת.
    - `GET /ratings/user/{role}/{user_id}` — רשימת הדירוגים (הערות) שקיבל המשתמש (לתצוגת מוניטין).
13. **`server/controller/moderation_controller.py`**:
    - `POST /reports/` — גוף `ReportCreateDTO`; כל משתמש מאומת מדווח (ModerationService).
    - `GET /admin/reports` — תור הדיווחים, **admin בלבד** (`Depends(require_admin)` מ-`service/security.py`).
    - `POST /admin/users/block` (גוף `BlockCreateDTO`) ו-`POST /admin/blocks/{block_id}/release` — **admin בלבד**.
    - חבר את שני ה-routers ב-`server/app.py` (בתבנית `app.include_router(...)` הקיימת; ראה שורות 58–70).

### לקוח

14. **API + טפסים + מוניטין** (React 19 + TS, RTL; דפוס `client/src/api/notifications.ts`, `client/src/api/matches.ts`):
    - `client/src/api/ratings.ts` — `createRating(payload)`, `getReputation(role, id)`, `getUserRatings(role, id)`; `client/src/api/reports.ts` — `reportUser(payload)`, ולמנהל `listReports()`, `blockUser(payload)`, `releaseBlock(id)`. הוסף טיפוסים תואמים ל-`client/src/api/types.ts` (`Rating`, `Reputation`, `Report`, `Block`).
    - **טופס דירוג במסך העסקה הסגורה:** ב-`client/src/pages/customer/RequestDetailPage.tsx` — כשהבקשה `CLOSED` ויש התאמה `ACCEPTED`, הצג רכיב `RatingForm` (בחירת 1–5 + הערה) לדירוג **הקבלן**; לאחר שליחה או כשכבר דורג → מצב "כבר דירגת". במקביל ב-`client/src/pages/contractor/OfferDetailPage.tsx` — כשהפנייה `CLOSED`, טופס דירוג **הלקוח**. חלץ רכיב משותף `client/src/components/RatingForm.tsx` (RTL, כפתורי כוכב/מספר, `aria-label` לנגישות בהתאם לדפוס R4).
    - **הצגת מוניטין:** ליד כרטיס פרטי-הקשר של הצד השני (במסכי העסקה הסגורה הנ"ל) הצג את הממוצע+מונה (`getReputation`). *(כשמסך הפרופיל מ-R5 קיים — הצג שם גם את המוניטין; אם R5 טרם בוצע, ההצגה ליד פרטי-הקשר מספקת.)* השתמש ב-`client/src/utils/format.ts` לעיצוב (למשל הצגת "★ 4.5 (12)"), והוסף עוזר פורמט אם צריך.
    - **דיווח:** כפתור "דווח" מינימלי בכרטיס הצד-השני (במסכי העסקה הסגורה) → טופס קטן (סיבה חופשית) → `reportUser`. Toast הצלחה.
    - **חסימה/דיווחים למנהל:** הרחב `client/src/pages/admin/UsersPage.tsx` בכפתור **חסום/שחרר** לכל משתמש (`blockUser`/`releaseBlock`), וצור `client/src/pages/admin/ReportsPage.tsx` (תור דיווחים, `listReports`) + נתיב `/admin/reports` ב-`client/src/App.tsx` (בתוך `RoleRoute allow={['admin']}`) וקישור ב-`Layout`/לוח המנהל.
    - שמור על מצבי טעינה/ריק/שגיאה ו-`aria-live` להודעות (בהתאם ל-R4/§12.7).

## בדיקת מקצה-לקצה (E2E)

15. **שרת — `server/tests/test_ratings.py` (חדש).** בנה תרחיש עם עסקה סגורה (נצל את עוזרי `test_accept.py`: `_mk_contractor/_mk_customer/_mk_offer/_mk_request/_mk_match` + `DealService.accept_match` שמביא ל-`ACCEPTED`; תגיות ניקוי בסגנון `PYTEST`-כלשהו, למשל `PYTEST8-`, עם `_wipe` ב-`finally`/fixture):
    - **מסלול חיובי:** אחרי אישור, הלקוח מדרג את הקבלן (score=5) → נוצר `Rating`, ו-`reputation('contractor', contractor_id)` מחזיר `average=5.0, count=1`; הקבלן מדרג את הלקוח → כיוון שני נשמר בנפרד (אותו `match_id`, `rater_role` שונה — לא מתנגש ב-`UQ_Ratings_match_role`).
    - **שלילי — לא צד לעסקה:** לקוח/קבלן זר מנסה לדרג → 403.
    - **שלילי — עסקה לא סגורה:** דירוג על `match` במצב `NOTIFIED` → 409.
    - **שלילי — כפילות:** אותו מדרג מדרג פעמיים את אותה עסקה → 409 (גם בבדיקה סדרתית וגם דרך אילוץ ה-UNIQUE).
    - **ממוצע:** שני דירוגים לאותו מדורג (על שתי עסקאות) → `average` הוא הממוצע, `count=2`.
16. **שרת — `server/tests/test_moderation.py` (חדש).**
    - **דיווח:** משתמש מדווח על אחר → נוצר `UserReports` בסטטוס `OPEN`; `GET /admin/reports` (כ-admin) מחזיר אותו; לא-admin → 403.
    - **חסימה מסתירה מהמנוע:** צור לקוח + בקשה תואמת שאמורה להתאים לפנייה; הרץ את המנוע **לפני** חסימה → יש התאמה; חסום את הלקוח (block פעיל) והרץ שוב על פנייה טרייה → **אין** התאמה ללקוח החסום (מוודא את משימה 9). שחרר → ההתנהגות חוזרת.
    - **חסום לא נכנס:** login של משתמש חסום → 403 (משימה 11).
    - **רגרסיה:** ודא שריצת המנוע ללא חסומים זהה לקודם (אין שינוי בקבוצת המועמדים כשאין UserBlocks פעילים).
17. **הרצה:** מתוך `server/` הרץ `PYTHONUTF8=1 ./.venv/Scripts/python.exe -m pytest -q` — **כל הבדיקות הקיימות עוברות + החדשות, אפס רגרסיות**. הרץ ממוקד: `... -m pytest tests/test_ratings.py tests/test_moderation.py tests/test_matching.py tests/test_auth.py -q`.
18. **לקוח:** מתוך `client/` הרץ `npm run build` (`tsc && vite build`) — עובר נקי (זכור `noUnusedLocals`/`verbatimModuleSyntax` — `import type` לטיפוסים). בדיקה ידנית בשני חלונות: עסקה נסגרת → כל צד מדרג את השני פעם אחת → המוניטין מתעדכן; דיווח נוצר ומופיע בתור המנהל; מנהל חוסם משתמש → המשתמש אינו מקבל התאמות חדשות ואינו מצליח להתחבר.

## הגדרת סיום
1. כל משימות ה-DB/שרת/לקוח בוצעו לפי הקובץ; הדירוג ההדדי, המוניטין, הדיווח והחסימה עובדים קצה-לקצה.
2. **חבילת ה-pytest ירוקה** (הקיימות + `test_ratings.py` + `test_moderation.py`, בלי רגרסיות), וגם **`npm run build`** בלקוח עובר.
3. עדכן `SPEC.md` §18.3 — סמן את הפריט **"דירוג/מוניטין + דיווח/חסימה"** כ-✅ עם ציון מה יושם (דירוג הדדי חד-פעמי לעסקה סגורה, מוניטין בזמן-קריאה, דיווח, חסימת-מנהל ואכיפתה במנוע/התחברות/חשיפה) ומה נותר עתידי (קאש דנורמלי, block אישי, תג מאומת). עדכן בהתאמה את המראה הקריא `SPEC.html`. שקול לסמן את הבונוסים המתאימים ב-§17.1 ("דירוג ומוניטין", "דיווח וחסימה").
4. עדכן את הזיכרון `memory/project-sari-state.md` (מנוהל דרך `memory/MEMORY.md`): נוספו טבלאות `Ratings`/`UserReports`/`UserBlocks`, מנוע ההתאמה מסנן חסומים, מספר הבדיקות המעודכן.
5. סיכום קצר למשתמש: מה נבנה (דירוג/מוניטין/דיווח/חסימה), איך נאכפת ההגבלה "צד-לעסקה-סגורה, פעם אחת", איך חסימה משפיעה על התאמה/התחברות/חשיפה, איך נבדק, ומה נותר עתידי. זהו **השלב האחרון במסלול התיקונים (R0–R8)** — ציין שהמסלול הושלם.

## הערות/מלכודות
- **שלב [מומלץ]/עתידי:** אם מיישמים חלקית — לפחות **הסכימה (מיגרציה 006 + schema.sql) והמודלים חייבים להיכתב מראש** (דרישת המשימה: "לתכנן את הסכימה מראש גם אם לא מיישמים מיד"). אל תשאיר את ה-DB חצי-מוגדר.
- **אל תשבור את הבדיקות הקיימות ואת §18.4 ("לשמר, לא לגעת"):** המנוע הדו-כיווני, האישור האטומי first-wins, וה-soft-delete של FIX-3 נשארים כפי שהם — R8 רק **מוסיף** טבלאות ומסנן חסימה. הרץ את הסוויטה אחרי כל שינוי.
- **הגבלת "פעם אחת" נאכפת בשתי שכבות:** בדיקה מקדימה בשירות **וגם** `UNIQUE (match_id, rater_role)` ב-DB (הגנת-עומק מפני מרוץ) — אל תסתמך רק על אחת מהן, בדיוק כדפוס ה-savepoint על ה-`OfferMatches` שב-§18.2.
- **"עסקה סגורה" = `OfferMatches.status='ACCEPTED'`** (לא רק `ConcreteRequests.status='CLOSED'`) — זו הרשומה שקושרת את שני הצדדים (§6.3). דרג תמיד מול `match_id`.
- **חסימה = soft/הפיך** (`is_active` + `released_at`) — לעולם לא למחוק משתמש (עקבי עם החלטת ה-soft-delete של FIX-3). ה-`UNIQUE` המסונן מונע כפל חסימה פעילה.
- **`requirements.txt` נשאר ASCII** — לא נדרשות תלויות שרת חדשות (SQLAlchemy/FastAPI/pytest כבר קיימים).
- **שמות עמודות באותיות גדולות** (`Reliant`, `Stone_size`, `Purpose`, `Reliant_id`, `Stone_size_id`, `Purpose_id`) ו-`ContractorConcreteRequests.id_customer` (ה-FK לבקשה שאישרה) — **לא לשנות**; ה-SQL בטבלאות החדשות עומד בפני עצמו ואינו נוגע בהם.
- **RTL עברית** בכל טקסט (הודעות שרת, כותרות/הערות, תוויות UI); הודעות שגיאה בגוף `{ "detail": "..." }` בעברית (§8.7). ב-UI שמור על `aria-label`/`aria-live` (נגישות, R4/§12.7).
- **מרוץ הדירוג הכפול** אינו קריטי כמו מרוץ האישור — אך עדיין השתמש ב-savepoint/rollback על ה-`IntegrityError` כדי להחזיר 409 נקי במקום 500.
- **ניקוי נתוני בדיקה:** תגית ייחודית (למשל `PYTEST8-`) ו-`_wipe`/`finally` בכל בדיקה חדשה, כדי לא להזליג ל-DB `beton` החי (כמו יתר קבצי הבדיקה).
