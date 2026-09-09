import React from 'react'
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// Fix Leaflet marker icon asset loading in Vite
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

const darkTileLayer = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'

const MapView = ({ alerts = [] }) => {
  const defaultCenter = [15.0, 82.0] // Bay of Bengal & Indian Ocean center
  const defaultZoom = 5

  const getPosition = (alert) => {
    if (alert.lat !== undefined && alert.lng !== undefined) {
      return [alert.lat, alert.lng]
    }
    if (Array.isArray(alert.coordinates) && alert.coordinates.length >= 2) {
      return [alert.coordinates[1], alert.coordinates[0]]
    }
    return null
  }

  return (
    <MapContainer
      center={defaultCenter}
      zoom={defaultZoom}
      style={{ height: '100%', width: '100%' }}
    >
      <TileLayer
        attribution='&copy; <a href="https://carto.com/">CARTO</a>'
        url={darkTileLayer}
      />
      {alerts.map((alert, index) => {
        const pos = getPosition(alert)
        if (!pos) return null
        return (
          <Marker key={alert.id || index} position={pos}>
            <Popup>
              <div className="text-gray-900 font-sans">
                <strong className="text-blue-600 block mb-1">{alert.type || 'Alert'}</strong>
                <p className="text-sm m-0">{alert.message}</p>
                {alert.severity && (
                  <span className={`inline-block mt-1 text-xs px-2 py-0.5 rounded font-semibold uppercase ${
                    alert.severity === 'high' ? 'bg-red-100 text-red-700' :
                    alert.severity === 'medium' ? 'bg-amber-100 text-amber-700' :
                    'bg-blue-100 text-blue-700'
                  }`}>
                    {alert.severity}
                  </span>
                )}
              </div>
            </Popup>
          </Marker>
        )
      })}
    </MapContainer>
  )
}

export default MapView
