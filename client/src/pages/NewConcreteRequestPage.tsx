import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { MapPicker } from '../components/MapPicker'
import { getPurposes } from '../api/lookups'
import { createConcreteRequest } from '../api/requests'
import { extractErrorMessage } from '../api/client'
import type { Purpose, LatLng } from '../api/types'

// יצירת בקשת בטון של לקוח — הבקשה נקשרת אוטומטית למשתמש המחובר (ללא customer_id ידני).
export function NewConcreteRequestPage() {
  const navigate = useNavigate()
  const [purposes, setPurposes] = useState<Purpose[]>([])
  const [purposeId, setPurposeId] = useState('')
  const [quantity, setQuantity] = useState('')
  const [address, setAddress] = useState('')
  const [location, setLocation] = useState<LatLng | null>(null)

  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    getPurposes()
      .then(setPurposes)
      .catch(() => setError('לא ניתן לטעון את רשימת המטרות'))
  }, [])

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError('')

    if (!purposeId) {
      setError('יש לבחור מטרת שימוש')
      return
    }
    if (!quantity || Number(quantity) <= 0) {
      setError('יש להזין כמות גדולה מ-0')
      return
    }
    if (!location) {
      setError('יש לבחור מיקום על המפה')
      return
    }

    setSubmitting(true)
    try {
      await createConcreteRequest({
        purpose_id: Number(purposeId),
        quantity: Number(quantity),
        address: address || null,
        lat: location.lat,
        lng: location.lng,
      })
      navigate('/customer/requests', { replace: true })
    } catch (err) {
      setError(extractErrorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div>
      <h1>בקשת בטון חדשה</h1>
      <p className="subtitle">מלא/י את פרטי הבקשה ובחר/י מיקום על המפה</p>

      {error && <div className="alert alert-error">{error}</div>}

      <form className="card" onSubmit={handleSubmit}>
        <div className="form-grid">
          <div className="form-row">
            <label htmlFor="purposeId">מטרת השימוש *</label>
            <select id="purposeId" value={purposeId} onChange={(e) => setPurposeId(e.target.value)}>
              <option value="">— בחר/י מטרה —</option>
              {purposes.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.Purpose ?? `מטרה ${p.id}`}
                </option>
              ))}
            </select>
          </div>

          <div className="form-row">
            <label htmlFor="quantity">כמות בטון (מ״ק) *</label>
            <input
              id="quantity"
              type="number"
              step="0.01"
              min="0"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              placeholder="לדוגמה: 3.5"
            />
          </div>

          <div className="form-row">
            <label htmlFor="address">כתובת</label>
            <input
              id="address"
              type="text"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              placeholder="הקלד/י כתובת או בחר/י על המפה — יתמלא אוטומטית"
            />
          </div>
        </div>

        <div className="form-row">
          <label>מיקום על המפה *</label>
          <MapPicker
            value={location}
            onChange={setLocation}
            address={address}
            onAddressResolved={setAddress}
            onLocationResolved={setLocation}
          />
          <div className="coords-line">
            {location
              ? `נבחר: ${location.lat.toFixed(6)}, ${location.lng.toFixed(6)}`
              : 'לחצ/י על המפה כדי לבחור מיקום'}
          </div>
        </div>

        <button type="submit" className="btn btn-primary" disabled={submitting}>
          {submitting ? 'שולח…' : 'שלח בקשה'}
        </button>
      </form>
    </div>
  )
}
