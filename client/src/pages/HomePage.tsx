import { Link } from 'react-router-dom'

// דף נחיתה ציבורי — הסבר קצר + CTA להרשמה/התחברות, והבחנה לקוח מול קבלן.
export function HomePage() {
  return (
    <div className="app">
      <header className="app-header">
        <div className="brand">🏗️ בטון</div>
        <nav className="nav">
          <Link to="/login">התחברות</Link>
          <Link to="/register" className="btn btn-primary">
            הרשמה
          </Link>
        </nav>
      </header>

      <main className="app-main">
        <div className="card">
          <h1>ברוכים הבאים למערכת בטון 🏗️</h1>
          <p className="subtitle">
            פלטפורמה לתיווך שאריות בטון: קבלנים עם עודפי בטון פוגשים לקוחות שצריכים
            כמות קטנה — לפני שהבטון פג.
          </p>
          <div className="cta-row">
            <Link to="/register" className="btn btn-primary">
              להרשמה
            </Link>
            <Link to="/login" className="btn">
              כבר יש לי חשבון
            </Link>
          </div>
        </div>

        <div className="home-grid">
          <div className="home-card">
            <div className="icon">📋</div>
            <h2>לקוח — צריך בטון</h2>
            <p>פתח/י בקשה לכמות בטון, בחר/י מיקום על המפה וקבל/י התאמות מקבלנים.</p>
          </div>
          <div className="home-card">
            <div className="icon">🚚</div>
            <h2>קבלן — יש שאריות</h2>
            <p>פרסם/י הצעת בטון והפעל/י את מנוע ההתאמה ללקוחות בסביבה.</p>
          </div>
        </div>
      </main>

      <footer className="app-footer">
        פרויקט בטון — מערכת לתיווך שאריות בטון בין קבלנים ללקוחות
      </footer>
    </div>
  )
}
