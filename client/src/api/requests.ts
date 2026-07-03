// קריאות API לבקשות בטון של לקוחות — endpoint: /concrete-requests
import { api } from './client'
import type { ConcreteRequest, ConcreteRequestCreate } from './types'

export async function getConcreteRequests(): Promise<ConcreteRequest[]> {
  const { data } = await api.get<ConcreteRequest[]>('/concrete-requests/')
  return data
}

export async function getRequestsByCustomer(
  customerId: number,
): Promise<ConcreteRequest[]> {
  const { data } = await api.get<ConcreteRequest[]>(
    `/concrete-requests/customer/${customerId}`,
  )
  return data
}

export async function getConcreteRequest(id: number): Promise<ConcreteRequest> {
  const { data } = await api.get<ConcreteRequest>(`/concrete-requests/${id}`)
  return data
}

export async function createConcreteRequest(
  payload: ConcreteRequestCreate,
): Promise<ConcreteRequest> {
  const { data } = await api.post<ConcreteRequest>('/concrete-requests/', payload)
  return data
}

export async function updateConcreteRequest(
  id: number,
  payload: ConcreteRequestCreate,
): Promise<ConcreteRequest> {
  const { data } = await api.put<ConcreteRequest>(`/concrete-requests/${id}`, payload)
  return data
}

export async function deleteConcreteRequest(id: number): Promise<void> {
  await api.delete(`/concrete-requests/${id}`)
}
