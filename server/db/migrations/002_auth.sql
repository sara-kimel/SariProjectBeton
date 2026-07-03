/* =====================================================================
   Beton — מיגרציה 002: אימות והרשאות (שלב 1)
   ---------------------------------------------------------------------
   סקריפט אידמפוטנטי. מבצע על DB "beton":
     1. Customers / Contractors:
        - user_name -> NVARCHAR(50) NOT NULL + UNIQUE
        - password_hash NVARCHAR(255) NULL   (ממולא ע"י seed.py — bcrypt)
        - created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME()
        - הסרת עמודת password הגלויה (אין ערכים אמיתיים — נמחקת)
     3. טבלה חדשה Admins.
   *** זריעת המנהל הראשוני + password_hash לדמו נעשית ב-db/seed.py
       (דורש bcrypt, לא ניתן ב-SQL טהור). ***
   הרצה:
     sqlcmd -S localhost -E -C -i db\migrations\002_auth.sql
   ===================================================================== */

USE beton;
GO

PRINT '--- מיגרציה 002 (auth): התחלה ---';
GO

/* =====================================================================
   פונקציית עזר: החלת השינויים על טבלת משתמשים (Customers/Contractors)
   מבוצע פעמיים בהמשך (אין פרוצדורות זמניות — קוד משוכפל, מוגן ב-IF).
   ===================================================================== */

/* ---------- Customers ---------- */
-- user_name: מילוי NULL, הרחבה ל-50, NOT NULL
UPDATE dbo.Customers SET user_name = CONCAT('user_', id) WHERE user_name IS NULL;
GO
ALTER TABLE dbo.Customers ALTER COLUMN user_name NVARCHAR(50) NOT NULL;
GO
IF NOT EXISTS (SELECT 1 FROM sys.key_constraints WHERE name = 'UQ_Customers_user_name')
    ALTER TABLE dbo.Customers ADD CONSTRAINT UQ_Customers_user_name UNIQUE (user_name);
GO
IF COL_LENGTH('dbo.Customers', 'password_hash') IS NULL
    ALTER TABLE dbo.Customers ADD password_hash NVARCHAR(255) NULL;
GO
IF COL_LENGTH('dbo.Customers', 'created_at') IS NULL
    ALTER TABLE dbo.Customers ADD created_at DATETIME2 NOT NULL CONSTRAINT DF_Customers_created_at DEFAULT SYSDATETIME();
GO
-- הסרת password הגלוי (אם קיים)
IF COL_LENGTH('dbo.Customers', 'password') IS NOT NULL
    ALTER TABLE dbo.Customers DROP COLUMN [password];
GO

/* ---------- Contractors ---------- */
UPDATE dbo.Contractors SET user_name = CONCAT('user_', id) WHERE user_name IS NULL;
GO
ALTER TABLE dbo.Contractors ALTER COLUMN user_name NVARCHAR(50) NOT NULL;
GO
IF NOT EXISTS (SELECT 1 FROM sys.key_constraints WHERE name = 'UQ_Contractors_user_name')
    ALTER TABLE dbo.Contractors ADD CONSTRAINT UQ_Contractors_user_name UNIQUE (user_name);
GO
IF COL_LENGTH('dbo.Contractors', 'password_hash') IS NULL
    ALTER TABLE dbo.Contractors ADD password_hash NVARCHAR(255) NULL;
GO
IF COL_LENGTH('dbo.Contractors', 'created_at') IS NULL
    ALTER TABLE dbo.Contractors ADD created_at DATETIME2 NOT NULL CONSTRAINT DF_Contractors_created_at DEFAULT SYSDATETIME();
GO
IF COL_LENGTH('dbo.Contractors', 'password') IS NOT NULL
    ALTER TABLE dbo.Contractors DROP COLUMN [password];
GO

/* =====================================================================
   Admins  (מנהלים)  |  id מתחיל מ-1
   ===================================================================== */
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

PRINT '--- מיגרציה 002 (auth): הושלמה ---';
GO
