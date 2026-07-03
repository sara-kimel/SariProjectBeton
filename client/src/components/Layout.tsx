import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { roleHome } from './RouteGuards'
import { NotificationBell } from './NotificationBell'

// מעטפת האזור המחובר: כותרת עם ניווט מותאם-תפקיד, שם המשתמש וכפתור יציאה.
export function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="brand">🏗️ בטון</div>

        <nav className="nav">
          {user && (
            <NavLink to={roleHome(user.role)} end>
              לוח בקרה
            </NavLink>
          )}
          {user?.role === 'customer' && (
            <>
              <NavLink to="/customer/requests">הבקשות שלי</NavLink>
              <NavLink to="/customer/requests/new">בקשה חדשה</NavLink>
            </>
          )}
          {user?.role === 'contractor' && (
            <>
              <NavLink to="/contractor/offers">הפניות שלי</NavLink>
              <NavLink to="/contractor/offers/new">פנייה חדשה</NavLink>
            </>
          )}
          {user?.role === 'admin' && (
            <>
              <NavLink to="/admin/lookups">טבלאות עזר</NavLink>
              <NavLink to="/admin/concrete-types">סוגי בטון</NavLink>
              <NavLink to="/admin/users">משתמשים</NavLink>
            </>
          )}
        </nav>

        <div className="user-menu">
          {(user?.role === 'customer' || user?.role === 'contractor') && <NotificationBell />}
          {user && <span className="user-name">{user.first_name || user.user_name}</span>}
          <button type="button" className="btn btn-ghost" onClick={handleLogout}>
            יציאה
          </button>
        </div>
      </header>

      <main className="app-main">
        <Outlet />
      </main>

      <footer className="app-footer">
        פרויקט בטון — מערכת לתיווך שאריות בטון בין קבלנים ללקוחות
      </footer>
    </div>
  )
}
