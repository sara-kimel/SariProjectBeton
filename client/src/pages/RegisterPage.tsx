import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { extractErrorMessage } from '../api/client'
import { roleHome } from '../components/RouteGuards'

type Step = 'role' | 'form'
type RegRole = 'customer' | 'contractor'

export function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()

  const [step, setStep] = useState<Step>('role')
  const [role, setRole] = useState<RegRole>('customer')
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [userName, setUserName] = useState('')
  const [phone, setPhone] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  function chooseRole(r: RegRole) {
    setRole(r)
    setError('')
    setStep('form')
  }

  function validate(): string | null {
    if (userName.trim().length < 3) return 'שם משתמש חייב להכיל לפחות 3 תווים'
    if (password.length < 6) return 'סיסמה חייבת להכיל לפחות 6 תווים'
    if (password !== confirm) return 'הסיסמאות אינן תואמות'
    return null
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError('')
    const problem = validate()
    if (problem) {
      setError(problem)
      return
    }
    setSubmitting(true)
    try {
      const me = await register(role, {
        first_name: firstName || null,
        last_name: lastName || null,
        user_name: userName.trim(),
        phone: phone || null,
        password,
      })
      navigate(roleHome(me.role), { replace: true })
    } catch (err) {
      setError(extractErrorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  if (step === 'role') {
    return (
      <div className="auth-page">
        <div className="card auth-card">
          <h1>הרשמה</h1>
          <p className="subtitle">בחר/י את סוג המשתמש</p>
          <div className="home-grid">
            <button type="button" className="home-card" onClick={() => chooseRole('customer')}>
              <div className="icon">📋</div>
              <h2>לקוח</h2>
              <p>צריך/ה כמות בטון קטנה</p>
            </button>
            <button type="button" className="home-card" onClick={() => chooseRole('contractor')}>
              <div className="icon">🚚</div>
              <h2>קבלן</h2>
              <p>יש לי שאריות בטון להציע</p>
            </button>
          </div>
          <p className="auth-alt">
            כבר רשום/ה? <Link to="/login">להתחברות</Link>
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="auth-page">
      <form className="card auth-card" onSubmit={handleSubmit}>
        <h1>הרשמה כ{role === 'customer' ? 'לקוח' : 'קבלן'}</h1>
        <button type="button" className="btn-link" onClick={() => setStep('role')}>
          ← שינוי סוג משתמש
        </button>

        {error && <div className="alert alert-error">{error}</div>}

        <div className="form-grid">
          <div className="form-row">
            <label htmlFor="firstName">שם פרטי</label>
            <input id="firstName" value={firstName} onChange={(e) => setFirstName(e.target.value)} />
          </div>
          <div className="form-row">
            <label htmlFor="lastName">שם משפחה</label>
            <input id="lastName" value={lastName} onChange={(e) => setLastName(e.target.value)} />
          </div>
          <div className="form-row">
            <label htmlFor="userName">שם משתמש *</label>
            <input
              id="userName"
              value={userName}
              onChange={(e) => setUserName(e.target.value)}
              autoComplete="username"
            />
          </div>
          <div className="form-row">
            <label htmlFor="phone">טלפון</label>
            <input
              id="phone"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="050-0000000"
            />
          </div>
          <div className="form-row">
            <label htmlFor="password">סיסמה *</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="new-password"
            />
          </div>
          <div className="form-row">
            <label htmlFor="confirm">אימות סיסמה *</label>
            <input
              id="confirm"
              type="password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              autoComplete="new-password"
            />
          </div>
        </div>

        <button type="submit" className="btn btn-primary" disabled={submitting}>
          {submitting ? 'נרשם…' : 'הרשמה'}
        </button>

        <p className="auth-alt">
          כבר רשום/ה? <Link to="/login">להתחברות</Link>
        </p>
      </form>
    </div>
  )
}
