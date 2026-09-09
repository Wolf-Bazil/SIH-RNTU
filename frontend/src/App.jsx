import React, { useState, useEffect } from 'react'
import MapView from './components/MapView'
import AskPanel from './components/AskPanel'
import AlertPanel from './components/AlertPanel'
import LanguageToggle from './components/LanguageToggle'

function App() {
  const [alerts, setAlerts] = useState([])
  const [language, setLanguage] = useState('en')

  useEffect(() => {
    let eventSource
    try {
      eventSource = new EventSource('/api/alerts/stream')
      eventSource.addEventListener('alert', (e) => {
        try {
          const alert = JSON.parse(e.data)
          setAlerts((prev) => {
            const filtered = prev.filter((a) => a.type !== alert.type)
            return [alert, ...filtered]
          })
        } catch (err) {
          console.error('Error parsing SSE alert', err)
        }
      })
    } catch (e) {
      console.error('Failed to connect to SSE stream', e)
    }
    return () => {
      if (eventSource) eventSource.close()
    }
  }, [])

  return (
    <div className="flex flex-col h-screen bg-maritime-900 text-white font-sans">
      <header className="bg-maritime-800 border-b border-maritime-700 px-6 py-3 flex justify-between items-center shadow-lg">
        <div className="flex items-center gap-3">
          <span className="text-2xl font-black tracking-wider text-blue-400">ORCA</span>
          <span className="text-xs bg-maritime-700 text-maritime-200 px-2 py-1 rounded border border-maritime-600 font-mono">
            SIH 2026 PS 176
          </span>
          <span className="text-sm text-gray-300 hidden md:inline">Oceanic Risk & Cyclone Advisory System</span>
        </div>
        <div className="w-56">
          <LanguageToggle language={language} onLanguageChange={setLanguage} />
        </div>
      </header>
      <div className="flex flex-1 overflow-hidden">
        <div className="w-3/4 relative h-full">
          <MapView alerts={alerts} />
        </div>
        <div className="w-1/4 flex flex-col border-l border-maritime-700 bg-maritime-800 p-3 gap-3 overflow-y-auto">
          <AlertPanel alerts={alerts} language={language} />
          <AskPanel language={language} />
        </div>
      </div>
    </div>
  )
}

export default App
