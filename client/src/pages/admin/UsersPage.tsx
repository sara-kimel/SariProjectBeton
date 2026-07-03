import { useEffect, useState } from 'react'
import type { AdminUser } from '../../api/types'
import { getAdminUsers, resetUserPassword } from '../../api/admin'
import { extractErrorMessage } from '../../api/client'

// ניהול משתמשים — רשימת לקוחות/קבלנים + איפוס סיסמה ע"י מנהל (OD-12).
export function UsersPage() {
  const [users, setUsers] = useState<AdminUser[]>([])
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    getAdminUsers()
      .then(setUsers)
      .catch((e) => setError(extractErrorMessage(e)))
  }, [])

  async function handleReset(u: AdminUser) {
    const pw = window.prompt(`סיסמה זמנית חדשה עבור ${u.user_name}:`)
    if (!pw) return
    setBusy(true); setError(''); setNotice('')
    try {
      await resetUserPassword(u.id, u.role, pw)
      setNotice(`הסיסמה של ${u.user_name} אופסה. יש למסור לו את הסיסמה הזמנית.`)
    } catch (e) {
      setError(extractErrorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div>
      <div className="page-head"><h1>ניהול משתמשים</h1></div>
      {error && <div className="alert alert-error">{error}</div>}
      {notice && <div className="alert alert-success">{notice}</div>}

      <div className="card">
        <table className="admin-table">
          <thead>
            <tr><th>#</th><th>שם משתמש</th><th>שם</th><th>תפקיד</th><th>טלפון</th><th></th></tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={`${u.role}-${u.id}`}>
                <td>{u.id}</td>
                <td>{u.user_name}</td>
                <td>{[u.first_name, u.last_name].filter(Boolean).join(' ') || '—'}</td>
                <td>{u.role === 'customer' ? 'לקוח' : 'קבלן'}</td>
                <td>{u.phone || '—'}</td>
                <td>
                  <button type="button" className="btn btn-ghost" disabled={busy} onClick={() => handleReset(u)}>
                    איפוס סיסמה
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
