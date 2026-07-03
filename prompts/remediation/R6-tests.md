# שלב R6 — השלמת בדיקות (Tests)

> פרומפט עצמאי לצ'אט חדש. **לפני שמתחילים:** קרא/י את SPEC.md (§18 + §13 מקרי-קצה + §5 המנוע) ואת prompts/README.md ו-prompts/remediation/README.md. ודא ש-R0 (תיקוני P0) בוצע ושחבילת הבדיקות ירוקה: מתוך `server/` הרץ `PYTHONUTF8=1 ./.venv/Scripts/python.exe -m pytest -q` → אמור להחזיר **52 passed** (דורש SQL Server מקומי + DB `beton` עם seed).

## מטרת השלב
לסגור את פער הבדיקות המרכזי שזוהה בסקירה (SPEC §18.3): **ליבת מנוע ההתאמה — שלב הדירוג (score) — כרגע 0 כיסוי**, גבולות סינון-הכמות נבדקים חלקית, אין בדיקות שליליות, בדיקת-המרוץ אינה דטרמיניסטית, ואין ולו בדיקה אחת בצד הלקוח. השלב מוסיף בדיקות בלבד — **בלי לשנות קוד ייצור** (חריג יחיד ומותר: חילוץ פונקציית ולידציה טהורה בלקוח לצורך בדיקתה, ללא שינוי התנהגות).

## היקף
**נכלל:**
- בדיקות שרת (pytest) חדשות: דירוג/score, גבולות כמות (OD-4) בפרמטריזציה, בדיקות שליליות (סטטוס לא-OPEN, decline→accept), והפיכת בדיקת-המרוץ לדטרמיניסטית עם `threading.Barrier` + כיסוי צד-בקשה.
- אימות distance_m מול חישוב Haversine עצמאי, ואימות נוסחת ה-score מול המשקלים ב-config.
- הקמת תשתית בדיקות **בצד הלקוח** (vitest + @testing-library/react) והוספת בדיקות ראשונות: הזרקת Authorization + טיפול 401 בשכבת ה-API, ולידציית טפסים, עוזרי `format.ts`, ורינדור RTL.

**מחוץ להיקף:**
- שינוי לוגיקת המנוע/אישור/הרשאות (נבדקים כפי שהם; אם נחשף באג — לתעד ב-SPEC §18, לא לתקן כאן).
- שינוי סמנטיקת ה-`status`/הסכימה (שייך ל-R2).
- smoke E2E בדפדפן אמיתי עם **Playwright** — נשאר כ**המשך אופציונלי/עתידי** (ראה משימה 9); לא חובה לשלב.
- ErrorBoundary/CI/README — שייכים ל-R7.

## משימות

### שרת — בדיקות מנוע ההתאמה (`server/tests/test_matching.py`)

הקובץ כבר מכיל fixture `env` שמכין lookup + לקוח/קבלן ומנקה נתוני `PYTEST3`, ועוזרים: `_mk_purpose`, `_mk_concrete`, `_mk_request(db, cust, purpose_id, qty, lat, lng, tag, days_ago=0)`, `_mk_offer`, `_addrs`. **נצל אותם — אל תשכפל.** שים לב ש-`_mk_request` כבר תומך ב-`days_ago` (שורה ~101) אך אף בדיקה קיימת אינה משתמשת בו (כולן `days_ago=0`, בלי שום assertion על סדר/score).

1. **בדיקת דירוג לפי ותק (waiting_days).** הוסף `test_score_orders_by_waiting_days`: מטרה+concrete תואמים אחת, שתי בקשות **באותו מיקום** (`TA`) עם `days_ago=0` מול `days_ago=7`, כמות בטווח. הרץ `match_requests_for_offer(db, {...})` וסנן את התוצאות ל-`PYTEST3-` בלבד. אמת ש-`results[0]` הוא הבקשה הוותיקה (7 ימים) — כי `score = w1*waiting_days − w2*travel_minutes` והוותק מזכה בניקוד גבוה יותר (SPEC §5.2 שלב 4; המנוע ב-`matching_engine_service.py`, `get_candidates` שורה ~221, ממיין יורד לפי `score` בשורה ~232). אמת גם ש-`results[0]["waiting_days"] >= 7` (רזולוציית יום, §13.4).

2. **בדיקת דירוג לפי מרחק (עונש travel_minutes).** הוסף `test_score_orders_by_distance`: שתי בקשות באותו **ותק** (`days_ago=0`) אך במרחקים שונים בתוך הרדיוס — למשל אחת ב-`TA` ואחת בנקודה ~5 ק"מ ממנה (שתיהן < 10 ק"מ). אמת שהקרובה מדורגת ראשונה (`results[0]`), כי `travel_minutes = (dist/1000)*2` והעונש `w2*travel_minutes` קטן יותר לקרובה. אמת שהניקוד יורד עם המרחק (`results[0]["score"] > results[1]["score"]`).

3. **אימות `distance_m` מול Haversine עצמאי.** באותה בדיקה (או נפרדת `test_distance_matches_haversine`): לכל תוצאה, חשב מרחק ב**מימוש Haversine עצמאי בתוך הבדיקה** (R=6371000, נוסחת `atan2`) בין קואורדינטת הפנייה (`TA`) לקואורדינטת הבקשה, ואמת `abs(result["distance_m"] − expected) < 50` מטר. זהו שומר-סף מפני שגיאות יחידות (מ' מול ק"מ). בנוסף אמת את קשרי הנוסחה מול הקונפיג: `result["travel_minutes"] == (result["distance_m"]/1000)*2` ו-`result["score"] == settings.MATCH_SCORE_W1_WAITING*result["waiting_days"] − settings.MATCH_SCORE_W2_TRAVEL*result["travel_minutes"]` (ייבוא `from config import settings`).

4. **גבולות סינון-הכמות (OD-4) בפרמטריזציה.** כרגע `test_quantity_filter` (שורה ~195) בודק רק ערך אמצעי. הוסף `@pytest.mark.parametrize` על ארבעת הגבולות של `filter_by_quantity` (`matching_engine_service.py` שורות ~354–373; התנאי `min_qty <= qty <= max_qty` בשורה ~370, כאשר `min_qty = offer.qty*0.9`, `max_qty = offer.qty`). בחר `offer.qty = 10.0` כדי שהגבולות ינחתו נקי על `DECIMAL(6,2)`:
   - `request.qty = 10.0` (== `max_qty`) → **מתקבל**.
   - `request.qty = 9.0` (== `min_qty = 0.9×10`) → **מתקבל**.
   - `request.qty = 8.9` (0.89×10, מתחת ל-`min_qty`) → **נדחה**.
   - `request.qty = 10.1` (מעל `max_qty`) → **נדחה**.
   הרץ את הפרמטריזציה **בשני הכיוונים** (OD-6): טריגר A דרך `match_requests_for_offer` (הפנייה `quantity=10.0`, הבקשה משתנה), וטריגר B דרך `match_offers_for_request` (הבקשה `quantity` משתנה מול פנייה `quantity=10.0`; התנאי המקביל בשורה ~441). אפשר גם `test` יחידתי ישיר על `filter_by_quantity(10.0, [{"quantity": v}])` להשלמה מהירה.

5. **בדיקה שלילית — סטטוס לא-OPEN לא מוחזר.** הוסף עוזר `_mk_request_status(...)` (וריאנט של `_mk_request` שמקבל `status`) או SQL ישיר, ובדיקה `test_non_open_request_not_matched`: הכנס בקשה תואמת לחלוטין (גיאו+מטרה+כמות) אך עם `status='CLOSED'`, ועוד אחת `status='CANCELLED'` — ואמת ששתיהן **אינן** בתוצאות (`load_data` מסננת `WHERE [status]='OPEN'`, `matching_engine_service.py` שורה ~57; יש גם הגנה כפולה ב-`get_candidates` שורה ~207). הוסף בקשת ביקורת `status='OPEN'` תואמת שכן חוזרת, כדי להוכיח שהסינון סלקטיבי ולא מרוקן-הכל.

### שרת — בדיקות אישור/דחייה ומרוץ (`server/tests/test_accept.py`)

הקובץ כבר מכיל fixture `scene` (קבלן + פנייה אחת + שני לקוחות + שתי בקשות + שתי התאמות `NOTIFIED` לאותה פנייה: `m1→c1`, `m2→c2`), עוזרים `_mk_contractor/_mk_customer/_mk_offer/_mk_request/_mk_match`, ואת `DealService`. **R0 כבר הוסיף** `test_concurrent_double_booking_prevented` (שורה ~204), `test_cancel_offer_with_matches_soft`, `test_cancel_request_with_matches_soft`, ו-`test_concurrent_accept_first_wins` (שורה ~170) — **אל תשכפל אותן**; השלם סביבן.

6. **מסלול decline→accept.** הוסף `test_decline_then_accept`: על `scene`, קרא `DealService(db).decline_match(d["m1"], d["c1"])` ואז `DealService(db).accept_match(d["m2"], d["c2"])`. אמת: `m1` → `DECLINED`, `m2` → `ACCEPTED`, הפנייה → `CLOSED`, בקשת `c2` → `CLOSED`, וש-`accept` על `m2` הצליח למרות ה-decline הקודם (דחייה אינה נועלת את הפנייה — §13.3). זהו מסלול חיובי משלים לבדיקות ה-409 הקיימות.

7. **בדיקת-מרוץ דטרמיניסטית (`threading.Barrier`).** שפר את מנגנון המרוץ: הוסף `threading.Barrier(2)` שכל worker קורא לו (`barrier.wait()`) מיד לפני `accept_match`, כדי לכפות חפיפה אמיתית בין שני ה-threads (הגרסה הקיימת מסתמכת על תזמון). עטוף בלולאה של **N=10 חזרות** (בכל חזרה לבנות תרחיש טרי או לאפס), ואמת בכל חזרה: בדיוק אישור אחד `"ok"` והשני `409`; הפנייה `CLOSED` פעם אחת; בדיוק התאמה אחת `ACCEPTED`. אפשר להוסיף כבדיקה חדשה `test_concurrent_accept_deterministic` (ולהשאיר את הקיימת) או לשדרג את הקיימת בזהירות. ייבוא: `import threading`, `from database import SessionLocal` (כבר קיים).

8. **מרוץ בצד-הבקשה: שני קבלנים מול אותה בקשה.** `test_concurrent_double_booking_prevented` של R0 מכסה **קבלן יחיד** עם שתי פניות. הוסף `test_concurrent_double_booking_two_contractors`: **שני קבלנים שונים**, שתי פניות (אחת לכל קבלן), **בקשה אחת** של לקוח יחיד שהותאמה לשתיהן (שתי התאמות `NOTIFIED`), ושני אישורים במקביל עם ה-Barrier. אמת שהשער האטומי על הבקשה (FIX-2, `deal_service.py`) מונע double-booking: בדיוק פנייה אחת נסגרת, הבקשה `CLOSED` פעם אחת, ורק קבלן אחד יזכה לחשיפת טלפון הלקוח.

### לקוח — תשתית בדיקות ובדיקות ראשונות (`client/`)

אין כיום שום בדיקת לקוח. הוסף תשתית **vitest** (משתלב מקורית ב-Vite; Node v22 ב-`C:\nvm4w\nodejs`).

9. **התקנה והגדרה.**
   - התקן dev-deps: `npm i -D vitest jsdom @testing-library/react @testing-library/jest-dom @testing-library/user-event axios-mock-adapter` (מתוך `client/`). `axios-mock-adapter` דרוש כדי לבדוק את ה-interceptors של axios מול תגובות מדומות.
   - הוסף ל-`client/package.json` scripts: `"test": "vitest run"` ו-`"test:watch": "vitest"`.
   - הגדר vitest ב-`client/vite.config.ts`: הוסף בראש הקובץ `/// <reference types="vitest/config" />` ובלוק `test: { environment: 'jsdom', globals: true, setupFiles: './src/test/setup.ts', css: false }`.
   - צור `client/src/test/setup.ts` שמייבא `import '@testing-library/jest-dom'` ומכין RTL כמו ב-`index.html` (`document.documentElement.setAttribute('dir','rtl'); document.documentElement.setAttribute('lang','he')`) — כי vitest/jsdom **אינו** טוען את `index.html` (שם מוגדר `<html lang="he" dir="rtl">`).
   - **מלכודת `npm run build`:** `tsconfig.json` כולל `noUnusedLocals`/`noUnusedParameters`/`verbatimModuleSyntax`, ו-`build` מריץ `tsc` על כל `src`. כדי שהבילד יישאר ירוק: הוסף ל-`tsconfig.json` `"exclude": ["src/**/*.test.ts", "src/**/*.test.tsx", "src/test"]`, וצור `client/tsconfig.vitest.json` (יורש מ-`tsconfig.json`, מבטל את ה-exclude ומוסיף `"types": ["vitest/globals", "@testing-library/jest-dom"]`) לשימוש ה-IDE/vitest. ודא ש-`npm run build` וגם `npm run test` שניהם עוברים.

10. **בדיקות שכבת ה-API (`client/src/api/client.ts`).** צור `client/src/api/client.test.ts`:
    - **הזרקת Authorization:** שמור טוקן ב-`localStorage` (`TOKEN_STORAGE_KEY`), עטוף את `api` ב-`axios-mock-adapter`, בצע קריאה, ואמת שה-request היוצא נשא `Authorization: Bearer <token>` (interceptor הבקשה, שורות ~15–22). בדוק גם שבלי טוקן אין כותרת.
    - **טיפול 401:** דמה תגובת `401` על URL שאינו `/auth/login`, ואמת שהטוקן+המשתמש נמחקו מ-`localStorage` (שורות ~31–36). לניתוב (`window.location.href = '/login'`) — **מלכודת jsdom:** השמה ל-`window.location.href` זורקת אזהרת "Not implemented: navigation"; החלף את `window.location` במוק כתיב (`Object.defineProperty(window, 'location', { value: { pathname:'/x', href:'' }, writable:true })` או `vi.stubGlobal`) ואמת את היעד, או לכל הפחות אמת את ניקוי ה-`localStorage`. אמת גם ש-`401` על `/auth/login` **אינו** מנתב (שורה ~31).
    - **`extractErrorMessage`:** אמת מיפוי `detail` מחרוזת → אותה מחרוזת, ו-`detail` מערך (שגיאות Pydantic) → שרשור `msg` (שורות ~43–54).

11. **ולידציית טפסים (חילוץ פונקציה טהורה).** הפונקציה `validate()` ב-`client/src/pages/RegisterPage.tsx` (שורות ~32–37) היא inline ולא ניתנת לבדיקה. חלץ אותה ל-`client/src/utils/validation.ts` כפונקציה טהורה `validateRegister({ userName, password, confirm })` המחזירה `string | null`, וייבא אותה חזרה ל-`RegisterPage` **בלי לשנות התנהגות** (ה-messages זהים: שם < 3 תווים, סיסמה < 6 תווים, סיסמאות לא תואמות). צור `client/src/utils/validation.test.ts` שמכסה את שלושת הגבולות + מקרה תקין. (זהו החריג המותר היחיד לשינוי קוד ייצור — refactor זהה-התנהגות לצורך בדיקה.)

12. **בדיקות `format.ts` (רווח מהיר).** צור `client/src/utils/format.test.ts` על העוזרים הטהורים ב-`client/src/utils/format.ts`: `statusLabel` (כולל `CANCELLED`→"בוטל", `SUPERSEDED`→"נתפסה", ברירת מחדל), `formatQuantity` (`—` ל-null; סיומת מ"ק), `formatDistance` (< 1000 → מ׳; אחרת ק"מ עם ספרה עשרונית), `formatPrice` (הוספת ₪ למספר בלבד). אלה מאמתים RTL/מטבע/יחידות בלי DOM.

13. **בדיקת רינדור RTL.** צור בדיקת render עם `@testing-library/react` (למשל `client/src/pages/RegisterPage.test.tsx` או רכיב פשוט יותר). מכיוון ש-`dir="rtl"` מוגדר ב-`<html>` שב-`index.html` ולא ברכיב עצמו, ה-setup (משימה 9) מציב `dir='rtl'` על `document.documentElement`. עטוף את הרכיב ב-`MemoryRouter` (ובמידת הצורך `AuthProvider` מ-`client/src/context/AuthContext.tsx`), אמת ש**תוויות עברית מרונדרות** (למשל שדות/כפתור ההרשמה), ואמת `expect(document.documentElement.dir).toBe('rtl')`. זו בדיקת smoke לרינדור + כיווניות; לא בדיקת פריסה מלאה.

14. **[אופציונלי/עתידי] smoke E2E בדפדפן (Playwright).** תעד כ**המשך** (לא חובה בשלב זה): התקנת `@playwright/test`, תרחיש smoke יחיד (טעינת דף הבית → מעבר ל-login → רינדור עברי), ובעיית **NetFree** שעלולה לחסום טעינת Google Maps בדפדפן (§13.7 — נפתרת ב-R5). אם לא מבצעים — להשאיר הערה ב-SPEC §18.3.

## בדיקת מקצה-לקצה (E2E)
1. **שרת:** מתוך `server/` הרץ `PYTHONUTF8=1 ./.venv/Scripts/python.exe -m pytest -q`. כל **52 הבדיקות הקיימות** + הבדיקות החדשות (~10–14) עוברות, **אפס רגרסיות**. הרץ ממוקד לוודא את הליבה: `... -m pytest tests/test_matching.py tests/test_accept.py -q`.
2. הרץ את בדיקת-המרוץ הדטרמיניסטית מספר פעמים ברצף (למשל 3 הרצות) כדי לוודא יציבות (אין flakiness): `... -m pytest tests/test_accept.py -q` ×3.
3. **לקוח:** מתוך `client/` הרץ `npm run test` — כל בדיקות vitest ירוקות; ואז `npm run build` (`tsc && vite build`) — עובר נקי (הקבצי-בדיקה מוחרגים מה-build, משימה 9).
4. ודא שאין `console.error` מיותרים בפלט vitest (במיוחד אזהרות jsdom של ניווט — כוסו במוק, משימה 10).

## הגדרת סיום
1. כל משימות השרת והלקוח בוצעו לפי הקובץ; בדיקות בלבד (למעט חילוץ `validateRegister` הזהה-התנהגות).
2. **חבילת ה-pytest ירוקה** (52 קיימות + חדשות, בלי רגרסיות), **`npm run test` ירוק**, וגם **`npm run build`** ירוק.
3. עדכן `SPEC.md` §18.3 — סמן את פריט **"בדיקות"** כ-✅ (בדיקת דירוג/ליבה, גבולות כמות, שליליות, מרוץ דטרמיניסטי, בדיקות לקוח) עם ציון מה בוצע ומה נדחה (Playwright). עדכן בהתאמה את המראה הקריא `SPEC.html`.
4. עדכן את הזיכרון `memory/project-sari-state.md` (מנוהל דרך `memory/MEMORY.md`): כיסוי המנוע נסגר, מספר הבדיקות המעודכן, ותשתית vitest בלקוח.
5. סיכום קצר למשתמש: אילו בדיקות נוספו, מה הכיסוי החדש (score/כמות/שליליות/מרוץ/לקוח), איך נבדק, ומה הבא (R7 — תשתית).

## הערות/מלכודות
- **אל תשבור את 52 הבדיקות הקיימות ואל תשנה קוד ייצור בשרת** — R6 מוסיף בדיקות בלבד. אם בדיקה חדשה חושפת באג במנוע/אישור, תעד אותו ב-SPEC §18 (לא לתקן כאן, כדי לא לערבב אחריות עם שלבי P1/P2).
- **הרץ את הסוויטה אחרי כל שינוי** — הבדיקות תלויות ב-DB `beton` חי עם seed; ריצה מקבילה של שני threads (בדיקות המרוץ) דורשת סשנים נפרדים (`SessionLocal()`), לא את ה-fixture `db` המשותף.
- **ניקוי נתונים:** הקפד על תגיות `PYTEST3-`/`pytest3` (מנוע) ו-`PYTEST4-`/`pytest4` (אישור) ועל ה-`_wipe` הקיים, כדי לא להזליג נתוני-בדיקה ל-DB. כל בדיקה חדשה חייבת להתנקות (fixture או `finally`).
- **דיוק צף ו-`DECIMAL(6,2)`:** בחר ערכי כמות שנוחתים נקי על שתי ספרות עשרוניות (למשל `offer.qty=10.0` → גבולות 9.0/8.9/10.1) כדי שבדיקות-הגבול לא ייפלו על עיגול.
- **`waiting_days` ברזולוציית יום** (עמודת `date` היא `DATE`, §13.4) — אל תבדוק דיוק שעתי; בדוק סדר-גודל (`>= 7` וכו').
- **`threading.Barrier`** מבטיח חפיפה, אך עדיין ייתכן ש-thread יגיע ל-DB מעט אחרי השני — זו התנהגות רצויה; הקביעה היחידה שקבועה היא "בדיוק אחד מצליח". אל תניח מי מהשניים.
- **לקוח — `noUnusedLocals`/`noUnusedParameters`/`verbatimModuleSyntax`** ב-`tsconfig.json` נוקשים; ייבא רק מה שבשימוש, השתמש ב-`import type` לטיפוסים, והחרג את קבצי הבדיקה מה-build (משימה 9) כדי ש-`npm run build` יישאר ירוק.
- **jsdom אינו טוען את `index.html`** — `dir="rtl"`/`lang="he"` חייבים להיקבע ב-`setup.ts`. ניתוב `window.location` ב-jsdom אינו ממומש — החלף במוק לפני בדיקת ה-401.
- **RTL עברית** בכל טקסט בדיקה/הודעה; **שמות עמודות באותיות גדולות** (`Reliant`, `Stone_size`, `Purpose`, `Reliant_id`, `Stone_size_id`, `Purpose_id`) — לא לגעת; ה-SQL בבדיקות משתמש בהם כפי שהם.
- **`requirements.txt` נשאר ASCII** — לא נדרשות תלויות שרת חדשות (pytest/threading כבר קיימים). התלויות החדשות הן dev-deps של הלקוח בלבד.
