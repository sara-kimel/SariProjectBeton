// טיפוסי TypeScript שמשקפים את ה-DTOs של השרת (תיקיית server/dto).
// שדות Decimal בשרת מוחזרים כמספרים ב-JSON (FastAPI ממיר Decimal ל-float),
// לכן lat/lng/quantity מיוצגים כאן כ-number.

// ---------- אימות (Auth) ----------
export type Role = 'customer' | 'contractor' | 'admin'

// תשובת התחברות/הרשמה מהשרת
export interface TokenResponse {
  access_token: string
  token_type: string
  role: Role
  user_id: number
}

// פרטי המשתמש המחובר (GET /auth/me)
export interface AuthUser {
  id: number
  role: Role
  user_name?: string | null
  first_name?: string | null
  last_name?: string | null
  phone?: string | null
}

// גוף הרשמה
export interface RegisterPayload {
  first_name?: string | null
  last_name?: string | null
  user_name: string
  phone?: string | null
  password: string
}

// ---------- לקוח (Customer) ----------
export interface Customer {
  id: number
  first_name?: string | null
  last_name?: string | null
  user_name?: string | null
  phone?: string | null
}

export interface CustomerCreate {
  first_name?: string | null
  last_name?: string | null
  user_name?: string | null
  phone?: string | null
}

// ---------- קבלן (Contractor) ----------
export interface Contractor {
  id: number
  first_name?: string | null
  last_name?: string | null
  user_name?: string | null
  phone?: string | null
}

export interface ContractorCreate {
  first_name?: string | null
  last_name?: string | null
  user_name?: string | null
  phone?: string | null
}

// ---------- בקשת בטון של לקוח (ConcreteRequest) ----------
export interface ConcreteRequest {
  request_id: number
  customer_id?: number | null
  purpose_id?: number | null
  quantity?: number | null
  address?: string | null
  lat: number
  lng: number
  date: string
  status?: string | null
}

export interface ConcreteRequestCreate {
  customer_id?: number | null
  purpose_id?: number | null
  quantity?: number | null
  address?: string | null
  lat: number
  lng: number
  status?: string | null
}

// ---------- הצעת בטון של קבלן (ContractorConcreteRequest) ----------
export interface ContractorOffer {
  request_id: number
  concrete_id?: number | null
  contractor_id?: number | null
  quantity?: number | null
  address?: string | null
  lat?: number | null
  lng?: number | null
  expiry_time?: string | null
  price?: string | null
  status?: string | null
  created_at?: string | null
}

export interface ContractorOfferCreate {
  concrete_id?: number | null
  contractor_id?: number | null
  quantity?: number | null
  address?: string | null
  lat?: number | null
  lng?: number | null
  expiry_time?: string | null
  price?: string | null
  id_customer?: number | null
}

// ---------- טבלאות lookup ----------
export interface Purpose {
  id: number
  Purpose?: string | null
  req_strength_id?: number | null
  req_reliant_id?: number | null
  req_stone_size_id?: number | null
}

export interface Strength {
  id: number
  strength?: string | null
  sort_order?: number | null
}

export interface Reliant {
  id: number
  Reliant?: string | null
}

export interface StoneSize {
  id: number
  Stone_size?: string | null
}

export interface ConcreteType {
  id: number
  strength_id?: number | null
  Reliant_id?: number | null
  Stone_size_id?: number | null
  Purpose_id?: number | null
}

// ---------- התאמות (OfferMatches) — שלב 3 ----------
// תצוגת התאמה מועשרת: רשומת ההתאמה + צד הבקשה (לקוח) + צד הפנייה (קבלן).
export interface MatchView {
  id: number
  offer_id: number
  request_id: number
  customer_id?: number | null
  score?: number | null
  distance_m?: number | null
  status: string
  created_at?: string | null
  responded_at?: string | null
  // צד הבקשה
  request_quantity?: number | null
  request_address?: string | null
  request_purpose_id?: number | null
  request_date?: string | null
  request_status?: string | null
  // צד הפנייה
  offer_quantity?: number | null
  offer_price?: string | null
  offer_address?: string | null
  offer_expiry_time?: string | null
  offer_status?: string | null
  contractor_id?: number | null
  // פרטי קשר — נחשפים רק לאחר סגירה (status=ACCEPTED); אחרת null
  customer_name?: string | null
  customer_phone?: string | null
  contractor_name?: string | null
  contractor_phone?: string | null
}

// סיכום הרצת המנוע ב-POST /contractor-offers/send/
export interface OfferSendResult {
  offer_id: number
  matched_count: number
  matches: MatchView[]
}

// תוצאת אישור/דחיית עסקה (POST /matches/{id}/accept|decline)
export interface DealResult {
  match_id: number
  offer_id: number
  request_id: number
  match_status: string
  offer_status?: string | null
  request_status?: string | null
  contact_name?: string | null
  contact_phone?: string | null
  message: string
}

// ---------- ניהול (Admin) — שלב 5 ----------
export interface AdminUser {
  id: number
  role: Role
  user_name?: string | null
  first_name?: string | null
  last_name?: string | null
  phone?: string | null
}

export interface AdminStats {
  open_requests: number
  open_offers: number
  closed_deals: number
  total_matches: number
  accepted_matches: number
  match_rate: number
}

// ---------- התראות (Notifications) — שלב 4 ----------
export interface AppNotification {
  id: number
  user_id: number
  user_role: Role
  type: string
  title?: string | null
  body?: string | null
  related_offer_id?: number | null
  related_request_id?: number | null
  is_read: boolean
  created_at?: string | null
}

// קואורדינטה גיאוגרפית — לשימוש רכיב המפה
export interface LatLng {
  lat: number
  lng: number
}
