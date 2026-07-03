// עזרי תצוגה משותפים — עברית, ₪, מ"ק, וספירה-לאחור לתפוגה.

export function statusLabel(status?: string | null): string {
  switch ((status ?? '').toUpperCase()) {
    case 'OPEN':
      return 'פתוח'
    case 'CLOSED':
      return 'נסגר'
    case 'CANCELLED':
      return 'בוטל'
    case 'EXPIRED':
      return 'פג'
    // מצבי התאמה (OfferMatches) — שלב 3/4
    case 'NOTIFIED':
      return 'הותאם'
    case 'ACCEPTED':
      return 'אושר'
    case 'DECLINED':
      return 'נדחה'
    case 'SUPERSEDED':
      return 'נתפסה'
    default:
      return status || '—'
  }
}

// מחזיר class עזר לפי סטטוס (לצביעת תג)
export function statusClass(status?: string | null): string {
  switch ((status ?? '').toUpperCase()) {
    case 'OPEN':
    case 'NOTIFIED':
      return 'badge-open'
    case 'CLOSED':
    case 'ACCEPTED':
      return 'badge-closed'
    case 'CANCELLED':
    case 'EXPIRED':
    case 'DECLINED':
    case 'SUPERSEDED':
      return 'badge-muted'
    default:
      return 'badge-muted'
  }
}

export function formatQuantity(q?: number | null): string {
  if (q === null || q === undefined) return '—'
  return `${q} מ״ק`
}

export function formatPrice(price?: string | null): string {
  if (!price) return '—'
  const trimmed = String(price).trim()
  // אם זה מספר בלבד — נוסיף ₪
  return /^\d+(\.\d+)?$/.test(trimmed) ? `${trimmed} ₪` : trimmed
}

// מרחק במטרים -> תצוגה בק"מ/מ' (לרשימות ההתאמה, שלב 3).
export function formatDistance(meters?: number | null): string {
  if (meters === null || meters === undefined) return '—'
  if (meters < 1000) return `${Math.round(meters)} מ׳`
  return `${(meters / 1000).toFixed(1)} ק״מ`
}

export function formatDate(iso?: string | null): string {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return String(iso)
  return d.toLocaleDateString('he-IL')
}

// זמן יחסי בעברית ("לפני 3 שעות") — למרכז ההתראות ולרשימות.
export function formatRelativeTime(iso?: string | null): string {
  if (!iso) return '—'
  const t = new Date(iso).getTime()
  if (Number.isNaN(t)) return '—'
  const diffMs = Date.now() - t
  const min = Math.floor(diffMs / 60000)
  if (min < 1) return 'זה עתה'
  if (min < 60) return `לפני ${min} דק׳`
  const hours = Math.floor(min / 60)
  if (hours < 24) return `לפני ${hours} שע׳`
  const days = Math.floor(hours / 24)
  if (days < 30) return `לפני ${days} ימים`
  return formatDate(iso)
}

// ספירה לאחור עד תפוגה. מקבל timestamp מ-Date.now() כדי להתעדכן חי.
export function formatCountdown(expiryIso?: string | null, nowMs?: number): string {
  if (!expiryIso) return '—'
  const expiry = new Date(expiryIso).getTime()
  if (Number.isNaN(expiry)) return '—'
  const now = nowMs ?? Date.now()
  const diff = expiry - now
  if (diff <= 0) return 'פג התוקף'

  const totalMinutes = Math.floor(diff / 60000)
  const days = Math.floor(totalMinutes / (60 * 24))
  const hours = Math.floor((totalMinutes % (60 * 24)) / 60)
  const minutes = totalMinutes % 60

  if (days > 0) return `בעוד ${days} ימים ${hours} שע׳`
  if (hours > 0) return `בעוד ${hours} שע׳ ${minutes} דק׳`
  return `בעוד ${minutes} דק׳`
}
