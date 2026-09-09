import React from 'react'
import { LANGUAGES } from '../i18n'
import { IconPin, IconRefresh } from './Icons'

function StatusPill({ status, t }) {
  const map = {
    live: { text: t('live'), dot: 'bg-emerald-500', ring: 'bg-emerald-500/30',
            cls: 'border-emerald-200 bg-emerald-50 text-emerald-700' },
    degraded: { text: t('degraded'), dot: 'bg-amber-500', ring: 'bg-amber-500/30',
                cls: 'border-amber-200 bg-amber-50 text-amber-700' },
    error: { text: t('degraded'), dot: 'bg-rose-500', ring: 'bg-rose-500/30',
             cls: 'border-rose-200 bg-rose-50 text-rose-700' },
    loading: { text: t('connecting'), dot: 'bg-slate-400', ring: 'bg-slate-400/30',
               cls: 'border-slate-200 bg-slate-50 text-slate-600' },
  }
  const s = map[status] || map.loading

  return (
    <span className={`chip ${s.cls}`}>
      <span className="relative grid h-2 w-2 place-items-center">
        <span className={`absolute h-2 w-2 rounded-full ${s.ring} animate-pulse-ring`} />
        <span className={`h-2 w-2 rounded-full ${s.dot}`} />
      </span>
      {s.text}
    </span>
  )
}

export default function TopBar({
  status, observedAt, stations, station, onStationChange,
  language, onLanguageChange, onRefresh, t,
}) {
  return (
    <header className="z-30 border-b border-slate-200 bg-white/85 backdrop-blur-md">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2 px-4 py-2.5 sm:px-6">
        <div className="flex items-center gap-3">
          <div className="relative grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-abyss-600 to-abyss-900 shadow-card">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white"
                 strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round">
              <path d="M2 12c3-4.5 7-6.5 11-6.5S20 8 22 12c-2 4-5 6.5-9 6.5S5 16.5 2 12Z" />
              <circle cx="16" cy="11" r="1.1" fill="white" stroke="none" />
            </svg>
          </div>
          <div className="leading-tight">
            <div className="flex items-center gap-2">
              <span className="text-lg font-extrabold tracking-tight text-abyss-900">ORCA</span>
              <span className="hidden rounded-md border border-slate-200 bg-slate-50 px-1.5 py-0.5 font-mono text-[10px] font-semibold text-slate-500 sm:inline">
                SIH 2026 · PS 176
              </span>
            </div>
            <div className="hidden text-[11px] text-slate-500 md:block">{t('subtitle')}</div>
          </div>
        </div>

        <div className="ml-auto flex flex-wrap items-center gap-2">
          <StatusPill status={status} t={t} />

          {observedAt && (
            <span className="hidden font-mono text-[11px] text-slate-500 lg:inline">
              {t('observed')} {observedAt}Z
            </span>
          )}

          <div className="relative">
            <IconPin className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <select
              aria-label={t('station')}
              className="focusable h-9 appearance-none rounded-lg border border-slate-200 bg-white py-0 pl-8 pr-8 text-xs font-medium text-abyss-800 transition-colors hover:border-abyss-300"
              value={station?.name || ''}
              onChange={(e) => {
                const next = stations.find((s) => s.name === e.target.value)
                if (next) onStationChange(next)
              }}
            >
              {stations.map((s) => (
                <option key={s.name} value={s.name}>{s.name}</option>
              ))}
            </select>
            <svg className="pointer-events-none absolute right-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-400"
                 viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2"
                 strokeLinecap="round" strokeLinejoin="round">
              <path d="m6 9 6 6 6-6" />
            </svg>
          </div>

          <select
            aria-label="Language"
            className="focusable h-9 rounded-lg border border-slate-200 bg-white px-2.5 text-xs font-medium text-abyss-800 transition-colors hover:border-abyss-300"
            value={language}
            onChange={(e) => onLanguageChange(e.target.value)}
          >
            {LANGUAGES.map((l) => (
              <option key={l.code} value={l.code}>{l.label}</option>
            ))}
          </select>

          <button
            type="button"
            onClick={onRefresh}
            title={t('refresh')}
            aria-label={t('refresh')}
            className="focusable group grid h-9 w-9 place-items-center rounded-lg border border-slate-200 bg-white text-slate-500 transition-all hover:border-abyss-300 hover:text-abyss-700"
          >
            <IconRefresh className="h-4 w-4 transition-transform duration-500 group-hover:rotate-180" />
          </button>
        </div>
      </div>
    </header>
  )
}
