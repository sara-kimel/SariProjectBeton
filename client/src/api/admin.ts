// קריאות API לניהול (Admin) — שלב 5.
import { api } from './client'
import type { AdminStats, AdminUser, Role } from './types'

export async function getAdminStats(): Promise<AdminStats> {
  const { data } = await api.get<AdminStats>('/admin/stats')
  return data
}

export async function getAdminUsers(): Promise<AdminUser[]> {
  const { data } = await api.get<AdminUser[]>('/admin/users')
  return data
}

export async function resetUserPassword(
  userId: number,
  role: Role,
  newPassword: string,
): Promise<void> {
  await api.post(`/admin/users/${userId}/reset-password`, { role, new_password: newPassword })
}
