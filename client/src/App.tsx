import { Routes, Route } from 'react-router-dom'
import { Layout } from './components/Layout'
import {
  ProtectedRoute,
  PublicOnlyRoute,
  RoleRoute,
  RoleRedirect,
} from './components/RouteGuards'
import { HomePage } from './pages/HomePage'
import { LoginPage } from './pages/LoginPage'
import { RegisterPage } from './pages/RegisterPage'
import { CustomerDashboard } from './pages/CustomerDashboard'
import { ContractorDashboard } from './pages/ContractorDashboard'
import { AdminDashboard } from './pages/AdminDashboard'
import { NewConcreteRequestPage } from './pages/NewConcreteRequestPage'
import { NotificationsPage } from './pages/NotificationsPage'
import { LookupsPage } from './pages/admin/LookupsPage'
import { ConcreteTypesPage } from './pages/admin/ConcreteTypesPage'
import { UsersPage } from './pages/admin/UsersPage'
import { MyRequestsPage } from './pages/customer/MyRequestsPage'
import { RequestDetailPage } from './pages/customer/RequestDetailPage'
import { NewOfferPage } from './pages/contractor/NewOfferPage'
import { MyOffersPage } from './pages/contractor/MyOffersPage'
import { OfferDetailPage } from './pages/contractor/OfferDetailPage'
import { ForbiddenPage } from './pages/ForbiddenPage'
import { NotFoundPage } from './pages/NotFoundPage'

export function App() {
  return (
    <Routes>
      {/* ציבורי */}
      <Route path="/" element={<HomePage />} />

      {/* ציבורי-בלבד: מחובר מנותב ללוח שלו */}
      <Route element={<PublicOnlyRoute />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
      </Route>

      {/* מוגן: דורש התחברות */}
      <Route element={<ProtectedRoute />}>
        <Route element={<Layout />}>
          <Route path="/app" element={<RoleRedirect />} />

          {/* מרכז ההתראות — משותף לכל משתמש מחובר */}
          <Route path="/notifications" element={<NotificationsPage />} />

          <Route element={<RoleRoute allow={['customer']} />}>
            <Route path="/customer" element={<CustomerDashboard />} />
            <Route path="/customer/requests" element={<MyRequestsPage />} />
            <Route path="/customer/requests/new" element={<NewConcreteRequestPage />} />
            <Route path="/customer/requests/:id" element={<RequestDetailPage />} />
          </Route>

          <Route element={<RoleRoute allow={['contractor']} />}>
            <Route path="/contractor" element={<ContractorDashboard />} />
            <Route path="/contractor/offers" element={<MyOffersPage />} />
            <Route path="/contractor/offers/new" element={<NewOfferPage />} />
            <Route path="/contractor/offers/:id" element={<OfferDetailPage />} />
          </Route>

          <Route element={<RoleRoute allow={['admin']} />}>
            <Route path="/admin" element={<AdminDashboard />} />
            <Route path="/admin/lookups" element={<LookupsPage />} />
            <Route path="/admin/concrete-types" element={<ConcreteTypesPage />} />
            <Route path="/admin/users" element={<UsersPage />} />
          </Route>
        </Route>
      </Route>

      <Route path="/403" element={<ForbiddenPage />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
