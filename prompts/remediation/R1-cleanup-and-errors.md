# שלב R1 — ניקוי קוד מת, טיפול-שגיאות אחיד ושכבתיות (Cleanup / Errors / Layering)

> פרומפט עצמאי לצ'אט חדש. **לפני שמתחילים:** קרא/י את `SPEC.md` (§18 + §8.7 + §9 + §14) ואת `prompts/README.md` ו-`prompts/remediation/README.md`. ודא ש-R0 (תיקוני P0, §18.1 FIX-1..FIX-6) בוצע ושחבילת הבדיקות ירוקה (52 בדיקות שרת: `pytest` מתוך `server/`, דורש SQL Server מקומי + DB `beton` עם seed).

## מטרת השלב
לנקות את שכבת ה-`service/` מקבצי ניסוי/זבל ומ**מוקשים רדומים** (בעיקר הכפלת מחיר ×2 בסתירה ל-§14), לאחד את טיפול השגיאות בשרת לפורמט עברי עקבי (§8.7), ולהחזיר את שני הבקרים שחורגים מהשכבתיות (§9) לזרימה `controller → service → repository`. שלב זה **לא מוסיף פיצ'ר** — הוא הקשחת איכות בלבד, בלי לשבור התנהגות קיימת.

## היקף
**נכלל:** מחיקת 5 קבצי קוד מת ב-`server/`, שינוי-שם/מיזוג של `contractor_matching_controller.py`, הוספת `exception_handler`-ים ב-`app.py`, החזרת `admin_controller`/`auth_controller` לשכבתיות תקינה, ועדכוני תיעוד (SPEC/README) שנגזרים מהמחיקות.
**מחוץ להיקף:** הקשחת DB (אינדקסים/CHECK/NOT NULL — §18.2, שלב R2), אבטחה נוספת (ביטול טוקנים/rate-limit — §18.2), שיפורי לקוח (§18.2/§18.3), והשלמות P2 (§18.3). אין שינוי DB, אין שינוי `requirements.txt`, אין שינוי בלקוח בשלב זה.

## משימות

### שרת — ניקוי קוד מת ומוקשים (§18.2, §14)
1. **מחיקת 5 קבצים מתים.** לפני כל מחיקה הרץ `grep`/Grep על שם המודול והמחלקה כדי לוודא שאין ייבוא חי (מחוץ לקובץ עצמו ולתיעוד). כבר אומת שאף בקר/שירות חי אינו מייבא אותם:
   - `server/service/contractor_concrete_service.py` — קורא ל-`double_price_from_string` ומכפיל מחיר; אינו מיובא (השירות החי לפניות הוא `service/contractor_concrete_request_service.py`, שם שונה).
   - `server/service/price_service.py` — **⚠️ מוקש רדום:** `double_price_from_string` מכפיל את המחיר ×2 (שורה 12: `return str(price * 2)`), בסתירה ישירה להחלטת §14 (המחיר נשמר/מוצג **כפי שהוזן**, מודל תיווך). לא מחובר ל-`/send/`, אך חייב להימחק כדי שלא יחזור לשימוש בטעות.
   - `server/service/candidate_selector.py` — `CandidateSelector.get_candidate_requests` מריץ `EXEC GetCandidateRequests` (Stored Procedure שאינו קיים במאגר) + `print(candidates)` (שורה 67). מת לחלוטין.
   - `server/service/region_service.py` — `RegionService` שכל מתודה בו מעלה `NotImplementedError`; אינו מיובא בשום מקום.
   - `server/utils.py` — קובץ ריק.
   - לאחר המחיקה נקה גם `__pycache__` תואם אם נוצר, והרץ את הסוויטה (`pytest`) לוודא ירוקה.

2. **שינוי-שם/מיזוג של `server/service/contractor_matching_controller.py`** (§18.2 — "שם מטעה"). הקובץ נקרא `*_controller` אך אינו בקר: הוא מכיל רק את המחלקה `TestService` (`run_pipeline`), ומופעל **אך ורק** מבדיקת העשן `server/tests/e2e/test_engine_smoke.py` (אומת ב-grep — אין שום בקר/שירות חי שמייבא אותו; ההערה ב-`prompts/README.md:54` על הפעלה מ-`/send/` התיישנה, המנוע החי רץ ישירות דרך `matching_engine_service`).
   - שנה את שם הקובץ ל-`server/service/engine_pipeline.py` ואת שם המחלקה מ-`TestService` ל-`EnginePipeline` (שם שאינו מתחיל ב-`Test`, כדי ש-pytest לא ינסה לאסוף אותו כמחלקת בדיקות — מה שמייתר את הפתרון-עוקף שמתועד ב-`test_engine_smoke.py:22-23`).
   - עדכן את `server/tests/e2e/test_engine_smoke.py`: שורה 24 `import service.engine_pipeline as matching_pipeline`, שורה 51 `matching_pipeline.EnginePipeline(db).run_pipeline(offer)`. אפשר להסיר/לעדכן את הערת ה-workaround בשורות 22-23 (כבר לא נחוצה משיצא שם ה-`Test`).
   - שמור על גוף `run_pipeline` כפי שהוא (הצינור גיאו→מטרה→כמות דרך `matching_engine_service`) — זו לוגיקה מאומתת (§18.4), רק שם הקובץ/המחלקה משתנים.

### שרת — טיפול שגיאות אחיד (§8.7)
3. **הוספת `exception_handler`-ים ב-`server/app.py`.** כיום אין אף handler רשום, ולכן שגיאת ולידציה מחזירה את רשימת-האובייקטים הדיפולטית של FastAPI (לא עברית, לא `{"detail": "..."}` אחיד), וחריגה לא-מטופלת מחזירה 500 גנרי. הוסף מעל חיבור ה-routers (או מיד אחריו):
   - handler ל-`fastapi.exceptions.RequestValidationError` → `JSONResponse(status_code=422, content={"detail": "..."})` עם **מחרוזת עברית מגובשת** (למשל `"הנתונים שנשלחו אינם תקינים"`; אופציונלי — לבנות הודעה מפורטת יותר מ-`exc.errors()` בעברית, אך מחרוזת אחת מספיקה ל-MVP).
   - handler ל-`Exception` → `JSONResponse(status_code=500, content={"detail": "שגיאת שרת"})`, **תוך רישום ה-traceback ללוג** (`logging.getLogger(...).exception(...)`). אל תבלע את החריגה בשקט.
   - **אל תרשום handler ל-`HTTPException`/`StarletteHTTPException`** — ה-`HTTPException`-ים שנזרקים בקוד (auth/ownership וכו') כבר מחזירים `{"detail": "..."}` בעברית ובסטטוס הנכון, ו-FastAPI מטפל בהם לפני ה-handler הגנרי. שינוי שלהם יסכן בדיקות קיימות (401/403/404/409).
   - **`request-id` (אופציונלי, "לשקול" ב-§18.2):** אם מוסיפים — middleware קליל שמייצר `uuid4`, שם אותו על `request.state.request_id` ומחזיר בכותרת `X-Request-ID`, וכולל אותו בשורת הלוג של ה-500. אל תסבך; אפשר לדלג אם קצר בזמן.

### שרת — החזרת שכבתיות (§9)
4. **`server/controller/admin_controller.py` — הוצאת גישת-DB ישירה מהבקר** (שורות ~27-55). כרגע הבקר מריץ `db.query(Customer).all()`/`db.query(Contractor).all()` ב-`list_users` (שורות 27-36) ו-חמש שאילתות `db.execute(text(...))` ב-`stats` (שורות 43-55) — חריגה מ-§9 (בקר לא ניגש ל-DB ישירות).
   - העבר את ההרכבה לשירות חדש `server/service/admin_service.py` (`list_all_users()`, `get_stats()`), שיישען על ה-repositories: `CustomerRepository.get_all()` ו-`ContractorRepository.get_all()` **כבר קיימים** ומחזירים את הרשומות; את חמש הספירות (`ConcreteRequests` OPEN, `ContractorConcreteRequests` OPEN/CLOSED, `OfferMatches` total/ACCEPTED) העבר למתודות `count_*`/`count_by_status` ב-repositories המתאימים (`concrete_request_repository`, `contractor_concrete_request_repository`, `offer_match_repository`) — SQL פרמטרי, בלי מחרוזות מודבקות.
   - הבקר יישאר דק: `Depends(get_current_admin)` (כפי שהוא היום ברמת ה-router) + קריאה לשירות + מיפוי ל-`AdminUserDTO`/`AdminStatsDTO`. **שמור על אותם שמות עמודות/סטטוסים בדיוק** (`[status]='OPEN'/'CLOSED'/'ACCEPTED'`, טבלת `OfferMatches`) כדי לא לשנות ערכי הפלט.
5. **`server/controller/auth_controller.py` — שימוש ב-`set_password_hash` במקום `commit` ישיר.** בשתי נקודות הבקר מבצע `user.password_hash = hash_password(...)` ואז `db.commit()` ישירות (חריגה מ-§9):
   - `change_password` — שורות 143-144.
   - `admin_reset_password` — שורות 161-162.
   - בשתיהן החלף ל-`repo.set_password_hash(user, hash_password(...))`. המתודה `set_password_hash` **כבר קיימת** ב-`CustomerRepository` (שורה 57), `ContractorRepository` (שורה 47) ו-`AdminRepository` (שורה 32). מכיוון ש-`_get_user_record` מחזיר רשומת ORM לפי תפקיד, בחר את ה-repo המתאים לפי `current["role"]`/`data.role` (customer/contractor/admin). שמור על אותה תגובת JSON ואותם קודי סטטוס (401 על סיסמה ישנה שגויה, 404 על משתמש חסר).

### תיעוד — עדכונים נגזרים מהמחיקות
6. עדכן הפניות שהתיישנו כתוצאה ממשימות 1-2 (כדי שה-SPEC לא יפנה לקבצים שנמחקו/שונו):
   - `SPEC.md` §5 (שורה ~112) ו-§9 (שורה ~378, "כבר קיים שלד `RegionService`") — הסר/תקן את ההפניות ל-`contractor_matching_controller.py` ול-`RegionService`; ציין שממשק ה-Geocoding יתווסף כשיידרש בפועל (§18.3), ושצינור המנוע מרוכז ב-`matching_engine_service.py` (+`engine_pipeline.py` לבדיקות).
   - `prompts/README.md` (שורה ~54) ו-`CLAUDE.md` (שורה ~41 ברשימת קבצי הזבל) — עדכן את השם `contractor_matching_controller.py` ל-`engine_pipeline.py`, והסר מהרשימות את הקבצים שנמחקו.

## בדיקת מקצה-לקצה (E2E)
1. **סוויטה ירוקה:** מתוך `server/` הרץ `pytest` — כל 52 הבדיקות הקיימות חייבות לעבור **אחרי כל מחיקה ואחרי כל refactor** (הרץ שוב-ושוב, לא רק בסוף). בדיקת העשן `test_engine_smoke.py` חייבת לעבור עם הייבוא/השם החדשים.
2. **בדיקות חדשות (הוסף ל-`server/tests/`):**
   - ולידציה → 422 עם `{"detail": "<מחרוזת עברית>"}`: שלח גוף לא-תקין ל-endpoint קיים (למשל `POST /auth/login` בלי שדה חובה) וּודא סטטוס 422 ו-`detail` הוא מחרוזת (לא רשימת אובייקטים).
   - 500 מגובש: בדוק את handler ה-`Exception` עם `TestClient(app, raise_server_exceptions=False)` על route שמעלה חריגה מכוונת (אפשר route זמני בבדיקה או monkeypatch לשירות שיזרוק), וּודא 500 + `{"detail": "שגיאת שרת"}`.
   - רגרסיה לשכבתיות: `GET /admin/users` ו-`GET /admin/stats` (עם טוקן admin) עדיין מחזירים אותו מבנה כמו לפני; `change-password` ואיפוס-ע"י-admin עדיין עובדים מקצה-לקצה (התחברות עם הסיסמה החדשה מצליחה).
3. **לקוח:** אין שינוי בלקוח בשלב זה — אין צורך ב-`npm run build` פונקציונלי, אך ניתן להריצו כ-sanity שלא נשבר דבר (לא חובה).

## הגדרת סיום
- כל 5 הקבצים המתים נמחקו, `contractor_matching_controller.py` שוּנה ל-`engine_pipeline.py` (+שם המחלקה), ו-`grep` מאמת שאין ייבוא שבור.
- `app.py` רושם handler ל-`RequestValidationError` (422) ול-`Exception` (500), שניהם בפורמט `{"detail": "..."}` עברי; ה-500 נרשם ללוג.
- `admin_controller`/`auth_controller` אינם ניגשים ל-DB/`commit` ישירות — הכול דרך service/repository.
- **הסוויטה ירוקה** (52 הקיימות + הבדיקות החדשות שהוספת).
- עדכן `SPEC.md` §18.2 — סמן ✅ ליד שלוש הנקודות שטופלו כאן: "ניקוי קוד מת ומלכודות", "טיפול שגיאות אחיד (§8.7)", "שכבתיות (§9)"; ועדכן את ההפניות ב-§5/§9 כנדרש במשימה 6.
- עדכן את הזיכרון `memory/project-sari-state.md` (הקבצים שנמחקו/שונו, ה-handlers החדשים, שינויי השכבתיות) — ואם קיים, את `memory/MEMORY.md`.
- סכם למשתמש: מה נמחק, מה שוּנה-שם, מה הפורמט האחיד לשגיאות, ומה השלב הבא (R2 — הקשחת DB).

## הערות/מלכודות
- **אל תשבור בדיקות קיימות.** הרץ `pytest` אחרי כל מחיקה/refactor בנפרד — כך תזהה מיד מה שבר.
- **אל תשנה התנהגות, רק מבנה.** ה-`admin_controller`/`auth_controller` חייבים להחזיר בדיוק אותם ערכים/סטטוסים; המחרוזות `'OPEN'/'CLOSED'/'ACCEPTED'` ושמות הטבלאות (`OfferMatches` וכו') נשארים מילה-במילה.
- **שמות עמודות עם אותיות גדולות** (`Reliant`, `Stone_size`, `Purpose`, `*_id`) — לא לגעת, גם לא ב-repositories החדשים.
- **ה-handler הגנרי של `Exception` לא תופס `HTTPException`.** ודא שה-401/403/404/409 הקיימים ממשיכים להחזיר את ה-`detail` העברי שלהם ואת הסטטוס המקורי.
- **`TestClient` מעלה חריגות שרת כברירת מחדל** (`raise_server_exceptions=True`) — לבדיקת ה-500 יש להשתמש ב-`TestClient(app, raise_server_exceptions=False)`, אחרת הבדיקה תיפול על re-raise במקום לקבל 500.
- **`double_price_from_string` הוא מוקש רדום** — ודא שאף נתיב חי אינו קורא לו (אומת), ומחק אותו לגמרי; אל "תשמר" אותו "ליתר ביטחון".
- אין שינוי ב-`requirements.txt` בשלב זה; אם בכל זאת נגעת בו — הוא חייב להישאר **ASCII** (בלי הערות בעברית).
- RTL/עברית: כל מחרוזת שגיאה חדשה שמוצגת למשתמש — בעברית, בפורמט `{"detail": "..."}` בלבד.
