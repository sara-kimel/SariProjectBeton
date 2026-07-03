import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getUnreadCount } from '../api/notifications'

// פעמון התראות עם מונה לא-נקראו; מתעדכן ב-polling כל 20 שנ' (OD-13, MVP).
export function NotificationBell() {
  const navigate = useNavigate()
  const [count, setCount] = useState(0)

  useEffect(() => {
    let active = true
    const load = () =>
      getUnreadCount()
        .then((c) => {
          if (active) setCount(c)
        })
        .catch(() => {})
    load()
    const t = setInterval(load, 20000)
    return () => {
      active = false
      clearInterval(t)
    }
  }, [])

  return (
    <button
      type="button"
      className="notif-bell"
      onClick={() => navigate('/notifications')}
      title="התראות"
      aria-label={count > 0 ? `${count} התראות שלא נקראו` : 'התראות'}
    >
      <span aria-hidden="true">🔔</span>
      {count > 0 && <span className="notif-badge">{count > 99 ? '99+' : count}</span>}
    </button>
  )
}
