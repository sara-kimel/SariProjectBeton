# שלב R4 — הקשחת צד לקוח (Client Hardening)

> פרומפט עצמאי לצ'אט חדש. **לפני שמתחילים:** קרא/י את `SPEC.md` (§18.2 + §12.6 + §12.7 + §17.3) ואת `prompts/README.md` ו-`prompts/remediation/README.md`. ודא ש-R0 (תיקוני P0) בוצע (`prompts/remediation/R0-critical-fixes-DONE.md`) ושחבילת הבדיקות ירוקה: `cd server && PYTHONUTF8=1 ./.venv/Scripts/python.exe -m pytest -q` → **52 passed**.

## מטרת השלב

להפוך את חוויית צד-הלקוח לאמינה ונגישה: להבחין בין "שגיאת רשת" ל"אין נתונים" בלוחות הבקרה, לשדר הודעות שגיאה/הצלחה לקוראי-מסך (`role="alert"`/`aria-live`), להחליף את ה-redirect הקשיח ב-401 בניווט SPA עדין עם הודעת "הסשן פג", לרענן את מונה פעמון ההתראות בזמן אמת, ולתעד את סיכון אחסון הטוקן. שלב איכות בלבד — אין שינוי בסכימה או ב-API של השרת. מקור: `SPEC.md` §18.2 (פריט "לקוח") + §12.7.

## היקף

**נכלל:** רק `client/src` — מצבי טעינה/ריק/שגיאה בלוחות הבקרה (§12.7), רכיב `Alert` נגיש משותף, טיפול 401 מבוסס-SPA + איפוס `AuthContext` דרך אירוע, רענון חי של מונה הפעמון, ותיעוד/שקילת הקשחת אחסון הטוקן.

**מחוץ להיקף:** כל שינוי בשרת/DB/מנוע ההתאמה; מימוש בפועל של refresh-token בשרת (רק תיעוד/הכנה — ראה §12.6); חלופת המפה ל-NetFree ומסכי פרופיל/היסטוריה (שייכים ל-R5); `ErrorBoundary` גלובלי, CI ו-README (שייכים ל-R7); בדיקות vitest צד-לקוח (שייכות ל-R6). אין לחזור על תיקוני R0.

## משימות

### תשתית — רכיב `Alert` נגיש משותף

1. **צור `client/src/components/Alert.tsx`** — רכיב יחיד שעוטף את מחלקות ה-CSS הקיימות (`alert alert-error` / `alert alert-success`, מוגדרות ב-`client/src/index.css` שורות 244–262, אל תשנה אותן). ה-API: `type: 'error' | 'success'`, `children`, ו-`onRetry?`.
   - לשגיאה: `role="alert"` + `aria-live="assertive"` (מכריז מיד).
   - להצלחה/מידע: `role="status"` + `aria-live="polite"`.
   - כאשר מסופק `onRetry` — להציג כפתור "נסה שוב" בתוך ה-alert (עם `type="button"`).
   - RTL: להסתמך על ה-layout הלוגי הקיים; לא לקבע `direction`/`text-align` פיזי.

### לוחות הבקרה — הבחנה בין שגיאה לריק (§12.7)

2. **`client/src/pages/CustomerDashboard.tsx`** — כרגע ה-`useEffect` (שורות 12–17) עושה `getRequestsByCustomer(user.id).then(setRequests).catch(() => setRequests([]))`, כך שכשל רשת נראה זהה ל"אין בקשות" ומציג "0" מטעה (סעיף ה-`stat` בשורות 27–34). לתקן:
   - להוסיף שלושה מצבים לפי §12.7: `loading` (בוליאני, מתחיל `true`), `error` (מחרוזת), ו-`requests`.
   - ב-`.catch` — `setError(extractErrorMessage(err))` (מיובא מ-`../api/client`) במקום לבלוע ל-`[]`; ב-`.finally` — `setLoading(false)`.
   - ברינדור: בזמן `loading` להציג שלד טעינה (skeleton) במקום מספרים; ב-`error` להציג `<Alert type="error" onRetry={reload}>{error}</Alert>` (חלץ את הטעינה לפונקציית `reload` שניתן לקרוא לה מחדש) — ולא להציג את שורת ה-stat עם 0; רק במצב תקין להציג את המספרים ואת שורת ה-CTA (שורות 26–43).
3. **`client/src/pages/ContractorDashboard.tsx`** — אותו תיקון בדיוק לפניות: ה-`.catch(() => setOffers([]))` (שורה 16) → `error`/`loading`/`reload` + `<Alert type="error" onRetry={reload}>`, שלד בזמן טעינה, שורת ה-stat (שורות 27–34) רק במצב תקין.
4. **שלד טעינה (skeleton) מינימלי** — הוסף מחלקת `.skeleton` ל-`client/src/index.css` (רקע בהיר + אנימציית pulse עדינה, `prefers-reduced-motion` מכובד), ושמור אותה לשימוש חוזר בכל מסך רשימה. אין צורך בספריית שלד — `div` פשוט בגובה קבוע מספיק. זה ממלא את מצב "טעינה" שדורש §12.7.

### נגישות — `role="alert"`/`aria-live` בכל ה-alerts

5. **החלף את כל שימושי ה-`<div className="alert alert-error">…</div>` וה-`alert-success` ברכיב `Alert`** (כרגע 0 מופעים של `role=`/`aria-live` בכל `client/src` — grep מאשר). המקומות בפועל:
   - `pages/LoginPage.tsx` (שורה 41), `pages/RegisterPage.tsx` (שורה 98), `pages/NewConcreteRequestPage.tsx` (שורה 67), `pages/NotificationsPage.tsx` (שורה 46).
   - `pages/customer/RequestDetailPage.tsx` (שורות 95, 107 error + 108 success), `pages/customer/MyRequestsPage.tsx` (שורה 33).
   - `pages/contractor/NewOfferPage.tsx` (שורה 123), `pages/contractor/OfferDetailPage.tsx` (שורות 54, 68), `pages/contractor/MyOffersPage.tsx` (שורה 40).
   - `pages/AdminDashboard.tsx` (שורה 27), `pages/admin/UsersPage.tsx` (שורות 36–37), `pages/admin/LookupsPage.tsx` (שורה 65), `pages/admin/ConcreteTypesPage.tsx` (שורה 67).
   - אין לשנות את הטקסטים/הזרימות — רק לעטוף בקומפוננטה כדי שקורא-מסך יכריז. הודעות הצלחה (`notice`) → `type="success"`; שגיאות → `type="error"`.

### פקיעת סשן — ניווט SPA במקום reload (§12.6)

6. **`client/src/api/client.ts`** — ה-interceptor לתשובה (שורות 25–40) עושה `window.location.href = '/login'` על כל 401 (שורה 35), טעינת-דף מלאה שמוחקת את מצב ה-SPA וגורמת להבהוב. לתקן:
   - להשאיר את ניקוי הטוקן/המשתמש מ-`localStorage` ואת החרגת `/auth/login` (שורה 31) כפי שהם.
   - במקום ה-redirect הקשיח — לפרסם אירוע גלובלי, למשל `window.dispatchEvent(new CustomEvent('beton:session-expired'))`, בלי לגעת ב-`window.location`.
7. **`client/src/context/AuthContext.tsx`** — להוסיף `useEffect` שמאזין ל-`'beton:session-expired'` וקורא ל-`logout()` הקיים (שורות 90–95), כדי לאפס את ה-state של ה-SPA (`token`/`user`) בלי reload. כך `ProtectedRoute` יסיט אוטומטית ל-`/login`. בנוסף להעביר סימן "הסשן פג" (למשל `sessionStorage.setItem('beton:session-expired', '1')` בעת האירוע).
8. **`client/src/pages/LoginPage.tsx`** — בעליית הדף, אם קיים הסימן `beton:session-expired` ב-`sessionStorage`, להציג `<Alert type="error">הסשן פג, יש להתחבר מחדש</Alert>` ולנקות את הסימן. הודעה עדינה במקום ניתוק פתאומי.
9. **הכנה ל-refresh-token (תיעוד בלבד, §12.6):** להוסיף הערת TODO קצרה ב-`client/src/api/client.ts` ליד ה-interceptor, שמתארת את נקודת ההרחבה העתידית (ניסיון `POST /auth/refresh` פעם אחת לפני איפוס הסשן). אין לממש כעת — ה-endpoint אינו קיים בשרת וזה מחוץ להיקף.

### מונה פעמון ההתראות — רענון חי

10. **`client/src/components/NotificationBell.tsx`** — כרגע (שורות 10–24) המונה נטען ב-`getUnreadCount()` עם `setInterval` כל 20 שנ' (שורה 19), אך **אינו מתעדכן מיד אחרי סימון התראה כנקראה** (`markNotificationRead` ב-`pages/NotificationsPage.tsx` שורה 27) — הפעמון נשאר "תקוע" עד ה-poll הבא. לתקן שני מנגנונים:
    - **Focus refresh:** להוסיף מאזין ל-`window` events `focus` (ואפשר `visibilitychange`) שקורא ל-`load()` מיד, כדי שהמונה יתרענן בחזרה ללשונית.
    - **עדכון מיידי אחרי קריאה:** להרים את מונה ה-`unread` להקשר משותף (מומלץ ליצור `client/src/context/NotificationsContext.tsx` עם `unreadCount` + `refreshUnread()`), או לחלופין לפרסם אירוע `window.dispatchEvent(new CustomEvent('beton:notifications-changed'))` מ-`NotificationsPage.handleClick` אחרי `markNotificationRead`, ולהאזין לו ב-`NotificationBell` כדי לקרוא `load()` מיד. שמור על ה-polling הקיים כרשת-ביטחון.
    - לשמור את `aria-label` הדינמי הקיים (שורה 32) — הוא כבר נגיש.

### תיעוד/הקשחה (§17.3)

11. **תיעוד סיכון אחסון הטוקן:** להוסיף הערת קוד ב-`client/src/api/client.ts` ליד הגדרת `TOKEN_STORAGE_KEY`/`USER_STORAGE_KEY` (שורות 6–7) שמסבירה שאחסון ה-JWT ב-`localStorage` חשוף ל-XSS, ומפנה למסלול הקשחה: מעבר ל-cookie מסוג `httpOnly`+`SameSite` (דורש שינוי שרת — עתידי) ו/או הגדרת `Content-Security-Policy` הדוקה. לתעד את אותה המלצה בקצרה גם בעדכון הזיכרון וב-`SPEC.md` §18.2 (הפריט "לקוח") כפעולת המשך. אין לשנות את מנגנון האחסון עצמו כעת — שינוי ל-`httpOnly` חוצה שרת ומחוץ להיקף R4.

## בדיקת מקצה-לקצה (E2E)

1. **`npm run build` נקי** (מ-`client/`): `npm run build` (tsc + vite) עובר בלי שגיאות טיפוסים.
2. **הבחנה שגיאה/ריק:** הרץ `npm run dev`, התחבר כלקוח, כבה את השרת (או נתק רשת), רענן את לוח הבקרה — צריך להופיע `Alert` שגיאה עם "נסה שוב", **לא** "0 בקשות". הפעל את השרת מחדש ולחץ "נסה שוב" — הנתונים נטענים. חזור על אותו תרחיש בלוח הקבלן.
3. **טעינה:** בטעינה איטית (throttling ב-DevTools) מופיע שלד ולא מספרים ריקים.
4. **פקיעת סשן:** מחק/שבש ידנית את `beton_token` ב-`localStorage` (או המתן לפקיעת ה-JWT), בצע פעולה שקוראת ל-API — האפליקציה עוברת ל-`/login` **ללא reload מלא** (ה-URL משתנה בלי הבהוב), ומופיעה ההודעה "הסשן פג, יש להתחבר מחדש".
5. **מונה הפעמון:** עם התראות שלא נקראו, פתח `/notifications`, לחץ על התראה — מונה הפעמון ב-Layout יורד **מיד** (לא אחרי 20 שנ'). מעבר ללשונית אחרת וחזרה מרענן את המונה.
6. **נגישות:** ודא ש-`grep -rn "role=\"alert\"" client/src` מחזיר מופעים (כרגע 0), ובדוק עם קורא-מסך/DevTools שהודעות שגיאה מוכרזות.
7. **רגרסיה בשרת:** למרות ששלב זה צד-לקוח בלבד, הרץ את חבילת ה-pytest כדי לוודא שאין השפעה: `cd server && PYTHONUTF8=1 ./.venv/Scripts/python.exe -m pytest -q` → עדיין **52 passed**.

## הגדרת סיום

- כל משימות הלקוח בוצעו; אין שימוש ב-`.catch(() => setX([]))` שבולע שגיאה לריק בלוחות הבקרה; אין יותר `window.location.href` בטיפול ה-401.
- **`npm run build` נקי** ו-**חבילת ה-pytest ירוקה** (52, ללא regressions).
- עדכון `SPEC.md` §18.2 — סימון פריטי ה"לקוח" שבוצעו ✅ (ובמראה הקריא `SPEC.html`).
- עדכון הזיכרון `memory/project-sari-state.md` (מדד ב-`memory/MEMORY.md`): מה תוקן בצד-לקוח, האירוע `beton:session-expired`, וסיכון אחסון הטוקן כפעולת המשך.
- עדכון טבלת השלבים ב-`prompts/remediation/README.md` (שורה R4) ל-✅.
- סיכום קצר למשתמש: מה תוקן, איך נבדק, ומה הבא (R5 — מסכי פרופיל/היסטוריה והסכמת תנאים).

## הערות/מלכודות

- **אל תשבור בדיקות/זרימות קיימות** — כל שינוי מלווה ב-`npm run build`, ובסיום גם הרצת ה-pytest (ודא שנשאר 52 ירוק).
- **RTL בכל מקום** — הסתמך על מאפייני layout לוגיים כפי שקיים; אל תוסיף `direction: rtl` פיזי או יישור ימין/שמאל קשיח ברכיב `Alert`.
- **אל תשנה את מחלקות ה-CSS הקיימות** `.alert`/`.alert-error`/`.alert-success` (`index.css` 244–262) — ה-`Alert` עוטף אותן, כדי שהעיצוב יישאר זהה.
- **בטיפול 401 שמור את החרגת `/auth/login`** (`client.ts` שורה 31) ואת ניקוי הטוקן — רק ה-redirect הקשיח מוחלף. אל תגרום ל-reload מלא בשום מסלול.
- **אל תשבור את הזרקת הטוקן** — ה-interceptor לבקשה (`client.ts` שורות 15–22) והקבועים `TOKEN_STORAGE_KEY`/`USER_STORAGE_KEY` נשארים כפי שהם.
- **הודעות בעברית בלבד** ותמציתיות; אל תחשוף פרטי חריגה גולמיים למשתמש — השתמש ב-`extractErrorMessage` הקיים (`client.ts` שורות 43–54).
- **refresh-token — תיעוד בלבד:** ה-endpoint אינו קיים בשרת; אל תממש קריאת רשת ל-`/auth/refresh` בשלב זה.
- **אחסון הטוקן — לא לשנות כעת:** מעבר ל-cookie `httpOnly` דורש שינוי שרת (מחוץ להיקף R4) — רק לתעד את הסיכון ואת מסלול ההקשחה.
- שינוי צד-לקוח אינו נוגע בשמות עמודות ה-DB (`Reliant`/`Stone_size`/`Purpose`) ואינו נוגע ב-`requirements.txt` — אין כאן מלכודות ASCII/ORM, אך ודא שלא נגעת בהם בטעות.
