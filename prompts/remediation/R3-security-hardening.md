# שלב R3 — הקשחת אבטחה (Security Hardening)

> פרומפט עצמאי לצ'אט חדש. **לפני שמתחילים:** קרא/י את SPEC.md (§18 + סעיפים רלוונטיים) ואת prompts/README.md ו-prompts/remediation/README.md. ודא ש-R0 (תיקוני P0) בוצע ושחבילת הבדיקות ירוקה.

## מטרת השלב
לסגור חמישה ליקויי אבטחה מדרג P1 (§18.2, שורת "אבטחה נוספת" + §10): ביטול טוקנים בשינוי/איפוס סיסמה, הקשחת ה-rate-limit, סיסמת admin ראשונית מחוץ לקוד + אכיפת החלפה, צמצום מניית שמות משתמש (enumeration), ועטיפת ה-insert ל-`OfferMatches` ב-savepoint. אלה תיקוני עומק בשרת/DB בלבד — לא נגיעה במנוע ההתאמה ולא בזרימות שכבר אומתו כתקינות (§18.4).

## היקף
**נכלל:** עמודות `token_version` + `must_change_password` בשלוש טבלאות המשתמשים (Customers/Contractors/Admins) + מיגרציה + עדכון schema.sql + מודלים; שילוב `token_version` ב-JWT ובבדיקת ה-decode; העלאת הגרסה בכל change/reset; הקשחת `service/rate_limit.py`; קריאת סיסמת ה-admin מ-env ב-`db/seed.py` + הגנת פרודקשן + דגל החלפה כפויה; bcrypt-דמה בכניסה למניעת הבדל תזמון; savepoint ב-`repository/offer_match_repository.py`.

**מחוץ להיקף:** FIX-1 (הרשאות `/customers`+`/contractors`) ו-FIX-4 (fail-fast על JWT_SECRET) — **כבר בוצעו ב-R0, לא לגעת**. מסך פרופיל/שינוי-סיסמה בצד לקוח (§12.6) ומצבי שגיאה/נגישות בלקוח — שייכים ל-R4/R5. Redis תשתיתי מלא, refresh-tokens ו-CI — לא כאן.

## משימות

### DB — עמודות, מיגרציה ומודלים

1. **מיגרציה חדשה `server/db/migrations/006_security_hardening.sql`** (הבא בתור אחרי `005_indexes.sql`; אם R2 כבר תפס את מספר 006 — קדם למספר הפנוי הבא). אידמפוטנטי בסגנון המיגרציות הקיימות (`USE beton; GO`, `PRINT`, בדיקות `COL_LENGTH(...) IS NULL`). לכל אחת מ-`dbo.Customers`, `dbo.Contractors`, `dbo.Admins` להוסיף:
   - `token_version INT NOT NULL CONSTRAINT DF_<Table>_token_version DEFAULT 0` — גרסת הטוקן הפעילה; העלאתה פוסלת טוקנים ישנים (§10, OD-12).
   - `must_change_password BIT NOT NULL CONSTRAINT DF_<Table>_must_change DEFAULT 0` — אכיפת החלפת סיסמה זמנית בכניסה ראשונה.
   (אופציונלי חלופי לפי §18.2: `password_changed_at DATETIME2 NULL` במקום `token_version` — אם בוחרים בו, השוואת ה-`iat` של הטוקן מולו במקום השוואת גרסה. הפרומפט הזה נוקט ב-`token_version` כמנגנון הראשי כי הוא פשוט ודטרמיניסטי.)

2. **`server/db/schema.sql`** — לשקף את שתי העמודות בהגדרות שלוש הטבלאות (Customers סביב שורות 44–54, Contractors 61–71, Admins 78–87), מיד אחרי `password_hash`, בדיוק כמו במיגרציה. **לא לשנות שמות/טיפוסים של עמודות קיימות ולא את טווחי ה-IDENTITY** (Customers 100 / Contractors 300 / Admins 1).

3. **מודלים** — להוסיף את שתי העמודות ל-`server/models/customer.py`, `server/models/contractor.py`, `server/models/admin.py`:
   `token_version = Column(Integer, nullable=False, server_default=text("0"))` ו-`must_change_password = Column(Boolean, nullable=False, server_default=text("0"))` (לייבא `Boolean` מ-`sqlalchemy`). לשמור על הסגנון והתיעוד הקיימים בקבצים.

### שרת — ביטול טוקנים בשינוי/איפוס סיסמה (משימה 1)

4. **`server/service/auth_service.py`** — `create_access_token` (שורות 37–46): להוסיף פרמטר `token_version: int` ולכלול אותו ב-payload כ-`"tv": int(token_version)`. (ה-`sub`/`role`/`iat`/`exp` נשמרים.)

5. **`server/service/security.py`** — `get_current_user` (שורות 18–36) כרגע חסר-מצב (רק decode). לחזק אותו כך שיאמת את גרסת הטוקן מול ה-DB:
   - להוסיף תלות `db: Session = Depends(get_db)` (מ-`database`). FastAPI מאחד את אותו סשן עם שאר התלויות בבקשה — אין פתיחת סשן כפול.
   - אחרי ה-decode, לטעון את רשומת המשתמש לפי `role`+`id` ולהשוות `payload.get("tv")` ל-`user.token_version`; אי-התאמה (או `tv` חסר / משתמש לא קיים) → `401` ("הטוקן בוטל — יש להתחבר מחדש"). כדי לא לשכפל את `_get_user_record` מ-`auth_controller`, להוציא helper משותף (למשל `service/user_directory.py::load_user(db, role, id)` הממפה role→repository) ולהשתמש בו בשני המקומות.
   - **אכיפת החלפה כפויה:** אם `user.must_change_password` פעיל ונתיב הבקשה אינו ברשימת-היתר (`/auth/change-password`, `/auth/me`, `/auth/login`, `/health`) → `403` עם `{"detail": "יש להחליף את הסיסמה הזמנית לפני המשך", "code": "MUST_CHANGE_PASSWORD"}` (את הנתיב אפשר לקרוא דרך תלות `request: Request`).
   - ⚠️ **הערת תזמון-שינוי:** מרגע הפריסה כל הטוקנים הישנים (ללא `tv`, או עם `tv` שאינו תואם) ייפסלו — התנהגות רצויה, אך יש לתעד. הבדיקות מייצרות טוקנים טריים ולכן אינן נשברות.

6. **`server/controller/auth_controller.py`** — לחווט את הגרסה:
   - `login` (99–109) ו-`_register` (58–77): `create_access_token(user.id, role, user.token_version)`. משתמש חדש נוצר עם `token_version=0` (ברירת המחדל).
   - `change_password` (130–145): באותו commit, בנוסף ל-`password_hash`, להעלות `user.token_version += 1` ו-`user.must_change_password = False` (לנקות את הדגל).
   - `admin_reset_password` (149–163, OD-12): להעלות `user.token_version += 1` ו-`user.must_change_password = True` (לחייב את המשתמש להחליף לאחר איפוס). כך איפוס/שינוי פוסלים מיידית כל טוקן קודם של אותו משתמש.

### שרת — הקשחת rate limiting (משימה 2)

7. **`server/service/rate_limit.py`** — כרגע `_buckets` הוא `dict` per-process לפי `request.client.host`, ללא הגבלת גודל, וללא קריאה נכונה מאחורי proxy. להקשיח (§10):
   - **מקור IP מהימן:** לקרוא `X-Forwarded-For` **רק** כאשר `settings.RATE_LIMIT_TRUST_PROXY` פעיל (מאחורי reverse-proxy/NetFree), ואז לקחת את ה-hop המהימן (למשל ה-IP הימני-ביותר או לפי מספר proxies מוגדר) במקום להסתמך על `request.client.host`. ללא הדגל — להישאר על `request.client.host` כדי לא לבטוח בכותרת שהלקוח יכול לזייף.
   - **הגבלת גודל המילון:** ניקוי דלי ריק (`if not dq: del _buckets[key]`) בכל מעבר, ותקרת מפתחות (`RATE_LIMIT_MAX_KEYS`, ברירת מחדל למשל 10000) עם פינוי LRU/ישן כשעוברים אותה — כדי למנוע גדילה בלתי-מוגבלת/DoS זיכרון.
   - **מגבלה פר-`user_name` בכניסה:** ב-`login` להוסיף דלי נוסף לפי שם המשתמש (למשל scope `"login_user"`) כדי לחסום ניחוש סיסמה ממוקד גם כשה-IP מתחלף. לממש כפונקציית עזר שה-controller קורא עם ה-`user_name` מגוף הבקשה (לא כ-dependency, כי הגוף לא זמין ל-dependency ללא קריאה כפולה).
   - **תיעוד קנה-מידה:** להשאיר את המימוש per-process אך לתעד בראש הקובץ ש**לריבוי workers/instances נדרש Redis או הישענות על ה-proxy**, ולהשאיר תפר (interface) שמאפשר החלפה עתידית. **חובה לשמר את פטור ה-`testclient`** (`_EXEMPT_HOSTS`) ואת כיבוי ה-flag `RATE_LIMIT_ENABLED` — אחרת סוויטת הבדיקות (שמריצה הרבה login/register מאותו host) תישבר.

8. **`server/config.py`** — להוסיף את ההגדרות התומכות ב-`Settings` (ליד שאר `RATE_LIMIT_*` בשורות 73–78): `RATE_LIMIT_TRUST_PROXY` (`bool`, ברירת מחדל `false`), `RATE_LIMIT_MAX_KEYS` (`int`), ו-`RATE_LIMIT_LOGIN_USER_MAX` (`int`, מגבלת ניסיונות פר-שם-משתמש בחלון). כולם נקראים מ-`os.getenv` בדיוק כמו ההגדרות הקיימות.

### שרת — סיסמת admin ראשונית + חוסן seed (משימה 3)

9. **`server/db/seed.py`** — כרגע `ADMIN_SEED=('admin','Admin!2026')` ו-`DEMO_PASSWORD='demo123'` מקובעים ומודפסים לקונסולה (שורות 32–34, 210–211):
   - לקרוא את סיסמת ה-admin מ-`os.getenv("ADMIN_PASSWORD")`. **בפרודקשן** (`settings.APP_ENV in {"production","prod"}`) — ללא ברירת מחדל: אם `ADMIN_PASSWORD` חסר, להעלות `SystemExit`/`RuntimeError` ברור. בפיתוח בלבד מותר fallback לערך הנוכחי (לנוחות בדיקות/דמו).
   - **הגנת הרצה בפרודקשן:** ה-`main()` מבצע `DELETE FROM` לכל הטבלאות (איפוס הרסני). להוסיף בראש `main()` שער: אם `APP_ENV` הוא production — לסרב לרוץ אלא אם הועבר דגל מפורש (למשל `SEED_ALLOW_PROD=1`), כדי למנוע מחיקת נתוני אמת.
   - בהוספת ה-admin (שורות 154–161): לקבוע `must_change_password = 1` עבור המנהל הראשוני (סיסמה זמנית → חובה להחליף בכניסה הראשונה). **את משתמשי הדמו (Customers/Contractors) להשאיר `must_change_password = 0`** כדי לא לשבור זרימות E2E/בדיקות שמתחברות כמשתמשי דמו וכדי שהשער מ-משימה 5 לא יחסום אותם. (ה-`must_change_password` על ה-admin לא שובר את `test_admin.py`, כי היא נכנסת עם ה-admin ואז השער חוסם רק אם הדגל פעיל — אם הבדיקות נכנסות ל-admin ומצפות לגשת ל-`/admin/*`, יש להעמיד את ה-seed של ה-admin ל-`0` **או** להתאים את הבדיקה; ברירת המחדל הבטוחה לשמירת ה-52 הירוקות היא `admin=0` והדגמת האכיפה דרך `admin_reset_password` שמדליק `must_change_password=1` על היעד. בחר/י את הגישה שלא שוברת את הסוויטה ותעד/י).
   - להסיר את הדפסת הסיסמאות הגלויות לקונסולה בפרודקשן (בפיתוח מותר רמז, לא הסיסמה עצמה).

10. **`server/dto/auth_dto.py`** — להוסיף ל-`TokenDTO` שדה `must_change_password: bool = False`, ולמלא אותו ב-`login` מ-`user.must_change_password`, כדי שהלקוח (R5) יוכל להפנות למסך החלפת סיסמה. (אין שינוי ב-`RegisterDTO`.)

### שרת — צמצום מניית שמות משתמש / enumeration (משימה 4)

11. **`server/service/auth_service.py`** — להוסיף hash-דמה קבוע (מחושב פעם אחת ברמת המודול, למשל `_DUMMY_HASH = hash_password("timing-equalizer")`) ופונקציה `verify_dummy()` שמריצה `bcrypt.checkpw` מולו. המטרה: להשוות תזמון גם כשהמשתמש לא נמצא.

12. **`server/controller/auth_controller.py`** — `login` (99–109): כרגע `verify_password` (bcrypt היקר) רץ רק כשהמשתמש קיים → הבדל תזמון מסגיר קיום שם משתמש. לתקן כך שגם כשאף מועמד לא נמצא (או שנמצא אך הסיסמה שגויה) **תמיד תרוץ בדיוק פעולת bcrypt אחת** — אם לא נמצא מועמד, לקרוא ל-`verify_dummy()` לפני החזרת `401`. ההודעה נשארת אחידה ("שם משתמש או סיסמה שגויים", ללא הבחנה בין שם לא-קיים לסיסמה שגויה).
    - **register (§17.1):** `_register` מחזיר `409 "שם המשתמש כבר תפוס"` שמאשר קיום שם. לשקול הודעה גנרית יותר / לתעד את ה-trade-off (חוויית משתמש מול enumeration). לכל הפחות לוודא שהניסוח לא חושף באיזו טבלה (role) השם קיים. אם משנים את קוד/הטקסט — לוודא ש-`test_duplicate_username_409` (המצפה ל-409) עדיין עובר, או לעדכן אותו במפורש.

### שרת — savepoint ב-create_notified (משימה 5)

13. **`server/repository/offer_match_repository.py`** — `create_notified` (שורות 63–87) בודק `exists()` ואז `add`+`flush` — לא אטומי מול `UQ_OfferMatches_offer_request UNIQUE(offer_id, request_id)`. בטריגר הדו-כיווני שני מסלולים יכולים לנסות להכניס את אותו זוג, וה-`IntegrityError` בזמן ה-`flush` מפיל את **כל** הטרנזקציה (הפנייה/הבקשה + שאר ההתאמות + ההתראות — בניגוד לאטומיות §5.4). לעטוף את ה-`flush` ב-savepoint:
    - להשאיר את בדיקת `exists()` כמסלול המהיר, ובנוסף לעטוף את `self.db.add(match)` + `self.db.flush()` ב-`with self.db.begin_nested():` (SAVEPOINT), וללכוד `IntegrityError` (מ-`sqlalchemy.exc`) → ה-savepoint בלבד מתגלגל אחורה, מחזירים `None` ("כבר קיים") **בלי** להפיל את הטרנזקציה החיצונית. כך ה-commit של שירות התזמור נשאר תקין.
    - לוודא שהחתימה/החוזה לא משתנים (עדיין `Optional[OfferMatch]`, עדיין ללא commit — ה-commit באחריות המתזמן).

## בדיקת מקצה-לקצה (E2E)

1. **הרצת הסוויטה:** `cd server && PYTHONUTF8=1 ./.venv/Scripts/python.exe -m pytest -q` → כל הבדיקות עוברות ללא regressions (בסיס: 52). דורש SQL Server מקומי + DB `beton` **לאחר הרצת המיגרציה 006** (`sqlcmd -S localhost -E -C -i db\migrations\006_security_hardening.sql`) וריצת `python db/seed.py`.
2. **בדיקות חדשות מומלצות** (למשל `server/tests/test_security.py` הקיים / קובץ ייעודי):
   - *ביטול טוקן:* הרשמה → קבלת טוקן → `POST /auth/change-password` → קריאה מוגנת עם **הטוקן הישן** מחזירה `401`, ועם טוקן חדש `200`. וכן `admin_reset_password` פוסל טוקן קודם של היעד.
   - *enumeration:* `login` לשם-משתמש לא-קיים ולשם-קיים-עם-סיסמה-שגויה מחזירים אותו `401` ואותה הודעה (ושתי הדרכים מריצות bcrypt — לאמת שאין קריסה על משתמש חסר).
   - *savepoint:* קריאה ל-`create_notified` פעמיים לאותו זוג `(offer_id, request_id)` באותו סשן → שורה אחת בלבד, החזרה שנייה `None`, והטרנזקציה עדיין ניתנת ל-commit (לא abort). ניתן גם דרך תרחיש מנוע דו-כיווני קיים.
   - *rate-limit פר-user:* מעל המכסה לאותו `user_name` מחזיר `429` (עם `RATE_LIMIT_ENABLED=true` וממקור שאינו `testclient`), ובדיקות רגילות עדיין עוברות בזכות פטור ה-`testclient`.
3. `cd client && npm run build` — נקי (אין שינוי חוזה שבור; `TokenDTO.must_change_password` הוא שדה אופציונלי חדש).
4. אין regressions מול R0 ומול phases 0–6.

## הגדרת סיום
- כל משימות ה-DB/שרת בוצעו לפי הקובץ; המיגרציה 006 הורצה ו-`schema.sql`+המודלים מסונכרנים.
- **חבילת ה-pytest ירוקה** (בלי regressions) ו-`npm run build` עובר.
- עדכון `SPEC.md` §18.2 — סימון ✅ לפריטי "אבטחה נוספת" שבוצעו (ביטול טוקנים, הקשחת rate-limit, סיסמת admin מ-env, enumeration, savepoint), ובמראה `SPEC.html`.
- עדכון הזיכרון `memory/project-sari-state.md`: העמודות החדשות (`token_version`, `must_change_password`), שינוי הסמנטיקה של `get_current_user` (כעת נוגע ב-DB ומאמת גרסת טוקן), אכיפת `must_change_password`, וסיסמת ה-admin מ-`ADMIN_PASSWORD`.
- סיכום קצר למשתמש: מה הוקשח, איך נבדק, ומה הבא (R4 — הקשחת לקוח).

## הערות/מלכודות
- **לא לחזור על R0:** FIX-1 (הרשאות `/customers`+`/contractors`) ו-FIX-4 (fail-fast על JWT_SECRET ב-`config.py`) כבר בוצעו — לא לגעת.
- **לא לשבור את 52 הבדיקות:** להריץ את הסוויטה אחרי כל שינוי. הסיכונים העיקריים: (א) `must_change_password` על משתמשי seed שחוסם זרימות בדיקה — להשאיר משתמשי דמו על `0`; (ב) מגבלת rate-limit פר-user שחוסמת בדיקות — לשמר את פטור ה-`testclient` ואת `RATE_LIMIT_ENABLED`; (ג) פסילת טוקן ישן שמפילה בדיקות — הבדיקות מייצרות טוקנים טריים, ודא/י שכל טוקן חדש כולל `tv` תואם.
- **שמות עמודות קיימים לא נשברים:** `Reliant`/`Stone_size`/`Purpose`/`Reliant_id`/`Stone_size_id`/`Purpose_id` וה-FK `ContractorConcreteRequests.id_customer→ConcreteRequests.request_id` — כמו שהם. העמודות החדשות בלבד מתווספות.
- **מיגרציה אידמפוטנטית:** אך ורק בסגנון הקבצים הקיימים (בדיקות `COL_LENGTH ... IS NULL` לפני `ALTER TABLE ADD`), עם `USE beton; GO` ו-`PRINT` פתיחה/סיום.
- **טווחי IDENTITY לא נוגעים** (Customers 100 / ConcreteRequests 200 / Contractors 300 / ContractorConcreteRequests 600 / lookups 1100–2000).
- **`requirements.txt` נשאר ASCII** — אם מוסיפים תלות (אין צורך אמיתי כאן; bcrypt/jwt כבר קיימים) — לוודא קידוד. עדיף שלא להוסיף Redis כתלות בשלב זה (רק תפר/תיעוד).
- **RTL עברית** בכל הודעות השגיאה החדשות (`401`/`403`/`429`), בפורמט `{"detail": "..."}` האחיד של הפרויקט.
- **`get_current_user` נעשה stateful:** הוא כעת מבצע שאילתת DB לכל בקשה מאומתת. זו העלות המקובלת של ביטול טוקנים ל-JWT חסר-מצב; לתעד ולוודא שהסשן משותף (אותו `get_db`) ולא נפתח כפול.
