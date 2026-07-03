// AuthContext — מצב המשתמש/הטוקן, התחברות/הרשמה/יציאה, שמירה ב-localStorage,
// וריענון פרטי המשתמש מהשרת בעליית האפליקציה.
import { createContext, useContext, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import type { AuthUser, Role, RegisterPayload } from '../api/types'
import * as authApi from '../api/auth'
import { TOKEN_STORAGE_KEY, USER_STORAGE_KEY } from '../api/client'

interface AuthContextValue {
  user: AuthUser | null
  token: string | null
  loading: boolean
  login: (userName: string, password: string) => Promise<AuthUser>
  register: (role: Exclude<Role, 'admin'>, payload: RegisterPayload) => Promise<AuthUser>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

function readStoredUser(): AuthUser | null {
  try {
    const raw = localStorage.getItem(USER_STORAGE_KEY)
    return raw ? (JSON.parse(raw) as AuthUser) : null
  } catch {
    return null
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_STORAGE_KEY))
  const [user, setUser] = useState<AuthUser | null>(() => readStoredUser())
  const [loading, setLoading] = useState<boolean>(() => !!localStorage.getItem(TOKEN_STORAGE_KEY))

  // בעליית האפליקציה: אם יש טוקן שמור — לרענן את פרטי המשתמש מהשרת (ולוודא תוקף)
  useEffect(() => {
    let active = true
    if (!localStorage.getItem(TOKEN_STORAGE_KEY)) {
      setLoading(false)
      return
    }
    authApi
      .getMe()
      .then((me) => {
        if (!active) return
        setUser(me)
        localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(me))
      })
      .catch(() => {
        if (!active) return
        localStorage.removeItem(TOKEN_STORAGE_KEY)
        localStorage.removeItem(USER_STORAGE_KEY)
        setToken(null)
        setUser(null)
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [])

  function persist(newToken: string, me: AuthUser) {
    localStorage.setItem(TOKEN_STORAGE_KEY, newToken)
    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(me))
    setToken(newToken)
    setUser(me)
  }

  async function login(userName: string, password: string): Promise<AuthUser> {
    const res = await authApi.login(userName, password)
    // שמירת הטוקן לפני getMe כדי שה-interceptor יצרף אותו
    localStorage.setItem(TOKEN_STORAGE_KEY, res.access_token)
    const me = await authApi.getMe()
    persist(res.access_token, me)
    return me
  }

  async function register(
    role: Exclude<Role, 'admin'>,
    payload: RegisterPayload,
  ): Promise<AuthUser> {
    const res = await authApi.registerByRole(role, payload)
    localStorage.setItem(TOKEN_STORAGE_KEY, res.access_token)
    const me = await authApi.getMe()
    persist(res.access_token, me)
    return me
  }

  function logout() {
    localStorage.removeItem(TOKEN_STORAGE_KEY)
    localStorage.removeItem(USER_STORAGE_KEY)
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
