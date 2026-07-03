// קריאות API להצעות בטון של קבלנים — endpoint: /contractor-offers
import { api } from './client'
import type { ContractorOffer, ContractorOfferCreate, OfferSendResult } from './types'

export async function getOffers(): Promise<ContractorOffer[]> {
  const { data } = await api.get<ContractorOffer[]>('/contractor-offers/')
  return data
}

export async function getOffersByContractor(
  contractorId: number,
): Promise<ContractorOffer[]> {
  const { data } = await api.get<ContractorOffer[]>(
    `/contractor-offers/contractor/${contractorId}`,
  )
  return data
}

export async function getOffer(id: number): Promise<ContractorOffer> {
  const { data } = await api.get<ContractorOffer>(`/contractor-offers/${id}`)
  return data
}

// יצירת פניה (שמירה בלבד בשלב 2 — המנוע לא רץ כאן)
export async function createOffer(
  payload: ContractorOfferCreate,
): Promise<ContractorOffer> {
  const { data } = await api.post<ContractorOffer>('/contractor-offers/', payload)
  return data
}

export async function deleteOffer(id: number): Promise<void> {
  await api.delete(`/contractor-offers/${id}`)
}

// שליחת פניה — /send/ שומר את הפניה, מריץ את מנוע ההתאמה (גיאו → מטרה/מפרט → כמות),
// יוצר רשומות OfferMatches, ומחזיר סיכום מדורג של הלקוחות שהותאמו.
export async function sendOffer(payload: ContractorOfferCreate): Promise<OfferSendResult> {
  const { data } = await api.post<OfferSendResult>('/contractor-offers/send/', payload)
  return data
}
