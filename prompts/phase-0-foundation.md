# שלב 0 — ייצוב בסיס (Foundation)

> פרומפט עצמאי לצ'אט חדש. **לפני שמתחילים:** קרא/י את `SPEC.md` (בעיקר סעיפים 5, 7, 14) ואת `prompts/README.md` (הקשר מאסטר, מחסנית, מצב נוכחי).

## מטרת השלב
להביא את הפרויקט למצב יציב ומוכן לפיתוח: ניקוי קבצי ניסוי, מיגרציית DB לפי האיפיון, זריעת נתונים (seed), ותשתית בדיקות. **בלי פיצ'רים חדשים** — רק תשתית. אין UI חדש בשלב זה (מלבד ודאות שהלקוח עדיין נבנה).

## היקף
**נכלל:** ניקוי שרת · מיגרציית סכימה · seed ל-lookups · תיקון תלויות · תשתית pytest + E2E · ודאות שהשרת עולה והמנוע מחזיר מועמדים.
**לא נכלל:** אימות (שלב 1), התאמות/התראות (שלב 3), מסכים.

## משימות

### DB (`server/db/`)
1. צור סקריפט מיגרציה `db/migrations/001_foundation.sql` (אידמפוטנטי) שמבצע על DB `beton`:
   - **`ConcreteRequests.status`**: להמיר לעמודת סטטוס עקבית `NVARCHAR(20) NOT NULL DEFAULT 'OPEN'` (ערכים: OPEN/CLOSED/CANCELLED). לטפל בנתונים קיימים (NULL→'OPEN').
   - **`ContractorConcreteRequests`**: להוסיף `status NVARCHAR(20) NOT NULL DEFAULT 'OPEN'` + `created_at DATETIME2 DEFAULT SYSDATETIME()`. `lat/lng` → `NOT NULL` (אם יש שורות עם NULL — לנקות/למלא קודם).
   - **`Strength`**: להוסיף `sort_order INT NULL` (לדירוג חוזק להשוואת `≥`).
   - **`Purpose`**: להוסיף `req_strength_id INT NULL`, `req_reliant_id INT NULL`, `req_stone_size_id INT NULL` (FK ל-Strength/Reliant/Stone_size) — מיפוי מטרה→מפרט.
   - שדות אימות (`password_hash`, `created_at`) יתווספו בשלב 1 — לא כאן.
2. עדכן את `db/schema.sql` שישקף את המצב הסופי (כדי שהקמה נקייה תיצור את הכול נכון).

### שרת (`server/`)
3. **ניקוי קבצי ניסוי** (מחיקה): `service/rrrrrrrrrrrrrrr.py`, `service/ttttttttttttttt.py`, `service/test.py`, `service/test163.py`, `service/matching_service.py`, `service/matching_service2.py`, `controller/test.py`, `dto/testDto.py`, `gm2.py`, `GoogleMaps.py`, `main.py` (סקריפט ניסוי — הכניסה היא `app.py`). את `service/mounday154.py` להשאיר זמנית (יוחלף בשלב 4) או להמיר ל-stub נקי. ודא שאף `import` פעיל לא נשבר (בדוק `matching_service*`, `mounday154` הם מיובאים איפשהו פעיל? תקן/הסר יבוא).
4. **תלויות:** הוסף ל-`requirements.txt` את `rtree` (המנוע משתמש ב-`from rtree import index` אך הוא חסר). תעד ש-`rtree` דורש את הספרייה המקורית `libspatialindex` (ב-Windows החבילה כוללת בינארי; אם לא נטען — לתעד פתרון). ודא התקנה נקייה של כל ה-`requirements.txt` בסביבת Python אמיתית (venv).
5. **קונפיג מנוע:** רכז את פרמטרי המנוע (רדיוס=10000, w1=5, w2=1, quantity_min_ratio=0.9) ב-`config.py` (OD-9), במקום קבועים מפוזרים.

### Seed (`server/db/seed.sql` או `server/seed.py`)
6. צור seed לטבלאות ה-lookup (כרגע ריקות!). **ערכים לדוגמה — לאמת מול המשתמש** (ידע דומיין ישראלי):
   - `Strength`: ב-20 (sort_order=1), ב-30 (2), ב-40 (3), ב-50 (4).
   - `Reliant` (סומך/slump): S1..S5 או ערכי שקיעה.
   - `Stone_size`: אגרגט 9.5מ"מ / 19מ"מ / 25מ"מ.
   - `Purpose`: יסודות, רצפה, גדר, שביל, קיר תומך, עמודים — **כולל מיפוי `req_*`** (למשל יסודות→חוזק ב-30).
   - `Concrete_type`: כמה צירופים תואמים למטרות.
7. הוסף גם מעט **נתוני דמו** ל-`Customers`, `Contractors`, `ConcreteRequests` (בקשות OPEN עם lat/lng אמיתיים בישראל) כדי שאפשר יהיה לבדוק את המנוע.

### תשתית בדיקות (`server/tests/`)
8. הקם `pytest`: `requirements-dev.txt` (pytest, httpx), `server/tests/conftest.py` (fixture ל-`TestClient`), ותיקיית `server/tests/e2e/`.
9. בדיקה ראשונה `tests/test_health.py`: `GET /` ו-`GET /health` מחזירים 200.

## בדיקת מקצה-לקצה (E2E) של השלב
הרץ את השרת (`uvicorn app:app --port 8001`) מול DB עם ה-seed, ואמת:
1. `GET /health` → `{"status":"healthy"}`.
2. `GET /purposes/` ו-`GET /strengths/` → מחזירים את נתוני ה-seed (לא ריק).
3. `GET /concrete-requests/` → מחזיר את בקשות הדמו עם `status="OPEN"`.
4. **בדיקת המנוע ידנית** (סקריפט `tests/e2e/test_engine_smoke.py`): הרץ את `GeoCandidateService` + סינון מטרה + סינון כמות על נתוני ה-seed, וּודא שמוחזרים מועמדים סבירים (מרחק/ניקוד). זו הבדיקה שמוכיחה שהבסיס חי.
5. לקוח: `cd client && npm install && npm run build` — עובר בלי שגיאות.

## הגדרת סיום
- כל הבדיקות עוברות; השרת עולה; ה-seed טעון; המנוע מחזיר מועמדים.
- עדכן `memory/project-sari-state.md`: הסכימה שודרגה, seed נטען, קבצי ניסוי נוקו, תשתית בדיקות קיימת.
- סכם למשתמש מה נוקה ומה נזרע, ובקש אישור לערכי ה-seed הדומייניים.

## הערות/מלכודות
- Python ב-PATH הוא stub של החנות — ודא venv אמיתי עם pyodbc + ODBC Driver 17.
- שמות עמודות עם אותיות גדולות (`Reliant`, `Stone_size`, `Purpose`, `Reliant_id`...) — לא לשנות, ה-ORM ממופה אליהם.
- אל תשבור את `database.py`/`config.py` (Windows Auth). אם אין SQL Server זמין — עצור ובקש מהמשתמש.
