# שלב R5 — מסכים חסרים והסכמת תנאים (Screens / Profile / History / ToS)

> פרומפט עצמאי לצ'אט חדש. **לפני שמתחילים:** קרא/י את `SPEC.md` (§18 + §12.3/§12.4/§12.6 + §17.1) ואת `prompts/README.md` ו-`prompts/remediation/README.md`. ודא ש-R0 (תיקוני P0) בוצע ושחבילת הבדיקות ירוקה (`cd server && PYTHONUTF8=1 ./.venv/Scripts/python.exe -m pytest -q` → 52 עוברות).
>
> **הערה (2026-07-03):** בעיית טעינת המפה **נפתרה** (הופעל billing על מפתח Google Maps תקין; המפה נטענת ועובדת מקצה-לקצה). לכן **חלופת המיקום הידנית (NetFree) ירדה מההיקף** — אין צורך בה, והשלב מתמקד במסכים החסרים ובהסכמת התנאים בלבד.

## מטרת השלב
לסגור את פערי ה-P2 בצד הלקוח (`SPEC.md` §18.3): להוסיף את המסכים החסרים לפי ה-SPEC — פרופיל/שינוי-סיסמה, היסטוריית עסקאות, והסכמת תנאי-שימוש/פרטיות חובה בהרשמה.

## היקף
**נכלל:** עמוד פרופיל `/profile` עם שינוי סיסמה + יציאה (§12.6) · מסכי היסטוריה `/customer/history` ו-`/contractor/history` (§12.3/§12.4) · עמוד תנאי-שימוש/פרטיות + checkbox הסכמה חובה בהרשמה (§17.1, [חובה]). רובו `client/src`, עם התאמת שרת אופציונלית בלבד (פילטר `?status=`).
**מחוץ להיקף:** ~~חלופת מפה~~ (בוטל — המפה עובדת, ראה ההערה למעלה). `ErrorBoundary`, README אנושי, CI/Dockerfile ובדיקות צד-לקוח (vitest) — שייכים ל-R7. דירוג/מוניטין ודיווח/חסימה — R8. אין נגיעה במנוע ההתאמה, באישור העסקה או בתיקוני R0.

## משימות

### לקוח (client) — פרופיל ושינוי סיסמה

1. **עמוד פרופיל `/profile`** (`SPEC.md` §12.6). ה-endpoint `POST /auth/change-password` כבר קיים (`server/controller/auth_controller.py:130`) ופונקציית ה-API `changePassword(old_password, new_password)` קיימת אך **אינה בשימוש** (`client/src/api/auth.ts:32`); אין route ל-`/profile`. ליצור `client/src/pages/ProfilePage.tsx` (מוגן) שכולל:
   - הצגת פרטי המשתמש מה-`useAuth()` (`client/src/context/AuthContext`): שם משתמש, שם פרטי, תפקיד.
   - טופס שינוי סיסמה (סיסמה נוכחית + חדשה + אימות) שקורא ל-`changePassword`, עם ולידציה תואמת ל-`RegisterPage` (חדשה ≥ 6 תווים, התאמה לאימות), הודעת הצלחה/שגיאה בעברית (`extractErrorMessage`) ומניעת שליחה כפולה (`disabled`).
   - כפתור **יציאה** (`logout` מה-context), כמו ב-`Layout`.
   - לרשום את ה-route ב-`client/src/App.tsx` תחת `<ProtectedRoute>`+`<Layout>` המשותף (ליד `/notifications`, שורה 46): `<Route path="/profile" element={<ProfilePage />} />`.
   - להוסיף קישור "פרופיל" ב-`client/src/components/Layout.tsx` בתפריט המשתמש (`.user-menu`, שורות 48–54, ליד שם המשתמש/כפתור היציאה).

### לקוח (client) — מסכי היסטוריית עסקאות

2. **היסטוריית לקוח `/customer/history`** (`SPEC.md` §12.3). ליצור `client/src/pages/customer/HistoryPage.tsx`: לטעון `getRequestsByCustomer(user.id)` (מ-`client/src/api/requests.ts`) ולסנן ל-`status === 'CLOSED'` (העסקאות שנסגרו). להציג לכל פריט: כמות, תאריך, תג סטטוס (מ-`statusLabel`/`statusClass` הקיימים ב-`client/src/utils/format.ts`, שכבר מטפלים ב-`CLOSED`/`CANCELLED`), ואת **פרטי הצד השני שנחשפו** + המחיר. פרטי הקבלן שאישר והמחיר מגיעים מההתאמה שאושרה — למשוך אותם דרך `getMatchesForRequest(requestId)` (`client/src/api/matches.ts`) ולסנן `status === 'ACCEPTED'`, או פשוט לקשר כל שורה לעמוד הפרטים הקיים `/customer/requests/:id` שכבר חושף טלפון קבלן ומחיר לאחר אישור (§17.1). לכבד את שלושת מצבי ה-UI (טעינה/ריק/שגיאה) כמו ב-`MyRequestsPage`.

3. **היסטוריית קבלן `/contractor/history`** (`SPEC.md` §12.4). ליצור `client/src/pages/contractor/HistoryPage.tsx` באותו דפוס: `getOffersByContractor(user.id)` (מ-`client/src/api/offers.ts`), סינון `status === 'CLOSED'`, הצגת מחיר/כמות/תאריך + פרטי הלקוח שאישר (דרך `getMatchesForOffer` עם `status === 'ACCEPTED'` או קישור ל-`/contractor/offers/:id` שכבר חושף את טלפון הלקוח). לשים לב: לפי מכונת המצב ביטול = `CANCELLED` ותפוגה = `EXPIRED`; ההיסטוריה מציגה `CLOSED` בלבד (עסקאות שהושלמו).

4. **ניתוב וניווט להיסטוריה.** לרשום ב-`client/src/App.tsx` את `/customer/history` בתוך `<RoleRoute allow={['customer']}>` (שורות 48–53) ואת `/contractor/history` בתוך `<RoleRoute allow={['contractor']}>` (שורות 55–60). להוסיף קישורי ניווט ב-`client/src/components/Layout.tsx` בבלוקים המתאימים לתפקיד (customer שורות 27–32, contractor שורות 33–38).

### לקוח (client) — הסכמת תנאי-שימוש ופרטיות [חובה]

5. **עמוד תנאים `/terms`** (`SPEC.md` §17.1, [חובה] — משתפים מספרי טלפון). ליצור `client/src/pages/TermsPage.tsx` ציבורי עם תוכן תנאי-שימוש + מדיניות פרטיות בעברית, שמסביר במפורש שהמערכת היא **תיווך בלבד** (בלי סליקה) ושפרטי הקשר (טלפון) של הצד השני נחשפים לאחר סגירת עסקה. לרשום route ציבורי ב-`client/src/App.tsx` (ליד `/`, שורה 32): `<Route path="/terms" element={<TermsPage />} />` — נגיש גם ללא התחברות.

6. **checkbox הסכמה חובה בהרשמה** (`SPEC.md` §17.1). ב-`client/src/pages/RegisterPage.tsx`, בשלב הטופס (`step === 'form'`, שורות 90–158): להוסיף state `agreed` ו-checkbox "קראתי ואני מסכימ/ה ל<Link to='/terms'>תנאי השימוש ומדיניות הפרטיות</Link>" לפני כפתור השליחה (שורות 149–151). לחסום שליחה עד סימון: להוסיף בדיקה בתחילת `validate()` (שורות 32–37) — אם `!agreed` → החזרת הודעה בעברית ("יש לאשר את תנאי השימוש"). לוודא RTL תקין של ה-checkbox (label לוגי).

### שרת (server) — אופציונלי בלבד

7. **פילטר סטטוס אופציונלי (לא חובה).** ה-SPEC מציג `GET /concrete-requests/customer/{id}?status=CLOSED` (§12.3/§12.4). מסכי ההיסטוריה עובדים ללא זה על-ידי סינון בצד הלקוח. אם בכל זאת מוסיפים פרמטר `status` אופציונלי לראוטרים ולפונקציות ה-API (`getRequestsByCustomer`/`getOffersByContractor`) — לשמור על תאימות-לאחור (ברירת מחדל: כל הסטטוסים), להוסיף בדיקת pytest קצרה, ולא לשבור את 52 הבדיקות הקיימות. אחרת — אין שינויי שרת בשלב זה.

## בדיקת מקצה-לקצה (E2E)
1. **שרת:** `cd server && PYTHONUTF8=1 ./.venv/Scripts/python.exe -m pytest -q` — **52 עוברות** (או 53+ אם נוספה בדיקת פילטר). אין regressions.
2. **בילד לקוח:** `cd client && npm run build` נקי (tsc + vite, ללא שגיאות טיפוס).
3. **פרופיל:** התחברות → `/profile` → שינוי סיסמה תקין (הצלחה) → התחברות מחדש עם הסיסמה החדשה. שינוי עם סיסמה נוכחית שגויה → הודעת שגיאה.
4. **היסטוריה:** לאחר תרחיש עסקה שנסגרה (הרשמה→בקשה→פנייה→התאמה→אישור), `/customer/history` ו-`/contractor/history` מציגים את העסקה עם מחיר, תאריך ופרטי הצד השני; מצב ריק מוצג כשאין עסקאות סגורות.
5. **תנאים:** הרשמה חדשה **חסומה** עד סימון ה-checkbox; קישור `/terms` מציג את העמוד; לאחר סימון — ההרשמה מצליחה.

## הגדרת סיום
1. כל משימות הלקוח (ואופציונלית השרת) בוצעו לפי הקובץ.
2. **חבילת ה-pytest ירוקה** (בלי regressions) ו-`npm run build` נקי.
3. עדכון `SPEC.md` §18.3 — סימון ✅ לפריטים שבוצעו (פרופיל/שינוי-סיסמה, מסכי היסטוריה, הסכמת תנאי-שימוש/פרטיות), ושיקוף ל-`SPEC.html`.
4. עדכון הזיכרון (`memory/project-sari-state.md`, מאונדקס ב-`memory/MEMORY.md`) — מה נוסף (מסכים/route-ים חדשים) והחלטות חדשות.
5. סיכום קצר למשתמש: מה נבנה, איך נבדק, ומה הבא (`R6-tests.md`).

## הערות/מלכודות
- **לא לשבור את 52 הבדיקות הקיימות** — להריץ את הסוויטה אחרי כל שינוי משמעותי. רוב השלב הוא לקוח; אם נוגעים בשרת (פילטר `status`), לשמור תאימות-לאחור.
- **לעשות שימוש חוזר בקיים, לא להמציא מערכת עיצוב חדשה:** `statusLabel`/`statusClass`/`formatQuantity`/`formatPrice` ב-`client/src/utils/format.ts`, מחלקות `.card`/`.alert`/`.empty-state`, ודפוסי הטעינה/ריק/שגיאה מ-`MyRequestsPage`/`MyOffersPage`.
- **שינוי סיסמה:** אם R3 (ביטול טוקנים בשינוי סיסמה) כבר בוצע — שינוי מוצלח עלול לפסול את הטוקן הנוכחי; לטפל בחן (למשל ניתוב ל-`/login` עם הודעה). R3 עצמאי משלב זה — אל תניח שבוצע.
- **חשיפת פרטי קשר רק לאחר סגירה (§17.1):** מסכי ההיסטוריה חייבים לשאוב את טלפון הצד השני מהתאמה במצב `ACCEPTED` (או מעמוד הפרטים) — לא לחשוף טלפונים על עסקאות שאינן סגורות.
- **RTL עברית** בכל מסך/רכיב חדש (checkbox, טבלאות היסטוריה) — מאפיינים לוגיים, כיווניות תקינה.
- **אל תיגע בתיקוני R0** ובסמנטיקת הביטול הרך (`DELETE` = `CANCELLED`), ואל תשנה שמות עמודות DB (`Reliant`/`Stone_size`/`Purpose`).
