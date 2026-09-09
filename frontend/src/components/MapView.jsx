import React, { useMemo, useState } from 'react'
import {
  Circle, MapContainer, Marker, Polyline, Popup, TileLayer, ZoomControl, useMap,
} from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// Low-chroma basemaps so the data layers carry the colour rather than the
// tiles. All three are Esri's public tile services: keyless, no API key
// watermark, and no usage token. CARTO's light_all was the obvious choice for
// the light theme but now stamps "API KEY REQUIRED" across every tile.
//
// `reference` is Esri's label-only transparent layer, drawn above the data so
// place names stay readable.
// Served through our own nginx (see nginx.conf `location /tiles/`) rather than
// hit directly. A direct third-party request to arcgisonline.com is blocked by
// browser tracking protection and by corporate filters, which leaves the map
// blank; proxying keeps it first-party and adds a 30-day tile cache.
const ESRI = '/tiles'

const BASEMAPS = {
  light: {
    label: 'Light',
    url: `${ESRI}/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}`,
    reference: `${ESRI}/Canvas/World_Light_Gray_Reference/MapServer/tile/{z}/{y}/{x}`,
    attribution: 'Tiles &copy; Esri &mdash; Esri, HERE, Garmin',
  },
  ocean: {
    label: 'Ocean',
    url: `${ESRI}/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}`,
    reference: `${ESRI}/Ocean/World_Ocean_Reference/MapServer/tile/{z}/{y}/{x}`,
    attribution: 'Tiles &copy; Esri &mdash; GEBCO, NOAA, and other contributors',
  },
  satellite: {
    label: 'Satellite',
    url: `${ESRI}/World_Imagery/MapServer/tile/{z}/{y}/{x}`,
    reference: null,
    attribution: 'Tiles &copy; Esri &mdash; Maxar, Earthstar Geographics',
  },
}

const SEVERITY_COLOR = {
  high: '#dc2626',
  medium: '#d97706',
  low: '#0d9488',
}

/** Pulsing dot, built as a divIcon so it can be animated with CSS. */
function pulseIcon(color, active) {
  return L.divIcon({
    className: '',
    iconSize: [16, 16],
    iconAnchor: [8, 8],
    html: `<div class="station-marker">
             ${active ? `<span class="ring" style="background:${color}"></span>` : ''}
             <span class="dot" style="background:${color}"></span>
           </div>`,
  })
}

/**
 * Eases the map to a new centre whenever the selected station changes.
 *
 * Guarded on two counts. Leaflet computes a flight path from the container's
 * pixel size, so calling flyTo while the flex layout still reports a zero-size
 * container produces an "Invalid LatLng object: (NaN, NaN)" throw that takes
 * the whole tree down. The first position is also skipped, because
 * MapContainer has already been initialised at that centre.
 */
function FlyTo({ position, zoom }) {
  const map = useMap()
  const isFirst = React.useRef(true)
  const lat = position?.[0]
  const lon = position?.[1]

  React.useEffect(() => {
    if (!Number.isFinite(lat) || !Number.isFinite(lon)) return undefined
    if (isFirst.current) {
      isFirst.current = false
      return undefined
    }

    let frame = 0
    const run = () => {
      const size = map.getSize()
      if (!size || size.x === 0 || size.y === 0) {
        // Layout has not settled yet; retry on the next frame.
        frame = requestAnimationFrame(run)
        return
      }
      map.flyTo([lat, lon], zoom ?? map.getZoom(), { duration: 0.9 })
    }
    frame = requestAnimationFrame(run)
    return () => cancelAnimationFrame(frame)
  }, [lat, lon, zoom, map])

  return null
}

/** Leaflet mis-measures inside a flex column until the first paint settles. */
function ResizeOnMount() {
  const map = useMap()
  React.useEffect(() => {
    const id = setTimeout(() => map.invalidateSize(), 180)
    const onResize = () => map.invalidateSize()
    window.addEventListener('resize', onResize)
    return () => {
      clearTimeout(id)
      window.removeEventListener('resize', onResize)
    }
  }, [map])
  return null
}

function Legend({ basemap, onBasemapChange }) {
  return (
    <div className="pointer-events-auto absolute bottom-4 left-4 z-[500] space-y-2">
      <div className="card flex overflow-hidden p-0.5">
        {Object.entries(BASEMAPS).map(([key, b]) => (
          <button
            key={key}
            type="button"
            onClick={() => onBasemapChange(key)}
            className={`focusable rounded-lg px-2.5 py-1 text-[10.5px] font-semibold transition-colors ${
              basemap === key
                ? 'bg-abyss-700 text-white'
                : 'text-slate-500 hover:bg-slate-50 hover:text-abyss-700'
            }`}
          >
            {b.label}
          </button>
        ))}
      </div>
      <div className="card px-3 py-2">
        <div className="label mb-1.5">Severity</div>
        <div className="space-y-1">
          {[['high', 'Warning'], ['medium', 'Advisory'], ['low', 'Nominal']].map(([k, txt]) => (
            <div key={k} className="flex items-center gap-2 text-[10.5px] text-slate-600">
              <span className="h-2 w-2 rounded-full" style={{ background: SEVERITY_COLOR[k] }} />
              {txt}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default function MapView({
  alerts = [], stations = [], station, overlays, onSelectStation, followStation = false,
}) {
  const [basemap, setBasemap] = useState('light')
  const base = BASEMAPS[basemap]

  const center = useMemo(
    () => (station ? [station.lat, station.lon] : [15.0, 84.0]),
    [station?.lat, station?.lon]
  )

  // One alert per station, so the map shows current state rather than history.
  const byStation = useMemo(() => {
    const map = new Map()
    for (const a of alerts) if (!map.has(a.station)) map.set(a.station, a)
    return map
  }, [alerts])

  const hazard = overlays?.satellite?.mean_hazard
  const routePath = overlays?.eco_route?.path

  return (
    <div className="relative h-full w-full">
      <MapContainer
        center={[15.0, 84.0]}
        zoom={5}
        minZoom={3}
        maxZoom={12}
        style={{ height: '100%', width: '100%' }}
        zoomControl={false}
        attributionControl
      >
        <TileLayer key={basemap} url={base.url} attribution={base.attribution} />
        <ZoomControl position="topright" />
        <ResizeOnMount />
        {followStation && <FlyTo position={center} zoom={6} />}

        {/* Hazard footprint around the selected station, radius scaled by the
            live hazard index so a rising index visibly widens the ring. */}
        {station && hazard != null && (
          <Circle
            center={[station.lat, station.lon]}
            radius={80000 + hazard * 220000}
            pathOptions={{
              color: hazard >= 0.6 ? '#dc2626' : hazard >= 0.35 ? '#d97706' : '#0d9488',
              fillColor: hazard >= 0.6 ? '#dc2626' : hazard >= 0.35 ? '#d97706' : '#0d9488',
              fillOpacity: 0.08,
              weight: 1.5,
              dashArray: '6 6',
            }}
          >
            <Popup>
              <div className="font-sans">
                <strong className="mb-1 block text-abyss-900">Hazard footprint</strong>
                <p className="m-0 text-slate-600">
                  H(x,y,t) = {hazard.toFixed(3)} · radius scaled by index
                </p>
              </div>
            </Popup>
          </Circle>
        )}

        {/* Modified A* eco-route, projected onto the Bay of Bengal corridor. */}
        {Array.isArray(routePath) && routePath.length > 1 && (
          <Polyline
            positions={routePath
              .filter((_, i) => i % 3 === 0)
              .map(([r, c]) => [13.0 - (r / 49) * 3.2, 80.3 + (c / 49) * 12.4])}
            pathOptions={{ color: '#0369a1', weight: 2.5, opacity: 0.75, dashArray: '8 6' }}
          >
            <Popup>
              <div className="font-sans">
                <strong className="mb-1 block text-abyss-900">Eco-route (modified A*)</strong>
                <p className="m-0 text-slate-600">
                  J_route = {overlays?.eco_route?.total_cost_J_route}
                </p>
                <p className="m-0 mt-1 text-[10px] text-slate-400">
                  Environmental field: {overlays?.eco_route?.environmental_field}
                </p>
              </div>
            </Popup>
          </Polyline>
        )}

        {stations.map((s) => {
          const alert = byStation.get(s.name)
          const color = alert ? SEVERITY_COLOR[alert.severity] : '#94a3b8'
          const isSelected = station?.name === s.name
          return (
            <Marker
              key={s.name}
              position={[s.lat, s.lon]}
              icon={pulseIcon(color, Boolean(alert) || isSelected)}
              eventHandlers={{ click: () => onSelectStation?.(s) }}
            >
              <Popup>
                <div className="font-sans">
                  <strong className="mb-1 block text-abyss-900">{s.name}</strong>
                  {alert ? (
                    <>
                      <div
                        className="mb-1 inline-block rounded px-1.5 py-0.5 text-[9px] font-bold uppercase"
                        style={{ background: `${color}1a`, color }}
                      >
                        {alert.severity} · {alert.type}
                      </div>
                      <p className="m-0 text-slate-600">{alert.message}</p>
                      {alert.readings && (
                        <div className="mt-1.5 border-t border-slate-100 pt-1.5 font-mono text-[9.5px] text-slate-500">
                          SST {alert.readings.sst_c ?? '—'}°C · wave{' '}
                          {alert.readings.wave_height_m ?? '—'}m · wind{' '}
                          {alert.readings.wind_speed_kmh ?? '—'}km/h
                        </div>
                      )}
                    </>
                  ) : (
                    <p className="m-0 text-slate-500">Awaiting this station&apos;s next reading.</p>
                  )}
                </div>
              </Popup>
            </Marker>
          )
        })}
        {/* Labels last, so place names stay legible over the data layers. */}
        {base.reference && (
          <TileLayer key={`${basemap}-ref`} url={base.reference} pane="shadowPane" />
        )}
      </MapContainer>

      <Legend basemap={basemap} onBasemapChange={setBasemap} />
    </div>
  )
}
