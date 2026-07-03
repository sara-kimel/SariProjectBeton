// שומרי ניתוב: ProtectedRoute (מחובר בלבד), PublicOnlyRoute (רק לא-מחוברים),
// RoleRoute (תפקיד ספציפי), ו-RoleRedirect (הפניה לפי תפקיד).
import { Navigate, Outlet, useLocation } from 'react-router-dom'
import type { Role } from '../api/types'
import { useAuth } from '../context/AuthContext'

// עמוד הבית של כל תפקיד
export function roleHome(role: Role): string {
  if (role === 'customer') return '/customer'
  if (role === 'contractor') return '/contractor'
  return '/admin'
}

function FullPageLoader() {
  return <div className="app-loading">טוען…</div>
}

// מחייב משתמש מחובר; אחרת מפנה ל-login (ושומר לאן ניסה להגיע)
export function ProtectedRoute() {
  const { user, loading } = useAuth()
  const location = useLocation()
  if (loading) return <FullPageLoader />
  if (!user) return <Navigate to="/login" replace state={{ from: location }} />
  return <Outlet />
}

// עמודים ציבוריים (login/register) — משתמש מחובר מנותב ללוח שלו
export function PublicOnlyRoute() {
  const { user, loading } = useAuth()
  if (loading) return <FullPageLoader />
  if (user) return <Navigate to={roleHome(user.role)} replace />
  return <Outlet />
}

// מחייב אחד התפקידים המותרים; אחרת 403
export function RoleRoute({ allow }: { allow: Role[] }) {
  const { user, loading } = useAuth()
  if (loading) return <FullPageLoader />
  if (!user) return <Navigate to="/login" replace />
  if (!allow.includes(user.role)) return <Navigate to="/403" replace />
  return <Outlet />
}

// /app -> הפניה לעמוד הבית של התפקיד
export function RoleRedirect() {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" replace />
  return <Navigate to={roleHome(user.role)} replace />
}
