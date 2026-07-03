import { useEffect, useRef } from 'react'
import {
  APIProvider,
  Map,
  Marker,
  useMap,
  useMapsLibrary,
} from '@vis.gl/react-google-maps'
import {
  GOOGLE_MAPS_API_KEY,
  DEFAULT_MAP_CENTER,
  DEFAULT_MAP_ZOOM,
} from '../config'
import type { LatLng } from '../api/types'

interface MapPickerProps {
  value: LatLng | null
  onChange: (coords: LatLng) => void
  // הכתובת הנוכחית (מהשדה בטופס) — משמשת ל-forward geocoding: הקלדת כתובת מזיזה את הסמן.
  address?: string
  // reverse: נקודה על המפה -> כתובת מזוהה (למילוי שדה הכתובת).
  onAddressResolved?: (address: string) => void
  // forward: כתובת שהוקלדה -> נקודה על המפה (להזזת הסמן ומרכוז).
  onLocationResolved?: (coords: LatLng) => void
}

// צורה מבנית מינימלית של תשובת ה-Geocoder (ה-namespace הגלובלי google לא זמין לקוד האפליקציה).
type GeoResult = {
  results?: Array<{
    formatted_address?: string
    geometry?: { location?: { lat(): number; lng(): number } }
  }>
}

// גשר גיאוקודינג דו-כיווני בין המפה לשדה הכתובת. חייב לשבת בתוך <APIProvider>.
//
// מניעת לולאת feedback (כתובת->מפה->כתובת->…): זוכרים בכל כיוון מה אנחנו עצמנו
// הזרמנו (lastReverseAddr / lastForwardLoc) ומדלגים אם הערך הנכנס זהה.
//
// מניעת דריסת קלט במרוצי async: רפרנסים "חיים" (addressRef / valueRef) מאפשרים
// לזהות שהמשתמש שינה את הכיוון השני בזמן שבקשת geocode כבר בדרך, ואז לזרוק את
// התוצאה המאוחרת במקום לדרוס את מה שהמשתמש הקליד/לחץ. mapRef נקרא בזמן הריצה כדי
// שה-pan יעבוד גם אם מופע המפה עדיין לא היה מוכן כשהבקשה תוזמנה.
function GeocodingBridge({
  value,
  address,
  onAddressResolved,
  onLocationResolved,
}: {
  value: LatLng | null
  address?: string
  onAddressResolved?: (address: string) => void
  onLocationResolved?: (coords: LatLng) => void
}) {
  const geocodingLib = useMapsLibrary('geocoding')
  const map = useMap()
  const lastReverseAddr = useRef<string | null>(null)
  const lastForwardLoc = useRef<LatLng | null>(null)

  // רפרנסים חיים לערכים האחרונים (מתעדכנים בכל רינדור)
  const addressRef = useRef(address)
  addressRef.current = address
  const valueRef = useRef<LatLng | null>(value)
  valueRef.current = value
  const mapRef = useRef(map)
  mapRef.current = map

  // REVERSE: נקודה -> כתובת
  useEffect(() => {
    if (!geocodingLib || !value || !onAddressResolved) return
    // דילוג אם הנקודה הזו הגיעה מ-forward geocoding שלנו (אחרת נדרוס את מה שהמשתמש הקליד)
    const f = lastForwardLoc.current
    if (f && f.lat === value.lat && f.lng === value.lng) return

    const addrAtDispatch = addressRef.current
    const geocoder = new geocodingLib.Geocoder()
    let cancelled = false
    geocoder
      .geocode({ location: { lat: value.lat, lng: value.lng } })
      .then((res: GeoResult) => {
        if (cancelled) return
        // המשתמש התחיל להקליד כתובת אחרי הלחיצה — לא דורסים את הקלט שלו בתוצאה מאוחרת
        if (addressRef.current !== addrAtDispatch) return
        const addr = res.results?.[0]?.formatted_address
        if (addr) {
          lastReverseAddr.current = addr
          onAddressResolved(addr)
        }
      })
      .catch(() => {
        /* זיהוי נכשל — לא חוסמים, אפשר להקליד ידנית */
      })
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [geocodingLib, value?.lat, value?.lng])

  // FORWARD: כתובת -> נקודה (עם debounce, מוגבל לישראל)
  useEffect(() => {
    if (!geocodingLib || !onLocationResolved) return
    const q = (address ?? '').trim()
    // סף קצר מספיק לשמות ערים בני 3 אותיות (עכו/צפת/לוד/יפו); ה-debounce מרסן עלות
    if (q.length < 3) return
    // דילוג אם הכתובת הזו הגיעה מ-reverse geocoding שלנו (אחרת לולאה)
    if (q === lastReverseAddr.current) return

    const valueAtSchedule = valueRef.current
    const geocoder = new geocodingLib.Geocoder()
    let cancelled = false
    const timer = setTimeout(() => {
      geocoder
        .geocode({ address: q, componentRestrictions: { country: 'il' } })
        .then((res: GeoResult) => {
          if (cancelled) return
          // המשתמש הזיז את הסמן (לחיצה על המפה) אחרי שהבקשה תוזמנה — לא דורסים את הלחיצה
          const cur = valueRef.current
          if (
            cur &&
            (!valueAtSchedule ||
              cur.lat !== valueAtSchedule.lat ||
              cur.lng !== valueAtSchedule.lng)
          ) {
            return
          }
          const loc = res.results?.[0]?.geometry?.location
          if (loc) {
            const coords = { lat: loc.lat(), lng: loc.lng() }
            lastForwardLoc.current = coords
            onLocationResolved(coords)
            mapRef.current?.panTo(coords)
            mapRef.current?.setZoom(15)
          }
        })
        .catch(() => {
          /* כתובת לא זוהתה — נשארים כמו שהמשתמש הקליד */
        })
    }, 800)
    return () => {
      cancelled = true
      clearTimeout(timer)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [geocodingLib, address])

  return null
}

// רכיב לבחירת מיקום על מפת Google — לחיצה על המפה קובעת סמן ומחזירה lat/lng.
// כתובת<->מפה מסונכרנים דו-כיוונית דרך GeocodingBridge.
export function MapPicker({
  value,
  onChange,
  address,
  onAddressResolved,
  onLocationResolved,
}: MapPickerProps) {
  if (!GOOGLE_MAPS_API_KEY) {
    return (
      <div className="map-placeholder">
        לא הוגדר מפתח Google Maps.
        <br />
        יש להגדיר את VITE_GOOGLE_MAPS_API_KEY בקובץ .env כדי להציג את המפה.
      </div>
    )
  }

  return (
    <div className="map-wrapper">
      {/* language/region — כתובות ותוויות בעברית, מוטות לישראל */}
      <APIProvider apiKey={GOOGLE_MAPS_API_KEY} language="he" region="IL">
        <Map
          style={{ width: '100%', height: '100%' }}
          defaultCenter={value ?? DEFAULT_MAP_CENTER}
          defaultZoom={value ? 14 : DEFAULT_MAP_ZOOM}
          gestureHandling="greedy"
          onClick={(event) => {
            const latLng = event.detail.latLng
            if (latLng) {
              onChange({ lat: latLng.lat, lng: latLng.lng })
            }
          }}
        >
          {value && <Marker position={value} />}
        </Map>
        <GeocodingBridge
          value={value}
          address={address}
          onAddressResolved={onAddressResolved}
          onLocationResolved={onLocationResolved}
        />
      </APIProvider>
    </div>
  )
}
