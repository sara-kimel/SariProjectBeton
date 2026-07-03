// קריאות API להתאמות (OfferMatches) — endpoint: /matches (שלבים 3–4).
import { api } from './client'
import type { MatchView, DealResult } from './types'

// ההתאמות של פנייה (לקבלן הבעלים) — הלקוחות שהותאמו, מדורג לפי ניקוד.
export async function getMatchesForOffer(offerId: number): Promise<MatchView[]> {
  const { data } = await api.get<MatchView[]>(`/matches/offer/${offerId}`)
  return data
}

// ההתאמות של בקשה (ללקוח הבעלים) — הפניות שהותאמו.
export async function getMatchesForRequest(requestId: number): Promise<MatchView[]> {
  const { data } = await api.get<MatchView[]>(`/matches/request/${requestId}`)
  return data
}

// לקוח מאשר פנייה (אטומי — הראשון זוכה). מחזיר את פרטי הקבלן ליצירת קשר.
export async function acceptMatch(matchId: number): Promise<DealResult> {
  const { data } = await api.post<DealResult>(`/matches/${matchId}/accept`)
  return data
}

// לקוח דוחה התאמה.
export async function declineMatch(matchId: number): Promise<DealResult> {
  const { data } = await api.post<DealResult>(`/matches/${matchId}/decline`)
  return data
}
