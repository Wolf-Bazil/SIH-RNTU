import React from 'react'

// Presentational only. App owns the single /api/alerts/stream EventSource and
// passes the alerts down. Opening a second stream here duplicated every server
// connection and, because the effect depended on the alerts array, tore down
// and reopened that stream on every incoming alert.
function AlertPanel({ language, alerts = [] }) {
  return (
    <div className="bg-maritime-700 rounded-lg p-4">
      <h2 className="text-lg font-bold mb-2 text-maritime-200">
        {language === 'hi' ? 'चेतावनियाँ' : 'Alerts'}
      </h2>
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {alerts.length === 0 && (
          <div className="text-xs text-gray-400">
            {language === 'hi' ? 'लाइव फ़ीड से जुड़ रहे हैं…' : 'Connecting to live feed…'}
          </div>
        )}
        {alerts.map((alert, idx) => (
          <div key={alert.id || idx} className={`p-2 rounded ${
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
