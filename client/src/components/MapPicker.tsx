import { APIProvider, Map, Marker } from '@vis.gl/react-google-maps'
import {
  GOOGLE_MAPS_API_KEY,
  DEFAULT_MAP_CENTER,
  DEFAULT_MAP_ZOOM,
} from '../config'
import type { LatLng } from '../api/types'

interface MapPickerProps {
  value: LatLng | null
  onChange: (coords: LatLng) => void
}

// רכיב לבחירת מיקום על מפת Google — לחיצה על המפה קובעת סמן ומחזירה lat/lng
export function MapPicker({ value, onChange }: MapPickerProps) {
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
      <APIProvider apiKey={GOOGLE_MAPS_API_KEY}>
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
      </APIProvider>
    </div>
  )
}
