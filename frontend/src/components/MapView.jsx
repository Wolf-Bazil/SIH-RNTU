import React from 'react'
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'

const MapView = ({ alerts }) => {
  const defaultCenter = [20.5937, 78.9629] // India center
  const defaultZoom = 5

  return (
    <MapContainer
      center={defaultCenter}
      zoom={defaultZoom}
      style={{ height: '100%', width: '100%' }}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {alerts.map((alert, index) => (
        <Marker key={index} position={[alert.lat, alert.lng]}>
          <Popup>
            <strong>{alert.severity.toUpperCase()}</strong><br />
            {alert.message}
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  )
}

export default MapView
