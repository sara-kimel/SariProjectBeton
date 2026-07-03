import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getNotifications, markNotificationRead } from '../api/notifications'
import { extractErrorMessage } from '../api/client'
import { useAuth } from '../context/AuthContext'
import type { AppNotification } from '../api/types'
import { formatRelativeTime } from '../utils/format'

// מרכז ההתראות של המשתמש המחובר. לחיצה מסמנת כנקרא ומנווטת ליעד הרלוונטי.
export function NotificationsPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [items, setItems] = useState<AppNotification[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    getNotifications()
      .then(setItems)
      .catch((e) => setError(extractErrorMessage(e)))
      .finally(() => setLoading(false))
  }, [])

  async function handleClick(n: AppNotification) {
    if (!n.is_read) {
      try {
        await markNotificationRead(n.id)
        setItems((prev) => prev.map((x) => (x.id === n.id ? { ...x, is_read: true } : x)))
      } catch {
        /* סימון כנקרא אינו קריטי — נתעלם משגיאה */
      }
    }
    if (user?.role === 'customer' && n.related_request_id) {
      navigate(`/customer/requests/${n.related_request_id}`)
    } else if (user?.role === 'contractor' && n.related_offer_id) {
      navigate(`/contractor/offers/${n.related_offer_id}`)
    }
  }

  return (
    <div>
      <div className="page-head">
        <h1>התראות</h1>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {loading ? (
        <div className="card">טוען…</div>
      ) : items.length === 0 ? (
        <div className="card empty-state">
          <p>אין התראות כרגע.</p>
        </div>
      ) : (
        <div className="list">
          {items.map((n) => (
            <button
              key={n.id}
              type="button"
              className={`card list-row notif-item ${n.is_read ? '' : 'notif-unread'}`}
              onClick={() => handleClick(n)}
            >
              <div>
                <strong>{n.title || 'התראה'}</strong>
                <div className="muted">{n.body}</div>
                <div className="muted small">{formatRelativeTime(n.created_at)}</div>
              </div>
              {!n.is_read && <span className="badge badge-open">חדש</span>}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
