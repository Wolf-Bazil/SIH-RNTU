import { useCallback, useEffect, useRef, useState } from 'react'

/**
 * Polls /api/overlays for the selected station.
 *
 * The upstream marine feed updates every 15 minutes and the backend caches for
 * 10, so polling faster than 60s only burns requests. A refresh is also
 * triggered whenever the station changes.
 */
export function useOverlays(station, { intervalMs = 60000 } = {}) {
  const [data, setData] = useState(null)
  const [status, setStatus] = useState('loading')
  const [error, setError] = useState(null)
  const abortRef = useRef(null)

  const load = useCallback(async () => {
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller

    try {
      const params = station
        ? `?lat=${station.lat}&lon=${station.lon}`
        : ''
      const res = await fetch(`/api/overlays${params}`, { signal: controller.signal })
      if (!res.ok) throw new Error(`overlays returned ${res.status}`)
      const json = await res.json()
      setData(json)
      setStatus(json.live ? 'live' : 'degraded')
      setError(null)
    } catch (e) {
      if (e.name === 'AbortError') return
      setStatus('error')
      setError(e.message)
    }
  }, [station])

  useEffect(() => {
    setStatus('loading')
    load()
    const id = setInterval(load, intervalMs)
    return () => {
      clearInterval(id)
      abortRef.current?.abort()
    }
  }, [load, intervalMs])

  return { data, status, error, refresh: load }
}

/**
 * Single EventSource for the alert stream, owned here so no component opens a
 * competing connection. Keeps the most recent `limit` alerts, de-duplicated by
 * station so one station cannot flood the feed.
 */
export function useAlertStream({ limit = 12 } = {}) {
  const [alerts, setAlerts] = useState([])
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    const source = new EventSource('/api/alerts/stream')

    source.onopen = () => setConnected(true)
    source.onerror = () => setConnected(false)

    source.addEventListener('alert', (event) => {
      try {
        const alert = JSON.parse(event.data)
        setAlerts((prev) => {
          const withoutStation = prev.filter((a) => a.station !== alert.station)
          return [alert, ...withoutStation].slice(0, limit)
        })
      } catch {
        // A malformed frame should not tear down the stream.
      }
    })

    return () => source.close()
  }, [limit])

  return { alerts, connected }
}

export function useStations() {
  const [stations, setStations] = useState([])

  useEffect(() => {
    let cancelled = false
    fetch('/api/stations')
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(r.status))))
      .then((j) => {
        if (!cancelled) setStations(j.stations || [])
      })
      .catch(() => {
        if (!cancelled) setStations([])
      })
    return () => {
      cancelled = true
    }
  }, [])

  return stations
}
