import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getRequestsByCustomer } from '../../api/requests'
import { extractErrorMessage } from '../../api/client'
import { useAuth } from '../../context/AuthContext'
import type { ConcreteRequest } from '../../api/types'
import { statusLabel, statusClass, formatQuantity } from '../../utils/format'

// רשימת הבקשות של הלקוח המחובר.
export function MyRequestsPage() {
  const { user } = useAuth()
  const [requests, setRequests] = useState<ConcreteRequest[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!user) return
    getRequestsByCustomer(user.id)
      .then(setRequests)
      .catch((err) => setError(extractErrorMessage(err)))
      .finally(() => setLoading(false))
  }, [user])

  return (
    <div>
      <div className="page-head">
        <h1>הבקשות שלי</h1>
        <Link to="/customer/requests/new" className="btn btn-primary">
          בקשה חדשה
        </Link>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {loading ? (
        <div className="card">טוען…</div>
      ) : requests.length === 0 ? (
        <div className="card empty-state">
          <p>עדיין לא פתחת בקשות.</p>
          <Link to="/customer/requests/new" className="btn btn-primary">
            פתיחת בקשה ראשונה
          </Link>
        </div>
      ) : (
        <div className="list">
          {requests.map((r) => (
            <Link key={r.request_id} to={`/customer/requests/${r.request_id}`} className="card list-row">
              <div>
                <strong>בקשה #{r.request_id}</strong>
                <div className="muted">
                  {formatQuantity(r.quantity)} · {r.address || 'ללא כתובת'}
                </div>
              </div>
              <span className={`badge ${statusClass(r.status)}`}>{statusLabel(r.status)}</span>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
