// קריאות API למרכז ההתראות — endpoint: /notifications (שלב 4).
import { api } from './client'
import type { AppNotification } from './types'

export async function getNotifications(): Promise<AppNotification[]> {
  const { data } = await api.get<AppNotification[]>('/notifications/')
  return data
}

export async function getUnreadCount(): Promise<number> {
  const { data } = await api.get<{ unread: number }>('/notifications/unread-count')
  return data.unread
}

export async function markNotificationRead(id: number): Promise<AppNotification> {
  const { data } = await api.post<AppNotification>(`/notifications/${id}/read`)
  return data
}
