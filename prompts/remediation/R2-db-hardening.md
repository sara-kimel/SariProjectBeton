# שלב R2 — הקשחת בסיס הנתונים (DB Hardening)

> פרומפט עצמאי לצ'אט חדש. **לפני שמתחילים:** קרא/י את `SPEC.md` (§18 + §7) ואת `prompts/README.md` ו-`prompts/remediation/README.md`. ודא ש-R0 (תיקוני P0) בוצע ושחבילת הבדיקות ירוקה (`pytest` מ-`server/`, דורש SQL Server מקומי + DB `beton`).

## מטרת השלב
לאכוף את חוזי מודל הנתונים של §7 **ברמת ה-DB עצמו** (לא רק בקוד): אינדקסים בסכימה הנקייה, אילוצי `CHECK` על עמודות `status`, עמודות מפתח-חובה כ-`NOT NULL`, מיגרציות אידמפוטנטיות באמת, ושימור טווחי ה-IDENTITY המתועדים בין הרצות `seed`. זהו שלב תשתית — **אין פיצ'רים ואין שינוי התנהגות אפליקטיבית**.

## היקף
**נכלל:** סנכרון `schema.sql` מול מיגרציה `005` (אינדקסים) · אילוצי `CHECK` על `status` (`schema.sql` + מיגרציה חדשה `006`) · `customer_id`/`purpose_id` → `NOT NULL` · הפיכת מיגרציה `002` לאידמפוטנטית אמיתית · `DBCC CHECKIDENT ... RESEED` ב-`seed.py`.
**מחוץ להיקף:** כל שינוי בלוגיקת המנוע/האישור/ההרשאות; שינוי שמות עמודות; פריטי P1 האחרים (ניקוי קוד מת, טיפול-שגיאות אחיד, שכבתיות, אבטחה נוספת, לקוח) — הם שלבי R נפרדים. אין שינוי ב-DTO/בקרים.

## משימות

### DB — סכימה ואינדקסים (`server/db/schema.sql`)
1. **העתקת כל האינדקסים ממיגרציה `005` אל `schema.sql`** כדי שהקמה נקייה מהסכימה תיצור אותם. הוסף בסוף הקובץ (לפני `PRINT 'Beton schema created successfully.'` בשורה 258), כל אינדקס עטוף ב-`IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name='...')` + `GO`, בדיוק כמו `IX_Notifications_user` הקיים (שורות 253–256). האינדקסים מ-`server/db/migrations/005_indexes.sql`:
   - על `ConcreteRequests`: `IX_CR_status([status])`, `IX_CR_geo(lat, lng)`, `IX_CR_customer(customer_id)`, `IX_CR_purpose(purpose_id)`.
   - על `ContractorConcreteRequests`: `IX_CCR_status_expiry([status], expiry_time)`, `IX_CCR_contractor(contractor_id)`, `IX_CCR_concrete(concrete_id)`.
   - על `OfferMatches`: `IX_OM_offer(offer_id, [status])`, `IX_OM_request(request_id, [status])`.
2. **עדכון הערת הכותרת** של `schema.sql` (שורות 21–25) שמפרטת כרגע רק את מיגרציות `001`/`003`/`004`. הרחב אותה כך שתשקף גם: `002` (auth — `user_name` NOT NULL+UNIQUE, `password_hash`, `created_at`, טבלת `Admins`), `005` (אינדקסי ביצועים), ו-`006` (אילוצי `CHECK` על `status` + `customer_id`/`purpose_id` NOT NULL — נוצרת במשימה 3–4). המשפט "הקמה נקייה מקובץ זה => סכימה סופית" חייב להישאר נכון.

### DB — אילוצי CHECK על `status` (`schema.sql` + מיגרציה חדשה `006`)
3. **אכיפת ה-enum ברמת ה-DB.** כיום ה-enum נאכף רק בקוד; אין `CHECK`. הערכים המדויקים שהקוד כותב (אומתו ב-`service/deal_service.py`, `service/expiry_service.py`, `service/match_service.py`, `repository/*`) — **אל תוסיף/תשמיט ערך, אחרת בדיקות ייכשלו**:
   - `ConcreteRequests.status` → `IN ('OPEN','CLOSED','CANCELLED')` (SPEC §7.1).
   - `ContractorConcreteRequests.status` → `IN ('OPEN','CLOSED','EXPIRED','CANCELLED')` (SPEC §7.1; ה-`+EXPIRED` הוא תפוגה עצלה, `expiry_service`).
   - `OfferMatches.status` → `IN ('NOTIFIED','ACCEPTED','DECLINED','SUPERSEDED','EXPIRED')` (SPEC §6.3/§7.2).
   ליישום בשני מקומות שחייבים להתכנס לאותה סכימה:
   - **`schema.sql`** — הוסף בתוך כל `CREATE TABLE` שורת אילוץ inline צמוד לעמודת ה-`status`, למשל: `CONSTRAINT CK_ConcreteRequests_status CHECK ([status] IN ('OPEN','CLOSED','CANCELLED'))` (וכן `CK_CCR_status`, `CK_OfferMatches_status`).
   - **מיגרציה חדשה `server/db/migrations/006_db_hardening.sql`** — לבסיסי-נתונים קיימים: `ALTER TABLE dbo.<t> WITH CHECK ADD CONSTRAINT CK_... CHECK (...)`, כל אחד עטוף אידמפוטנטית: `IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name='CK_...')`. פתח את הקובץ ב-`USE beton; GO` ובלוק `PRINT`, בסגנון `005_indexes.sql`.

### DB — עמודות חובה `NOT NULL` (מודל + `schema.sql` + `006`)
4. **`ConcreteRequests.customer_id` → `NOT NULL`** (SPEC §7.1 🔧 — "בקשה חייבת לקוח לאחר אימות"). האפליקציה תמיד ממלאת אותו מהמשתמש המחובר (`controller/concrete_request_controller.py` שורה 93 → `current["id"]`), כך שאין שורות עם `NULL`. יש לשנות בשלושה מקומות במקביל:
   - `server/models/concrete_request.py` שורה 24: `nullable=True` → `nullable=False`.
   - `server/db/schema.sql` שורה 168: `customer_id INT NULL` → `INT NOT NULL`.
   - `006_db_hardening.sql`: אידמפוטנטי — `IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME='ConcreteRequests' AND COLUMN_NAME='customer_id' AND IS_NULLABLE='YES') ALTER TABLE dbo.ConcreteRequests ALTER COLUMN customer_id INT NOT NULL;`
   הרץ את `006` **אחרי** `005`: שינוי nullability-בלבד (אותו טיפוס `INT`) תואם לקיום `IX_CR_customer` ואינו מפיל שגיאת 5074.
5. **`purpose_id` — יישור לפי §7.1.** נתיב היצירה כבר מחייב אותו (`concrete_request_controller.py` שורות 88–91 מחזירות 422 כשהוא `None` / לא קיים), כך שגם עמודה זו לעולם לא `NULL`. §7.1 אינו מסמן אותה ב-🔧 במפורש, ולכן זו הידוקה עקבית ולא חובת-SPEC: החל את אותו שינוי בשלושת המקומות (מודל שורה 27, `schema.sql` שורה 169, `006`) **או** השאר nullable — אך תעד את ההחלטה, ודאג ש-`schema.sql` ומיגרציה `006` יגיעו בדיוק לאותה תוצאה. אין להשאיר סתירה בין השניים.

### DB — אידמפוטנטיות אמיתית למיגרציה `002` (`server/db/migrations/002_auth.sql`)
6. הקובץ מצהיר "אידמפוטנטי" אך שתי הפעולות רצות **ללא תנאי** ונשברות בהרצה חוזרת:
   - `UPDATE ... SET user_name = CONCAT('user_', id) WHERE user_name IS NULL` (שורות 30, 49).
   - `ALTER TABLE ... ALTER COLUMN user_name NVARCHAR(50) NOT NULL` (שורות 32, 51) — בהרצה שנייה, לאחר שכבר קיים `UQ_<t>_user_name`, ה-`ALTER COLUMN` על עמודה שיש עליה אילוץ ייחודי תלוי **נכשל בשגיאה 5074** ("The object 'UQ_...' is dependent on column 'user_name'").
   התיקון, לכל אחת מ-`Customers` ו-`Contractors`:
   - עטוף את ה-`UPDATE` כך שירוץ רק כשיש שורות רלוונטיות: `IF EXISTS (SELECT 1 FROM dbo.Customers WHERE user_name IS NULL) UPDATE dbo.Customers SET user_name = CONCAT('user_', id) WHERE user_name IS NULL;`
   - עטוף את ה-`ALTER COLUMN` בבדיקת `IS_NULLABLE`, כך שיפעל רק כשהעמודה עדיין מאפשרת NULL: `IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME='Customers' AND COLUMN_NAME='user_name' AND IS_NULLABLE='YES') ALTER TABLE dbo.Customers ALTER COLUMN user_name NVARCHAR(50) NOT NULL;`
   שמור על גבולות ה-`GO` הקיימים (כל בדיקה + הפעולה שלה באותו batch, משפט יחיד אחרי ה-`IF` ללא `BEGIN/END`). שאר הפעולות בקובץ כבר מוגנות ב-`COL_LENGTH`/`sys.key_constraints` — אל תיגע בהן.

### שרת — שימור טווחי IDENTITY ב-`seed` (`server/db/seed.py`)
7. `main()` מבצע `DELETE FROM dbo.[<t>]` בלולאת ה-`WIPE_ORDER` (שורות 111–112) **בלי לאפס IDENTITY**, ולכן טווחי ה-seed המתועדים נשחקים ועולים בכל הרצה (הבקשה `DEMO-A` וכו' מקבלות מזהים שונים בכל פעם). מיד **אחרי** לולאת ה-`DELETE` (ולפני הכנסת ה-lookups), הוסף `DBCC CHECKIDENT('dbo.<table>', RESEED, <seed-1>)` לכל טבלה עם טווח מתועד, בתוך אותה טרנזקציית `engine.begin()`. ערך ה-RESEED = `seed − 1` (כך שההכנסה הבאה מקבלת בדיוק את ערך ה-seed). הטווחים המתועדים (CLAUDE.md / `schema.sql` / הערות המודלים):

   | טבלה | seed | RESEED |
   |---|---|---|
   | Customers | 100 | 99 |
   | ConcreteRequests | 200 | 199 |
   | Contractors | 300 | 299 |
   | ContractorConcreteRequests | 600 | 599 |
   | Strength | 1100 | 1099 |
   | Reliant | 1200 | 1199 |
   | Stone_size | 1300 | 1299 |
   | Purpose | 1400 | 1399 |
   | Concrete_type | 2000 | 1999 |

   מומלץ גם `Admins`/`OfferMatches`/`Notifications` (מתחילות מ-1 → RESEED `0`) לדטרמיניזם מלא של נתוני הדמו. מימוש: מילון `table → seed` ולולאה `c.execute(text(f"DBCC CHECKIDENT ('dbo.[{t}]', RESEED, {seed-1})"))`. הערה: `DBCC CHECKIDENT` דורש עמודת IDENTITY — לכל הטבלאות הללו יש. **אל תשנה את ערכי ה-seed המתועדים.**

## בדיקת מקצה-לקצה (E2E)
1. **הקמה נקייה מ-`schema.sql`** (על DB זמני/מאופס): כל האינדקסים מ-005 קיימים (`SELECT name FROM sys.indexes`), שלושת אילוצי ה-`CHECK` קיימים (`SELECT name FROM sys.check_constraints`), ו-`ConcreteRequests.customer_id` הוא `NOT NULL` (`INFORMATION_SCHEMA.COLUMNS`).
2. **אידמפוטנטיות:** הרץ `002_auth.sql`, `005_indexes.sql` ו-`006_db_hardening.sql` **פעמיים** ברצף — אין שגיאה (במיוחד: `002` בהרצה שנייה לא זורק 5074).
3. **טווחי IDENTITY:** הרץ `python db/seed.py` פעמיים; לאחר כל הרצה `SELECT MIN(id) FROM dbo.Customers` = 100, `MIN(request_id) FROM dbo.ConcreteRequests` = 200, וכן הלאה לפי הטבלה — המזהים אינם זוחלים.
4. **ה-CHECK אוכף:** ניסיון ידני `INSERT`/`UPDATE` עם `status` לא חוקי (למשל `'FOO'`) נדחה ע"י ה-DB.
5. **`pytest` מ-`server/` — 52 בדיקות ירוקות**, ללא רגרסיה (דורש SQL Server מקומי + `beton` זרוע). ריצת המנוע/האישור/התפוגה עדיין עוברת (הערכים החוקיים לא הושמטו).
6. **התכנסות סכימה:** ודא שהקמה נקייה מ-`schema.sql` שקולה למצב הסופי לאחר `001`→`006` (אותם אילוצים, אינדקסים, ו-nullability).

## הגדרת סיום
- כל השינויים יושמו; `schema.sql` ומיגרציה `006` מתכנסים לאותה סכימה סופית; הערת הכותרת ב-`schema.sql` מעודכנת (001–006).
- **`pytest` ירוק (52).**
- עדכון `SPEC.md` §18.2 — סמן ✅ בפריט "הקשחת DB" (שורה 722) על הפריטים שבוצעו: אינדקסי `005` ל-`schema.sql`, `CHECK` על `status`, `customer_id`(/`purpose_id`) → NOT NULL, `002` אידמפוטנטית, `DBCC CHECKIDENT ... RESEED` ב-`seed.py`.
- עדכון `memory/project-sari-state.md` (מדד ב-`memory/MEMORY.md`): הסכימה הוקשחה — אינדקסים בסכימה הנקייה, אילוצי CHECK, NOT NULL, מיגרציה 006, seed שומר טווחי IDENTITY.
- סיכום למשתמש: מה הוקשח ולמה, ותזכורת שיש להריץ `006` על סביבות DB קיימות (לא רק על הקמה נקייה).

## הערות/מלכודות
- **אל תשבור בדיקות קיימות** — הרץ את הסוויטה אחרי כל שינוי DB. סט ערכי ה-`CHECK` חייב להיות בדיוק כפי שהקוד כותב (משימה 3); ערך חסר או מיותר יפיל את `deal_service`/`expiry_service`/המרוץ.
- **אל תשנה שמות עמודות עם אותיות גדולות** — `Reliant`, `Stone_size`, `Purpose`, `Reliant_id`, `Stone_size_id`, `Purpose_id`; ואל תיגע בעמודת ה-FK `id_customer` (מפנה ל-`ConcreteRequests.request_id`). כאן משנים רק nullability ומוסיפים אילוצים.
- כל DDL חדש חייב להיות **אידמפוטנטי** ומוגן: `sys.check_constraints` לאילוצים, `sys.indexes` לאינדקסים, `INFORMATION_SCHEMA.COLUMNS.IS_NULLABLE` ל-nullability.
- **סדר הרצה:** `006` אחרי `005`. שינוי nullability-בלבד (אותו טיפוס) בטוח מול אינדקס קיים ואינו מפיל 5074 (5074 שמור לשינויי טיפוס/גודל).
- ה-`ALTER COLUMN ... NOT NULL` ייכשל אם קיימות שורות עם `NULL` בעמודה. ה-seed והאפליקציה מבטיחים שאין כאלה; אם יש נתוני legacy — נקה/מלא ידנית לפני ההרצה (אין backfill מלאכותי ל-`customer_id`).
- שמור על גבולות ה-`GO` הקיימים במיגרציות; `IF ... <statement>` יחיד אינו דורש `BEGIN/END`.
- אל תשנה את ערכי ה-seed המתועדים ב-`seed.py`; RESEED = `seed − 1` (לא `seed`).
