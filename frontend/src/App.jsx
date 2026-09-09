import React, { useState } from 'react'
import MapView from './components/MapView'
import AskPanel from './components/AskPanel'
import AlertPanel from './components/AlertPanel'
import LanguageToggle from './components/LanguageToggle'

function App() {
  const [alerts, setAlerts] = useState([])
  const [language, setLanguage] = useState('en')

  return (
    <div className="flex flex-col h-screen">
      <header className="bg-blue-800 text-white p-4 flex justify-between items-center">
        <h1 className="text-xl font-bold">SIH RNTU - Disaster Resilience</h1>
        <LanguageToggle language={language} onLanguageChange={setLanguage} />
      </header>
      <div className="flex flex-1 overflow-hidden">
        <div className="w-3/4 relative">
          <MapView alerts={alerts} />
        </div>
        <div className="w-1/4 flex flex-col border-l">
          <AlertPanel alerts={alerts} />
          <AskPanel onAlertsUpdate={setAlerts} language={language} />
        </div>
      </div>
    </div>
  )
}

export default App
