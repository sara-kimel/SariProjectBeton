import { Link } from 'react-router-dom'

export function ForbiddenPage() {
  return (
    <div className="auth-page">
      <div className="card auth-card">
        <h1>403 — אין הרשאה</h1>
        <p className="subtitle">אין לך הרשאה לצפות בעמוד זה.</p>
        <Link to="/app" className="btn btn-primary">
          חזרה ללוח הבקרה
        </Link>
      </div>
    </div>
  )
}
