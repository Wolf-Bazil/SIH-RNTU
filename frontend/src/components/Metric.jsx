import React from 'react'
import useCountUp from '../hooks/useCountUp'

/**
 * One live reading. Animates toward each new value and renders a shimmer
 * placeholder while the value is missing, so a dropped feed never shows as a
 * confident zero.
 */
export default function Metric({ label, value, unit, decimals = 1, icon, accent = 'abyss', hint }) {
  const animated = useCountUp(value)
  const missing = animated === null || animated === undefined

  const accents = {
    abyss: 'text-abyss-700 bg-abyss-50 ring-abyss-100',
    teal: 'text-teal-700 bg-teal-50 ring-teal-100',
    amber: 'text-amber-700 bg-amber-50 ring-amber-100',
    rose: 'text-rose-700 bg-rose-50 ring-rose-100',
  }

  return (
    <div className="group relative flex items-center gap-3 rounded-lg border border-slate-200/70 bg-white p-3 transition-all duration-300 hover:border-abyss-200 hover:shadow-card">
      {icon && (
        <div className={`grid h-9 w-9 shrink-0 place-items-center rounded-lg ring-1 ${accents[accent]}`}>
          {icon}
        </div>
      )}
      <div className="min-w-0 flex-1">
        <div className="label truncate">{label}</div>
        {missing ? (
          <div className="mt-1 h-5 w-16 rounded shimmer" />
        ) : (
          <div className="tnum flex items-baseline gap-1 text-abyss-900">
            <span className="text-lg font-semibold leading-tight">
              {animated.toFixed(decimals)}
            </span>
            {unit && <span className="text-xs font-medium text-slate-500">{unit}</span>}
          </div>
        )}
      </div>
      {hint && (
        <span className="pointer-events-none absolute -top-1 right-2 translate-y-[-100%] whitespace-nowrap rounded-md bg-abyss-900 px-2 py-1 text-[10px] font-medium text-white opacity-0 shadow-lift transition-opacity duration-200 group-hover:opacity-100">
          {hint}
        </span>
      )}
    </div>
  )
}
