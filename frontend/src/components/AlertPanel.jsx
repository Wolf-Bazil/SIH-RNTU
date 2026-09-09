import React from 'react'
import { IconAlert, IconFish } from './Icons'

const SEVERITY = {
  high: {
    ring: 'border-rose-200 bg-rose-50/70',
    badge: 'bg-rose-100 text-rose-700',
    bar: 'bg-rose-500',
  },
  medium: {
    ring: 'border-amber-200 bg-amber-50/70',
    badge: 'bg-amber-100 text-amber-700',
    bar: 'bg-amber-500',
  },
  low: {
    ring: 'border-teal-200 bg-teal-50/60',
    badge: 'bg-teal-100 text-teal-700',
    bar: 'bg-teal-500',
  },
}

export default function AlertPanel({ alerts = [], connected, t, onFocus }) {
  return (
    <section className="card flex min-h-0 flex-1 flex-col p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-bold text-abyss-900">{t('alerts')}</h2>
        <span className="flex items-center gap-1.5 text-[10px] font-medium text-slate-400">
          <span
            className={`h-1.5 w-1.5 rounded-full ${
              connected ? 'bg-emerald-500' : 'bg-slate-300'
            }`}
          />
          SSE
        </span>
      </div>

      {alerts.length === 0 ? (
        <div className="flex flex-1 flex-col items-center justify-center gap-2 py-6 text-center">
          <div className="animate-drift grid h-10 w-10 place-items-center rounded-full bg-slate-50 text-slate-300">
            <IconFish className="h-5 w-5" />
          </div>
          <p className="text-[11px] text-slate-400">{t('noAlerts')}</p>
        </div>
      ) : (
        <div className="scroll-slim -mr-1 min-h-0 flex-1 space-y-2 overflow-y-auto pr-1">
          {alerts.map((a) => {
            const s = SEVERITY[a.severity] || SEVERITY.low
            return (
              <button
                key={a.id}
                type="button"
                onClick={() => onFocus?.(a)}
                className={`animate-slide-in focusable relative w-full overflow-hidden rounded-lg border ${s.ring} p-2.5 pl-3 text-left transition-all duration-200 hover:shadow-card`}
              >
                <span className={`absolute inset-y-0 left-0 w-1 ${s.bar}`} />
                <div className="flex items-start justify-between gap-2">
                  <span className="flex items-center gap-1.5 text-[11.5px] font-bold text-abyss-900">
                    {a.severity === 'high' && <IconAlert className="h-3.5 w-3.5 text-rose-600" />}
                    {a.type}
                  </span>
                  <span className={`shrink-0 rounded px-1.5 py-0.5 text-[9px] font-bold uppercase ${s.badge}`}>
                    {a.severity}
                  </span>
                </div>
                <p className="mt-1 text-[11px] leading-relaxed text-slate-600">{a.message}</p>
                <div className="mt-1.5 flex items-center justify-between font-mono text-[9.5px] text-slate-400">
                  <span className="truncate">{a.station}</span>
                  <span>{a.timestamp}</span>
                </div>
              </button>
            )
          })}
        </div>
      )}
    </section>
  )
}
