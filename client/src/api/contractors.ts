// קריאות API לניהול קבלנים — endpoint: /contractors
import { api } from './client'
import type { Contractor, ContractorCreate } from './types'

export async function getContractors(): Promise<Contractor[]> {
  const { data } = await api.get<Contractor[]>('/contractors/')
  return data
}

export async function getContractor(id: number): Promise<Contractor> {
  const { data } = await api.get<Contractor>(`/contractors/${id}`)
  return data
}

export async function createContractor(
  payload: ContractorCreate,
): Promise<Contractor> {
  const { data } = await api.post<Contractor>('/contractors/', payload)
  return data
}
