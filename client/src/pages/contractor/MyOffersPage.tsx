import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getOffersByContractor } from '../../api/offers'
import { extractErrorMessage } from '../../api/client'
import { useAuth } from '../../context/AuthContext'
import type { ContractorOffer } from '../../api/types'
import { statusLabel, statusClass, formatQuantity, formatPrice, formatCountdown } from '../../utils/format'

// רשימת הפניות של הקבלן המחובר, עם ספירה-לאחור חיה לתפוגה.
export function MyOffersPage() {
  const { user } = useAuth()
  const [offers, setOffers] = useState<ContractorOffer[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [now, setNow] = useState(() => Date.now())

  useEffect(() => {
    if (!user) return
    getOffersByContractor(user.id)
      .then(setOffers)
      .catch((err) => setError(extractErrorMessage(err)))
      .finally(() => setLoading(false))
  }, [user])

  // עדכון הספירה לאחור כל 30 שניות
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 30000)
    return () => clearInterval(t)
  }, [])

  return (
    <div>
      <div className="page-head">
        <h1>הפניות שלי</h1>
        <Link to="/contractor/offers/new" className="btn btn-primary">
          פניה חדשה
        </Link>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {loading ? (
        <div className="card">טוען…</div>
      ) : offers.length === 0 ? (
        <div className="card empty-state">
          <p>עדיין לא פרסמת פניות.</p>
          <Link to="/contractor/offers/new" className="btn btn-primary">
            פרסום פניה ראשונה
          </Link>
        </div>
      ) : (
        <div className="list">
          {offers.map((o) => (
            <Link key={o.request_id} to={`/contractor/offers/${o.request_id}`} className="card list-row">
              <div>
                <strong>פניה #{o.request_id}</strong>
                <div className="muted">
                  {formatQuantity(o.quantity)} · {formatPrice(o.price)} · {formatCountdown(o.expiry_time, now)}
                </div>
              </div>
              <span className={`badge ${statusClass(o.status)}`}>{statusLabel(o.status)}</span>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
