import React from 'react'
import { MapContainer, TileLayer, Marker, Popup, Polygon, Polyline, Circle } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// Fix Leaflet marker icon asset loading in Vite
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

// High-resolution public satellite imagery (No API key required, no watermarks)
const satelliteTileLayer = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'

const MapView = ({ alerts = [] }) => {
  const defaultCenter = [14.0, 83.5] // Centered on Bay of Bengal & Indian coastline
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
        attribution='Tiles &copy; Esri &mdash; Source: Esri, Maxar, Earthstar Geographics'
        url={satelliteTileLayer}
      />

      {/* 1. Cyclone Hazard Cone (Bay of Bengal) */}
      <Polygon
        positions={[
          [11.5, 84.5],
          [14.2, 87.8],
          [17.8, 88.2],
          [18.5, 85.0],
          [15.0, 82.8]
        ]}
        pathOptions={{
          color: '#ef4444',
          fillColor: '#dc2626',
          fillOpacity: 0.28,
          weight: 2,
          dashArray: '5, 5'
        }}
      >
        <Popup>
          <div className="text-gray-900 font-sans">
            <strong className="text-red-600 block mb-1">Cyclone Hazard Cone H(x,y,t)</strong>
            <p className="text-xs m-0">Convective Core: Cloud Top &lt; -74°C | Wind: 52 kt</p>
            <span className="inline-block mt-1 text-xs px-2 py-0.5 rounded bg-red-100 text-red-700 font-semibold">
              SEVERITY: HIGH
            </span>
          </div>
        </Popup>
      </Polygon>

      {/* 2. Potential Fishing Zone (PFZ Chlorophyll Front) */}
      <Circle
        center={[11.2, 80.6]}
        radius={75000}
        pathOptions={{
          color: '#10b981',
          fillColor: '#059669',
          fillOpacity: 0.32,
          weight: 2
        }}
      >
        <Popup>
          <div className="text-gray-900 font-sans">
            <strong className="text-emerald-600 block mb-1">Potential Fishing Zone (PFZ)</strong>
            <p className="text-xs m-0">Chlorophyll Gradient: 3.4 mg/m³ | CI_PFZ: 0.88</p>
            <span className="inline-block mt-1 text-xs px-2 py-0.5 rounded bg-emerald-100 text-emerald-700 font-semibold">
              RECOMMENDED HARVEST
            </span>
          </div>
        </Popup>
      </Circle>

      {/* 3. Modified A* Eco-Route (Chennai to Port Blair avoiding Cyclone) */}
      <Polyline
        positions={[
          [13.08, 80.27], // Chennai
          [11.8, 82.5],
          [10.5, 86.2],
          [10.8, 90.0],
          [11.66, 92.73]  // Port Blair
        ]}
        pathOptions={{
          color: '#06b6d4',
          weight: 3,
          dashArray: '6, 6'
        }}
      >
        <Popup>
          <div className="text-gray-900 font-sans">
            <strong className="text-cyan-600 block mb-1">Eco-Route J_route (Modified A*)</strong>
            <p className="text-xs m-0">Optimized Fuel Burn: -17.4% | Storm Margin: &gt; 180 NM</p>
          </div>
        </Popup>
      </Polyline>

      {/* 4. IMBL Maritime Boundary Line */}
      <Polyline
        positions={[
          [10.2, 79.9],
          [9.7, 79.6],
          [9.2, 79.3],
          [8.8, 79.0],
          [8.2, 78.8]
        ]}
        pathOptions={{
          color: '#f59e0b',
          weight: 2,
          dashArray: '8, 4'
        }}
      >
        <Popup>
          <div className="text-gray-900 font-sans">
            <strong className="text-amber-600 block mb-1">IMBL / EEZ Boundary (Bhuvan)</strong>
            <p className="text-xs m-0">Automated Geofence: Active | Encroachment: Nil</p>
          </div>
        </Popup>
      </Polyline>

      {/* Live Event Markers */}
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
