import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { getAdminStats } from '../api/admin'
import { extractErrorMessage } from '../api/client'
import type { AdminStats } from '../api/types'

// לוח בקרה של מנהל — KPI מ-/admin/stats + קיצורים למסכי הניהול.
export function AdminDashboard() {
  const { user } = useAuth()
  const [stats, setStats] = useState<AdminStats | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    getAdminStats()
      .then(setStats)
      .catch((e) => setError(extractErrorMessage(e)))
  }, [])

  return (
    <div>
      <div className="page-head">
        <h1>לוח בקרה — מנהל</h1>
      </div>
      <p className="subtitle">שלום {user?.first_name || user?.user_name} 👋</p>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="stat-grid">
        <div className="card stat"><span className="stat-num">{stats?.open_requests ?? '—'}</span><span className="stat-label">בקשות פתוחות</span></div>
        <div className="card stat"><span className="stat-num">{stats?.open_offers ?? '—'}</span><span className="stat-label">פניות פתוחות</span></div>
        <div className="card stat"><span className="stat-num">{stats?.closed_deals ?? '—'}</span><span className="stat-label">עסקאות שנסגרו</span></div>
        <div className="card stat"><span className="stat-num">{stats ? `${stats.match_rate}%` : '—'}</span><span className="stat-label">אחוז אישור התאמות</span></div>
      </div>

      <div className="cta-row">
        <Link to="/admin/lookups" className="btn btn-primary">ניהול טבלאות עזר</Link>
        <Link to="/admin/concrete-types" className="btn">ניהול סוגי בטון</Link>
        <Link to="/admin/users" className="btn">ניהול משתמשים</Link>
      </div>
    </div>
  )
}
