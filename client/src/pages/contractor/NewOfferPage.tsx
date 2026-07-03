import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { MapPicker } from '../../components/MapPicker'
import {
  getConcreteTypes,
  getPurposes,
  getStrengths,
  getReliants,
  getStoneSizes,
} from '../../api/lookups'
import { sendOffer } from '../../api/offers'
import { extractErrorMessage } from '../../api/client'
import type { ConcreteType, LatLng, Purpose, Strength, Reliant, StoneSize } from '../../api/types'

// בונה תווית קריאה לסוג בטון מצירוף ערכי ה-lookup.
function buildLabel(
  ct: ConcreteType,
  purposes: Map<number, string>,
  strengths: Map<number, string>,
  reliants: Map<number, string>,
  stones: Map<number, string>,
): string {
  const parts: string[] = []
  if (ct.Purpose_id && purposes.has(ct.Purpose_id)) parts.push(purposes.get(ct.Purpose_id)!)
  if (ct.strength_id && strengths.has(ct.strength_id)) parts.push(strengths.get(ct.strength_id)!)
  if (ct.Reliant_id && reliants.has(ct.Reliant_id)) parts.push(reliants.get(ct.Reliant_id)!)
  if (ct.Stone_size_id && stones.has(ct.Stone_size_id)) parts.push(stones.get(ct.Stone_size_id)!)
  return parts.length ? parts.join(' · ') : `סוג בטון #${ct.id}`
}

function toMap<T extends { id: number }>(items: T[], pick: (t: T) => string | null | undefined) {
  const m = new Map<number, string>()
  for (const it of items) {
    const v = pick(it)
    if (v) m.set(it.id, v)
  }
  return m
}

export function NewOfferPage() {
  const navigate = useNavigate()

  const [concreteTypes, setConcreteTypes] = useState<ConcreteType[]>([])
  const [purposes, setPurposes] = useState<Purpose[]>([])
  const [strengths, setStrengths] = useState<Strength[]>([])
  const [reliants, setReliants] = useState<Reliant[]>([])
  const [stones, setStones] = useState<StoneSize[]>([])

  const [concreteId, setConcreteId] = useState('')
  const [quantity, setQuantity] = useState('')
  const [price, setPrice] = useState('')
  const [address, setAddress] = useState('')
  const [expiry, setExpiry] = useState('')
  const [location, setLocation] = useState<LatLng | null>(null)

  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([getConcreteTypes(), getPurposes(), getStrengths(), getReliants(), getStoneSizes()])
      .then(([ct, pu, st, re, so]) => {
        setConcreteTypes(ct)
        setPurposes(pu)
        setStrengths(st)
        setReliants(re)
        setStones(so)
      })
      .catch(() => setError('לא ניתן לטעון את נתוני סוגי הבטון'))
  }, [])

  const options = useMemo(() => {
    const pMap = toMap(purposes, (p) => p.Purpose)
    const sMap = toMap(strengths, (s) => s.strength)
    const rMap = toMap(reliants, (r) => r.Reliant)
    const soMap = toMap(stones, (s) => s.Stone_size)
    return concreteTypes.map((ct) => ({
      id: ct.id,
      label: buildLabel(ct, pMap, sMap, rMap, soMap),
    }))
  }, [concreteTypes, purposes, strengths, reliants, stones])

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError('')

    if (!concreteId) return setError('יש לבחור סוג בטון')
    if (!quantity || Number(quantity) <= 0) return setError('יש להזין כמות גדולה מ-0')
    if (!location) return setError('יש לבחור מיקום על המפה')
    if (!expiry) return setError('יש להזין זמן תפוגה')
    const expiryDate = new Date(expiry)
    if (Number.isNaN(expiryDate.getTime()) || expiryDate.getTime() <= Date.now()) {
      return setError('זמן התפוגה חייב להיות עתידי')
    }

    setSubmitting(true)
    try {
      // /send/ שומר את הפנייה ומריץ מיד את מנוע ההתאמה — מנווטים לפרטי הפנייה
      // כדי להציג את הלקוחות שהותאמו.
      const result = await sendOffer({
        concrete_id: Number(concreteId),
        quantity: Number(quantity),
        price: price || null,
        address: address || null,
        lat: location.lat,
        lng: location.lng,
        // שולחים ISO ב-UTC כדי שהשרת יזהה נכון את התפוגה
        expiry_time: expiryDate.toISOString(),
      })
      navigate(`/contractor/offers/${result.offer_id}`, { replace: true })
    } catch (err) {
      setError(extractErrorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div>
      <h1>פנייה חדשה</h1>
      <p className="subtitle">פרסום שאריות בטון — בחר/י סוג בטון, כמות, מחיר, תפוגה ומיקום</p>

      {error && <div className="alert alert-error">{error}</div>}

      <form className="card" onSubmit={handleSubmit}>
        <div className="form-grid">
          <div className="form-row">
            <label htmlFor="concreteId">סוג בטון *</label>
            <select id="concreteId" value={concreteId} onChange={(e) => setConcreteId(e.target.value)}>
              <option value="">— בחר/י סוג בטון —</option>
              {options.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.label}
                </option>
              ))}
            </select>
            {options.length === 0 && <div className="hint">אין עדיין סוגי בטון במערכת</div>}
          </div>

          <div className="form-row">
            <label htmlFor="quantity">כמות (מ״ק) *</label>
            <input
              id="quantity"
              type="number"
              step="0.01"
              min="0"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              placeholder="לדוגמה: 5"
            />
          </div>

          <div className="form-row">
            <label htmlFor="price">מחיר (₪)</label>
            <input
              id="price"
              type="text"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              placeholder="לדוגמה: 600"
            />
          </div>

          <div className="form-row">
            <label htmlFor="expiry">זמן תפוגה *</label>
            <input
              id="expiry"
              type="datetime-local"
              value={expiry}
              onChange={(e) => setExpiry(e.target.value)}
            />
          </div>

          <div className="form-row">
            <label htmlFor="address">כתובת</label>
            <input
              id="address"
              type="text"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              placeholder="רחוב, עיר"
            />
          </div>
        </div>

        <div className="form-row">
          <label>מיקום על המפה *</label>
          <MapPicker value={location} onChange={setLocation} />
          <div className="coords-line">
            {location
              ? `נבחר: ${location.lat.toFixed(6)}, ${location.lng.toFixed(6)}`
              : 'לחצ/י על המפה כדי לבחור מיקום'}
          </div>
        </div>

        <button type="submit" className="btn btn-primary" disabled={submitting}>
          {submitting ? 'שולח…' : 'פרסום פנייה'}
        </button>
      </form>
    </div>
  )
}
