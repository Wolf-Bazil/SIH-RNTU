import React, { useState, useEffect } from 'react'

function AlertPanel({ language }) {
  const [alerts, setAlerts] = useState([])

  useEffect(() => {
    const eventSource = new EventSource('/api/alerts/stream')
    eventSource.addEventListener('alert', (e) => {
      const alert = JSON.parse(e.data)
      setAlerts(prev => [alert, ...prev.slice(0, 9)])
    })
    return () => eventSource.close()
  }, [])

  return (
    <div className="bg-maritime-700 rounded-lg p-4">
      <h2 className="text-lg font-bold mb-2 text-maritime-200">
        {language === 'hi' ? 'चेतावनियाँ' : 'Alerts'}
      </h2>
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {alerts.map((alert, idx) => (
          <div key={idx} className={`p-2 rounded ${
            alert.severity === 'high' ? 'bg-red-900/50 border border-red-500' :
            alert.severity === 'medium' ? 'bg-yellow-900/50 border border-yellow-500' :
            'bg-blue-900/50 border border-blue-500'
          }`}>
            <div className="text-sm font-semibold">{alert.type}</div>
            <div className="text-xs text-gray-300">{alert.message}</div>
            <div className="text-xs text-gray-400 mt-1">{alert.timestamp}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default AlertPanel
