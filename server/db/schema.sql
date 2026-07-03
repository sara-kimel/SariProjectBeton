/* =====================================================================
   Beton API - סכימת מסד נתונים
   נגזר אוטומטית ממודלי ה-SQLAlchemy שבתיקיית models/
   מסד יעד: SQL Server  |  שם DB: beton
   ---------------------------------------------------------------------
   סדר יצירה לפי תלויות מפתחות זרים:
     1. טבלאות lookup / עצמאיות: Customers, Contractors,
        Strength, Reliant, Stone_size, Purpose
     2. Concrete_type          (תלוי ב-Strength/Reliant/Stone_size/Purpose)
     3. ConcreteRequests       (תלוי ב-Customers/Purpose)
     4. ContractorConcreteRequests (תלוי ב-Concrete_type/Contractors/ConcreteRequests)
     5. OfferMatches           (תלוי ב-ContractorConcreteRequests/ConcreteRequests/Customers)
     6. Notifications          (עצמאית — user_id/role לוגי, בלי FK קשיח)

   הערות עיצוב:
   - נעשה שימוש ב-NVARCHAR (ולא VARCHAR) כי המערכת מאחסנת טקסט בעברית
     (כתובות, שמות, אזורים). המודל מגדיר String -> VARCHAR, אך NVARCHAR
     מונע שיבוש תווים עבריים.
   - ערכי IDENTITY seed נלקחו מההערות שבמודלים.
   - סקריפט אידמפוטנטי: כל טבלה נוצרת רק אם אינה קיימת.
   - משקף את המצב לאחר מיגרציה 001 (שלב 0): status עקבי כ-NVARCHAR,
     Strength.sort_order, מיפוי Purpose.req_*, ו-status/created_at ב-
     ContractorConcreteRequests. ולאחר מיגרציה 003 (שלב 3): טבלת OfferMatches,
     ומיגרציה 004 (שלב 4): טבלת Notifications.
     הקמה נקייה מקובץ זה => סכימה סופית.
   ===================================================================== */

-------------------------------------------------------------------------
-- יצירת מסד הנתונים אם אינו קיים
-------------------------------------------------------------------------
IF DB_ID('beton') IS NULL
BEGIN
    CREATE DATABASE beton;
END
GO

USE beton;
GO

-------------------------------------------------------------------------
-- 1. Customers  (לקוחות)  |  id מתחיל מ-100
-------------------------------------------------------------------------
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Customers')
CREATE TABLE dbo.Customers (
    id             INT IDENTITY(100, 1) NOT NULL,
    first_name     NVARCHAR(15) NULL,
    last_name      NVARCHAR(15) NULL,
    user_name      NVARCHAR(50) NOT NULL,                     -- מיגרציה 002: חובה + UNIQUE
    password_hash  NVARCHAR(255) NULL,                        -- מיגרציה 002: bcrypt (שלב 1)
    phone          NVARCHAR(20) NULL,
    created_at     DATETIME2 NOT NULL CONSTRAINT DF_Customers_created_at DEFAULT SYSDATETIME(),
    CONSTRAINT PK_Customers PRIMARY KEY (id),
    CONSTRAINT UQ_Customers_user_name UNIQUE (user_name)
);
GO

-------------------------------------------------------------------------
-- 2. Contractors  (קבלנים)  |  id מתחיל מ-300
-------------------------------------------------------------------------
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Contractors')
CREATE TABLE dbo.Contractors (
    id             INT IDENTITY(300, 1) NOT NULL,
    first_name     NVARCHAR(15) NULL,
    last_name      NVARCHAR(15) NULL,
    user_name      NVARCHAR(50) NOT NULL,                     -- מיגרציה 002: חובה + UNIQUE
    password_hash  NVARCHAR(255) NULL,                        -- מיגרציה 002: bcrypt (שלב 1)
    phone          NVARCHAR(15) NULL,
    created_at     DATETIME2 NOT NULL CONSTRAINT DF_Contractors_created_at DEFAULT SYSDATETIME(),
    CONSTRAINT PK_Contractors PRIMARY KEY (id),
    CONSTRAINT UQ_Contractors_user_name UNIQUE (user_name)
);
GO

-------------------------------------------------------------------------
-- 2b. Admins  (מנהלים)  |  id מתחיל מ-1   (מיגרציה 002, שלב 1)
-------------------------------------------------------------------------
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Admins')
CREATE TABLE dbo.Admins (
    id             INT IDENTITY(1, 1) NOT NULL,
    user_name      NVARCHAR(50) NOT NULL,
    password_hash  NVARCHAR(255) NOT NULL,
    first_name     NVARCHAR(50) NULL,
    last_name      NVARCHAR(50) NULL,
    created_at     DATETIME2 NOT NULL CONSTRAINT DF_Admins_created_at DEFAULT SYSDATETIME(),
    CONSTRAINT PK_Admins PRIMARY KEY (id),
    CONSTRAINT UQ_Admins_user_name UNIQUE (user_name)
);
GO

-------------------------------------------------------------------------
-- 3. Strength  (חוזק בטון - lookup)  |  id מתחיל מ-1100
-------------------------------------------------------------------------
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Strength')
CREATE TABLE dbo.Strength (
    id          INT IDENTITY(1100, 1) NOT NULL,
    strength    NVARCHAR(50) NULL,
    sort_order  INT NULL,                 -- דירוג לחוזק להשוואת ">=" (מיגרציה 001)
    CONSTRAINT PK_Strength PRIMARY KEY (id)
);
GO

-------------------------------------------------------------------------
-- 4. Reliant  (סומך בטון - lookup)  |  id מתחיל מ-1200
--    שם העמודה זהה לשם הטבלה (Reliant), לפי המודל
-------------------------------------------------------------------------
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Reliant')
CREATE TABLE dbo.Reliant (
    id        INT IDENTITY(1200, 1) NOT NULL,
    Reliant   NVARCHAR(50) NULL,
    CONSTRAINT PK_Reliant PRIMARY KEY (id)
);
GO

-------------------------------------------------------------------------
-- 5. Stone_size  (גודל אבן - lookup)  |  id מתחיל מ-1300
-------------------------------------------------------------------------
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Stone_size')
CREATE TABLE dbo.Stone_size (
    id          INT IDENTITY(1300, 1) NOT NULL,
    Stone_size  NVARCHAR(50) NULL,
    CONSTRAINT PK_Stone_size PRIMARY KEY (id)
);
GO

-------------------------------------------------------------------------
-- 6. Purpose  (מטרת שימוש - lookup)  |  id מתחיל מ-1400
-------------------------------------------------------------------------
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Purpose')
CREATE TABLE dbo.Purpose (
    id                 INT IDENTITY(1400, 1) NOT NULL,
    Purpose            NVARCHAR(50) NULL,
    -- מיפוי מטרה->מפרט נדרש (מיגרציה 001): חוזק/סומך/גודל-אבן
    req_strength_id    INT NULL,
    req_reliant_id     INT NULL,
    req_stone_size_id  INT NULL,
    CONSTRAINT PK_Purpose PRIMARY KEY (id),
    CONSTRAINT FK_Purpose_ReqStrength  FOREIGN KEY (req_strength_id)   REFERENCES dbo.Strength(id),
    CONSTRAINT FK_Purpose_ReqReliant   FOREIGN KEY (req_reliant_id)    REFERENCES dbo.Reliant(id),
    CONSTRAINT FK_Purpose_ReqStoneSize FOREIGN KEY (req_stone_size_id) REFERENCES dbo.Stone_size(id)
);
GO

-------------------------------------------------------------------------
-- 7. Concrete_type  (סוג בטון מורכב)  |  id מתחיל מ-2000
--    מקשר בין חוזק / סומך / גודל אבן / מטרה
-------------------------------------------------------------------------
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Concrete_type')
CREATE TABLE dbo.Concrete_type (
    id             INT IDENTITY(2000, 1) NOT NULL,
    strength_id    INT NULL,
    Reliant_id     INT NULL,
    Stone_size_id  INT NULL,
    Purpose_id     INT NULL,
    CONSTRAINT PK_Concrete_type PRIMARY KEY (id),
    CONSTRAINT FK_ConcreteType_Strength  FOREIGN KEY (strength_id)   REFERENCES dbo.Strength(id),
    CONSTRAINT FK_ConcreteType_Reliant   FOREIGN KEY (Reliant_id)    REFERENCES dbo.Reliant(id),
    CONSTRAINT FK_ConcreteType_StoneSize FOREIGN KEY (Stone_size_id) REFERENCES dbo.Stone_size(id),
    CONSTRAINT FK_ConcreteType_Purpose   FOREIGN KEY (Purpose_id)    REFERENCES dbo.Purpose(id)
);
GO

-------------------------------------------------------------------------
-- 8. ConcreteRequests  (בקשות בטון של לקוחות)  |  request_id מתחיל מ-200
-------------------------------------------------------------------------
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'ConcreteRequests')
CREATE TABLE dbo.ConcreteRequests (
    request_id   INT IDENTITY(200, 1) NOT NULL,
    customer_id  INT NULL,
    purpose_id   INT NULL,
    quantity     DECIMAL(6, 2) NULL,
    address      NVARCHAR(255) NULL,
    lat          DECIMAL(9, 6) NOT NULL,
    lng          DECIMAL(9, 6) NOT NULL,
    [date]       DATE NOT NULL CONSTRAINT DF_ConcreteRequests_date DEFAULT (GETDATE()),
    /* status: מנורמל בשלב 0 (מיגרציה 001) לעמודת מחרוזת עקבית.
       ערכים: OPEN / CLOSED / CANCELLED. בקשה זמינה למנוע כאשר status='OPEN'. */
    [status]     NVARCHAR(20) NOT NULL CONSTRAINT DF_ConcreteRequests_status DEFAULT 'OPEN',
    CONSTRAINT PK_ConcreteRequests PRIMARY KEY (request_id),
    CONSTRAINT FK_ConcreteRequests_Customer FOREIGN KEY (customer_id) REFERENCES dbo.Customers(id),
    CONSTRAINT FK_ConcreteRequests_Purpose  FOREIGN KEY (purpose_id)  REFERENCES dbo.Purpose(id)
);
GO

-------------------------------------------------------------------------
-- 9. ContractorConcreteRequests  (הצעות קבלנים)  |  request_id מתחיל מ-600
-------------------------------------------------------------------------
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'ContractorConcreteRequests')
CREATE TABLE dbo.ContractorConcreteRequests (
    request_id     INT IDENTITY(600, 1) NOT NULL,
    concrete_id    INT NULL,
    contractor_id  INT NULL,
    quantity       DECIMAL(6, 2) NULL,
    address        NVARCHAR(255) NULL,
    lat            DECIMAL(9, 6) NOT NULL,                        -- מיגרציה 001: חובה
    lng            DECIMAL(9, 6) NOT NULL,                        -- מיגרציה 001: חובה
    expiry_time    DATETIME NULL,
    price          NVARCHAR(100) NULL,
    id_customer    INT NULL,
    -- מיגרציה 001: סטטוס ההצעה + חותמת יצירה
    [status]       NVARCHAR(20) NOT NULL CONSTRAINT DF_CCR_status DEFAULT 'OPEN',
    created_at     DATETIME2 NOT NULL CONSTRAINT DF_CCR_created_at DEFAULT SYSDATETIME(),
    CONSTRAINT PK_ContractorConcreteRequests PRIMARY KEY (request_id),
    CONSTRAINT FK_CCR_ConcreteType FOREIGN KEY (concrete_id)   REFERENCES dbo.Concrete_type(id),
    CONSTRAINT FK_CCR_Contractor   FOREIGN KEY (contractor_id) REFERENCES dbo.Contractors(id),
    CONSTRAINT FK_CCR_Request      FOREIGN KEY (id_customer)   REFERENCES dbo.ConcreteRequests(request_id)
);
GO

-------------------------------------------------------------------------
-- 10. OfferMatches  (התאמות פנייה<->בקשה)  |  id מתחיל מ-1   (מיגרציה 003, שלב 3)
--     רשומת התאמה שהמנוע יוצר; בסיס ל"מי הותאם" ו"מי אישר".
-------------------------------------------------------------------------
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'OfferMatches')
CREATE TABLE dbo.OfferMatches (
    id            INT IDENTITY(1, 1) NOT NULL,
    offer_id      INT NOT NULL,
    request_id    INT NOT NULL,
    customer_id   INT NULL,
    score         DECIMAL(12, 4) NULL,
    distance_m    DECIMAL(12, 2) NULL,
    /* status: NOTIFIED / ACCEPTED / DECLINED / SUPERSEDED / EXPIRED (SPEC §6.3) */
    [status]      NVARCHAR(20) NOT NULL CONSTRAINT DF_OfferMatches_status DEFAULT 'NOTIFIED',
    created_at    DATETIME2 NOT NULL CONSTRAINT DF_OfferMatches_created_at DEFAULT SYSDATETIME(),
    responded_at  DATETIME2 NULL,
    CONSTRAINT PK_OfferMatches PRIMARY KEY (id),
    CONSTRAINT UQ_OfferMatches_offer_request UNIQUE (offer_id, request_id),
    CONSTRAINT FK_OfferMatches_Offer    FOREIGN KEY (offer_id)    REFERENCES dbo.ContractorConcreteRequests(request_id),
    CONSTRAINT FK_OfferMatches_Request  FOREIGN KEY (request_id)  REFERENCES dbo.ConcreteRequests(request_id),
    CONSTRAINT FK_OfferMatches_Customer FOREIGN KEY (customer_id) REFERENCES dbo.Customers(id)
);
GO

-------------------------------------------------------------------------
-- 11. Notifications  (מרכז התראות בתוך-אפליקציה)  |  id מתחיל מ-1   (מיגרציה 004, שלב 4)
--     user_id/user_role לוגיים (המשתמש עשוי להיות בכל אחת מ-3 הטבלאות) — ללא FK קשיח.
-------------------------------------------------------------------------
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Notifications')
CREATE TABLE dbo.Notifications (
    id                  INT IDENTITY(1, 1) NOT NULL,
    user_id             INT NOT NULL,
    user_role           NVARCHAR(20) NOT NULL,
    [type]              NVARCHAR(40) NOT NULL,
    title               NVARCHAR(200) NULL,
    body                NVARCHAR(1000) NULL,
    related_offer_id    INT NULL,
    related_request_id  INT NULL,
    is_read             BIT NOT NULL CONSTRAINT DF_Notifications_is_read DEFAULT 0,
    created_at          DATETIME2 NOT NULL CONSTRAINT DF_Notifications_created_at DEFAULT SYSDATETIME(),
    CONSTRAINT PK_Notifications PRIMARY KEY (id)
);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Notifications_user')
    CREATE INDEX IX_Notifications_user
        ON dbo.Notifications (user_id, user_role, is_read, created_at);
GO

PRINT 'Beton schema created successfully.';
GO
