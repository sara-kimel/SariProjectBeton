/* =====================================================================
   Beton — מיגרציה 003: טבלת OfferMatches (שלב 3)
   ---------------------------------------------------------------------
   סקריפט אידמפוטנטי — ניתן להריץ שוב ושוב בבטחה.
   יוצר את טבלת ההתאמות בין פניית קבלן לבקשת לקוח (SPEC §7.2):
     OfferMatches(id, offer_id, request_id, customer_id, score, distance_m,
                  status, created_at, responded_at, UNIQUE(offer_id, request_id))
   status: NOTIFIED / ACCEPTED / DECLINED / SUPERSEDED / EXPIRED (SPEC §6.3).
   טבלת Notifications תיווצר בשלב 4 (מרכז ההתראות + אישור טרנזקציוני).
   הרצה:
     sqlcmd -S localhost -E -C -i db\migrations\003_matches.sql
   ===================================================================== */

USE beton;
GO

PRINT '--- מיגרציה 003: התחלה ---';
GO

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'OfferMatches')
CREATE TABLE dbo.OfferMatches (
    id            INT IDENTITY(1, 1) NOT NULL,
    offer_id      INT NOT NULL,                 -- FK -> ContractorConcreteRequests(request_id)
    request_id    INT NOT NULL,                 -- FK -> ConcreteRequests(request_id)
    customer_id   INT NULL,                     -- דנורמליזציה לנוחות (FK -> Customers)
    score         DECIMAL(12, 4) NULL,          -- ניקוד מהמנוע
    distance_m    DECIMAL(12, 2) NULL,          -- מרחק במטרים
    /* status: מצב ההתאמה (SPEC §6.3). ברירת מחדל NOTIFIED בעת יצירת ההתאמה. */
    [status]      NVARCHAR(20) NOT NULL CONSTRAINT DF_OfferMatches_status DEFAULT 'NOTIFIED',
    created_at    DATETIME2 NOT NULL CONSTRAINT DF_OfferMatches_created_at DEFAULT SYSDATETIME(),
    responded_at  DATETIME2 NULL,               -- מתי הלקוח הגיב (אישר/דחה)
    CONSTRAINT PK_OfferMatches PRIMARY KEY (id),
    CONSTRAINT UQ_OfferMatches_offer_request UNIQUE (offer_id, request_id),
    CONSTRAINT FK_OfferMatches_Offer    FOREIGN KEY (offer_id)    REFERENCES dbo.ContractorConcreteRequests(request_id),
    CONSTRAINT FK_OfferMatches_Request  FOREIGN KEY (request_id)  REFERENCES dbo.ConcreteRequests(request_id),
    CONSTRAINT FK_OfferMatches_Customer FOREIGN KEY (customer_id) REFERENCES dbo.Customers(id)
);
GO

PRINT '--- מיגרציה 003: הושלמה בהצלחה ---';
GO
