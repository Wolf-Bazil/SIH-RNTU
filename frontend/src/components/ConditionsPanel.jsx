import React from 'react'
import Metric from './Metric'
import { IconGauge, IconRain, IconThermo, IconWave, IconWind } from './Icons'

export default function ConditionsPanel({ data, t }) {
  const c = data?.conditions || {}

  return (
    <section className="card p-4">
      <div className="mb-3 flex items-baseline justify-between">
        <h2 className="text-sm font-bold text-abyss-900">{t('conditions')}</h2>
        {data?.sources?.length > 0 && (
          <span className="font-mono text-[10px] text-slate-400">
            {data.sources.join(' · ')}
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 gap-2 stagger">
        <Metric label={t('sst')} value={c.sst_c} unit="°C" icon={<IconThermo />}
                accent="rose" hint="Above 28 °C fuels cyclones" />
        <Metric label={t('waves')} value={c.wave_height_m} unit="m" icon={<IconWave />}
                accent="abyss" hint="INCOIS warns above 3 m" />
        <Metric label={t('wind')} value={c.wind_speed_kmh} unit="km/h" decimals={0}
                icon={<IconWind />} accent="teal" hint="62 km/h is cyclonic" />
        <Metric label={t('pressure')} value={c.pressure_hpa} unit="hPa" decimals={0}
                icon={<IconGauge />} accent="abyss" hint="Lower means a deeper low" />
        <Metric label={t('gusts')} value={c.wind_gusts_kmh} unit="km/h" decimals={0}
                icon={<IconWind />} accent="amber" />
        <Metric label={t('rain')} value={c.precipitation_mm} unit="mm/h" icon={<IconRain />}
                accent="teal" hint="7.5 mm/h is heavy" />
      </div>

      {c.wave_period_s != null && (
        <div className="mt-3 flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2 text-[11px]">
          <span className="font-medium text-slate-500">{t('period')}</span>
          <span className="tnum font-semibold text-abyss-800">
            {c.wave_period_s.toFixed(1)} s
            {c.wave_direction_deg != null && (
              <span className="ml-2 font-normal text-slate-400">
                from {Math.round(c.wave_direction_deg)}°
              </span>
            )}
          </span>
        </div>
      )}
    </section>
  )
}
