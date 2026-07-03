import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { getRequestsByCustomer } from '../api/requests'
import type { ConcreteRequest } from '../api/types'

// לוח בקרה של לקוח — סיכום קצר + כניסה לבקשות/בקשה חדשה.
export function CustomerDashboard() {
  const { user } = useAuth()
  const [requests, setRequests] = useState<ConcreteRequest[]>([])

  useEffect(() => {
    if (!user) return
    getRequestsByCustomer(user.id)
      .then(setRequests)
      .catch(() => setRequests([]))
  }, [user])

  const open = requests.filter((r) => (r.status ?? 'OPEN').toUpperCase() === 'OPEN').length

  return (
    <div>
      <div className="card">
        <h1>לוח בקרה — לקוח</h1>
        <p className="subtitle">שלום {user?.first_name || user?.user_name} 👋</p>
        <div className="stat-row">
          <div className="stat">
            <span className="stat-num">{requests.length}</span>
            <span className="stat-label">סה״כ בקשות</span>
          </div>
          <div className="stat">
            <span className="stat-num">{open}</span>
            <span className="stat-label">בקשות פתוחות</span>
          </div>
        </div>
        <div className="cta-row">
          <Link to="/customer/requests/new" className="btn btn-primary">
            בקשת בטון חדשה
          </Link>
          <Link to="/customer/requests" className="btn">
            הבקשות שלי
          </Link>
        </div>
      </div>
    </div>
  )
}
