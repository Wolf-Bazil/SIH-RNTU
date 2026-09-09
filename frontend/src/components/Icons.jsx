import React from 'react'

// Inline 20px stroke icons. Kept local so the bundle carries no icon library.
const base = {
  width: 18,
  height: 18,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.8,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
}

export const IconThermo = (p) => (
  <svg {...base} {...p}>
    <path d="M14 14.76V4.5a2.5 2.5 0 0 0-5 0v10.26a4.5 4.5 0 1 0 5 0Z" />
  </svg>
)

export const IconWave = (p) => (
  <svg {...base} {...p}>
    <path d="M2 8c2.5 0 2.5 2.5 5 2.5S9.5 8 12 8s2.5 2.5 5 2.5S19.5 8 22 8" />
    <path d="M2 15c2.5 0 2.5 2.5 5 2.5s2.5-2.5 5-2.5 2.5 2.5 5 2.5 2.5-2.5 5-2.5" />
  </svg>
)

export const IconWind = (p) => (
  <svg {...base} {...p}>
    <path d="M3 8h10a3 3 0 1 0-3-3" />
    <path d="M3 12h14a3 3 0 1 1-3 3" />
    <path d="M3 16h7" />
  </svg>
)

export const IconGauge = (p) => (
  <svg {...base} {...p}>
    <path d="M12 14a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z" />
    <path d="M13.4 10.6 19 5" />
    <path d="M3.05 13a9 9 0 1 1 17.9 0" />
  </svg>
)

export const IconRain = (p) => (
  <svg {...base} {...p}>
    <path d="M4 14.5A4.5 4.5 0 0 1 7.5 7a5.5 5.5 0 0 1 10.6 1.5A3.75 3.75 0 0 1 18 15.9" />
    <path d="M8 18l-1 2.5M12 18l-1 2.5M16 18l-1 2.5" />
  </svg>
)

export const IconClock = (p) => (
  <svg {...base} {...p}>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 7v5l3 2" />
  </svg>
)

export const IconAlert = (p) => (
  <svg {...base} {...p}>
    <path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z" />
    <path d="M12 9v4M12 17h.01" />
  </svg>
)

export const IconFish = (p) => (
  <svg {...base} {...p}>
    <path d="M2 12c3-4.5 7-6.5 11-6.5S20 8 22 12c-2 4-5 6.5-9 6.5S5 16.5 2 12Z" />
    <path d="M17 12h.01" />
  </svg>
)

export const IconSend = (p) => (
  <svg {...base} {...p}>
    <path d="m4 4 16 8-16 8 3-8-3-8Z" />
  </svg>
)

export const IconRefresh = (p) => (
  <svg {...base} {...p}>
    <path d="M21 12a9 9 0 1 1-2.6-6.4" />
    <path d="M21 4v5h-5" />
  </svg>
)

export const IconPin = (p) => (
  <svg {...base} {...p}>
    <path d="M12 21s7-5.6 7-11a7 7 0 1 0-14 0c0 5.4 7 11 7 11Z" />
    <circle cx="12" cy="10" r="2.5" />
  </svg>
)

export const IconTrendUp = (p) => (
  <svg {...base} {...p}>
    <path d="m3 17 6-6 4 4 8-8" />
    <path d="M17 7h4v4" />
  </svg>
)

export const IconTrendDown = (p) => (
  <svg {...base} {...p}>
    <path d="m3 7 6 6 4-4 8 8" />
    <path d="M17 17h4v-4" />
  </svg>
)

export const IconTrendFlat = (p) => (
  <svg {...base} {...p}>
    <path d="M3 12h18" />
  </svg>
)
