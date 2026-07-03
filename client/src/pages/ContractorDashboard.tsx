import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { getOffersByContractor } from '../api/offers'
import type { ContractorOffer } from '../api/types'

// לוח בקרה של קבלן — סיכום קצר + כניסה לפניות/פניה חדשה.
export function ContractorDashboard() {
  const { user } = useAuth()
  const [offers, setOffers] = useState<ContractorOffer[]>([])

  useEffect(() => {
    if (!user) return
    getOffersByContractor(user.id)
      .then(setOffers)
      .catch(() => setOffers([]))
  }, [user])

  const open = offers.filter((o) => (o.status ?? 'OPEN').toUpperCase() === 'OPEN').length

  return (
    <div>
      <div className="card">
        <h1>לוח בקרה — קבלן</h1>
        <p className="subtitle">שלום {user?.first_name || user?.user_name} 👋</p>
        <div className="stat-row">
          <div className="stat">
            <span className="stat-num">{offers.length}</span>
            <span className="stat-label">סה״כ פניות</span>
          </div>
          <div className="stat">
            <span className="stat-num">{open}</span>
            <span className="stat-label">פניות פתוחות</span>
          </div>
        </div>
        <div className="cta-row">
          <Link to="/contractor/offers/new" className="btn btn-primary">
            פניה חדשה
          </Link>
          <Link to="/contractor/offers" className="btn">
            הפניות שלי
          </Link>
        </div>
      </div>
    </div>
  )
}
