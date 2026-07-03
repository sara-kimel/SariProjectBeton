// הגדרות כלליות לצד הלקוח — נטענות ממשתני סביבה (קובץ .env) עם ברירות מחדל

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8001'

export const GOOGLE_MAPS_API_KEY =
  import.meta.env.VITE_GOOGLE_MAPS_API_KEY ?? ''

// מרכז ברירת מחדל למפה — מרכז ישראל (אזור מודיעין)
export const DEFAULT_MAP_CENTER = { lat: 31.9, lng: 34.9 }

// רמת זום התחלתית שמראה את רוב הארץ
export const DEFAULT_MAP_ZOOM = 8
