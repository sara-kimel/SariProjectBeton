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

// אפשרויות שעה (00–23) ודקות (00–59) — בורר 24 שעות, ללא AM/PM וללא תאריך.
const HOUR_OPTIONS = Array.from({ length: 24 }, (_, i) => String(i).padStart(2, '0'))
const MINUTE_OPTIONS = Array.from({ length: 60 }, (_, i) => String(i).padStart(2, '0'))

// ברירת מחדל סבירה: בעוד שעה וחצי מעכשיו.
function defaultExpiryParts() {
  const d = new Date(Date.now() + 90 * 60 * 1000)
  return {
    hour: String(d.getHours()).padStart(2, '0'),
    minute: String(d.getMinutes()).padStart(2, '0'),
  }
}

// מועד התפוגה = המופע הקרוב של HH:MM מעכשיו. אם השעה כבר עברה היום — מדובר במחר
// (מטפל גם במעבר חצות). כך אין צורך בבחירת תאריך, והתוצאה תמיד עתידית.
function buildExpiryDate(hour: string, minute: string): Date {
  const exp = new Date()
  exp.setHours(Number(hour), Number(minute), 0, 0)
  if (exp.getTime() <= Date.now()) exp.setDate(exp.getDate() + 1)
  return exp
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
  const [expiryHour, setExpiryHour] = useState(() => defaultExpiryParts().hour)
  const [expiryMin, setExpiryMin] = useState(() => defaultExpiryParts().minute)
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

  // תצוגה מקדימה של מועד התפוגה שנבחר ("היום/מחר בשעה HH:MM") — כדי שברור מתי יפוג.
  const expiryPreview = useMemo(() => {
    const exp = buildExpiryDate(expiryHour, expiryMin)
    const isTomorrow = exp.toDateString() !== new Date().toDateString()
    return `${isTomorrow ? 'מחר' : 'היום'} בשעה ${expiryHour}:${expiryMin}`
  }, [expiryHour, expiryMin])

  // מציג שגיאה וגם גולל אותה לתצוגה — באנר השגיאה בראש העמוד, וכפתור השליחה
  // נמצא מתחת למפה; בלי הגלילה נראה כאילו "כלום לא קרה" בעת שדה חובה חסר.
  function fail(message: string) {
    setError(message)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError('')

    if (!concreteId) return fail('יש לבחור סוג בטון')
    if (!quantity || Number(quantity) <= 0) return fail('יש להזין כמות גדולה מ-0')
    if (!location) return fail('יש לבחור מיקום על המפה')
    // זמן תפוגה = השעה שנבחרה (המופע הקרוב שלה) — תמיד עתידי, אין צורך בוולידציה.
    const expiryDate = buildExpiryDate(expiryHour, expiryMin)

    setSubmitting(true)
    try {
      // /send/ שומר את הפניה ומריץ מיד את מנוע ההתאמה — מנווטים לפרטי הפניה
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
      fail(extractErrorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div>
      <h1>פניה חדשה</h1>
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
            <label htmlFor="expiryHour">זמן תפוגה — עד איזו שעה הבטון פעיל *</label>
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, direction: 'ltr' }}>
              <select
                id="expiryHour"
                value={expiryHour}
                onChange={(e) => setExpiryHour(e.target.value)}
                aria-label="שעה"
                style={{ width: 80 }}
              >
                {HOUR_OPTIONS.map((h) => (
                  <option key={h} value={h}>{h}</option>
                ))}
              </select>
              <span style={{ fontWeight: 700 }}>:</span>
              <select
                value={expiryMin}
                onChange={(e) => setExpiryMin(e.target.value)}
                aria-label="דקות"
                style={{ width: 80 }}
              >
                {MINUTE_OPTIONS.map((m) => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            </div>
            <div className="hint">הפניה תפוג {expiryPreview}</div>
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
          {submitting ? 'שולח…' : 'פרסום פניה'}
        </button>
      </form>
    </div>
  )
}
