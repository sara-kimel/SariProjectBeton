// קריאות API לטבלאות ה-lookup: מטרות, חוזק, סומך, גודל אבן, סוגי בטון
import { api } from './client'
import type {
  Purpose,
  Strength,
  Reliant,
  StoneSize,
  ConcreteType,
} from './types'

export async function getPurposes(): Promise<Purpose[]> {
  const { data } = await api.get<Purpose[]>('/purposes/')
  return data
}

export async function getStrengths(): Promise<Strength[]> {
  const { data } = await api.get<Strength[]>('/strengths/')
  return data
}

export async function getReliants(): Promise<Reliant[]> {
  const { data } = await api.get<Reliant[]>('/reliants/')
  return data
}

export async function getStoneSizes(): Promise<StoneSize[]> {
  const { data } = await api.get<StoneSize[]>('/stone-sizes/')
  return data
}

export async function getConcreteTypes(): Promise<ConcreteType[]> {
  const { data } = await api.get<ConcreteType[]>('/concrete-types/')
  return data
}

// ---------- ניהול (מנהל בלבד) — שלב 5 ----------

// מטרות
export async function createPurpose(payload: Partial<Purpose>): Promise<Purpose> {
  const { data } = await api.post<Purpose>('/purposes/', payload)
  return data
}
export async function updatePurpose(id: number, payload: Partial<Purpose>): Promise<Purpose> {
  const { data } = await api.put<Purpose>(`/purposes/${id}`, payload)
  return data
}
export async function updatePurposeMapping(
  id: number,
  mapping: { req_strength_id: number | null; req_reliant_id: number | null; req_stone_size_id: number | null },
): Promise<Purpose> {
  const { data } = await api.put<Purpose>(`/purposes/${id}/mapping`, mapping)
  return data
}
export async function deletePurpose(id: number): Promise<void> {
  await api.delete(`/purposes/${id}`)
}

// חוזק (כולל sort_order)
export async function createStrength(payload: Partial<Strength>): Promise<Strength> {
  const { data } = await api.post<Strength>('/strengths/', payload)
  return data
}
export async function updateStrength(id: number, payload: Partial<Strength>): Promise<Strength> {
  const { data } = await api.put<Strength>(`/strengths/${id}`, payload)
  return data
}
export async function deleteStrength(id: number): Promise<void> {
  await api.delete(`/strengths/${id}`)
}

// סומך
export async function createReliant(payload: Partial<Reliant>): Promise<Reliant> {
  const { data } = await api.post<Reliant>('/reliants/', payload)
  return data
}
export async function deleteReliant(id: number): Promise<void> {
  await api.delete(`/reliants/${id}`)
}

// גודל אבן
export async function createStoneSize(payload: Partial<StoneSize>): Promise<StoneSize> {
  const { data } = await api.post<StoneSize>('/stone-sizes/', payload)
  return data
}
export async function deleteStoneSize(id: number): Promise<void> {
  await api.delete(`/stone-sizes/${id}`)
}

// סוגי בטון
export async function createConcreteType(payload: Partial<ConcreteType>): Promise<ConcreteType> {
  const { data } = await api.post<ConcreteType>('/concrete-types/', payload)
  return data
}
export async function deleteConcreteType(id: number): Promise<void> {
  await api.delete(`/concrete-types/${id}`)
}
