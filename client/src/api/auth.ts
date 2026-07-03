// קריאות ה-API של האימות: הרשמה, התחברות, פרטי המשתמש, שינוי סיסמה.
import { api } from './client'
import type { TokenResponse, AuthUser, RegisterPayload, Role } from './types'

export async function registerCustomer(payload: RegisterPayload): Promise<TokenResponse> {
  const { data } = await api.post<TokenResponse>('/auth/register/customer', payload)
  return data
}

export async function registerContractor(payload: RegisterPayload): Promise<TokenResponse> {
  const { data } = await api.post<TokenResponse>('/auth/register/contractor', payload)
  return data
}

export async function registerByRole(
  role: Exclude<Role, 'admin'>,
  payload: RegisterPayload,
): Promise<TokenResponse> {
  return role === 'customer' ? registerCustomer(payload) : registerContractor(payload)
}

export async function login(user_name: string, password: string): Promise<TokenResponse> {
  const { data } = await api.post<TokenResponse>('/auth/login', { user_name, password })
  return data
}

export async function getMe(): Promise<AuthUser> {
  const { data } = await api.get<AuthUser>('/auth/me')
  return data
}

export async function changePassword(old_password: string, new_password: string): Promise<void> {
  await api.post('/auth/change-password', { old_password, new_password })
}
