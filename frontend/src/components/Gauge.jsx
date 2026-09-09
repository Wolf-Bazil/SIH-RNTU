import React from 'react'
import useCountUp from '../hooks/useCountUp'

/**
 * Radial gauge for a normalised [0,1] index. The arc sweeps to the value on
 * every update, which makes a rising hazard index legible at a glance.
 */
export default function Gauge({ value, label, caption, size = 108, tone = 'auto' }) {
  const animated = useCountUp(value, { duration: 900 })
  const missing = animated === null || animated === undefined
  const v = missing ? 0 : Math.max(0, Math.min(1, animated))

  const radius = (size - 14) / 2
  const circumference = 2 * Math.PI * radius
  // Three quarters of the circle, so the gauge reads as a dial, not a donut.
  const arc = circumference * 0.75
  const offset = arc * (1 - v)

  const toneColor =
    tone !== 'auto'
      ? tone
      : v >= 0.66
      ? '#dc2626'
      : v >= 0.33
      ? '#d97706'
      : '#0d9488'

  return (
    <div className="flex flex-col items-center">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-[225deg]">
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="#e2e8f0"
            strokeWidth="9"
            strokeLinecap="round"
            strokeDasharray={`${arc} ${circumference}`}
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={toneColor}
            strokeWidth="9"
            strokeLinecap="round"
            strokeDasharray={`${arc} ${circumference}`}
            strokeDashoffset={offset}
            style={{ transition: 'stroke 600ms ease' }}
          />
        </svg>
        <div className="absolute inset-0 grid place-items-center">
          {missing ? (
            <div className="h-6 w-12 rounded shimmer" />
          ) : (
            <div className="text-center">
              <div className="tnum text-2xl font-bold leading-none text-abyss-900">
                {animated.toFixed(2)}
              </div>
              {caption && (
                <div className="mt-0.5 text-[10px] font-medium uppercase tracking-wide text-slate-500">
                  {caption}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
      <div className="mt-1.5 text-center text-xs font-semibold text-slate-600">{label}</div>
    </div>
  )
}
