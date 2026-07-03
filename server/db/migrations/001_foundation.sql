/* =====================================================================
   Beton — מיגרציה 001: ייצוב בסיס (שלב 0)
   ---------------------------------------------------------------------
   סקריפט אידמפוטנטי — ניתן להריץ שוב ושוב בבטחה.
   מבצע על DB "beton":
     1. ConcreteRequests.status  -> NVARCHAR(20) NOT NULL DEFAULT 'OPEN'
        (נורמליזציה: NULL/ערך לא-חוקי -> 'OPEN'; ערכים: OPEN/CLOSED/CANCELLED)
     2. ContractorConcreteRequests: הוספת status + created_at,
        והפיכת lat/lng ל-NOT NULL.
     3. Strength.sort_order INT NULL  (דירוג חוזק להשוואת ">=")
     4. Purpose: req_strength_id / req_reliant_id / req_stone_size_id
        (+ FK ל-Strength/Reliant/Stone_size) — מיפוי מטרה->מפרט.
   שדות אימות (password_hash, created_at למשתמשים) — שלב 1, לא כאן.
   הרצה:
     sqlcmd -S localhost -E -C -i db\migrations\001_foundation.sql
   ===================================================================== */

USE beton;
GO

PRINT '--- מיגרציה 001: התחלה ---';
GO

/* =====================================================================
   1. ConcreteRequests.status -> NVARCHAR(20) NOT NULL DEFAULT 'OPEN'
   ===================================================================== */

-- 1א. אם הטיפוס אינו NVARCHAR (כיום DECIMAL) — הסר ברירת מחדל והמר ל-NVARCHAR NULL
IF EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'ConcreteRequests' AND COLUMN_NAME = 'status'
      AND DATA_TYPE <> 'nvarchar'
)
BEGIN
    DECLARE @df_status sysname;
    SELECT @df_status = dc.name
    FROM sys.default_constraints dc
    JOIN sys.columns c
      ON c.object_id = dc.parent_object_id AND c.column_id = dc.parent_column_id
    WHERE dc.parent_object_id = OBJECT_ID('dbo.ConcreteRequests') AND c.name = 'status';

    IF @df_status IS NOT NULL
        EXEC('ALTER TABLE dbo.ConcreteRequests DROP CONSTRAINT ' + @df_status);

    ALTER TABLE dbo.ConcreteRequests ALTER COLUMN [status] NVARCHAR(20) NULL;
    PRINT '1. ConcreteRequests.status הומר ל-NVARCHAR(20) NULL';
END
GO

-- 1ב. נורמול ערכים: NULL או ערך לא-חוקי -> 'OPEN'
UPDATE dbo.ConcreteRequests
SET [status] = 'OPEN'
WHERE [status] IS NULL
   OR [status] NOT IN ('OPEN', 'CLOSED', 'CANCELLED');
GO

-- 1ג. אכיפת NOT NULL
IF EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'ConcreteRequests' AND COLUMN_NAME = 'status' AND IS_NULLABLE = 'YES'
)
    ALTER TABLE dbo.ConcreteRequests ALTER COLUMN [status] NVARCHAR(20) NOT NULL;
GO

-- 1ד. ברירת מחדל 'OPEN' (אם אינה קיימת)
IF NOT EXISTS (
    SELECT 1 FROM sys.default_constraints dc
    JOIN sys.columns c
      ON c.object_id = dc.parent_object_id AND c.column_id = dc.parent_column_id
    WHERE dc.parent_object_id = OBJECT_ID('dbo.ConcreteRequests') AND c.name = 'status'
)
    ALTER TABLE dbo.ConcreteRequests
        ADD CONSTRAINT DF_ConcreteRequests_status DEFAULT 'OPEN' FOR [status];
GO

/* =====================================================================
   2. ContractorConcreteRequests: status + created_at, lat/lng NOT NULL
   ===================================================================== */

-- 2א. status
IF COL_LENGTH('dbo.ContractorConcreteRequests', 'status') IS NULL
    ALTER TABLE dbo.ContractorConcreteRequests
        ADD [status] NVARCHAR(20) NOT NULL CONSTRAINT DF_CCR_status DEFAULT 'OPEN';
GO

-- 2ב. created_at
IF COL_LENGTH('dbo.ContractorConcreteRequests', 'created_at') IS NULL
    ALTER TABLE dbo.ContractorConcreteRequests
        ADD created_at DATETIME2 NOT NULL CONSTRAINT DF_CCR_created_at DEFAULT SYSDATETIME();
GO

-- 2ג. lat/lng -> NOT NULL (מנקים קודם שורות עם NULL — אין כאלה כרגע)
DELETE FROM dbo.ContractorConcreteRequests WHERE lat IS NULL OR lng IS NULL;
GO
IF EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'ContractorConcreteRequests' AND COLUMN_NAME = 'lat' AND IS_NULLABLE = 'YES'
)
    ALTER TABLE dbo.ContractorConcreteRequests ALTER COLUMN lat DECIMAL(9, 6) NOT NULL;
GO
IF EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'ContractorConcreteRequests' AND COLUMN_NAME = 'lng' AND IS_NULLABLE = 'YES'
)
    ALTER TABLE dbo.ContractorConcreteRequests ALTER COLUMN lng DECIMAL(9, 6) NOT NULL;
GO

/* =====================================================================
   3. Strength.sort_order INT NULL
   ===================================================================== */
IF COL_LENGTH('dbo.Strength', 'sort_order') IS NULL
    ALTER TABLE dbo.Strength ADD sort_order INT NULL;
GO

/* =====================================================================
   4. Purpose: req_strength_id / req_reliant_id / req_stone_size_id (+ FK)
   ===================================================================== */
IF COL_LENGTH('dbo.Purpose', 'req_strength_id') IS NULL
    ALTER TABLE dbo.Purpose ADD req_strength_id INT NULL;
GO
IF COL_LENGTH('dbo.Purpose', 'req_reliant_id') IS NULL
    ALTER TABLE dbo.Purpose ADD req_reliant_id INT NULL;
GO
IF COL_LENGTH('dbo.Purpose', 'req_stone_size_id') IS NULL
    ALTER TABLE dbo.Purpose ADD req_stone_size_id INT NULL;
GO

IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_Purpose_ReqStrength')
    ALTER TABLE dbo.Purpose ADD CONSTRAINT FK_Purpose_ReqStrength
        FOREIGN KEY (req_strength_id) REFERENCES dbo.Strength(id);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_Purpose_ReqReliant')
    ALTER TABLE dbo.Purpose ADD CONSTRAINT FK_Purpose_ReqReliant
        FOREIGN KEY (req_reliant_id) REFERENCES dbo.Reliant(id);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_Purpose_ReqStoneSize')
    ALTER TABLE dbo.Purpose ADD CONSTRAINT FK_Purpose_ReqStoneSize
        FOREIGN KEY (req_stone_size_id) REFERENCES dbo.Stone_size(id);
GO

PRINT '--- מיגרציה 001: הושלמה בהצלחה ---';
GO
