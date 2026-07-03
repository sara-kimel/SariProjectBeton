import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { extractErrorMessage } from '../api/client'
import { roleHome } from '../components/RouteGuards'

export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const [userName, setUserName] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError('')
    if (!userName.trim() || !password) {
      setError('יש למלא שם משתמש וסיסמה')
      return
    }
    setSubmitting(true)
    try {
      const me = await login(userName.trim(), password)
      const from = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname
      navigate(from ?? roleHome(me.role), { replace: true })
    } catch (err) {
      setError(extractErrorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="auth-page">
      <form className="card auth-card" onSubmit={handleSubmit}>
        <h1>התחברות</h1>
        {error && <div className="alert alert-error">{error}</div>}

        <div className="form-row">
          <label htmlFor="username">שם משתמש</label>
          <input
            id="username"
            value={userName}
            onChange={(e) => setUserName(e.target.value)}
            autoComplete="username"
          />
        </div>

        <div className="form-row">
          <label htmlFor="password">סיסמה</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
          />
        </div>

        <button type="submit" className="btn btn-primary" disabled={submitting}>
          {submitting ? 'מתחבר…' : 'התחבר'}
        </button>

        <p className="auth-alt">
          אין לך חשבון? <Link to="/register">להרשמה</Link>
        </p>
      </form>
    </div>
  )
}
