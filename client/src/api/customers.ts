// קריאות API לניהול לקוחות — endpoint: /customers
import { api } from './client'
import type { Customer, CustomerCreate } from './types'

export async function getCustomers(): Promise<Customer[]> {
  const { data } = await api.get<Customer[]>('/customers/')
  return data
}

export async function getCustomer(id: number): Promise<Customer> {
  const { data } = await api.get<Customer>(`/customers/${id}`)
  return data
}

export async function createCustomer(payload: CustomerCreate): Promise<Customer> {
  const { data } = await api.post<Customer>('/customers/', payload)
  return data
}
