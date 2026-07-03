/* =====================================================================
   Beton — מיגרציה 004: טבלת Notifications (שלב 4)
   ---------------------------------------------------------------------
   סקריפט אידמפוטנטי — ניתן להריץ שוב ושוב בבטחה.
   מרכז ההתראות בתוך-האפליקציה (SPEC §7.2, §11). התראה נכתבת לכל אירוע
   (נמצאה התאמה / לקוח אישר / ההצעה נתפסה) ומוצגת למשתמש הרלוונטי.
   הרצה:
     sqlcmd -S localhost -E -C -i db\migrations\004_notifications.sql
   ===================================================================== */

USE beton;
GO

PRINT '--- מיגרציה 004: התחלה ---';
GO

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Notifications')
CREATE TABLE dbo.Notifications (
    id                  INT IDENTITY(1, 1) NOT NULL,
    user_id             INT NOT NULL,                       -- מזהה המשתמש שמקבל את ההתראה
    user_role           NVARCHAR(20) NOT NULL,              -- customer / contractor / admin
    [type]              NVARCHAR(40) NOT NULL,              -- MATCH_FOUND / CUSTOMER_ACCEPTED / OFFER_TAKEN ...
    title               NVARCHAR(200) NULL,
    body                NVARCHAR(1000) NULL,
    related_offer_id    INT NULL,
    related_request_id  INT NULL,
    is_read             BIT NOT NULL CONSTRAINT DF_Notifications_is_read DEFAULT 0,
    created_at          DATETIME2 NOT NULL CONSTRAINT DF_Notifications_created_at DEFAULT SYSDATETIME(),
    CONSTRAINT PK_Notifications PRIMARY KEY (id)
);
GO

-- אינדקס לשליפת התראות המשתמש (מרכז ההתראות + מונה לא-נקראו)
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Notifications_user')
    CREATE INDEX IX_Notifications_user
        ON dbo.Notifications (user_id, user_role, is_read, created_at);
GO

PRINT '--- מיגרציה 004: הושלמה בהצלחה ---';
GO
