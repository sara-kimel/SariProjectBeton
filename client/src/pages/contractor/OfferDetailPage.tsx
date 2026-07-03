import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { getOffer, deleteOffer } from '../../api/offers'
import { getMatchesForOffer } from '../../api/matches'
import { extractErrorMessage } from '../../api/client'
import type { ContractorOffer, MatchView } from '../../api/types'
import {
  statusLabel,
  statusClass,
  formatQuantity,
  formatPrice,
  formatCountdown,
  formatDate,
  formatDistance,
} from '../../utils/format'

// פרטי פניה בודדת + רשימת הלקוחות שהותאמו (מדורג לפי ניקוד — שלב 3).
export function OfferDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [offer, setOffer] = useState<ContractorOffer | null>(null)
  const [matches, setMatches] = useState<MatchView[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    if (!id) return
    getOffer(Number(id))
      .then(setOffer)
      .catch((err) => setError(extractErrorMessage(err)))
      .finally(() => setLoading(false))
    // ההתאמות נטענות בנפרד; כשל בשליפתן לא מפיל את מסך הפניה.
    getMatchesForOffer(Number(id))
      .then(setMatches)
      .catch(() => setMatches([]))
  }, [id])

  async function handleDelete() {
    if (!offer) return
    if (!window.confirm('לבטל את הפניה?')) return
    setDeleting(true)
    setError('')
    try {
      await deleteOffer(offer.request_id)
      navigate('/contractor/offers', { replace: true })
    } catch (err) {
      setError(extractErrorMessage(err))
      setDeleting(false)
    }
  }

  if (loading) return <div className="card">טוען…</div>
  if (error && !offer) return <div className="alert alert-error">{error}</div>
  if (!offer) return <div className="card">הפניה לא נמצאה</div>

  const isOpen = (offer.status ?? 'OPEN').toUpperCase() === 'OPEN'
  // ההתאמה שאושרה (אם קיימת) — נחשפים בה פרטי הקשר של הלקוח
  const accepted = matches.find((m) => (m.status || '').toUpperCase() === 'ACCEPTED') || null

  return (
    <div>
      <div className="page-head">
        <h1>פניה #{offer.request_id}</h1>
        <span className={`badge ${statusClass(offer.status)}`}>{statusLabel(offer.status)}</span>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="card">
        <dl className="detail-grid">
          <dt>כמות</dt>
          <dd>{formatQuantity(offer.quantity)}</dd>
          <dt>מחיר</dt>
          <dd>{formatPrice(offer.price)}</dd>
          <dt>תפוגה</dt>
          <dd>
            {formatDate(offer.expiry_time)} ({formatCountdown(offer.expiry_time)})
          </dd>
          <dt>כתובת</dt>
          <dd>{offer.address || '—'}</dd>
          <dt>מיקום</dt>
          <dd>
            {offer.lat != null && offer.lng != null
              ? `${offer.lat.toFixed(5)}, ${offer.lng.toFixed(5)}`
              : '—'}
          </dd>
        </dl>
      </div>

      {accepted && (
        <div className="card">
          <h2>העסקה נסגרה 🎉</h2>
          <div className="contact-box">
            לקוח אישר את הפניה. ליצירת קשר — {accepted.customer_name || 'לקוח'} · טלפון:{' '}
            <a href={`tel:${accepted.customer_phone ?? ''}`}>{accepted.customer_phone || '—'}</a>
          </div>
        </div>
      )}

      <div className="card">
        <h2>לקוחות שהותאמו ({matches.length})</h2>
        {matches.length === 0 ? (
          <p className="muted">לא נמצאו לקוחות מתאימים לפניה זו.</p>
        ) : (
          <div className="list">
            {matches.map((m) => (
              <div key={m.id} className="card list-row">
                <div>
                  <strong>בקשה #{m.request_id}</strong>
                  <div className="muted">
                    {formatQuantity(m.request_quantity)} · {formatDistance(m.distance_m)}
                    {m.request_address ? ` · ${m.request_address}` : ''}
                  </div>
                </div>
                <span className={`badge ${statusClass(m.status)}`}>{statusLabel(m.status)}</span>
              </div>
            ))}
          </div>
        )}
        {matches.length > 0 && !accepted && (
          <p className="muted">פרטי הלקוח ייחשפו לאחר שאחד הלקוחות יאשר את הפניה.</p>
        )}
      </div>

      <div className="cta-row">
        <Link to="/contractor/offers" className="btn">
          חזרה לרשימה
        </Link>
        {isOpen && (
          <button type="button" className="btn btn-ghost" onClick={handleDelete} disabled={deleting}>
            {deleting ? 'מבטל…' : 'ביטול פניה'}
          </button>
        )}
      </div>
    </div>
  )
}
