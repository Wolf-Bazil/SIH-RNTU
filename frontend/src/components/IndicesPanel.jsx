import React from 'react'
import Gauge from './Gauge'
import { IconTrendDown, IconTrendFlat, IconTrendUp } from './Icons'

function TrendBadge({ trend, t }) {
  const map = {
    increasing: { cls: 'border-rose-200 bg-rose-50 text-rose-700', Icon: IconTrendUp },
    decreasing: { cls: 'border-emerald-200 bg-emerald-50 text-emerald-700', Icon: IconTrendDown },
    stable: { cls: 'border-slate-200 bg-slate-50 text-slate-600', Icon: IconTrendFlat },
    unknown: { cls: 'border-slate-200 bg-slate-50 text-slate-400', Icon: IconTrendFlat },
  }
  const s = map[trend] || map.unknown
  return (
    <span className={`chip ${s.cls}`}>
      <s.Icon className="h-3.5 w-3.5" />
      {t('trend')}: {trend || '—'}
    </span>
  )
}

export default function IndicesPanel({ data, t }) {
  const hazard = data?.satellite?.mean_hazard
  const ci = data?.met?.mean_ci_pfz
  const pfz = data?.pfz
  const outlook = data?.hazard?.next_24h
  const confidence = data?.satellite?.confidence
  const missing = data?.satellite?.drivers_missing

  const pfzTone =
    pfz?.band === 'high' ? '#0d9488' : pfz?.band === 'moderate' ? '#d97706' : '#dc2626'

  return (
    <section className="card p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-bold text-abyss-900">{t('indices')}</h2>
        <TrendBadge trend={data?.hazard?.trend} t={t} />
      </div>

      <div className="grid grid-cols-3 gap-1">
        <Gauge value={hazard} label={t('hazard')} caption="H(x,y,t)" size={96} />
        <Gauge value={ci} label={t('ciPfz')} caption="CI_PFZ" size={96} />
        <Gauge value={pfz?.score} label={t('pfz')} caption={pfz?.band || '—'} size={96}
               tone={pfz?.band ? pfzTone : 'auto'} />
      </div>

      {/* An index computed from a subset of its drivers must not read as
          confidently as a complete one. */}
      {confidence != null && confidence < 1 && (
        <div className="mt-3 flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2">
          <span className="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-amber-500" />
          <p className="text-[10.5px] leading-relaxed text-amber-800">
            Partial data: {Math.round(confidence * 100)}% of the hazard model had a
            live reading
            {missing?.length ? ` (missing ${missing.join(', ')})` : ''}. Treat these
            indices as provisional.
          </p>
        </div>
      )}

      {pfz?.recommendation && (
        <div className="mt-3 rounded-lg border border-abyss-100 bg-abyss-50/60 px-3 py-2 text-[11px] font-medium text-abyss-800">
          {pfz.recommendation}
        </div>
      )}

      {outlook && (
        <div className="mt-3 border-t border-slate-100 pt-3">
          <div className="label mb-1.5">{t('outlook')}</div>
          <div className="grid grid-cols-2 gap-2 text-[11px]">
            <div className="flex items-center justify-between rounded-lg bg-slate-50 px-2.5 py-1.5">
              <span className="text-slate-500">{t('peakWind')}</span>
              <span className="tnum font-semibold text-abyss-800">
                {outlook.peak_wind_kmh} km/h
              </span>
            </div>
            <div className="flex items-center justify-between rounded-lg bg-slate-50 px-2.5 py-1.5">
              <span className="text-slate-500">{t('peakRain')}</span>
              <span className="tnum font-semibold text-abyss-800">
                {outlook.peak_precipitation_mm} mm/h
              </span>
            </div>
          </div>
        </div>
      )}
    </section>
  )
}
