import React, { useEffect, useMemo, useState } from 'react'
import AlertPanel from './components/AlertPanel'
import AskPanel from './components/AskPanel'
import ConditionsPanel from './components/ConditionsPanel'
import ErrorBoundary from './components/ErrorBoundary'
import ExplanationPanel from './components/ExplanationPanel'
import IndicesPanel from './components/IndicesPanel'
import MapView from './components/MapView'
import TopBar from './components/TopBar'
import { useAlertStream, useOverlays, useStations } from './hooks/useLiveData'
import { useT } from './i18n'

export default function App() {
  const [language, setLanguage] = useState('en')
  const [station, setStation] = useState(null)
  // The map should open on the whole basin and only zoom in once the user has
  // actually chosen a station, not because the first one was auto-selected.
  const [userPicked, setUserPicked] = useState(false)

  const pickStation = (next) => {
    setUserPicked(true)
    setStation(next)
  }

  const stations = useStations()
  const { alerts, connected } = useAlertStream()
  const { data, status, refresh } = useOverlays(station)
  const t = useT(language)

  // Default to the first station once the catalogue arrives.
  useEffect(() => {
    if (!station && stations.length) setStation(stations[0])
  }, [stations, station])

  const observedAt = useMemo(
    () => data?.observed_at?.replace('T', ' ') ?? null,
    [data?.observed_at]
  )

  const focusAlert = (alert) => {
    const match = stations.find((s) => s.name === alert.station)
    if (match) pickStation(match)
  }

  return (
    <div className="flex h-full flex-col bg-[#f6f8fa]">
      <TopBar
        status={status}
        observedAt={observedAt}
        stations={stations}
        station={station}
        onStationChange={pickStation}
        language={language}
        onLanguageChange={setLanguage}
        onRefresh={refresh}
        t={t}
      />

      <main className="flex min-h-0 flex-1 flex-col lg:flex-row">
        {/* Map. Fixed height on small screens so the rails stay reachable. */}
        <div className="relative h-[46vh] shrink-0 border-b border-slate-200 lg:h-auto lg:min-h-0 lg:flex-1 lg:border-b-0 lg:border-r">
          <ErrorBoundary label="The map">
            <MapView
              alerts={alerts}
              stations={stations}
              station={station}
              overlays={data}
              followStation={userPicked}
              onSelectStation={pickStation}
            />
          </ErrorBoundary>
        </div>

        {/* Telemetry rail. */}
        <aside className="scroll-slim min-h-0 w-full shrink-0 space-y-3 overflow-y-auto bg-[#f6f8fa] p-3 lg:w-[340px] xl:w-[380px]">
          <ErrorBoundary label="Sea state">
            <ConditionsPanel data={data} t={t} />
          </ErrorBoundary>
          <ErrorBoundary label="Indices">
            <IndicesPanel data={data} t={t} />
          </ErrorBoundary>
          <ErrorBoundary label="The explanation">
            <ExplanationPanel data={data} t={t} />
          </ErrorBoundary>
        </aside>

        {/* Interaction rail. On a wide screen the two panels split it in half
            and scroll inside themselves, so a long conversation grows its own
            transcript instead of pushing the alert feed off the bottom. On a
            narrow screen they stack at their natural height and the rail
            scrolls as a whole, which is the right behaviour when there is no
            room to halve. */}
        <aside className="scroll-slim flex min-h-0 w-full shrink-0 flex-col gap-3 overflow-y-auto border-slate-200 bg-white/60 p-3 lg:w-[330px] lg:overflow-hidden lg:border-l xl:w-[360px]">
          <ErrorBoundary label="Ask ORCA">
            <AskPanel language={language} station={station} t={t} />
          </ErrorBoundary>
          <ErrorBoundary label="The alert feed">
            <AlertPanel alerts={alerts} connected={connected} t={t} onFocus={focusAlert} />
          </ErrorBoundary>
        </aside>
      </main>

      <footer className="flex items-center justify-between border-t border-slate-200 bg-white px-4 py-1.5 text-[10px] text-slate-400 sm:px-6">
        <span>
          ORCA · Multi-agent marine reasoning · Smart India Hackathon 2026, PS 176
        </span>
        <span className="hidden font-mono sm:inline">
          {data?.sources?.length ? data.sources.join(' · ') : 'awaiting feed'}
        </span>
      </footer>
    </div>
  )
}
