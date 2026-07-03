/* =====================================================================
   Beton — מיגרציה 005: אינדקסים לביצועים (שלב 6)
   ---------------------------------------------------------------------
   אידמפוטנטי. אינדקסים על עמודות חיפוש/סינון נפוצות: status, מיקום,
   ומפתחות זרים (SQL Server אינו יוצר אינדקס אוטומטי ל-FK).
   הרצה:
     sqlcmd -S localhost -E -C -i db\migrations\005_indexes.sql
   ===================================================================== */

USE beton;
GO

PRINT '--- מיגרציה 005: התחלה ---';
GO

-- ConcreteRequests: המנוע מסנן status='OPEN' + גיאו + FK
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name='IX_CR_status')
    CREATE INDEX IX_CR_status ON dbo.ConcreteRequests([status]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name='IX_CR_geo')
    CREATE INDEX IX_CR_geo ON dbo.ConcreteRequests(lat, lng);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name='IX_CR_customer')
    CREATE INDEX IX_CR_customer ON dbo.ConcreteRequests(customer_id);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name='IX_CR_purpose')
    CREATE INDEX IX_CR_purpose ON dbo.ConcreteRequests(purpose_id);
GO

-- ContractorConcreteRequests: status + expiry (תפוגה עצלה) + FK
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name='IX_CCR_status_expiry')
    CREATE INDEX IX_CCR_status_expiry ON dbo.ContractorConcreteRequests([status], expiry_time);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name='IX_CCR_contractor')
    CREATE INDEX IX_CCR_contractor ON dbo.ContractorConcreteRequests(contractor_id);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name='IX_CCR_concrete')
    CREATE INDEX IX_CCR_concrete ON dbo.ContractorConcreteRequests(concrete_id);
GO

-- OfferMatches: שליפה לפי פנייה/בקשה/סטטוס
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name='IX_OM_offer')
    CREATE INDEX IX_OM_offer ON dbo.OfferMatches(offer_id, [status]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name='IX_OM_request')
    CREATE INDEX IX_OM_request ON dbo.OfferMatches(request_id, [status]);
GO

PRINT '--- מיגרציה 005: הושלמה בהצלחה ---';
GO
