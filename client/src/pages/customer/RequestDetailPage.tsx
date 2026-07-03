import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { getConcreteRequest, deleteConcreteRequest } from '../../api/requests'
import { getMatchesForRequest, acceptMatch, declineMatch } from '../../api/matches'
import { extractErrorMessage } from '../../api/client'
import type { ConcreteRequest, MatchView } from '../../api/types'
import {
  statusLabel,
  statusClass,
  formatQuantity,
  formatPrice,
  formatDate,
  formatDistance,
  formatCountdown,
} from '../../utils/format'

// פרטי בקשה בודדת + הפניות שהותאמו לה. הלקוח מאשר/דוחה; אישור מוצלח חושף טלפון הקבלן.
export function RequestDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [request, setRequest] = useState<ConcreteRequest | null>(null)
  const [matches, setMatches] = useState<MatchView[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [deleting, setDeleting] = useState(false)
  const [actingId, setActingId] = useState<number | null>(null)

  const reload = useCallback(() => {
    if (!id) return
    getConcreteRequest(Number(id)).then(setRequest).catch((err) => setError(extractErrorMessage(err)))
    getMatchesForRequest(Number(id)).then(setMatches).catch(() => setMatches([]))
  }, [id])

  useEffect(() => {
    if (!id) return
    getConcreteRequest(Number(id))
      .then(setRequest)
      .catch((err) => setError(extractErrorMessage(err)))
      .finally(() => setLoading(false))
    getMatchesForRequest(Number(id))
      .then(setMatches)
      .catch(() => setMatches([]))
  }, [id])

  async function handleAccept(matchId: number) {
    setActingId(matchId)
    setError('')
    setNotice('')
    try {
      const result = await acceptMatch(matchId)
      setNotice(
        `${result.message} ${result.contact_name ? `קבלן: ${result.contact_name}. ` : ''}` +
          `${result.contact_phone ? `טלפון: ${result.contact_phone}` : ''}`,
      )
      reload()
    } catch (err) {
      // 409 "כבר נתפסה" / 410 "פגה" — מציגים ומרעננים כדי לשקף סטטוסים
      setError(extractErrorMessage(err))
      reload()
    } finally {
      setActingId(null)
    }
  }

  async function handleDecline(matchId: number) {
    setActingId(matchId)
    setError('')
    setNotice('')
    try {
      await declineMatch(matchId)
      reload()
    } catch (err) {
      setError(extractErrorMessage(err))
    } finally {
      setActingId(null)
    }
  }

  async function handleDelete() {
    if (!request) return
    if (!window.confirm('לבטל את הבקשה?')) return
    setDeleting(true)
    setError('')
    try {
      await deleteConcreteRequest(request.request_id)
      navigate('/customer/requests', { replace: true })
    } catch (err) {
      setError(extractErrorMessage(err))
      setDeleting(false)
    }
  }

  if (loading) return <div className="card">טוען…</div>
  if (error && !request) return <div className="alert alert-error">{error}</div>
  if (!request) return <div className="card">הבקשה לא נמצאה</div>

  const isOpen = (request.status ?? 'OPEN').toUpperCase() === 'OPEN'

  return (
    <div>
      <div className="page-head">
        <h1>בקשה #{request.request_id}</h1>
        <span className={`badge ${statusClass(request.status)}`}>{statusLabel(request.status)}</span>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {notice && <div className="alert alert-success">{notice}</div>}

      <div className="card">
        <dl className="detail-grid">
          <dt>כמות</dt>
          <dd>{formatQuantity(request.quantity)}</dd>
          <dt>כתובת</dt>
          <dd>{request.address || '—'}</dd>
          <dt>מיקום</dt>
          <dd>
            {request.lat.toFixed(5)}, {request.lng.toFixed(5)}
          </dd>
          <dt>תאריך</dt>
          <dd>{formatDate(request.date)}</dd>
        </dl>
      </div>

      <div className="card">
        <h2>פניות שהותאמו ({matches.length})</h2>
        {matches.length === 0 ? (
          <p className="muted">עדיין לא נמצאו פניות מתאימות. נעדכן אותך כשתימצא שארית מתאימה.</p>
        ) : (
          <div className="list">
            {matches.map((m) => {
              const isNotified = (m.status || '').toUpperCase() === 'NOTIFIED'
              const isAccepted = (m.status || '').toUpperCase() === 'ACCEPTED'
              return (
                <div key={m.id} className="card list-row">
                  <div>
                    <strong>פניה #{m.offer_id}</strong>
                    <div className="muted">
                      {formatQuantity(m.offer_quantity)} · {formatPrice(m.offer_price)} ·{' '}
                      {formatDistance(m.distance_m)}
                      {m.offer_expiry_time ? ` · ${formatCountdown(m.offer_expiry_time)}` : ''}
                    </div>
                    {isAccepted && (
                      <div className="contact-box">
                        ✅ אישרת פניה זו. ליצירת קשר — קבלן: {m.contractor_name || '—'} · טלפון:{' '}
                        <a href={`tel:${m.contractor_phone ?? ''}`}>{m.contractor_phone || '—'}</a>
                      </div>
                    )}
                  </div>
                  <div className="row-actions">
                    <span className={`badge ${statusClass(m.status)}`}>{statusLabel(m.status)}</span>
                    {isNotified && isOpen && (
                      <>
                        <button
                          type="button"
                          className="btn btn-primary"
                          disabled={actingId !== null}
                          onClick={() => handleAccept(m.id)}
                        >
                          {actingId === m.id ? 'מאשר…' : 'אישור'}
                        </button>
                        <button
                          type="button"
                          className="btn btn-ghost"
                          disabled={actingId !== null}
                          onClick={() => handleDecline(m.id)}
                        >
                          דחייה
                        </button>
                      </>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      <div className="cta-row">
        <Link to="/customer/requests" className="btn">
          חזרה לרשימה
        </Link>
        {isOpen && (
          <button type="button" className="btn btn-ghost" onClick={handleDelete} disabled={deleting}>
            {deleting ? 'מבטל…' : 'ביטול בקשה'}
          </button>
        )}
      </div>
    </div>
  )
}
