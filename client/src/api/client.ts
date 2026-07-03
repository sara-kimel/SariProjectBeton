// מופע axios מרכזי לכל קריאות ה-API. כתובת הבסיס נטענת מ-config.
import axios from 'axios'
import { API_BASE_URL } from '../config'

// מפתחות אחסון הטוקן/המשתמש ב-localStorage
export const TOKEN_STORAGE_KEY = 'beton_token'
export const USER_STORAGE_KEY = 'beton_user'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

// interceptor לבקשה: מזריק Authorization: Bearer <token> אם קיים טוקן שמור
api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_STORAGE_KEY)
  if (token) {
    // ב-InternalAxiosRequestConfig הכותרות תמיד מוגדרות (AxiosHeaders)
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// interceptor לתשובה: 401 => ניקוי טוקן והפניה ל-login; 403 => נותר לטיפול מקומי
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status
    const url: string = error.config?.url ?? ''
    // לא לנתב מחדש כשה-401 מגיע מבקשת ההתחברות עצמה (שם הוא צפוי)
    if (status === 401 && !url.includes('/auth/login')) {
      localStorage.removeItem(TOKEN_STORAGE_KEY)
      localStorage.removeItem(USER_STORAGE_KEY)
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  },
)

// חילוץ הודעת שגיאה קריאה מתשובת שגיאה של FastAPI (שדה detail)
export function extractErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail) && detail.length > 0) {
      return detail.map((d) => d?.msg ?? JSON.stringify(d)).join(', ')
    }
    return error.message
  }
  if (error instanceof Error) return error.message
  return 'אירעה שגיאה לא צפויה'
}
