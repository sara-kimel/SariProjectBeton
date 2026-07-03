import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return (
    <div className="auth-page">
      <div className="card auth-card">
        <h1>404 — הדף לא נמצא</h1>
        <p className="subtitle">הכתובת שביקשת אינה קיימת.</p>
        <Link to="/" className="btn btn-primary">
          חזרה לדף הבית
        </Link>
      </div>
    </div>
  )
}
