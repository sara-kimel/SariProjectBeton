# שלב R7 — תשתית ותפעול (Infra: ErrorBoundary / README / CI / Docker)

> פרומפט עצמאי לצ'אט חדש. **לפני שמתחילים:** קרא/י את `SPEC.md` (§18 + §12.6 + §17.3/§17.4) ואת `prompts/README.md` ו-`prompts/remediation/README.md`. ודא ש-R0 (תיקוני P0) בוצע ושחבילת הבדיקות ירוקה: `cd server && PYTHONUTF8=1 ./.venv/Scripts/python.exe -m pytest -q` → **52 passed**.

## מטרת השלב
להשלים את שכבת ה**תשתית והתפעול** החסרה סביב ה-MVP הבנוי: גדר-בטיחות לרינדור בצד לקוח (`ErrorBoundary`), `README` אנושי עם הוראות הרצה, אינטגרציה רציפה (GitHub Actions) ו-`Dockerfile` לפריסה עקבית. זהו שלב תפעולי — **לא נוגעים בלוגיקה עסקית, במנוע ההתאמה או בסכימת ה-DB**.

## היקף
**נכלל:** `ErrorBoundary` שעוטף את הראוטים (§12.6) · `README.md` בשורש עם דרישות מקדימות ופקודות הרצה/seed · workflow ל-CI שמריץ pytest בשרת ו-`npm run build` בלקוח (§17.3) · `Dockerfile` לשרת (+`docker-compose` אופציונלי עם SQL Server) · נעילת גרסת `rtree` ב-`requirements.txt`.

**מחוץ להיקף:** מסכי פרופיל/היסטוריה והסכמת תנאים (R5) · תוספת בדיקות תוכן חדשות למנוע/לקוח (R6) · Alembic/מיגרציות מנוהלות (עתידי, §17.3) · כל שינוי ב-endpoints, במודלים או בסכימה. **אין לחזור על תיקוני R0** (הרשאות owner-or-admin, שער אטומי, soft-delete, JWT fail-fast, `DB_SERVER` מ-env, `cos(lat)`).

## משימות

### לקוח — ErrorBoundary (§12.6)
כרגע אין `componentDidCatch`/`ErrorBoundary` בכל `client/src` — כל חריגת רינדור מפילה את העץ כולו למסך לבן. `SPEC.md` §12.6 מונה `ErrorBoundary` בספריית ה-UI, אך הוא לא מומש.

1. **צור רכיב `client/src/components/ErrorBoundary.tsx`** — קומפוננטת **מחלקה** (React error boundaries חייבים להיות class components), עם `static getDerivedStateFromError` ו-`componentDidCatch(error, info)` (רישום ל-`console.error`). ה-`render` מחזיר `this.props.children` במצב תקין, ובמצב שגיאה מסך fallback ב-RTL עברית: כותרת "אירעה שגיאה בלתי צפויה", טקסט קצר, וכפתור **"רענון הדף"** (מבצע `window.location.reload()`) וקישור **"חזרה לדף הבית"** (`window.location.href = '/'` — טעינה נקייה שמאפסת את ה-state). ללא תלות בספריות חיצוניות.
2. **עטוף את הראוטים ב-`client/src/components/../App.tsx`** (`client/src/App.tsx`) — עטוף את אלמנט ה-`<Routes>…</Routes>` (שורות 30–73) ב-`<ErrorBoundary>…</ErrorBoundary>`, והוסף את ה-import בראש הקובץ. שמור על מיקום בתוך ה-Router (ה-`ErrorBoundary` נשאר בפנים כדי שהמצב התקין ימשיך לעבוד; ההתאוששות היא דרך `window.location` ולכן אינה תלויה ב-router).

### שורש הריפו — README אנושי
אין `README.md` בשורש/`server/`/`client/` — קיים רק `prompts/README.md` שהוא הקשר-בנייה, לא מדריך הרצה למפתח.

3. **צור `README.md` בשורש** (בעברית, RTL), עם:
   - **תיאור קצר:** "Beton / פרויקט שרי" — פלטפורמת תיווך בין קבלנים עם שאריות בטון ללקוחות (הפניה ל-`SPEC.md` כמסמך האמת ול-`prompts/` לבנייה המדורגת).
   - **דרישות מקדימות:** SQL Server מקומי + DB בשם `beton` (Windows Authentication); `ODBC Driver 17 for SQL Server`; **Python אמיתי** — יש להדגיש ש-`python`/`py` שב-PATH הם **stub של Microsoft Store** ואינם מפרש אמיתי, לכן יש ליצור venv (`server/.venv` כבר קיים בסביבה זו) ולהתקין דרכו; Node v22 (בסביבה זו ב-`C:\nvm4w\nodejs`).
   - **התקנת השרת:** יצירת venv + `pip install -r requirements.txt -r requirements-dev.txt` (מתוך `server/`). לציין ש-`rtree` נשען על `libspatialindex` — ב-Windows גלגל ה-wheel כולל את הבינארי, ב-Linux ייתכן צורך ב-`libspatialindex` מהמערכת. **מלכודת NetFree:** יירוט ה-SSL עלול להפיל את `pip`/`npm` — לתעד עקיפה: `pip install --cert <netfree-ca.pem> …` (או `--trusted-host pypi.org --trusted-host files.pythonhosted.org` כמוצא אחרון), ובלקוח ייתכן שיחסם גם Google Maps (§17.3).
   - **הגדרת סביבה:** להעתיק `server/.env.example` ל-`server/.env` ולעדכן (`DB_SERVER`, `DB_NAME=beton`, `USE_WINDOWS_AUTH`, `APP_ENV`, `JWT_SECRET`) — הפניה ל-FIX-4/FIX-5.
   - **זריעת נתונים:** `python db/seed.py` (מתוך `server/`, בתוך ה-venv) — זורע lookups + דמו + משתמש מנהל ראשוני (`admin` / `Admin!2026`). לציין שה-lookups חייבים להיזרע אחרת המנוע לא ימצא התאמות.
   - **הרצת השרת:** `uvicorn app:app --reload --port 8001` (מתוך `server/`); מסמכי API ב-`http://localhost:8001/docs`.
   - **הרצת הלקוח:** `npm install && npm run dev` (מתוך `client/`, פורט 5173); בילד/בדיקת-טיפוסים: `npm run build` (= `tsc && vite build`). מפתח Maps ב-`client/.env` (`VITE_GOOGLE_MAPS_API_KEY`).
   - **בדיקות:** `PYTHONUTF8=1 ./.venv/Scripts/python.exe -m pytest -q` (מתוך `server/`; דורש SQL Server + DB `beton` חיים).

### CI — GitHub Actions (§17.3)
אין `.github/workflows/`.

4. **צור `.github/workflows/ci.yml`** שמופעל על `push` ו-`pull_request`, עם שני jobs:
   - **job `server`** (ubuntu-latest): התקנת Python 3.12; התקנת דרייבר ה-ODBC (`msodbcsql17` ממאגר Microsoft) + `unixodbc-dev` + `libspatialindex-dev` (רשת-בטיחות ל-`rtree`); `pip install -r server/requirements.txt -r server/requirements-dev.txt`; הרצת `pytest` מתוך `server/`.
   - **job `client`** (ubuntu-latest): `node 22`; `npm ci` ואז `npm run build` מתוך `client/`. הערה: לבילד דרוש `VITE_GOOGLE_MAPS_API_KEY` — אפשר להזריק ערך-דמה (`env`) כי הבילד לא פונה ל-Google בפועל.
   - **מלכודת מרכזית — בדיקות השרת דורשות SQL Server + DB `beton`.** ה-`conftest` פותח `SessionLocal()` אמיתי מול DB חי (`server/tests/conftest.py`), ומרבית הבדיקות (מנוע/accept/auth) תלויות בו. שתי גישות, יש **ליישם את השנייה כרשת-בטיחות ולהעדיף את הראשונה**:
     1. **service container של SQL Server (מומלץ — מריץ את הסוויטה באמת):** הוסף ל-job `server` שירות `mcr.microsoft.com/mssql/server:2022-latest` עם `ACCEPT_EULA=Y` ו-`MSSQL_SA_PASSWORD` **חזק** (SQL Server דוחה סיסמה חלשה), המתן ל-healthy, צור DB `beton` + הרץ את `server/db/schema.sql` + `python db/seed.py`, והזרק env לחיבור **ב-SQL Auth** (Windows Auth לא זמין ב-Linux): `USE_WINDOWS_AUTH=False`, `DB_USER=sa`, `DB_PASSWORD=<הסיסמה>`, `DB_SERVER=localhost`, `APP_ENV=development` (כדי לא להפיל את `_validate_production_settings`), ו-`RATE_LIMIT_ENABLED=false`.
     2. **skip-on-unavailable (רשת בטיחות):** הוסף ב-`server/tests/conftest.py` בדיקת-חיבור בזמן איסוף — נסה `engine.connect()` פעם אחת, ואם נכשל קרא `pytest.skip("no DB", allow_module_level=True)` / דלג עם `pytest.mark.skipif` על הבדיקות התלויות-DB, כך שרנר בלי SQL ידווח **skipped ולא failed**. **לתאם עם הגישה הקיימת:** אל תשבור בדיקות שכן רצות מקומית מול DB; הדילוג חייב להיות רק כאשר החיבור **באמת** לא זמין.

### פריסה — Dockerfile
אין `Dockerfile`.

5. **צור `server/Dockerfile`** — בסיס `python:3.12-slim`; התקנת `msodbcsql17` + `unixodbc-dev` + `libspatialindex-dev` (שכבת apt עם מאגר Microsoft ו-`ACCEPT_EULA`); `COPY` של `requirements*.txt` + `pip install`; `COPY` של קוד השרת; `EXPOSE 8001`; `CMD ["uvicorn","app:app","--host","0.0.0.0","--port","8001"]`. הערה מפורשת בקובץ/README: בקונטיינר Linux **חובה `USE_WINDOWS_AUTH=False`** + `DB_USER`/`DB_PASSWORD` (Windows Auth אינו זמין).
6. **(אופציונלי) `docker-compose.yml` בשורש** — שירות `server` (Build מ-`server/Dockerfile`) + שירות `db` (`mcr.microsoft.com/mssql/server:2022-latest`, `ACCEPT_EULA=Y`, `MSSQL_SA_PASSWORD`), `depends_on`, והזרקת ה-env של SQL Auth. לתעד שיצירת ה-DB + schema + seed מתבצעת כצעד ראשון (init) לפני הרצת השרת.

### נעילת תלות
7. **נעל גרסת `rtree` ב-`server/requirements.txt`** — שנה `rtree>=1.3.0` (שורה 17) ל-`rtree==1.3.0` לשחזוריות בילד. **מלכודת קריטית:** `requirements.txt` ו-`requirements-dev.txt` **חייבים להישאר ASCII בלבד** — `pip` מפענח אותם בקידוד ה-locale (cp1255 במכונה זו) ונופל על עברית. אל תוסיף הערות עבריות לקבצים אלה.

## בדיקת מקצה-לקצה (E2E)
1. **לקוח:** `cd client && npm run build` עובר נקי (ה-`ErrorBoundary` מתקמפל ב-`tsc`). אימות ידני: הזרק זמנית `throw new Error('test')` בתוך רכיב עמוד, ודא שמופיע מסך ה-fallback ב-RTL (במקום מסך לבן) ושכפתור "רענון הדף" עובד — ואז **החזר את השינוי**.
2. **שרת:** `cd server && PYTHONUTF8=1 ./.venv/Scripts/python.exe -m pytest -q` → **52 passed**, ללא regressions (שינויי התשתית לא נוגעים בקוד הבדיקות; אם הוספת skip-guard ל-`conftest` — ודא שמול DB חי כל 52 עדיין רצות ולא מדלגות).
3. **README:** עבור על הפקודות שכתבת וודא שכל נתיב/פקודה אמיתי (מתוך `server/`: `uvicorn app:app --port 8001`, `python db/seed.py`; מתוך `client/`: `npm run dev`/`npm run build`).
4. **CI:** ולידציית תחביר ה-YAML; ודא שהצעדים ב-job `server` תואמים לזרימת ההרצה המקומית המתועדת, ושה-triggers הם `push`/`pull_request`. אם `act` זמין — הרצה מקומית; אחרת, אימות סטטי מספיק לשלב זה.
5. **Docker:** `docker build -f server/Dockerfile server/` בונה בהצלחה (אם Docker זמין; ייתכן שחסום ע"י NetFree למשיכת בסיס — לתעד). אם הוגדר compose ו-Docker זמין: `docker compose up` מעלה server+db.

## הגדרת סיום
- כל 7 המשימות בוצעו: `ErrorBoundary` עוטף את הראוטים, `README.md` בשורש, `.github/workflows/ci.yml`, `server/Dockerfile` (+compose אופציונלי), ו-`rtree` נעול.
- **חבילת ה-pytest ירוקה** (52, בלי regressions) ו-`npm run build` נקי.
- עדכון `SPEC.md` §18.3 — סימון פריט ה**תשתית** ("`ErrorBoundary`, `README` אנושי עם הוראות הרצה, CI (GitHub Actions) + Dockerfile", שורה 731) כ-✅ (ועדכון המראה הקריא `SPEC.html`).
- עדכון הזיכרון `memory/project-sari-state.md` עם מה שנוסף (תשתית CI/Docker/ErrorBoundary/README) והחלטות (SQL Auth ב-CI/Docker, גישת skip-on-unavailable).
- סיכום קצר למשתמש: מה נבנה, איך נבדק, ומה השלב הבא (R6 בדיקות / R8 דירוגים, לפי העדיפות שנבחרה).

## הערות/מלכודות
- **אל תשבור בדיקות קיימות** — הרץ את הסוויטה אחרי כל שינוי (גם שינויים ב-`conftest`/`requirements` יכולים להשפיע). זהו שלב תפעולי בלבד; אל תיגע בלוגיקה עסקית, במנוע ההתאמה, ב-endpoints או בסכימת ה-DB.
- **ASCII ב-`requirements*.txt`** — `pip` מפענח cp1255 ונופל על עברית. אל תכניס תווים לא-ASCII לקבצים אלה (הן ל-`requirements.txt` והן ל-`requirements-dev.txt`).
- **RTL עברית** במסך ה-fallback של `ErrorBoundary` וב-`README`.
- **אל תשנה שמות עמודות/טבלאות** (`Reliant`, `Stone_size`, `Purpose`, `Reliant_id` וכו') — לא רלוונטי ישירות כאן, אך אם ה-CI מריץ `schema.sql`/`seed.py` ודא שאתה משתמש בהם כמות שהם.
- **Windows Auth לא זמין ב-Linux** — גם ב-CI וגם ב-Docker חובה `USE_WINDOWS_AUTH=False` + `DB_USER`/`DB_PASSWORD` (בניגוד להרצה המקומית ב-Windows).
- **`APP_ENV`/JWT (FIX-4):** ב-CI/Docker השאר `APP_ENV=development` (או הגדר `JWT_SECRET` אקראי ≥32 תווים) אחרת `_validate_production_settings` יעלה `RuntimeError` בעליית האפליקציה.
- **NetFree (יירוט SSL)** עלול לחסום `pip`/`npm`/`docker pull`/Google Maps — לתעד עקיפה (cert) ב-`README` ולא להיתקע.
- **אל תחזור על R0** — אם נתקלת בהרשאות/מרוץ/ביטול/JWT/`DB_SERVER`/`cos(lat)`, אלה כבר בוצעו (`prompts/remediation/R0-critical-fixes-DONE.md`).
